#!/usr/bin/env python3
"""Prepare immutable version-2 module/person QA assignments; never run live tests."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('qa_catalog',Path(__file__).with_name('qa_catalog.py'))
cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
spec=importlib.util.spec_from_file_location('coverage',Path(__file__).with_name('qa_coverage.py'))
coverage=importlib.util.module_from_spec(spec);spec.loader.exec_module(coverage)
load_catalog=cat.load_catalog
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*')
REV=re.compile(r'[0-9a-f]{40}')


def cell(value) -> str:
    """Escape user/case text for a single preview table cell."""
    return ' '.join(str(value).replace('|',r'\|').split())



def references() -> dict:
    """Freeze the normative/specification and execution-rule sources for preparation."""
    paths=list((ROOT/'spec files').glob('*.md'))+[ROOT/'.agent/workflows/qa-run.md',
        ROOT/'docs/qa/QA_Run_Queues.md',ROOT/'docs/qa/QA_Journeys_and_Scope.md',ROOT/'docs/qa/Next_Permission_Batch_Review.md',
        ROOT/'docs/qa/Automation_Readiness.md',ROOT/'docs/qa/Automation_Coverage.md',
        ROOT/'docs/qa/Module_2-9_Adapter_Review.md',ROOT/'docs/qa/Module_2-9_Fixture_Plan.md',
        ROOT/'docs/qa/queues/modules-2-9-card-drafts-v3.json',
        ROOT/'scripts/qa_catalog.py',ROOT/'scripts/qa_queue.py',ROOT/'scripts/qa_evidence.py',
        ROOT/'scripts/qa_execute.py',ROOT/'scripts/qa_transport.py',ROOT/'scripts/qa_supervisor.py',ROOT/'scripts/qa_process.py',ROOT/'scripts/qa_results.py',ROOT/'scripts/qa_coverage.py',coverage.REGISTRY,
        ROOT/'scripts/qa_control.py',ROOT/'scripts/vmlab',ROOT/'scripts/vmlab_preflight.py',
        ROOT/'scripts/qa_container.py',
        ROOT/'scripts/qa_bridge.py',ROOT/'scripts/qa_deployment.py',
        ROOT/'scripts/qa_pilot.py',ROOT/'scripts/qa_pilot_guest.py',ROOT/'scripts/qa_recovery.py',ROOT/'scripts/qa_handoff.py',
        ROOT/'client/playwright.qa.config.ts',ROOT/'client/qa/selection.mjs',
        ROOT/'client/playwright.modules.qa.config.ts',ROOT/'client/qa/module-selection.mjs',
        ROOT/'client/qa/module-selection.node.mjs',
        ROOT/'lab/unix_web_proxy.mjs',ROOT/'scripts/playwright-lab',ROOT/'client/playwright.config.ts',
        ROOT/'client/package.json',ROOT/'client/package-lock.json']+list((ROOT/'client/e2e').glob('*.ts'))
    return {p.relative_to(ROOT).as_posix():cat.digest(p.read_text()) for p in sorted(paths)}


def seal(value:dict) -> dict:
    """Record a content checksum; review/start authorization is a separate operation."""
    value['scope_hash']=cat.digest({k:v for k,v in value.items() if k!='scope_hash'})
    return value


def selected_sets(value:dict, run:str|None=None) -> list:
    """Resolve saved sets after structural validation without expanding scope."""
    validate(value)
    result=[s for s in value['sets'] if run is None or s['name']==run]
    if not result: raise ValueError(f'No queued set: {run}')
    return result


def validate(value:dict) -> None:
    """Reject old formats, modified snapshots, overlapping IDs and invalid batches."""
    if not isinstance(value,dict) or value.get('version')!=2:
        raise ValueError('Expected version 2 module queue; legacy ISO queues cannot be reused')
    if not REV.fullmatch(value.get('target_revision','')):
        raise ValueError('A full target application revision is required')
    if value.get('scope_hash')!=cat.digest({k:v for k,v in value.items() if k!='scope_hash'}):
        raise ValueError('Queue checksum changed; prepare/review a new queue')
    sets=value.get('sets')
    if not isinstance(sets,list) or not sets: raise ValueError('No sets')
    names,assigned=set(),set()
    for s in sets:
        if not isinstance(s,dict):raise ValueError('Set must be an object')
        if not NAME.fullmatch(s.get('name','')) or s['name'] in names:raise ValueError('Invalid/duplicate set name')
        names.add(s['name'])
        if not isinstance(s.get('owner'),str) or not s['owner'].strip():raise ValueError('Owner is required')
        if s.get('purpose') not in ('untested','retest','recheck','investigate'):raise ValueError('Invalid purpose')
        cases=s.get('cases')
        if not isinstance(cases,list) or not cases:raise ValueError('Set has no eligible cases')
        ids=[]
        for c in cases:
            if not isinstance(c,dict) or not cat.CASE_ID.fullmatch(c.get('id','')):raise ValueError('Invalid case')
            if s['purpose']=='investigate' and c.get('status')!='partial':raise ValueError('Investigation requires a partial verdict')
            if c['id'] in assigned:raise ValueError(f"{c['id']}: assigned more than once")
            assigned.add(c['id']);ids.append(c['id'])
            if not c.get('procedure') or not c.get('expectations'):raise ValueError('Incomplete case snapshot')
        flat=[]
        for i,b in enumerate(s.get('batches',[]),1):
            if b.get('id')!=f'{s["name"]}-{i:03}' or not isinstance(b.get('ids'),list) or not 1<=len(b['ids'])<=5:
                raise ValueError('Invalid batch identity/size')
            if any(k not in ids for k in b['ids']):raise ValueError('Batch includes unassigned case')
            if any(c['singleton'] for c in cases if c['id'] in b['ids']) and len(b['ids'])!=1:
                raise ValueError('High-impact case requires its own batch')
            flat.extend(b['ids'])
        if flat!=ids:raise ValueError('Batch order/coverage differs from fixed cases')


def prepare(selections:list[str], catalog:dict, target_revision:str,
            purpose:str='untested', evidence:dict|None=None, cards:dict|None=None) -> dict:
    """Expand module/ID selectors once and snapshot eligible cases plus exclusions."""
    if purpose not in ('untested','recheck','retest','investigate'):raise ValueError('Unknown purpose')
    evidence=evidence or {};cards=cards or {};sets=[]
    registry=coverage.load()['cases']
    if not isinstance(cards,dict) or any(k not in catalog or not isinstance(v,dict) for k,v in cards.items()):
        raise ValueError('Cards must be a dictionary keyed only by current case IDs')
    if evidence:
        spec=importlib.util.spec_from_file_location('ev',Path(__file__).with_name('qa_evidence.py'))
        ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
        evidence=ev.validate_review(dict(version=1,target_revision=target_revision,
            cutoff_approved=all(e.get('cutoff_approved') is True for e in evidence.values()),entries=list(evidence.values())),catalog,target_revision)
    modules={c['module'] for c in catalog.values()}
    for selection in selections:
        parts=selection.split(':')
        if len(parts)!=3:raise ValueError('Use NAME:OWNER:MODULE,ID for --set')
        name,owner,selectors=parts;chosen=set();explicit=set()
        for token in selectors.split(','):
            if token in modules:chosen.update(k for k,c in catalog.items() if c['module']==token)
            elif token in catalog:chosen.add(token);explicit.add(token)
            else:raise ValueError(f'Unknown module/case: {token}')
        cases,excluded=[],[]
        for k,c in catalog.items():
            if k not in chosen:continue
            status=c['status'];record=evidence.get(k)
            reason=status
            accepted=record and record['classification']=='accepted historical coverage'
            retest=record and record['classification']=='retest required' and record.get('fix')
            eligible=(status=='untested' and purpose=='untested' and not accepted)
            eligible|=(purpose=='recheck' and status not in ('needs-decision',) and not accepted)
            eligible|=bool(purpose=='retest' and retest and status!='needs-decision')
            eligible|=(purpose=='investigate' and status=='partial')
            if accepted:reason='accepted historical coverage; '+record['report']
            if not eligible:
                if k in explicit:raise ValueError(f'{k}: ineligible ({reason})')
                excluded.append({'id':k,'reason':reason});continue
            mapping=registry[k]
            if cards.get(k):coverage.validate_card_binding(mapping,cards[k])
            cases.append({'id':k,**c,'reuse':record,'coverage':mapping,'execution':cards.get(k,{})})
        if not cases:raise ValueError(f'{name}: no eligible cases')
        batches=[];pending=[]
        def flush():
            if pending:
                batches.append({'id':f'{name}-{len(batches)+1:03}','ids':list(pending)});pending.clear()
        for c in cases:
            if c['singleton']:
                flush();pending.append(c['id']);flush()
            else:
                pending.append(c['id'])
                if len(pending)==5:flush()
        flush()
        sets.append(dict(name=name,owner=owner,purpose=purpose,modules=sorted({c['module'] for c in cases}),
                         cases=cases,exclusions=excluded,batches=batches))
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    result=seal(dict(version=2,prepared_at=datetime.now(timezone.utc).isoformat(),
                     catalog=str(cat.PLAN.relative_to(ROOT)),source_revision=revision,
                     target_revision=target_revision,references=references(),evidence=evidence,sets=sets))
    validate(result);return result


def check(value:dict,catalog:dict,run:str|None=None,evidence_root:Path=ROOT) -> list[str]:
    """Check full selected source snapshots; never add newly eligible cases."""
    errors=[]
    try:registry=coverage.load()['cases']
    except (ValueError,OSError,KeyError) as exc:return [f'Coverage changed/invalid: {exc}']
    if value.get('references')!=references():errors.append('Specifications/execution rules changed; prepare and review a replacement')
    sets=selected_sets(value,run)
    relevant={c['id'] for s in sets for c in s['cases']}|{c['id'] for s in sets for c in s['exclusions']}
    evidence={k:e for k,e in value.get('evidence',{}).items() if k in relevant}
    if evidence:
        spec=importlib.util.spec_from_file_location('ev',Path(__file__).with_name('qa_evidence.py'))
        ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
        try:
            ev.validate_review(dict(version=1,target_revision=value['target_revision'],
                cutoff_approved=all(e.get('cutoff_approved') is True for e in evidence.values()),entries=list(evidence.values())),
                catalog,value['target_revision'],evidence_root)
        except (ValueError,OSError,KeyError) as exc:errors.append(f'Historical evidence changed/invalid: {exc}')
    for s in sets:
        for saved in s['cases']:
            current=catalog.get(saved['id'])
            original={k:v for k,v in saved.items() if k not in ('id','execution','reuse','coverage')}
            if saved.get('coverage')!=registry.get(saved['id']):errors.append(f"{saved['id']}: coverage changed; review a replacement")
            if saved.get('execution'):
                try:coverage.validate_card_binding(registry[saved['id']],saved['execution'])
                except (ValueError,OSError,KeyError) as exc:errors.append(f"{saved['id']}: adapter binding invalid: {exc}")
            if current!=original:errors.append(f"{saved['id']}: source/procedure/status changed; prepare/review a replacement")
    return errors


def preview(value:dict,run:str|None=None) -> str:
    """Show the entire fixed assignment, including full expectations and readiness gaps."""
    lines=['# Prepared module QA queue','','Waiting for explicit start. No tests have started.',
           f"Target revision: `{value['target_revision']}`; scope: `{value['scope_hash']}`",'']
    for s in selected_sets(value,run):
        if s['purpose']=='investigate':
            lines += ['', 'Investigation only: review source evidence, search duplicate issues and record a linked disposition. No product case execution or PASS promotion.', '']
        lines.extend([f"## {s['name']} — {s['owner']}",'',f"Modules: {', '.join(s['modules'])}; purpose: {s['purpose']}.",
                      'Five batches per session; at most five ordinary IDs per batch.','',
                      '| Batch | Exact IDs |','|---|---|'])
        lines += [f"| {b['id']} | {', '.join(b['ids'])} |" for b in s['batches']]
        lines.extend(['','### Exclusions','']+[f"- {x['id']}: {x['reason']}" for x in s['exclusions']])
        for c in s['cases']:
            lines.extend(['',f"### Card: {c['id']} — {c['title']}",'',
                          f"Historical summary: {cell(c['summary_result'])}; detail: {cell(c['detailed_result'])}.",
                          f"Phase: {c['phase']}; singleton: {c['singleton']}; requirements: {', '.join(c['requirements'])}",
                          f"Source adapter coverage: {c['coverage']['status']} / {c['coverage']['mode']} (not a runtime result).",
                          '', 'Module setup/notes:',c['module_context'],'', 'Prerequisites:', *c['dependencies'],'',c['procedure'],'',
                          'Expected-item evidence checklist:',''])
            lines += [f'- E{i}: {e}' for i,e in enumerate(c['expectations'],1)]
            lines += ['', 'Execution adapter/card (empty means BLOCKED):','```json',json.dumps(c['execution'],indent=2),'```']
        lines += ['','### Global setup and dependency source snapshot','',s['cases'][0]['global_context'],'']
    return '\n'.join(lines)+'\n'


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);cmd=p.add_subparsers(dest='command',required=True)
    prep=cmd.add_parser('prepare');prep.add_argument('--set',dest='selections',action='append',required=True,metavar='NAME:OWNER:MODULE,ID')
    prep.add_argument('--output',type=Path,required=True);prep.add_argument('--target-revision',required=True)
    prep.add_argument('--purpose',choices=['untested','recheck','retest','investigate'],default='untested')
    prep.add_argument('--cards',type=Path);prep.add_argument('--evidence',type=Path)
    for name in ('check','show'):
        sub=cmd.add_parser(name);sub.add_argument('--queue',type=Path,required=True);sub.add_argument('--run')
    a=p.parse_args()
    try:
        if a.command=='prepare':
            if a.output.suffix!='.json':raise ValueError('--output must end in .json')
            md=a.output.with_suffix('.md')
            if a.output.exists() or md.exists():raise ValueError('Queue/preview exists; use a new filename')
            catalog=load_catalog();evidence={}
            if a.evidence:
                spec=importlib.util.spec_from_file_location('evidence',Path(__file__).with_name('qa_evidence.py'))
                ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
                evidence=ev.load_review(a.evidence,catalog,a.target_revision)
            cards=json.loads(a.cards.read_text()) if a.cards else {}
            v=prepare(a.selections,catalog,a.target_revision,a.purpose,evidence,cards)
            a.output.parent.mkdir(parents=True,exist_ok=True)
            a.output.write_text(json.dumps(v,indent=2)+'\n');md.write_text(preview(v))
            print(f'Saved {a.output} and {md}; review both. No tests started.')
        else:
            v=json.loads(a.queue.read_text());validate(v)
            if a.command=='show':print(preview(v,a.run))
            else:
                errors=check(v,load_catalog(),a.run)
                if errors:raise ValueError('\n'.join(errors))
                print('Scope matches. This is not a live start or environment preflight.')
    except (ValueError,OSError,KeyError,TypeError) as exc:p.exit(2,f'qa_queue: {exc}\n')
    return 0
if __name__=='__main__':raise SystemExit(main())
