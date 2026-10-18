#!/usr/bin/env python3
"""Durable supervisor lifecycle core; NO production driver or live command entry.

The narrow qa_pilot driver composes this core behind reviewed baseline/card/start
gates. This core has no default driver. Runtime observations, bounded termination
and verified cleanup remain the supplied driver's duty; grants are not proof.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import time

spec=importlib.util.spec_from_file_location('transport',Path(__file__).with_name('qa_transport.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')
control_spec=importlib.util.spec_from_file_location('control',Path(__file__).with_name('qa_control.py'))
control=importlib.util.module_from_spec(control_spec);control_spec.loader.exec_module(control)


def private_file(path:Path,flags:int) -> int:
    """Open a private single-link file without following its final symlink."""
    try:fd=os.open(path,flags|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    except FileNotFoundError:raise
    except OSError:raise ValueError('Unavailable or unsafe supervisor file') from None
    info=os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid()
        or info.st_mode & 0o077 or info.st_nlink!=1):
        os.close(fd);raise ValueError('Unsafe supervisor file')
    return fd


class Ledger:
    """Shared private lifecycle store with OS locks and durable atomic checkpoints.

    A fixed per-user host lock also coordinates mutating vmlab entry points even
    when ledger directories differ. Persistent budgets/replay still require the
    same ledger. Direct controllers and malicious same-user code can bypass this
    cooperative mechanism; it is not an OS permission boundary.
    """
    def __init__(self,root:Path):
        """Use an existing private shared directory; never invent/clear lab claims."""
        self.root=t.private_directory(root)
        self.held=set()

    def path(self,uuid:str,suffix:str) -> Path:
        """Restrict resource identities to canonical UUIDs, never paths or names."""
        if not isinstance(uuid,str) or not UUID.fullmatch(uuid):raise ValueError('Canonical lab UUID required')
        t.private_directory(self.root)
        return self.root/f'{uuid}.{suffix}'

    @contextmanager
    def claim(self,uuid:str):
        """Hold a nonblocking exclusive OS lock throughout proof/run/cleanup."""
        with control.claim() as control_fd:
            self.control_fd=control_fd
            try:
                with self.lab_claim(uuid):yield
            finally:self.control_fd=None

    @contextmanager
    def lab_claim(self,uuid:str):
        """Hold the ledger-specific UUID lock inside the canonical host claim."""
        if uuid in self.held:raise ValueError('Lab already held by this supervisor')
        fd=private_file(self.path(uuid,'lock'),os.O_RDWR|os.O_CREAT)
        try:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('Lab is owned by another supervisor') from None
            self.held.add(uuid)
            try:yield
            finally:self.held.discard(uuid)
        finally:os.close(fd)

    def snapshot(self,uuid:str) -> dict:
        """Read validated persisted state; corruption blocks instead of resetting it."""
        path=self.path(uuid,'json')
        try:fd=private_file(path,os.O_RDONLY)
        except FileNotFoundError:return dict(version=1,lab_uuid=uuid,halted=False,attempts=[],sessions={})
        with os.fdopen(fd) as source:value=json.load(source)
        if (value.get('version')!=1 or value.get('lab_uuid')!=uuid
            or value.get('checksum')!=t.x.queue.cat.digest({k:v for k,v in value.items() if k!='checksum'})
            or type(value.get('halted')) is not bool or not isinstance(value.get('attempts'),list)
            or not isinstance(value.get('sessions'),dict)):
            raise ValueError('Supervisor state changed or invalid; recovery required')
        return value

    def save(self,uuid:str,state:dict) -> None:
        """Fsync a private replacement and its directory before returning to dispatch."""
        if uuid not in self.held:raise ValueError('Mutation requires the lab lock')
        state['checksum']=t.x.queue.cat.digest({k:v for k,v in state.items() if k!='checksum'})
        path=self.path(uuid,'pending')
        fd=private_file(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
        with os.fdopen(fd,'w') as output:
            json.dump(state,output);output.flush();os.fsync(output.fileno())
        os.replace(path,self.path(uuid,'json'))
        directory=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)

    def recovered(self,uuid:str,state:dict) -> set[int]:
        """Validate audited dispositions against exact private pre-recovery archives."""
        records=state.get('recoveries',[]);indices=set()
        if not isinstance(records,list):raise ValueError('Invalid recovery history')
        for number,record in enumerate(records):
            if not isinstance(record,dict):raise ValueError('Invalid recovery disposition')
            index=record.get('attempt_index');checksum=record.get('source_checksum')
            if (type(index) is not int or not 0<=index<len(state['attempts']) or index in indices
                or not isinstance(checksum,str) or not re.fullmatch(r'[0-9a-f]{64}',checksum)
                or not re.fullmatch(r'[0-9a-f]{64}',record.get('next_queue_hash',''))
                or not re.fullmatch(r'[0-9a-f]{64}',record.get('evidence_hash',''))):
                raise ValueError('Invalid recovery disposition')
            with os.fdopen(private_file(self.path(uuid,'archive-'+checksum+'.json'),os.O_RDONLY),'rb') as source:
                raw=source.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:raise ValueError('Oversized recovery archive')
            archived=json.loads(raw)
            if (archived.get('checksum')!=checksum
                or checksum!=t.x.queue.cat.digest({k:v for k,v in archived.items() if k!='checksum'})
                or archived.get('lab_uuid')!=uuid or archived.get('halted') is not True
                or archived.get('attempts')!=state['attempts'][:index+1]
                or archived['attempts'][-1].get('status')!='halted'
                or record.get('attempt_hash')!=t.x.queue.cat.digest(state['attempts'][index])
                or archived.get('recoveries',[])!=records[:number]
                or any(state['sessions'].get(k,[])[:len(v)]!=v for k,v in archived['sessions'].items())):
                raise ValueError('Recovery archive/history changed')
            indices.add(index)
        return indices

    def recovery_request(self,uuid:str,plan:dict,review:dict) -> dict:
        """Check an exact expiring recovery grant before any external proof work."""
        if uuid not in self.held:raise ValueError('Recovery requires the lab lock')
        with control.claim(inherited_fd=self.control_fd):pass
        if self.path(uuid,'pending').exists():raise ValueError('Interrupted checkpoint requires manual review')
        state=self.snapshot(uuid);prior=self.recovered(uuid,state)
        if (state['halted'] is not True or not state['attempts']
            or state['attempts'][-1].get('status')!='halted'
            or any(a.get('status')!='complete' and i not in prior for i,a in enumerate(state['attempts'][:-1]))):
            raise ValueError('Only one terminal halted attempt can be recovered')
        if (review.get('version')!=1 or review.get('mode')!='supervised recovery'
            or review.get('explicit_recovery') is not True
            or not isinstance(review.get('reviewed_by'),str)
            or not re.fullmatch(r'[A-Za-z0-9 ._#-]{1,120}',review['reviewed_by'])
            or review.get('lab_uuid')!=uuid or review.get('source_checksum')!=state['checksum']
            or review.get('attempt_hash')!=t.x.queue.cat.digest(state['attempts'][-1])
            or review.get('next_queue_hash')!=plan.get('queue_hash')
            or review.get('target_revision')!=plan.get('target_revision')
            or review.get('baseline_hash')!=plan.get('baseline_hash')
            or not re.fullmatch(r'[0-9a-f]{64}',review.get('evidence_hash',''))
            or not re.fullmatch(r'[0-9a-f]{64}',plan.get('queue_hash',''))
            or plan['queue_hash'] in {a['queue_hash'] for a in state['attempts']}
            or not re.fullmatch(r'[0-9a-f]{40}',plan.get('target_revision',''))
            or not re.fullmatch(r'[0-9a-f]{64}',plan.get('baseline_hash',''))):
            raise ValueError('Separate exact recovery review required')
        expiry=datetime.fromisoformat(review.get('expires_at',''))
        if expiry.tzinfo is None or expiry<=datetime.now(timezone.utc):raise ValueError('Recovery review expired')
        return state

    def recover(self,uuid:str,plan:dict,review:dict,proof:dict) -> None:
        """Archive exact halted state and append a reviewed disposition; never replay.

        This trusted-core API does not collect proof. Only the gated pilot recovery
        caller may supply independently fresh cleanup/baseline observations. It
        preserves attempts/session budgets; clearing files or changing stores is
        never a recovery operation.
        """
        state=self.recovery_request(uuid,plan,review)
        proof_check(proof,plan,uuid)
        if (any(proof.get(k) is not True for k in ('container_absent','bridge_absent','processes_absent','session_closed'))
            or not re.fullmatch(r'[0-9a-f]{64}',proof.get('evidence_hash',''))
            or proof['evidence_hash']!=review.get('evidence_hash')):
            raise ValueError('Independent recovery cleanup evidence required')
        # Copy exact original bytes privately before updating the current halt gate.
        with os.fdopen(private_file(self.path(uuid,'json'),os.O_RDONLY),'rb') as source:
            raw=source.read(4*1024*1024+1)
        if len(raw)>4*1024*1024 or json.loads(raw)!=state:raise ValueError('Recovery source changed')
        archive=self.path(uuid,'archive-'+state['checksum']+'.json')
        try:fd=private_file(archive,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
        except FileExistsError:
            with os.fdopen(private_file(archive,os.O_RDONLY),'rb') as source:
                if source.read(4*1024*1024+1)!=raw:raise ValueError('Recovery archive changed')
        else:
            with os.fdopen(fd,'wb') as output:
                output.write(raw);output.flush();os.fsync(output.fileno())
        directory=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
        state.setdefault('recoveries',[]).append(dict(attempt_index=len(state['attempts'])-1,
            source_checksum=state['checksum'],attempt_hash=review['attempt_hash'],next_queue_hash=plan['queue_hash'],
            target_revision=plan['target_revision'],baseline_hash=plan['baseline_hash'],
            reviewed_by=review['reviewed_by'],review_hash=t.x.queue.cat.digest(review),
            evidence_hash=proof['evidence_hash'],proof_hash=t.x.queue.cat.digest(proof),at=t.x.now()))
        state['halted']=False
        self.save(uuid,state)

    def ready(self,uuid:str) -> dict:
        """Reject unresolved interruption/halt, even after a process restart."""
        if uuid not in self.held:raise ValueError('Readiness requires the lab lock')
        state=self.snapshot(uuid)
        recovered=self.recovered(uuid,state)
        if state['halted'] or any(a['status']!='complete' and i not in recovered for i,a in enumerate(state['attempts'])):
            raise ValueError('Lab halted or interrupted; separately verified recovery required')
        if self.path(uuid,'pending').exists():raise ValueError('Interrupted checkpoint; recovery required')
        return state

    def consume(self,uuid:str,plan:dict) -> None:
        """Consume one case slot before driver invocation; never permit implicit replay."""
        state=self.ready(uuid)
        key=(plan['queue_hash'],plan['set'],plan['case'])
        if any((a['queue_hash'],a['set'],a['case'])==key for a in state['attempts']):
            raise ValueError('Case already consumed; new session cannot replay it')
        if state.get('recoveries') and plan['queue_hash']!=state['recoveries'][-1]['next_queue_hash']:
            raise ValueError('Recovery permits only its separately reviewed new queue')
        session=t.x.queue.cat.digest([plan['queue_hash'],plan['set'],plan['owner'],plan['session']])
        batches=state['sessions'].setdefault(session,[])
        if plan['batch'] not in batches:
            if len(batches)>=5:raise ValueError('Persistent five-batch budget exhausted')
            batches.append(plan['batch'])
        state['attempts'].append({k:plan[k] for k in ('queue_hash','set','case','session','batch','owner')}
            |dict(status='running',started_at=t.x.now(),transport_hash=t.x.queue.cat.digest(plan)))
        self.save(uuid,state)

    def finish(self,uuid:str,success:bool,result:dict|None=None) -> None:
        """Persist outcome or a generic halted state; never save raw exception text."""
        if uuid not in self.held:raise ValueError('Completion requires the lab lock')
        state=self.snapshot(uuid)
        if not state['attempts'] or state['attempts'][-1]['status']!='running':raise ValueError('No running attempt')
        attempt=state['attempts'][-1]
        attempt.update(status='complete' if success else 'halted',ended_at=t.x.now())
        if success:attempt['result']=result
        else:state['halted']=True;attempt['reason']='Execution, proof, timing or cleanup unresolved; review private evidence'
        self.save(uuid,state)


def grant_check(q:dict,journal:dict,grant:dict) -> None:
    """Require a distinct explicit live start; never use offline attestations as one."""
    if (not isinstance(grant,dict) or grant.get('version')!=1 or grant.get('mode')!='supervised live'
        or grant.get('explicit_start') is not True or not isinstance(grant.get('reviewed_by'),str)
        or not grant['reviewed_by'].strip() or not UUID.fullmatch(grant.get('lab_uuid',''))):
        raise ValueError('Separate reviewed live start required')
    for field,value in dict(queue_hash=q['scope_hash'],owner=journal['owner'],set=journal['set'],
                            session=journal['session_id'],target_revision=q['target_revision']).items():
        if grant.get(field)!=value:raise ValueError('Live start identity mismatch')
    expiry=datetime.fromisoformat(grant.get('expires_at',''))
    if expiry.tzinfo is None or expiry<=datetime.now(timezone.utc):raise ValueError('Live start expired')


def proof_check(proof:dict,plan:dict,uuid:str) -> None:
    """Validate fresh driver observations; their acquisition is the driver's duty."""
    if (not isinstance(proof,dict) or proof.get('lab_uuid')!=uuid
        or proof.get('target_revision')!=plan['target_revision']
        or proof.get('origin')!=plan['bridge_origin']
        or any(proof.get(k) is not True for k in ('exclusive','runtime_identity_verified',
            'baseline_verified','recovery_verified','deployment_clean'))):
        raise ValueError('Live ownership/deployment/baseline proof missing or changed')
    observed=datetime.fromisoformat(proof.get('observed_at',''))
    if observed.tzinfo is None or not 0<=(datetime.now(timezone.utc)-observed).total_seconds()<=30:
        raise ValueError('Live proof stale')


def supervise(q:dict,journal:dict,grant:dict,ledger:Ledger,state_dir:Path,bridge_dir:Path,driver) -> dict:
    """Run one lifecycle through an explicitly supplied trusted driver.

    There is deliberately no default driver or CLI. Production integration needs
    independently verified proof collection, bounded process-group cancellation,
    private raw output/result parsing and verified cleanup. Synthetic tests prove
    sequencing and persistence, not those production capabilities.
    """
    grant_check(q,journal,grant)
    uuid=grant['lab_uuid']
    with ledger.claim(uuid):
        ledger.ready(uuid)
        plan=t.prepare(q,journal,state_dir,bridge_dir)
        actual=ledger.snapshot(uuid)['attempts']
        for prior in journal['results']:
            matches=[a for a in actual if a['queue_hash']==plan['queue_hash'] and a['set']==plan['set'] and a['case']==prior['case']]
            if len(matches)!=1 or matches[0].get('result')!=prior:
                raise ValueError('Prior offline result is not backed by this supervisor ledger')
        proof_check(driver.verify(plan),plan,uuid)
        # Recheck source/card/path/start and fresh proof immediately before consume.
        plan=t.prepare(q,journal,state_dir,bridge_dir)
        grant_check(q,journal,grant)
        proof_check(driver.verify(plan),plan,uuid)
        case=next(c for st in q['sets'] for c in st['cases'] if c['id']==plan['case'])
        timeout=case['execution']['timeout_seconds']
        elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(journal['active_case']['started_at'])).total_seconds()
        grant_remaining=(datetime.fromisoformat(grant['expires_at'])-datetime.now(timezone.utc)).total_seconds()
        remaining=min(timeout-elapsed,grant_remaining)
        if remaining<=0:raise ValueError('Case deadline passed')
        plan['remaining_seconds']=remaining
        plan['step_timeout_seconds']=case['execution']['step_timeout_seconds']
        ledger.consume(uuid,plan)
        started=time.monotonic();failed=False;outcome=None;clean=False
        try:
            outcome=driver.run(plan,remaining)
            if time.monotonic()-started>remaining:raise TimeoutError()
        except BaseException:
            failed=True
            try:driver.cancel(plan)
            except BaseException:pass
        finally:
            try:
                cleanup_started=time.monotonic()
                clean=driver.cleanup(plan) is True
                if clean:proof_check(driver.verify(plan),plan,uuid)
                if time.monotonic()-cleanup_started>plan['step_timeout_seconds']:clean=False
            except BaseException:clean=False
        try:
            if failed or not clean or outcome.get('restored',True) is not True:
                raise ValueError('Run or cleanup evidence unresolved')
            result_journal=json.loads(json.dumps(journal))
            t.x.authorize_action(q,result_journal,case['execution']['actions'][0])
            t.x.record_result(q,result_journal,outcome['result'],outcome['evidence'],True,outcome.get('reason',''))
            result=result_journal['results'][-1]
            ledger.finish(uuid,True,result)
            return result
        except BaseException:
            ledger.finish(uuid,False)
            raise ValueError('Supervisor halted; review private evidence and verified recovery before further work') from None
