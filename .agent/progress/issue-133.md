# Issue #133: Clear acknowledgements on recovery and audit History

Branch: `issue-133-clear-ack-recovery-audit-history`
Status: in-progress

## Finish condition

Copied from issue sections E, F, H. Tick only with observed evidence.

### E — Acceptance
- [x] Recovered service removes active acknowledgement and writes exactly one actorless AUTO_RESOLVED row (isolated `test_status.py`; live not run).
- [x] Repeated poll writes no further row (`test_status.py`).
- [x] Failed or empty poll leaves acknowledgements intact (`test_status.py`).
- [x] Still-failing item retains acknowledgement (`test_status.py`).
- [x] Acknowledge, unacknowledge and history routes retain behavior (`test_dashboard.py`, `test_history.py`; live not run).
- [x] Audit table covers every History requirement with evidence and result (`docs/test-runs/2026-10-14-issue-133-history-audit/AUDIT.md`; source review only).
- [x] Every page-only gap is fixed and tested (`HistoryPage.test.tsx`; backend-dependent gaps separately tracked).
- [x] Every backend-dependent gap has a separate linked issue (audit links #141–#144).
- [x] New HistoryPage test file passes (`scripts/verify.sh all`: 518 frontend tests passed).

### F — Deliverables
- [x] Updated application source code (section C): `status.py`, `dashboard.py`, `HistoryPage.tsx`.
- [x] New/updated API endpoints with docstrings and permission checks: N/A; no endpoint changed.
- [x] Database migrations: N/A; no model changes.
- [x] Updated frontend components, types and routes where needed: `HistoryPage.tsx`; types/routes unchanged as not needed.
- [x] Unit tests for new or modified logic (`test_status.py`).
- [x] Frontend interaction tests under client/src/test/ (`HistoryPage.test.tsx`).
- [ ] Integration or regression tests for workflows in G: isolated regression tests pass; live appliance workflow/manual walk outstanding.
- [x] Updated Data_Model_and_Integrations.md, Display_Requirements.md, Alerts_Notifications_History_Requirements.md, Frontend_Modules_and_Routes.md, Implementation_Status.md.
- [x] User-facing documentation: N/A; no separate user guide required by issue.
- [x] `scripts/verify.sh all` output attached to PR as result excerpts in [verification comment](https://github.com/esfen14/Pinpoint/pull/145#issuecomment-6150729909); full local log not uploaded.

### H — Definition of done
- [ ] All mandatory acceptance criteria satisfied end-to-end: isolated E checks pass; live lab pending.
- [ ] Required functionality works as specified in deployment: only isolated tests observed.
- [ ] Existing behavior not unintentionally broken in deployment: regressions pass, live behavior unverified.
- [x] Applicable edge cases handled in isolated tests (stale/missing/failed/empty, deleted target, rollback, repeated poll).
- [x] Code follows existing architecture and conventions (source diff; shared history builder).
- [x] No unnecessary duplicate functionality (shared `_new_ack_history` used).
- [x] Relevant lint and static analysis pass (`scripts/verify.sh all`: 0 errors, 26 warnings).
- [ ] No unresolved critical defects: live validation/review needed; #141–#144 are open backend History gaps.
- [x] Required automated tests added or updated (`test_status.py`, `HistoryPage.test.tsx`).
- [x] All applicable automated tests pass (`scripts/verify.sh all`: 2382 backend passed/14 skipped, 518 frontend passed).
- [ ] Relevant integration and regression tests pass: isolated regressions pass; live lab pending.
- [x] Test results/evidence attached to PR ([verification comment](https://github.com/esfen14/Pinpoint/pull/145#issuecomment-6150729909); full log not attached).
- [x] Inputs/config validated for changed logic (fresh status checks; no new config; isolated tests).
- [x] Authorization enforced where required (existing route guards unchanged; `test_dashboard.py`, `test_history.py`, `PageAccess.test.tsx`).
- [x] Sensitive data securely handled (source review: no new logging/secret persistence in changed logic).
- [x] Errors controlled (poll failure/empty/stale and rollback tests).
- [ ] Performance/reliability requirements met in deployment: isolated safety tests pass; no live observation.
- [x] Technical documentation updated (five specification files and audit).
- [x] User documentation updated if applicable: N/A; issue marks it N/A.
- [x] New configuration parameters documented: N/A; none added.
- [x] Deployment/migration steps documented if applicable: N/A; none required by change.
- [x] PR references #133 (`Closes #133` in PR #145).
- [x] PR describes implementation/testing (PR #145 body and verification comment).
- [x] Required CI checks pass (PR #145 head `18ca01f3`: docs/backend/frontend SUCCESS).
- [ ] Required reviewer approvals obtained: no reviews yet.
- [x] Blocking review comments resolved: none currently present (PR #145 reviews/comments queried); recheck before completion.
- [ ] All applicable acceptance criteria/deliverables complete: live G workflow and review pending.

Requirement coverage (section A problem, C changes, D guidelines, G testing, exclusions and E/F/H):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Stale ack and missing AUTO_RESOLVED; recover host/service atomically, no actor | E recovered service; H functionality/edge cases | test_status.py recovery host/service and rollback tests |
| Repeated, missing/stale, failed, empty polls; deleted target; still-failing retained | E repeated/failed/still-failing; H reliability | test_status.py polling cases |
| Reuse dashboard helpers; unchanged routes and permissions | E route regression; H architecture/security | test_dashboard.py, test_history.py, source inspection |
| Audit each History requirement against page; fix page-only gaps | E audit/page fixes; F frontend | audit table, HistoryPage.test.tsx |
| Backend-dependent History gaps | E backend issues | gh issue links in audit table; backend defects excluded from implementation |
| All History interactions incl permission, Nagios/Pinpoint, filters, pagination, detail, empty/error | E test file; F frontend tests | HistoryPage.test.tsx, PageAccess.test.tsx, App.test.tsx |
| Spec/status updates and verification | F docs/evidence; H docs/testing | docs and scripts/verify.sh docs/all |
| Live lab ack/recover/history and manual History walk | F regression/evidence; H relevant integration/evidence | sanitized docs/test-runs report only if safely run; otherwise draft PR and explicit unverified |
| No dependencies/migrations/new settings/permissions/config changes intended | F N/A entries; H security/config | git diff and applicable tests |
| PR, CI, approvals/review | H PR/review items | gh PR checks and human review; cannot claim before observed |

## Plan

1. [x] Add failing isolated poll lifecycle tests in `server/tests/unit/test_status.py` for host/service recovery, repeat, stale/missing/failed/empty, still failing, deleted target, rollback; implement in `server/app/nagios/status.py` with shared history builder in `server/app/api/system/dashboard.py` or extracted module; verify `test_status.py` then `scripts/verify.sh backend`.
2. [x] Add failing History page interaction tests `client/src/test/HistoryPage.test.tsx` (list, filters, pagination, detail, sources, empty/error, permission), audit `spec files/Alerts_Notifications_History_Requirements.md` against `client/src/pages/HistoryPage.tsx`; fix page-only gaps in page and related frontend code, then verify focused test and `scripts/verify.sh frontend`. Document audit table in `docs/test-runs/` or PR.
3. [x] For backend-dependent audit gaps, search existing issues then file separate issues and link in audit table; preserve backend scope, verify audit table with `scripts/verify.sh docs`.
4. [x] Recheck routes/regressions in `server/tests/unit/test_dashboard.py`, `test_status.py`, `test_history.py` and `client/src/test/PageAccess.test.tsx`, `App.test.tsx`; update specs `spec files/Data_Model_and_Integrations.md`, `Display_Requirements.md`, `Alerts_Notifications_History_Requirements.md`, `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`; verify narrow checks and stage checks.
5. [x] Re-read issue/comments, prove each requirement, run `scripts/verify.sh docs` and `scripts/verify.sh all` once; record real output. If live Nagios/manual lab unavailable or review/CI outstanding, keep progress file and open draft PR; otherwise finish per workflow.
6. [ ] With owner approval for VM Playwright in issue comment, inspect current lab ownership/deployment and run targeted live acknowledge → recover → history and real-event History browser checks using `scripts/vmlab` and `scripts/playwright-lab`; add a focused `client/e2e/` spec only if the existing runner cannot prove the workflow; record sanitized `docs/test-runs/<date>-issue-133-live/REPORT.md` and index, update evidence/PR, verify stages. Do not reset/provision the VM without separate explicit approval.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added recovery/safety tests and poll reconciliation with shared dashboard history builder in `test_status.py`, `status.py`, `dashboard.py` | `server/.venv/bin/python -m pytest server/tests/unit/test_status.py -q --tb=short`; `scripts/verify.sh backend` | Red first: 3 expected recovery failures; green: 26 passed, backend 2380 passed/14 skipped |
| 2 | Added `HistoryPage.test.tsx`; enabled sortable supported columns and alert-to-notification link in `HistoryPage.tsx` | `npm run test -- --run src/test/HistoryPage.test.tsx`; `scripts/verify.sh frontend` | Red first: 3 failures (sort/link/test selector), then green: 5 passed, frontend OK (26 warnings) |
| 3 | Audited each History requirement in `docs/test-runs/2026-10-14-issue-133-history-audit/AUDIT.md`; filed #141–#144 for backend gaps | `scripts/verify.sh docs` | green — docs OK |
| 4 | Added no-check/re-failure safety tests; ran route and page guard regressions; updated five specs | `server/.venv/bin/python -m pytest server/tests/unit/test_dashboard.py server/tests/unit/test_status.py server/tests/unit/test_history.py -q --tb=short`; `npm run test -- --run src/test/HistoryPage.test.tsx src/test/PageAccess.test.tsx src/test/App.test.tsx`; `scripts/verify.sh docs` | green — 163 backend, 29 frontend, docs OK |
| 5 | Re-read issue/comments; checked full local CI-equivalent suite; no further code changes | `scripts/verify.sh all > /tmp/opencode/issue-133-all.log 2>&1; tail -30 /tmp/opencode/issue-133-all.log` | green — verify: all OK; 26 lint warnings, zero errors |
| resumed | Re-read issue and comments; reconciled finish condition with source audit, PR and CI. First check timed out at 120 seconds; reran with 600-second timeout. | `scripts/verify.sh all > /tmp/opencode/issue-133-all.log 2>&1; result=$?; tail -40 /tmp/opencode/issue-133-all.log; exit "$result"` | green — 2382 backend passed/14 skipped; 518 frontend passed; 26 lint warnings/0 errors. CI docs/backend/frontend success on PR head. Live lab/manual walk and human review remain blocked. |
| resumed | Owner issue comment approved VM + Playwright for remaining functionality; added live-verification plan step, not previously available. Existing VM running; five targets up; base snapshot stamp is stale against newer installer base steps. | `scripts/verify.sh all > /tmp/opencode/issue-133-all.log 2>&1; result=$?; tail -40 /tmp/opencode/issue-133-all.log; exit "$result"`; `scripts/vmlab status`; `scripts/vmlab targets up` | green local all; VM running with `os-nagios-ready` snapshot but installer base-step stamp warning. No reset or provision. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh all > /tmp/opencode/issue-133-all.log 2>&1; result=$?; tail -40 /tmp/opencode/issue-133-all.log; exit "$result"`
- Result (first failing lines, or "green"): green — 2382 passed, 14 skipped backend; 518 passed frontend; lint 0 errors/26 warnings; `verify: all OK`. First 120-second attempt timed out; 600-second rerun passed.
- Hypothesis: Isolated tests and CI are green, but the requested live Nagios appliance and real-event History walk require a person/lab. PR must stay draft; #141–#144 are separately filed backend gaps, not implementation in #133.
- Next action (one specific step, not "continue"): Ask the lab owner to perform acknowledge → recover → check History and manually walk filters/details with real events, then provide a sanitized `docs/test-runs/` report and deployment evidence.

## Decisions and notes

- `gh issue view 133` fails because of deprecated projectCards GraphQL; `gh issue view 133 --json title,body,labels,state,comments` succeeds and is the issue text used.
- Specs: Display_Requirements.md §4.9; Data_Model_and_Integrations.md §§Nagios integration, Alert acknowledgement lifecycle; Alerts_Notifications_History_Requirements.md §§1–5. Implementation_Status.md identifies both gaps.
- Section G explicitly calls for live lab and manual walk, but no lab action will be implied by isolated tests. If unavailable, report honestly and use a draft PR.
- CI docs/backend/frontend checks succeeded on PR head `18ca01f3`; no human reviews or comments were present when queried. Recheck CI for this progress-only checkpoint and review state before completion.
- Owner approved VM with Playwright for remaining functionality in issue comment https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6157312406. This answers the prior blocker and justifies plan step 6. It does not explicitly authorize destructive `fresh`/`provision --force`. Existing snapshot stamp differs from current installer base-step hash; inspect running deployment before any sync and avoid reset.
- Draft PR: https://github.com/esfen14/Pinpoint/pull/145. `gh pr edit` hits deprecated projectCards GraphQL; body updated via `gh api PATCH`. Backend gaps #141–#144 are tracked out of scope. Local full verification log is `/tmp/opencode/issue-133-all.log`; result excerpts are posted in a PR comment, but the full log is not uploaded.
