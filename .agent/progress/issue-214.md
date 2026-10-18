# Issue #214: Prepare current-case adapters for unrun Modules 2–9 cases

Branch: `issue-214-qa-adapters`
Status: in-progress

## Finish condition

- [ ] Review the complete catalog procedure, expected items, prerequisites, and applicable behavioral specifications for each still-unrun case in Modules 2–9: TC-ACC-10, TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03, TC-DASH-07, TC-NH-05, TC-NH-06, TC-NH-07, TC-DI-05, TC-DI-06, TC-DI-07, TC-DI-08, TC-DI-09, TC-DI-11, TC-DI-12, TC-DI-13, TC-DI-14, TC-DI-15, TC-DI-16, TC-DI-17, TC-DI-18, TC-DI-19, TC-ACK-04, TC-ACK-07, TC-ACK-08, TC-HIS-04, TC-DI-10, TC-DASH-09, TC-SS-05, and TC-DASH-06.
- [ ] Add a source-reviewed adapter for each expected item that can be exercised by the supported harness; preserve human-required evidence as an explicit blocker rather than fabricating automation coverage.
- [ ] Add or update focused offline adapter/selection/collection checks so each mapping is tied to its exact case, expected-item assertions, ordered actions, and cleanup behavior.
- [ ] Update automation coverage/readiness documentation and implementation status to distinguish source coverage from live-launch readiness; do not claim runtime acceptance.
- [ ] Produce a new immutable queue at the final tested repository revision that excludes completed TC-ACC-09 and TC-SS-04, preserves historical results, includes exact eligible IDs, full case snapshots, and fixed batches of at most five.
- [ ] Keep the queue execution-only blocked until the live launcher, current lab/preflight facts, case cards, and separate explicit start satisfy `.agent/workflows/qa-run.md`; do not contact or mutate the lab or execute a product case in this issue.
- [ ] `scripts/verify.sh docs` and the relevant focused harness checks pass; record any remaining limitations in the new queue/readiness documentation.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Review all 31 remaining catalog cases and behavioral specifications | 1 | Source review record and coverage mappings |
| Source-map all runnable expected items without claiming live results | 2 | `scripts/qa_coverage.py check`; explicit blocked/human statuses |
| Focused offline checks bind mappings to exact adapters/items/actions/cleanup | 3 | Relevant Node/Python harness checks |
| Keep docs/status aligned on source versus runtime readiness | 4 | `scripts/verify.sh docs` |
| Replace stale queue, preserving result records, excluding completed ACC-09/SS-04 | 5 | `scripts/qa_queue.py check --queue <new queue>` and report links |
| No live case/lab action; queue remains blocked pending separate reviewed start | 6 | Review diff and queue/card readiness fields |
| Relevant gates pass and limitations are recorded | 7 | Focused checks and `scripts/verify.sh docs` |

## Plan

1. [ ] Review all selected case procedures and prerequisite tables, applicable frontend/backend/data/page specifications, existing adapter sources, coverage registry, and status gaps; record exact runnable/human/blocker classifications in a review artifact (`docs/qa/Automation_Readiness.md` or a focused linked document).
2. [ ] Design and implement source adapters plus isolated selection/collection checks for the reviewed runnable cases (`client/e2e/`, `client/qa/`, `client/playwright.qa.config.ts`, focused Node tests); keep tests fail-closed on missing prerequisites and do not connect to a live lab.
3. [ ] Update reviewed case coverage records and derived coverage view (`docs/qa/automation-coverage.json`, `docs/qa/Automation_Coverage.md`) with exact expected-item markers, source hashes, prerequisites and cleanup.
4. [ ] Update QA implementation status and any owning specifications only where adapter/workflow support changes (`spec files/Implementation_Status.md`, relevant QA docs).
5. [ ] Prepare a new immutable explicit-ID queue excluding the two completed cases and record blockers and fixed batches (`docs/qa/queues/`); validate it with the queue checker.
6. [ ] Run the focused offline harness checks and `scripts/verify.sh docs`; update this progress record and checkpoint.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Issue review and full required-source inspection underway | `gh issue view 214 --json number,title,body,url,state,comments` | Issue finish conditions cover requested scope; no source changes yet |

## State for the next session

- Last check run (exact command): `gh issue view 214 --json number,title,body,url,state,comments`
- Result (first failing lines, or "green"): green; issue #214 is open with the copied finish condition.
- Hypothesis: Scope is a test-harness preparation task across 31 cases; only source-mapped assertion coverage can be completed without live lab facts.
- Next action (one specific step, not "continue"): Inspect and classify all 31 case procedures and prerequisites against their owning specifications and existing Playwright sources.

## Decisions and notes

- TC-ACC-09 has a completed supervised PASS in `docs/test-runs/2026-10-18-next-permissions/REPORT.md`; TC-SS-04 has a completed supervised PASS in `docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md`. They must not be replayed as untested cases.
- The earlier prepared queue includes both cases because it lacked reviewer-bound run eligibility input; do not mutate it. Prepare a replacement after adapter/source changes are finalized.
- No lab operation, live browser run, deployment check or execution start is authorized by this issue.
