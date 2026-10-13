# Issue #133: Clear acknowledgements on recovery and audit History

Branch: `issue-133-clear-ack-recovery-audit-history`
Status: ready-for-review

## Finish condition

Copied from issue sections E, F, H. Tick only with observed evidence.

### E — Acceptance
- [ ] Recovered service removes active acknowledgement and writes exactly one actorless AUTO_RESOLVED row.
- [ ] Repeated poll writes no further row.
- [ ] Failed or empty poll leaves acknowledgements intact.
- [ ] Still-failing item retains acknowledgement.
- [ ] Acknowledge, unacknowledge and history routes retain behavior.
- [ ] Audit table covers every History requirement with evidence and result.
- [ ] Every page-only gap is fixed and tested.
- [ ] Every backend-dependent gap has a separate linked issue.
- [ ] New HistoryPage test file passes.

### F — Deliverables
- [ ] Updated application source code (section C).
- [ ] New/updated API endpoints with docstrings and permission checks (N/A if no endpoint change).
- [ ] Database migrations (N/A: no model changes planned).
- [ ] Updated frontend components, types and routes (only where a gap requires changes).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under client/src/test/.
- [ ] Integration or regression tests for workflows in G (isolated tests; live run separately).
- [ ] Updated Data_Model_and_Integrations.md, Display_Requirements.md, Alerts_Notifications_History_Requirements.md, Frontend_Modules_and_Routes.md, Implementation_Status.md.
- [ ] User-facing documentation (N/A unless page change needs it).
- [ ] scripts/verify.sh all output attached to PR.

### H — Definition of done
- [ ] All mandatory acceptance criteria satisfied.
- [ ] Required functionality works as specified.
- [ ] Existing behavior not unintentionally broken.
- [ ] Applicable edge cases handled.
- [ ] Code follows existing architecture and conventions.
- [ ] No unnecessary duplicate functionality.
- [ ] Relevant lint and static analysis pass.
- [ ] No unresolved critical defects.
- [ ] Required automated tests added or updated.
- [ ] All applicable automated tests pass.
- [ ] Relevant integration and regression tests pass.
- [ ] Test results/evidence attached to PR.
- [ ] Inputs/config validated.
- [ ] Authorization enforced where required.
- [ ] Sensitive data securely handled.
- [ ] Errors controlled.
- [ ] Performance/reliability requirements met.
- [ ] Technical documentation updated.
- [ ] User documentation updated if applicable.
- [ ] New configuration parameters documented (N/A).
- [ ] Deployment/migration steps documented if applicable (N/A).
- [ ] PR references #133.
- [ ] PR describes implementation/testing.
- [ ] Required CI checks pass.
- [ ] Required reviewer approvals obtained (human after PR).
- [ ] Blocking review comments resolved (human after PR).
- [ ] All applicable acceptance criteria/deliverables complete.

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

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added recovery/safety tests and poll reconciliation with shared dashboard history builder in `test_status.py`, `status.py`, `dashboard.py` | `server/.venv/bin/python -m pytest server/tests/unit/test_status.py -q --tb=short`; `scripts/verify.sh backend` | Red first: 3 expected recovery failures; green: 26 passed, backend 2380 passed/14 skipped |
| 2 | Added `HistoryPage.test.tsx`; enabled sortable supported columns and alert-to-notification link in `HistoryPage.tsx` | `npm run test -- --run src/test/HistoryPage.test.tsx`; `scripts/verify.sh frontend` | Red first: 3 failures (sort/link/test selector), then green: 5 passed, frontend OK (26 warnings) |
| 3 | Audited each History requirement in `docs/test-runs/2026-10-14-issue-133-history-audit/AUDIT.md`; filed #141–#144 for backend gaps | `scripts/verify.sh docs` | green — docs OK |
| 4 | Added no-check/re-failure safety tests; ran route and page guard regressions; updated five specs | `server/.venv/bin/python -m pytest server/tests/unit/test_dashboard.py server/tests/unit/test_status.py server/tests/unit/test_history.py -q --tb=short`; `npm run test -- --run src/test/HistoryPage.test.tsx src/test/PageAccess.test.tsx src/test/App.test.tsx`; `scripts/verify.sh docs` | green — 163 backend, 29 frontend, docs OK |
| 5 | Re-read issue/comments; checked full local CI-equivalent suite; no further code changes | `scripts/verify.sh all > /tmp/opencode/issue-133-all.log 2>&1; tail -30 /tmp/opencode/issue-133-all.log` | green — verify: all OK; 26 lint warnings, zero errors |

## State for the next session

- Last check run (exact command): `scripts/verify.sh all > /tmp/opencode/issue-133-all.log 2>&1; tail -30 /tmp/opencode/issue-133-all.log`
- Result (first failing lines, or "green"): green — verify: all OK; 26 lint warnings, zero errors
- Hypothesis: Backend-dependent history gaps remain open as #141–#144; live lab and reviewer/CI evidence are not available in this session, so PR must stay draft with progress file.
- Next action (one specific step, not "continue"): After a fresh session, re-run full verification and arrange a live appliance walk for acknowledge/recovery/history and History filters, then finish PR review checklist.

## Decisions and notes

- `gh issue view 133` fails because of deprecated projectCards GraphQL; `gh issue view 133 --json title,body,labels,state,comments` succeeds and is the issue text used.
- Specs: Display_Requirements.md §4.9; Data_Model_and_Integrations.md §§Nagios integration, Alert acknowledgement lifecycle; Alerts_Notifications_History_Requirements.md §§1–5. Implementation_Status.md identifies both gaps.
- Section G explicitly calls for live lab and manual walk, but no lab action will be implied by isolated tests. If unavailable, report honestly and use a draft PR.
- H reviewer approvals and CI require people/remote CI and cannot be ticked speculatively.
