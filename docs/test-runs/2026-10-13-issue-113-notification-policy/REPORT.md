# Test run: issue-113-notification-policy

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | `6fb8df73` (working tree unchanged application code during run) |
| Plan | `docs/issues/issue-001.md` §G; approved repository Docker lab |
| Tester | OpenCode agent |
| Environment | Docker local lab, Nagios Core 4.5.11, isolated `10.78.0.0/24`, existing seeded appliance upgraded to issue migration |
| Raw evidence | Local development host `/tmp/opencode/issue113-lab-*.log`; live container `/usr/local/nagios/var/nagios.log` (not committed) |

## Result

**Overall: Partial.** Config validation and host/service notification timing passed in the Docker lab; browser UI interaction and actual email delivery were not observed. The first smoke attempt failed because the existing seeded appliance had not run the new migration; after `flask db upgrade`, the repeat passed. Docker is not the installer-built VM specified in the issue.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Migration and discovery smoke | Pass | Initial discovery failed with missing policy table; upgraded existing lab database and reran `scripts/lab smoke`: 9/9 checks passed. `issue113-lab-smoke*.log` | — |
| Custom policy apply and `nagios -v` | Pass | PUT of quiet hours covering current local day succeeded; `nagios -v` checked 6 time periods, 6 hosts, 29 contacts, 0 errors/warnings. Generated `pinpoint-contact` had `register 0` and the custom period; host objects referenced it. Container command output observed interactively. | — |
| Forced DOWN during quiet window | Pass | After stopping one isolated target and sending `PROCESS_HOST_CHECK_RESULT`, Nagios logged the HARD DOWN for `issue113 quiet test` and zero matching `HOST NOTIFICATION` events. Raw Nagios log in container. | — |
| Forced DOWN outside quiet window | Pass | Restored target, removed quiet window through the policy API, then forced DOWN; Nagios logged 28 matching `HOST NOTIFICATION` events for `issue113 outside test`. Raw Nagios log in container. This is Nagios notification dispatch, not inbox delivery. | — |
| Service CRITICAL inside/outside quiet window | Pass | Enabled the SSH plugin in the lab; five services attached, `nagios -v` then checked 13 services with zero errors/warnings. A forced service CRITICAL reached HARD in both windows: zero matching `SERVICE NOTIFICATION` during quiet hours, 28 matching notifications after restoring 24x7. The target SSH daemon was restarted and service reset to OK afterward. Raw Nagios log in container. | — |
| Browser settings flow | Skipped | API was exercised with a cookie-session script; browser card was not driven. | — |
| Installer-built VM and actual email | Skipped | Repository Docker lab was approved; installer/systemd and mail delivery are outside this run. | — |

## Deviations from the plan

The issue requests a VM service CRITICAL exercise; this approved Docker run covered both host DOWN and service CRITICAL after enabling the SSH plugin. The first run on existing lab state required a manual database upgrade; `scripts/lab up` seeds/upgrades only on first initialization. The lab's accelerated check interval does not represent production renotification timing.

## Follow-up

- Defects found: none confirmed from this run. Existing-container migration handling is a lab limitation; fresh initialization runs migrations.
- Cases to repeat: browser save/reload and installer-built VM/email delivery if required for sign-off.
- Policy restored to no quiet hours and isolated target restarted after testing.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
