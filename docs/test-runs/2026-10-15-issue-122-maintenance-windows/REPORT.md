# Test run: issue-122-maintenance-windows

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `0883693c` |
| Plan | Issue #122 section G lab cases (no separate plan file) |
| Tester | Claude Code (agent) on the issue #122 branch |
| Environment | Docker local lab (`scripts/lab`): Ubuntu 22.04 appliance, Nagios Core 4.5.11 with `interval_length=10`, lab network 10.78.0.0/24, fresh database after `scripts/lab reset` and `scripts/lab smoke` (6 hosts up). Working tree of the issue branch synced with `scripts/lab sync`; the commit above is the branch base, the run used uncommitted work from the same branch |
| Raw evidence | Lab appliance `/usr/local/nagios/var/nagios.log` and `status.dat` (not committed); the driving scripts were temporary |

## Result

**Overall: Partial.** Creating, dispatching, suppressing and cancelling maintenance windows
works against a real Nagios 4.5.11. Not covered: a recurring window across a restart on the
appliance, service downtime for a monitored plugin service (the lab had no plugin services on the
target hosts), a failed send on the appliance, the browser UI, and an installer-built appliance.
One defect was found and fixed during the run (case 1).

Totals: Pass 8, Fail 0, Blocked 0, Skipped 4.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| 1 Create a one-off window for one device through the API | Pass | First attempt returned 400 "timeZone is not a known time zone" for `UTC`: the appliance image has no tz database, so `zoneinfo` could not load any zone. Fixed in this branch (`UTC` needs no database; `tzdata` added to `requirements.txt`) and repeated: 201 | fixed in branch |
| 2 Dispatcher hands the occurrence to Nagios before it starts | Pass | Within one 60 s tick the occurrence was `sent` (1 attempt); `nagios.log` shows `EXTERNAL COMMAND: SCHEDULE_HOST_DOWNTIME;<host>;<start>;<end>;1;0;0;PinPoint;PinPoint maintenance window 1 starting <epoch>` | |
| 3 Downtime is visible in PinPoint after the next poll | Pass | After the start, `GET /network-health/hosts` showed `in_downtime` true for the 6 hosts and `GET /network-health/services` showed 8 of 8 services in downtime (all-devices window; 6 `SCHEDULE_HOST_DOWNTIME` and 8 `SCHEDULE_SVC_DOWNTIME` accepted, 14 new downtime entries in `status.dat`) | |
| 4 Notifications are suppressed during the window | Pass | web01 and web02 stopped (`scripts/lab break … all`) while the all-devices window was open; both reached `DOWN;HARD`; 0 `HOST NOTIFICATION … ;DOWN;` lines were logged for either | |
| 5 Cancel another window removes its downtime | Pass | Window B (web02) cancelled through the API: response `cancelled`, `nagios_synced` true; `nagios.log` shows `DEL_DOWNTIME_BY_HOST_NAME;<web02>;;;PinPoint maintenance window 2 starting <epoch>`; `status.dat` kept only window A's downtime | |
| 6 Cancelling the running window removes host and service downtime and notifications resume | Pass | Window C cancelled: one `DEL_DOWNTIME_BY_HOST_NAME` per host; `status.dat` fell from 15 downtime entries to 1 (window A's, untouched); web02's DOWN notifications then reached 28 contacts, while web01 stayed silent because window A (still active) covers it | |
| 7 Invalid body is rejected | Pass | A window whose end equals its start returned 400 | |
| 8 Cancel by comment touches only that occurrence | Pass | Cancelling B and C left window A's downtime in `status.dat` | |
| 9 Recurring window creates the next occurrence once after a PinPoint restart | Skipped | Covered by unit tests (`test_maintenance.py`: second run and a restart do not send again); not run on the appliance | |
| 10 Service downtime for a plugin-monitored service | Skipped | The lab targets had no plugin services (Plugin Manager not enabled for them); service downtime was exercised on `localhost`'s 8 services only | |
| 11 Nagios refuses the command (failed state) | Skipped | Covered by unit and route tests with the pipe mocked; Nagios was not stopped on the appliance | |
| 12 Maintenance page in a browser | Skipped | Covered by vitest tests only; `scripts/lab ui` was not run | |

## Deviations from the plan

The run used the API and the real scheduler job (no code was called directly). Window start times
were set 1 to 2 minutes ahead so the lab's 60 s dispatcher tick and 10 s Nagios intervals fit
the session; lead time (10 minutes) is therefore not what was exercised here, only that the
occurrence is sent before it starts. `scripts/lab sync` was used after the first fix; the database
had been recreated with `scripts/lab reset` first because the previous lab database predated the
current schema (`SYSTEM_SETTINGS.Retry_Interval` missing), which is unrelated to this change.

## Follow-up

- Defects found: the missing tz database (case 1) was found and fixed in this branch, so there is no separate issue.
- Cases to repeat in the next run: 9 to 12, on an installer-built appliance, after enabling plugins for the lab targets.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
