"""Reviewed permission-assignment handoff; no case/browser/resource mutation.

The prior queue must have supervisor-backed restored PASS for every fixed ID.
Read-only terminal-resource and current baseline checks precede an audited ledger
append. This operation neither authorizes nor starts the next case assignment.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

spec=importlib.util.spec_from_file_location('pilot',Path(__file__).with_name('qa_pilot.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
r=v.module('recovery','qa_recovery.py')


def request_plan(queue,prior,baseline):
    """Validate only the new source-current finite permission scope and old checksum."""
    v.s.t.x.queue.validate(prior);v.validate_baseline(baseline)
    if v.s.t.x.queue.check(queue,v.s.t.x.queue.load_catalog()):raise ValueError('New assignment sources changed')
    if len(queue['sets'])!=1:raise ValueError('One new owner/set required')
    selected=queue['sets'][0];ids=[case['id'] for case in selected['cases']]
    if (selected['purpose']!='untested' or not 1<=len(ids)<=5 or not set(ids)<=v.SUPPORTED_CASES
        or len(selected['batches'])!=1 or queue['scope_hash']==prior['scope_hash']
        or queue['target_revision']!=prior['target_revision']
        or queue['target_revision']!=baseline['manifest']['target_revision']):
        raise ValueError('Exact new untested permission batch required')
    paths=set()
    for case in selected['cases']:
        card=v.s.t.x.validate_card(case)
        if (card.get('baseline_hash')!=baseline['checksum'] or card.get('container_image_id')!=baseline['container_image_id']
            or card['timeout_seconds']>300 or card['step_timeout_seconds']>30):
            raise ValueError('Reviewed card baseline/image/budgets required')
        paths.update(card['write_paths'])
    return dict(queue_hash=queue['scope_hash'],set=selected['name'],owner=selected['owner'],case=ids[0],
        target_revision=queue['target_revision'],baseline_hash=baseline['checksum'],bridge_origin=v.b.ORIGIN,case_ids=ids,
        write_paths=sorted(paths))


def completed_evidence(prior,state,uuid):
    """Verify exact accepted result files and terminal custody without reimport/rewrite."""
    attempts=[a for a in state['attempts'] if a['queue_hash']==prior['scope_hash']]
    identities=[];hashes=[];protected=[]
    for attempt in attempts:
        card=r.prior_card(prior,attempt);case=attempt['case']
        if case not in v.SUPPORTED_CASES:raise ValueError('Unsupported previous permission case')
        evidence=v.s.t.private_directory(Path(card['evidence_dir']))
        control=v.s.t.private_directory(Path(card.get('control_dir',str(evidence.parent/'control'))))
        bridge=v.s.t.private_directory(Path(card.get('bridge_dir',str(evidence.parent/'bridge'))))
        journal_path=Path(card.get('journal_path',str(control/'session.json')))
        journal=v.private_json(journal_path)
        container=v.private_json(control/'container/container-intent.json')
        relay=v.private_json(bridge/'bridge-intent.json')
        for record in (container,relay):
            if (record.get('version')!=1 or record.get('status')!='complete'
                or record.get('transport_hash')!=attempt['transport_hash']
                or record.get('queue_hash')!=attempt['queue_hash'] or record.get('case')!=case):
                raise ValueError('Previous terminal transport custody changed')
        if (container.get('session')!=attempt['session'] or relay.get('lab_uuid')!=uuid
            or relay.get('origin')!=v.b.ORIGIN
            or not re.fullmatch(r'[0-9a-f]{64}',container.get('container_id',''))
            or not re.fullmatch(r'pinpoint-qa-[0-9a-f]{32}',container.get('name',''))
            or not re.fullmatch(r'[0-9a-f]{64}',container.get('token',''))
            or journal.get('queue_hash')!=prior['scope_hash'] or journal.get('owner')!=attempt['owner']
            or journal.get('set')!=attempt['set'] or journal.get('session_id')!=attempt['session']
            or journal.get('status') not in ('active','complete')
            or journal.get('active_case') is not None or journal.get('active_batch') is not None
            or journal.get('results')!=[a['result'] for a in attempts]
            or journal.get('journal_hash')!=v.s.t.x.queue.cat.digest({k:x for k,x in journal.items() if k!='journal_hash'})):
            raise ValueError('Previous complete session or resource identity changed')
        result=attempt['result']
        if (result.get('result')!='PASS' or result.get('restored') is not True
            or set(result.get('evidence',{}))!=set(v.r.OBSERVATIONS[case])):
            raise ValueError('Complete accepted expected-item evidence required')
        files=[control/'container/container-intent.json',bridge/'bridge-intent.json',journal_path,evidence/'results.json']
        for item,text in v.r.OBSERVATIONS[case].items():
            row=result['evidence'][item];ref=row['reference']
            if (row.get('verdict')!='PASS' or row.get('observed')!=text or not isinstance(ref,str)
                or Path(ref).is_absolute() or '..' in Path(ref).parts):raise ValueError('Accepted item changed')
            path=evidence/ref;observation=v.r.decode_json(v.r.read_private(path,evidence,4096))
            if (observation.get('case_id')!=case or observation.get('item')!=item
                or observation.get('verdict')!='PASS' or observation.get('observed')!=text):
                raise ValueError('Accepted observation file changed')
            files.append(path)
        for path in files:
            hashes.append(dict(case=case,path=str(path),sha256=hashlib.sha256(v.r.read_private(path,path.parent,16*1024*1024)).hexdigest()))
        identities.append(dict(container_id=container['container_id'],name=container['name'],
            socket=str(bridge/'web.sock'),old_control=str(control)))
        protected.extend([evidence,control,bridge,journal_path.parent])
    if not identities:raise ValueError('No accepted previous transport')
    return dict(evidence_hash=v.s.t.x.queue.cat.digest(hashes),identities=identities,protected=sorted({str(p) for p in protected}))


def advance(queue,prior,review,baseline,control_dir,ssh_key):
    """Append reviewed forward scope only after independent fresh absence/baseline proof."""
    began=time.monotonic();plan=request_plan(queue,prior,baseline);uuid=baseline['lab_uuid']
    ledger=v.s.Ledger(v.s.control.canonical_root()/'pilot-ledger')
    with ledger.claim(uuid):
        state=ledger.handoff_request(uuid,prior,plan,review)  # Before any external probe/output.
        before=completed_evidence(prior,state,uuid)
        if before['evidence_hash']!=review['evidence_hash']:raise ValueError('Reviewed historical evidence changed')
        output=v.s.t.private_directory(control_dir,empty=True)
        if not any(output.is_relative_to(v.s.t.clean_path(Path(p))) for p in plan['write_paths']):
            raise ValueError('Handoff output outside reviewed write paths')
        protected=[v.ROOT,Path(baseline['state_dir']),ledger.root,*map(Path,before['protected'])]
        protected += [Path(c['execution'][k]) for c in queue['sets'][0]['cases']
                      for k in ('evidence_dir','control_dir','bridge_dir') if k in c['execution']]
        if any(output.is_relative_to(p) or p.is_relative_to(output) for p in protected):
            raise ValueError('Handoff output overlaps protected or next case paths')
        inspector=v.Inspector(baseline,output,ssh_key)
        for i,identity in enumerate(before['identities']):
            r.process_absence(identity);r.daemon_absence(identity,inspector.runner,f'handoff-before-{i}')
        proof=inspector.verify(plan,ledger.control_fd)
        for i,identity in enumerate(before['identities']):
            r.daemon_absence(identity,inspector.runner,f'handoff-after-{i}');r.process_absence(identity)
        if completed_evidence(prior,state,uuid)!=before or request_plan(queue,prior,baseline)!=plan:
            raise ValueError('Handoff evidence/scope changed during proof collection')
        if time.monotonic()-began>90:raise ValueError('Handoff proof budget exhausted')
        proof.update(container_absent=True,bridge_absent=True,processes_absent=True,session_closed=True,
            evidence_hash=before['evidence_hash'])
        v.save_private(output/'handoff-proof.json',dict(version=1,lab_uuid=uuid,source_checksum=state['checksum'],
            prior_queue_hash=prior['scope_hash'],next_queue_hash=queue['scope_hash'],case_attempted=False,proof=proof),new=True)
        ledger.handoff(uuid,prior,plan,review,proof)
    return dict(handed_off=True,case_attempted=False,next_queue_hash=queue['scope_hash'],explicit_start_still_required=True)
