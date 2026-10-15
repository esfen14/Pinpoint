# Test run: issue-79-rebuilt-inbox

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `4ed80435f088ddda26302a44a6008037bdfec933` |
| Plan | Issue [#79](https://github.com/esfen14/Pinpoint/issues/79) finish condition and opt-in recipient browser projects |
| Tester | Codex; owner inbox confirmation pending |
| Environment | Rebuilt Ubuntu appliance, Nagios Core 4.5.11, isolated `10.77.0.0/28` targets; separate checkout and upgraded copies of both baseline databases |
| Raw evidence | Local ignored `test-results/issue79-post165/`; private VM backup/trial state retained by lab owner; no raw evidence committed |

## Result

**Overall: Partial.** Current-main integration, real browser editing and permission enforcement, generated groups, real Nagios transitions and Gmail SMTP acceptance passed. Actual inbox arrival and exclusion still need owner confirmation; PR remains draft.

Totals: Pass 11, Fail 0, Blocked 1, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| V1: ownership and deployment isolation | Pass | Repeated current preflight proves exclusive controller/process and runtime SSH/web ownership on rebuilt appliance. Original tracked source unchanged; separate detached checkout, explicit database URI assertions, SQLite backups, additive migrations and separate service override. `deploy-repeat.log` | — |
| V2: current-main compatibility and full suites | Pass | Merge revision joins both migration parents. Populated upgrade/downgrade/reupgrade and SNMP-only interface recipient regression cases pass. Focused backend 45, frontend 41; full backend 2821 passed/14 skipped, frontend 640, build/lint/docs green. CI all three jobs green on tested commit ([run](https://github.com/esfen14/Pinpoint/actions/runs/38674517921)). Local `issue79-post165-all.log` and integration logs | — |
| V3: authorized browser editor | Pass | Actual browser saves selected IDs, reopens persisted selection, clears to default, reopens empty/default and restores original selection. No API stubbing. `playwright.log` | — |
| V4: browser and API permission denial | Pass | Separate Staff reader completes password change, sees no recipient editor and gets forbidden responses for recipient GET and PUT. Four total Playwright checks pass including authentication setup. `playwright.log` | — |
| V5: selected and default generated groups | Pass | Selected host and generated SSH service use private group with exactly the selected eligible contact. Other host and service use default group containing both controlled eligible contacts. Actual `nagios -v` reports zero errors. `routing-prepare.log`, private generated config and validation log | — |
| V6: real host DOWN routing | Pass | Both targets reach HARD DOWN. Notification log records exactly one chosen recipient for selected host and two for default host. `delivery-verified.log`, private notification log | — |
| V7: real service CRITICAL routing | Pass | Repeated passive SSH results reach HARD CRITICAL, observed in event log. Exact one-versus-two recipient sets match host selection. `delivery-verified.log`, private notification log | — |
| V8: actual SMTP transport | Pass | Installed sendmail/msmtp transport used without replacement/capture. Gmail accepts all 12 problem/recovery messages: SMTP 250 and EX_OK, eight to selected mailbox and four to default-only mailbox. `delivery-verified.log`, private journal export | — |
| V9: bounded live rescan | Pass | Settings asserted exactly `10.77.0.0/28`, five explicit TCP ports and UDP 161; one discovery run succeeds. Stable device recipient IDs before/after match exactly. `rescan.log`, private result JSON | — |
| V10: entirely ineligible fallback | Pass | Save only opted-out reader; host and generated services use default group, no empty private group; actual Nagios validation has zero errors. Restore original selection. `fallback.log` | — |
| V11: restoration | Pass | Targets restored UP/OK and original active-check/notification/flap settings restored. Original service, static site and generated config restored; baseline database/static hashes unchanged and source clean. `delivery-verified.log`, `restore.log`, `baseline-verified.log` | — |
| V12: actual inbox comparison | Blocked | Owner must confirm selected host arrives only in selected mailbox, while default host arrives in both, for DOWN and CRITICAL alerts. SMTP acceptance alone does not prove inbox arrival/exclusion. Requested window: Oct 15, 03:14–03:18 UTC (11:14–11:18 Manila). No mailbox access is available to the agent | [#79](https://github.com/esfen14/Pinpoint/issues/79) |

## Deviations from the plan

The old lab incident is historical. Merged #165 resolves #162 through owner-authorized retirement and rebuild with verified endpoint snapshot restoration; this run uses that rebuilt appliance and its fail-closed preflight. It does not claim the old overwritten source edits were recovered.

An initial deployment assertion stopped before mutation because Git ran as root against a service-owned checkout; Git was rerun as the checkout owner. The temporary API fixture used an incorrect role field and omitted account status; these fixture errors were corrected before testing.

The initial notification driver asserted service state against an unpublished/stale `status.dat` snapshot and exited through its cleanup handler. The same run's event log proves both services reached HARD CRITICAL and dispatched the expected alerts before recovery. A separate verification checks exact event states, recipient sets, 12 SMTP receipts and restored runtime settings; no extra alerts were sent to repair the assertion. The temporary driver now waits for snapshot publication. Original driver output is retained in `real-delivery.log`; the observed behavior was verified in `delivery-verified.log`.

No external mail was intercepted. Reports contain mailbox roles only; addresses and raw SMTP/Nagios evidence remain private.

## Follow-up

- Owner inbox comparison is the remaining original acceptance requirement. Keep PR #160 draft until it is confirmed.
- Preserve historical reports and their original results; this run supplements them.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
