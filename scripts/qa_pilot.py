"""Narrow permission-pilot driver and read-only preparation inspection.

A reviewed controlled-deployment baseline is required; disk/Git matches alone
never create one. The driver composes consumed-slot components. The live CLI requires a complete
source-bound card and separately reviewed explicit start; inspect never launches.
"""
from datetime import datetime,timezone
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import time
import urllib.request
import zlib


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

s=module('supervisor','qa_supervisor.py')
d=module('deployment','qa_deployment.py')
p=module('process','qa_process.py')
c=module('container','qa_container.py')
b=module('bridge','qa_bridge.py')
r=module('results','qa_results.py')
h=module('host','vmlab_preflight.py')
ROOT=Path(__file__).resolve().parent.parent
APP=Path('/opt/pinpoint/Network-Diagnosis-System')
SUPPORTED_CASES=frozenset({
    'TC-SS-04','TC-ACC-09','TC-NCPA-08',
    # Read-only module adapters with a reviewed exact fixture profile.
    'TC-ACC-08','TC-ROL-04','TC-DI-02','TC-DI-03','TC-DI-08','TC-HIS-04','TC-DASH-07',
})
MODULE_CASES=SUPPORTED_CASES-frozenset({'TC-SS-04','TC-ACC-09','TC-NCPA-08'})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):raise ValueError('Unexpected appliance redirect')


def validate_baseline(value):
    """Require reviewed controlled launch/build provenance and immutable content.

    This is an attestation boundary: a checksum does not prove the preparation
    happened. The reviewer must attach actual deployment/build/restart evidence.
    The runtime observer always stays negative until this independent record and
    current launch/process/source/config/dependency/served facts all agree.
    """
    if (not isinstance(value,dict) or value.get('version')!=1
        or value.get('checksum')!=d.manifest_digest({k:v for k,v in value.items() if k!='checksum'})
        or not value.get('reviewed_by') or not value.get('preparation_report')
        or not value.get('state_dir')
        or not isinstance(value.get('container_image_id'),str)
        or not value['container_image_id'].startswith('sha256:')
        or not d.HASH.fullmatch(value['container_image_id'][7:])
        or not d.HASH.fullmatch(value.get('browser_sha256',''))
        or not value.get('browser_relative_path')
        or value.get('method')!='controlled stopped-service deployment'
        or value.get('launch_verified') is not True or value.get('build_verified') is not True
        or not s.UUID.fullmatch(value.get('lab_uuid',''))
        or not d.HASH.fullmatch(value.get('email_fingerprint',''))):
        raise ValueError('Reviewed controlled-deployment baseline required')
    d.validate(value['manifest'])
    guest=value['guest'];obs=guest['observation']
    if (obs.get('source_files_match') is not True or obs.get('frontend_files_match') is not True
        or obs.get('unexpected_python_count')!=0 or not obs.get('processes')
        or guest.get('inputs_precede_launch') is not True
        or not any(row['pid']==guest['main_pid'] and row['parent_pid']==1 for row in obs['processes'])
        or guest.get('staff')!=[['ACTIVE',0,0,'Staff',1,0]] or guest.get('scheduler_enabled') is not False
        or [json.loads(row[0]) for row in guest.get('networks',[])]!=[['10.77.0.0/28']]
        or guest.get('dependencies',{}).get('file_count',0)<20 or not guest.get('configuration')
        or not guest.get('sources') or not guest.get('executables') or not guest.get('boot_id')):
        raise ValueError('Incomplete or unsuitable controlled baseline')
    if (obs.get('target_revision')!=value['manifest']['target_revision']
        or obs.get('manifest_hash')!=value['manifest']['checksum']
        or obs.get('artifact_hashes')!={k:value['manifest'][k] for k in ('sources','frontend')}
        or set(guest['sources'])!=set(value['manifest']['sources'])
        or any(record.get('sha256')!=value['manifest']['sources'][name] for name,record in guest['sources'].items())):
        raise ValueError('Source provenance mismatch')
    build=value['build']
    if (build.get('target')!=value['manifest']['target_revision']
        or build.get('frontend_artifacts')!=value['manifest']['frontend']
        or build.get('package_lock_sha256')!=value['manifest']['sources'].get('client/package-lock.json')):
        raise ValueError('Build provenance mismatch')
    launch=value['launch']
    if (launch.get('main_pid')!=guest['main_pid'] or launch.get('target')!=value['manifest']['target_revision']
        or launch.get('database_revisions_after')!=guest['database_versions']
        or launch.get('scheduler_enabled') is not False or launch.get('service_active') is not True
        or not {'database-upgrade','start-application'}<={row.get('step') for row in launch.get('steps',[]) if row.get('returncode')==0}):
        raise ValueError('Controlled launch provenance mismatch')


def compare_guest(expected,actual):
    """Reject reboot, worker replacement, file/config/dependency or baseline drift."""
    observation=actual['observation']
    if (observation.get('source_files_match') is not True or observation.get('frontend_files_match') is not True
        or observation.get('unexpected_python_count')!=0):raise ValueError('Deployment mismatch')
    for key in ('main_pid','boot_id','configuration','dependencies','sources','executables','staff',
                'networks','scans','database_versions','scheduler_enabled','inputs_precede_launch'):
        if actual.get(key)!=expected.get(key):raise ValueError('Prepared baseline changed')
    for key in ('target_revision','manifest_hash','artifact_hashes','processes'):
        if observation.get(key)!=expected['observation'].get(key):raise ValueError('Prepared runtime changed')


def collect_guest(manifest,email_fingerprint,ssh_key,runner,label):
    """Collect negative-readiness facts for reviewed preparation or verification."""
    d.validate(manifest)
    if not d.HASH.fullmatch(email_fingerprint):raise ValueError('Email fingerprint required')
    ssh_key=s.t.private_credential(ssh_key);ssh=str(Path('/usr/bin/ssh').resolve())
    code=(ROOT/'scripts/qa_deployment.py').read_text()+'\n'+(ROOT/'scripts/qa_pilot_guest.py').read_text()
    code+='\nprint(json.dumps(pilot_guest('+repr(manifest)+','+repr(email_fingerprint)+')))\n'
    packed=base64.b64encode(zlib.compress(code.encode())).decode()
    command='sudo -n python3 -I -B -c '+shlex.quote('import base64,zlib;exec(zlib.decompress(base64.b64decode('+repr(packed)+')))')
    argv=[ssh,'-p','2250','-i',str(ssh_key),'-oBatchMode=yes','-oStrictHostKeyChecking=no',
        '-oUserKnownHostsFile=/dev/null','-oConnectTimeout=5','-oLogLevel=ERROR','lab@127.0.0.1',command]
    response=runner.run(argv,{'PATH':'/usr/bin:/bin','HOME':str(runner.root),'LANG':'C'},20,
        label,max_output_bytes=4*1024*1024)
    if response.get('returncode')!=0 or response.get('group_clean') is not True:
        raise ValueError('Guest proof unavailable; inspect private output')
    return r.decode_json(r.read_private(Path(response['stdout']),runner.root,4*1024*1024))



class Inspector:
    """Fresh read-only host/SSH/public-HTTP observations under the caller's claim."""
    def __init__(self,baseline,output,ssh_key):
        validate_baseline(baseline);self.baseline=json.loads(json.dumps(baseline))
        self.root=s.t.private_directory(output);self.key=s.t.private_credential(ssh_key)
        self.ssh=str(Path('/usr/bin/ssh').resolve());self.docker=str(Path('/usr/bin/docker').resolve());self.runner=p.GroupRunner(self.root,{self.ssh,self.docker})
        self.sequence=0

    def guest(self):
        self.sequence+=1
        return collect_guest(self.baseline['manifest'],self.baseline['email_fingerprint'],
            self.key,self.runner,f'probe-{self.sequence}')

    def local(self,plan):
        """Inspect the cached image and pinned browser without starting either."""
        image=self.baseline['container_image_id']
        if plan.get('approved_image_id',image)!=image:raise ValueError('Image pin changed')
        self.sequence+=1
        result=self.runner.run([self.docker,'image','inspect',image,'--format','{{.Id}}'],
            {'PATH':'/usr/bin:/bin','HOME':str(self.root),'LANG':'C'},5,f'image-{self.sequence}',max_output_bytes=4096)
        if result['returncode']!=0 or result.get('group_clean') is not True or r.read_private(Path(result['stdout']),self.root,4096).decode().strip()!=image:
            raise ValueError('Pinned local image unavailable')
        definitions=json.loads((ROOT/'client/node_modules/playwright-core/browsers.json').read_text())
        revision=next(row['revision'] for row in definitions['browsers'] if row['name']=='chromium-headless-shell')
        name='chromium_headless_shell-'+revision+'/chrome-headless-shell-linux64/chrome-headless-shell'
        if self.baseline['browser_relative_path']!=name:raise ValueError('Browser revision changed')
        binary=s.t.clean_path(Path.home()/'.cache/ms-playwright'/name)
        if not binary.is_file() or not os.access(binary,os.X_OK) or binary.stat().st_size>512*1024*1024:
            raise ValueError('Pinned cached browser unavailable')
        digest=hashlib.sha256()
        with binary.open('rb') as stream:
            while chunk:=stream.read(1024*1024):digest.update(chunk)
        if digest.hexdigest()!=self.baseline['browser_sha256']:raise ValueError('Cached browser changed')

    def served(self):
        """Require exact fresh served public bytes, with no redirects or credentials."""
        deadline=time.monotonic()+10;total=0
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        for name,digest in self.baseline['manifest']['frontend'].items():
            d.relative_name(name)
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ValueError('Served proof budget exceeded')
            request=urllib.request.Request(b.ORIGIN+'/'+name,headers={'Accept-Encoding':'identity'})
            with opener.open(request,timeout=min(2,remaining)) as response:
                raw=response.read(d.MAX_FILE+1);total+=len(raw)
                if response.status!=200 or len(raw)>d.MAX_FILE or total>32*1024*1024 or hashlib.sha256(raw).hexdigest()!=digest:
                    raise ValueError('Served build changed')

    def verify(self,plan,control_fd):
        """Combine trusted preparation provenance with independently fresh facts."""
        with s.control.claim(inherited_fd=control_fd):pass
        expected=self.baseline
        if (plan.get('case') not in SUPPORTED_CASES or plan.get('baseline_hash')!=expected['checksum']
            or plan.get('target_revision')!=expected['manifest']['target_revision']
            or plan.get('bridge_origin')!=b.ORIGIN):raise ValueError('Pilot/baseline scope mismatch')
        if plan.get('state_dir') is not None:
            state=s.t.private_directory(Path(plan['state_dir']))
            if str(state)!=expected['state_dir'] or hashlib.sha256(s.t.private_credential(state/'restricted-email').read_bytes().strip()).hexdigest()!=expected['email_fingerprint']:
                raise ValueError('Staff credential identity changed')
            s.t.private_credential(state/'restricted-new-password')
        before=h.observe('pinpoint-qa-appliance','lab@127.0.0.1',[2250,18080])
        if not before['running_endpoints_verified'] or before['lab_uuid']!=expected['lab_uuid']:
            raise ValueError('Appliance ownership changed')
        self.local(plan)
        compare_guest(expected['guest'],self.guest());self.served()
        compare_guest(expected['guest'],self.guest())
        after=h.observe('pinpoint-qa-appliance','lab@127.0.0.1',[2250,18080])
        for key in ('lab_uuid','controller_pid','controller_start_ticks','vm_pid','vm_start_ticks'):
            if before[key]!=after[key] or after[key]!=expected['host'][key]:raise ValueError('Host baseline changed')
        return dict(lab_uuid=after['lab_uuid'],target_revision=plan['target_revision'],origin=b.ORIGIN,
            observed_at=datetime.now(timezone.utc).isoformat(),exclusive=True,runtime_identity_verified=True,
            baseline_verified=True,recovery_verified=True,deployment_clean=True)


class PilotDriver:
    """Wire trusted observations, owned transport, strict results and cleanup.

    Only explicit permission IDs and the reviewed read-only module IDs are allowed. Cleanup means session logout proved by adapter,
    container removal and bridge shutdown, then a fresh unchanged baseline. Any
    uncertainty halts; this driver never restores snapshots, resets users, retries,
    changes the product or claims a tool failure is a product FAIL.
    """
    def __init__(self,inspector,ledger,uuid,control_root):
        self.inspector=inspector;self.ledger=ledger;self.uuid=uuid
        self.root=s.t.private_directory(control_root,empty=True)
        self.bridge=None;self.runtime=None;self.runner=None;self.recovery_runner=None
        self.outcome=None;self.transport_complete=False;self.used=False

    def verify(self,plan):
        if self.uuid not in self.ledger.held or self.ledger.control_fd is None:raise ValueError('Held supervisor claim required')
        with s.control.claim(inherited_fd=self.ledger.control_fd):
            return self.inspector.verify(plan,self.ledger.control_fd)

    def run(self,plan,timeout):
        if self.used or plan.get('case') not in SUPPORTED_CASES:raise ValueError('Single supported current-case attempt per driver only')
        self.used=True
        self.bridge=b.Bridge(Path(plan['bridge_socket']).parent,**plan['bridge_limits'])
        self.bridge.start(plan,self.ledger,self.uuid,timeout)
        docker=str(Path('/usr/bin/docker').resolve())
        self.runner=p.GroupRunner(self.root,{docker});self.recovery_runner=p.GroupRunner(self.root,{docker})
        self.runtime=c.ContainerRuntime(self.root,docker,self.runner,self.recovery_runner,bridge=self.bridge)
        result=self.runtime.execute(plan,self.ledger,self.uuid,plan['approved_image_id'],timeout,
            min(30,plan['step_timeout_seconds']))
        self.transport_complete=result.get('container_clean') is True
        self.outcome=r.parse_report(Path(plan['evidence_dir'])/'results.json',
            plan['case'],Path(plan['evidence_dir']),result['run_started_at'],
            result['run_finished_at'],run_elapsed_seconds=result['run_elapsed_seconds'],max_run_seconds=min(timeout,plan['remaining_seconds']))
        if result['exit_code']!=0 and self.outcome['result']=='PASS':
            self.outcome.update(result='INCONCLUSIVE',reason='Container exit disagrees with successful report')
        return self.outcome

    def cancel(self,plan):
        """Cancel owned CLI groups; container component already owns daemon recovery."""
        for runner in (self.runner,self.recovery_runner):
            if runner is not None:runner.cancel()

    def cleanup(self,plan):
        """No invented restoration or fallback if browser/session cleanup is absent."""
        bridge_clean=self.bridge is not None and self.bridge.stop() is True
        return bool(bridge_clean and self.transport_complete and self.outcome
            and self.outcome.get('restored') is True and self.runner.idle() and self.recovery_runner.idle())


def private_json(path):
    """Load bounded private records, never print untrusted error contents."""
    path=s.t.private_credential(path)
    return r.decode_json(r.read_private(path,path.parent,4*1024*1024))


def save_private(path,value,*,new=False):
    """Durably checkpoint without reusing interrupted outputs."""
    path=s.t.clean_path(path);s.t.private_directory(path.parent)
    if new and path.exists():raise ValueError('Existing journal requires reviewed recovery')
    if path.exists():s.t.private_credential(path)
    pending=path.with_name(path.name+'.pending')
    fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    os.replace(pending,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def run_pilot(queue,run,owner,session,grant,baseline,state_dir,bridge_dir,control_dir,ssh_key):
    """One explicitly started fixed current-case batch; no retries or auto-resume.

    Supports three fixed permission cases and five read-only Module 2–9 cases.
    Every case uses a fresh driver, evidence directory, bridge and container and
    is saved before the next opens. Any non-PASS stops the remaining assignment;
    cleanup uncertainty halts.
    """
    errors=s.t.x.queue.check(queue,s.t.x.queue.load_catalog(),run)
    if errors:raise ValueError('Queue source changed; replacement review/start required')
    selected=s.t.x.queue.selected_sets(queue,run)[0]
    ids=[case['id'] for case in selected['cases']]
    if (selected['owner']!=owner or not 1<=len(ids)<=5 or not set(ids)<=SUPPORTED_CASES
        or len(selected['batches'])!=1 or selected['purpose']=='investigate'):
        raise ValueError('Only one fixed supported current-case batch is allowed')
    validate_baseline(baseline)
    cards=[s.t.x.validate_card(case) for case in selected['cases']]
    for card in cards:
        if (card.get('baseline_hash')!=baseline['checksum']
            or card.get('container_image_id')!=baseline['container_image_id']
            or card['timeout_seconds']>300 or card['step_timeout_seconds']>30):
            raise ValueError('Card baseline/image/budget mismatch')
    if str(state_dir)!=baseline['state_dir']:raise ValueError('Reviewed credential state required')
    identity=dict(owner=owner,set=run,session_id=session)
    s.grant_check(queue,identity,grant)
    if grant['lab_uuid']!=baseline['lab_uuid']:raise ValueError('Start/baseline lab mismatch')
    # All scope/card/start checks precede probes, output creation and transport.
    control_dir=s.t.private_directory(control_dir,empty=True)
    bridge_dir=s.t.private_directory(bridge_dir,empty=True);state_dir=s.t.private_directory(state_dir)
    evidence=[s.t.private_directory(Path(card['evidence_dir']),empty=True) for card in cards]
    paths=[control_dir,bridge_dir,state_dir,ROOT,*evidence]
    for i,a in enumerate(paths):
        for other in paths[i+1:]:
            if a.is_relative_to(other) or other.is_relative_to(a):raise ValueError('Permission batch paths overlap')
    multi=len(ids)>1
    for case,card in zip(selected['cases'],cards):
        case_control=control_dir/case['id'] if multi else control_dir
        case_bridge=bridge_dir/case['id'] if multi else bridge_dir
        if (card.get('control_dir',str(case_control))!=str(case_control)
            or card.get('bridge_dir',str(case_bridge))!=str(case_bridge)):
            raise ValueError('Card runtime output paths differ from fixed case paths')
        for path in (control_dir,bridge_dir):
            if not any(path.is_relative_to(s.t.clean_path(Path(p))) for p in card['write_paths']):
                raise ValueError('Control/bridge outputs outside approved write paths')
    (control_dir/'probes').mkdir(mode=0o700)
    inspector=Inspector(baseline,control_dir/'probes',ssh_key)
    proof_plan=dict(case=ids[0],baseline_hash=baseline['checksum'],target_revision=queue['target_revision'],bridge_origin=b.ORIGIN)
    with s.control.claim() as fd:proof=inspector.verify(proof_plan,fd)
    preflight=dict(owner=owner,lab=baseline['lab_uuid'],target_revision=queue['target_revision'],
        catalog_hash=selected['cases'][0]['source_hash'],observed_at=proof['observed_at'],exclusive=True,
        baseline_verified=True,recovery_verified=True,network_guard=True,live_authorized=False)
    journal=s.t.x.start(queue,run,owner,session,preflight,True)
    s.t.x.begin_batch(queue,journal,selected['batches'][0]['id'])
    journal_path=control_dir/'session.json'
    def checkpoint(*,new=False):
        journal.pop('journal_hash',None);journal['journal_hash']=s.t.x.queue.cat.digest(journal)
        save_private(journal_path,journal,new=new)
    checkpoint(new=True)
    ledger_root=s.control.canonical_root()/'pilot-ledger'
    ledger_root.mkdir(mode=0o700,exist_ok=True);ledger=s.Ledger(ledger_root)
    for case in selected['cases']:
        try:
            case_control=control_dir/case['id'] if multi else control_dir
            case_bridge=bridge_dir/case['id'] if multi else bridge_dir
            if multi:case_control.mkdir(mode=0o700);case_bridge.mkdir(mode=0o700)
            (case_control/'container').mkdir(mode=0o700)
            s.t.x.begin_case(queue,journal,case['id']);checkpoint()
            driver=PilotDriver(inspector,ledger,baseline['lab_uuid'],case_control/'container')
            result=s.supervise(queue,journal,grant,ledger,state_dir,case_bridge,driver)
            journal['results'].append(result);journal['active_case']=None
            journal['events'].append({'at':s.t.x.now(),'event':'supervised-permission-case-complete','case':case['id']})
            if len(journal['results'])==len(ids):
                journal['active_batch']=None
                journal['events'].append({'at':s.t.x.now(),'event':'batch-closed','batch':selected['batches'][0]['id']})
                journal['status']='complete'
            if result['result']!='PASS':journal['status']='stopped'
            checkpoint()
            if result['result']!='PASS':break
        except BaseException:
            journal['status']='halted'
            journal['events'].append({'at':s.t.x.now(),'event':'permission-batch-stopped-review-required'})
            checkpoint()
            raise ValueError('Permission batch stopped; preserve outputs and obtain reviewed recovery') from None
    if len(ids)==1:return journal['results'][0]
    return dict(results=journal['results'],status=journal['status'],
        next_case=ids[len(journal['results'])] if len(journal['results'])<len(ids) else None)


def main():
    """Read-only inspect or separately authorized bounded initial pilot launch."""
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    inspect=sub.add_parser('inspect')
    run=sub.add_parser('run')
    recovery=sub.add_parser('recover')
    handoff=sub.add_parser('handoff')
    for command in (inspect,run,recovery,handoff):
        command.add_argument('--baseline',type=Path,required=True)
        command.add_argument('--ssh-key',type=Path)
        command.add_argument('--control-dir',type=Path,required=True)
    for name in ('queue','grant','state-dir','bridge-dir'):run.add_argument('--'+name,type=Path,required=True)
    for name in ('run','owner','session'):run.add_argument('--'+name,required=True)
    for name in ('queue','prior-queue','grant'):recovery.add_argument('--'+name,type=Path,required=True)
    for name in ('queue','prior-queue','grant'):handoff.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:
        baseline=private_json(args.baseline)
        key=args.ssh_key or Path(baseline['state_dir'])/'id_ed25519'
        if args.command=='inspect':
            directory=s.t.private_directory(args.control_dir,empty=True)
            inspector=Inspector(baseline,directory,key)
            plan=dict(case='TC-SS-04',baseline_hash=baseline['checksum'],target_revision=baseline['manifest']['target_revision'],bridge_origin=b.ORIGIN)
            with s.control.claim() as fd:proof=inspector.verify(plan,fd)
            save_private(directory/'inspection.json',dict(proof=proof,live_authorized=False,test_cases_executed=0),new=True)
            print('Read-only pilot inspection passed. No test or transport launched; this is not a test start.')
        elif args.command=='handoff':
            handoff_module=module('handoff','qa_handoff.py')
            print(json.dumps(handoff_module.advance(r.decode_json(args.queue.read_bytes()),
                r.decode_json(args.prior_queue.read_bytes()),private_json(args.grant),baseline,args.control_dir,key)))
        elif args.command=='recover':
            recovery_module=module('recovery','qa_recovery.py')
            result=recovery_module.recover_pilot(r.decode_json(args.queue.read_bytes()),
                r.decode_json(args.prior_queue.read_bytes()),private_json(args.grant),baseline,args.control_dir,key)
            print(json.dumps(result))
        else:
            queue=r.decode_json(args.queue.read_bytes())
            result=run_pilot(queue,args.run,args.owner,args.session,private_json(args.grant),baseline,
                args.state_dir,args.bridge_dir,args.control_dir,key)
            print(json.dumps(result))
    except (Exception,KeyboardInterrupt):
        parser.exit(2,'qa_pilot: blocked/stopped; preserve private evidence and review scope, baseline, start and recovery\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
