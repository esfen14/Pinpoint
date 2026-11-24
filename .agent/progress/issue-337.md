# Issue #337: Wire up Remember me: 30-day persistent session cookie

Branch: `issue-337-remember-me`
Status: in-progress

## Finish condition

- [ ] Checked: cookie has a 30-day `Expires`; session persists across browser restart and idle gaps longer than the timeout.
- [ ] Unchecked: behaviour identical to today (browser-session cookie, idle timeout applies).
- [ ] Logout always ends a remembered session; deactivated accounts are still signed out.
- [ ] Frontend sends `remember_me`; remembered sessions are not signed out by the client idle watcher.
- [ ] Config: `PERMANENT_SESSION_LIFETIME` 30 days (env override); explicit cookie flags.
- [ ] Specs and manuals updated; TBC resolved and ticked; security note (remembered sessions bypass idle timeout) in manuals.
- [ ] `scripts/verify.sh all` passes.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Frontend sends `remember_me` | item 4 | LoginPage test |
| Backend accepts optional bool (default false, non-bool 400) | items 1, 2 | backend login tests |
| `session.permanent` true/false + `remembered` flag; skip idle check; clear on logout | items 1-3 | test_remember_me.py |
| Audit log notes remembered | item 1 | backend test |
| Config lifetime + cookie flags | item 5 | config test |
| Frontend idle watcher skips remembered | item 4 | SessionTimeoutWatcher test (`/me` returns `remembered`) |
| Tests | all | verify.sh |
| Docs + TBC resolution | item 6 | verify.sh docs |
| Security note | item 6 | manuals diff |

## Plan

1. [ ] Backend tests first (server/tests/unit/test_remember_me.py), then login.py: `remember_me` parsing, permanent flag, `remembered` session flag, skip idle check, clear on logout/expiry, audit text; `/me` returns `remembered` (server/app/api/user/login.py, management.py)
2. [ ] Config: PERMANENT_SESSION_LIFETIME + cookie flags with a test (server/config.py, test)
3. [ ] Frontend: LoginPage sends `remember_me`; watcher reads `remembered` from `/me` and skips idle logout (client/src/pages/LoginPage.tsx, components/layout/SessionTimeoutWatcher.tsx, tests)
4. [ ] Specs: Backend_Modules_and_Routes.md, Frontend_Modules_and_Routes.md, Data_Model_and_Integrations.md, Implementation_Status.md
5. [ ] Manuals: Login_Accounts_and_Roles.md:33, User_Manual.md:152, TEMP_TBC_Worklist.md tick
6. [ ] Finish: verify.sh all, delete progress file, PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan written | n/a | n/a |

## State for the next session

- Last check run (exact command): none
- Result: n/a
- Hypothesis: Flask session.permanent refreshes expiry each request (sliding 30 days); document it.
- Next action: step 1, write failing backend tests.

## Decisions and notes

- Worktree at ../Network-Diagnosis-System-issue-337; server/.venv and client/node_modules symlinked from the main checkout.
- Client watcher learns `remembered` from the `/api/user/me` call it already makes, so no context change.
