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
- [x] Integration or regression tests for workflows in G: isolated regressions and targeted live service acknowledgement/recovery and real-event History browser walk pass (`docs/test-runs/2026-10-14-issue-133-live/REPORT.md`); full manual audit and live edge-case injection not claimed.
- [x] Updated Data_Model_and_Integrations.md, Display_Requirements.md, Alerts_Notifications_History_Requirements.md, Frontend_Modules_and_Routes.md, Implementation_Status.md.
- [x] User-facing documentation: N/A; no separate user guide required by issue.
- [x] `scripts/verify.sh all` output attached to PR as result excerpts in [verification comment](https://github.com/esfen14/Pinpoint/pull/145#issuecomment-6150729909); full local log not uploaded.

### H — Definition of done
- [x] All mandatory acceptance criteria satisfied by isolated tests, audit and targeted live service recovery; backend-dependent gaps tracked separately. Full manual History audit not claimed.
- [x] Required functionality works on synced VM for one real service lifecycle and targeted browser History interactions; see live report.
- [ ] Existing behavior not unintentionally broken in deployment: isolated regressions and targeted browser pass; full live regression breadth not observed.
- [x] Applicable edge cases handled in isolated tests (stale/missing/failed/empty, deleted target, rollback, repeated poll).
- [x] Code follows existing architecture and conventions (source diff; shared history builder).
- [x] No unnecessary duplicate functionality (shared `_new_ack_history` used).
- [x] Relevant lint and static analysis pass (`scripts/verify.sh all`: 0 errors, 26 warnings).
- [ ] No unresolved critical defects: live validation/review needed; #141–#144 are open backend History gaps.
- [x] Required automated tests added or updated (`test_status.py`, `HistoryPage.test.tsx`).
- [x] All applicable automated tests pass (`scripts/verify.sh all`: 2382 backend passed/14 skipped, 518 frontend passed; targeted Playwright 2 passed).
- [x] Relevant integration and regression tests pass: isolated suites and targeted VM/Playwright run passed (report); no claim of all possible live edge cases.
- [x] Test results/evidence attached to PR ([local verification](https://github.com/esfen14/Pinpoint/pull/145#issuecomment-6150729909), [live report/results](https://github.com/esfen14/Pinpoint/pull/145#issuecomment-6158903980)); full local log not uploaded.
- [x] Inputs/config validated for changed logic (fresh status checks; no new config; isolated tests).
- [x] Authorization enforced where required (existing route guards unchanged; `test_dashboard.py`, `test_history.py`, `PageAccess.test.tsx`).
- [x] Sensitive data securely handled (source review: no new logging/secret persistence in changed logic).
- [x] Errors controlled (poll failure/empty/stale and rollback tests).
- [ ] Performance/reliability requirements met in deployment: one live recovery worked, but no timed/repeated load or extended reliability run.
- [x] Technical documentation updated (five specification files and audit).
- [x] User documentation updated if applicable: N/A; issue marks it N/A.
- [x] New configuration parameters documented: N/A; none added.
- [x] Deployment/migration steps documented if applicable: N/A; none required by change.
- [x] PR references #133 (`Closes #133` in PR #145).
- [x] PR describes implementation/testing (PR #145 body and verification comment).
- [ ] Required CI checks pass on current head: previous head passed, but new live-spec/report head `dc628187` has no check conclusions yet.
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
6. [x] With owner approval for VM Playwright in issue comment, inspect current lab ownership/deployment and run targeted live acknowledge → recover → history and real-event History browser checks using `scripts/vmlab` and `scripts/playwright-lab`; add a focused `client/e2e/` spec only if the existing runner cannot prove the workflow; record sanitized `docs/test-runs/<date>-issue-133-live/REPORT.md` and index, update evidence/PR, verify stages. Do not reset/provision the VM without separate explicit approval.

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
| resumed | Owner authorized VM use; synced #133 server/client without reset, checked matching hashes, attempted Playwright admin smoke. | `scripts/playwright-lab --project admin`; private HTTP login probe | Red: Playwright admin login remains `/login`; private stored admin credential returns HTTP 401. Existing database preserved; no History acceptance run. |
| 6 | Owner authorized disposable admin reset; recovered bootstrap via supported CLI, completed forced change through API, ran real web01 SSH failure → ack → recovery and focused History Playwright walk; wrote sanitized report/index and isolated lab spec/config. | `scripts/playwright-lab --project issue-133-live`; `scripts/verify.sh frontend`; `scripts/verify.sh docs` | Initial live spec locator failed on hidden option; refined selector. Green: 2 Playwright passed, frontend/docs OK. DB observed active ack 0, one actorless AUTO_RESOLVED row, unchanged on recheck. |
| 7 | Reverified whole branch and posted live report/results on draft PR; inspected current PR checks/reviews. | `scripts/verify.sh all > /tmp/opencode/issue-133-all-live.log 2>&1; result=$?; grep -E 'passed,|Test Files|Tests  |problems|verify: all' /tmp/opencode/issue-133-all-live.log | tail -10; exit "$result"`; `gh pr view 145 --json ...` | green local all: 2382 backend/14 skipped, 518 frontend, 26 lint warnings/0 errors. Current PR head has no CI conclusions yet and no reviews. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh all > /tmp/opencode/issue-133-all-live.log 2>&1; result=$?; grep -E 'passed,|Test Files|Tests  |problems|verify: all' /tmp/opencode/issue-133-all-live.log | tail -10; exit "$result"`
- Result (first failing lines, or "green"): green — 2382 backend passed, 14 skipped; 518 frontend passed; 0 lint errors/26 warnings; `verify: all OK`. Targeted Playwright 2 passed; report and PR evidence comment posted.
- Hypothesis: Targeted live flow works on #133 source synced into a preserved VM database. Full manual requirement audit, fresh-install/deployment evidence, remote CI on new spec, performance, and human review remain outstanding; #141–#144 are tracked backend gaps. Keep PR draft.
- Next action (one specific step, not "continue"): Observe PR #145 current-head docs/backend/frontend CI conclusions and request a human review; retain draft/progress file until remaining finish-condition evidence is supplied.

## Decisions and notes

- `gh issue view 133` fails because of deprecated projectCards GraphQL; `gh issue view 133 --json title,body,labels,state,comments` succeeds and is the issue text used.
- Specs: Display_Requirements.md §4.9; Data_Model_and_Integrations.md §§Nagios integration, Alert acknowledgement lifecycle; Alerts_Notifications_History_Requirements.md §§1–5. Implementation_Status.md identifies both gaps.
- Section G explicitly calls for live lab and manual walk, but no lab action will be implied by isolated tests. If unavailable, report honestly and use a draft PR.
- CI docs/backend/frontend checks succeeded on PR head `18ca01f3`; no human reviews or comments were present when queried. Recheck CI for this progress-only checkpoint and review state before completion.
- Owner approved VM with Playwright for remaining functionality in issue comment https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6157312406 and added https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6158650087: "Use of the VM is authorized." This answers the lab-use blocker and justifies plan step 6. It does not explicitly authorize destructive `fresh`/`provision --force`. Existing snapshot stamp differs from current installer base-step hash; avoid reset.
- Owner confirmed current host fingerprint from VM console in https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6158435300 and authorized local password use to install public key in https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6158612514. Password was supplied only through a temporary askpass helper (removed on exit), not echoed; key-based SSH now succeeds with checking enabled. Appliance has issue #113 application commit `1ca2c757`, not #133. Pause before sync/reset to avoid overwriting another issue's lab state without exclusive ownership confirmation.
- Owner additionally authorized VM use in https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6158650087. Ran `scripts/vmlab sync --client` on existing VM (no reset); current source and built HTML hashes matched VM after sync. Playwright admin setup failed at login, and private local credential also received API HTTP 401. Current preserved database credentials are out of sync; no live acceptance behavior observed. Need a person for authorized credential recovery or explicit destructive reset.
- Owner authorized resetting disposable lab admin password in https://github.com/esfen14/Pinpoint/issues/133#issuecomment-6158705038. `flask recover-bootstrap-admin` succeeded with a private temporary password; the normal authenticated change-password route completed the forced change. Corrected the private lab admin email from the uniquely identified bootstrap account (the old state email mismatched); values were never printed. Targeted live evidence in `docs/test-runs/2026-10-14-issue-133-live/REPORT.md` with caveat: synced source on preserved issue #113 VM DB, not a clean #133 install; VM Git HEAD remains old despite matching source/build hashes.
- Draft PR: https://github.com/esfen14/Pinpoint/pull/145. `gh pr edit` hits deprecated projectCards GraphQL; body updated via `gh api PATCH`. Backend gaps #141–#144 are tracked out of scope. Local full verification log is `/tmp/opencode/issue-133-all.log`; result excerpts are posted in a PR comment, but the full log is not uploaded.
