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
2. [x] Model `ResourceForecast` (default bind) in `server/app/system_models.py` plus multi-database migration with downgrade and a migration test.
3. [x] Job `compute_forecasts()` in `server/app/forecast.py`: bounded queries, service cap, skip paused/retired/merged devices, replace the latest row per host/service/metric; register in `server/app/scheduler.py`. Tests in `test_forecast_job.py`, including a query-count bound.
4. [x] Read route `GET /system/forecast` in `server/app/api/system/forecast.py`, registered in `server/app/api/system/__init__.py`; permission reuse; tests in `test_forecast_routes.py`.
5. [x] Frontend: `client/src/types/forecast.ts`, `ForecastList` on the Dashboard, forecast badge in `ServiceStatusTable.tsx`, three states, tests under `client/src/test/`.
6. [ ] Help text explaining the estimate and limits (where Help text lives; find it).
7. [ ] Specs: Backend_Modules_and_Routes, Data_Model_and_Integrations, Frontend_Modules_and_Routes, Implementation_Status; `scripts/verify.sh docs`.
8. [ ] `scripts/verify.sh all`; re-read the issue; delete this file; open the PR.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written, branch created | none | n/a |
| 1 | `fit_forecast` in `server/app/forecast.py` with 15 unit tests (failed first: module missing) | `python -m pytest tests/unit/test_forecast.py -q` in `server/` | 15 passed |
| 2 | `ResourceForecast` model, hand-written migration `b7e2a9c4d518` (`flask db migrate` has no `--multidb` here), round-trip test and runner (failed first: no table) | `python -m pytest tests/unit/test_forecast_migration.py tests/unit/test_forecast.py -q` | 16 passed |
| 3 | `compute_forecasts()` (hourly-averaged, 3 fixed queries plus one bulk insert, cap `MAX_SERIES_PER_RUN`, paused skipped) and scheduler job `resource_forecast` every 30 min; tests in `test_forecast_job.py`, `test_scheduler.py` (failed first: no function) | `python -m pytest tests/unit/test_scheduler.py tests/unit/test_forecast_job.py tests/unit/test_forecast.py -q` | 35 passed |
| 4 | `GET /system/forecast` (`server/app/api/system/forecast.py`; either `system.dashboard` or `system.services`; `limit`, `hostname`), registered in `api/system/__init__.py`; 12 route tests (failed first) | `python -m pytest tests/unit/test_forecast_routes.py -q` | 12 passed |
| 5 | Added the "not enough data yet" backend state: `Kind='insufficient'` rows (nullable estimate columns, migration edited in place), `enough_data()`, route returns `insufficient` list (tests failed first) | forecast, job, route, migration and scheduler tests | 52 passed |
| 6 | Frontend: `types/forecast.ts`, `hooks/useForecasts.ts`, `ForecastList` on Dashboard, badge in `ServiceStatusTable` (wired from `SystemStatusPage`), tests (failed first: modules missing) | vitest ForecastList, ServiceStatusTableForecast, DashboardPage, SystemStatusPage; `tsc -b`; lint (no warnings on new files) | all passed |

## State for the next session

- Last check run (exact command): `cd server && python -m pytest tests/unit/test_forecast.py -q`
- Result (first failing lines, or "green"): green, 15 passed
- Hypothesis: NCPA metric names are `disk/logical/<part>/used_percent` and `memory/virtual/percent` (see `server/tests/unit/test_dashboard.py:242`); `ServicePerfData` joins `ServiceStatus` for the timestamp.
- Route now returns `{forecasts: [...], insufficient: [{hostname, service_name, metric, sample_count, window_hours}]}`. Full unit suite was started in the background earlier; check result before finishing.
- Next action (step 6): find where Help text lives (grep the client for a Help page / `help`), add a section explaining how the estimate is calculated and its limits, with a test. Then step 7 specs. Full backend unit run on this Windows machine has many unrelated failures (platform), compare against a clean `origin/main` worktree before concluding. Old step 5 text follows, ignore: write the Vitest tests first (`client/src/test/ForecastList.test.tsx`, a badge test for `ServiceStatusTable`), then `client/src/types/forecast.ts`, `client/src/components/dashboard/ForecastList.tsx`, wire into `client/src/pages/DashboardPage.tsx` and the badge into `client/src/components/system-status/ServiceStatusTable.tsx` (+ its page). Route JSON is snake_case: hostname, service_name, metric, kind, threshold, crossing_at, slope_per_hour, r_squared, sample_count, window_hours, current_value, unit, computed_at. Old step 4 text follows, ignore: write `server/tests/unit/test_forecast_routes.py` first for `GET /api/system/forecast` (login, permission, ordering by soonest, empty), then `server/app/api/system/forecast.py` and register it in `server/app/api/system/__init__.py`. Check whether `require_permission` accepts either `system.dashboard` or `system.services`. Full unit run was started in the background to find unrelated Windows failures (`test_automation.py::TestSecurityCheck` fails on this machine, likely unrelated). Old step 3 text follows, ignore: write `server/tests/unit/test_forecast_job.py` first for `compute_forecasts()`; then implement it in `server/app/forecast.py` and register it in `server/app/scheduler.py`. (Old step 2 text follows, ignore:) Add model `ResourceForecast` to `server/app/system_models.py`, write the migration test first (copy the pattern of `server/tests/unit/test_maintenance_migration.py`), then `flask db migrate --multidb` and review it. Head revision is `d117f3b8a053`.

## Decisions and notes

- The existing `test_maintenance_migration.py` fails on this Windows machine (temp-dir cleanup of an open SQLite file, `PermissionError` after the report prints). Not caused by this branch; the forecast runner uses `ignore_cleanup_errors=True`.

- Display only (user, 2026-10-17). Notification delivery needs #132 and #153 and a settings UI; record as a follow-up issue (not yet created on GitHub; ask the user).
- The issue asks for a lab report comparing the forecast with a real disk fill. That needs a lab appliance; it cannot be produced here and will be listed as not verified.
- Forecasts are never written into Nagios state or config; the job only reads history.db and writes one table in system.db.
