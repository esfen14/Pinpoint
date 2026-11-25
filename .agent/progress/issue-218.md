# Issue #218: TC-ACC-05: Clarify the recorded sign-out warning failure

Branch: `issue-218-signout-warning`
Status: blocked
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] Identify which warning was missing: administrator Edit Account warning, idle-timeout notice, or a message after administrative suspension.
- [ ] In Paeng's separately recorded manual check, verify the administrator dialog warning, session invalidation on the next request, and redirect to `/login`.
- [ ] Preserve the historical FAIL and attach the clarified finding/new result with actual tested build and evidence.
- [ ] If the only complaint is the non-required login-page notice, document that disposition; do not add a requirement without an explicit behavior decision.
- [ ] If a required expectation fails, record its exact step and create/link the specific product defect.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Comment: sign out after edit only at the idle session limit, not abruptly | none (gap) | |
| Comment: admin notifies the user that credentials were replaced | none (gap) | |
| Comment: suspended account sees a pop-up "This account is suspended. Contact the admin for any concerns." on login | none (gap) | |

## Plan

1. [ ] Wait for a person to decide the questions below and amend the finish condition.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | none (source reading only) | none | blocked on decisions |
| 2 | recorded owner answers; checked mail support | none | blocked on email scope |

## State for the next session

- Last check run (exact command): none; no tests run, no dependencies installed in this worktree.
- Result (first failing lines, or "green"): n/a
- Hypothesis: see findings below (source reading, not reproduced).
- Next action (one specific step, not "continue"): read the new issue comment or amended finish condition, then rewrite the plan.

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
