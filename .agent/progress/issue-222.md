# Issue #222: Prevent existing-session login confusion

Branch: `issue-222-existing-session-login`
Status: blocked

## Finish condition

- [ ] Record manual role pair, tested build, before/after identity and sanitized evidence.
- [x] Guard authenticated `/login` access.
- [x] Reject existing-session login explicitly and document the contract.
- [x] Cover conflicting login identity and permissions with backend regressions.
- [x] Cover direct login navigation and conflicting response with frontend regressions.
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

1. [x] Add failing backend/session and frontend route/conflict tests in test_auth.py, App.test.tsx and LoginPage.test.tsx.
2. [x] Reject authenticated login with 409 in server/app/api/user/login.py; add LoginRoute.tsx session check and wire App.tsx.
3. [ ] Update reviewed QA dependency fingerprints in automation-coverage.json and Automation_Readiness.md after source changes; update backend/frontend specifications and Implementation_Status.md; run focused tests and repository gates.
4. [ ] Record manual appliance verification with differing roles if available; otherwise preserve the blocker in a draft PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 2 | Implemented 409 rejection and LoginRoute; updated specifications | Focused pytest and Vitest | 11 backend and 23 frontend passed; frontend pre-fix 3 failed, 20 passed |
| 1 | Added backend and frontend regressions | pytest tests/unit/test_auth.py -q | Expected red: 3 failed, 8 passed; API returns 200 instead of 409. Frontend dependency install pending |
| 3 | Ran repository gates and full frontend unit suite; requested manual evidence | verify.sh all, backend, frontend; npm test | Full gate blocked by Windows catalog decoding; direct UTF-8 traceability passes. Frontend QA gate: 14 failed, 4 passed (Unix directory custody). Frontend unit suite: 1035 passed. Backend/build/lint pending |
| Plan | Read issue and sources; chose explicit logout with 409 rejection | git status --short | Separate clean worktree; original NCPA changes preserved |

## State for the next session

- Last check run (exact command): python -X utf8 -I scripts/check_traceability.py
- Result (first failing lines, or "green"): green; normal verify.sh docs fails No TC/E2E definitions because isolated Python uses Windows default encoding
- Hypothesis: Reject all login attempts while authenticated before credential validation; check /me before exposing login form.
- Next action: Collect running backend/build/lint results and Linux CI, then obtain manual acceptance evidence before marking PR ready.

## Decisions and notes

Issue explicitly permits rejection or switching; choose rejection requiring explicit sign-out. Preserve existing session on 409. No live changes made. Original historical manual account pair and request evidence were not supplied; do not invent them. Manual acceptance remains required before ready for review.

Manual acceptance blocker: the user confirmed the QA environment cannot be provided. No endpoint, second role/account or original sanitized request evidence is available. Credentials shared in chat were not used or persisted. A person must supply an endpoint and manual before/after evidence for both role directions, normal login and logout then another login.

Round 4 decision: CI docs exposed stale source bindings for login.py and App.tsx. Reviewed the eight affected permission cases, assertion/fixture/cleanup paths and added LoginRoute to their source dependencies. This metadata update is required for the login change; it does not change QA scope, coverage, historical results or authorization.
