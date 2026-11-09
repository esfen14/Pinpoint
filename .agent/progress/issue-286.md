# Issue #286: System Refinement Consolidate the overlapping documents in docs/qa

Branch: `issue-286-consolidate-qa-docs`
Status: in-progress

## Finish condition

- [ ] Keep: QA_Journeys_and_Scope, canonical catalog, QA_Case_Status, QA_Run_Queues, Playwright_Setup, Automation_Readiness
- [ ] Module_2-9_Adapter_Review, Fixture_Plan, Automation_Handoff folded into Automation_Readiness; Automation_Coverage.md stays as generated view
- [ ] Issue_211_Recheck_Review, Next_Permission_Batch_Review, Partial_Pass_Investigations, Historical_Evidence_Review, QA_Report_Timing moved to docs/test-runs/ as dated reports (or conclusions folded into kept docs)
- [ ] Every JSON data file notes the script that regenerates it
- [ ] AGENTS.md routing rows, docs/README.md and spec files/README.md updated
- [ ] Done when: docs/qa has about 6 documents plus data; no broken links; scripts/verify.sh docs passes

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Keep list | item 1 | `ls docs/qa/*.md` |
| Fold 3 docs | item 2 | grep for old names finds no live links; verify.sh docs |
| Move 5 one-off reviews | item 3 | files under docs/test-runs/, index rows; check_doc_links |
| JSON regeneration notes | item 4 | table in Automation_Readiness.md |
| Routing/README updates | item 5 | AGENTS.md, docs/README.md, spec files/README.md diff |
| Done when | item 6 | verify.sh docs |

## Plan

1. [ ] Inventory: for each JSON in docs/qa (and queues/), find the generating script; list live references to every doc being folded/moved (AGENTS.md, qa-run.md, spec files, scripts/qa_queue.py references())
2. [ ] Fold Adapter_Review, Fixture_Plan, Automation_Handoff into Automation_Readiness.md as sections; git rm the three; update links (Automation_Readiness.md, scripts/qa_queue.py references())
3. [ ] Move Issue_211_Recheck_Review, Next_Permission_Batch_Review, Partial_Pass_Investigations, QA_Report_Timing, Historical_Evidence_Review to docs/test-runs/<date>-<slug>/REPORT.md (git mv, fix relative links, add index rows); leave JSON data in docs/qa
4. [ ] Add "Data files and regeneration" table to Automation_Readiness.md
5. [ ] Update links in AGENTS.md, .agent/workflows/qa-run.md, docs/README.md, spec files/README.md, Agent_Workflow_and_CI.md, Implementation_Status.md, docs/test-runs/README.md, QA_Run_Queues.md, scripts/qa_queue.py
6. [ ] scripts/verify.sh docs, then all; delete progress file; open PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan written | - | - |

## State for the next session

- Last check run (exact command): none yet
- Result: n/a
- Hypothesis: docs-only; qa_queue.py references() hashes the folded files and must be edited with them
- Next action: step 1 inventory

## Decisions and notes

- Issue says 16 files; there are 21 in docs/qa. Module_Blackbox_Test_Cases.md and the duplicate catalog belong to #284 (PR #295); queues/ belongs to #285 (PR #296). Not touched here.
- PRs #295/#296 also edit AGENTS.md and docs/README.md: expect merge conflicts in routing rows.
- Test-run reports are never edited after the fact (docs/test-runs/README.md); moved files get only link fixes and a note line.
