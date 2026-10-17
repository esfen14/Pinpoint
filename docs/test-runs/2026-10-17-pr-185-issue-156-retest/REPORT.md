# Test run: PR #185 / issue #156 forecast defect retest

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `298aa620c6f80442565dabb12f5173e1337cecf5` |
| Scope | Three seeded forecast job findings in [PR #185](https://github.com/esfen14/Pinpoint/pull/185) / [issue #156](https://github.com/esfen14/Pinpoint/issues/156); [original acceptance report](../2026-10-17-pr-185-issue-156/REPORT.md) |
| Tester | Codex |
| Environment | Linux 6.12.105+deb13-amd64; Python 3.14.2; Node 20.19.2; isolated in-memory system/history SQLite engines; application scheduler disabled |
| Raw evidence | Repository `test-results/pr-185-issue-156/` (ignored; not committed) |

## Result

**Overall: Pass for the three scoped defect fixes; overall issue acceptance remains Partial.** The five new regressions, seeded measurements and full local verification pass. Remote CI has no check runs on the pushed fix and the issue's real disk-fill comparison remains pending.

Totals: Pass 7, Fail 0, Blocked 2, Skipped 1 (case rows, not individual automated tests).

## Cases

| Case | Result | Observed behavior and evidence | Issue |
|---|---|---|---|
| New regressions demonstrate the original defects | Pass | Five new tests failed against the original implementation; `fix-regressions-before.log`. Tests include exact host/service/metric filtering, mixed-row statement count, rotating/wrapping batches, advancing past flat series and commit-failure retry. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Focused fit/job/API/migration/scheduler regressions | Pass | 57 passed in 5.68 s; `fixed-focused.log`, `fixed-focused.xml`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Mixed ready/insufficient insert batching | Pass | Two trials each at 10, 100 and 500 series: five SQL statements in every trial (formerly 14, 104 and 504); 500-series runs preserve all 250 forecasts and 250 insufficient rows with nullable fields unset. `fixed-seeded-mixed.log`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Hourly fetch restricted to selected tuples | Pass | At 1,000 series / 72,000 seeded history rows on one host, each 500-series batch fetches 35,500 hourly rows (formerly 71,000). Measured job durations 0.3021 s and 0.3407 s; five statements each. Regression also covers two metrics on the same service. `fixed-seeded-scale.log`, focused regression output. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Excess series receive later turns | Pass | Consecutive 500-series batches cover disk-0000–disk-0499 and disk-0500–disk-0999: 1,000 distinct series processed. A smaller regression proves suffix/prefix wrap in one capped query and advancement through flat series. `fixed-seeded-scale.log`, `fixed-focused.log`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Failed commit does not lose the processing turn | Pass | Forced commit failure leaves prior stored rows and cursor intact; the next successful run processes the same intended batch. `TestRotation.test_commit_failure_preserves_rows_and_retries_the_same_batch` in `fixed-focused.log`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Full local gate | Pass | `bash scripts/verify.sh all` exited 0: 3,799 backend passed / 14 skipped in 429.70 s, 881 frontend passed across 71 files, production build passed, lint 0 errors / 30 warnings, docs and drift checks passed. `fixed-verify-all.log`. Documentation checks also passed after completing this retest report. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Required remote CI | Blocked | Latest pushed fix currently has no check runs; do not inherit the older commit's green CI. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Real known-rate disk-fill comparison | Blocked | Still pending from the original acceptance report; this round uses synthetic history and no lab changes. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Forecast notifications/settings and live browser | Skipped | Outside the three-defect fix scope; no new live or notification claim. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |

## Implementation and limits

The hourly query matches the selected host/service/metric tuples in SQL. Uniform nullable columns and Core executemany preserve a single insertion statement for mixed rows. A process-local cursor orders eligible tuples after the preceding batch before wrapping to the beginning. It advances only after successful commit, including batches with no forecasts; restart begins traversal again. Each run still replaces the prior batch's stored set, keeping at most 500 rows. The existing scheduler has `max_instances=1`.

No dependency, migration, permission, forecast arithmetic, notification behavior or Nagios configuration change is introduced. SQL timings exclude seeding and extra diagnostic fetches. They are local observations, not production throughput guarantees.

## Reproduction

```bash
bash scripts/verify.sh all
FLASK_DEBUG=1 server/.venv/bin/python -m pytest -c server/pytest.ini server/tests/unit/test_forecast_job.py -q
FLASK_DEBUG=1 server/.venv/bin/python test-results/pr-185-issue-156/seeded_scale.py
FLASK_DEBUG=1 server/.venv/bin/python test-results/pr-185-issue-156/seeded_mixed.py
```

The seeded runners are retained with ignored local evidence. Permanent regressions are committed in `server/tests/unit/test_forecast_job.py`; the owning data specification and test inventory describe the final behavior.

## Follow-up

- The existing issue still needs its real known-rate disk-fill comparison and scoped product/merge checklist reconciliation.
- Keep PR #185 a draft until remaining issue acceptance and remote CI requirements are met.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Raw evidence referenced by name and location, not pasted
