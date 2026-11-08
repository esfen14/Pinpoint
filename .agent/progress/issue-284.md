# Issue #284: Retire the duplicate black-box catalog and clean up docs/README.md

Branch: `issue-284-retire-duplicate-catalog`
Status: blocked

## Finish condition

- [ ] Inventory of docs/qa/* and docs/qa/queues/* posted on the issue
- [ ] Case-ID diff of both catalogs: nothing only in the old one
- [ ] Module_Blackbox_Test_Cases.md removed
- [ ] Canonical file: QA_Test_Plan.md references -> QA_Journeys_and_Scope.md; personal byline removed
- [ ] docs/README.md has one qa/ row
- [ ] No link points to the removed file; verify.sh docs and test_qa_catalog.py pass
- [ ] scripts/qa_catalog.py unchanged; no file renames

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Inventory posted | item 1 | `gh issue view 284 --comments` |
| Diff by case ID | item 2 | ID comm output (266 vs 266, none only-old) |
| Remove old file | item 3 | `ls docs/qa`; grep for name |
| Fix ref + byline | item 4 | grep QA_Test_Plan / @Raf in canonical |
| One README row | item 5 | docs/README.md |
| Done when | items 6-7 | verify.sh docs; python scripts/test_qa_catalog.py; git diff scripts/ |

## Plan

1. [ ] Post inventory comment on the issue (no files)
2. [ ] git rm docs/qa/Module_Blackbox_Test_Cases.md
3. [ ] Edit canonical catalog (lines 3, 26, 4442; removed-file mentions stay as history)
4. [ ] Edit docs/README.md (merge two qa/ rows)
5. [ ] verify.sh docs, test_qa_catalog.py, then verify.sh all

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | case-ID diff | comm on sorted IDs | 266/266, none only in old |

## State for the next session

- Last check run: ID diff
- Result: green
- Hypothesis: docs-only change
- Last check run: scripts/verify.sh docs -> fails at qa_queue tests: 'Coverage catalog changed; review mappings'
- Done so far: inventory posted; old catalog removed; byline + 2 QA_Test_Plan refs fixed; docs/README.md one qa/ row; QA_Case_Status.md regenerated
- Next action: person decides how to refresh automation-coverage.json catalog/case hashes (see Decisions)

## Decisions and notes

Canonical file mentions the removed file in 3 historical notes ("removed from the repo"); kept as provenance, not links.

Blocked: any edit to the canonical catalog changes source_hash/global_context of all 239 cases, so automation-coverage.json and queues report stale. Precedent: Automation_Readiness.md '2026-10-19 result-only catalog refresh' (verify behavior unchanged, refresh fingerprints, record catalog_result_review). Awaiting owner decision; may be cheaper to batch with other catalog edits.
