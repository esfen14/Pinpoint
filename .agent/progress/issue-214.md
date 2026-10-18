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

1. [x] Review all selected case procedures and prerequisite tables, applicable frontend/backend/data/page specifications, existing adapter sources, coverage registry, and status gaps; record per-case source/test/prerequisite/mutation/recovery classifications in `docs/qa/Module_2-9_Adapter_Review.md`.
2. [ ] Design and implement source adapters plus isolated selection/collection checks for all reviewable cases; retain explicit partial/human blockers and never connect a live lab during issue work.
3. [x] Update source coverage for complete mappings plus partial TC-ACC-10, with exact expected-item markers, hashes, prerequisites and recovery; derived view is current.
4. [x] Update QA workflow/readiness/implementation status and fixture plan to distinguish source coverage from live readiness.
5. [x] Prepare replacement immutable queue v4 excluding the two completed cases, with 31 exact IDs, 12 fixed batches, five source-bound blocked cards and fixture blockers.
6. [x] Run the focused offline adapter/selection/collection checks and `scripts/verify.sh docs`; update this progress record and checkpoint after each round. (Repeat for every later adapter round.)

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Read the 31 catalog procedures, phase/prerequisite tables, frontend route map, page requirements, architecture/engineering rules, current status and adapter/coverage constraints; found historical partial-report triage needed for several listed cases | `python3 scripts/qa_catalog.py`; `python3 -I scripts/qa_coverage.py check` | Catalog valid (231 TC/8 E2E, 27 existing verdict conflicts); all 239 coverage records source-current; no product tests executed |
| 2 | Added case-by-case review matrix with source/test references and explicit prerequisite, mutation, and cleanup concerns | `python3 -I scripts/qa_coverage.py check` | Green; existing coverage unchanged. Matrix explicitly notes that the bounded pilot is not a general launcher and no live action is authorized. |
| 3 | Added exact-ID source adapters for TC-ACC-08 and TC-ROL-04, a private-directory selector, isolated Playwright collection config and offline collection checks; updated source coverage and blocked legacy-launch routing | `cd client && node --test qa/module-selection.node.mjs`; `cd client && npx tsc --noEmit -p tsconfig.qa.json`; `python3 -I scripts/qa_coverage.py check` | 5 offline selection/collection checks pass; QA config type-check passes; all 239 coverage records validate. These are adapter checks, not product-case results. No live browser or lab was contacted. |
| 4 | Recorded report-backed PASS exclusions for TC-ACC-09/TC-SS-04 and same-lab read-only host preflight in the adapter review; documented that target revision/baseline and live authorization remain unverified | `scripts/vmlab preflight --json`; `scripts/verify.sh docs` | Host preflight confirms the configured VM UUID is running and host/loopback ownership checks pass; `live_authorized=false`; served app revision/current baseline not established. Docs gate green. No product case executed. |
| 5 | Added read-only source adapters for TC-DI-02 and TC-DI-03; refreshed reviewed coverage hashes; updated readiness and implementation status to distinguish 11 source mappings from live support and retain ACC-09/SS-04 report outcomes | `cd client && node --test qa/module-selection.node.mjs`; `cd client && npx tsc --noEmit -p tsconfig.qa.json`; `python3 -I scripts/qa_coverage.py check`; `git diff --check` | 5 offline selection/collection checks pass; TypeScript QA config passes; 239 coverage records validate (11 implemented, 228 unmapped); whitespace check passes. No product case or browser ran. |
| 6 | Added read-only TC-DASH-07 adapter for no-ping/no-NCPA dashboard state; updated coverage/readiness/status counts and assertion source hashes | `cd client && node --test qa/module-selection.node.mjs`; `cd client && npx tsc --noEmit -p tsconfig.qa.json`; `python3 -I scripts/qa_coverage.py check`; `git diff --check` | 5 offline exact-selection checks pass; TypeScript QA config passes; 239 coverage records validate (12 implemented, 227 unmapped); whitespace check passes. No product case or browser ran. |
| 7 | Used supported read-only pilot inspection with the last reviewed baseline; updated review matrix with exact currently served target and remaining lab fixture/launcher blockers | `scripts/vmlab preflight --json`; `python3 -I scripts/qa_pilot.py inspect --baseline … --control-dir …` | Same UUID running; controlled inspection passed for deployed target `299ab3ba…`; `live_authorized=false`; no product case or transport ran. Current role/device/dashboard fixtures remain unverified. |
| 8 | Prepared the 31-case Module 2–9 v2 queue with 12 fixed batches and linked report-backed PASS outcomes for TC-ACC-09/TC-SS-04 in the adapter review | `python3 -I scripts/qa_queue.py check --queue docs/qa/queues/2026-10-18-modules-2-9-v2.json --run modules-2-9-v2` | Queue scope validates; ACC-09 and SS-04 are not selected. The queue is preparation-only and does not start the live suite. Five cards have source adapters but remain blocked on supported launch integration and reviewed live prerequisites; 26 cases remain unmapped. |
| 9 | Added partial TC-ACC-10 E1/E2 automation with inactive account cleanup and explicit persistent-row/E3 blockers; expanded exact five-module live pilot, module-scoped transport credentials and strict per-item result parsing; added unverified fixture plan and source-bound case-card prerequisites; generated replacement 31-case queue v4 | `python3 -I scripts/qa_coverage.py check`; `python3 -I scripts/test_qa_coverage.py`; `python3 -I scripts/test_qa_results.py`; `python3 -I scripts/test_qa_transport.py`; `python3 -I scripts/test_qa_pilot.py`; `cd client && node --test qa/module-selection.node.mjs`; `cd client && npx tsc --noEmit -p tsconfig.qa.json`; `python3 -I scripts/qa_queue.py check --queue docs/qa/queues/2026-10-18-modules-2-9-v4.json --run modules-2-9-v4`; `scripts/verify.sh docs` | Green at that checkpoint. No product case/browser/lab action ran. Five module cases were dispatchable only with completed cards and separate named start; fixtures remained unverified. |
| 10 | Added complete read-only TC-DI-08 adapter for known TCP, generic TCP, unknown UDP and pin-warning assertions; blocked every port PUT and canceled both dialogs; bound exact private TCP/UDP fixture labels into card and transport preparation; expanded supervised module allowlist to six and regenerated coverage/cards/queue v6 | `cd client && node --test qa/module-selection.node.mjs`; `cd client && npx tsc --noEmit -p tsconfig.qa.json`; `python3 -I scripts/test_qa_results.py`; `python3 -I scripts/test_qa_transport.py`; `python3 -I scripts/qa_coverage.py check`; `python3 -I scripts/qa_queue.py check --queue docs/qa/queues/2026-10-18-modules-2-9-v6.json --run modules-2-9-v6`; `git diff --check`; `scripts/verify.sh docs` | Green. Seven offline selection tests, 15 result parser tests, 11 transport tests, 8 coverage tests and all docs verification contracts pass; QA TypeScript compiles; 239 coverage rows validate; v6 scope matches with 31 IDs/12 batches. No product case/browser/lab action ran. Six complete module cases are dispatchable only with reviewed cards, current fixture/baseline proof and separate named start; fixtures remain unverified. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): green; docs and all included synthetic harness contracts passed.
- Hypothesis: Six complete read-only module mappings are in the exact supervised pilot allowlist and TC-ACC-10 is partial; their lab fixture states are unverified and the 25 other cases lack complete adapters.
- Next action (one specific step, not "continue"): Review the next low-risk read-only current case's exact UI/API behavior and fixture needs, then add its source assertions and fail-closed fixture guard.

## Decisions and notes

- TC-ACC-09 has a completed supervised PASS in `docs/test-runs/2026-10-18-next-permissions/REPORT.md`; TC-SS-04 has a completed supervised PASS in `docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md`. They must not be replayed as untested cases.
- Queue `docs/qa/queues/2026-10-18-modules-2-9-v2.json` explicitly selects 31 IDs and excludes TC-ACC-09/TC-SS-04; their supervised PASS reports are linked in `docs/qa/Module_2-9_Adapter_Review.md`. Historical catalog result cells remain unchanged per workflow.
- Queue `docs/qa/queues/2026-10-18-modules-2-9-v6.json` is the current replacement snapshot after v2-v5 became stale from adapter, coverage, reference and card-template changes. It includes 31 IDs/12 batches, excludes TC-ACC-09 and TC-SS-04, and passes `qa_queue.py check`. Six cards are source-bound but deliberately blocked on live reviewer, fixture observations and output paths. Earlier queue snapshots are immutable historical preparation artifacts; use v6 for further review.
- The current case-card source is `docs/qa/queues/modules-2-9-card-drafts-v3.json`. Six source-complete cards carry exact adapter binding and fixture prerequisites; their live fields remain unset.
- `docs/qa/Module_2-9_Fixture_Plan.md` lists required live state and mutation/recovery boundaries for every queued case. All entries remain unverified. No fixture was created or changed.
- TC-ACC-10 covers E1/E2 only and remains partial; two inactive rows/audit records persist even if cleanup deactivates them. Its E3 no-active-role branch is not covered and it is excluded from live dispatch.
- TC-ACC-10 and TC-DI-10 have earlier partial reports and TC-DI-16–19 have #164 partial reports; the case catalog still says Not run. Queue eligibility and any retest/diagnostic decision must preserve both facts rather than treating the partial report as a pass or silently overwriting it.
- The per-case source/prerequisite/mutation assessment is in `docs/qa/Module_2-9_Adapter_Review.md`; it does not authorize lab access or fixture changes.
- No product case, live browser run, deployment, or execution start has occurred. A host-only read-only preflight is documented; it does not authorize a live start.
