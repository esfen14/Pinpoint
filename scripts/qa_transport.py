#!/usr/bin/env python3
"""Build an OFFLINE transport preview. Never start Docker, a bridge or a browser.

This module defines the proposed container boundary, not a live dispatcher. An
explicit future supervisor must prove deployed revision, ownership and recovery,
consume the journal slot durably and hold its lock before using any transport.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
from datetime import datetime, timezone

spec=importlib.util.spec_from_file_location('execution',Path(__file__).with_name('qa_execute.py'))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
ROOT=Path(__file__).resolve().parent.parent
IMAGE='nikolaik/python-nodejs:python3.14-nodejs22'
# Fixed code only. Credentials never become Docker argv or preview JSON values.
BOOTSTRAP='''set -euo pipefail
umask 077
node /work/lab/unix_web_proxy.mjs /tmp/pinpoint-web.sock &
tunnel_pid=$!
trap 'kill "$tunnel_pid" 2>/dev/null || true' EXIT
export PINPOINT_RESTRICTED_USER="$(cat /state/restricted-email)"
export PINPOINT_RESTRICTED_NEW_PASSWORD="$(cat /state/restricted-new-password)"
cd /work/client
./node_modules/.bin/playwright test "$@"
'''


def clean_path(path:Path) -> Path:
    """Reject symlinks, nonabsolute paths and Docker mount-list delimiters."""
    path=Path(path)
    if (not path.is_absolute() or any(c in str(path) for c in (',','\n','\r','\x00'))
        or '..' in path.parts or path.resolve()!=path):raise ValueError('Unsafe transport path')
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('Symlink transport path')
    return path


def private_directory(path:Path,empty:bool=False) -> Path:
    """Require same-owner private existing directory; never create/clean evidence."""
    path=clean_path(path);info=path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode & 0o077:
        raise ValueError('Transport directory must be same-owner and private')
    if empty and any(path.iterdir()):raise ValueError('Transport directory is not empty; no overwrite')
    return path


def private_credential(path:Path) -> Path:
    """Validate file metadata only; never open or print credential contents."""
    path=clean_path(path);info=path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid()
        or info.st_mode & 0o077 or info.st_nlink!=1 or not info.st_size):
        raise ValueError('Credential file must be nonempty, private, regular and same-owner')
    return path


def prepare(q:dict,journal:dict,state_dir:Path,bridge_dir:Path) -> dict:
    """Validate one unconsumed opened case and describe its minimal container mount.

    All attestations remain offline. This does not read credentials, reserve the
    lab, consume a slot, create a socket, or execute anything in the returned plan.
    """
    errors=x.queue.check(q,x.queue.load_catalog())
    if errors:raise ValueError('; '.join(errors))
    if journal.get('journal_hash')!=x.queue.cat.digest({k:v for k,v in journal.items() if k!='journal_hash'}):
        raise ValueError('Journal checksum changed')
    selected=x.active_set(q,journal)
    # Reuse start validation for current ownership/revision and fresh attestations.
    x.start(q,journal['set'],journal['owner'],journal['session_id'],journal['preflight'],True)
    if selected['purpose']=='investigate':raise ValueError('Investigation is not product execution')
    batches=journal.get('batches_started',[])
    if not 1<=len(batches)<=5 or len(set(batches))!=len(batches):raise ValueError('Invalid consumed batch budget')
    listed=[b['id'] for b in selected['batches']]
    if batches!=listed[:len(batches)] or journal.get('active_batch')!=batches[-1]:raise ValueError('Not the current fixed batch')
    batch=next(b for b in selected['batches'] if b['id']==journal['active_batch'])
    results=journal.get('results',[])
    done={r['case'] for r in results}
    if len(done)!=len(results) or any(r.get('restored') is not True for r in results):raise ValueError('Unresolved or duplicate case outcomes')
    ordered=[k for b in selected['batches'] for k in b['ids']]
    if [r['case'] for r in results]!=ordered[:len(results)]:raise ValueError('Case results are not the fixed prefix')
    prior={k for b in selected['batches'][:len(batches)-1] for k in b['ids']}
    if not prior<=done or not done<=prior|set(batch['ids']):raise ValueError('Unaccounted or unlisted prior cases')
    todo=[k for k in batch['ids'] if k not in done];active=journal.get('active_case')
    if (not isinstance(active,dict) or not todo or active.get('id')!=todo[0]
        or active.get('attempt')!=1 or active.get('actions')!=[]):raise ValueError('No next unconsumed initial case action')
    case=next(c for c in selected['cases'] if c['id']==active['id'])
    card=x.validate_card(case)
    elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(active['started_at'])).total_seconds()
    if not 0<=elapsed<=card['timeout_seconds']:raise ValueError('Case timeout elapsed; review interrupted state')
    if card['selection']['config']!='client/playwright.qa.config.ts' or card['selection']['project']!='qa-permissions':
        raise ValueError('Unsupported transport adapter configuration')
    evidence=private_directory(Path(card['evidence_dir']),empty=True)
    state=private_directory(state_dir);bridge=private_directory(bridge_dir,empty=True)
    clean_path(ROOT)
    paths=[ROOT,evidence,state,bridge]
    for i,a in enumerate(paths):
        for b in paths[i+1:]:
            if a.is_relative_to(b) or b.is_relative_to(a):raise ValueError('Source, state, evidence and bridge paths must be disjoint')
    argv=container_command(evidence,state,bridge,case['id'])
    return dict(version=1,readiness='BLOCKED: live supervisor, ownership/deployment proof and recovery required',
        live_authorized=False,queue_hash=q['scope_hash'],journal_hash=journal['journal_hash'],
        owner=journal['owner'],set=journal['set'],session=journal['session_id'],
        batch=journal['active_batch'],case=case['id'],target_revision=q['target_revision'],
        evidence_dir=str(evidence),state_dir=str(state),bridge_socket=str(bridge/'web.sock'),
        approved_image_id=card.get('container_image_id'),
        bridge_origin='http://127.0.0.1:18080',docker_argv=argv,
        missing_live_guards=['Exclusive lab lock and runtime ownership proof',
            'Actual deployed revision and baseline/recovery verification',
            'Durable action-slot consumption, cancellation, cleanup and halted recovery',
            'Reviewed explicit live set start; offline journal is not authorization'])


def container_command(evidence:Path,state:Path,bridge:Path,case_id:str) -> list[str]:
    """Build the exact transport argv; this function grants no authority to run it.

    Unlike preparation, this permits already-created bridge/artifact entries so
    a future lifecycle component can revalidate the fixed command before launch.
    """
    evidence=private_directory(evidence);state=private_directory(state);bridge=private_directory(bridge)
    cases=x.queue.coverage.load()['cases']
    if case_id not in cases or cases[case_id]['status']!='implemented':raise ValueError('Unsupported transport case')
    paths=[ROOT,evidence,state,bridge]
    for i,a in enumerate(paths):
        for b in paths[i+1:]:
            if a.is_relative_to(b) or b.is_relative_to(a):raise ValueError('Transport paths overlap')
    credentials=[private_credential(state/name) for name in ('restricted-email','restricted-new-password')]
    cache=clean_path(Path.home()/'.cache/ms-playwright')
    uid,gid=os.getuid(),os.getgid()
    mounts=[f'type=bind,src={ROOT},dst=/work,readonly',
        f'type=bind,src={evidence},dst=/evidence',
        f'type=bind,src={bridge}/web.sock,dst=/tmp/pinpoint-web.sock,readonly',
        f'type=bind,src={cache},dst=/ms-playwright,readonly',
        'type=bind,src=/lib/x86_64-linux-gnu,dst=/host-libs,readonly']
    mounts += [f'type=bind,src={p},dst=/state/{p.name},readonly' for p in credentials]
    argv=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--shm-size=1g','--user',f'{uid}:{gid}',
        '--tmpfs',f'/tmp:rw,nosuid,nodev,mode=1777,uid={uid},gid={gid}']
    for mount in mounts:argv+=['--mount',mount]
    for env in ('HOME=/tmp','PLAYWRIGHT_BROWSERS_PATH=/ms-playwright','LD_LIBRARY_PATH=/host-libs',
                f'PINPOINT_QA_CASES={case_id}','PINPOINT_QA_RUN_DIR=/evidence'):
        argv+=['--env',env]
    argv += [IMAGE,'bash','-c',BOOTSTRAP,'bash',*x.queue.coverage.action_for(cases[case_id])[1:]]
    return argv


def main() -> int:
    """Print transport metadata only; do not write artifacts or invoke commands."""
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('queue','journal','state-dir','bridge-dir'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:
        plan=prepare(json.loads(a.queue.read_text()),json.loads(a.journal.read_text()),a.state_dir,a.bridge_dir)
        print(json.dumps(plan,indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError,StopIteration):
        # Untrusted parse/OS exceptions can include credential/file contents.
        p.exit(2,'qa_transport: invalid or blocked offline transport inputs; review scope, journal and private paths\n')


if __name__=='__main__':raise SystemExit(main())
