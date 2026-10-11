"""Drift check: every traceability-matrix row must reference a real case, spec and heading."""
import re, sys
from pathlib import Path

# Allowed verification statuses in the traceability matrix.
STATUSES = {"pass", "fail-filed", "untested", "needs-decision", "won't-do", "retest"}
# The actual column layout of docs/qa/Requirements_Traceability.md.
COLUMNS = ["ID", "Source Spec/Journey", "ISO Characteristic", "Env",
           "Verification", "Status", "Notes"]


def validate_row(cells, plan_content, spec_dir):
    """Validate a single traceability row. Returns a list of error strings."""
    errors = []
    if len(cells) != len(COLUMNS) + 2:  # leading and trailing '|'
        return [f"malformed row ({len(cells)-2} columns, expected {len(COLUMNS)}): {cells}"]

    case_id, source, iso, env, ver, status, notes = [c.strip() for c in cells[1:-1]]

    if not (f"#### {case_id}" in plan_content or f"| {case_id} |" in plan_content):
        errors.append(f"unknown case {case_id!r}: not present in QA_Test_Plan.md")

    if "#" in source:
        spec_path, heading = source.split("#", 1)
        if not (spec_dir / spec_path).exists():
            errors.append(f"spec file not found: {spec_path!r}")
        elif heading not in (spec_dir / spec_path).read_text():
            errors.append(f"heading not found: {heading!r} in {spec_path!r}")

    if status not in STATUSES:
        errors.append(f"invalid status: {status!r}")
    elif status == "pass" and not notes.strip():
        errors.append(f"pass row for {case_id!r} needs evidence in the notes column")

    return errors


def validate(root, plan_content, trac_content):
    """Validate the traceability matrix against the test plan and spec files."""
    errors = []
    seen_ids = set()
    spec_dir = root / "spec files"

    for i, row in enumerate(trac_content.splitlines()):
        if i < 2 or not row.strip() or not row.startswith("|"):
            continue
        cells = [c.strip() for c in row.split("|")]
        if cells[1] in ("ID", "---", "**Acceptance**"):
            continue

        case_id = cells[1].strip()
        if case_id in seen_ids:
            errors.append(f"duplicate case id: {case_id!r}")
        seen_ids.add(case_id)
        errors.extend(validate_row(cells, plan_content, spec_dir))

    return errors


def main():
    root = Path(__file__).resolve().parent.parent
    trac = root / "docs" / "qa" / "Requirements_Traceability.md"
    plan = root / "docs" / "qa" / "QA_Test_Plan.md"

    errors = validate(root, plan.read_text(), trac.read_text())
    for e in errors:
        print(f"Error: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
