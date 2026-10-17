# Issue #156: Forecast job acceptance defect fixes

Branch: `issue-156-forecast-warnings`
Status: in-progress

## Finish condition

The user's follow-up narrows this round to the three reproduced defects in PR #185.
The original issue remains open for the real disk-fill comparison and its other merge requirements.

- [ ] Constant SQL statement count for mixed ready/insufficient series.
- [ ] Hourly fetches restricted to the selected series.
- [ ] Repeated runs eventually process eligible series beyond the cap.
- [ ] Regression tests, seeded measurements and full local verification pass.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Bounded runtime/query work and capped services (#156 E/G) | First three items | Mixed-row SQL count, fetched-row cap and repeated-run regression tests; seeded runners |
| Preserve forecast fit, permissions, migration and UI (#156 E/F/H) | Regression verification | Focused forecast tests and scripts/verify.sh all |
| Technical documentation and real evidence (#156 F) | Verification | Updated data specification, test inventory and new retest report |
| Real known-rate disk-fill comparison (#156 G) | Outside this defect-fix round; still pending | Original acceptance report records Blocked; no live pass claimed |
| Forecast notifications/settings | PR's declared display-only scope | Still deferred; no feature expansion in this fix |

## Plan

1. [ ] Add failing regressions to server/tests/unit/test_forecast_job.py for all three defects and commit-failure cursor behavior.
2. [ ] Fix server/app/forecast.py with exact series filtering, uniform insert column sets and transaction-aware in-process rotation; update owning specs and server/tests/README.md.
3. [ ] Run focused tests, repeat seeded measurements, run scripts/verify.sh all, and record a new docs/test-runs retest report; checkpoint changes on existing draft PR #185.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Resumed the existing draft branch and recorded the scoped fix plan | Prior run: scripts/verify.sh all; seeded measurements | Gate green; three supplemental defects reproduced |

## State for the next session

- Last check run (exact command): bash scripts/verify.sh all
- Result: Previous turn green (3,794 backend passed, 14 skipped; 881 frontend passed); supplemental seeded checks failed as recorded in the acceptance report.
- Hypothesis: Heterogeneous ORM dictionaries split inserts; hostname-only SQL fetches extra series; fixed LIMIT without rotation starves later series.
- Next action: Add and run the regression tests before changing app/forecast.py.

## Decisions and notes

- User explicitly authorized fixing the three observed defects and testing afterward; existing branch/PR are resumed in place.
- No new migration/dependency or live lab mutation is needed.
- Cursor will be process-local (scheduler has max_instances=1), advance only after commit, and wrap within one capped query. Restart starts at the beginning; this limitation will be documented.
- Preserve the original acceptance report as historical evidence; publish a separate retest report.
