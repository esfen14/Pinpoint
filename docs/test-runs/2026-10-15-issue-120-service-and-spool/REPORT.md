# Test run: issue-120-service-and-spool

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `420e55d9` deployed on the appliance (the consumer fix); the later commits only merge `main` and change documents and the migration's parent |
| Plan | Follow-up to [2026-10-15 issue-120-event-handler](../2026-10-15-issue-120-event-handler/REPORT.md): the cases that run skipped |
| Tester | Claude Code agent for the project owner, who approved running on this appliance |
| Environment | Same existing lab appliance as the first run; databases already at `e4a7c1d9b305` |
| Raw evidence | On the appliance: `/usr/local/nagios/var/nagios.log`, the `REMEDIATION_RUN` table and the service journal. Not committed |

## Result

**Overall: Partial.** A service-scope action ran live on a real PinPoint-generated service, and forged, malformed, oversized, symlinked and replayed spool files were all handled safely on the live system. A live SOFT state could not be produced, and the Remediation page was not opened in a browser.

Totals: Pass 7, Fail 0, Blocked 0, Skipped 3.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| A plugin attaches one generated service so a service action can be tested | Pass | Enabling `check_tcp` through the Plugin Manager API attached exactly one service, `http-proxy-8080-tcp` on `dev-8f4ce9`; Nagios stayed active | |
| A service-scope action puts the handler on that service only | Pass | After `POST /api/system/remediation/actions` (201), `hosts.cfg` had one service `event_handler` (on that service) and the earlier host one; `nagios -v` 0 warnings, 0 errors | |
| A hard CRITICAL on the covered service gives exactly one run | Pass | Nagios log: `SERVICE EVENT HANDLER: ...CRITICAL;HARD;1`; run row 6: `SUCCEEDED`, output `recorded`. Three CRITICAL results in a row changed state once, so one event and one run | |
| A recovery on a service gives no run | Pass | Nagios log: `SERVICE EVENT HANDLER: ...OK;HARD;1`; no new run row | |
| Forged, malformed, oversized and symlinked spool files are discarded | Pass | Four files written into the spool (one valid event owned by `pinpoint`, one non-JSON text, one 3000-byte file, one symlink to `/etc/hostname`, all owned by `nagios` except the first): four "discarded a spool file" warnings, no run rows, spool empty afterwards, the symlink target unchanged | |
| A replayed copy of a real event does not run the action again | Pass | A `nagios`-owned file with the same host, service, state and last state change as the handled event produced no second run (no discard warning either, so it passed validation and was recognised as a repeat) | |
| Discard messages and the journal carry no file content | Pass | The malformed file contained the text `password=hunter2`; searching the service journal for `hunter2` found 0 matches | |
| A SOFT state gives no run | Skipped | Nagios treats a passive service result as hard on the first one, so no live SOFT could be produced; unit tested only | |
| Browser: Remediation page | Skipped | No login was available to the agent: the bootstrap administrator's password is not known, and creating a new administrator was refused by the permission system. The page is covered by 25 component tests | |
| Byte-identical config with no action | Skipped | Unit tested only | |

## Deviations from the plan

- Passive results were used to force states; notifications and active checks for the test service and host were switched off for the run and switched back on afterwards.
- Cleanup: the service action was deleted and `check_tcp` disabled again, so the generated config has no services and only the host action `lab-120-record-only` remains. `nagios -v` is clean.
- One spool file (the replay) is evidenced by absence: no row and no discard warning. The duplicate-ignored line is logged at INFO, which the service does not show by default.

## Follow-up

- A live SOFT state needs an active-check failure (a service that really fails twice before the third attempt); repeat when a lab service can be made to fail on demand.
- The Remediation page walk-through is still outstanding; the owner can do it with the checklist in section 8 of `docs/plans/Event_Handler_Design.md` once a login works.
- The INFO-level logging observation from the first run is unchanged.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
