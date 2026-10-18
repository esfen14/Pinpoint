#!/usr/bin/env python3
"""Validate the current module catalog, source references and reviewed evidence ledger."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('catalog',Path(__file__).with_name('qa_catalog.py'))
cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
SOURCES={'DR':'Display_Requirements.md','DIR':'Device_Inventory_Requirements.md',
         'AHR':'Alerts_Notifications_History_Requirements.md','FMR':'Frontend_Modules_and_Routes.md'}


def validate_source(source:str,root:Path) -> list[str]:
    """Check local owning specifications without treating historical journey IDs as cases."""
    errors=[];spec_dir=(root/'spec files').resolve()
    names=re.findall(r'`?([\w./-]+\.md)(?:#([^`,;|]+))?',source)
    for name,heading in names:
        path=(spec_dir/name).resolve()
        if not path.is_relative_to(spec_dir) or not path.is_file():
            errors.append(f'spec file not found/unsafe: {name}')
        elif heading and heading not in path.read_text():errors.append(f'heading not found: {heading}')
    for token,name in SOURCES.items():
        if re.search(r'\b'+token+r'\b',source) and not (spec_dir/name).is_file():
            errors.append(f'missing source {token}: {name}')
    return errors


def validate(root:Path,text:str) -> list[str]:
    """Validate every definition/requirement and each declared source; return actionable errors."""
    try:cat.parse_catalog(text)
    except ValueError as exc:return [str(exc)]
    errors=[]
    for line in text.split('## Requirements traceability matrix',1)[1].splitlines():
        cells=cat.columns(line) if line.startswith('|') else []
        if cells and cells[0].startswith('REQ-'):
            if len(cells)!=4:errors.append('malformed requirement row');continue
            errors += [f'{cells[0]}: {e}' for e in validate_source(cells[2],root)]
    return errors


def main() -> int:
    errors=validate(ROOT,cat.PLAN.read_text())
    review=ROOT/'docs/qa/historical-evidence-review.json'
    if review.exists():
        import json
        spec=importlib.util.spec_from_file_location('evidence',Path(__file__).with_name('qa_evidence.py'))
        ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
        try:
            value=json.loads(review.read_text());ev.load_review(review,cat.load_catalog(),value['target_revision'])
        except (ValueError,KeyError,OSError) as exc:errors.append(f'Evidence review: {exc}')
    for error in errors:print(error)
    if not errors:print('Module catalog, requirement mappings and reviewed evidence validate')
    return bool(errors)
if __name__=='__main__':raise SystemExit(main())
