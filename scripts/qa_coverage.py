#!/usr/bin/env python3
"""Validate source-reviewed case adapters and derive coverage; never execute tests."""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
REGISTRY=ROOT/'docs/qa/automation-coverage.json'
VIEW=ROOT/'docs/qa/Automation_Coverage.md'
spec=importlib.util.spec_from_file_location('catalog',Path(__file__).with_name('qa_catalog.py'))
catalog=importlib.util.module_from_spec(spec);spec.loader.exec_module(catalog)
MODES={'unassigned','scripted automation','AI-assisted browser/API','human manual','mixed'}


def file_hash(path:Path) -> str:
    """Hash exact file bytes, independent of platform newline decoding."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(root:Path,relative:str) -> Path:
    """Require a regular repository file, rejecting escapes and symlink components."""
    if not isinstance(relative,str) or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Invalid coverage source path')
    path=root/relative
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():raise ValueError('Unavailable coverage source')
    if any(p.is_symlink() for p in (path,*path.parents) if p!=root and p.is_relative_to(root)):
        raise ValueError('Symlink coverage source')
    return path


def blank_registry(cases:dict) -> dict:
    """Account for every case without inferring its executor or automation coverage."""
    return dict(version=1,catalog_hash=catalog.digest(cases),cases={k:dict(
        case_hash=catalog.digest(v),status='unmapped',mode='unassigned',
        reason='No source-reviewed current-case adapter; fixture, observations and recovery need assessment.',
        items={},adapter=None,source_hashes={},prerequisites=[],recovery=[])
        for k,v in cases.items()})


def validate(value:dict,cases:dict,root:Path=ROOT) -> None:
    """Reject stale definitions/sources, incomplete claims and unknown evidence items.

    Assertion markers identify reviewed code; they are not formal proof that an
    assertion is correct or evidence that a browser ran. Review and live proof are
    separate gates.
    """
    if not isinstance(value,dict) or value.get('version')!=1:raise ValueError('Expected coverage registry version 1')
    if value.get('catalog_hash')!=catalog.digest(cases):raise ValueError('Coverage catalog changed; review mappings')
    entries=value.get('cases')
    if not isinstance(entries,dict) or set(entries)!=set(cases):raise ValueError('Missing or unknown coverage case IDs')
    for key,record in entries.items():
        if not isinstance(record,dict) or record.get('case_hash')!=catalog.digest(cases[key]):raise ValueError(f'{key}: case changed')
        status=record.get('status');mode=record.get('mode');items=record.get('items')
        expected={f'E{i}' for i in range(1,len(cases[key]['expectations'])+1)}
        if status not in ('unmapped','partial','implemented') or mode not in MODES:raise ValueError(f'{key}: invalid coverage status/mode')
        if not isinstance(record.get('reason'),str) or not record['reason'].strip():raise ValueError(f'{key}: missing assessment reason')
        if not isinstance(items,dict) or set(items)-expected:raise ValueError(f'{key}: unknown expected item')
        if status=='unmapped':
            if items or record.get('adapter') or record.get('source_hashes'):raise ValueError(f'{key}: unmapped case claims coverage')
            continue
        for field in ('reviewed_by','reviewed_at','procedure_review'):
            if not isinstance(record.get(field),str) or not record[field].strip():raise ValueError(f'{key}: missing {field}')
        date.fromisoformat(record['reviewed_at'])
        for field in ('prerequisites','recovery'):
            if not isinstance(record.get(field),list) or not record[field] or not all(isinstance(v,str) and v.strip() for v in record[field]):
                raise ValueError(f'{key}: missing {field}')
        adapter=record.get('adapter')
        if not isinstance(adapter,dict) or set(adapter)!={'path','title','project','config'}:raise ValueError(f'{key}: incomplete adapter')
        if any(not isinstance(v,str) or not v for v in adapter.values()):raise ValueError(f'{key}: missing adapter identity')
        if not adapter['title'].startswith(key+': '):raise ValueError(f'{key}: adapter title must identify current case')
        hashes=record.get('source_hashes')
        if not isinstance(hashes,dict) or not {adapter['path'],adapter['config']}<=set(hashes):raise ValueError(f'{key}: incomplete source hashes')
        for path,digest in hashes.items():
            if file_hash(source_path(root,path))!=digest:raise ValueError(f'{key}: coverage source changed: {path}')
        source=source_path(root,adapter['path']).read_text()
        if source.count(json.dumps(adapter['title']))+source.count("'"+adapter['title']+"'")!=1:
            raise ValueError(f'{key}: title missing or ambiguous in source; verify Playwright collection separately')
        for item,observation in items.items():
            marker=f'qa-evidence:{key}:{item}'
            if (not isinstance(observation,dict) or observation.get('marker')!=marker
                or not isinstance(observation.get('method'),str) or not observation['method'].strip()
                or source.count(marker)!=1):raise ValueError(f'{key}: missing/ambiguous expected-item assertion marker')
        if status=='implemented' and (mode!='scripted automation' or set(items)!=expected):
            raise ValueError(f'{key}: implemented adapter requires every expected item and scripted mode')


def action_for(record:dict) -> list[str]:
    """Describe one exact adapter invocation; do not launch or supply live credentials.

    The isolated launcher does not yet forward current-case selection/artifact
    environment. This vector is an identity constraint for reviewed future cards,
    not proof that live execution is ready.
    """
    adapter=record['adapter']
    path=adapter['path']
    if path.startswith('client/'):path=path[len('client/'):]
    config=adapter['config']
    if config.startswith('client/'):config=config[len('client/'):]
    return ['scripts/playwright-lab',f'--config={config}',f"--project={adapter['project']}",path,
        '--grep=(?:^| )'+re.escape(adapter['title'])+'$', '--workers=1','--retries=0']


def validate_card_binding(record:dict,card:dict,root:Path=ROOT) -> None:
    """Reject stale/partial mappings and cards that select another or broader test."""
    if record.get('status')!='implemented':raise ValueError('No complete source-reviewed adapter; execution card is blocked')
    adapter=record['adapter'];path=root/adapter['path']
    if (card.get('coverage_hash')!=catalog.digest(record) or card.get('selection')!=adapter
        or card.get('mode')!=record['mode'] or not isinstance(card.get('adapter'),str)
        or Path(card['adapter']).resolve()!=path.resolve()
        or card.get('adapter_hash')!=catalog.digest(path.read_text())
        or card.get('actions')!=[action_for(record)]):
        raise ValueError('Execution card differs from exact reviewed coverage/adapter selection')


def load(cases:dict|None=None,path:Path=REGISTRY,root:Path=ROOT) -> dict:
    """Load only a complete, source-current coverage register."""
    if cases is None:cases=catalog.load_catalog()
    value=json.loads(path.read_text());validate(value,cases,root);return value


def render(value:dict,cases:dict) -> str:
    """Render source implementation and missing work separately from runtime verdicts."""
    lines=['# Current-case automation coverage','',
        'Generated from `automation-coverage.json`; source implementation is not a runtime result.',
        'No case is certified PASS here. Human catalog verdicts and historical report credit remain separate.',
        'An implemented adapter still needs reviewed live cards, environment/preflight, exact launcher support and explicit start.',
        'Assertion markers and source hashes support review; they do not prove assertion correctness or live behavior.','',
        '| Case | Module | Source coverage / executor | Adapter | Missing expected items | Next work |',
        '|---|---|---|---|---|---|']
    def cell(text):return ' '.join(str(text).replace('|',r'\|').split())
    for key,case in cases.items():
        record=value['cases'][key];expected={f'E{i}' for i in range(1,len(case['expectations'])+1)}
        adapter=record.get('adapter');link='None'
        if adapter:link=f"[{adapter['title']}](../../{adapter['path']})"
        lines.append(f"| {key} | {case.get('module','—')} | {record['status']} / {record['mode']} | {link} | {', '.join(sorted(expected-set(record['items']))) or 'None in source review'} | {cell(record['reason'])} |")
    lines+=['',f"Source register: {sum(v['status']=='implemented' for v in value['cases'].values())} implemented, "
        f"{sum(v['status']=='partial' for v in value['cases'].values())} partial, "
        f"{sum(v['status']=='unmapped' for v in value['cases'].values())} unmapped (TC and E2E combined; not execution counts).",'']
    return '\n'.join(lines)


def card_template(record:dict) -> dict:
    """Expose reviewed identity, leaving unobserved live readiness explicitly blocked."""
    if record['status']!='implemented':raise ValueError('No source-complete adapter for this case')
    adapter=ROOT/record['adapter']['path']
    return dict(readiness='BLOCKED: launcher integration and reviewed live prerequisites required',
        coverage_hash=catalog.digest(record),selection=record['adapter'],mode=record['mode'],
        adapter=str(adapter),adapter_hash=catalog.digest(adapter.read_text()),actions=[action_for(record)],
        reviewed_by='',timeout_seconds=None,step_timeout_seconds=None,human_required=True,
        prerequisites=[],recovery=record['recovery'],evidence_dir='',write_paths=[])


def main() -> int:
    """Check/render source coverage without importing Playwright or contacting a lab."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','render','show','card-template'])
    parser.add_argument('--write',action='store_true');parser.add_argument('--id')
    args=parser.parse_args()
    try:
        cases=catalog.load_catalog();value=load(cases)
        if args.command in ('show','card-template'):
            if args.id not in cases:raise ValueError('Provide a current case ID')
            record=value['cases'][args.id]
            print(json.dumps(card_template(record) if args.command=='card-template' else record,indent=2));return 0
        if args.command=='render' and args.write:VIEW.write_text(render(value,cases))
        elif not VIEW.exists() or VIEW.read_text()!=render(value,cases):raise ValueError('Derived coverage differs; render --write after review')
        print(f'{len(cases)} coverage records validated; no product tests executed');return 0
    except (ValueError,KeyError,OSError) as error:
        print(f'Coverage error: {error}');return 1


if __name__=='__main__':raise SystemExit(main())
