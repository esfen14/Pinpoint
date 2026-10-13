# Issue #109: Prevent bootstrap administrator from removing their own administrative access

Branch: `issue-109-bootstrap-admin-lockout`
Status: ready-for-review

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] The backend rejects changing the bootstrap administrator's role when the resulting permissions would remove administrative access needed to manage accounts and roles; the rejected request leaves account data unchanged.
- [x] The backend rejects removing the required administrative permissions from the bootstrap administrator's assigned role; the rejected request leaves role data unchanged.
- [x] Account and role management explain the restriction clearly, and direct API requests cannot bypass it.
- [x] Regression tests cover both lockout paths, unchanged persisted data after rejection, and permitted account/role edits that preserve administrative access.
- [x] Update the owning specifications and `spec files/Implementation_Status.md` to document the protection.
- [x] `scripts/verify.sh all` passes.

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

1. [x] Add failing backend regression tests for both lockout paths, unchanged persistence, and permitted edits in `server/tests/unit/test_management.py`; implement the shared required-permission guard and response metadata in `server/app/api/user/management.py`; run the focused test module and `scripts/verify.sh backend`.
2. [x] Add failing UI regression tests in `client/src/test/ManageAccountsPage.test.tsx` and a focused Manage Roles test; update `client/src/types/user.ts`, `client/src/pages/ManageAccountsPage.tsx`, and `client/src/pages/ManageRolesPage.tsx` to explain and prevent unsafe changes before save; run focused tests and `scripts/verify.sh frontend`.
3. [x] Update `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`; run `scripts/verify.sh docs`.
4. [x] Re-read issue #109, map every requirement to observed proof, run the named focused checks and `scripts/verify.sh all`, then complete the PR workflow.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added backend regression coverage, required-permission guards before mutation, and role-option safety metadata. | `.venv/bin/python -m pytest tests/unit/test_management.py -q`; `scripts/verify.sh backend` | Focused suite: 66 passed. Initial sandboxed backend run: 5 failed / 1 error because sockets and DNS were denied; identical escalated run: 2,337 passed, 14 skipped, backend OK. |
| 2 | Added account-role safety mapping and UI explanation/disabled unsafe options; added locked-role explanation and disabled required permission controls; added focused page tests. | `npm run test -- --run src/test/ManageAccountsPage.test.tsx src/test/ManageRolesPage.test.tsx`; `scripts/verify.sh frontend` | Tests failed first because both protections were absent, then 27 passed; full frontend test/build/lint stage passed with 25 existing warnings. |
| 3 | Documented the backend invariant/response metadata, both pre-save UI protections, and completed implementation status. | `scripts/verify.sh docs` | Green: links, drift checks, QA contracts, and progress validation passed; `verify: docs OK`. |
| 4 | Re-read the unchanged issue and comments, audited every requirement against its proof, and ran the full repository gate. | `scripts/verify.sh all` | Green: docs passed; backend 2,337 passed / 14 skipped; frontend test/build/lint passed with existing non-blocking warnings; `verify: all OK`. |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `scripts/verify.sh all`
- Result (first failing lines, or "green"): Green: `verify: all OK` (backend 2,337 passed, 14 skipped; frontend test/build/lint passed).
- Hypothesis: Every current issue requirement is implemented and proven; the branch is ready for the progress-file removal and pull request.
- Next action (one specific step, not "continue"): Delete this progress file, push the final branch state, and open the issue #109 pull request from the repository template.

## Decisions and notes

- The required permission set is the set used by the account and role management workflows: `account.view`, `account.edit`, `account.info`, `role.view`, `role.edit`, `role.info`, and `role.list`. `account.alerts` and unrelated system/plugin/settings permissions are not required to recover account/role administration.
- The existing user change in `client/src/test/SystemSettingsConflict.test.tsx` predates this issue and must not be included in checkpoints or the pull request.
- Password recovery behavior is explicitly outside issue #109 and will not be changed.
- The first full backend run was sandbox-limited, not a product failure: local socket creation raised `PermissionError` and DNS resolution failed. The same command passed outside the sandbox.
