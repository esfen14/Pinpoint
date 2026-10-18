#!/usr/bin/env python3
"""Offline QA session/card/evidence validator. NEVER launch commands, browsers or labs.

A journal records approved scope and rejects incomplete operations. This is not an
OS sandbox, a live preflight implementation or an unattended test dispatcher.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('queue',Path(__file__).with_name('qa_queue.py'))
queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)
RESULTS={'PASS','FAIL','PARTIALLY PASS','BLOCKED','Not run','INCONCLUSIVE'}


def now() -> str:
    """Return an attributable UTC journal timestamp."""
    return datetime.now(timezone.utc).isoformat()


def active_set(q:dict,s:dict) -> dict:
    """Validate immutable queue identity and reject halted/exhausted scope."""
    queue.validate(q)
    if s.get('queue_hash')!=q['scope_hash']:raise ValueError('Queue changed since session start')
    selected=queue.selected_sets(q,s['set'])[0]
    if s.get('owner')!=selected['owner']:raise ValueError('Owner changed')
    if s.get('status')!='active':raise ValueError('Session is not active; review recovery before resuming')
    return selected


def start(q:dict,run:str,owner:str,session_id:str,preflight:dict,confirmed_start:bool=False) -> dict:
    """Record explicit start/preflight attestations; this function performs no live preflight."""
    selected=queue.selected_sets(q,run)[0]
    if not confirmed_start or owner!=selected['owner'] or not queue.NAME.fullmatch(session_id):
        raise ValueError('Explicit start, correct owner and session ID are required')
    for field in ('lab','observed_at'):
        if not preflight.get(field):raise ValueError(f'Missing preflight {field}')
    observed=datetime.fromisoformat(preflight['observed_at'])
    if observed.tzinfo is None or not 0<=(datetime.now(timezone.utc)-observed).total_seconds()<=1800:
        raise ValueError('Preflight observation must be timezone-aware and no older than 30 minutes')
    if (preflight.get('owner')!=owner or preflight.get('target_revision')!=q['target_revision']
        or preflight.get('catalog_hash')!=selected['cases'][0]['source_hash']
        or any(preflight.get(k) is not True for k in ('exclusive','baseline_verified','recovery_verified','network_guard'))):
        raise ValueError('Missing/mismatched ownership, revision, baseline, recovery or network observation')
    # The offline validator must never be mistaken for an authorized live launcher.
    if preflight.get('live_authorized') is not False:
        raise ValueError('This validator supports offline journals only; no live dispatcher is implemented')
    return dict(version=1,queue_hash=q['scope_hash'],set=run,owner=owner,session_id=session_id,
      started_at=now(),preflight=preflight,status='active',batches_started=[],active_batch=None,
      active_case=None,results=[],events=[{'at':now(),'event':'offline-session-started'}])


def begin_batch(q:dict,s:dict,batch_id:str) -> None:
    """Consume budget at open, including interrupted/blocked batches, in fixed order."""
    selected=active_set(q,s)
    if s['active_case'] or s['active_batch']:raise ValueError('Previous case/batch is incomplete')
    if len(s['batches_started'])>=5:raise ValueError('Five-batch session limit reached')
    completed={r['case'] for r in s['results'] if r.get('restored') is True}
    remaining=[b for b in selected['batches'] if not set(b['ids'])<=completed]
    if not remaining or remaining[0]['id']!=batch_id:raise ValueError('Not the next fixed batch')
    if batch_id in s['batches_started']:raise ValueError('Batch already consumed; no counter reset')
    s['batches_started'].append(batch_id);s['active_batch']=batch_id
    s['events'].append({'at':now(),'event':'batch-opened','batch':batch_id})


def validate_card(c:dict) -> dict:
    """Require review, immutable adapter, bounded waits, exact actions and recovery."""
    card=c.get('execution',{})
    for k in ('reviewed_by','adapter','adapter_hash','mode','evidence_dir'):
        if not isinstance(card.get(k),str) or not card[k].strip():raise ValueError(f'{c["id"]}: missing {k}')
    if card['mode'] not in ('scripted automation','AI-assisted browser/API','human manual','mixed'):
        raise ValueError('Unknown executor mode')
    if card.get('human_required') is not False:raise ValueError('Unmet human evidence requirement')
    adapter=Path(card['adapter'])
    if not adapter.is_file() or adapter.is_symlink() or queue.cat.digest(adapter.read_text())!=card['adapter_hash']:
        raise ValueError('Adapter unavailable or changed')
    for k in ('timeout_seconds','step_timeout_seconds'):
        if type(card.get(k)) is not int or not 1<=card[k]<=21600:raise ValueError(f'Missing/bad timeout: {k}')
    if card['step_timeout_seconds']>card['timeout_seconds']:raise ValueError('Step timeout exceeds case timeout')
    for k in ('prerequisites','recovery','write_paths'):
        if not isinstance(card.get(k),list) or not card[k] or not all(isinstance(v,str) and v.strip() for v in card[k]):
            raise ValueError(f'Missing explicit {k}')
    actions=card.get('actions')
    if not isinstance(actions,list) or not actions or not all(isinstance(a,list) and a and all(isinstance(v,str) and v for v in a) for a in actions):
        raise ValueError('Exact argument-vector allowlist is required')
    if any(a[0] not in ('scripts/playwright-lab','scripts/vmlab','scripts/lab') for a in actions):
        raise ValueError('Unreviewed tool; no arbitrary shell actions')
    root=Path(card['evidence_dir']).resolve()
    if not root.is_dir() or not any(root.is_relative_to(Path(p).resolve()) for p in card['write_paths']):
        raise ValueError('Evidence directory is outside approved writable outputs')
    return card


def begin_case(q:dict,s:dict,case_id:str) -> None:
    """Open only the next listed case with a complete unchanged execution card."""
    selected=active_set(q,s)
    if s['active_case'] or not s['active_batch']:raise ValueError('Case active or batch not opened')
    batch=next(b for b in selected['batches'] if b['id']==s['active_batch'])
    done={r['case'] for r in s['results']}
    todo=[k for k in batch['ids'] if k not in done]
    if not todo or todo[0]!=case_id:raise ValueError('Not the next listed case')
    c=next(c for c in selected['cases'] if c['id']==case_id);validate_card(c)
    s['active_case']={'id':case_id,'started_at':now(),'attempt':1,'actions':[]}
    s['events'].append({'at':now(),'event':'case-opened','case':case_id})


def authorize_action(q:dict,s:dict,argv:list[str]) -> None:
    """Validate an exact action without executing it; no shell expansion is supported."""
    selected=active_set(q,s)
    if not s['active_case']:raise ValueError('No active case')
    c=next(c for c in selected['cases'] if c['id']==s['active_case']['id'])
    card=validate_card(c)
    index=len(s['active_case']['actions'])
    if index>=len(card['actions']) or argv!=card['actions'][index]:
        raise ValueError('Action is outside the next fixed allowlist slot; no hidden retry')
    s['active_case']['actions'].append({'at':now(),'argv':argv})



def block_case(q:dict,s:dict,case_id:str,reason:str) -> None:
    """Account for an unattempted blocked slot without inventing an adapter or observation."""
    selected=active_set(q,s)
    if not reason.strip() or s['active_case'] or not s['active_batch']:
        raise ValueError('Block requires a reason, an open batch and no active attempt')
    batch=next(b for b in selected['batches'] if b['id']==s['active_batch'])
    done={r['case'] for r in s['results']};todo=[k for k in batch['ids'] if k not in done]
    if not todo or todo[0]!=case_id:raise ValueError('Only the next fixed case can be blocked')
    s['results'].append(dict(case=case_id,batch=s['active_batch'],attempt=0,result='BLOCKED',
        evidence={},restored=True,reason=reason,at=now(),elapsed_seconds=0))
    if set(batch['ids'])<={r['case'] for r in s['results']}:
        s['events'].append({'at':now(),'event':'batch-closed','batch':s['active_batch']});s['active_batch']=None


def record_result(q:dict,s:dict,result:str,evidence:dict,restored:bool,reason:str='') -> None:
    """Require complete observed item evidence for PASS and stop on failed cleanup."""
    selected=active_set(q,s)
    if not s['active_case'] or result not in RESULTS:raise ValueError('No active case or invalid result')
    c=next(c for c in selected['cases'] if c['id']==s['active_case']['id']);card=validate_card(c)
    elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(s['active_case']['started_at'])).total_seconds()
    required={f'E{i}' for i in range(1,len(c['expectations'])+1)}
    if not isinstance(evidence,dict) or set(evidence)-required:raise ValueError('Unknown/malformed expected-item evidence')
    for item in evidence.values():
        if (not isinstance(item,dict) or item.get('verdict') not in RESULTS or not item.get('observed')
            or not isinstance(item.get('reference'),str)):raise ValueError('Incomplete expected-item observation')
        ref=Path(card['evidence_dir'])/item['reference']
        if (Path(item['reference']).is_absolute() or '..' in Path(item['reference']).parts
            or not ref.resolve().is_relative_to(Path(card['evidence_dir']).resolve()) or not ref.is_file()):
            raise ValueError('Evidence reference is missing or outside private evidence root')
    if type(restored) is not bool:raise ValueError('Restoration must be explicitly true/false')
    if result=='FAIL' and not any(v['verdict']=='FAIL' for v in evidence.values()):
        raise ValueError('FAIL requires an observed failed expected item')
    if result=='PASS' and (set(evidence)!=required or any(v['verdict']!='PASS' for v in evidence.values())
                           or not restored or elapsed>card['timeout_seconds']):
        raise ValueError('PASS needs all expected items, on-time observation and verified cleanup')
    if result!='PASS' and not reason.strip():raise ValueError('Non-pass needs an explicit reason')
    s['results'].append(dict(case=c['id'],batch=s['active_batch'],attempt=1,result=result,
                            evidence=evidence,restored=restored,reason=reason,at=now(),elapsed_seconds=elapsed))
    s['active_case']=None
    if not restored:s['status']='halted';s['events'].append({'at':now(),'event':'cleanup-failed'})
    batch=next(b for b in selected['batches'] if b['id']==s['active_batch'])
    if set(batch['ids'])<={r['case'] for r in s['results']}:
        s['events'].append({'at':now(),'event':'batch-closed','batch':s['active_batch']});s['active_batch']=None


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--queue',type=Path,required=True)
    p.add_argument('--journal',type=Path,required=True)
    cmd=p.add_subparsers(dest='command',required=True)
    st=cmd.add_parser('start');st.add_argument('--run',required=True);st.add_argument('--owner',required=True)
    st.add_argument('--session',required=True);st.add_argument('--preflight',type=Path,required=True)
    st.add_argument('--confirmed-start',action='store_true')
    batch=cmd.add_parser('batch');batch.add_argument('--id',required=True)
    case=cmd.add_parser('case');case.add_argument('--id',required=True)
    block=cmd.add_parser('block');block.add_argument('--id',required=True);block.add_argument('--reason',required=True)
    action=cmd.add_parser('action');action.add_argument('--argv-json',required=True)
    result=cmd.add_parser('result');result.add_argument('--input',type=Path,required=True)
    halt=cmd.add_parser('halt');halt.add_argument('--reason',required=True)
    cmd.add_parser('show')
    a=p.parse_args()
    try:
        q=json.loads(a.queue.read_text());queue.validate(q)
        errors=queue.check(q,queue.load_catalog())
        if errors:raise ValueError('\n'.join(errors))
        if a.command=='start':
            if a.journal.exists():raise ValueError('Journal exists; no session reset/overwrite')
            s=start(q,a.run,a.owner,a.session,json.loads(a.preflight.read_text()),a.confirmed_start)
        else:
            s=json.loads(a.journal.read_text())
            if s.get('journal_hash')!=queue.cat.digest({k:v for k,v in s.items() if k!='journal_hash'}):raise ValueError('Journal checksum changed')
            if a.command=='batch':begin_batch(q,s,a.id)
            elif a.command=='case':begin_case(q,s,a.id)
            elif a.command=='block':block_case(q,s,a.id,a.reason)
            elif a.command=='action':authorize_action(q,s,json.loads(a.argv_json))
            elif a.command=='result':
                r=json.loads(a.input.read_text());record_result(q,s,r['result'],r['evidence'],r['restored'],r.get('reason',''))
            elif a.command=='halt':s['status']='halted';s['events'].append({'at':now(),'event':'halt','reason':a.reason})
            else:print(json.dumps(s,indent=2));return 0
        s['journal_hash']=queue.cat.digest({k:v for k,v in s.items() if k!='journal_hash'})
        a.journal.parent.mkdir(parents=True,exist_ok=True)
        temp=a.journal.with_suffix('.pending');temp.write_text(json.dumps(s,indent=2)+'\n');temp.replace(a.journal)
        print('Offline journal updated. No command, browser or lab was executed.')
    except (ValueError,OSError,KeyError,TypeError,StopIteration) as exc:p.exit(2,f'qa_execute: {exc}\n')
    return 0
if __name__=='__main__':raise SystemExit(main())
