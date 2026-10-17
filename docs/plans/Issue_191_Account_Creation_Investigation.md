# Issue #191: account creation investigation

Issue: [Cannot add more users](https://github.com/esfen14/Pinpoint/issues/191).
Baseline inspected and tested: `8abddf55` (`origin/main`, 2026-10-17).

## Finding

A UI defect is confirmed. Open Manage Accounts → Add User while the initial
role-options request is pending. Fill the names, email and matching valid
passwords, then let the request finish. The role selector displays its first
option, but Save Changes stays disabled. `AddAccountModal` initializes
`form.roleId` to zero when the options are empty. Later props populate the
native select without updating that state; validation still sees zero.

The added `can save when Add User opens before role options arrive` interaction
test failed before the fix: the role selector had value `1`, but
`expect(Save Changes).toBeEnabled()` failed. The other 26 page tests passed.

This establishes a defect consistent with the disabled button, not an exact
reproduction of every detail in the report. Selecting a different role can
work around this race. The report says changing roles/status did not help,
so its exact original trigger remains unconfirmed. Weak or mismatched passwords
also intentionally disable Save; changing roles/status cannot make those valid.
The page already displays the active password policy and mismatch feedback.
No password, email or authorization rules should be relaxed to enable saving.

## Backend inspection

`server/app/api/user/management.py:create_account` validates permissions, role,
status, passwords and email uniqueness, then inserts a new user. There is no
one-account limit. An account is committed before applying its Nagios contact;
a failed apply returns a warning and does not undo the created account.

## Fix and verification scope

Derive an effective role from the explicitly selected role or the first loaded
option, and use that same value for rendering, validation and the POST body.
Keep Save disabled when no valid role exists. Explain the no-role state.
Preserve deliberate role/status choices and all existing validation.

Verify delayed options, no available roles, sequential account creation with
list refresh, explicit role/status choices, backend persistence of multiple
accounts, and server rejection/retry without losing the form. These are isolated
React interaction and Flask temporary-database tests, not a deployed appliance
or real Nagios acceptance run. Full verification results are recorded in the PR.
