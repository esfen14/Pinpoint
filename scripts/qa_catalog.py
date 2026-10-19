#!/usr/bin/env python3
"""Read the module black-box catalog; preserve human verdicts and reject ambiguity.

Only standard-library parsing and local file reads; never connect to the product.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / 'docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md'
CASE_ID = re.compile(r'(?:TC-[A-Z]+|E2E)-\d{2}')
HEADER = re.compile(r'^#{3,4} (?P<id>(?:TC-[A-Z]+|E2E)-\d{2}) [–—-] (?P<title>.+)$', re.M)


def digest(value) -> str:
    """Hash text or canonical JSON for immutable scope/evidence comparisons."""
    data = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data.encode()).hexdigest()


def columns(line: str) -> list[str]:
    """Split a Markdown table row without splitting escaped pipe characters."""
    return [c.strip().replace(r'\|', '|') for c in re.split(r'(?<!\\)\|', line.strip())[1:-1]]


def expand_ids(value: str, requirement: bool = False) -> list[str]:
    """Expand catalog shorthand and inclusive numeric ranges, retaining order."""
    prefix = r'REQ-[A-Z]+-' if requirement else r'(?:TC-[A-Z]+-|E2E-)'
    token = re.compile(rf'({prefix})(\d+)|\bto\s+(\d+)|(?<=,)\s*(\d+)')
    result, current, previous = [], None, None
    for match in token.finditer(value):
        if match[1]:
            current, number = match[1], int(match[2])
        elif match[3]:
            if current is None or previous is None or int(match[3]) < previous:
                raise ValueError(f'Invalid range: {value}')
            for number in range(previous + 1, int(match[3]) + 1):
                result.append(f'{current}{number:02}')
            previous = int(match[3]); continue
        elif current:
            number = int(match[4])
        else:
            continue
        result.append(f'{current}{number:02}'); previous = number
    return result


def verdict(value: str | None) -> str | None:
    """Normalize only explicit verdict prefixes; free-text observations stay unknown."""
    if value is None: return None
    for token, normalized in [('PARTIALLY PASS','partial'),('Not run','untested'),
                              ('PASS','pass'),('FAIL','fail'),('BLOCKED','blocked')]:
        if re.match(re.escape(token) + r'(?:\b|$)', value, re.I): return normalized
    return 'needs-decision'


def section(body: str, label: str) -> str:
    """Return an explicitly labelled case field without consuming later fields."""
    match = re.search(r'^\*\*' + re.escape(label) + r'\*\*\s*\n(.+?)(?=\n\*\*|\Z)', body, re.M | re.S)
    return match[1].strip() if match else ''


def parse_catalog(text: str) -> dict:
    """Validate definitions, module summaries, run order and requirement coverage."""
    if '## Requirements traceability matrix' not in text:
        raise ValueError('Missing requirements matrix')
    definitions, matrix = text.split('## Requirements traceability matrix', 1)
    headers = list(HEADER.finditer(definitions))
    if not headers: raise ValueError('No TC/E2E definitions')
    global_context = definitions.split('## Test cases:', 1)[0].strip()
    modules = list(re.finditer(r'^### Module (\d+) [–—-] (.+)$', definitions, re.M))
    summaries, phases, dependencies, requirements, e2e_reqs = {}, {}, {}, {}, {}
    order = 0
    for line in definitions.splitlines():
        c = columns(line) if line.startswith('|') else []
        if len(c) in (5,6) and re.fullmatch(r'TC-[A-Z]+-\d{2}', c[0]):
            if c[0] in summaries: raise ValueError(f'Duplicate summary: {c[0]}')
            summaries[c[0]] = c[5] if len(c) == 6 else None
        if len(c) == 3 and c[0].isdigit():
            for case_id in expand_ids(c[2]):
                if case_id in phases: raise ValueError(f'Duplicate phase assignment: {case_id}')
                phases[case_id] = (int(c[0]), order); order += 1
        if len(c) == 3 and c[0].startswith('TC-'):
            for case_id in expand_ids(c[0]):
                dependencies.setdefault(case_id, []).append(line)
        if len(c) == 2 and c[0].startswith('E2E-'):
            e2e_reqs[c[0]] = expand_ids(c[1], True)
    for line in matrix.splitlines():
        c = columns(line) if line.startswith('|') else []
        if len(c) == 4 and c[0].startswith('REQ-'):
            if c[0] in requirements: raise ValueError(f'Duplicate requirement: {c[0]}')
            requirements[c[0]] = {'statement':c[1], 'source':c[2], 'cases':expand_ids(c[3])}
    cases = {}
    for h in headers:
        case_id = h['id']
        if case_id in cases: raise ValueError(f'Duplicate case: {case_id}')
        # End at any peer/parent heading, not at the next case across a module intro.
        rest = definitions[h.end():]
        end = re.search(r'^#{2,4} ', rest, re.M)
        body = rest[:end.start() if end else len(rest)].strip()
        e2e = case_id.startswith('E2E-')
        mod = next((m for m in reversed(modules) if m.start() < h.start()), None)
        summary = summaries.get(case_id)
        result = re.search(r'\*\*Result:\*\*\s*(.*)', body)
        detail = result[1].strip() if result else None
        if not e2e and (case_id not in summaries or detail is None):
            raise ValueError(f'{case_id}: missing summary or detailed Result')
        steps, expected = section(body,'Steps'), section(body,'Expected result')
        if e2e:
            rows = [columns(l) for l in body.splitlines() if l.startswith('|')]
            rows = [r for r in rows if len(r)==3 and r[0].isdigit()]
            steps = '\n'.join(f'{r[0]}. {r[1]}' for r in rows)
            expectations = [f'Step {r[0]}: {r[2]}' for r in rows]
        else:
            expectations = [l[2:].strip() for l in expected.splitlines() if l.startswith('- ')]
        if not steps or not expectations:
            raise ValueError(f'{case_id}: missing steps/expected results')
        priority=re.search(r'\*\*Priority:\*\*\s*([HML])\b',body)
        if not priority:raise ValueError(f'{case_id}: missing priority')
        reqs = e2e_reqs.get(case_id, []) if e2e else expand_ids(body.split('\n',1)[0], True)
        if not reqs: raise ValueError(f'{case_id}: no requirements')
        a,b = verdict(summary),verdict(detail)
        status = (b or 'untested') if e2e else (b if a is None or a == b else 'needs-decision')
        if case_id not in phases: raise ValueError(f'{case_id}: no run phase')
        phase, position = phases[case_id]
        # Conservatively isolate operations whose outcome can affect another case.
        singleton = (e2e or phase in (11,14,15) or case_id == 'TC-NFR-11'
                     or bool(re.search(r'\b(stop|restart|delete|remove|deploy|cancel|disconnect|break|shutdown)\b', steps, re.I)))
        cases[case_id] = dict(title=h['title'], priority=priority[1], module='E2E' if e2e else case_id.split('-')[1],
            module_title='End-to-end' if e2e else mod[2], phase=phase, order=position,
            requirements=reqs, summary_result=summary, detailed_result=detail,
            status=status, steps=steps, expectations=expectations,
            procedure=h[0]+'\n\n'+body, dependencies=dependencies.get(case_id,[]),
            global_context=global_context,
            module_context=(definitions[mod.start():next(x.start() for x in headers if x.start()>mod.start())]
                            if not e2e else 'E2E requires the documented fresh/restored appliance and complete integrated sequence.'),
            singleton=singleton,
            source_hash=digest(text), procedure_hash=digest(body))
    for case_id,rows in dependencies.items():
        if case_id not in cases:raise ValueError(f'Unknown prerequisite owner: {case_id}')
        for row in rows:
            for reference in expand_ids(columns(row)[1]):
                if reference not in cases:raise ValueError(f'{case_id}: unknown prerequisite {reference}')
    if set(summaries) != {k for k in cases if k.startswith('TC-')}:
        raise ValueError('Module summary IDs differ from definitions')
    if set(phases) != set(cases): raise ValueError('Run phase IDs differ from definitions')
    covered = set()
    for req, row in requirements.items():
        if not row['cases'] or any(k not in cases for k in row['cases']):
            raise ValueError(f'{req}: unknown or missing mapped cases')
        for k in row['cases']:
            # Some cases exercise additional requirements declared by the matrix.
            if req not in cases[k]['requirements']: cases[k]['requirements'].append(req)
            covered.add(k)
    if covered != {k for k in cases if k.startswith('TC-')}:
        raise ValueError('Some TC cases lack requirement mappings')
    for k,c in cases.items():
        if any(req not in requirements for req in c['requirements']):
            raise ValueError(f'{k}: unknown requirement')
    return dict(sorted(cases.items(), key=lambda item:item[1]['order']))


def load_catalog(path: Path = PLAN) -> dict:
    """Read current catalog without changing any result or connecting to the lab."""
    return parse_catalog(path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    c = load_catalog()
    print(json.dumps({'cases':len(c), 'tc':sum(k.startswith('TC-') for k in c),
        'e2e':sum(k.startswith('E2E-') for k in c),
        'conflicts':[k for k,v in c.items() if v['status']=='needs-decision']}, indent=2))
