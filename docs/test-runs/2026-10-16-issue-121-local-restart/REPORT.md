# Test run: issue-121-local-restart

| | |
|---|---|
| Date | 2026-10-16 |
| Commit tested | `8869235` (`main` after PR #175, which delivered #121 Parts 8.1 and 8.2) |
| Plan | Issue #121 (`docs/issues/issue-008.md`) sections E and G, Parts 8.1 and 8.2 |
| Tester | Claude Code agent for the project owner, who gave the lab access and approved each change to it |
| Environment | New lab appliance (Ubuntu 22.04, Nagios Core 4.5.11, gunicorn service `pinpoint-gunicorn`). The installer had already placed `/etc/sudoers.d/pinpoint-restart`, the event spool folder and the event handler. The application was updated in place from `edb5036` to `8869235` (fast-forward), then both databases were upgraded by migration `b8e3d5f2a417`, the client was rebuilt and the service restarted. Not a fresh build |
| Raw evidence | On the appliance: `/usr/local/nagios/var/nagios.log`, the journal of `pinpoint-gunicorn`, and the `REMEDIATION_RUN` table. Not committed |

## Result

**Overall: Pass for Parts 8.1 and 8.2.** On a real Nagios, a forced HARD DOWN on a covered host restarted Nagios exactly once and left one audited run. The cooldown, Maintenance Mode and the hourly cap each blocked a restart and recorded why. Every unit outside the list was rejected at creation, and the sudo rule allowed exactly one command. The whole sequence was run twice from a clean action, with the same result. Part 8.3 is reported separately.

Totals: Pass 16, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Part 8.2: drop-in installed correctly | Pass | `/etc/sudoers.d/pinpoint-restart` is `root:root` mode 0440 with one line: `pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl restart nagios`. No wildcard, no shell | |
| Part 8.2: `visudo -c` passes | Pass | All sudoers files parse OK | |
| Part 8.2: allowed restart works | Pass | As `pinpoint`, `sudo -n /usr/bin/systemctl restart nagios` exited 0; the Nagios process id changed and the service stayed active | |
| Part 8.2: other units and commands are refused | Pass | `restart ssh`, `restart nagios extra`, `restart pinpoint-gunicorn`, `stop nagios`, `restart nagios.service` and `sh -c id` were all refused with "a password is required"; none ran | |
| Part 8.2: existing rules unchanged | Pass | `sudo -l` for `pinpoint` still lists `pinpoint-apply-smtp` and `systemctl reload nagios`; the reload ran with exit 0 | |
| Part 8.2: `sudo -l` shows no wildcard or shell | Pass | Three entries only | |
| Part 8.1: unit outside the list rejected at creation (8 cases) | Pass | `POST /api/system/remediation/actions` returned 400 with a per-field message for `sshd`, `pinpoint-gunicorn`, `nagios; id`, `../../bin/sh`, `nagios.service`, an extra `cmd` parameter, a missing unit and a list instead of a string | |
| Part 8.1: the API offers only valid choices | Pass | `GET /api/system/remediation/action-types` lists `nagios` as the only choice for `restart_local_service` | |
| Part 8.1: a unit outside the list is refused at run time | Skipped | Cannot be produced through the API, which stops it at creation. Covered by `test_remediation_actions.py` | |
| Part 8.1: a HARD failure restarts once and is audited | Pass | Passive DOWN on a covered host: the handler fired, one run row `succeeded`, output "Restarted nagios; exit code 0.", Nagios process id changed once. The UP/HARD event produced no run | |
| Part 8.1: a repeat inside the cooldown is skipped | Pass | Run row `skipped_cooldown`: "Within the 60 second cooldown since the last run for this host and service."; no restart | |
| Part 8.1: Maintenance Mode blocks the restart | Pass | Run row `failed`, output "Refused: Maintenance Mode is on."; the Nagios process id did not change | |
| Part 8.1: the hourly cap blocks the restart | Pass | Run row `skipped_hourly_cap`: "Reached the limit of 2 runs per hour for this action."; no restart | |
| Part 8.1: output holds no secrets | Pass | Recorded output is fixed text only; the command's own output is never kept (see `run_restart_local_service`) | |
| Part 8.1: no shell | Pass | The command is built as an argument list in code; unit names with shell characters never reach it (rejected at creation) | |
| Repeat of the whole 8.1 live sequence from a clean state | Pass | Same outcomes in the same order: succeeded, skipped_cooldown, failed (Maintenance), skipped_hourly_cap | |
| Migration `b8e3d5f2a417` on the live databases | Pass | Both databases moved from `a4c8e1b7d933` to `b8e3d5f2a417`; permissions sync added nothing new | |

## Deviations from the plan

- The first live pass used a short wait and the second run happened more than 60 seconds after the first, so it ran instead of being skipped. This was a test-timing mistake, not a defect; the cooldown was then tested with a window that really applied.
- The hourly cap was tested with a cap of 2 after editing the action. Deleting a test action and creating another gave the new action the same id (SQLite reuses ids), so the new action counted the old action's runs against its cap. See Follow-up.

## Follow-up

- `RemediationRun.Action_Id` is deliberately not a foreign key, so runs survive a deleted action. SQLite reuses ids, so a new action can inherit a deleted action's cooldown and hourly-cap history. To be filed as an issue; it does not affect normal use.
- Cases to repeat: none for 8.1 and 8.2.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
