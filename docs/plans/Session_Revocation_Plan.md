# Server-side session revocation (option 2 of #339)

Status: **implemented in PR #340** (current behavior:
[`Backend_Modules_and_Routes.md`](../../spec%20files/Backend_Modules_and_Routes.md)).
The text below is the original proposal. Decisions taken: (1) `Last_Activity` lives in
the table; (2) the per-request read is accepted, not yet measured on the lab; (3)
everyone signs in once after the upgrade; (4) several sessions per user; (5) no admin
"sign out user" route. Password, role, email and status changes already end sessions
through #218's `auth_stamp`; rows are also revoked on administrator password changes
and non-Active status, and other rows on a user's own password change.

## Problem

The session is a stateless signed cookie. The server keeps no record of who is
signed in, so logout cannot invalidate a cookie that is already out there. The
throttle in #340 makes the race much rarer (most responses carry no `Set-Cookie`)
but cannot close it: a request that crosses the 60-second mark can still overwrite
the logout cookie, and an older cookie replayed by a client stays valid until it
idles out.

## Proposal

Give every sign-in a server-side record, and make the cookie prove it points at a
live record.

### Data (default bind, `system.db`)

New table `USER_SESSION` in `server/app/system_models.py`:

| Column | Type | Purpose |
|---|---|---|
| `SessionID` | `String(64)`, primary key | Random token (`secrets.token_urlsafe(32)`); the cookie carries this, never the user id alone |
| `UserID` | FK `USER.UserID`, indexed | Owner |
| `Created_At` | datetime | Sign-in time |
| `Last_Activity` | datetime | Idle-timeout clock (see decision 1) |
| `Remembered` | bool | Same meaning as `session["remembered"]` today |
| `Revoked_At` | datetime, nullable | Set on logout, password change, deactivation; null means live |

It is application data, so it belongs on the default bind, not `history_models.py`
(`Engineering_Standards.md`, Database rules). One Alembic revision in
`server/migrations/versions/`, applied with `flask db upgrade --multidb`; back up
both databases first.

### Behavior

- **Login** (`api/user/login.py`): insert a row, store `session["sid"]` in the
  cookie beside the Flask-Login user id.
- **Every request** (`enforce_session_timeout`, before the existing checks): load
  the row by `sid`. Missing, revoked, or owned by another user → `logout_user()`
  and 401. This is what makes an old cookie useless after logout, whatever order
  responses arrive in.
- **Logout:** set `Revoked_At` on the row, then clear the cookie as today.
- **Revoke on credential events:** set `Revoked_At` for all of the user's rows when
  their password changes (`api/user/management.py` change-password and reset
  paths, `api/user/password_requests.py`) or the account stops being Active. Today
  these cannot end other signed-in devices.
- **Cleanup:** delete rows revoked or idle past the longest lifetime (30 days
  remembered) on a schedule, or opportunistically at login, so the table stays small.

### Decisions for the team

1. **Where does `last_activity` live?** Recommended: move it into the table, which
   lets the cookie stay unchanged on almost every request and makes the 60-second
   throttle in #340 unnecessary. Cost: a write per throttled interval instead of a
   cookie rewrite. Alternative: keep it in the cookie and use the table only for
   revocation (smaller change, keeps #340 as is).
2. **Read cost.** One indexed primary-key read per request, including the dashboard
   polling. SQLite handles this, but it is new load on every API call.
3. **One-time sign-out.** Existing cookies carry no `sid`, so everyone is signed out
   once on upgrade. Acceptable, or allow `sid`-less cookies for one release?
4. **Multiple devices.** Allow several live sessions per user (assumed above), or
   limit to one?
5. **Admin "sign out user".** The table makes it possible; is it wanted? Out of
   scope here unless the team says so.

## Work breakdown

1. Model and migration (`system_models.py`, new revision).
2. Session helper module: create, validate, revoke, revoke-all-for-user, purge.
3. Wire login, logout, `enforce_session_timeout`, password and status changes.
4. Tests (`server/tests/unit/`): logout then replay the old cookie → 401; revoked
   or unknown `sid` → 401; password change revokes other sessions; idle timeout and
   Remember me still behave; migration upgrade test.
5. Specs: `Data_Model_and_Integrations.md` (new model),
   `Backend_Modules_and_Routes.md` (session section; replace the residual-race
   paragraph), `Implementation_Status.md` if the throttle limitation is closed.
6. QA register: `login.py` and likely `management.py` hashes in
   `docs/qa/automation-coverage.json`, with a note in `docs/qa/Automation_Readiness.md`.
7. Lab check: logout with requests in flight, then replay the old cookie; idle
   watcher logout still lands on the login page.

## Risks

- A bug in the per-request check can sign everyone out or lock the API; keep the
  check small and covered by the tests above.
- Per-request DB read on a hot path; measure on the lab before merging.
- Touches authentication, so it needs the same review care as other security code.

## Not in scope

IP or user-agent binding, session listing UI, and token rotation.
