# Issue #120: System Implementation Add Allowlisted Event Handler Framework With Remediation Screen and Installer Support

Branch: `issue-120-event-handler-framework`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

Plan issue #7. Design approved by the project owner 2026-10-15 (answers recorded at the top of
the design). Sensitive module: Nagios config generation and an action-running path.
Design: `docs/plans/Event_Handler_Design.md`.

## Finish condition

Copied from the issue's section E. Installer items (Part 7.3) cannot be proven in this repository;
by the owner's instruction they are delivered as installer instructions
(`Installer_Instructions_Proactive_Resolution.md`, PR #157) and verified in the installer repository.

- [ ] 7.1 With no actions defined, generated config has no `event_handler` and is unchanged.
- [ ] 7.1 Enabling an action for a service adds the handler to that service only; Nagios validates.
- [ ] 7.1 A hard CRITICAL for a covered service gives exactly one `RemediationRun` and at most one execution; a soft state gives none.
- [ ] 7.1 Cooldown and hourly cap stop repeated runs; the skip is recorded with its reason.
- [ ] 7.1 A malformed or oversized spool line is discarded and logged without crashing the consumer.
- [ ] 7.1 Creating an action needs the new permission (403 otherwise); invalid parameters give 400.
- [ ] 7.1 No secret or credential appears in a run record, a log line or a response.
- [ ] 7.2 A permitted user can create, edit, enable and disable an action and sees changes after reload.
- [ ] 7.2 The run log lists runs with filters and pagination, including skipped ones.
- [ ] 7.2 Users without the permission do not see the page and are blocked on direct access.
- [ ] 7.2 Server validation errors are shown against the right field.
- [ ] 7.2 Existing navigation and page-access tests pass after being updated for the new page.
- [ ] 7.3 (installer repository) spool folder, root-owned handler, web user cannot modify it, upgrade keeps other config: tracked in the installer instructions.
- [ ] Deliverables: migration with downgrade, tests, specs and Implementation_Status, lab report, `scripts/verify.sh all`.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Models, migration (7.1 C1) | items 3, 6 | migration test, unit tests |
| Handler command and executable (7.1 C2) | items 1-3 | handler unit tests, config tests |
| Consumer and scheduler job (7.1 C3) | items 3-5 | consumer unit tests |
| Config rendering only for covered objects (7.1 C4) | items 1-2 | byte-identical fixture, new template tests |
| Routes, permission, validation (7.1 C5) | items 6 | API tests |
| Activity log without secrets (7.1 C6) | item 7 | unit test |
| Remediation page, run log, route/nav/permission (7.2) | items 8-12 | vitest, PageAccess and App tests |
| Spool and executable on the appliance (7.3) | item 13 | installer repository; lab report |
| Out of scope: real recovery actions (#121) | - | - |

## Plan

1. [x] Design review: approved 2026-10-15 (docs/plans/Event_Handler_Design.md)
2. [x] Migration, models and action registry with tests, plus RemediationRun pruning in _purge_old_data (server/app/system_models.py, server/app/remediation_actions.py, server/app/scheduler.py, new migration)
3. [x] Handler script and consumer with tests (server/scripts/pinpoint_event_handler.py, server/app/remediation.py, server/app/scheduler.py)
4. [ ] Config rendering with byte-identical proof (server/app/network_discovery/host_config_templates.py, create_host_cfg.py, templates)
5. [ ] API routes and permission seeding (server/app/api/system/remediation.py, server/app/api/commands/seed.py)
6. [ ] Frontend page, route, navigation, tests (client/src/pages/RemediationPage.tsx, components/remediation/, App.tsx, Sidebar.tsx, pageAccess.ts)
7. [ ] Specs and Implementation_Status; verify.sh; lab run and report; delete this file; PR ready

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Read issue and standards; wrote the design; edited issue text for D1/D3; opened draft PR | scripts/check_agent_progress.py | n/a, no code |
| 2 | resumed after design approval; found standards reserve history.db for Nagios snapshots, owner chose system.db for RemediationRun | - | design and notes updated |
| 3 | Plan step 2: migration e4a7c1d9b305 (REMEDIATION_ACTION, REMEDIATION_RUN), models, registry (record_only, validation, timeout), RemediationRun pruning in _purge_old_data; tests written first and seen failing | pytest test_remediation_migration.py test_remediation_actions.py test_scheduler.py | 23 passed |
| 4 | Plan step 3, first half: handler server/scripts/pinpoint_event_handler.py; tests first (hostile args, state sets, flood limit, atomic write); tests caught '..' passing the character check, now rejected | pytest tests/unit/test_event_handler.py | 83 passed, 1 skipped (POSIX file mode, runs on Linux CI) |
| 5 | Plan step 3, second half: consumer server/app/remediation.py, config REMEDIATION_SPOOL_DIR/OWNER, 15 s scheduler job, mark_interrupted at start; tests first (decisions, replay, crash, forged/malformed/oversize/symlink/owner, flood, redaction, name parity with handler). Dropped outcomes duplicate, discarded_malformed, skipped_disabled (cannot be stored as rows; design and migration updated) | pytest consumer, handler, actions, migration, scheduler tests | 166 passed, 2 skipped (symlink and POSIX mode tests: Linux CI must prove them) |

## State for the next session

- Last check run (exact command): cd server; python -m pytest tests/unit/test_remediation_consumer.py tests/unit/test_event_handler.py tests/unit/test_remediation_actions.py tests/unit/test_remediation_migration.py tests/unit/test_scheduler.py -q
- Result: 166 passed, 2 skipped (symlink test and handler file-mode test are POSIX only: confirm green on Linux CI)
- Hypothesis: build order in the design is sound; the handler and consumer are the risky part
- Next action: plan step 4, config rendering: failing tests first in server/tests/unit (no enabled action => generated hosts.cfg byte-identical, e.g. fixture notification_policy_default_hosts.cfg; enabled action => event_handler lines only on covered objects; commands only when the handler file exists on this machine; hostile names; quoting), then server/app/network_discovery/host_config_templates.py and create_host_cfg.py. Sensitive module (needs injection review). Also needs a note in the security review doc. Session round limit reached (5)

## Decisions and notes

- Owner decisions 2026-10-14: D1 narrow nagios group rights; D2 no remote restart; D3 handler at /usr/local/sbin with source here.
- Owner instruction: whenever a fix needs the installer, leave an md file for the installer maintainer (as in PR #157).
- Owner asked: review the design before writing code (sensitive module).
- Review answers 2026-10-15: Q1-Q4 accepted; Q4 changed to system.db, plus pruning RemediationRun with Diagnostic_History_Retention_Days (90) in this issue; Q5 test every threat row, lab run limited to security-relevant checks.
- Note for the specs: service-uptime reports (/report/network-services, /device-services) are built from ServiceStatus snapshots, so Diagnostic_History_Retention_Days below 90 shortens last_90d reports. Consider a line in Implementation_Status.md (not part of #120).
- Issue #120 text updated 2026-10-14 to match D1 and D3 (spool group pinpoint, handler in /usr/local/sbin).
- Deviations from the issue wording are listed in the design for the reviewer: one file per event, two commands, two permissions, runs in system.db (changed 2026-10-15: standards reserve history.db for Nagios snapshots).
