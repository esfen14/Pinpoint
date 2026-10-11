# Issue #72: Prevent the super admin (first account) from being set to Suspended or Inactive

Branch: `issue-72-prevent-super-admin-lockout`
Status: in-progress

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] The first account (super admin) cannot be set to Suspended or Inactive. The update route returns a 400 with a clear message.
- [ ] Any other route or helper that changes `User.Status` applies the same guard.
- [ ] The Users edit form disables or hides those status options for the super admin.
- [ ] Backend tests cover the rejected status change and an allowed edit of other fields on that account.
- [ ] `spec files/Backend_Modules_and_Routes.md` and `spec files/Implementation_Status.md` are updated.
- [ ] `scripts/verify.sh all` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| An administrator cannot suspend or inactivate the first account. | 1 | `server/tests/unit/test_management.py::TestEditAccount` |
| The rejection is a clear 400 error. | 1 | `server/tests/unit/test_management.py::TestEditAccount` |
| Every application status-changing path has the guard. | 2 | `rg` audit of `server/app` plus management-route tests |
| The account can still be edited without a status change. | 4 | `server/tests/unit/test_management.py::TestEditAccount` |
| The edit form prevents the invalid status choice for the super admin. | 3 | `client/src/test/ManageAccountsPage.test.tsx` |
| Backend-route and implementation-status specifications are current. | 5 | `scripts/verify.sh docs` |
| Full CI-equivalent verification passes. | 6 | `scripts/verify.sh all` |

## Plan

1. [x] Add precise backend regression coverage in `server/tests/unit/test_management.py` for both rejected super-admin status values, their message, and a non-status edit of the same account; run the focused test.
2. [x] Add UI regression coverage in `client/src/test/ManageAccountsPage.test.tsx` for the disabled super-admin status control; run the focused frontend test.
3. [x] Audit every `User.Status` mutation in `server/app/` and confirm the account update route is the only mutable application path; record the result and run the narrow backend/frontend checks.
4. [ ] Update `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md` to document the shipped super-admin guard; run `scripts/verify.sh docs`.
5. [ ] Re-read issue #72 and its comments, verify every finish-condition item with current evidence, then run `scripts/verify.sh all`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Inspected current `origin/main`; the server guard and disabled selector are already present, but targeted regression evidence and documentation are incomplete. | Source inspection and issue read | Plan created; no code changed. |
| 1 | Added parameterized rejected-status assertions (including the response message) and an allowed non-status edit for the first account. | `cd server && ./.venv/bin/python -m pytest tests/unit/test_management.py::TestEditAccount -q` | 8 passed. |
| 2 | Added a super-admin API fixture and UI assertion; associated the Status label with its select after the new accessibility-aware test first failed. | `cd client && npm run test -- ManageAccountsPage.test.tsx` | 25 passed. |
| 3 | Audited application `User.Status` assignments; only the guarded account-update route mutates an existing user's status. | Focused backend and frontend regression tests | 8 backend tests and 25 frontend tests passed. |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `cd server && ./.venv/bin/python -m pytest tests/unit/test_management.py::TestEditAccount -q; cd ../client && npm run test -- ManageAccountsPage.test.tsx`
- Result (first failing lines, or "green"): green — backend 8 passed in 2.06s; frontend 25 passed in 2.64s.
- Hypothesis: The status guard's route/UI contract is proven; the owning specifications and implementation inventory need explicit coverage before docs verification.
- Next action (one specific step, not "continue"): Document the super-admin `is_super_admin` account field, status-update guard, and disabled edit-form behavior in the owning specifications and implementation status.

## Decisions and notes

- `gh issue view 72` currently fails because GitHub's GraphQL response includes a deprecated Projects classic field. The issue and comments were read through `gh api repos/{owner}/{repo}/issues/72` and its `/comments` endpoint instead.
- The branch was created from `origin/main` at `aefe80dd`; current upstream already contains the route guard, list/detail `is_super_admin` contract, and UI disabled selector.
- The UI test initially failed because the Status label was not associated with the select. `htmlFor`/`id` now expose the selector as an accessible `Status` combobox.
- Source audit: `server/app/api/user/management.py` is the sole application path that assigns an existing `User.Status`; bootstrap creation in `seed.py` initializes it to Active. The update route uses `is_super_admin()` before its assignment.
- No live/lab tests are in scope.
