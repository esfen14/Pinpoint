#!/usr/bin/env python3
"""Derive a read-only module case/status view; never rewrite human or run results."""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import json

spec=importlib.util.spec_from_file_location('catalog',Path(__file__).with_name('qa_catalog.py'))
cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
ROOT=cat.ROOT;PLAN=cat.PLAN;OUTPUT=ROOT/'docs/qa/QA_Case_Status.md'


def cell(value) -> str:
    """Escape source text, including empty historical result columns, for a table."""
    if value is None:return 'No Result column / no recorded verdict'
    return ' '.join(str(value).replace('|',r'\|').split())


def render(text:str,review:dict|None=None) -> str:
    """Produce original human results and eligibility distinctly from new executions."""
    cases=cat.parse_catalog(text);entries={e['case_id']:e for e in (review or {}).get('entries',[])}
    out=['# Derived black-box case status','','Generated from the module catalog; do not hand-edit.',
         'This is a source/result-conflict view, not a new execution or current-build certification.',
         'Catalog results include human manual confirmations and report-attributed outcomes. Historical reports retain their original executors.',
         'E2E without a detailed Result field is pending/unrecorded, not proof it was never attempted.',
         'Accepted evidence and new execution totals must be reported separately.','',
         f"Source SHA-256: `{cat.digest(text)}`.",
         f"Cases: {sum(k.startswith('TC-') for k in cases)} TC plus {sum(k.startswith('E2E-') for k in cases)} E2E.",
         'Regenerate: `python3 -I scripts/render_qa_case_tables.py --write`.','',
         '| Case | Module / phase | Summary result | Detailed result | Eligibility | Historical evidence |',
         '|---|---|---|---|---|---|']
    for k,c in cases.items():
        e=entries.get(k);note='No reviewed mapping'
        if e:
            name=Path(e['report']).parent.name
            note=f"{e['classification']}: [source report](../test-runs/{name}/REPORT.md)"
            for supporting in e.get('supporting_reports',[]):
                support_name=Path(supporting['report']).parent.name
                note+=f"; supporting: [source report](../test-runs/{support_name}/REPORT.md)"
        out.append('| '+' | '.join(map(cell,[k,f"{c['module']} / {c['phase']}",c['summary_result'],c['detailed_result'],c['status'],note]))+' |')
    return '\n'.join(out)+'\n'


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--write',action='store_true');g.add_argument('--check',action='store_true');a=p.parse_args()
    review=ROOT/'docs/qa/historical-evidence-review.json'
    rendered=render(PLAN.read_text(),json.loads(review.read_text()) if review.exists() else None)
    if a.write:OUTPUT.write_text(rendered);return 0
    if not OUTPUT.exists() or OUTPUT.read_text()!=rendered:
        print('Derived QA status is stale; run python3 -I scripts/render_qa_case_tables.py --write');return 1
    print('Derived module QA status is current');return 0
if __name__=='__main__':raise SystemExit(main())
