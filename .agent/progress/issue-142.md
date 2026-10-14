# Issue #142: History backend: support date-time bounds and all-column stable sorting

Branch: `issue-142-history-bounds-sorting`
Status: in-progress

## Finish condition

- [x] Both history list routes accept validated custom date/time bounds with clear timezone semantics.
- [ ] Both routes support each table column as a sort key and timestamp descending as secondary tie-breaker.
- [ ] Tests cover ranges, invalid bounds, each sort key, and ties; specs updated.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Custom date/time windows on both lists, timezone semantics and invalid bounds | 1, 3 | server/tests/unit/test_history.py range cases; verify backend |
| All columns sortable with descending timestamp ties on both lists | 2, 3 | server/tests/unit/test_history.py sort cases; verify backend |
| Specs updated | 3 | Alerts_Notifications_History_Requirements.md, Backend_Modules_and_Routes.md, Implementation_Status.md; verify docs |
| Backend-only gap from #133, no frontend changes | 1, 2 | git diff --stat |

## Plan

1. [x] Add failing custom range validation and timezone tests in `server/tests/unit/test_history.py`; implement shared parsing in `server/app/api/system/history.py` and verify backend.
2. [ ] Add failing per-column and tie sort tests in `server/tests/unit/test_history.py`; implement shared sorting in `server/app/api/system/history.py` and verify backend.
3. [ ] Recheck issue and proof, update `spec files/Alerts_Notifications_History_Requirements.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Implementation_Status.md`; verify docs and all.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added validated offset-aware ISO bounds alongside legacy date bounds to both lists, with range tests | `cd server && .venv/bin/python -m pytest tests/unit/test_history.py -q`; `scripts/verify.sh backend` | green: 99 tests; backend 2454 passed, 14 skipped |

## State for the next session

- Last check run (exact command): `scripts/verify.sh backend`
- Result (first failing lines, or "green"): green: 2454 passed, 14 skipped
- Hypothesis: sorting still covers only four alert and three notification keys, without tie-breakers.
- Next action (one specific step, not "continue"): add per-column and timestamp tie tests in server/tests/unit/test_history.py.

## Decisions and notes

- Finish condition covers both stated gaps; #133 remains separate and no frontend work is requested. Existing date-only inputs remain compatible. Use offset-aware ISO 8601 bounds converted to UTC UNIX seconds, inclusive, and reject missing or reversed bounds; preserve preset precedence.
- Owning sections: Alerts_Notifications_History_Requirements.md §§3.3–3.4 and 4.3–4.4; Backend_Modules_and_Routes.md history routes.
