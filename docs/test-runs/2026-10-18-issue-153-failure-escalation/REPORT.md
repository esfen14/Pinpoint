# Test run: issue-153-failure-escalation

| | |
|---|---|
| Date | 2026-10-17 to 2026-10-18 |
| Commit tested | `ad23308b` (branch tip when deployed; the client bundle was built from the same tree). Main was merged afterwards in `145623ef` with no code conflict. |
| Plan | none (acceptance criteria of issue #153) |
| Tester | Claude Code for the project owner, who approved each deployment step |
| Environment | Existing lab appliance, Ubuntu 22.04.5, Nagios Core, SQLite. Upgraded in place from `f155a3c7d2b1` to `e153c4a8b2d7`. The appliance was at the main commit before #153 plus uncommitted files, not a fresh build. |
| Raw evidence | Nagios log and the PinPoint run records on the appliance. Not committed. A pre-change backup of code, both databases, `nagios.cfg` and the client bundle was taken on the appliance. |

## Result

**Overall: Partial.** The notification path was observed working end to end on a dummy host and
service (failed run, cap skip, repeat recovery, downtime, unwritable command pipe, feed). Not
observed: the new screens in a browser, and the owner has not yet confirmed the mail arrived in
the inbox for a notification sent by an automatic recovery run.

Totals: Pass 8, Fail 0, Blocked 0, Skipped 2.

All checks used a dummy host `pp153-dummy` with one service whose state was set by a file, and
three test actions limited to that host. No discovered device was touched. The dummy objects, the
test actions and the temporary files were removed afterwards.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Failed action sends one custom notification | Pass | Action `restart_remote_service` on a host outside the device inventory ended `failed` (run 10). Nagios logged one `SEND_CUSTOM_SVC_NOTIFICATION;…;0;PinPoint;` (option `0`, the force option is not used) with the fixed text, action name, outcome code and run id only. Run shows `notifyState sent`, 1 attempt, no error. | |
| Hourly cap skip sends one `capped` notification | Pass | `record_only` with 1 run per hour: the first event succeeded without a notification, the next was `skipped_hourly_cap` and sent one custom notification (run 12). Later blocked events each sent one (runs 13 to 15), as the issue asks. | |
| Repeat recovery: one notification per window | Pass | Three successful runs of the same action for the same service (runs 11, 16, 17): run 17 sent one `repeated` notification, run 18 (fourth success in the window) sent none. | |
| Scheduled downtime suppresses the notification | Pass | Downtime on the service, then a custom notification command: Nagios accepted the command and logged no `SERVICE NOTIFICATION` for it. Confirms the force option is not set. | |
| Unwritable command pipe | Pass | Pipe mode changed to read-only for the group, then a failing run (run 19): 3 attempts about 15 seconds apart, `notifyState failed`, error "The Nagios command pipe could not be opened.", the consumer kept running. The pipe mode was restored afterwards. | |
| Local service restart action runs | Pass | `restart_local_service` for `nagios` succeeded (run 20); Nagios was active afterwards. No notification was due. | |
| Feed carries the custom notification and its comment | Pass | `/api/system/history/notifications` returned 11 custom rows for the dummy service with `is_custom` true and the comment rebuilt from the run record (run 17 text). Nagios' archive entry itself holds no comment or author (captured earlier on the lab). | |
| Mail delivery of a custom notification | Pass (hand-sent) | After SMTP credentials were corrected, a custom notification sent with the same command was accepted by the mail server (`smtpstatus=250`). The notifications from runs 10 and 12 were generated while the appliance had no working SMTP (an empty `msmtprc`, then rejected credentials), so their mail failed; that is outside this change. | |
| New screens in a browser (bell, Dashboard, History labels, run drawer, service-row badge) | Skipped | The client bundle was deployed and is served, but no browser pass was recorded. Covered by frontend unit tests only. | |
| Host-form custom notification and a flapping service producing many skip notifications | Skipped | The host form was verified on 2026-10-13 only. The many-notifications behavior is by design and is called out in the PR. | |

## Deviations from the plan

- Dummy host and service instead of discovered devices, at the owner's request.
- Mail could not be proven at first: SMTP on this appliance was unconfigured. After the owner fixed
  it, one notification was sent by hand rather than re-running a failing action.
- A first run of the repeat case did not apply its settings because the login session had expired
  (HTTP 401); it left the cap at 1 and so produced two extra `capped` notifications (runs 14 and
  15). The case was re-run with the session renewed.
- During deployment, unpacking the code archive reset `server/` to root ownership, so the migration
  and the app could not write their database journal. It was fixed by restoring `pinpoint` ownership
  and re-running the migration. The app ran new code against the old schema for about a minute.

## Follow-up

- Defects found: none in the feature.
- Cases to repeat in the next run: the browser checks above, and the mail for an automatic failed run
  once SMTP is known good. A `sent` run state means Nagios accepted the command, not that mail arrived.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
