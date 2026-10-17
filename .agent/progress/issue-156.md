# Issue #156: Forecast job acceptance defect fixes

Branch: `issue-156-forecast-warnings`
Status: in-progress

## Finish condition

The user's follow-up narrows this round to the three reproduced defects in PR #185.
The original issue remains open for the real disk-fill comparison and its other merge requirements.

- [x] Constant SQL statement count for mixed ready/insufficient series.
- [x] Hourly fetches restricted to the selected series.
- [x] Repeated runs eventually process eligible series beyond the cap.
- [x] Regression tests, seeded measurements and full local verification pass.

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
3. [x] Run focused tests, repeat seeded measurements, run scripts/verify.sh all, and record a new docs/test-runs retest report; checkpoint changes on existing draft PR #185.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Resumed the existing draft branch and recorded the scoped fix plan | Prior run: scripts/verify.sh all; seeded measurements | Gate green; three supplemental defects reproduced |

| 1 | Five regressions fail before fix; exact tuple filtering, uniform Core executemany and commit-aware cursor implemented; docs updated | Focused forecast/scheduler tests; homogeneous and mixed seeded scripts | 57 passed; mixed rows stay at 5 statements; 1,000 series processed in two capped batches fetching 35,500 hourly rows each |

| 2 | Repeated seeded measurements and full gate; wrote separate retest report without altering original failed-run evidence | bash scripts/verify.sh all; gh pr view 185 --json statusCheckRollup | Local gate green: 3,799 backend passed / 14 skipped; 881 frontend passed; build/lint/docs pass. Remote CI has no check runs for updated head. |

## State for the next session

- Last check run (exact command): bash scripts/verify.sh all
- Result: Green at code commit 298aa620c6f80442565dabb12f5173e1337cecf5: 3,799 backend passed / 14 skipped; 881 frontend passed; build passed; lint zero errors / 30 warnings. Evidence: test-results/pr-185-issue-156/fixed-verify-all.log and docs/test-runs/2026-10-17-pr-185-issue-156-retest/REPORT.md.
- Hypothesis: All three user-requested defect fixes are complete. Remaining issue acceptance is unrelated to these scoped fixes: real disk-fill comparison and remote CI evidence.
- Next action: Obtain a GitHub Actions run for the updated PR head; GitHub currently reports no checks on the pushed fix.

## Decisions and notes

- User explicitly authorized fixing the three observed defects and testing afterward; existing branch/PR are resumed in place.
- No new migration/dependency or live lab mutation is needed.
- Cursor will be process-local (scheduler has max_instances=1), advance only after commit, and wrap within one capped query. Restart starts at the beginning; this limitation will be documented.
- Preserve the original acceptance report as historical evidence; publish a separate retest report.

- All three user-requested defects are fixed and retested; retain this progress file because PR #185 remains a draft with original issue acceptance still pending. Do not claim the original issue is complete or merge the PR.
