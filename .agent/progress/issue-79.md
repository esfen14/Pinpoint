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

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Required docs and source inspected; isolated worktree; prerequisite checked | gh issue view 80 and gh pr list --state merged --search 80 | #80 merged and VM verification documented |
| 1 | Added backend model/migration, recipient API, shared-writer groups and lifecycle handling with tests | cd server && .venv/bin/python -m pytest tests/unit/test_host_recipients.py -q | 34 passed, 2 failed: custom-check test used unsupported ssh plugin; permission-delete fixture hit write-only ORM relationship |

| 2 | Corrected custom-check and permission fixtures, based migration on current head; implemented permission-gated host editor and drawer tests; refreshed specs | focused backend (36 passed), focused frontend (26 passed), scripts/verify.sh frontend | green; full backend running; local lint 0 errors / 29 existing warnings |

| 3 | Completed backend and docs stages; fallback validation tested at fake Nagios boundary; recorded blocked live preflight report | scripts/verify.sh backend; scripts/verify.sh frontend; scripts/verify.sh docs; focused recipient tests | backend 2658 passed / 14 skipped; frontend 565 passed and build/lint green; docs green; focused backend 38 passed; live blocked |

| 4 | Re-read unchanged issue/comments, ran all verification, opened draft #160, recorded live blocker | scripts/verify.sh all; gh pr checks 160 | green: 2660 backend passed / 14 skipped; 565 frontend passed; build/lint/docs green; all 3 CI jobs passed on aa273270; only live acceptance remains |

## State for the next session

- Last check run (exact command): scripts/verify.sh all > /tmp/issue79-all.log 2>&1
- Result (first failing lines, or green): green; backend 2660 passed / 14 skipped; frontend 565 passed; docs, build and lint pass (0 errors / 29 warnings). Logs copied to ignored test-results/issue79-*.log. PR docs/backend/frontend CI passed on code commit aa273270; final metadata checkpoint triggers the same checks again.
- Hypothesis: NetDiscoveryID is durable across rescans. Numeric device-ID group names avoid injection. Eligibility derives from existing active/opt-in filter. The shared writer reads uncommitted flushed assignments, allowing rollback on apply failure.
- Next action: Provide exclusive access to a VM lab with configured mail transport and controlled test inboxes; run F8 (save, nagios -v, selected-versus-default delivery comparison), record evidence, then remove the progress file and mark draft PR #160 ready only after acceptance and CI pass.

## Decisions and notes

- The requested workflow is .agent/workflows/work-issue.md (no .agents/workflows/work-issue exists).
- Workflow sensitive-module pause was explained; user continued twice after switching to unrestricted permissions. Proceed with the requested writer changes and additive migration, including explicit injection/secret-exposure review.
- New permission: system.hosts.alerts, separate from account.alerts and system.hosts.edit; both read and write recipients require it.
- Recipient rows use the stable device ID, never hostname/IP. Merge unions source and target selections, dropping duplicate source rows; retire removes assignments to the retired device. Users are not deleted and no user delete cascade is introduced.
- Preserve #80 behavior when there are no globally eligible contacts: omit contact_groups and never write an empty group.
- Keep current checkout untouched. Worktree: /tmp/Pinpoint-issue-79.

- VM acceptance cannot run: scripts/vmlab status reports VBoxManage not found; user confirms only Docker exists here. docker ps initially reports socket permission denied; inspect sudo Docker access before declaring Docker blocked. Keep VM/inbox finish condition unticked and PR draft.

- Docker preflight: docker ps denied at /var/run/docker.sock; sudo -n docker ps requires interactive authentication. No Docker or VM mutation performed. User confirms Docker is the only lab technology here. Live acceptance needs an accessible lab and inbox evidence.
- Injection and secret-exposure review: group names derive only from integer device IDs; PUT rejects booleans, strings, duplicates, unknown IDs and extra fields before config generation. New group members reuse previously validated contact emails; no request text enters commands or paths; no new secrets are read, logged or returned.
- TDD failures observed before implementation: missing HostAlertRecipient model; missing DeviceRecipientsSection module.
- Backend fixture fixes: custom checks use supported check_ping; permission deletion uses explicit SQL bulk delete. Migration parent is c5e2a8f4d716 (current main head), avoiding an accidental second Alembic head.

- Draft PR: https://github.com/esfen14/Pinpoint/pull/160. F1-F7 and F9-F10 are proven by the named isolated tests, specs and all verification; F8 remains blocked. No services, containers, network devices or mailboxes were modified in this environment.
- Final acceptance report: docs/test-runs/2026-10-14-issue-79-preflight/REPORT.md; blocked prerequisites only, no real Nagios or email pass claimed.
- The last session round includes only progress/report metadata after the verified implementation; no code changes after scripts/verify.sh all. Watch final-checkpoint PR CI before reporting status.
