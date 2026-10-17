# Test run: 2026-10-17-issue-155-remediation-safety

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `b4bbefec` (branch `issue-155-remediation-safety-controls`, merged with main at `6bd763c`) |
| Plan | Issue #155 section G, driven through the API on the appliance (no browser) |
| Tester | Claude Code, with the owner's approval for each change on the appliance |
| Environment | Ubuntu 22.04.5 lab appliance reached over Tailscale; Nagios Core 4.5.11; app deployed by copying the branch over the main build; database upgraded in place (migration `f155a3c7d2b1`, both databases) |
| Raw evidence | Command output in the session transcript; not committed |

## Result

**Overall: Partial.** The kill switch, all four skip reasons, stalled detection, interrupted-run handling, retention, the spool cap, input validation and the audit trail were proven on the appliance. The 403 path and the browser checks (E7 to E9) were not run live and rest on unit and frontend tests.

Totals: Pass 11, Fail 0, Blocked 0, Skipped 4.

## Cases

| Case | Result | Notes |
|---|---|---|
| Normal run (control) | Pass | A `record_only` action matched a fake HARD CRITICAL event and the run ended `succeeded`. |
| E1 kill switch off | Pass | `PUT /api/system/remediation/settings {"enabled":false}`, then one event: run recorded as `skipped_kill_switch` with the reason text, nothing ran, no restart needed. Health showed 1 run and 1 skipped in 24 h. |
| Switch back on | Pass | Next event ran and ended `succeeded`. |
| E4 stalled | Pass | Web service stopped and a second copy started without the scheduler. Last tick froze; `stalled` was false 44 s later and true 74 s later (limit 45 s). |
| E5 interrupted | Pass | A run left `running` became `interrupted` after a restart ("PinPoint stopped while this action was running."); still one row, not run again. |
| E6 validation and audit | Pass | `retentionDays: 2` returned 400 (range 7 to 3650). Both switch changes appear in the configuration log as `remediation_setting`. |
| E2 acknowledged | Pass | Real host `gateway` (down) acknowledged through the PinPoint API. The acknowledgement reached the status data after about 130 s (status poll). Then an event gave `skipped_acknowledged`. With `Run when acknowledged` turned on, the same event ran and ended `succeeded`. This also confirms that #132 acknowledgements reach the field the check reads. |
| E2 Maintenance Mode | Pass | Maintenance Mode set on in the database (the Settings API needs a versioned full body), then an event for a `record_only` action gave `skipped_maintenance`, so it skips every action type. Switched off afterwards. |
| E2 scheduled downtime | Pass | A real downtime window on `gateway` was created through the maintenance API. Once the status showed `in_downtime`, an event gave `skipped_downtime`. Window cancelled afterwards. |
| E3 spool cap | Pass | 1010 event files written at once. The consumer kept the newest 1000 and dropped the 10 oldest; health showed `droppedTotal: 10` and a drop time. |
| E3 retention | Pass | A run backdated 100 days and one 1 day old were inserted with retention at 90 days. Calling the purge job removed only the 100-day row. Test rows deleted afterwards. |
| E6 403 without permission | Skipped | No restricted account used. Covered by API unit tests. |
| E7 health card, stalled banner | Skipped | Not checked in a browser. Frontend tests cover it. |
| E8 confirmation and persistence | Skipped | Not checked in a browser. Persistence of the setting was seen through the API only. |
| E9 skip reasons in run log | Skipped | The API returns them; the log display is covered by frontend tests. |

## Deviations from the plan

Everything was driven through the API from the appliance itself, with fake events written to the spool as the `nagios` user. No real host was taken down; the acknowledged and downtime cases used the host that was already down, and both were undone. The test action was deleted afterwards and the kill switch left on.

## Follow-up

- Defects found: none.
- Cases to repeat in the next run: the 403 without the permission, and E7 to E9 in a browser.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
