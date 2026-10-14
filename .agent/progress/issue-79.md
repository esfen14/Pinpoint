# Issue #79: Choose which users receive email alerts for each host

Branch: `issue-79-host-alert-recipients`
Status: blocked

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
- [ ] F10: scripts/verify.sh all passes and PR CI is green.

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

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
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

- Last check run (exact command): scripts/verify.sh all > test-results/issue79-final-all.log 2>&1
- Result (first failing lines, or green): green: final scripts/verify.sh all passed (2660 backend / 14 skipped; 565 frontend; docs/build/lint, 29 existing lint warnings); focused recipient backend 38 passed; final live Playwright 4 passed; browser scaffold safety 8 passed. Latest checkpoint CI remains to be observed.
- Hypothesis: The former VM availability blocker is resolved. Actual VM API save, Nagios validation and host/service MIME capture prove routing, but cannot prove external SMTP acceptance or actual inbox receipt. No application defect observed. F8 remains unchecked.
- Next action: Verify merge with current main and its CI, resolve lab-control/recovery issue #162, then supply controlled selected/default recipient mailboxes and complete actual inbox delivery comparison before making PR #160 ready. User input for mailbox addresses is pending; do not substitute local capture for inbox proof.

## Decisions and notes

- The requested workflow is .agent/workflows/work-issue.md (no .agents/workflows/work-issue exists).
- Workflow sensitive-module pause was explained; user continued twice after switching to unrestricted permissions. Proceed with the requested writer changes and additive migration, including explicit injection/secret-exposure review.
- New permission: system.hosts.alerts, separate from account.alerts and system.hosts.edit; both read and write recipients require it.
- Recipient rows use the stable device ID, never hostname/IP. Merge unions source and target selections, dropping duplicate source rows; retire removes assignments to the retired device. Users are not deleted and no user delete cascade is introduced.
- Preserve #80 behavior when there are no globally eligible contacts: omit contact_groups and never write an empty group.
- Keep current checkout untouched. Worktree: /tmp/Pinpoint-issue-79.

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

- Recovery limitation requiring owner input: inactive original checkout at 1ca2c75 had pre-existing edits in server/app/api/system/dashboard.py and server/app/nagios/status.py; initial sync overwrote their bytes before the wrong-instance snapshot problem was found. Seventeen other previously clean tracked files restored from original HEAD. The original active issue-129 checkout c9f8e26 and its DB remain intact. Asked owner for original two-file source/backup; exact restoration cannot be claimed. Report V1 is Fail, linked to #79.

- Lab recovery tracked as https://github.com/esfen14/Pinpoint/issues/162 after searching existing issues. Original active issue-129 service and database, sendmail, generated config and frontend restored directly. Inactive checkout two-file original edits remain unrecovered; no further VM mutations.

- Latest PR CI did not trigger because GitHub reported CONFLICTING after #128 merged into main. Merged origin/main (9ce590eb); only report-index conflict, resolved by retaining both sets of reports. No migration-head conflict. Incoming #128 NCPA generation changes are automatically merged; recipient-focused tests and full verification must be rerun. No post-merge live run is authorized until #162 is resolved; previous VM evidence remains attributed to 3d6471dc.
