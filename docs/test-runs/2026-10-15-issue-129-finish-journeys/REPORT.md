# Test run: issue-129 remaining live journeys

| | |
|---|---|
| Date | 2026-10-15 Asia/Manila (2026-10-14 UTC) |
| Commit tested | Application functional source `c9f8e263`; local full gate `a119afa4`; installed helper `15c27d1` (published installer `b166953`) |
| Plan | [Issue #129](https://github.com/esfen14/Pinpoint/issues/129) E/G/H; [transport plan](../../plans/Issue_129_Check_Secret_Transport.md) |
| Tester | Codex |
| Environment | Existing Ubuntu 22.04.5 QA appliance, Nagios 4.5.11, NCPA client 1.2.4, existing web01. Network guard 10.77.0.0/28; actual sweeps limited to 10.77.0.2/32. Current application runs in the clean acceptance worktree with upgraded shared databases. |
| Raw evidence | Local git-ignored `test-results/issue-129/`: `finish-resume-verify.log`, `failed-install-cleanup-live.log`, `failed-install-cleanup-live-repeat.log`, `alternate-port-live.log`, `alternate-port-live-ready.log`, `finish-journeys-restoration.log`. Harness source retained locally under that same ignored directory. |

## Result

**Overall: Partial.** Required live failed-install cleanup and non-default-port monitoring/probe/relocation journeys now pass, complementing the prior macro/upgrade acceptance. Application implementation and automated checks pass. Human approvals and publication/current-head CI for this new evidence still prevent final issue completion.

Totals: Pass 7, Fail 0, Blocked 1, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Current full automated verification | Pass | Re-ran scripts/verify.sh all on a119afa4: 2766 backend passed/14 existing skips, 554 frontend passed, docs/build passed, lint 0 errors/29 existing warnings. Includes port/migration/cleanup/security/frontend/macro/adapter regressions. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Healthy cleanup refusal | Pass | Actual authenticated admin cleanup request for the deployed target returned 409 before remote changes. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Intentional failed install with real bootstrap | Pass | Selected target's deployment state temporarily made eligible. Real admin start route, background worker, fingerprint checks, password login, bootstrap/key/sudo installation ran. Test wrapped helper installation to replace the installed root-owned executable with a controlled exit-42 fault before its actual invocation. Run/device became Failed and all bootstrap artifacts remained. NCPA installation/package changes were not executed by the faulted helper. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Real cleanup and per-step/state/response behavior | Pass | Actual cleanup route returned HTTP 200 with key/sudo_rule/helper all OK. Verified deployment key absent from authorized_keys and helper/sudoers removed. Account retained because remove_account=false was selected for an existing target. State became Pending NCPA with cleared error; response contained no supplied password or token. Repeated cleanup refused with 409. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Stored non-default port and live probes | Pass | Controlled fixture moved existing agent listener to 5703 and stored that port while global default remained 5693. Actual port lifecycle marked 5703 protected; authenticated reachability/disk probes, certificate identity collection and real nmap sweep on guarded /32 passed. Listener readiness was bounded before probing. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Main Nagios monitoring on non-default port | Pass | Real generation/validation/helper/apply/reload followed the stored port. Forced generated CPU/memory/root-disk services on 5703 returned three OK states with performance data. No daemon/check/network operations were mocked. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Real relocation and exact fixture restoration | Pass | Test set a stale device address to unused guarded 10.77.0.8 and opened matching fixture address history. Actual main Nagios host check produced DOWN; real CGI poll stored it; production candidate selection selected the device. Real 5703 sweep/certificate matching relocated it to 10.77.0.2, recorded NCPA_RELOCATE history and applied/reloaded config. Original listener/bootstrap bytes and metadata, deployment/device/port/address rows and generated config/resource bytes were restored. Original 5693 authenticated reachability passed. App/Nagios active; notifications restored; temporary scripts removed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Publication and required human review | Blocked | a119afa4 application CI is green. App PR #161 and installer PR #7 have no reviewer approvals; app has zero inline review comments. This new report/progress checkpoint requires the owner's requested push confirmation and subsequent CI. Neither PR merged. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Optional account deletion on live target | Skipped | Retained existing deployment account deliberately; userdel branch and account-skip-on-step-failure are covered by passing unit tests. No claim of live account deletion. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Additional native endpoints and complete ISO | Skipped | No new Radius/MySQL endpoint parity or ISO rebuild. Installed synthetic check_nt and automated native parent/child checks are recorded in earlier evidence. Unsupported password-bearing SMB remains explicitly refused. These additional experiments are not replacements for required reviews. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

First cleanup attempt timed out opening an SSH command channel after password authentication, before any mutation. The exact repeated run passed the entire journey; no source fix or reproducible application defect was established.

First alternate-port fixture probed immediately after systemctl restart and asserted before NCPA had bound its listener. Restoration likewise needed startup time; config/DB were restored and original listener subsequently observed. Added bounded readiness to the test harness, then all cases passed. The application's deployment helper already waits for listener readiness; no product change was required.

Used existing web01 instead of creating/reprovisioning a target. Bootstrap/config snapshots stayed in harness memory; request password came from existing protected lab credentials through stdin. Fault injection was in the test harness, not committed application source. Gunicorn/scheduler were stopped during controlled fixture changes and restarted afterward. Notifications were suppressed during forced fault checks and restored afterward. Original dirty guest source was preserved. No broad network scan or VM reset occurred.

## Follow-up

- Publish this evidence only after owner approval; verify current-head CI afterward.
- Obtain required application and paired installer approvals before final completion/merge. Keep draft/progress tracking until the finish condition holds.
- No remaining implementation choice is required from the owner for supported secret transport. SMB refusal remains the accepted unsupported-plugin policy.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
