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
3. [x] Update reviewed QA dependency fingerprints in automation-coverage.json and Automation_Readiness.md after source changes; update backend/frontend specifications and Implementation_Status.md; run focused tests and repository gates.
4. [ ] Record manual appliance verification with differing roles if available; otherwise preserve the blocker in a draft PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Reviewed issue and sources; chose explicit sign-out | git status --short | Separate worktree preserves original NCPA work |
| 1 | Added failing backend/frontend regressions | pytest test_auth.py; focused Vitest | Expected red: backend 3 failed/8 passed, frontend 3 failed/20 passed |
| 2 | Implemented 409 and login route guard; updated specifications | Focused pytest and Vitest | 11 backend and 23 frontend passed |
| 3 | Ran full gates and requested manual evidence | verify.sh all/backend/frontend; npm test/build/lint | Windows catalog decoding and Unix QA custody gate failures. All 1035 frontend tests, production build and lint pass (33 existing warnings) |
| 4 | Reviewed eight affected permission cases and refreshed login/App/guard source bindings after CI detected stale dependencies | python -X utf8 -I scripts/qa_coverage.py check; test_qa_queue.py | 239 coverage records valid; queue tests 11 pass/1 Windows subprocess decoding failure |
| 5 | Verified adjacent auth behavior, syntax and final diff; prepared draft PR | pytest test_auth.py test_session_timeout.py test_password_change.py test_password_requests.py -q; py_compile; git diff --check | 45 passed; syntax and diff clean. Linux CI and full local backend still running; manual acceptance blocked |

## State for the next session

- Last check run (exact command): FLASK_DEBUG=1 python -m pytest tests/unit/test_auth.py tests/unit/test_session_timeout.py tests/unit/test_password_change.py tests/unit/test_password_requests.py -q
- Result (first failing lines, or "green"): green, 45 passed in 16.79s; full frontend 1035 passed, build/lint exit 0. Full local backend gate is still running (test-results/verify-backend.log); Windows-only failures already observed. Latest CI checks pending after the metadata correction.
- Hypothesis: Reject all login attempts while authenticated before credential validation; check /me before exposing login form.
- Next action: Inspect PR #258 Linux CI and local test-results/verify-backend.log; obtain the unavailable manual QA environment and evidence before marking ready.

## Decisions and notes

Issue explicitly permits rejection or switching; choose rejection requiring explicit sign-out. Preserve existing session on 409. No live changes made. Original historical manual account pair and request evidence were not supplied; do not invent them. Manual acceptance remains required before ready for review.

Manual acceptance blocker: the user confirmed the QA environment cannot be provided. No endpoint, second role/account or original sanitized request evidence is available. Credentials shared in chat were not used or persisted. A person must supply an endpoint and manual before/after evidence for both role directions, normal login and logout then another login.

Round 4 decision: CI docs exposed stale source bindings for login.py and App.tsx. Reviewed the eight affected permission cases, assertion/fixture/cleanup paths and added LoginRoute to their source dependencies. This metadata update is required for the login change; it does not change QA scope, coverage, historical results or authorization.

Session limit: five rounds recorded. Draft PR: https://github.com/esfen14/Pinpoint/pull/258 . Do not mark ready or remove the progress file until manual acceptance and required gates are complete.
