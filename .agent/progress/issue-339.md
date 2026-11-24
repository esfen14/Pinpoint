# Issue #339: Logout can be undone by an in-flight request re-issuing the session cookie

Branch: `issue-339-throttle-session-cookie`
Status: in-progress

## Finish condition

- [ ] A request whose `last_activity` is fresh (<=60 s) sets no `Set-Cookie`, so a logout cookie is not overwritten (reworded by the owner; the stale-cookie replay test is dropped because option 1 is stateless).
- [ ] Idle timeout still ends an idle session (`test_session_timeout.py` passes); a request within 60 s does not rewrite the cookie and one after does.
- [ ] Idle watcher logout in the browser leaves the user on the login page with polling running (Playwright check against the lab).
- [ ] `Backend_Modules_and_Routes.md` updated; `scripts/verify.sh all` passes.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Write last_activity only when older than 60 s; always at login | 1, 2 | test_session_timeout.py |
| SESSION_REFRESH_EACH_REQUEST False (owner decision) | 1 | unit test: remembered session fresh request has no Set-Cookie |
| Residual race documented | 4 | spec text |
| Option 2 | out of scope (owner: option 1 only) | n/a |

## Plan

1. [x] Tests first in server/tests/unit/test_session_timeout.py (no Set-Cookie when fresh, rewrite when stale, remembered too)
2. [x] Implement in server/app/api/user/login.py and server/app/config.py (SESSION_REFRESH_EACH_REQUEST=False)
3. [x] Spec (+ QA register login.py hashes, Automation_Readiness note): spec files/Backend_Modules_and_Routes.md
4. [ ] Playwright lab check (needs lab up)
5. [ ] verify.sh all, finish

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan | | |
| 1 | throttle + config + tests + spec + register hashes | pytest test_session_timeout.py; verify.sh docs | 13 passed; docs green apart from offline lab-smoke FAIL lines also on main |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs
- Result: green (lab-smoke FAIL lines identical on main)
- Hypothesis: n/a
- Next action: Playwright lab check. Running Docker lab mounts the issue-337 checkout as /src, so lab sync does not carry this branch; owner asked which of: docker cp patch, separate lab, wait. Then scripts/verify.sh all, finish.

## Decisions and notes

Owner chose option 1 only and SESSION_REFRESH_EACH_REQUEST=False.
