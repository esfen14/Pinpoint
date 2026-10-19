# Issue #219: Reject current-password reuse in User Management

Branch: `issue-219-password-reuse`
Status: in-progress

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
3. [ ] Run focused tests and `scripts/verify.sh all`; record platform limitations and open a draft PR while manual finish conditions remain unverified.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Inspected issue and user clarification; isolated checkout from origin/main | Existing relevant suite in original checkout | 122 backend + 30 frontend passed; no Edit Account reuse coverage |
| 1 | Four reuse tests failed with 200 instead of 400; added target hash guard and UI warning/retry coverage | Focused backend suite; ManageAccountsPage.test.tsx; build; lint | 126 backend and 31 UI tests passed; build passed; lint 0 errors/33 warnings |
| 2 | Updated owning specs and reviewed QA dependency fingerprints (Automation_Readiness.md, automation-coverage.json) | verify.sh all; backend and frontend gates | Windows encoding required explicit -X utf8; docs then correctly rejected changed dependency hashes. Refreshed only after impact review. Frontend QA preflight failed private-mode/symlink checks on Windows; full Vitest 1031 passed/1 existing Add User timeout. Backend gate still running with unrelated failures. |
| 3 | Completed source-binding review; repeated the single timed-out module once | verify.sh docs with -X utf8; ManageAccountsPage.test.tsx; qa_coverage.py check | Docs now reaches QA queue subprocess and fails Windows charmap decoding (child -I ignores UTF-8 environment). Account module 31 passed including existing Add User case. Source coverage validates. Build and lint passed. Full backend results pending; collecting first failure separately. |

## State for the next session

- Last check run (exact command): `.venv/Scripts/python.exe -m pytest tests/unit/test_password_change.py tests/unit/test_auth.py tests/unit/test_management.py tests/unit/test_password_requests.py tests/unit/test_validation.py -q --tb=short` from server/
- Result: green; 126 passed. Account-page suite: 31 passed. Full gate results pending/below.
- Hypothesis: Confirmed missing target hash guard; isolated behavior is corrected. Broader failures need platform/baseline classification.
- Next action: Inspect backend gate completion/first failure and create a draft PR retaining this progress file for manual acceptance and Linux CI.

## Decisions and notes

- User clarified on 2026-10-19 that entering the current password into NEW PASSWORD and CONFIRM PASSWORD in User Management succeeds and should warn/reject. This authorizes this behavior correction; original unknown-build manual FAIL is preserved.
- Compare against the edited account, including self edits. Historical password tracking is outside this request; no schema/dependency changes.
- No fresh manual appliance execution is authorized or claimed. Keep draft until issue's manual acceptance evidence is supplied.
- Worktree is under `.worktrees/issue-219`; original dirty issue-234 checkout is preserved.
- Expanded positive login test initially retained the administrator via the shared app-context fixture; explicitly logging out before target login fixes the test setup. No production login behavior changed.
- Plan expanded to refresh QA source fingerprints because the docs gate binds the changed route/test files; source review is recorded without promoting coverage or live results.
