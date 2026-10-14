# Issue #79: Choose which users receive email alerts for each host

Branch: `issue-79-host-alert-recipients`
Status: in-progress

## Finish condition

- [ ] F1: A host with recipients has its own group of only active opted-in users; host and all generated services use it (mocked test).
- [ ] F2: No recipients preserves the default group (test).
- [ ] F3: All ineligible recipients falls back to the default without an empty group (test).
- [ ] F4: Saving requires the separate permission, audits and uses the shared writer (test).
- [ ] F5: Failed validation or reload restores recipients and reports the error (test).
- [ ] F6: Rescans preserve assignments; merge and retire leave no orphan assignments (test).
- [ ] F7: Host detail editor is permission gated and sends recipient IDs (frontend test).
- [ ] F8: VM lab save writes per-host group; Nagios validates; alerts email only selected recipients while another host emails the default group.
- [ ] F9: Backend, data, frontend specifications and Implementation_Status updated.
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

1. [ ] Backend TDD: tests/unit/test_host_recipients.py and migration runner; add HostAlertRecipient in server/app/system_models.py and migration, seeded system.hosts.alerts permission, recipient routes, generated groups in create_host_cfg.py, merge/retire handling in device_identity.py. Update backend/data specs for route drift. Run focused then backend verification.
2. [ ] Frontend TDD: host editor and drawer integration tests; add DeviceRecipientsSection.tsx, types/hostRecipients.ts, and permission gate in StatusDetailDrawer.tsx. Update frontend and device inventory specifications; run frontend verification.
3. [ ] Live acceptance: inspect VM-lab ownership and tools, run issue-authorized save/validation/delivery comparison if exclusive lab and mailbox access are available; record sanitized report in docs/test-runs, refresh Implementation_Status, and run docs verification.
4. [ ] Re-read issue/comments, prove each finish condition, scripts/verify.sh all, checkpoint, and open a ready PR only when all acceptance is proven; otherwise draft with outstanding items recorded.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Required docs and source inspected; isolated worktree; prerequisite checked | gh issue view 80 and gh pr list --state merged --search 80 | #80 merged and VM verification documented |

## State for the next session

- Last check run (exact command): git status --short
- Result (first failing lines, or green): green; clean isolated worktree before plan creation.
- Hypothesis: NetDiscoveryID is durable across rescans. Numeric device-ID group names avoid injection. Eligibility derives from existing active/opt-in filter. The shared writer reads uncommitted flushed assignments, allowing rollback on apply failure.
- Next action: Add isolated backend recipient tests and confirm they fail before implementation.

## Decisions and notes

- The requested workflow is .agent/workflows/work-issue.md (no .agents/workflows/work-issue exists).
- Workflow sensitive-module pause was explained; user continued twice after switching to unrestricted permissions. Proceed with the requested writer changes and additive migration, including explicit injection/secret-exposure review.
- New permission: system.hosts.alerts, separate from account.alerts and system.hosts.edit; both read and write recipients require it.
- Recipient rows use the stable device ID, never hostname/IP. Merge unions source and target selections, dropping duplicate source rows; retire removes assignments to the retired device. Users are not deleted and no user delete cascade is introduced.
- Preserve #80 behavior when there are no globally eligible contacts: omit contact_groups and never write an empty group.
- Keep current checkout untouched. Worktree: /tmp/Pinpoint-issue-79.
