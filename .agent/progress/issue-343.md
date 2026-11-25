# Issue #343: API: signed-out requests get Flask's HTML 401 page instead of the JSON error envelope

Branch: `issue-343-api-401-envelope`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] A signed-out request to a protected `/api` route returns 401 `application/json` with the error envelope, covered by a unit test.
- [ ] The web interface's session-expiry handling still passes its tests.
- [ ] Decide whether unknown `/api` paths should use the envelope too; record the decision.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Errors use the envelope (signed-out 401) | 1 | `pytest tests/unit/test_api_error_envelope.py` |
| Web interface does not break | 2 | `scripts/verify.sh frontend` |
| Unknown `/api` path HTML 404 (related) | 3 | Owner decision below; same test file; Backend spec |

## Plan

1. [ ] Failing tests: `server/tests/unit/test_api_error_envelope.py` (401, unknown `/api` 404, non-API 404 and 405 unchanged)
2. [ ] Handlers: `server/app/api/error_handlers.py`, imported from `server/app/api/__init__.py`
3. [ ] Correct the stale comment in `client/src/lib/api.ts`; run frontend tests
4. [ ] Specs: `spec files/Backend_Modules_and_Routes.md` conventions; remove the gap row in `spec files/Implementation_Status.md`

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: no Flask-Login `unauthorized_handler` and no `/api` 404 handler
- Next action (one specific step, not "continue"): write the failing tests

## Decisions and notes

- Owner decision (2026-11-25, answered in session): unknown `/api` paths return the envelope (404 only). A 405 and non-`/api` paths stay unchanged.
- #343 had no comments when work started; the issue body was used.
