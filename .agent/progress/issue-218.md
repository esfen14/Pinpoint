# Issue #218: TC-ACC-05: Clarify the recorded sign-out warning failure

Branch: `issue-218-signout-warning`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Issue items (the first five depend on the owner's manual check; do not tick them here) and the
items agreed in the 2026-11-25 issue comment.

- [ ] Identify which warning was missing.
- [ ] Separately recorded manual check of dialog warning, invalidation and redirect (owner).
- [ ] Preserve the historical FAIL; attach the new result with tested build and evidence (owner).
- [ ] Document the disposition if only the login-page notice was meant.
- [ ] Record and link any failed expectation as a defect.
- [ ] A role, status, password or email change signs the user out on the next request; name and
      alert-setting changes do not; own "Change password" keeps the user signed in.
- [ ] The open page then goes to `/login`.
- [ ] Suspended login shows "This account is suspended. Contact the admin for any concerns.";
      Inactive keeps "Account inactive."
- [ ] Admin password reset (Edit Account or forgot-password request), email or role change emails
      the account (old and new address), never the password; on mail failure the change is saved
      and the admin is told.
- [ ] Specs, TC-ACC-05 wording, manuals and automated tests match.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Comment: sign out only at idle limit | out of scope: replaced by the owner decision "immediately" | issue comment 2026-11-25 |
| Comment: admin notifies the user | email item | tests/unit/test_account_notifications.py |
| Comment: suspended pop-up | suspended item | tests/unit/test_session_revocation.py |

## Plan

1. [x] Session revocation and suspended message: `server/app/api/user/login.py`, `management.py`,
       `server/tests/unit/test_session_revocation.py`.
2. [x] Account change email: `server/app/account_notifications.py`, `smtp_settings.py`,
       `management.py`, `password_requests.py`, `server/tests/unit/test_account_notifications.py`.
3. [x] Client: redirect on 401 and page change (`SessionTimeoutWatcher.tsx`, `lib/api.ts`,
       `CurrentUserContext.tsx`); dialog wording and mail notice (`ManageAccountsPage.tsx`,
       `PasswordRequestsPanel.tsx`); tests.
4. [ ] Specs, QA catalog TC-ACC-05, manuals; verify all.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | none (source reading only) | none | blocked on decisions |
| 2 | recorded owner answers; checked mail support | none | blocked on email scope |
| 3 | owner said go; posted condition on #218; installed deps; wrote plan | none | plan ready |
| 4 | session stamp, suspended message; four tests that edit the signed-in account now sign in again | unit tests (full run, then affected files) | green |
| 5 | account change email; client redirect, dialog wording, mail notice | affected pytest files; two vitest files | green |

## State for the next session

- Last check run (exact command): npx vitest run on SessionTimeoutWatcher and ManageAccountsPage tests
- Result (first failing lines, or "green"): green
- Hypothesis: a keyed stamp of password hash, role, email, status and forced-change flag in the
  session ends sessions without a database migration. Sessions without a stamp are rejected, so
  everyone signs in once after upgrade.
- Next action (one specific step, not "continue"): update specs, TC-ACC-05 and manuals, then run scripts/verify.sh all.

## Decisions and notes

Source findings:

- `server/app/api/user/login.py` `enforce_session_timeout` ends a session only for a
  non-Active status or idle timeout. Nothing in Edit Account
  (`server/app/api/user/management.py`) ends it after a role or password change, although the
  dialog (`client/src/pages/ManageAccountsPage.tsx`) says the user will be signed out and
  REQ-ACC-04 requires it. `CurrentUserContext.tsx` says role changes apply without logout.
- `SessionTimeoutWatcher.tsx` checks `/api/user/me` only on mount, and `CurrentUserContext.tsx`
  only logs a 401, so an open page is probably not redirected to `/login` on the next click.
- `LoginPage.tsx` already shows an `alert` with the server message; a suspended or inactive
  account gets "Account inactive." (403) after correct credentials.

Answers from the user, 2026-11-25:

- Q1: role or password change signs the user out immediately.
- Q2: Suspended or Inactive signs the user out immediately.
- Q3: asked whether an email would suffice. Yes: `server/app/smtp_settings.py` already
  sends over SMTP (test email only so far). Trigger events and behaviour when mail is not
  configured are still to be confirmed.
- Q4: agreed to the suspended login message.

Questions asked earlier:

1. Does the 2026-11-17 comment replace REQ-ACC-04 / TC-ACC-05 (immediate sign-out on the next
   request)? Does "at the idle session limit" also apply to Suspended and Inactive accounts?
   Remember me sessions never idle out.
2. Is "admin notifies the user" a manual action outside the product, or a feature?
3. Is the suspended message Suspended only, with Inactive keeping "Account inactive."?
4. Authentication and session invalidation are security behaviour: confirm the change.
