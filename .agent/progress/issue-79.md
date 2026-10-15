# Issue #79: Choose which users receive email alerts for each host

Branch: `issue-79-host-alert-recipients`
Status: in-progress

## Finish condition

- [x] F1: A host with recipients has its own group of only active opted-in users; host and all generated services use it (mocked test).
- [x] F2: No recipients preserves the default group (test).
- [x] F3: All ineligible recipients falls back to the default without an empty group (test).
- [x] F4: Saving requires the separate permission, audits and uses the shared writer (test).
- [x] F5: Failed validation or reload restores recipients and reports the error (test).
- [x] F6: Rescans preserve assignments; merge and retire leave no orphan assignments (test).
- [x] F7: Host detail editor is permission gated and sends recipient IDs (frontend test).
- [ ] F8: VM lab save writes per-host group; Nagios validates; alerts email only selected recipients while another host emails the default group.
- [x] F9: Backend, data, frontend specifications and Implementation_Status updated.
- [x] F10: scripts/verify.sh all passes and PR CI is green.

Requirement coverage (every requirement stated by the issue):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Prerequisite per-user flag merged | Prerequisite to F1 | #80 closed; PR #84 merged a55ae595; existing User.Receive_Email_Alerts and VM report |
| A: device-to-user table; no rows retains default | F1, F2, F6 | host-recipient model/migration and generation tests |
| B: eligible membership, host/services groups, fallback | F1, F2, F3 | generated-object assertions with mocked Nagios validation |
| C: read/edit, separate permission, audit, shared writer, rollback | F4, F5 | mocked API permission, validation, audit and rollback tests |
| D: permission-gated host editor | F7 | drawer integration and editor request tests |
| E: stable rescan/merge/retire ownership | F6 | real isolated scan reconciliation and lifecycle route tests |
| VM delivery comparison | F8 | sanitized attributable VM lab report and mailbox evidence |
| Owning docs refreshed | F9 | docs verification |
| All checks pass | F10 | scripts/verify.sh all and PR checks |
| Per-service/group recipients, escalations, schedules, other channels, per-user setting | Deliberately out of scope | no changes to these features |
| Owner comment: future nice-to-have | Scheduling only | User explicitly requested issue #79 now |

## Plan

1. [x] Backend TDD: tests/unit/test_host_recipients.py and migration runner; add HostAlertRecipient in server/app/system_models.py and migration, seeded system.hosts.alerts permission, recipient routes, generated groups in create_host_cfg.py, merge/retire handling in device_identity.py. Update backend/data specs for route drift. Run focused then backend verification.
2. [x] Frontend TDD: host editor and drawer integration tests; add DeviceRecipientsSection.tsx, types/hostRecipients.ts, and permission gate in StatusDetailDrawer.tsx. Update frontend and device inventory specifications; run frontend verification.
3. [x] Live acceptance: inspect VM-lab ownership and tools, run issue-authorized save/validation/delivery comparison if exclusive lab and mailbox access are available; record sanitized report in docs/test-runs, refresh Implementation_Status, and run docs verification.
4. [x] Re-read issue/comments, prove each finish condition, scripts/verify.sh all, checkpoint, and open a ready PR only when all acceptance is proven; otherwise draft with outstanding items recorded.

5. [x] Docker acceptance supplement: own temporary compose project with cached images; API recipient saves, actual Nagios validation, captured host/service notifications for selected/default/fallback recipients, scoped cleanup, and new sanitized report.

6. [ ] Resume on available VM: preserve inherited appliance state; sync issue branch and migrate; run real browser recipient save/reload/default/permission checks and Nagios delivery comparison; record report, restore lab and run all verification. Keep F8 pending until inbox evidence exists.

7. [x] Integrate merged PR #163 locally: merge origin/main, prove the migration graph has a single deployable head from both main and the already-tested #79 revision, preserve per-host groups on interface bandwidth services, then run isolated verification and CI. Recovery evidence from merged #165 verified; guarded VM testing resumed.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Rebuilt VM acceptance | Separate checkout/copied DBs, browser, real SMTP delivery, rescan/fallback, verified baseline restoration | scripts/playwright-lab; temporary guarded VM drivers | 11 pass; owner inbox comparison pending; baseline DB/static hashes unchanged |
| Post-#165 integration | Single migration head and SNMP-only compatibility fixes, full verification and CI | scripts/verify.sh all; gh pr checks 160 | 2821 backend / 14 skipped, 640 frontend; all three CI jobs green |
| Resumed after PR #165 | Read closed #162, merged #165, owner loss decision and clean rebuild/marker proof; rerun saved verification | scripts/verify.sh all | In progress; integrate the new preflight before VM access |
| Resumed after PR #163 | Fetched merged main and re-read #79/#162/#163; planned isolated integration/migration compatibility coverage | saved scripts/verify.sh all command rerun | In progress; no VM mutation; live blocker still unresolved |
| Resume 2026-10-15 | Current issue and draft #160 re-read; CI green; VirtualBox now available, appliance started; inherited source modifications found and will be preserved before sync | scripts/vmlab status; scripts/vmlab up; remote git status | VM and Nagios active; prior all run interrupted and must be rerun |
| Intake | Required docs and source inspected; isolated worktree; prerequisite checked | gh issue view 80 and gh pr list --state merged --search 80 | #80 merged and VM verification documented |
| 1 | Added backend model/migration, recipient API, shared-writer groups and lifecycle handling with tests | cd server && .venv/bin/python -m pytest tests/unit/test_host_recipients.py -q | 34 passed, 2 failed: custom-check test used unsupported ssh plugin; permission-delete fixture hit write-only ORM relationship |

| 2 | Corrected custom-check and permission fixtures, based migration on current head; implemented permission-gated host editor and drawer tests; refreshed specs | focused backend (36 passed), focused frontend (26 passed), scripts/verify.sh frontend | green; full backend running; local lint 0 errors / 29 existing warnings |

| 3 | Completed backend and docs stages; fallback validation tested at fake Nagios boundary; recorded blocked live preflight report | scripts/verify.sh backend; scripts/verify.sh frontend; scripts/verify.sh docs; focused recipient tests | backend 2658 passed / 14 skipped; frontend 565 passed and build/lint green; docs green; focused backend 38 passed; live blocked |

| 4 | Re-read unchanged issue/comments, ran all verification, opened draft #160, recorded live blocker | scripts/verify.sh all; gh pr checks 160 | green: 2660 backend passed / 14 skipped; 565 frontend passed; build/lint/docs green; all 3 CI jobs passed on aa273270; only live acceptance remains |

| Resume | User requested continuation; group membership refreshed using sg docker; discovered shared lab and chose separate three-container lab | id; id paeng; sg docker -c docker ps | Docker group exists on account but not inherited by session; sg docker grants legitimate group access |

| Live 1 | Own Docker appliance: real private/default group validation and host/service mail routing; ineligible-group fallback syntax valid | python3 -u /tmp/pinpoint-issue79-live/verify.py | 7 cases passed; fallback mail capture timed out (Nagios logged dispatch during HUP worker registration, no capture). Full resumed all and CI green. |

| Live 2 | Worker-ready fallback repeat, live rescan, real validation rejection, injected reload rejection and actual permission guard; sanitized initial/follow-up reports; own lab removed | resume.py; failures.py; scripts/verify.sh all; Docker project-scoped down | 7 further passes (14 distinct passes across both phases); resumed all green (2660 backend / 14 skipped; 565 frontend); original VM/inbox acceptance still pending |

| VM/browser 2026-10-15 | Preserved inherited VM, installed branch cleanly, real Nagios groups/default/ineligible validation, real host DOWN/service CRITICAL MIME routing, live rescan, and new administrator/restricted Playwright tests | scripts/playwright-lab --project issue-79-live --project issue-79-restricted; temporary VM drivers; scripts/verify.sh all | Browser 4 passed on final repeat; VM config/routing/rescan/fallback passed; external inbox proof unavailable. Initial auth/subject matcher assumptions fixed; original failures retained in report. |

## State for the next session

- Last check run (exact command): scripts/verify.sh all > test-results/issue79-post165-all.log 2>&1
- Result (first failing lines, or green): green, 2821 backend passed / 14 skipped, 640 frontend passed, build/lint/docs passed. All three CI jobs passed on 4ed80435 (run 38674517921). Rebuilt VM browser projects: 4 passed. Real generated host/service groups and nagios -v passed.
- Hypothesis: implementation and current-main compatibility now verified. F8 still needs actual mailbox comparison for real delivery; SMTP configured and test API successful.
- Next action: Await owner inbox confirmation for Oct 15 11:14–11:18 Manila; correlate both hosts and DOWN/CRITICAL events. All independent lab checks and baseline restoration are complete. If confirmed, check F8, delete progress, push final docs, make existing PR #160 ready and verify final CI; otherwise retain draft and document mismatch.

## Decisions and notes

- The requested workflow is .agent/workflows/work-issue.md (no .agents/workflows/work-issue exists).
- Workflow sensitive-module pause was explained; user continued twice after switching to unrestricted permissions. Proceed with the requested writer changes and additive migration, including explicit injection/secret-exposure review.
- New permission: system.hosts.alerts, separate from account.alerts and system.hosts.edit; both read and write recipients require it.
- Recipient rows use the stable device ID, never hostname/IP. Merge unions source and target selections, dropping duplicate source rows; retire removes assignments to the retired device. Users are not deleted and no user delete cascade is introduced.
- Preserve #80 behavior when there are no globally eligible contacts: omit contact_groups and never write an empty group.
- Historical worktree: /tmp/Pinpoint-issue-79. That path no longer exists in this resumed environment; the issue branch is checked out in the user-provided workspace.

- Historical 2026-10-14 VM preflight: scripts/vmlab status reported VBoxManage not found; user confirms only Docker exists here. docker ps initially reports socket permission denied; inspect sudo Docker access before declaring Docker blocked. Keep VM/inbox finish condition unticked and PR draft.

- Docker preflight: docker ps denied at /var/run/docker.sock; sudo -n docker ps requires interactive authentication. No Docker or VM mutation performed. User confirms Docker is the only lab technology here. Live acceptance needs an accessible lab and inbox evidence.
- Injection and secret-exposure review: group names derive only from integer device IDs; PUT rejects booleans, strings, duplicates, unknown IDs and extra fields before config generation. New group members reuse previously validated contact emails; no request text enters commands or paths; no new secrets are read, logged or returned.
- TDD failures observed before implementation: missing HostAlertRecipient model; missing DeviceRecipientsSection module.
- Backend fixture fixes: custom checks use supported check_ping; permission deletion uses explicit SQL bulk delete. Migration parent is c5e2a8f4d716 (current main head), avoiding an accidental second Alembic head.

- Draft PR: https://github.com/esfen14/Pinpoint/pull/160. F1-F7 and F9-F10 are proven by the named isolated tests, specs and all verification; F8 remains blocked. No services, containers, network devices or mailboxes were modified in this environment.
- Final acceptance report: docs/test-runs/2026-10-14-issue-79-preflight/REPORT.md; blocked prerequisites only, no real Nagios or email pass claimed.
- The last session round includes only progress/report metadata after the verified implementation; no code changes after scripts/verify.sh all. Watch final-checkpoint PR CI before reporting status.

- Resumed 2026-10-14: user added paeng to docker group; use sg docker for refreshed supplementary group access. Existing pinpoint-lab and issue-128 containers are left untouched. Own project uses the documented isolated 10.77.0.0/28 range and two targets. Compose and test mail capture artifacts are temporary and uncommitted. Re-running the previous all command into test-results/issue79-resume-all.log as required for resume.

- Docker reports: docs/test-runs/2026-10-14-issue-79-docker-initial/REPORT.md (7 passes, 1 failed immediate capture); docs/test-runs/2026-10-14-issue-79-docker-repeat/REPORT.md (7 follow-up passes). Eight copied source files matched commit a60e5aba. Raw evidence and temporary drivers are in ignored test-results/issue79-docker/.
- Own project pinpoint-issue79 was removed after collecting evidence, including its containers and networks. Existing pinpoint-lab and issue-128 containers remained running and were not modified. Docker is now usable through sg docker; the old preflight report remains historical.
- A scope clarification was asked after concrete Docker verification: accept Docker/local capture as a replacement for the explicit VM/inbox requirement, or keep the original requirement and draft. Until an explicit answer, retain the original finish condition; do not tick F8.

- User decision after reviewing Docker evidence: "Keep the original acceptance; leave the PR draft." F8 stays unticked; no issue acceptance edits or PR readiness change are authorized. Full local all verification and previous code CI passed; CI reruns automatically for these final report/progress-only checkpoints.

- 2026-10-15 preflight: inherited appliance uses issue-129 service override and a database stamped with revision 7db78f308ee5, absent from this branch. No migration stamping or cross-branch workaround used. Restore point `issue79-before-20261015` preserves the inherited state. Use documented fresh branch installation from os-nagios-ready for attributable acceptance.

- 2026-10-15 current evidence: docs/test-runs/2026-10-15-issue-79-vm-browser/REPORT.md. App commit 3d6471dc installed via installer 697869e. New browser projects issue-79-live and issue-79-restricted use private administrator/reader setup; reader needs system.network_health and system.hosts without system.hosts.alerts. Browser fixture addresses are synthetic; all mail captured privately at sendmail. No external email sent.
- Snapshot reliability FAILED final verification: two VBoxSVC processes exist, and the SSH endpoint did not revert with the reported snapshot restore. Neither issue79 snapshot is a verified backup of the endpoint. Original service/DB/sendmail restored directly; test checkout retained at /opt/pinpoint/issue79-tested-20261015. Private test login state is /tmp/issue79-private; original private state directory was not changed. Actual sendmail was restored directly after the test. Do not start further lab trials until VirtualBox ownership/control is resolved.

- Recovery limitation requiring owner input: inactive original checkout at 1ca2c75 had pre-existing edits in server/app/api/system/dashboard.py and server/app/nagios/status.py; initial sync overwrote their bytes before the wrong-instance snapshot problem was found. Seventeen other previously clean tracked files restored from original HEAD. The original active issue-129 checkout c9f8e26 and its DB remain intact. Asked owner for original two-file source/backup; exact restoration cannot be claimed. Report V1 is Fail, linked to #162.

- Lab recovery tracked as https://github.com/esfen14/Pinpoint/issues/162 after searching existing issues. Original active issue-129 service and database, sendmail, generated config and frontend restored directly. Inactive checkout two-file original edits remain unrecovered; no further VM mutations.

- Latest PR CI did not trigger because GitHub reported CONFLICTING after #128 merged into main. Merged origin/main (9ce590eb); only report-index conflict, resolved by retaining both sets of reports. No migration-head conflict. Incoming #128 NCPA generation changes are automatically merged; recipient-focused tests and full verification must be rerun. No post-merge live run is authorized until #162 is resolved; previous VM evidence remains attributed to 3d6471dc.

- Final merged verification: origin/main 9ce590eb merged as ccd2f254; only report-index conflict, both histories retained. Focused 38 passed, all 2676 backend / 14 skipped and 579 frontend passed. CI https://github.com/esfen14/Pinpoint/actions/runs/38609237571 passed all three jobs. No post-merge VM run: #162 forbids further mutation until control/recovery resolved. PR remains draft; external inbox and original two-file recovery questions remain unanswered.

- Resume after user reports PR #163 merged: confirmed 82ba9ce9 adds interface bandwidth (#126), not lab recovery; #162 is still open without comments. Re-running saved all command before merging. Both migrations b7d3f1a9c264 (main) and a79e14c0b621 (#79) currently descend from c5e2a8f4d716, so integration needs an explicit single-head merge revision without rewriting an already-tested revision. Ask for recovery details and two controlled mailbox addresses; continue isolated testing independently.

- User explicitly deferred further testing until they fix #162. Stopped this session’s running baseline verification; no merge with PR #163, migration changes or VM mutations performed. Compatibility work remains planned only. User supplied two controlled mailbox addresses in conversation for future delivery testing; keep them out of committed evidence. Resume only after #162 is resolved and control/recovery evidence is verified.

- Resume after PR #165: main 977deaea closes #162. Read both recovery reports: owner accepted original two-file loss, retired old disks, rebuilt the lab, and verified SSH+HTTP marker restoration plus sole-controller runtime NAT ownership. Previous test checkout and private issue79 credentials are obsolete. Resume authorized by user reporting the blocker resolved; integrate current main and its guard before any VM operation, recheck exclusive ownership, preserve clean rebuilt state, then deploy/test #79 against the two user-controlled mailboxes supplied in conversation. Existing setup-admin compatibility bug #167 is outside scope; use validated current private credentials/API rather than stale helpers.

- Integration round after #165: six new regression cases reproduced two failures after merging main: two Alembic heads, and SNMP-only monitored-interface facts raising KeyError ncpa while check_ncpa is globally enabled. Added no-op merge e79b7d3c2641 and guard NCPA probing on actual NCPA facts. Initial two migration assertions incorrectly expected sibling tables to disappear on merge rollback; observed Alembic correctly retains both parents, so assert exact preservation of both tables/data instead. Focused backend 45 passed; drawer/editor/interface frontend 41 passed; new ownership preflight passes on rebuilt UUID 351eb491-f5e1-4854-a7e4-68309ad774ad. SMTP API reports configured=false/passwordSet=false; owner asked to configure through UI. No test alert sent.

- Post-#165 verification: scripts/verify.sh all passed (2821 backend / 14 skipped; 640 frontend; docs, build and lint green); CI run 38674517921 all three jobs passed. Administrator email changed to the owner-selected address via supported API, existing password preserved and login verified; private host state updated. SMTP now configured with saved password and test send returns ok=true. Mailbox addresses remain private.
- Rebuilt VM isolation: separate detached checkout /opt/pinpoint/issue79-acceptance-20261015 at 4ed80435; original checkout has no tracked edits and remains untouched. Service stopped for sqlite backup of both databases into isolated checkout; database paths explicitly asserted and copied databases upgraded to e79b7d3c2641. Original Nginx/Nagios files backed up privately and separate systemd drop-in selects trial WorkingDirectory/database. Isolated build active. Initial deployment failed Git ownership assertion before mutation; fixed by running Git as checkout owner. Temporary API fixture initially used role_name instead of name and omitted create status; corrected fixture, no application change.
- Rebuilt run: scripts/playwright-lab --project issue-79-live --project issue-79-restricted passed 4/4, with actual API saves and Nagios apply. Two controlled globally eligible accounts only in copied DB; opted-out Staff reader has system.network_health/system.hosts without system.hosts.alerts. SSH plugin enabled through supported API; selected host and SSH service use private group, default host/service use system_users, group membership exact, actual Nagios validation zero errors. Real mail driver uses installed sendmail/msmtp and restores runtime checks in finally; inbox acceptance remains pending until observed.

- Current actual delivery run ID is retained privately in test-results/issue79-post165/delivery-window.json. Selected target 10.77.0.2 and default target 10.77.0.3 reached real HARD DOWN and SSH HARD CRITICAL. Exact recipient sets verified from Nagios events: selected mailbox only on selected host, both on default host. Twelve Gmail SMTP 250/EX_OK receipts verified (8 selected mailbox / 4 default-only mailbox including recovery). The initial service status assertion read a stale periodic status.dat; event log independently proves HARD states and dispatch. Finally cleanup restored runtime settings; subsequent verifier proves both UP/OK. Temporary driver now waits for publication; no redundant resend performed.
- Rebuilt live rescan succeeded within the exact 10.77.0.0/28 network and explicit TCP/UDP ports, preserving exact stable recipient IDs. Ineligible-only selection generated valid default host/service groups, then original selection restored. Baseline app restored by removing only task drop-in and restoring exact Nginx/Nagios backups. Original system.db and static index hashes match predeployment; services active and original HEAD/source unchanged. New administrator login and configured SMTP verified on restored baseline; temporary selected account absent there. Private isolated trial DB remains retained, inactive.
- New sanitized report: docs/test-runs/2026-10-15-issue-79-rebuilt-inbox/REPORT.md (11 pass / 1 inbox-confirmation blocked by #79). Owner asked to check both actual inboxes/Spam during Oct 15 03:14–03:18 UTC / 11:14–11:18 Manila, selected host dev-16a18e and default host dev-c61190. F8 stays unticked and PR stays draft until owner answers. No mailbox addresses or raw configs/evidence committed.
