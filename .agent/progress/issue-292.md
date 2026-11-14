# Issue #292: Inventory missing code documentation and cover it in the Technical Manual

Branch: `sys-missing-docu-inventory` (user instruction: work on the current branch; do NOT commit or push)
Status: in-progress

## Finish condition

- [x] Inventory (file list and counts) committed to `docs/`: `docs/plans/Code_Documentation_Inventory.md`.
- [x] Each undocumented module described, as the module reference section of that file, for the Technical Manual (#181 §3.7). The Technical Manual itself does not exist yet.
- [ ] Follow-up issue for the docstrings opened if approved: NOT opened; needs owner approval.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Inventory of files and counts | item 1 | AST count script; counts in the doc |
| Describe each undocumented module in the Technical Manual | item 2 | 37 rows in the module table; manual does not exist yet |
| Follow-up issue for docstrings if approved | item 3 | left for a person |
| Code is not touched | n/a | `git status` shows only docs |

## Plan

1. [x] Count modules and public names with `ast` (scratch script)
2. [x] Read top-level names of each of the 37 modules
3. [x] Write `docs/plans/Code_Documentation_Inventory.md`
4. [x] `scripts/check_doc_links.py`

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan, counts, inventory doc | `python3 -I scripts/check_doc_links.py .` | 274 docs, links resolve |

## State for the next session

- Last check run: `python3 -I scripts/check_doc_links.py .`; green
- Next action: person decides whether to open the docstring follow-up and where the module reference lives once #181 exists.

## Decisions and notes

- Nothing committed or pushed (user instruction). Delete this file before a ready PR.
- Counts differ from the issue (37 files matches; 217 vs about 225 names) because only top-level public names are counted.
- Module descriptions come from reading top-level names, not every function body; marked for confirmation in the doc.
