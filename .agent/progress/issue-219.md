# Issue #219: Reject current-password reuse in User Management

Branch: `issue-219-password-reuse`
Status: blocked

## Finish condition

- [ ] Record tested build, administrator permissions, policy mode and exact manual step (manual evidence pending).
- [x] Determine the failing flow and retain sanitized evidence: four isolated cases returned 200 before the guard, 400 after it; user reports Edit Account accepts the current password.
- [x] Administrator can set a different compliant temporary password through Edit Account (isolated API proof; live manual acceptance pending).
- [x] Old password is refused, temporary password works, and protected routes require a password change (isolated API proof; live manual acceptance pending).
- [ ] Preserve original manual FAIL and attach a separate new result; cover confirmed regression and run verification.
- [x] Reject reuse of the target account's current password with a visible warning and no saved changes (four backend cases plus UI warning/retry regression).

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Historical provenance, manual build/permissions/policy and exact failing step | Manual evidence and flow diagnosis | User reports current-password reuse; build/permissions/policy remain unreported |
| Distinct temporary password and forced change | Reset and authentication checks | server/tests/unit/test_password_change.py |
| Current-password reuse rejection and warning | Clarified regression | Backend rejection/atomicity tests and ManageAccountsPage UI retry test |
| Preserve original FAIL and separate results | Evidence preservation | Catalog unchanged; PR reports isolated results separately |
| Verification if a fix is needed | Applicable gates | scripts/verify.sh all and focused tests |
| No live execution by filing alone | Scope boundary | Only isolated tests; no live accounts, appliances or restarts |

## Plan

1. [x] Add failing backend regressions in `server/tests/unit/test_password_change.py`; verify failure, then add the guard in `server/app/api/user/management.py`.
2. [x] Add Edit Account error/retry coverage in `client/src/test/ManageAccountsPage.test.tsx`, verify distinct-password login/forced-change behavior, and update owning backend/frontend specs and implementation status.
3. [x] Run focused tests and `scripts/verify.sh all`; record platform limitations and open a draft PR while manual finish conditions remain unverified.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Inspected issue and user clarification; isolated checkout from origin/main | Existing relevant suite in original checkout | 122 backend + 30 frontend passed; no Edit Account reuse coverage |
| 1 | Four reuse tests failed with 200 instead of 400; added target hash guard and UI warning/retry coverage | Focused backend suite; ManageAccountsPage.test.tsx; build; lint | 126 backend and 31 UI tests passed; build passed; lint 0 errors/33 warnings |
| 2 | Updated owning specs and reviewed QA dependency fingerprints (Automation_Readiness.md, automation-coverage.json) | verify.sh all; backend and frontend gates | Windows encoding required explicit -X utf8; docs then correctly rejected changed dependency hashes. Refreshed only after impact review. Frontend QA preflight failed private-mode/symlink checks on Windows; full Vitest 1031 passed/1 existing Add User timeout. Backend gate still running with unrelated failures. |
| 3 | Completed source-binding review; repeated the single timed-out module once | verify.sh docs with -X utf8; ManageAccountsPage.test.tsx; qa_coverage.py check | Docs now reaches QA queue subprocess and fails Windows charmap decoding (child -I ignores UTF-8 environment). Account module 31 passed including existing Add User case. Source coverage validates. Build and lint passed. Full backend results pending; collecting first failure separately. |
| 4 | Completed verification and opened draft PR #262 | verify.sh backend; first failure repeated in original checkout; committed source hash comparison | Backend: 4157 passed, 122 failed, 44 errors, 29 skipped in 1128.92s. Errors include unavailable os.mkfifo on Windows. First failure is test_automation.py::TestSecurityCheck::test_flags_broken_plugins_and_logs_summary, expected (1,2), got (2,2); it also fails in the original checkout without #219. Not every broad failure was individually classified. Committed reviewed hashes match. PR has no CI checks/runs reported. |
| Conflict resume 1 | User requested conflict resolution; merged origin/main 317868099, retaining both QA review notes and independently changed dependency fingerprints | test_auth.py + test_password_change.py; ManageAccountsPage/App/LoginPage Vitest suites; qa_coverage.py check; verify.sh docs | 30 backend and 55 frontend tests passed; all 239 coverage records validate. Docs still hits the previously recorded Windows charmap error in the QA queue subprocess. No application-code conflicts; no behavior change beyond upstream main. |

## State for the next session

- Last check run (exact command): `bash scripts/verify.sh docs` with explicit `python -X utf8` wrapper for python3
- Result: QA queue child CLI still fails Windows charmap decoding. Conflict-resolution checks passed: 30 backend, 55 frontend, 239 coverage records; no conflict markers or whitespace errors.
- Hypothesis: Password reuse correction is verified in isolation; full acceptance is blocked by unavailable Linux gate results and missing identified-build manual evidence.
- Next action: Run `scripts/verify.sh all` on Linux for draft PR https://github.com/esfen14/Pinpoint/pull/262.

## Decisions and notes

- User clarified on 2026-10-19 that entering the current password into NEW PASSWORD and CONFIRM PASSWORD in User Management succeeds and should warn/reject. This authorizes this behavior correction; original unknown-build manual FAIL is preserved.
- Compare against the edited account, including self edits. Historical password tracking is outside this request; no schema/dependency changes.
- No fresh manual appliance execution is authorized or claimed. Keep draft until issue's manual acceptance evidence is supplied.
- Worktree is under `.worktrees/issue-219`; original dirty issue-234 checkout is preserved.
- Expanded positive login test initially retained the administrator via the shared app-context fixture; explicitly logging out before target login fixes the test setup. No production login behavior changed.
- Plan expanded to refresh QA source fingerprints because the docs gate binds the changed route/test files; source review is recorded without promoting coverage or live results.
- Draft PR: https://github.com/esfen14/Pinpoint/pull/262. Keep this file until green gates and the issue's manual finish conditions are proven. GitHub currently reports no runs or checks for this branch; no CI configuration was changed.
- Person needed: supply the identified-build manual reset/reuse result with administrator permissions and policy mode; preserve the original catalog FAIL. No live retest or account modification was performed by this agent.
- Conflict resolution is separately authorized by the user's follow-up; the manual acceptance blocker does not prevent merging main into this issue branch. Both #219 and #222 QA dependency reviews and their source hashes are retained. Full backend suite was not repeated for this metadata-only conflict resolution; affected login/account regressions were rerun instead.
