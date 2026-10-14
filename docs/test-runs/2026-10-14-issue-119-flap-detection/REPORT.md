# Test run: issue-119-flap-detection

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | `efbd2525` (branch `issue-119-flap-detection-settings`, stacked on the unmerged #123 commit `5d0b5dd6`) |
| Plan | none (issue #119 section G, lab bullet) |
| Tester | Claude Code session for the repository owner |
| Environment | Lab appliance `pinpoint` (Ubuntu 22.04.5, Nagios Core, existing install, not a `vmlab fresh` build). Existing databases upgraded in place: `a4c8e1f6d392` to `c5e2a8f4d716` (#123 migration `b7d3f1a9c8e5` then this issue's migration). Code and a freshly built client copied over the existing app; backups of code, databases and `hosts.cfg` kept on the appliance in `/tmp/pp_backup_119`. |
| Raw evidence | Console output of the test script in the session; nothing committed. The script signed in as the first existing administrator inside the app, so no account or password was created or used. |

## Result

**Overall: Partial.** Settings, generated Nagios config, validation, rollback-free
apply, the flapping history endpoint and the Flapping-only filter all behaved as
specified on the live appliance, and Nagios accepted every generated config. A
deliberate flap (rapid state changes on one service) was not forced, and the
browser screens were not clicked through.

Totals: Pass 8, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Both migrations upgrade the existing databases | Pass | `flask db current` showed `a4c8e1f6d392` before and `c5e2a8f4d716 (head)` for both databases after; app restarted and answered HTTP 200; no errors in the service log for 10 minutes | |
| Defaults leave generated config unchanged | Pass | Start state: detection on, no thresholds; `hosts.cfg` had no flap lines; `nagios -v` 0 warnings, 0 errors | |
| Custom thresholds written and accepted by Nagios | Pass | `PUT /api/system` low 10 / high 30 returned 200; `hosts.cfg` gained `low_flap_threshold 10` and `high_flap_threshold 30`; `nagios -v` 0 warnings, 0 errors | |
| Invalid thresholds rejected | Pass | low 40 / high 10 returned 400 ("Low flap threshold must be lower than the high flap threshold."); high 101 returned 400; `hosts.cfg` unchanged | |
| Detection off written and accepted | Pass | 200; `hosts.cfg` had only `flap_detection_enabled 0` (thresholds dropped); `nagios -v` 0 warnings, 0 errors | |
| Restore to defaults | Pass | 200; flap lines gone from `hosts.cfg`; settings read back as on / empty / empty; `nagios -v` clean | |
| Flapping history endpoint | Pass | `hours=24` and `168` listed two real hosts that Nagios had flagged (58 and 17 flagged snapshots); `hours=1` listed none; `hours=2` returned 400; `global_flap_detection_enabled` was true | |
| `flapping=true` filter on hosts and services lists | Pass | Both returned only items with `is_flapping` true (none were flapping at that moment, so 0 results of 17 hosts and 8 services) | |
| Force a flap on a service and see it flagged in Nagios | Skipped | Not done: rapid state changes would risk real alert emails to the configured contact. History shown above comes from real earlier flapping instead | |
| Settings card, table filter and drawer in a browser | Skipped | The built client was deployed and its bundle contains the new text, but the screens were not clicked through; covered by 522 passing frontend tests | |

## Deviations from the plan

The issue asks to toggle a service rapidly; that was skipped for the reason above.
The appliance already ran #123 only as code in the repository, not deployed, so
its migration ran in the same upgrade.

## Follow-up

- Defects found: none.
- Cases to repeat in the next run: a forced flap with notifications disabled for
  the service, and a click-through of Settings, the two tables and the drawer.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
