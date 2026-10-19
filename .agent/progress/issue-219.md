# Issue #219: Reject current-password reuse in User Management

Branch: `issue-219-password-reuse`
Status: in-progress

## Finish condition

- [ ] Record tested build, administrator permissions, policy mode and exact manual step (manual evidence pending).
- [ ] Determine the failing flow and retain sanitized evidence: user reports Edit Account accepts the current password.
- [ ] Administrator can set a different compliant temporary password through Edit Account.
- [ ] Old password is refused, temporary password works, and protected routes require a password change.
- [ ] Preserve original manual FAIL and attach a separate new result; cover confirmed regression and run verification.
- [ ] Reject reuse of the target account's current password with a visible warning and no saved changes (user clarification).

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Historical provenance, manual build/permissions/policy and exact failing step | Manual evidence and flow diagnosis | User reports current-password reuse; build/permissions/policy remain unreported |
| Distinct temporary password and forced change | Reset and authentication checks | server/tests/unit/test_password_change.py |
| Current-password reuse rejection and warning | Clarified regression | Backend rejection/atomicity tests and ManageAccountsPage UI retry test |
| Preserve original FAIL and separate results | Evidence preservation | Catalog unchanged; PR reports isolated results separately |
| Verification if a fix is needed | Applicable gates | scripts/verify.sh all and focused tests |
| No live execution by filing alone | Scope boundary | Only isolated tests; no live accounts, appliances or restarts |

## Plan

1. [ ] Add failing backend regressions in `server/tests/unit/test_password_change.py`; verify failure, then add the guard in `server/app/api/user/management.py`.
2. [ ] Add Edit Account error/retry coverage in `client/src/test/ManageAccountsPage.test.tsx`, verify distinct-password login/forced-change behavior, and update owning backend/frontend specs and implementation status.
3. [ ] Run focused tests and `scripts/verify.sh all`; record platform limitations and open a draft PR while manual finish conditions remain unverified.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Inspected issue and user clarification; isolated checkout from origin/main | Existing relevant suite in original checkout | 122 backend + 30 frontend passed; no Edit Account reuse coverage |

## State for the next session

- Last check run (exact command): `git worktree add -b issue-219-password-reuse .worktrees/issue-219 origin/main`
- Result: green; base 3c050ff9b
- Hypothesis: Edit Account lacks the target-user current hash check already used by self-service changes.
- Next action: Add parameterized backend reuse-rejection tests and run them before changing implementation.

## Decisions and notes

- User clarified on 2026-10-19 that entering the current password into NEW PASSWORD and CONFIRM PASSWORD in User Management succeeds and should warn/reject. This authorizes this behavior correction; original unknown-build manual FAIL is preserved.
- Compare against the edited account, including self edits. Historical password tracking is outside this request; no schema/dependency changes.
- No fresh manual appliance execution is authorized or claimed. Keep draft until issue's manual acceptance evidence is supplied.
- Worktree is under `.worktrees/issue-219`; original dirty issue-234 checkout is preserved.
