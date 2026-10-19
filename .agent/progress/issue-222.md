# Issue #222: Prevent existing-session login confusion

Branch: `issue-222-existing-session-login`
Status: in-progress

## Finish condition

- [ ] Record manual role pair, tested build, before/after identity and sanitized evidence.
- [ ] Guard authenticated `/login` access.
- [ ] Reject existing-session login explicitly and document the contract.
- [ ] Cover conflicting login identity and permissions with backend regressions.
- [ ] Cover direct login navigation and conflicting response with frontend regressions.
- [ ] Manually verify signed-out login, logout then another login, and differing privileges.
- [ ] Run verification gates and update session specifications.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Preserve attribution and record manual evidence | Manual evidence and verification | Separate attributable manual report; pending |
| Existing session must require explicit sign-out | Guard and API contract | App route tests and test_auth.py |
| Never accept B while retaining A | API regression | Both role directions, /me and protected endpoint checks |
| Accepted B has only B permissions | API regression | Logout then B, /me and protected endpoint checks |
| Frontend handles direct URL and conflict | Frontend regression | App.test.tsx and LoginPage.test.tsx |
| Document and verify behavior | Gates and specifications | verify.sh stages and session specifications |

## Plan

1. [ ] Add failing backend/session and frontend route/conflict tests in test_auth.py, App.test.tsx and LoginPage.test.tsx.
2. [ ] Reject authenticated login with 409 in server/app/api/user/login.py; add LoginRoute.tsx session check and wire App.tsx.
3. [ ] Update backend/frontend specifications and Implementation_Status.md; run focused tests and repository gates.
4. [ ] Record manual appliance verification with differing roles if available; otherwise preserve the blocker in a draft PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Read issue and sources; chose explicit logout with 409 rejection | git status --short | Separate clean worktree; original NCPA changes preserved |

## State for the next session

- Last check run (exact command): git status --short
- Result (first failing lines, or "green"): green
- Hypothesis: Reject all login attempts while authenticated before credential validation; check /me before exposing login form.
- Next action: Add failing regression tests for conflicting identities and authenticated navigation.

## Decisions and notes

Issue explicitly permits rejection or switching; choose rejection requiring explicit sign-out. Preserve existing session on 409. No live changes made. Original historical manual account pair and request evidence were not supplied; do not invent them. Manual acceptance remains required before ready for review.
