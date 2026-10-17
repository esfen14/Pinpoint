# Issue #156: Forecast job acceptance defect fixes

Branch: `issue-156-forecast-warnings`
Status: in-progress

## Finish condition

The user's follow-up narrows this round to the three reproduced defects in PR #185.
The original issue remains open for the real disk-fill comparison and its other merge requirements.

- [x] Constant SQL statement count for mixed ready/insufficient series.
- [x] Hourly fetches restricted to the selected series.
- [x] Repeated runs eventually process eligible series beyond the cap.
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

1. [x] Add failing regressions to server/tests/unit/test_forecast_job.py for all three defects and commit-failure cursor behavior.
2. [x] Fix server/app/forecast.py with exact series filtering, uniform insert column sets and transaction-aware in-process rotation; update owning specs and server/tests/README.md.
3. [ ] Run focused tests, repeat seeded measurements, run scripts/verify.sh all, and record a new docs/test-runs retest report; checkpoint changes on existing draft PR #185.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Resumed the existing draft branch and recorded the scoped fix plan | Prior run: scripts/verify.sh all; seeded measurements | Gate green; three supplemental defects reproduced |

| 1 | Five regressions fail before fix; exact tuple filtering, uniform Core executemany and commit-aware cursor implemented; docs updated | Focused forecast/scheduler tests; homogeneous and mixed seeded scripts | 57 passed; mixed rows stay at 5 statements; 1,000 series processed in two capped batches fetching 35,500 hourly rows each |

## State for the next session

- Last check run (exact command): FLASK_DEBUG=1 server/.venv/bin/python -m pytest -c server/pytest.ini server/tests/unit/test_forecast.py server/tests/unit/test_forecast_job.py server/tests/unit/test_forecast_routes.py server/tests/unit/test_forecast_migration.py server/tests/unit/test_scheduler.py -q --junitxml=test-results/pr-185-issue-156/fixed-focused.xml
- Result: 57 passed in 5.68 s. Seeded mixed runs: five statements at 10/100/500 series; homogeneous 1,000-series runs cover all 1,000 in two batches.
- Hypothesis: The three scoped defects are fixed; full regression verification remains.
- Next action: Run scripts/verify.sh all on the checkpointed fix, then record the retest and check CI.

## Decisions and notes

- User explicitly authorized fixing the three observed defects and testing afterward; existing branch/PR are resumed in place.
- No new migration/dependency or live lab mutation is needed.
- Cursor will be process-local (scheduler has max_instances=1), advance only after commit, and wrap within one capped query. Restart starts at the beginning; this limitation will be documented.
- Preserve the original acceptance report as historical evidence; publish a separate retest report.
