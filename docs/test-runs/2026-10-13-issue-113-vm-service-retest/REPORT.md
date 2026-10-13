# Test run: issue-113-vm-service-retest

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | Appliance application `1ca2c757` (source same for policy; browser test parametrization was uncommitted during run) |
| Plan | `docs/issues/issue-001.md` §G; issue #113 VM acceptance |
| Tester | OpenCode agent |
| Environment | Fresh installer-built Ubuntu 22.04.5 appliance VM, Nagios Core 4.5.11, five targets on isolated `10.77.0.0/28`; system database created by installer |
| Raw evidence | Local `/tmp/opencode/issue113-vm-fresh.log`, `/tmp/opencode/issue113-vm-smoke.log`, `/tmp/opencode/issue113-ncpa-deploy.log`, `/tmp/opencode/issue113-vm-browser.log`, `/tmp/opencode/issue113-vm-frontend.log`; appliance `/usr/local/nagios/var/nagios.log` (not committed) |

## Result

**Overall: Partial.** VM notification-dispatch comparison and browser policy save/reload passed. Actual mailbox delivery was not inspected, and the first discovery smoke timed out; after NCPA deployment, discovered services were present and the SSH plugin was enabled. The prior VM report mistakenly said Pass before forcing CRITICAL; this is a separate real retest.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Fresh VM installer/health | Pass | `scripts/vmlab fresh issue-113-notification-policy`: 60 passed, zero warnings/failures, database at migration `143c48cd6663`. `issue113-vm-fresh.log` | — |
| VM discovery and service prerequisites | Pass | Initial `scripts/vmlab smoke` timed out at 300 seconds (3 passed, 6 failed). Subsequent `scripts/vmlab ncpa` deployed to five targets (34 passed), and enabling the SSH plugin applied five SSH service checks. This is not a pass for the initial smoke. `issue113-vm-smoke.log`, `issue113-ncpa-deploy.log`; generated `hosts.cfg` inspected on appliance. | — |
| Quiet policy and Nagios config | Pass | API PUT set Tuesday 13:00–16:00 using Nagios server local time. Generated `pinpoint_notify` excluded the interval; host, service and contact directives referenced it. `nagios -v` showed 6 timeperiods and zero errors/warnings. | — |
| Forced service CRITICAL inside quiet window | Pass | At ~14:12 UTC, stopped web02 SSH, injected passive CRITICAL results for `dev-5e1804;ssh-22-tcp` until a HARD CRITICAL appeared at Nagios log timestamp 1791900763. Matching CRITICAL `SERVICE NOTIFICATION` count in the Nagios log: **0**. The target SSH service was restored and a passive OK processed before the second trial. | — |
| Forced service CRITICAL outside quiet window | Pass | Removed the quiet window via versioned API PUT; `nagios -v` again showed zero errors/warnings. Stopped web02 SSH, injected passive CRITICAL results until HARD CRITICAL at timestamp 1791900855. Nagios logged **1** CRITICAL `SERVICE NOTIFICATION` for the same service/contact. Restored web02 SSH and processed an OK result. This proves Nagios dispatch/logging, not inbox delivery. | — |
| VM browser save/reload | Pass | The opt-in Playwright browser test used `LAB_BASE_URL=http://127.0.0.1:18080` and environment-supplied credentials; added a window, saved, reloaded and observed it, then removed/saved (1 passed, 2.5s). GET afterward showed no quiet windows. `issue113-vm-browser.log`. Frontend verification passed with 0 lint errors and 26 warnings (`issue113-vm-frontend.log`). | — |
| Actual email arrival | Skipped | No receiving mailbox was checked; the Nagios log proves a notification command was invoked, not that a message arrived. | — |

## Deviations from the plan

The first discovery smoke did not finish within five minutes. NCPA deployment and SSH plugin activation supplied a real generated service for the policy comparison. Instead of waiting for the 5-minute normal check interval, passive check results were submitted to Nagios's external-command pipe while the target's SSH daemon was actually stopped. The browser test was run directly against the VM nginx port using an environment-selected base URL; credentials were not written to the report or test log.

## Follow-up

- Defects found: none confirmed for issue #113 from this retest. Investigate the initial discovery timeout separately if reproducible.
- Cases to repeat: actual mailbox delivery if required for sign-off; reviewer and CI approval remain external.
- Policy was returned to no quiet hours and web02 SSH restored.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
