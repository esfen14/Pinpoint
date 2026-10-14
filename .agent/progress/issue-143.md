# Issue #143: History backend: link exact alert and notification events

Branch: `issue-143-history-event-links`
Status: in-progress

## Finish condition

- [ ] History API returns stable event identifiers or unambiguous link metadata for related alert/notification events.
- [ ] List routes support an exact event locator (or equivalent) so cross-tab navigation selects/opens the correct event, including outside the default 24h range.
- [ ] Tests cover multiple nearby events, host/service and no match; frontend link updated; specs updated.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Nearby events must not select wrong event; stable identity | 1, 3 | server/tests/unit/test_history.py |
| Exact locator outside default range | 2, 3 | server/tests/unit/test_history.py; client history tests |
| Host/service and no match | 3 | server/tests/unit/test_history.py |
| Frontend cross-tab deep link | 2, 3 | client history tests; scripts/verify.sh frontend |
| Specs updated | 3 | scripts/verify.sh docs |
| Backend-dependent audit gap; not in #133 | 1–3 | Implementation_Status.md |

## Plan

1. [x] Test and implement event identity, related-event matching and exact locator in `server/tests/unit/test_history.py`, `server/app/api/system/history.py`.
2. [x] Test and implement exact cross-tab navigation in `client/src/test/HistoryPage.test.tsx`, `client/src/pages/HistoryPage.tsx`.
3. [ ] Update `spec files/Alerts_Notifications_History_Requirements.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Implementation_Status.md` and verify docs.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Deterministic Nagios event IDs, precise list locator, state/target-aware related links; backend tests | `cd server && .venv/bin/python -m pytest tests/unit/test_history.py -q && cd .. && scripts/verify.sh backend` | green: 133 passed; 2488 passed, 14 skipped |
| 2 | Cross-tab locator load and automatic expansion; frontend tests | `cd client && npm run test -- src/test/HistoryPage.test.tsx && npm run build && cd .. && scripts/verify.sh frontend` | green: 5 focused, 527 frontend; lint warnings only |

## State for the next session

- Last check run (exact command): `cd client && npm run test -- src/test/HistoryPage.test.tsx && npm run build && cd .. && scripts/verify.sh frontend`
- Result (first failing lines, or "green"): green (5 focused, 527 frontend; lint warnings only)
- Hypothesis: Document locator semantics and distinguish #143 from remaining #144 gap.
- Next action (one specific step, not "continue"): Update owning specification, route catalog, frontend catalog and Implementation_Status.

## Decisions and notes

Issue finish condition covers problem, proposed link behavior, and excludes #133; §5.4 and §4.2 own cross-tab semantics. No migration or sensitive modules planned.
