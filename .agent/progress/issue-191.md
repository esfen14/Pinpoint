# Issue #191: Cannot add more users

Branch: `issue-191-add-accounts`
Status: in-progress

## Finish condition

- [ ] Test the adding of accounts through the UI.
- [ ] Administrator can now create more than 1 account.
- [ ] Save Changes button should be clickable and can save the new account.

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Manage Accounts / Add User with necessary information | UI test | ManageAccountsPage interaction regressions |
| Administrator creates more than one account | Multiple accounts | Sequential UI creation and isolated persisted API regression |
| Save works regardless of role/status selection | Save Changes | Delayed-role-loading and valid form submission tests |
| Investigate, establish defect, document, fix (user request) | All three | Investigation note, failing regression, minimal fix, full verification |

## Plan

1. [ ] Investigate loading and validation in `client/src/pages/ManageAccountsPage.tsx` and `server/app/api/user/management.py`; reproduce with a failing regression in `client/src/test/ManageAccountsPage.test.tsx` and document findings in `docs/plans/Issue_191_Account_Creation_Investigation.md`.
2. [ ] Fix the confirmed UI defect in `ManageAccountsPage.tsx`; verify valid sequential UI creation, role/status choices, password validation and failed saves in the page tests, plus persisted creation in `server/tests/unit/test_management.py` if needed.
3. [ ] Update `spec files/Frontend_Modules_and_Routes.md` and `spec files/Implementation_Status.md`, re-read issue, run `scripts/verify.sh all`, remove progress file and open PR; verify CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Inspected create route and page: no backend count cap; possible stale initial role ID when modal opens before options load | Source inspection | Needs executable reproduction |

## State for the next session

- Last check run (exact command): `git status --short`
- Result (first failing lines, or "green"): green; isolated worktree created from origin/main 8abddf55.
- Hypothesis: modal role state initializes to zero during loading and never follows the arriving options; invalid passwords also intentionally disable Save.
- Next action (one specific step, not "continue"): Add and run the delayed-role UI regression before changing production code.

## Decisions and notes

- Issue finish condition covers all issue requirements; no exclusions or missing decisions.
- Use isolated worktree `/tmp/pinpoint-issue-191`; copied existing dependency environments for local checks.
- No VM/Docker lab operations or live Nagios tests are needed or authorized by the issue. UI interactions will run locally with isolated API fixtures; backend persistence uses temporary test databases.
- Owning spec: Frontend Modules and Routes, accounts route and loading states. Preserve password policy and server authorization.
