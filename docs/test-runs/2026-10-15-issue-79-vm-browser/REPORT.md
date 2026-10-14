# Issue #79: VM recipients and browser acceptance

| | |
|---|---|
| Date | 2026-10-15 (Asia/Manila; VM logs use UTC on October 14) |
| Application tested | `3d6471dc`; installed from the pushed issue branch into a clean checkout |
| Browser tests | `client/e2e/host-recipients.lab.spec.ts`, `host-recipients.restricted.lab.spec.ts`, `auth.host-recipients.setup.ts`; added during this run |
| Plan | [Issue #79](https://github.com/esfen14/Pinpoint/issues/79), finish condition and saved progress |
| Tester | Codex |
| Environment | VirtualBox Ubuntu 22.04 appliance, Nagios 4.5.11, real systemd/Gunicorn/Nginx, two Ubuntu target VMs; discovery strictly `10.77.0.0/28`, TCP 22/80 and UDP 161 |
| Installer | Local installer checkout `697869e` |
| Raw evidence | Local ignored `test-results/issue79-vm/`; private credentials outside the repository |

## Result

**Partial; lab restore failure requires follow-up.** VM save/config generation, real Nagios validation, normal host DOWN and service CRITICAL mail routing, live rescan, ineligible fallback, and browser end-to-end checks pass. Mail was captured at the VM sendmail boundary. External SMTP acceptance and actual inbox receipt remain unverified, so the original finish condition remains incomplete and PR #160 remains draft.

## Cases

| Case | Result | Observed evidence | Issue |
|---|---|---|---|
| V1 Preserve inherited state | Fail | Snapshot commands succeeded, but final checks exposed two VirtualBox management processes: the SSH endpoint still had the tested files after reported restore. Snapshot isolation was therefore not established. Original issue-129 service/DB and sendmail were restored directly; seventeen previously clean tracked paths were restored, but the inactive main checkout’s two pre-existing modified files were overwritten by the earlier sync and cannot be claimed restored exactly. | [#162](https://github.com/esfen14/Pinpoint/issues/162) |
| V2 Deploy attributable branch | Pass | Initial fresh deploy refused a dirty checkout present in the base snapshot. Preserved that directory and deployed clean branch `3d6471dc` through the installer application/privileges steps (`install.log`). Mandatory first-run setup completed. | |
| V3 Appliance health | Pass | `health-repeat.log`: 59 passed, zero failures, one warning about two historical tracebacks in the previous hour. The initial health attempt failed because the scheduler was deliberately off during setup; scheduler was enabled after guarding discovery networks. | |
| V4 Browser save/reopen/default | Pass | Real browser selected one eligible recipient, saved IDs through the actual PUT route/shared writer, reopened to observe the persisted checkbox, cleared selections, saved/reopened to observe default fallback, and restored the original selections. Initial and repeated administrator runs passed. | |
| V5 Restricted browser and API | Pass | Reader with host/network-health access and without `system.hosts.alerts` loaded host detail, saw no editor, and received 403 for GET and PUT. The initial shared auth helper expected Settings; this reader correctly lands on Network Health. Feature-specific setup now asserts that route. Repeated run: four Playwright checks passed including both login setups (`browser-repeat.log`; final repeat with explicit detail-loaded assertion: `browser-final.log`, four passed). | |
| V6 Selected group and host/services | Pass | Actual saved config contains a per-device group with exactly one eligible contact. The selected host and SSH service use that group; the other host and service use `system_users` (`hosts.cfg`, raw and ignored). | |
| V7 Real Nagios validation | Pass | `/usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg` reported zero errors after real API saves (`nagios-validation.log`). | |
| V8 Custom notification comparison | Pass | Initial observer expected stock `CUSTOM Host Alert` subjects, while installed mail commands produce `[PinPoint] NOTICE`. Corrected observer matched the four captured messages: one selected-host recipient, three default-host recipients (`routing-initial.log`, `routing-repeat.log`). Initial failed observer result is retained. | |
| V9 Normal host DOWN alerts | Pass | Fresh passive UP → DOWN transitions emitted actual Nagios HARD host alerts and mail. Captured recipient sets were exactly one selected user and all three eligible default users; no unselected user on the selected host (`problem-routing.log`, `problem-mail-capture.json`). | |
| V10 Normal service CRITICAL alerts | Pass | Repeated passive SSH failures reached HARD CRITICAL after baseline OK. Captured MIME mail showed the same selected/default recipient comparison, correlated by target address. Host and service states/checks were restored (`problem-routing.log`). | |
| V11 Actual rescan ownership | Pass | Second guarded discovery completed successfully and retained the recipient IDs on the same stable device ID (`rescan.log`). | |
| V12 All-ineligible fallback | Pass | Selected the opted-out reader through the actual API: `using_default` true, host/services use `system_users`, no per-device group generated, real Nagios validation zero errors; original recipients restored (`fallback-repeat.log`). | |
| V13 External SMTP and inbox comparison | Blocked | No controlled mailbox addresses or mailbox confirmation supplied in this session. Capture substitutes for sendmail only inside the disposable VM and cannot establish external receipt. F8 stays unchecked. | [#79](https://github.com/esfen14/Pinpoint/issues/79) |
| V14 Isolated regression suite | Pass | `scripts/verify.sh all`: 2,660 backend passed / 14 skipped; 565 frontend passed; docs/build/lint green (29 existing lint warnings). Browser scaffold safety: eight passed. Frontend stage repeated after new tests. | |

## Deviations and setup findings

- The former unavailable-VM blocker is resolved. The VM's base snapshot was not a clean no-application baseline, and the inherited Gunicorn override selected another checkout. Testing used an explicit service WorkingDirectory and clean branch install, preserving the database and directory rather than rewriting migration history. Final checks showed the snapshot belonged to a different VirtualBox management instance from the running SSH endpoint; it must not be treated as a usable backup of the tested endpoint.
- An empty UDP port list invoked Nmap's default UDP scan in this setup. The run was cancelled, its scoped Nmap process stopped, and acceptance used explicit UDP 161. No broad network scan was allowed; every discovery remained inside the documented lab range. This setup workaround does not change discovery behavior in #79.
- Live mail transport was replaced by a private sendmail capture, so test addresses did not receive external mail. Real Nagios notification dispatch and MIME recipient routing were exercised; Gmail or inbox receipt was not.
- Passive check results provide deterministic real Nagios transitions. This verifies recipient routing rather than physical link-failure detection.
- The initial auth-route mismatch and initial subject-matching failure were acceptance-harness assumptions, corrected without changing application code or weakening recipient assertions. Raw failed attempts remain alongside passing repeats.

## Follow-up

- Complete V13 with controlled selected/default mailboxes and positive receipt plus unselected-recipient absence confirmation. Do not mark F8 complete or make #160 ready before this proof.
- Previous Docker evidence remains supplementary: [initial](../2026-10-14-issue-79-docker-initial/REPORT.md), [repeat](../2026-10-14-issue-79-docker-repeat/REPORT.md).
- No application defect was observed in the recipient feature during this run.
- Lab recovery: original Gunicorn WorkingDirectory is again `/opt/pinpoint/issue-129-acceptance/server`, original DB preserved, original sendmail restored, and Nagios config regenerated successfully through that checkout’s shared writer. The test checkout/DB are retained at `/opt/pinpoint/issue79-tested-20261015`; captures remain private on the endpoint. Both targets started by this session were stopped through its VirtualBox manager; a pre-existing unmanaged target process was left alone.
- **Unresolved recovery limitation:** the initial inactive main checkout (`1ca2c75`) had uncommitted changes in `server/app/api/system/dashboard.py` and `server/app/nagios/status.py`. The initial sync overwrote their contents before the snapshot failure was discovered. No exact backup has been found. The live original issue-129 checkout (`c9f8e26`) was not synced or migrated and remains intact, but this does not recover those two inactive-checkout edits. The owner was asked for their source commit or backup. Do not claim complete restoration, and resolve VirtualBox control ownership before further VM trials.
- The two snapshots created in this run are retained for diagnosis but are **not verified recovery points for the tested SSH endpoint**.

## Sanitization

- No credentials, mailbox addresses, raw configs, databases, MIME messages or screenshots committed.
- Only the documented lab range appears in this report; raw evidence remains ignored.

Lab control/recovery incident is tracked separately in [#162](https://github.com/esfen14/Pinpoint/issues/162); it blocks further VM mutation until ownership is established.
