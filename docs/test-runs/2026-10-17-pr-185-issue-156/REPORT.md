# Test run: PR #185 / issue #156 resource forecasts

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `8c39c1ba2b732cfe2f86d76a09d2736924921f26` |
| Scope | [PR #185](https://github.com/esfen14/Pinpoint/pull/185), [issue #156](https://github.com/esfen14/Pinpoint/issues/156) sections E–H, and [plan issue #25](../../issues/issue-025.md) |
| Tester | Codex |
| Environment | Linux 6.12.105+deb13-amd64; Python 3.14.2; Node 20.19.2; disposable in-memory system/history SQLite databases; scheduler suppressed by the test configuration |
| Raw evidence | Local repository `test-results/pr-185-issue-156/` (ignored; not committed) |

## Result

**Overall: Partial; acceptance not satisfied.** The focused backend suite passes, but supplemental seeded runs reproduce three cost/coverage defects. A real disk-fill comparison has not been performed. `scripts/verify.sh all` passes: 3,794 backend tests passed / 14 skipped, 881 frontend tests passed, build passed, lint had zero errors and 30 warnings.

Totals: Pass 3, Fail 3, Blocked 1, Skipped 2 (case rows, not individual automated tests).

## Cases

| Case | Result | Notes (observed behavior and evidence) | Issue |
|---|---|---|---|
| Focused backend: fit, job, API, migration, scheduler | Pass | 52 passed in 5.36 s; `focused.log`, `focused.xml`. Includes rising-series tolerance, flat/falling/noisy/reset/short/already-crossed/horizon rejection, ordering, permissions, paused-device exclusion, replacement, no Nagios commands/config calls, and migration downgrade/re-upgrade. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Full local verification gate | Pass | `bash scripts/verify.sh all` exited 0 (`verify: all OK`): docs and route/API drift checks pass; backend 3,794 passed / 14 skipped in 428.05 s; frontend 881 passed across 71 files; production build passes; lint 0 errors / 30 warnings. `verify-all.log`. Documentation checks rerun after adding this report also pass (`report-docs.log`). | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Homogeneous seeded job cost | Pass | 10, 500 and 1,000 disk series on one host, 72 samples seeded per series; five statements per run; 10/500/500 forecasts. Repeated trials; `seeded-scale.log`, `seeded-scale-repeat.log`. This passes only the homogeneous query-count check. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Mixed ready/insufficient series: constant SQL statement count | Fail | Alternating 72-sample and two-sample series: 14 statements at 10 series, 104 at 100, 504 at 500. Both trials reproduce it. ORM bulk insertion splits alternating dictionaries with different populated columns into separate inserts. `seeded-mixed-repeat.log`; source `server/app/forecast.py:195–219`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Series cap bounds hourly result size | Fail | At 500 series, 35,500 hourly rows fetched; at 1,000 series, 71,000 fetched, despite storing at most 500 forecasts. Repeated measured duration grows from about 0.26–0.28 s to 0.50–0.51 s. Hourly query filters only hostnames, then discards excess series in Python. `seeded-scale-repeat.log`; source `server/app/forecast.py:181–191`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Excess series receive a later processing turn | Fail | With 1,000 eligible series, consecutive runs both store only `disk-0000` through `disk-0499`; `disk-0999` is absent both times. Fixed ordering plus LIMIT has no rotation/cursor, so unchanged eligible series beyond the cap do not get a turn. `seeded-scale-repeat.log`; source `server/app/forecast.py:155–165`. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Real disk fill: predicted versus observed crossing | Blocked | Not executed. Read-only VM ownership preflight passed with the appliance powered off. A newly collected series needs at least 36 hours of temporal coverage before a forecast is eligible; no sustained known-rate disk-fill dataset was collected in this run. No appliance or target was changed. Synthetic seeded history is not live acceptance evidence. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Forecast notification/settings behavior | Skipped | PR declares display-only scope approved by the team. Notification-on delivery and settings remain unimplemented and are not treated as passing issue criteria. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |
| Live browser and appliance deployment | Skipped | Automated frontend tests are covered by the full gate; no live browser session or appliance upgrade is claimed. | [#156](https://github.com/esfen14/Pinpoint/issues/156) |

## Reproduction

Run the normal gate from the repository root:

```bash
bash scripts/verify.sh all > test-results/pr-185-issue-156/verify-all.log 2>&1
```

Supplemental scripts are retained with ignored local evidence:

```bash
FLASK_DEBUG=1 server/.venv/bin/python test-results/pr-185-issue-156/seeded_scale.py
FLASK_DEBUG=1 server/.venv/bin/python test-results/pr-185-issue-156/seeded_mixed.py
```

They import `server/conftest.py` before the app, seed only disposable in-memory databases, capture SQLAlchemy statements on both binds during the job, measure wall time excluding seeding and instrumentation result retrieval, and execute each case twice. The homogeneous script also replays the captured hourly SELECT to count its returned rows. It leaves production databases, Nagios state/config and the lab untouched. Measurements are local observations, not production throughput guarantees. Samples are hourly; window boundaries leave 71 points per full series in these runs.

## Deviations from the plan

This is targeted PR verification, not an ISO-scoped QA queue. No qa-run/fix-found loop was invoked. Findings are recorded against the existing issue above; no GitHub comments, new issues, commits or pushes were made. Full suite output and supplemental scripts remain local evidence. Notifications are skipped according to the PR scope; the original issue still includes conditional notification criteria and has no decision comment.

## Follow-up

- Address all three reproduced job defects in #156 and add regression coverage for mixed row shapes, several series on one hostname beyond the cap, and repeated processing above the cap.
- Run the real known-rate disk-fill comparison on a dedicated lab volume with enough genuinely collected history and record observed versus predicted crossing and tolerance.
- Reconcile the issue's finish-condition checklist with the PR's display-only decision and track notifications separately.
- Attach verification evidence to the PR through the normal review process. This run does not establish reviewer approval or merge readiness.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Raw evidence is referenced by name and location, not pasted
