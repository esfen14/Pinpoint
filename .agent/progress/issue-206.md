# Issue #206: Module-based black-box QA readiness tooling

Branch: `issue-206-qa-readiness`
Status: in-progress

## Finish condition

- [x] Parse/validate 231 TC and 8 E2E cases, requirements, prerequisites and conflicting results.
- [x] Versioned module/person queues with explicit IDs, exclusions, batches, freshness, historical evidence and execution cards.
- [x] Enforce execution-state start/owner/scope/budgets/adapters/evidence/recovery offline; no live QA.
- [x] Inventory/link historical candidates without automatic PASS or invented provenance.
- [x] Migrate legacy validators/rendering/docs links without weakening coverage or rewriting historical outcomes.
- [x] Update reports/workflows/specs and pass isolated checks/docs gate.
- [x] Open reviewable PR with pending human decisions, adapter coverage and separately gated live work.

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Catalog/queues | First two items | Parser/queue isolated regression tests and real catalog check |
| Execution constraints | Third item | Offline state/adapter/budget/evidence rejection tests |
| Reuse | Fourth item | Candidate inventory, evidence validation and regression tests |
| Migration | Fifth item | Traceability/render/link validators and docs gate |
| Records and review | Last two items | Report schema, specifications, PR and CI |

## Plan

1. [x] Add shared catalog parser/tests in `scripts/qa_catalog.py`, `scripts/test_qa_catalog.py`.
2. [x] Migrate `scripts/qa_queue.py` and queue tests; add reviewed-evidence validation and historical inventory.
3. [x] Add offline execution-state/card/result validation and tests; do not launch labs or unmapped browser tests.
4. [x] Migrate traceability/rendering/tests/report templates/documentation links and specifications; verify docs.
5. [x] Review finish condition, verify required gates, checkpoint and open PR with explicit remaining live work.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 5 | Self-review added stale accepted-evidence checks (including excluded cases), normative/harness fingerprints, blocked-slot accounting, priority/module context and actual five-batch exhaustion tests | Final `scripts/verify.sh docs`; Python syntax; `git diff --check`; `scripts/verify.sh all` running | Docs green with 66 isolated checks after rejecting unknown prerequisite IDs; full local gate passes: 4310 backend/14 skips, 1003 frontend, build/lint zero errors; no live QA |
| 4 | Migrated source/derived/evidence validators and tests, fixed current/historical links, updated report templates/workflows/specs and docs gate | `scripts/verify.sh docs` | Green: all links and 61 isolated checks pass; no live operations |
| 3 | Added offline session/card/evidence validator with explicit start/owner checks, bounded batches, unchanged adapters, exact action slots and cleanup halt | `python3 -I scripts/test_qa_execute.py` | 7 tests pass; no dispatcher/subprocess exists; live preflight and recovery remain separately gated |
| 2 | Migrated module/person queue v2 and reviewer-bound evidence validation; inventoried 41 reports and attached six partial candidate mappings | `python3 -I scripts/test_qa_queue.py`; `python3 -I scripts/test_qa_evidence.py` | 8 queue and 3 evidence tests pass; no historical PASS inferred; docs migration remains round 4 |
| 1 | Added shared catalog parser with shorthand phase expansion, 239 definitions, complete procedures/expectations and result-conflict handling | `python3 -I scripts/test_qa_catalog.py`; `python3 -I scripts/qa_catalog.py` | 4 tests pass; 231 TC/8 E2E; 26 conflicts plus one free-text verdict flagged; docs gate migration remains step 4 |
| Plan | Copied approved local documentation/catalog transition into isolated issue checkout; recorded implementation plan | `gh issue view 206 --json body --jq .body` | Finish condition covers offline readiness; no live operations authorized |

## Partial-pass follow-up session (2026-10-18)

User addition: investigate partial passes so issues can be filed.

1. [x] Review all human partial verdicts, source/spec evidence and existing issues.
2. [x] File attributed acknowledgement confirmation defect [#208](https://github.com/esfen14/Pinpoint/issues/208) and missing-observation clarification [#209](https://github.com/esfen14/Pinpoint/issues/209).
3. [x] Add review-only `investigate` queues, partial-only validation, executor rejection and mandatory linked dispositions; preserve the catalog.
4. [x] Verify docs gate, selection/conflict/tampering and execution rejection checks; no live QA.
5. [x] Checkpoint/push to PR #207. Final-head CI status is recorded in the PR; inspect it before merging.

Follow-up round 1: docs gate passes with 68 isolated checks (including two new
regressions); `git diff --check` passes. ACK source corroborates the human note;
REM has no stated failing expectation and is not asserted to be a permission bug.
Prior full product checks and CI passed at `9e8d7f1`; the new-head CI must be
checked separately. Both investigation issues retain unknown original provenance
and require separately authorized live evidence where needed.

## State for the next session

- Last relevant checks: `scripts/verify.sh docs` (77 isolated checks) and `scripts/verify.sh frontend` (1003 Vitest tests, five offline Node/Playwright collection checks, QA type check, build/lint; zero errors and 33 existing warnings). Both green.
- Full check: `scripts/verify.sh all > /tmp/issue-206-coverage-all.log 2>&1` running at the coverage checkpoint. Final result and current-head CI proof are maintained in draft PR #207, not inferred from an earlier revision.
- Result: five source-complete permission adapters, 234 explicitly unmapped definitions. Source registry, exact selection, draft-card blocking and queue/journal bindings pass isolated checks. No live browser/lab test executed. Initial partial triage remains #208/#209; original human catalog unchanged.
- Next action: inspect final PR CI/full-gate proof, then implement reviewed current-case selection/private artifact integration in the isolated launcher with ownership, target-version and recovery enforcement. Actual live cards/preflight, atomic scan guarding and pilot execution still require their separate reviewed scope/start.

## Decisions and notes

- October 15 cutoff remains provisional. Preserve catalog human verdicts; reports retain original executor attribution.
- No product code, lab access, production discovery, installer work or live test execution in this issue.
- Existing related owner changes were copied, not moved; original checkout stays untouched.
- Overall readiness plan remains `.agent/progress/ai-testing-readiness.md`; this file tracks the authorized offline implementation milestone.

- The last hardening check rejects unknown prerequisite references instead of silently ignoring them. Local full-gate product tests ran against unchanged product source; the final QA-only parser change passed the rerun docs gate.

## Readiness checklist audit (2026-10-18)

- User asked whether the entire readiness plan was complete and to check applicable items.
- Checked completed offline tasks against source, tests and reporting rules; split aggregate requirements where live enforcement/cards remain missing. The full plan is not complete.
- Refreshed stack/status descriptions and synchronized the overall plan and this progress file into the original checkout for visibility. Implementation remains in the isolated checkout.
- `scripts/verify.sh docs` and `git diff --check` pass. At pre-checkpoint head `9828931`, docs and frontend CI passed; backend was still running. New-head CI remains separate. No live tests or product changes.
- Next work: selected-case coverage/cards and evidence/ambiguity review, then live boundaries/recovery and a separately started pilot.

## Coverage/adapters implementation session (2026-10-18)

Scope: continue the approved offline readiness work; no lab connection, test launch
against an application, account setup or product behavior change.

1. [x] Add a source-bound coverage registry/validator and derived all-case matrix in `scripts/qa_coverage.py`, regression tests and `docs/qa/automation-coverage.json` / `Automation_Coverage.md`. Unknown coverage stays explicitly unmapped; partial coverage cannot become whole-case automation.
2. [x] Add reviewed source adapters for Staff permission cases (SS-04, HIS-01, RPT-07, LOG-05, PLG-07), with isolated exact-selection Playwright configuration, no setup dependencies/retries/captures, and per-item evidence. Validate registration with offline `--list`, never a browser launch. Existing human passes stay excluded by normal queue eligibility.
3. [x] Bind queue snapshots/freshness to coverage metadata and reject mismatched adapter cards; include registry checks in the docs gate, document source implementation versus live readiness, and update the overall checklist. Complete live cards still require verified prerequisites/environment and a supported reviewed launcher.
4. [x] Verify docs and relevant frontend checks, inspect CI status and checkpoint to draft PR #207; synchronize the main-checkout progress copies. Full-gate/current-head CI proof is recorded in the PR before completion.

Next action: round 1 failing coverage registry contracts, then implement validation.

Coverage round 1: five isolated coverage contracts pass; the first run failed
because `qa_coverage.py` did not exist, then the implementation passed. All 239
records currently remain unmapped until the next source-review round.
`python3 -I scripts/qa_coverage.py render --write` generated the matrix; no runtime
verdict was changed. Next action: source permission adapters and offline collection.

Coverage rounds 2–3: frontend gate passes (1003 Vitest tests, five Node selection/
Playwright-list checks, QA type check, build and lint with zero errors/33 existing
warnings). Initial exact collection found zero tests because Playwright matches
full titles; the bounded title matcher was corrected and actual collection now
proves exact selection. A Node test filename was changed to `.node.mjs` so Vitest
does not collect it as a Vitest suite; it remains explicitly required in the
frontend gate. Registry reports five source-complete/234 unmapped definitions.
Card binding rejects wrong source/mode/selection/argv; template cards remain
blocked. A new regression first demonstrated PASS without recorded actions, then
the journal was hardened to require every approved action slot.
`python3 -I scripts/test_qa_coverage.py` (7), queue (12), executor (11) pass.
`verify.sh docs` passes with 77 isolated checks.

No live browser was launched. The existing launcher does not forward the new
selection/output environment or mount its private artifacts; all actual live
cards and deployment/ownership/recovery proof remain pending.

Next action: run final local verification, checkpoint and inspect current-head CI.

Coverage checkpoint: relevant docs/frontend checks pass; full local gate and
current-head CI are running. New source tests, coverage register and guide are
committed in #207. Progress copies are synchronized into the original checkout;
implementation source remains isolated. Final green proof must be checked in
the PR rather than inferred from this checkpoint.

## Transport preparation session (2026-10-18)

User requested continuation. Inspection confirms the journal deliberately rejects
live authorization; it cannot be promoted into a dispatcher by passing environment
variables. Continue the transport portion offline, without lab or credential reads.

1. [ ] Add `scripts/qa_transport.py` and isolated contracts for a queue/journal-bound transport preview: exact current case, immutable sources, unconsumed action slot, fresh offline attestations, private fresh artifact path, read-only sources and minimal credential mounts. No subprocess/live dispatch or authorization from previews.
2. [ ] Add `scripts/playwright-lab --qa-preview QUEUE JOURNAL STATE_DIR BRIDGE_DIR`; reject current-case config/environment bypasses in the legacy execution path before Docker/socket/credential work. Exercise the shell entry with fake commands only.
3. [ ] Wire docs-gate checks, fingerprint transport sources, update workflow/status/readiness docs and progress, verify and checkpoint to draft PR #207. Live preflight, ownership lock/deployed version proof, recovery supervisor and explicit started live cards remain pending.

Next action: failing transport validation tests, then smallest implementation.
