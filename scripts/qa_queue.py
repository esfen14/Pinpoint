#!/usr/bin/env python3
"""Prepare and preview fixed ISO-scoped QA sets; never execute tests or claim a lab."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("qa_tables", Path(__file__).with_name("render_qa_case_tables.py"))
tables = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tables)
ISO = dict(tables.ISO_ORDER)
PENDING = {"untested", "retest"}
NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]*")


def load_catalog() -> dict:
    """Read current case procedures and status without changing result artifacts."""
    plan = tables.PLAN.read_text(encoding="utf-8")
    traceability = tables.TRACEABILITY.read_text(encoding="utf-8")
    tables.render(plan, traceability)  # Validate IDs and ISO agreement first.
    cases = tables.cases_from_plan(plan)
    rows = tables.rows_from_traceability(traceability)
    headers = list(tables.CASE_HEADER.finditer(plan))
    for index, header in enumerate(headers):
        block = plan[header.start():headers[index + 1].start() if index + 1 < len(headers) else len(plan)]
        block = block.split("\n### ", 1)[0].strip()
        pre = re.search(r"^- \*\*Pre:\*\* (.+)$", block, re.M)
        cases[header.group("id")]["preconditions"] = pre.group(1) if pre else "Read the full case."
        cases[header.group("id")]["procedure_hash"] = hashlib.sha256(block.encode()).hexdigest()
    for case_id, case in cases.items():
        if case_id.startswith("BB-"):
            case["preconditions"] = case["steps"]
            case["procedure_hash"] = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
        case["status"] = rows[case_id]["status"]
        case["notes"] = rows[case_id]["notes"]
    return cases


def validate(value: dict) -> None:
    """Reject malformed queues, duplicate reservations, and nonpending cases."""
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("Unsupported queue format (expected version 1)")
    sets = value.get("sets")
    if not isinstance(sets, list) or not sets:
        raise ValueError("Queue must contain at least one set")
    names, ids = set(), set()
    for item in sets:
        if not isinstance(item, dict):
            raise ValueError("Each set must be an object")
        name, owner, iso = item.get("name"), item.get("owner"), item.get("iso")
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in names:
            raise ValueError(f"Invalid or duplicate set name: {name!r}")
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError(f"{name}: owner is required")
        if not isinstance(iso, str) or iso not in ISO:
            raise ValueError(f"{name}: unknown ISO characteristic: {iso!r}")
        names.add(name)
        cases = item.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError(f"{name}: no pending cases selected")
        for case in cases:
            if not isinstance(case, dict):
                raise ValueError(f"{name}: each case must be an object")
            case_id = case.get("id")
            if not isinstance(case_id, str) or not re.fullmatch(r"(?:[JX]\d+|PT|BB)-\d+", case_id):
                raise ValueError(f"{name}: invalid case ID: {case_id!r}")
            if case_id in ids:
                raise ValueError(f"{case_id}: assigned more than once in this queue")
            status = case.get("status")
            if case.get("iso") != iso or not isinstance(status, str) or status not in PENDING:
                raise ValueError(f"{case_id}: must be a pending {iso} case")
            ids.add(case_id)


def prepare(selections: list[str], catalog: dict) -> dict:
    """Snapshot named ISO sets, optionally restricted to explicit pending case IDs."""
    sets = []
    for selection in selections:
        parts = selection.split(":")
        if len(parts) not in (3, 4):
            raise ValueError("Use NAME:ISO:OWNER or NAME:ISO:OWNER:ID,ID for each --set")
        name, iso, owner = parts[:3]
        if iso not in ISO:
            raise ValueError(f"Unknown ISO characteristic: {iso!r}; choose {', '.join(ISO)}")
        if len(parts) == 4:
            ids = parts[3].split(",")
            if len(set(ids)) != len(ids):
                raise ValueError(f"{name}: duplicate case ID")
            for case_id in ids:
                if case_id not in catalog:
                    raise ValueError(f"Unknown case: {case_id}")
                if catalog[case_id]["iso"] != iso or catalog[case_id]["status"] not in PENDING:
                    raise ValueError(f"{case_id}: must be a pending {iso} case")
            # Keep master-plan order even if the user lists IDs in another order.
            ids = [case_id for case_id in catalog if case_id in ids]
        else:
            ids = [case_id for case_id, case in catalog.items()
                   if case["iso"] == iso and case["status"] in PENDING]
        sets.append({"name": name, "iso": iso, "owner": owner,
                     "cases": [{"id": case_id, **catalog[case_id]} for case_id in ids]})
    result = {"version": 1, "prepared_at": datetime.now(timezone.utc).isoformat(), "sets": sets}
    validate(result)
    return result


def selected_sets(value: dict, run: str | None = None) -> list[dict]:
    """Validate the saved queue and resolve a specific set without expanding scope."""
    validate(value)
    sets = [item for item in value["sets"] if run is None or item["name"] == run]
    if not sets:
        raise ValueError(f"No queued set named {run!r}")
    return sets


def check(value: dict, catalog: dict, run: str | None = None) -> list[str]:
    """Detect changed procedures, status, or notes for the set about to start."""
    errors = []
    for item in selected_sets(value, run):
        for saved in item["cases"]:
            case_id = saved["id"]
            current = catalog.get(case_id)
            if current is None:
                errors.append(f"{item['name']}: {case_id} no longer exists")
            elif {key: val for key, val in saved.items() if key != "id"} != current:
                errors.append(f"{item['name']}: {case_id} procedure/status/note changed; prepare and review a new queue")
    return errors


def preview_cell(value: str, directory: Path) -> str:
    """Rebase source-document links so a shared preview's evidence links resolve."""
    def replace(match: re.Match) -> str:
        target = urlsplit(match.group(2))
        if target.scheme or target.netloc or not target.path:
            return match.group(0)
        path = (tables.PLAN.parent / unquote(target.path)).resolve()
        relative = os.path.relpath(path, directory.resolve()).replace(" ", "%20")
        if target.fragment:
            relative += "#" + target.fragment
        return match.group(1) + relative + match.group(3)

    return tables.cell(re.sub(r"(\[[^\]]+\]\()([^\)]+)(\))", replace, value))


def preview(value: dict, run: str | None = None, directory: Path = tables.PLAN.parent) -> str:
    """Render a shareable case list, including prerequisites and manual/lab work."""
    lines = ["# Prepared QA queue", "",
             "Waiting for an explicit start command naming the queue and set. No tests have started.", "",
             "Pending cases only (`untested`, `retest`). Sets are listed in queue order;",
             "prerequisites determine which cases can execute. Assignments do not claim the lab.", ""]
    for item in selected_sets(value, run):
        lines.extend([f"## {item['name']} — {item['iso']} / {ISO[item['iso']]}", "",
                      f"Owner: {tables.cell(item['owner'])}. Cases: {len(item['cases'])}.", "",
                      "| Case | Module under test | Scenario | Environment / executor | Status | Prerequisites | Current note |",
                      "|---|---|---|---|---|---|---|"])
        for case in item["cases"]:
            fields = [case["id"], case.get("module", ""), case.get("title", ""),
                      f"{case.get('environment', '')} / {case.get('executor', '')}",
                      case["status"], case.get("preconditions", ""), case.get("notes", "")]
            lines.append("| " + " | ".join(preview_cell(field, directory) for field in fields) + " |")
        lines.append("")
    lines.extend(["Start only the named set after reviewing this list and coordinating lab ownership.",
                  "HUMAN cases require human evidence. Missing prerequisites are not added to the queue automatically."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare", help="save multiple ISO sets and print the full preview")
    prepare_parser.add_argument("--set", action="append", required=True, dest="selections",
                                metavar="NAME:ISO:OWNER[:ID,ID]")
    prepare_parser.add_argument("--output", type=Path, required=True, help="new JSON file; also saves a sibling .md preview")
    for command in ("show", "check"):
        sub = commands.add_parser(command, help="preview saved scope" if command == "show" else "check scope against current sources")
        sub.add_argument("--queue", type=Path, required=True)
        sub.add_argument("--run", help="check or show just this named set")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            if args.output.suffix != ".json":
                raise ValueError("--output must end in .json")
            markdown = args.output.with_suffix(".md")
            if args.output.exists() or markdown.exists():
                raise ValueError("Queue or preview already exists; use a new filename to preserve reviewed scope")
            value = prepare(args.selections, load_catalog())
            rendered = preview(value, directory=args.output.parent)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(value, indent=2) + "\n")
            with markdown.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
            print(rendered, end="")
            print(f"Saved queue: {args.output}; preview: {markdown}")
        else:
            value = json.loads(args.queue.read_text(encoding="utf-8"))
            if args.command == "show":
                print(preview(value, args.run, args.queue.parent), end="")
            else:
                errors = check(value, load_catalog(), args.run)
                if errors:
                    print("\n".join(errors))
                    return 1
                print("Queued scope matches current sources. Await explicit start and environment preflight.")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"qa_queue: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
