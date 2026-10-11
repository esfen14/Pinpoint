#!/usr/bin/env python3
"""Render the paper-ready QA case and result tables from the QA source files.

The master plan owns steps and expected results.  The traceability matrix owns
the current status.  Keeping this rendered document derived prevents a paper
table from silently drifting away from the executable QA loop.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "docs" / "qa" / "QA_Test_Plan.md"
TRACEABILITY = ROOT / "docs" / "qa" / "Requirements_Traceability.md"
OUTPUT = ROOT / "docs" / "qa" / "QA_Paper_Test_Case_Tables.md"
ISO_ORDER = (
    ("FS", "Functional Suitability"),
    ("PE", "Performance Efficiency"),
    ("IC", "Interaction Capability"),
    ("RE", "Reliability"),
    ("SE", "Security"),
)
CASE_HEADER = re.compile(r"^#### (?P<id>(?:[JX]\d+|PT)-\d+) (?P<title>.+)$", re.M)
METADATA = re.compile(r"^`\[(?P<iso>FS|PE|IC|RE|SE)\]` · (?P<env>.+?) · (?P<executor>.+?)$", re.M)
FIELD = re.compile(r"^- \*\*(?P<name>Steps|Expect)(?: [^*]*)?:\*\* (?P<value>.+)$", re.M)


def cell(value: str) -> str:
    """Make a source paragraph safe and readable in one Markdown table cell."""
    return " ".join(value.replace("|", "\\|").split())


def cases_from_plan(text: str) -> dict[str, dict[str, str]]:
    headers = list(CASE_HEADER.finditer(text))
    cases: dict[str, dict[str, str]] = {}
    for index, header in enumerate(headers):
        block = text[header.end():headers[index + 1].start() if index + 1 < len(headers) else len(text)]
        metadata = METADATA.search(block)
        fields = {match.group("name"): match.group("value") for match in FIELD.finditer(block)}
        if metadata is None or "Steps" not in fields or "Expect" not in fields:
            raise ValueError(f"{header.group('id')} is missing metadata, Steps, or Expect")
        cases[header.group("id")] = {
            "title": header.group("title"),
            "iso": metadata.group("iso"),
            "environment": metadata.group("env"),
            "executor": metadata.group("executor"),
            "steps": fields["Steps"],
            "expect": fields["Expect"],
        }
    for line in text.splitlines():
        columns = [column.strip() for column in line.split("|")]
        if len(columns) != 7 or not re.fullmatch(r"BB-\d+", columns[1]):
            continue
        paper_case, passes_when, iso, environment = columns[2:-1]
        module, remainder = paper_case.split(": ", 1)
        action, expected = remainder.split(" → ", 1)
        cases[columns[1]] = {
            "title": module,
            "iso": iso,
            "environment": environment,
            "executor": "agent (aggregate)",
            "steps": f"{action}. Aggregate the linked cases: {passes_when}.",
            "expect": expected,
        }
    return cases


def rows_from_traceability(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        columns = [column.strip() for column in line.split("|")]
        if len(columns) != 9 or columns[1] in {"ID", "---", "**Acceptance**"}:
            continue
        case_id, _source, iso, environment, executor, status, notes = columns[1:-1]
        rows[case_id] = {
            "iso": iso,
            "environment": environment,
            "executor": executor,
            "status": status,
            "notes": notes,
        }
    return rows


def render(plan: str, traceability: str) -> str:
    cases = cases_from_plan(plan)
    rows = rows_from_traceability(traceability)
    missing = set(cases) ^ set(rows)
    if missing:
        raise ValueError(f"plan and traceability IDs differ: {', '.join(sorted(missing))}")
    for case_id, case in cases.items():
        if rows[case_id]["iso"] != case["iso"]:
            raise ValueError(f"ISO tag differs for {case_id}")

    out = [
        "# QA Paper Test Case Tables",
        "",
        "These tables are suitable for the paper and for QA execution. They are rendered from",
        "[`QA_Test_Plan.md`](QA_Test_Plan.md) (scenario, action and expected result) and",
        "[`Requirements_Traceability.md`](Requirements_Traceability.md) (current result).",
        "The detailed plan remains the authority for preconditions and full procedure.",
        "",
        "Run `python3 -I scripts/render_qa_case_tables.py --write` after changing either source;",
        "`scripts/verify.sh docs` rejects stale tables.",
        "",
        "## 1. Test cases by ISO/IEC 25010:2023 characteristic",
        "",
        "Each case is listed once under its primary quality characteristic. `VM`, `MOCK` and",
        "`HUMAN` identify the required environment; the executor column identifies who performs it.",
    ]
    for tag, name in ISO_ORDER:
        group = [(case_id, case) for case_id, case in cases.items() if case["iso"] == tag]
        out.extend(["", f"### {tag} — {name}", "", "| Test case | Test scenario | Input / action | Expected output | Environment / executor |", "|---|---|---|---|---|"])
        for case_id, case in group:
            out.append(
                f"| {case_id} | {cell(case['title'])} | {cell(case['steps'])} | "
                f"{cell(case['expect'])} | {cell(case['environment'])} / {cell(case['executor'])} |"
            )

    out.extend([
        "",
        "## 2. Actual QA results by ISO/IEC 25010:2023 characteristic",
        "",
        "This is the result ledger used by the QA loop. `Untested` means no complete observed result has",
        "been recorded yet; it is not a pass. Partial observations remain in the evidence note until the",
        "whole case passes. Valid outcomes are `Pass`, `Fail-filed`, `Blocked`,",
        "`Skipped`, `Needs-decision`, `Won't-do`, and `Retest` (stored in the traceability source",
        "in lowercase). Every Pass must link to sanitized evidence in the Notes column.",
    ])
    for tag, name in ISO_ORDER:
        group = [(case_id, case) for case_id, case in cases.items() if case["iso"] == tag]
        out.extend(["", f"### {tag} — {name}", "", "| Test case | Actual result | Evidence / QA note |", "|---|---|---|"])
        for case_id, case in group:
            row = rows[case_id]
            result = row["status"].replace("-", " ").title()
            note = row["notes"] or "No result recorded yet."
            out.append(f"| {case_id} | {result} | {cell(note)} |")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the rendered table document")
    parser.add_argument("--check", action="store_true", help="fail if the rendered document is stale")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write or --check")
    rendered = render(PLAN.read_text(encoding="utf-8"), TRACEABILITY.read_text(encoding="utf-8"))
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        return 0
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
        print("QA paper test-case tables are stale; run: python3 -I scripts/render_qa_case_tables.py --write")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
