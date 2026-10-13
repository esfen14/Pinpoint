# Issue #111: Prevent changes to the Administrator role's permissions

Branch: `issue-111-administrator-permissions`
Status: in-progress

## Finish condition

- [ ] Backend rejects built-in Administrator permission changes and preserves persisted grants.
- [ ] Role management displays Administrator permissions read-only with an explanation.
- [ ] Direct API requests, including from an Administrator, cannot bypass protection.
- [ ] Same-set requests work regardless of permission order and allow otherwise permitted edits.
- [ ] Other roles remain editable under existing authorization.
- [ ] Regression tests cover rejection, persistence, same-set requests, and other roles.
- [ ] Backend/frontend specifications and Implementation_Status.md document the restriction.
- [ ] `scripts/verify.sh all` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Administrator role grants immutable for every account, via UI and API | 1, 2, 3 | test_management.py, ManageRolesPage.test.tsx |
| Add/remove/replace/clear rejected with no persisted change | 1, 6 | test_management.py |
| Same permission set independent of order; normal role edits | 4, 5, 6 | test_management.py |
| Document and verify | 7, 8 | `scripts/verify.sh docs`, `scripts/verify.sh all` |
| Bootstrap account role reassignment excluded (#109) | out of scope | No change to account role endpoint |

## Plan

1. [x] Add failing backend cases in `server/tests/unit/test_management.py` for built-in Administrator role and API permission changes.
2. [x] Implement Administrator role protection in `server/app/api/user/management.py`; run focused tests and `scripts/verify.sh backend`.
3. [x] Add failing UI cases in `client/src/test/ManageRolesPage.test.tsx` and implement read-only presentation in `client/src/pages/ManageRolesPage.tsx`; run focused tests and `scripts/verify.sh frontend`.
4. [x] Update `spec files/Backend_Modules_and_Routes.md`, `Frontend_Modules_and_Routes.md`, and `Implementation_Status.md`; run `scripts/verify.sh docs`.
5. [ ] Re-read issue, prove each finish item, run `scripts/verify.sh all`, remove progress file, and open PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): green.
- Hypothesis: The specification and stage checks agree; final full verification remains.
- Next action (one specific step, not "continue"): Re-read issue #111 and run final requirement checks, then `scripts/verify.sh all`.

## Decisions and notes

- Existing unrelated change in the original checkout is left untouched; work uses an isolated worktree.
- Built-in role identity currently depends on the seeded Administrator name; assess rename handling while implementing.
