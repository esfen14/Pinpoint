# Issue #343: API: signed-out requests get Flask's HTML 401 page instead of the JSON error envelope

Branch: `issue-343-api-401-envelope`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] A signed-out request to a protected `/api` route returns 401 `application/json` with the error envelope, covered by a unit test.
- [x] The web interface's session-expiry handling still passes its tests.
- [x] Decide whether unknown `/api` paths should use the envelope too; record the decision.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Errors use the envelope (signed-out 401) | 1 | `pytest tests/unit/test_api_error_envelope.py` |
| Web interface does not break | 2 | `scripts/verify.sh frontend` |
| Unknown `/api` path HTML 404 (related) | 3 | Owner decision below; same test file; Backend spec |

## Plan

1. [x] Failing tests: `server/tests/unit/test_api_error_envelope.py` (401, unknown `/api` 404, non-API 404 and 405 unchanged)
2. [x] Handlers: `server/app/api/error_handlers.py`, imported from `server/app/api/__init__.py`
3. [x] Correct the stale comment in `client/src/lib/api.ts`; run frontend tests
4. [x] Specs: `spec files/Backend_Modules_and_Routes.md` conventions; remove the gap row in `spec files/Implementation_Status.md`

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Tests, handlers, comment, specs, 2 coverage fingerprints | `verify.sh backend`, `frontend`, `docs` | backend and frontend green; docs blocked by QA supervisor lock held by other sessions |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): `ValueError: Host controller unavailable, already owned or unsafe` in `test_qa_supervisor.py`
- Hypothesis: other checkouts running verification hold the host-wide lock
- Next action (one specific step, not "continue"): rerun `scripts/verify.sh docs` when no other checkout is verifying, then `scripts/verify.sh all`

## Decisions and notes

- Owner decision (2026-11-25, answered in session): unknown `/api` paths return the envelope (404 only). A 405 and non-`/api` paths stay unchanged.
- #343 had no comments when work started; the issue body was used.
