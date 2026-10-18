# Test run: module-14-remediation

| | |
|---|---|
| Date | 2026-10-19 (tester's local date; the lab ran the cases on 2026-10-18 UTC, 15:50 to 16:20) |
| Commit tested | Lab runs `43f0df1`; the checkout used for this report is `65a5862c`. The only difference between them is one frontend test file (`client/src/test/RemediationPage.test.tsx`), so the deployed product code matches the checkout. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Module 14 TC-REM-02, 03, 05, 06, 07, 08, 09, 10 |
| Tester / executor mode | Mixed. AI-assisted (Claude) drove the browser UI with a Playwright script on installed Chrome and used SSH for setup, fault injection and Nagios evidence. The lab owner approved the plan, the lab changes, the dummy device and the temporary Nagios config break. |
| Catalog revision and SHA-256 | Checkout `65a5862c`; catalog SHA-256 `ec2b1c3f3b98f73da9b0f5d6656d1565b1405af97a58b2fcc8fe7481fbe5af71` |
| Queue / set / session / batch | No prepared queue (ad hoc run approved by the lab owner in chat). Session 1, one module per branch: `qa-run-module-14-remediation`. |
| Deployed application / installer revision | Application `43f0df1` (git HEAD on the appliance). Installer revision not checked. |
| Baseline / preflight / restoration | Before the run: one action ("Test web01 HTTP", not created by this run), kill switch on, 23 earlier runs in the log. Restoration below. |
| Start / end / time zone | 2026-10-18 15:50 to 16:20 UTC. Appliance in UTC; browser display time zone UTC+08:00. |
| Environment | Ubuntu 22.04.5 lab appliance reached over Tailscale; Nagios Core 4.5.11. Test device was a dummy (`qa-dummy-web`) on `10.77.0.0/28`; no real device was changed and no network scan was run. |
| Raw evidence | Run scratch folder on the tester machine and the appliance's Nagios log and `status.dat`. Not committed. |

## Result

**Overall: Pass.** All eight selected cases behaved as the catalog expects. No product defect was found. TC-REM-01 and TC-REM-04 already have recorded results and were out of scope.

Totals (unique TC): Pass 8, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
Attempts and setup operations are not extra unique cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-REM-02 | Pass | Valid "Record only" action saved and listed (defaults 2 runs/hour, 600 s). Cooldown 10 and 59, runs per hour 0 and 61 were each refused (HTTP 400) with a message beside the field, e.g. "Cooldown must be a whole number of seconds from 60 to 86400." Boundaries 60 s/1 run and 86400 s/60 runs were accepted. Renaming the action saved. | |
| TC-REM-03 | Pass | The enable switch turned an action on and off (PUT 200 each time) and the list showed it. Delete asked "Delete the action …? Its run history stays in the log."; Cancel kept it (0 requests); OK removed it ("Action deleted."). After deleting an action that had a run, that run stayed in the Run log with the action name kept and `actionId` null. | |
| TC-REM-05 | Pass | Two sessions edited one action: the first saved (200); the second was refused with 409 "This action was changed by someone else. Reload and try again." and offered **Reload**, which showed the first editor's value. With Nagios's own check failing, saving a new enabled host-scope action returned 422 "The action could not be applied: Config failed to validate: … Invalid service object directive …", the form stayed open, and nothing was kept. See Deviations. | |
| TC-REM-06 | Pass | Columns Time, Action, Host, Service, State, Outcome, Reason, Operator. The outcome filter (skipped, succeeded), host filter, action filter, From, To and paging narrowed or moved the list as expected; an empty filter shows "No runs match these filters." Skipped runs show their reason (hourly limit, acknowledged, kill switch). The detail drawer shows outcome, notification and output; none of the 23 runs' outputs contained a secret. Observation: the date filter uses UTC days while the table shows local time (see Follow-up). | |
| TC-REM-07 | Pass | Cancel changed nothing (0 requests). After confirming, the panel read "Stopped. No action runs; each covered failure is logged as skipped.", it stayed stopped after a reload, and the Actions tab showed "Paused by the kill switch". The covered Hard failure was logged as Skipped (kill switch) with "Automatic recovery is switched off (kill switch)." and no action ran. After resuming, the panel read "On. Enabled actions run when a covered failure becomes a hard failure." | |
| TC-REM-08 | Pass | The status panel showed last check-in, events waiting, runs, limits hit, skipped and events dropped; its numbers matched the health API and the last check-in advanced on its own. After the Pinpoint service was stopped for 65 s and restarted, a fresh page showed the red banner "Automatic recovery has stopped checking in. Failures are not being handled until it recovers. Last check-in: …" until the consumer checked in again (about 15 s). | |
| TC-REM-09 | Pass | Two enabled Record only actions covered the same service; A without and B with **Run when acknowledged**. The alert was acknowledged while the service was in a soft failure; at the Hard failure A was logged Skipped (acknowledged) with "An operator has already acknowledged this problem." and B Succeeded with output "recorded". | |
| TC-REM-10 | Pass | "Restart a PinPoint host service" offers a fixed list (only `nagios`); "Restart a service on the monitored device" offers a text box **Service to restart**. `my service!` was refused beside the field ("Enter a plain service name such as nagios or apache2."); `apache2` was accepted. Switching the type back and forth cleared the entered value. | |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-REM-02 | E1 valid action saved and listed | 201, row shown | Pass | scratch `rem02.png` | Action deleted |
| TC-REM-02 | E2 invalid values refused beside the field | Cooldown 10/59/86401 and runs 0/61 refused | Pass | run output | |
| TC-REM-02 | E3 edit saved | PUT 200, new name listed | Pass | run output | |
| TC-REM-03 | E1 switch changes state | on and off, PUT 200 | Pass | run output | |
| TC-REM-03 | E2 cancel keeps, confirm removes, runs stay | As stated | Pass | run output; API run 24 | Action deleted |
| TC-REM-05 | E1 second save refused 409 with Reload | As stated | Pass | scratch `rem05_conflict.png` | Action deleted |
| TC-REM-05 | E2 Nagios rejection 422 shows message, nothing kept | As stated | Pass | scratch `rem05_422_new.png` | `templates.cfg` restored: hash identical before and after, `nagios -v` 0 errors, 0 warnings |
| TC-REM-06 | E1 filters narrow, paging works | As stated | Pass | scratch `rem06_filters.png` | None needed |
| TC-REM-06 | E2 skipped run shows its reason | As stated | Pass | scratch `rem06_drawer15.png` | |
| TC-REM-06 | E3 drawer without secrets | 0 of 23 outputs sensitive | Pass | API scan | |
| TC-REM-07 | E1 cancel changes nothing; stopped text; survives reload | As stated | Pass | scratch `rem07_off.png` | Kill switch on |
| TC-REM-07 | E2 covered failure skipped, "Paused by the kill switch" | As stated | Pass | API run 26 | Dummy service restored |
| TC-REM-07 | E3 "On…" after resuming | As stated | Pass | run output | |
| TC-REM-08 | E1 numbers show and refresh | As stated | Pass | run output | None needed |
| TC-REM-08 | E2 red banner after 45 s+ without check-in | Shown after 65 s outage | Pass | scratch `rem08_after_restart.png` | Service active again |
| TC-REM-09 | E1 A skipped as acknowledged | As stated | Pass | scratch `rem09_log.png` | Both actions deleted; alert cleared on recovery |
| TC-REM-09 | E2 B runs, record written | Succeeded, "recorded" | Pass | run output | |
| TC-REM-10 | E1 type-specific fields | As stated | Pass | scratch `rem10.png` | Action deleted |
| TC-REM-10 | E2 bad name refused, plain name accepted | As stated | Pass | run output | |
| TC-REM-10 | E3 switching clears parameters | Value empty after switching | Pass | run output | |

Timing: Hard failures were reached with the app's Check Now (a forced Nagios check) instead of waiting for check intervals; no clock was changed. TC-REM-08 used a real 65-second outage.

## Deviations from the plan

- Actions and the failing service used a dummy device (`qa-dummy-web`, `10.77.0.5`, service on port 110 monitored with `check_tcp`) because the lab has no web VM and real devices must not be touched. Port 80 was unavailable because Apache listens on every address. Enabling the `check_tcp` plugin was needed; its preview showed it matched only that one service.
- Check Now was used to move the service to a Hard failure quickly (TC-REM-07 and 09).
- TC-REM-05 step 3: two earlier attempts returned HTTP 200 instead of 422 while Nagios's check was failing. They saved a rename and an enable switch on actions whose coverage was unchanged, so the generated Nagios config did not change and no validation ran. A third attempt, a new enabled host-scope action that changes the generated config, returned the 422. Recorded as attempts, not a defect.
- The Nagios break was a temporary invalid definition appended to `templates.cfg`, restored byte-for-byte. A first attempt to do this was blocked by the tester's permission guard until the lab owner granted the permission; nothing changed in between.
- TC-REM-06 filters were exercised on 23 older runs from earlier lab testing plus this run's own runs, not on runs created only for this case.
- A first TC-REM-08 attempt restarted the service after a few seconds because of a script error (`systemctl is-active` exits 3 for "inactive"). It was repeated with the full 65 s outage; only the repeat counts.
- A first TC-REM-03 delete attempt used a native browser dialog that the script dismissed; Cancel and confirm were then both recorded properly.

## Follow-up

- Defects found: none.
- Observation for the lab owner (not filed as a defect; the specification does not say which): in the Run log, **From** and **To** compare UTC days while the table shows times in the browser's time zone. In UTC+08:00 a row shown as "18/10/2026 07:39 AM" is a 17 October (UTC) run, so **From = 18/10/2026** hides it and **To = 17/10/2026** still shows it.
- Cleanup done: all test actions deleted; dummy device, loopback alias, systemd unit and temp files removed; `check_tcp` disabled (it was "Ready" before and now shows "Disabled"); `qa-staff` set Inactive (the app cannot delete users); maintenance windows 3 to 13 stay in the list as Cancelled (windows cannot be deleted). Kill switch on; nagios, apache2 and pinpoint-gunicorn active.
- Cases to repeat in the next run: none.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
