# Issue #156: Add Disk and Resource Trend Forecast Warnings From Stored Performance Data

Branch: `issue-156-forecast-warnings`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue (sections E and H). Tick an item only when a check proves it.
Product decision (user, 2026-10-17): **display only**. Notifications and the horizon and
on/off settings (Part 25.1 step 4, Part 25.2 step 3, and the two notification criteria) are
out of scope and move to a follow-up issue.

- [ ] E1 Rising synthetic series: forecast crossing date is within tolerance of the true value.
- [ ] E2 Flat, falling, noisy, too-short or already-crossed series returns no forecast.
- [ ] E3 Run time and query count stay bounded as services grow (seeded dataset).
- [ ] E4 A forecast never changes any Nagios state or generated config.
- [ ] E5 (notifications off/on) Deferred: display only. Nothing is ever sent.
- [ ] E6 Dashboard and service table show forecasts, the basis, and the empty and not-enough-data states.
- [ ] E7 (settings save/reload) Deferred with notifications; no settings are added.
- [ ] H Functional, code quality, testing, security, documentation and PR items.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| 25.1.1 linear fit over last W hours, disk and memory percent, crossing of warning and critical; none when few samples, flat/falling, poor fit, already past | E1, E2 | `server/tests/unit/test_forecast.py` |
| 25.1.2 APScheduler job, max_instances=1, coalesce, capped services, latest forecast only per host/service/metric | E3 | `test_forecast_job.py`, scheduler registration test |
| 25.1.3 read route sorted by soonest, with window, sample count, slope; existing view permissions | E3 | `test_forecast_routes.py` |
| 25.1.4 notifications | Deferred by decision | follow-up issue |
| 25.2.1 Dashboard "Running out soon" list, service table badge, basis text | E6 | `ForecastList.test.tsx`, `ServiceStatusTable` badge test |
| 25.2.2 empty and not-enough-data states | E6 | same frontend tests |
| 25.2.3 settings | Deferred by decision | follow-up issue |
| D no forecast for retired or paused device; never changes Nagios state; labelled as estimate | E4, E2 | job test with paused device; code has no Nagios write path |
| D counter reset or noisy series gives no forecast | E2 | unit test |
| Deliverables: migration with downgrade, specs, Help text, tests, `docs/test-runs/` lab report | H | migration test, `verify.sh all`; lab report needs a lab (see notes) |

## Plan

1. [x] Pure forecast math: `server/app/forecast.py` (`fit_forecast`), test first in `server/tests/unit/test_forecast.py`.
2. [ ] Model `ResourceForecast` (default bind) in `server/app/system_models.py` plus multi-database migration with downgrade and a migration test.
3. [ ] Job `compute_forecasts()` in `server/app/forecast.py`: bounded queries, service cap, skip paused/retired/merged devices, replace the latest row per host/service/metric; register in `server/app/scheduler.py`. Tests in `test_forecast_job.py`, including a query-count bound.
4. [ ] Read route `GET /system/forecast` in `server/app/api/system/forecast.py`, registered in `server/app/api/system/__init__.py`; permission reuse; tests in `test_forecast_routes.py`.
5. [ ] Frontend: `client/src/types/forecast.ts`, `ForecastList` on the Dashboard, forecast badge in `ServiceStatusTable.tsx`, three states, tests under `client/src/test/`.
6. [ ] Help text explaining the estimate and limits (where Help text lives; find it).
7. [ ] Specs: Backend_Modules_and_Routes, Data_Model_and_Integrations, Frontend_Modules_and_Routes, Implementation_Status; `scripts/verify.sh docs`.
8. [ ] `scripts/verify.sh all`; re-read the issue; delete this file; open the PR.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written, branch created | none | n/a |
| 1 | `fit_forecast` in `server/app/forecast.py` with 15 unit tests (failed first: module missing) | `python -m pytest tests/unit/test_forecast.py -q` in `server/` | 15 passed |

## State for the next session

- Last check run (exact command): `cd server && python -m pytest tests/unit/test_forecast.py -q`
- Result (first failing lines, or "green"): green, 15 passed
- Hypothesis: NCPA metric names are `disk/logical/<part>/used_percent` and `memory/virtual/percent` (see `server/tests/unit/test_dashboard.py:242`); `ServicePerfData` joins `ServiceStatus` for the timestamp.
- Next action: step 2. Add model `ResourceForecast` to `server/app/system_models.py`, write the migration test first (copy the pattern of `server/tests/unit/test_maintenance_migration.py`), then `flask db migrate --multidb` and review it. Head revision is `d117f3b8a053`.

## Decisions and notes

- Display only (user, 2026-10-17). Notification delivery needs #132 and #153 and a settings UI; record as a follow-up issue (not yet created on GitHub; ask the user).
- The issue asks for a lab report comparing the forecast with a real disk fill. That needs a lab appliance; it cannot be produced here and will be listed as not verified.
- Forecasts are never written into Nagios state or config; the job only reads history.db and writes one table in system.db.
