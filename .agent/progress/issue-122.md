# Issue #122: System Implementation Add Maintenance Windows That Create Nagios Scheduled Downtime and a Management Page

Branch: `issue-122-maintenance-windows`
Status: in-progress

## Finish condition

- [ ] E1 one-off window creates Nagios downtime before start, ends itself at end
- [ ] E2 recurring window creates next occurrence once, even after restart
- [ ] E3 cancel removes pending and active downtime
- [ ] E4 Nagios failure retried a bounded number of times, then shown failed
- [ ] E5 invalid -> 400, no permission -> 403
- [ ] E6 PinPoint Maintenance Mode unchanged
- [ ] E7 UI: create, edit, cancel, see status and next occurrence
- [ ] E8 times entered/shown in display time zone, stored UTC
- [ ] E9 failed occurrence visible with reason
- [ ] E10 two maintenance concepts labelled apart
- [ ] E11 PageAccess/App tests updated and pass
- [ ] F deliverables: code, routes, migration + sync-permissions note, frontend, unit/frontend/integration tests, spec files, help text/admin guide, verify.sh all + docs/test-runs lab report

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| MaintenanceWindow model + migration | F | migration round-trip test |
| Dispatcher job, de-dup | E1, E2 | tests/unit/test_maintenance.py |
| Routes, validation, permission | E5 | tests/unit/test_maintenance_routes.py |
| Cancel removes downtime | E3 | unit + lab report |
| Failure retry | E4 | unit |
| Audit entries | F | route/unit tests |
| Frontend page, form, tz | E7-E9 | client/src/test/MaintenancePage.test.tsx |
| Wording / link | E10 | frontend test |
| Route, sidebar, page permission | E11 | PageAccess/App tests |
| Out of scope: Maintenance Mode behaviour | E6 | existing test_automation.py |

## Plan

1. [ ] commands.py: add cancel_downtime_by_host_name (allowlisted) + tests (server/app/nagios/commands.py, tests/unit/test_nagios_commands.py)
2. [ ] Models MaintenanceWindow + MaintenanceOccurrence, migration, permission maintenance.manage (system_models.py, migrations, seed.py, conftest.py)
3. [ ] app/maintenance.py: recurrence expansion (DST), dispatcher, cancel; scheduler job (scheduler.py)
4. [ ] Routes api/system/maintenance.py + tests
5. [ ] Frontend: types, api, page, components, route, sidebar, pageAccess, wording link in SystemSettings
6. [ ] Frontend tests, PageAccess/App tests
7. [ ] Specs, Implementation_Status, help/admin guide; lab report; verify.sh all; PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Lab check on Docker Nagios 4.5.11: SCHEDULE_HOST_DOWNTIME + SCHEDULE_SVC_DOWNTIME then `DEL_DOWNTIME_BY_HOST_NAME;host;;;comment` | status.dat downtime count 2 -> 0 | cancel command verified |

## State for the next session

- Last check run (exact command): lab Nagios downtime schedule/cancel script
- Result (first failing lines, or "green"): green; cancel verified
- Hypothesis: n/a
- Next action: step 1, add cancel_downtime_by_host_name to server/app/nagios/commands.py with a test

## Decisions and notes

- Cancel command (verified in Docker lab, Nagios 4.5.11): `DEL_DOWNTIME_BY_HOST_NAME;<host>;;;<comment>` removes host and service downtime whose comment matches exactly. Each occurrence uses comment `PinPoint maintenance window <id> <start-epoch>`.
- Host downtime alone does not set service downtime depth, so send per-service downtime too.
- Recurrence is wall-clock in the creator's IANA zone (stored on the window) so daily/weekly keep local time across DST.
- Lab report in docs/test-runs still to be written from the lab runs.
