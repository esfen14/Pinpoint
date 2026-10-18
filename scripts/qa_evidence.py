#!/usr/bin/env python3
"""Inventory historical reports and validate explicitly reviewed coverage; never infer PASS."""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
CUTOFF='2026-10-15'
CLASSIFICATIONS={'accepted historical coverage','partial historical coverage','retest required','not applicable'}


def report_path(value:str, root:Path=ROOT) -> Path:
    """Require an existing committed-style report inside the evidence tree, not a traversal/symlink."""
    if not isinstance(value,str):raise ValueError('Report path must be a string')
    p=root/value
    if Path(value).is_absolute() or '..' in Path(value).parts or p.is_symlink():
        raise ValueError('Unsafe report path')
    resolved=p.resolve();base=(root/'docs/test-runs').resolve()
    if not resolved.is_relative_to(base) or resolved.name!='REPORT.md' or not resolved.is_file():
        raise ValueError('Evidence must reference a real docs/test-runs/.../REPORT.md')
    return resolved


def validate_review(value:dict,catalog:dict,target_revision:str,root:Path=ROOT) -> dict:
    """Validate reviewer decisions and complete item-level coverage before queue reuse."""
    if not isinstance(value,dict):raise ValueError('Evidence review must be an object')
    if value.get('version')!=1 or value.get('target_revision')!=target_revision:
        raise ValueError('Evidence review must be version 1 for this exact target revision')
    if not isinstance(value.get('cutoff_approved'),bool):raise ValueError('Record cutoff approval explicitly')
    entries=value.get('entries')
    if not isinstance(entries,list):raise ValueError('Evidence entries must be a list')
    result={}
    for entry in entries:
        k=entry.get('case_id')
        if k not in catalog or k in result:raise ValueError('Unknown/duplicate evidence case')
        if entry.get('classification') not in CLASSIFICATIONS:raise ValueError('Invalid evidence classification')
        if not entry.get('reviewed_by') or not entry.get('impact_review') or not entry.get('reviewed_at'):
            raise ValueError('An attributable compatibility review is required')
        date.fromisoformat(entry['reviewed_at'])
        if entry.get('case_hash')!=catalog[k]['procedure_hash']:raise ValueError('Evidence case changed since review')
        source=report_path(entry.get('report'),root);raw=source.read_bytes();text=raw.decode()
        if entry.get('report_sha256')!=hashlib.sha256(raw).hexdigest():raise ValueError('Evidence report changed')
        tested=entry.get('tested_revision','')
        if not re.fullmatch(r'[0-9a-f]{7,40}',tested) or tested not in text:
            raise ValueError('Tested revision must be present in the report; do not infer from its filename')
        day=date.fromisoformat(entry.get('execution_date',''))
        supporting=entry.get('supporting_reports',[])
        if not isinstance(supporting,list):raise ValueError('Supporting reports must be a list')
        seen_reports={entry['report']}
        for item in supporting:
            if not isinstance(item,dict) or not item.get('relationship','').strip():
                raise ValueError('Each supporting report needs a reason it applies')
            if item.get('report') in seen_reports:raise ValueError('Duplicate primary/supporting report')
            seen_reports.add(item.get('report'))
            supporting_source=report_path(item.get('report'),root)
            supporting_raw=supporting_source.read_bytes();supporting_text=supporting_raw.decode()
            if item.get('report_sha256')!=hashlib.sha256(supporting_raw).hexdigest():
                raise ValueError('Supporting report changed')
            supporting_revision=item.get('tested_revision','')
            if not re.fullmatch(r'[0-9a-f]{7,40}',supporting_revision) or supporting_revision not in supporting_text:
                raise ValueError('Supporting report revision must be present in the report')
            date.fromisoformat(item.get('execution_date',''))
        if entry['classification']=='accepted historical coverage':
            if not value['cutoff_approved']:raise ValueError('Cutoff decision is still provisional')
            if entry.get('catalog_hash')!=catalog[k]['source_hash']:
                raise ValueError('Catalog requirements/prerequisites changed since evidence review')
            if day<date.fromisoformat(CUTOFF) and not entry.get('approved_cutoff_exception'):
                raise ValueError('Pre-cutoff evidence needs an explicit reviewed exception')
            required={f'E{i}' for i in range(1,len(catalog[k]['expectations'])+1)}
            items=entry.get('covered_items',{})
            if set(items)!=required or not all(isinstance(v,str) and v.strip() and v in text for v in items.values()):
                raise ValueError('Full historical credit needs a report excerpt/reference for every expected item')
            if entry.get('environment_compatible') is not True or entry.get('requirements_unchanged') is not True:
                raise ValueError('Environment and requirement compatibility must be explicitly reviewed')
        if entry['classification']=='retest required' and entry.get('fix'):
            fix=entry['fix']
            if not (fix.get('merged') is True and fix.get('finding_closed') is True
                    and re.fullmatch(r'[0-9a-f]{40}',fix.get('merge_sha',''))
                    and re.fullmatch(r'https://github.com/[^/]+/[^/]+/pull/\d+',fix.get('pr',''))
                    and fix.get('issue') and fix.get('timeline_review')):
                raise ValueError('Retest requires reviewed merged product fix and closed finding')
        result[k]={**entry,'cutoff_approved':value['cutoff_approved']}
    return result


def load_review(path:Path,catalog:dict,target_revision:str,root:Path=ROOT) -> dict:
    """Load an explicit evidence-review document, preserving its cutoff decision."""
    return validate_review(json.loads(path.read_text()),catalog,target_revision,root)


def inventory(root:Path=ROOT,cutoff:str=CUTOFF) -> list:
    """List dated candidate reports; filename date is a filter, never compatibility evidence."""
    date.fromisoformat(cutoff);rows=[]
    for p in sorted((root/'docs/test-runs').glob('*/REPORT.md')):
        stamp=p.parent.name[:10]
        try:date.fromisoformat(stamp)
        except ValueError:continue
        if stamp<cutoff:continue
        text=p.read_text();sha=re.findall(r'`([0-9a-f]{7,40})`',text)
        rows.append(dict(report=p.relative_to(root).as_posix(),directory_date=stamp,
                         reported_revisions=list(dict.fromkeys(sha)),
                         report_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                         title=text.splitlines()[0].lstrip('# '),classification='unreviewed candidate'))
    return rows


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cutoff',default=CUTOFF);a=p.parse_args()
    if a.output.exists():p.error('Output exists; preserve previous inventory')
    rows=inventory(cutoff=a.cutoff)
    a.output.write_text(json.dumps({'version':1,'cutoff':a.cutoff,'cutoff_approved':False,'reports':rows},indent=2)+'\n')
    print(f'{len(rows)} candidate reports inventoried. None accepted automatically.')
    return 0
if __name__=='__main__':raise SystemExit(main())
