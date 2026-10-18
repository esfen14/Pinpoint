"""Gated permission-pilot recovery: read-only probes and audited ledger disposition.

No browser launch, reset, account change, resource kill/removal or report import.
The separate recovery grant authorizes proof acquisition and one disposition;
a later case still needs its own fresh queue and explicit live-start grant.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import time

spec=importlib.util.spec_from_file_location('pilot',Path(__file__).with_name('qa_pilot.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def request_plan(queue,prior,baseline):
    """Bind one new source-current recheck to the unchanged original target."""
    v.s.t.x.queue.validate(prior);v.validate_baseline(baseline)
    if v.s.t.x.queue.check(queue,v.s.t.x.queue.load_catalog()):raise ValueError('Recovery queue source changed')
    if (len(queue['sets'])!=1 or queue['sets'][0]['purpose']!='recheck'
        or [c['id'] for c in queue['sets'][0]['cases']]!=['TC-SS-04']
        or queue['scope_hash']==prior['scope_hash']
        or queue['target_revision']!=prior['target_revision']
        or queue['target_revision']!=baseline['manifest']['target_revision']):
        raise ValueError('Exact new permission recheck required')
    card=queue['sets'][0]['cases'][0]['execution']
    v.s.t.x.queue.coverage.validate_card_binding(queue['sets'][0]['cases'][0]['coverage'],card)
    if (card.get('baseline_hash')!=baseline['checksum']
        or card.get('container_image_id')!=baseline['container_image_id']
        or card.get('human_required') is not False
        or not isinstance(card.get('write_paths'),list) or not card['write_paths']):
        raise ValueError('Reviewed recovery baseline/image/output/participation scope required')
    return dict(queue_hash=queue['scope_hash'],target_revision=queue['target_revision'],
        baseline_hash=baseline['checksum'],case='TC-SS-04',bridge_origin=v.b.ORIGIN,write_paths=card['write_paths'])


def prior_card(prior,attempt):
    """Find the immutable consumed card without pretending historical sources are current."""
    matches=[c for group in prior['sets'] if group['name']==attempt['set'] and group['owner']==attempt['owner']
             for c in group['cases'] if c['id']==attempt['case']]
    if len(matches)!=1 or attempt['queue_hash']!=prior['scope_hash']:raise ValueError('Prior scope/attempt mismatch')
    return matches[0]['execution']


def old_evidence(prior,attempt,uuid):
    """Read only bounded owned terminal metadata and fixed browser logout evidence."""
    card=prior_card(prior,attempt)
    evidence=v.s.t.private_directory(Path(card['evidence_dir']))
    # The reviewed pilot has three sibling mounts, not caller-selected recovery roots.
    root=evidence.parent;control=v.s.t.private_directory(root/'control')
    bridge=v.s.t.private_directory(root/'bridge')
    container=v.private_json(control/'container/container-intent.json')
    relay=v.private_json(bridge/'bridge-intent.json')
    for record in (container,relay):
        if (record.get('version')!=1 or record.get('status')!='complete'
            or record.get('transport_hash')!=attempt['transport_hash']
            or record.get('queue_hash')!=attempt['queue_hash'] or record.get('case')!='TC-SS-04'):
            raise ValueError('Original transport cleanup unresolved')
    if (container.get('session')!=attempt['session'] or relay.get('lab_uuid')!=uuid
        or relay.get('origin')!=v.b.ORIGIN
        or not re.fullmatch(r'[0-9a-f]{64}',container.get('container_id',''))
        or not re.fullmatch(r'pinpoint-qa-[0-9a-f]{32}',container.get('name',''))
        or not re.fullmatch(r'[0-9a-f]{64}',container.get('token',''))):
        raise ValueError('Original resource identity unresolved')
    report=v.r.decode_json(v.r.read_private(evidence/'results.json',evidence,16*1024*1024))
    # Validate original report shape/identity without using the changed importer,
    # writing sanitized items or accepting the historical verdict.
    def specs(suites):
        return [spec for suite in suites for spec in [*suite.get('specs',[]),*specs(suite.get('suites',[]))]]
    selected=specs(report['suites'])
    if (len(selected)!=1 or selected[0]['title']!=card['selection']['title']
        or selected[0]['file']!='qa-permissions.lab.spec.ts' or len(selected[0]['tests'])!=1):
        raise ValueError('Original browser selection unresolved')
    test=selected[0]['tests'][0];results=test['results']
    if (test['projectName']!='qa-permissions' or len(results)!=1 or results[0]['retry']!=0
        or results[0]['status']!='passed' or report.get('errors')
        or results[0].get('errors') or results[0].get('error')
        or report['config']['version']!='1.64.0'
        or report['config']['metadata']['currentCaseIds']!=['TC-SS-04']):
        raise ValueError('Original browser cleanup provenance unresolved')
    config=report['config'];projects=config['projects'];filtered=config['filteredProjects']
    stats=report['stats']
    if (config.get('workers')!=1 or config.get('forbidOnly') is not True
        or config.get('fullyParallel') is not False
        or config.get('configFile')!='/work/client/playwright.qa.config.ts'
        or config.get('rootDir')!='/work/client/e2e'
        or config['metadata'].get('mode')!='scripted automation'
        or len(projects)!=1 or projects[0].get('name')!='qa-permissions'
        or projects[0].get('retries')!=0 or projects[0].get('repeatEach')!=1
        or len(filtered)!=1 or filtered[0].get('name')!='qa-permissions'
        or filtered[0].get('retries')!=0 or filtered[0].get('dependencies')!=[]
        or filtered[0]['use'].get('baseURL')!=v.b.ORIGIN
        or any(filtered[0]['use'].get(k)!='off' for k in ('trace','video','screenshot'))
        or any(type(stats.get(k)) is not int or stats[k]!=expected for k,expected in
               [('expected',1),('unexpected',0),('flaky',0),('skipped',0)])):
        raise ValueError('Original browser cleanup configuration unresolved')
    clean=[a for a in results[0].get('attachments',[]) if a.get('name')=='cleanup']
    if len(clean)!=1:raise ValueError('Original logout evidence unresolved')
    cleanup=v.r.attachment_data(clean[0],evidence)
    if set(cleanup)!={'session_closed'} or cleanup['session_closed'] is not True:
        raise ValueError('Original logout evidence unresolved')
    journal=v.private_json(control/'session.json')
    if (journal.get('status')!='halted' or journal.get('queue_hash')!=attempt['queue_hash']
        or journal.get('session_id')!=attempt['session'] or journal.get('results')!=[]
        or journal.get('journal_hash')!=v.s.t.x.queue.cat.digest({k:val for k,val in journal.items() if k!='journal_hash'})):
        raise ValueError('Original session history unresolved')
    digest=hashlib.sha256()
    for path in (control/'container/container-intent.json',bridge/'bridge-intent.json',evidence/'results.json',control/'session.json'):
        digest.update(v.r.read_private(path,path.parent,16*1024*1024))
    return dict(container_id=container['container_id'],name=container['name'],
        socket=str(bridge/'web.sock'),old_control=str(control),evidence_hash=digest.hexdigest())


def process_absence(identity,proc=Path('/proc')):
    """Reject surviving same-user original transport processes and Unix endpoints.

    No process data is returned/logged. Foreign-user processes are outside the
    same-user cooperative runner; container daemon absence is checked separately.
    """
    markers=[identity[k].encode() for k in ('container_id','name','socket','old_control')]
    for entry in proc.iterdir():
        if not entry.name.isdigit():continue
        try:
            if entry.stat().st_uid!=os.getuid():continue
            with (entry/'cmdline').open('rb') as source:command=source.read(65537)
            if len(command)>65536 or any(marker in command for marker in markers):
                raise ValueError('Original transport process remains or is ambiguous')
        except FileNotFoundError:continue
        except PermissionError:raise ValueError('Process identity unavailable') from None
    socket=Path(identity['socket'])
    if socket.exists() or socket.is_symlink():raise ValueError('Original socket remains')
    with (proc/'net/unix').open('rb') as source:connections=source.read(4*1024*1024+1)
    if len(connections)>4*1024*1024 or identity['socket'].encode() in connections:
        raise ValueError('Original Unix endpoint remains or is ambiguous')


def daemon_absence(identity,runner,label):
    """Require successful empty ID and name queries; no Docker mutation is allowed."""
    docker=str(Path('/usr/bin/docker').resolve())
    for number,selector in enumerate(('id='+identity['container_id'],'name=^/'+identity['name']+'$')):
        response=runner.run([docker,'container','ls','--all','--no-trunc','--filter',selector,'--format','{{.ID}}'],
            {'PATH':'/usr/bin:/bin','HOME':str(runner.root),'LANG':'C'},5,f'{label}-{number}',max_output_bytes=4096)
        if (response.get('returncode')!=0 or response.get('group_clean') is not True
            or v.r.read_private(Path(response['stdout']),runner.root,4096).strip()):
            raise ValueError('Original container absence not proved')


def recover_pilot(queue,prior,review,baseline,control_dir,ssh_key):
    """Apply only separately granted recovery after fresh actual cleanup/baseline checks."""
    began=time.monotonic()
    plan=request_plan(queue,prior,baseline);uuid=baseline['lab_uuid']
    # Fixed shared store, already present. Never create or choose another ledger.
    ledger=v.s.Ledger(v.s.control.canonical_root()/'pilot-ledger')
    with ledger.claim(uuid):
        state=ledger.recovery_request(uuid,plan,review)  # Before output or external calls.
        attempt=state['attempts'][-1]
        identity=old_evidence(prior,attempt,uuid)
        output=v.s.t.private_directory(control_dir,empty=True)
        if not any(output.is_relative_to(v.s.t.clean_path(Path(p))) for p in plan['write_paths']):
            raise ValueError('Recovery output outside reviewed write paths')
        old=Path(prior_card(prior,attempt)['evidence_dir']).parent
        paths=[output,old,v.ROOT,Path(baseline['state_dir']),ledger.root]
        for index,path in enumerate(paths):
            for other in paths[index+1:]:
                if path.is_relative_to(other) or other.is_relative_to(path):raise ValueError('Recovery outputs overlap protected paths')
        inspector=v.Inspector(baseline,output,ssh_key)
        process_absence(identity);daemon_absence(identity,inspector.runner,'before-recovery')
        proof=inspector.verify(plan,ledger.control_fd)
        daemon_absence(identity,inspector.runner,'after-recovery');process_absence(identity)
        if old_evidence(prior,attempt,uuid)!=identity:raise ValueError('Original evidence changed during recovery review')
        if request_plan(queue,prior,baseline)!=plan:raise ValueError('Recovery scope changed')
        proof.update(container_absent=True,bridge_absent=True,processes_absent=True,session_closed=True,
            evidence_hash=identity['evidence_hash'])
        if time.monotonic()-began>90:raise ValueError('Recovery proof budget exhausted')
        v.save_private(output/'recovery-proof.json',dict(version=1,lab_uuid=uuid,source_checksum=state['checksum'],
            next_queue_hash=queue['scope_hash'],original_result='INCONCLUSIVE',case_attempted=False,
            proof=proof),new=True)
        ledger.recover(uuid,plan,review,proof)
    return dict(recovered=True,case_attempted=False,original_result='INCONCLUSIVE')
