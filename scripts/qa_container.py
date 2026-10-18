"""Concrete bounded Docker lifecycle component; no CLI or default live driver.

Only a trusted future driver may call this after actual proof/start checks. A
consumed supervisor slot and held host claim are necessary, not authorization or
proof of deployment/baseline. Tests inject synthetic command responses only.
"""
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import time


def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

t=module('transport','qa_transport.py')
r=module('results','qa_results.py')
control=module('control','qa_control.py')
LABEL='org.pinpoint.qa.execution'
ID=re.compile(r'[0-9a-f]{64}')


class ContainerRuntime:
    """Create/attach/inspect/remove one owned container, never retry an attempt.

    Supply independent bounded GroupRunner instances for commands and recovery.
    A terminated Docker CLI is not container cleanup: cleanup uses Docker's actual
    resource identity/state and a successful daemon query proving absence. A failed
    or interrupted create remains halted even if no resource is currently visible,
    because an asynchronous daemon operation could finish later.
    """
    def __init__(self,root:Path,docker:str,runner,cleanup_runner,*,bridge):
        self.root=t.private_directory(root,empty=True)
        if not Path(docker).is_file() or str(Path(docker).resolve())!=docker:
            raise ValueError('Canonical reviewed Docker executable required')
        self.docker=docker;self.runner=runner;self.cleanup_runner=cleanup_runner
        self.bridge=bridge
        if not callable(getattr(bridge,'verify',None)):raise ValueError('Owned bridge custody checks required')
        if (runner is cleanup_runner or getattr(runner,'root',None)!=self.root
            or getattr(cleanup_runner,'root',None)!=self.root):
            raise ValueError('Independent bounded runners with shared private output required')
        self.intent=self.root/'container-intent.json';self.pending=self.root/'container-intent.pending'
        self.name='pinpoint-qa-'+secrets.token_hex(16);self.token=secrets.token_hex(32)
        self.cidfile=self.root/'container.cid';self.cid=None;self.used=False;self.halted=False;self.sequence=0

    def persist(self,status,plan,image):
        """Fsync intent before create and completion/halt after verified cleanup."""
        value=dict(version=1,status=status,name=self.name,token=self.token,container_id=self.cid,
            image=image,queue_hash=plan['queue_hash'],case=plan['case'],session=plan['session'],
            transport_hash=t.x.queue.cat.digest(plan))
        fd=os.open(self.pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as output:
            json.dump(value,output);output.flush();os.fsync(output.fileno())
        os.replace(self.pending,self.intent)
        directory=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)

    def call(self,args,deadline,*,cleanup=False,limit=1024*1024,allow_nonzero=False):
        """Use bounded private command output; never echo Docker diagnostics."""
        remaining=deadline-time.monotonic()
        if remaining<=0:raise ValueError('Container command budget exhausted')
        self.sequence+=1
        response=(self.cleanup_runner if cleanup else self.runner).run(
            [self.docker,*args],{'PATH':'/usr/bin:/bin','HOME':str(self.root),'LANG':'C'},
            remaining,f'container-{self.sequence}',max_output_bytes=limit)
        if (response.get('group_clean') is not True or type(response.get('returncode')) is not int
            or response['returncode']<0 or (not allow_nonzero and response['returncode']!=0)):
            raise ValueError('Container command or process cleanup unresolved')
        self.last_returncode=response['returncode']
        return r.read_private(Path(response['stdout']),self.root,limit)

    def inspected(self,plan,image,deadline,*,cleanup=False):
        """Require matching owned ID, image, command and actual isolation settings."""
        data=r.decode_json(self.call(['container','inspect',self.cid],deadline,cleanup=cleanup))
        if not isinstance(data,list) or len(data)!=1:raise ValueError('Ambiguous container inspection')
        item=data[0];config=item.get('Config',{});host=item.get('HostConfig',{})
        expected={}
        argv=plan['docker_argv']
        for i,value in enumerate(argv):
            if value=='--mount':
                text=argv[i+1];fields=dict(v.split('=',1) for v in text.split(',') if '=' in v)
                expected[fields['dst']]=(fields['src'],'readonly' not in text.split(','))
        actual={}
        for mount in item.get('Mounts',[]):
            key=mount.get('Destination')
            if key in actual or type(mount.get('RW')) is not bool:raise ValueError('Ambiguous container mount')
            actual[key]=(mount.get('Source'),mount['RW'])
        index=argv.index(t.IMAGE)
        if (item.get('Id')!=self.cid or item.get('Name')!='/'+self.name or item.get('Image')!=image
            or config.get('Labels',{}).get(LABEL)!=self.token or config.get('Entrypoint')!=['bash']
            or config.get('Cmd')!=argv[index+2:] or config.get('User')!=f'{os.getuid()}:{os.getgid()}'
            or host.get('NetworkMode')!='none' or host.get('ReadonlyRootfs') is not True
            or host.get('Privileged') is not False or host.get('AutoRemove') is not False
            or host.get('CapDrop')!=['ALL'] or host.get('CapAdd') not in (None,[])
            or host.get('SecurityOpt') not in (['no-new-privileges'],['no-new-privileges=true'])
            or host.get('RestartPolicy',{}).get('Name') not in ('no','')
            or host.get('PortBindings') not in (None,{}) or host.get('PidMode','')!=''
            or host.get('IpcMode','private') not in ('','private') or actual!=expected):
            raise ValueError('Container ownership or isolation changed')
        state=item.get('State',{})
        if type(state.get('Running')) is not bool:raise ValueError('Missing container state')
        return state

    def cleanup(self,plan,image,deadline):
        """Kill/remove only a positively identified owned resource; prove absence."""
        if self.cid is None:
            raw=self.call(['container','ls','--all','--no-trunc','--filter',f'name=^/{self.name}$',
                           '--format','{{.ID}}'],deadline,cleanup=True).decode().strip()
            if not raw:return  # Caller still halts after uncertain create.
            if not ID.fullmatch(raw):raise ValueError('Ambiguous resource lookup')
            self.cid=raw
        state=self.inspected(plan,image,deadline,cleanup=True)
        if state['Running']:
            self.call(['container','kill',self.cid],deadline,cleanup=True)
            if self.inspected(plan,image,deadline,cleanup=True)['Running']:
                raise ValueError('Owned container still running')
        self.call(['container','rm','--force',self.cid],deadline,cleanup=True)
        remaining=self.call(['container','ls','--all','--no-trunc','--filter',f'id={self.cid}',
                             '--format','{{.ID}}'],deadline,cleanup=True)
        if remaining.strip():raise ValueError('Container absence not proved')

    def execute(self,plan,ledger,uuid,image,timeout,cleanup_timeout):
        """One consumed attempt; caller still owns bridge/proof/result integration."""
        if self.used or self.halted:raise ValueError('Container attempt already used or halted')
        if (not isinstance(image,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',image)
            or image!=plan.get('approved_image_id')
            or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (timeout,cleanup_timeout))
            or timeout>21600 or cleanup_timeout>30
            or timeout>plan.get('remaining_seconds',0) or cleanup_timeout>plan.get('step_timeout_seconds',0)):
            raise ValueError('Scope-bound pinned image and bounded budgets required')
        if uuid not in ledger.held or getattr(ledger,'control_fd',None) is None:
            raise ValueError('Held supervisor/host claim required')
        with control.claim(inherited_fd=ledger.control_fd):pass
        state=ledger.snapshot(uuid);attempts=state['attempts']
        if (state['halted'] or not attempts or attempts[-1].get('status')!='running'
            or attempts[-1].get('transport_hash')!=t.x.queue.cat.digest(plan)
            or any(attempts[-1].get(k)!=plan.get(k) for k in ('queue_hash','set','case','session','batch','owner'))):
            raise ValueError('Durable consumed supervisor slot required')
        if self.bridge.verify(plan,ledger,uuid) is not True:raise ValueError('Owned bridge unavailable or changed')
        expected=t.container_command(Path(plan['evidence_dir']),Path(plan['state_dir']),
                                     Path(plan['bridge_socket']).parent,plan['case'])
        if plan.get('docker_argv')!=expected:raise ValueError('Prepared transport changed')
        t.private_directory(Path(plan['evidence_dir']),empty=True)
        try:bridge=Path(plan['bridge_socket']).lstat()
        except OSError:raise ValueError('Private bridge socket required') from None
        if not stat.S_ISSOCK(bridge.st_mode) or bridge.st_uid!=os.getuid() or bridge.st_mode & 0o077:
            raise ValueError('Private bridge socket required')
        for path in (Path(plan['evidence_dir']),Path(plan['state_dir']),Path(plan['bridge_socket']).parent,t.ROOT):
            if self.root.is_relative_to(path) or path.is_relative_to(self.root):raise ValueError('Control paths overlap transport')
        consumed=datetime.fromisoformat(attempts[-1]['started_at'])
        elapsed=(datetime.now(timezone.utc)-consumed).total_seconds()
        if not 0<=elapsed<plan['remaining_seconds']:raise ValueError('Consumed case budget expired')
        deadline=time.monotonic()+min(timeout,plan['remaining_seconds']-elapsed)
        self.used=True;failed=False;exit_code=None;started=None;create_called=False
        try:
            self.persist('creating',plan,image)
            index=expected.index(t.IMAGE)
            args=['create','--name',self.name,'--label',LABEL+'='+self.token,'--cidfile',str(self.cidfile),
                  '--entrypoint','bash',*expected[3:index],image,*expected[index+2:]]
            create_called=True
            raw=self.call(args,deadline).decode().strip()
            stored=r.read_private(self.cidfile,self.root,128).decode().strip()
            if not ID.fullmatch(raw) or stored!=raw:raise ValueError('Created resource identity ambiguous')
            self.cid=raw;self.persist('created',plan,image)
            if self.inspected(plan,image,deadline)['Running']:raise ValueError('Container started outside lifecycle')
            if self.bridge.verify(plan,ledger,uuid) is not True:raise ValueError('Bridge custody lost before attach')
            started=datetime.now(timezone.utc).isoformat()
            self.call(['start','--attach',self.cid],deadline,limit=8*1024*1024,allow_nonzero=True)
            attach_code=self.last_returncode
            if self.bridge.verify(plan,ledger,uuid) is not True:raise ValueError('Bridge custody lost during attach')
            observed=self.inspected(plan,image,deadline)
            if (observed['Running'] or observed.get('Status')!='exited'
                or type(observed.get('ExitCode')) is not int or not 0<=observed['ExitCode']<=255
                or observed['ExitCode']!=attach_code):
                raise ValueError('Container exit unresolved')
            exit_code=observed['ExitCode']
        except BaseException:
            failed=True
        finally:
            try:
                if create_called:self.cleanup(plan,image,time.monotonic()+cleanup_timeout)
                if not self.runner.idle() or not self.cleanup_runner.idle():raise ValueError('CLI group still active')
            except BaseException:failed=True
            try:self.persist('halted' if failed else 'complete',plan,image)
            except BaseException:failed=True
        if failed:
            self.halted=True
            raise ValueError('Container lifecycle halted; private evidence and verified recovery required') from None
        return dict(exit_code=exit_code,container_id=self.cid,container_clean=True,run_started_at=started)
