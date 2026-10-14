### Issue #12 — System Implementation Add Database Restore Command and Backup Health Reporting

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Redundant Monitoring

**Dependencies:** None

**Plan reference:** Issue #12 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Covers a documented cold-standby recovery only. Active/passive failover (two live nodes, duplicate-check prevention, split-brain handling) is not planned here and needs its own architecture decision, because PinPoint uses SQLite and an in-process scheduler on one host.

#### A. Problem Description

PinPoint has no redundancy: if the host is lost, monitoring and the dashboard stop together. The only protection is a daily database backup that nothing can restore, and nothing tells an administrator when backups stop. Nagios Core supports redundant monitoring hosts; PinPoint cannot yet recover onto a replacement host in a defined way.

**Out of scope for this issue:**

- A second live node or automatic failover.
- Backing up Nagios configuration or the NCPA deployment key (record the gap in the documentation, decide separately).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/automation.py` → `backup_databases()` copies `system.db` and `history.db` with SQLite's online backup API into timestamped folders under `DATABASE_BACKUP_DIR`, keeping `DATABASE_BACKUP_KEEP` (7). `list_backups()` and `is_due()` support scheduling; the setting is `SystemSettings.Automatic_Backups`.
- `server/app/api/commands/seed.py` defines the Flask CLI commands (`seed`, `init-production`, `sync-permissions`) and is the model for a new command.
- `server/config.py` → `DATABASE_BACKUP_DIR`, `DATABASE_BACKUP_KEEP`, `SQLALCHEMY_BINDS`.
- Tests: `server/tests/unit/test_automation.py`.
- The service runs as user `pinpoint` under `pinpoint-gunicorn.service` with `PINPOINT_SCHEDULER=1`.

#### C. Required Changes

**Backend / System**

1. Add a CLI command *(proposed `flask restore-backup <folder>`, in a new `server/app/api/commands/restore.py` registered in `server/app/__init__.py`)* that validates the folder name against `BACKUP_FOLDER_FORMAT`, checks both database files exist and pass `PRAGMA integrity_check`, refuses to run while the web service is active unless forced, makes a safety copy of the current databases, and replaces them atomically.
2. After a restore, print the follow-up steps: run `flask db upgrade --multidb` and `flask sync-permissions`, and regenerate the Nagios config through the existing writer.
3. Add backup health to the status data *(proposed fields on `GET /api/system/dashboard/status` or a new route)*: time of the newest backup, count, total size, whether `Automatic_Backups` is on, and a `stale` flag when the newest backup is older than twice the backup interval.
4. Write an activity-log entry for scheduled backup failures, which today are only logged.

#### D. Implementation Guidelines

- A restore is destructive. Require an explicit confirmation flag, keep the safety copy, and never touch files outside the configured backup and database paths.

General rules for every issue:

- Reuse the existing modules named in section B instead of adding parallel ones.
- Follow `spec files/Engineering_Standards.md`: route docstrings and banners, `success()`/`error()` envelopes, guard-clause validation, `db.session.rollback()` on every failed commit, TypeScript only in `client/src`.
- Keep existing behavior unchanged by default. New settings must default to what the code does today, and an existing test must prove the default output is unchanged.
- Any change under `app/network_discovery/`, `app/ncpa_deployment/` or a command execution path needs the injection and secret-exposure review required by Engineering Standards "Sensitive modules": no untrusted input in shell commands or Nagios config, no secrets in logs or responses, and Nagios pre-apply validation preserved.
- New permissions are seeded in `server/app/api/commands/seed.py`, granted through `flask sync-permissions`, and wired to client page access where applicable. The client guard never replaces the server check.
- Model changes need a multi-database migration (`flask db migrate --multidb`) that is reviewed, not hand-edited without reason, with a working downgrade.
- Any Nagios config change goes through `regenerate_and_apply_config_status()` in `server/app/network_discovery/create_host_cfg.py`, so it is validated with the Nagios binary and rolled back if rejected.
- Every user-facing control needs loading, error, empty and success states and a plain-language label.
- Consider reliability and cost: bound loops, set timeouts on network calls, and avoid per-poll work that grows with the number of hosts.
- Update the matching file in `spec files/` and `Implementation_Status.md` in the same pull request, as `AGENTS.md` requires.

#### E. Acceptance Criteria

- [ ] `restore-backup` refuses an invalid folder name, a missing database file, a corrupted database, and a running service (without the force flag).
- [ ] A valid restore replaces both databases atomically and leaves a safety copy of the previous ones.
- [ ] After the documented follow-up steps, a restored appliance starts and shows the backed-up data.
- [ ] The status data reports the newest backup time and a stale flag, and handles an empty backup folder.
- [ ] A failed scheduled backup creates an activity-log entry.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Agent_Workflow_and_CI.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: A recovery runbook added under `docs/manuals/`.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: path and name validation, integrity check, safety copy, atomic replace, refusal paths (use temp SQLite files).
- Unit: backup health calculation including stale, empty and disabled cases.
- Lab (record in `docs/test-runs/`): restore a backup onto a freshly installed appliance (`scripts/vmlab fresh`) and confirm the app starts with the restored data.
- Regression: `test_automation.py`.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

**A pull request addressing this issue must not be merged until all applicable conditions below are fulfilled.**

#### Functional Completion

- [ ] All mandatory acceptance criteria are satisfied.
- [ ] Required functionality works as specified.
- [ ] Existing behavior has not been unintentionally broken.
- [ ] Applicable edge cases are handled.

#### Code Quality

- [ ] Code follows PinPoint's existing architectural patterns and conventions.
- [ ] No unnecessary duplicate functionality is introduced.
- [ ] Relevant linting and static analysis checks pass.
- [ ] No unresolved critical defects remain.

#### Testing

- [ ] Required automated tests are added or updated.
- [ ] All applicable automated tests pass.
- [ ] Relevant integration and regression tests pass.
- [ ] Test results or verification evidence are attached to the pull request.

#### Security and Reliability

- [ ] User inputs and configuration values are validated.
- [ ] Authorization is enforced where required.
- [ ] Sensitive data is handled securely.
- [ ] Errors are handled without introducing uncontrolled failures.
- [ ] Relevant performance and reliability requirements are satisfied.

#### Documentation

- [ ] Relevant technical documentation is updated.
- [ ] User documentation is updated for user-facing changes.
- [ ] New configuration parameters are documented.
- [ ] Deployment or migration steps are documented where applicable.

#### Pull Request Review

- [ ] The pull request references the corresponding issue number.
- [ ] The pull request describes the implementation and testing performed.
- [ ] Required CI checks pass.
- [ ] All required reviewer approvals are obtained.
- [ ] Blocking review comments are resolved.
- [ ] All applicable acceptance criteria and required deliverables are complete.

Do not mark this issue as completed solely because code has been written. Test results, reviewer approvals and deployment verification must be backed by evidence attached to the pull request and must not be claimed without it.
