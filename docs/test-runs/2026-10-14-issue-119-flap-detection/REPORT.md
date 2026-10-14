# Test run: issue-119-flap-detection

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Round 1: `efbd2525`. Round 2 (merged with `origin/main`, including #113 notification policy and #132 command channel): `465f8c8f`. Both are on branch `issue-119-flap-detection-settings`, which also carries the unmerged #123 commit `5d0b5dd6`. |
| Plan | none (issue #119 section G, lab bullet; issue #123 exit condition) |
| Tester | Claude Code session for the repository owner |
| Environment | Existing lab appliance `pinpoint` (Ubuntu 22.04.5, Nagios Core, not a `vmlab fresh` build, 16 generated hosts, no generated services, 8 stock `localhost` services). Round 2 first rolled the databases back to `a4c8e1f6d392` with the old code, then deployed the merged code and upgraded to `c5e2a8f4d716` through `143c48cd6663` and `b7d3f1a9c8e5`. Backups of code, databases and `hosts.cfg` are in `/tmp/pp_backup_119` and `/tmp/pp_backup_119b` on the appliance. |
| Raw evidence | Console output of the test scripts in the session; nothing committed. The scripts signed in as the first existing administrator inside the app, so no account or password was created or used. |

## Result

**Overall: Pass for what the appliance can show, with one gap.** Flap settings,
retry interval and maximum check attempts reached the generated Nagios config
and the running Nagios, were validated, and rejected bad input. A deliberately
forced flap was flagged by Nagios, picked up by Pinpoint and listed in the flap
history and the Flapping-only list. The gap: this appliance has no generated
services, so the service side of both features is covered by the unit tests only.

Totals: Pass 13, Fail 0, Blocked 0, Skipped 2.

## Round 2 in plain words

1. The appliance was put onto the merged code. Its database had been upgraded in
   my old migration order, so it was rolled back and upgraded again in the order
   now on `main`. All three upgrades ran cleanly and the app came back up.
2. Retry interval 2 minutes and 5 attempts were saved. All 16 generated hosts
   changed from 3 attempts and no retry line to 5 attempts and a 2 minute retry.
   Nagios accepted the file, and after its reload the running Nagios showed the same
   values for the 16 hosts (the stock `localhost` host keeps its own 10 attempts and
   was not touched). Bad values (retry longer than the check interval, 11
   attempts) were refused. Settings were then put back and the file went back to
   the original.
3. Flap thresholds 10 and 30 were saved, and the running Nagios showed them on a
   test host (10 and 30). That host's notifications were turned off first, so no
   alert email could go out. Then 30 results alternating UP and DOWN were sent.
   Nagios marked the host as flapping (100 percent state change), Pinpoint
   picked it up within a minute, and the flap history and the flapping list both
   showed it. Then 30 UP results were sent, notifications were turned back on,
   and the settings were restored. A final check of Nagios's status file showed
   all 17 hosts with notifications on, and `nagios -v` reported 0 warnings and 0 errors.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Both migrations upgrade the existing databases | Pass | Round 1: `a4c8e1f6d392` to `c5e2a8f4d716`. Round 2: rollback to `a4c8e1f6d392`, then upgrade through `143c48cd6663`, `b7d3f1a9c8e5` to `c5e2a8f4d716 (head)`, for both databases; app restarted with no errors | |
| Defaults leave generated config unchanged | Pass | No flap lines, 3 attempts and no retry line on all 16 hosts; `nagios -v` 0 warnings, 0 errors | |
| Custom flap thresholds written and accepted | Pass | `low_flap_threshold 10`, `high_flap_threshold 30` written; `nagios -v` clean; running Nagios showed 10 and 30 on the test host | |
| Invalid flap thresholds rejected | Pass | low 40 / high 10 and high 101 returned 400; config unchanged | |
| Flap detection off written and accepted | Pass | `flap_detection_enabled 0` only; `nagios -v` clean | |
| Restore to defaults | Pass | Flap lines gone; settings read back as on / empty / empty | |
| Flapping history endpoint | Pass | Round 1: two real flapping devices listed, `hours=2` returned 400. Round 2: the forced-flap host listed with 2 flagged snapshots, flapping now | |
| `flapping=true` filter on the hosts list | Pass | Round 2: returned exactly the one flapping host (total 1) | |
| Forced flap flagged by Nagios | Pass | Host `is_flapping=1`, `percent_state_change=100.00` in `status.dat`; thresholds 10 and 30 in `objects.cache`. The config thresholds are in `objects.cache`; the flapping flag itself is in `status.dat` | |
| Retry interval and attempts in every generated host | Pass | 16 of 16 hosts: `max_check_attempts 5`, `retry_interval 2` in the file and in the running Nagios; `nagios -v` clean | |
| Retry interval and attempts validation | Pass | Retry 6 with check interval 5 returned 400; attempts 11 returned 400 | |
| Settings restored after the test | Pass | Retry 1, attempts 3, flap on with no thresholds; hosts file back to 3 attempts and no retry line | |
| No host left with notifications off | Pass | All 17 hosts `notifications_enabled=1` in `status.dat` after cleanup | |
| Retry, attempts and flap settings on a generated service | Skipped | The appliance has no generated services (8 stock `localhost` services only); covered by the unit tests | |
| Settings card, table filter and drawer in a browser | Skipped | The built client was deployed but the screens were not clicked through; covered by 553 passing frontend tests | |

## Deviations from the plan

The forced flap used passive check results on a generated host, because there
are no generated services to flap. Passive results make Nagios treat the changes as
hard state changes, so this shows the flap flag, the config and Pinpoint's
history, not a real network flap. Notifications for the test host were switched
off first. The first two script runs of this round stopped early on a pattern
mistake in my own script, before any flap results were sent; their cleanup ran
and was checked.

## Follow-up

- Defects found: none.
- Cases to repeat in the next run: a generated service (needs a monitored port on
  a discovered device) and a browser click-through of Settings, the two tables
  and the drawer.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
