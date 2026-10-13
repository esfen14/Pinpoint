# Issue #109: Prevent bootstrap administrator from removing their own administrative access

Branch: `issue-109-bootstrap-admin-lockout`
Status: in-progress

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] The backend rejects changing the bootstrap administrator's role when the resulting permissions would remove administrative access needed to manage accounts and roles; the rejected request leaves account data unchanged.
- [ ] The backend rejects removing the required administrative permissions from the bootstrap administrator's assigned role; the rejected request leaves role data unchanged.
- [ ] Account and role management explain the restriction clearly, and direct API requests cannot bypass it.
- [ ] Regression tests cover both lockout paths, unchanged persisted data after rejection, and permitted account/role edits that preserve administrative access.
- [ ] Update the owning specifications and `spec files/Implementation_Status.md` to document the protection.
- [ ] `scripts/verify.sh all` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Prevent assigning the bootstrap administrator an active role that lacks account/role administration access. | Backend role-change rejection and unchanged account data. | Backend regression cases in `server/tests/unit/test_management.py`; `scripts/verify.sh backend`. |
| Prevent removing account/role administration permissions from the bootstrap administrator's assigned role. | Backend permission-removal rejection and unchanged role data. | Backend regression cases in `server/tests/unit/test_management.py`; `scripts/verify.sh backend`. |
| Explain the restriction before saving in account and role management. | Account and role management explanation. | Frontend regression cases for `ManageAccountsPage` and `ManageRolesPage`; `scripts/verify.sh frontend`. |
| Enforce the restriction against direct API requests. | Both backend rejection items. | Direct Flask client PUT tests in `server/tests/unit/test_management.py`. |
| Allow edits that preserve required administrative access. | Permitted account/role edit regression coverage. | Backend regression cases in `server/tests/unit/test_management.py`. |
| Password recovery behavior is outside this issue. | Deliberately out of scope per issue. | No changes to `recover-bootstrap-admin`; diff review before finish. |
| Keep owning specifications and implementation status current. | Specification finish item. | `scripts/verify.sh docs`. |
| Keep the repository green. | Full-verification finish item. | `scripts/verify.sh all`. |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] Add failing backend regression tests for both lockout paths, unchanged persistence, and permitted edits in `server/tests/unit/test_management.py`; implement the shared required-permission guard and response metadata in `server/app/api/user/management.py`; run the focused test module and `scripts/verify.sh backend`.
2. [ ] Add failing UI regression tests in `client/src/test/ManageAccountsPage.test.tsx` and a focused Manage Roles test; update `client/src/types/user.ts`, `client/src/pages/ManageAccountsPage.tsx`, and `client/src/pages/ManageRolesPage.tsx` to explain and prevent unsafe changes before save; run focused tests and `scripts/verify.sh frontend`.
3. [ ] Update `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`; run `scripts/verify.sh docs`.
4. [ ] Re-read issue #109, map every requirement to observed proof, run the named focused checks and `scripts/verify.sh all`, then complete the PR workflow.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Planning checkpoint only. | Not run yet. | Plan ready; implementation has not started. |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): Not run yet (planning checkpoint).
- Result (first failing lines, or "green"): No check run yet.
- Hypothesis: A shared check for the account/role route permissions can reject unsafe bootstrap-account role assignments and unsafe replacement permission sets before any model mutation.
- Next action (one specific step, not "continue"): Add backend tests in `server/tests/unit/test_management.py` that demonstrate both lockout paths currently succeed when they must return 400 and preserve database state.

## Decisions and notes

- The required permission set is the set used by the account and role management workflows: `account.view`, `account.edit`, `account.info`, `role.view`, `role.edit`, `role.info`, and `role.list`. `account.alerts` and unrelated system/plugin/settings permissions are not required to recover account/role administration.
- The existing user change in `client/src/test/SystemSettingsConflict.test.tsx` predates this issue and must not be included in checkpoints or the pull request.
- Password recovery behavior is explicitly outside issue #109 and will not be changed.
