### Issue #24 — System Implementation Add Remediation Safety Controls, Run Retention and Consumer Health Reporting

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Event Handlers; Proactive Resolution

**Dependencies:** [Issue #7](issue-007.md). The acknowledgement and downtime checks also need [Issue #19](issue-019.md) and [Issue #9](issue-009.md).

**Plan reference:** Issue #24 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Work that only needs the framework (kill switch, retention, health, interrupted-run handling) can start after Issue #7. The acknowledgement check waits for Issue #19 (acknowledgements reaching Nagios) and the downtime check waits for Issue #9.

#### A. Problem Description

**Part 24.1 (System) — System Implementation Add Global Kill Switch, Operator-Ownership Checks, Retention and Consumer Health**

Issue #7 specifies a cooldown and hourly cap per action, and Issue #8 refuses restarts during Maintenance Mode. Several controls are still missing for something that restarts services unattended:

- There is no single switch to stop all automatic action at once during an incident.
- Nothing stops an action from running on a problem an operator has already acknowledged or that is in scheduled downtime.
- `RemediationRun` rows and spool files grow without bound.
- If the consumer stops (a failed scheduler job, a full disk, an unreadable spool), events pile up silently and no one learns that automatic recovery has stopped working.
- A crash while an action is running leaves a run in an unknown state, and a naive restart could run it again.

**Part 24.2 (Web-Interface) — Web-Interface Implementation Add Kill Switch and Health Card to the Remediation Screen**

Operators need to see whether automatic recovery is healthy and to stop it quickly.

**Out of scope for this issue:**

- Alerting by email about consumer health (use Issue #22's path once it exists).
- Changing the cooldown or hourly cap rules from Issue #7.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 24.1: `SystemSettings.Maintenance_Mode` exists (`server/app/system_models.py`) and is honored by `server/app/automation.py` (`run_due_automation`); Issue #8 Part 8.1 applies it to restart actions only.
- Part 24.1: `server/app/scheduler.py` registers jobs with `max_instances=1`, `coalesce=True`, and already has a `retention_purge` job that prunes the activity log and the history snapshots. The new retention rules extend this job instead of adding a second purge job.
- Part 24.1: `ServiceStatus.Acknowledgement_Type` and `Scheduled_Downtime_Depth` (`server/app/history_models.py`) and `AlertAcknowledgement` (`server/app/system_models.py`) hold ownership and downtime state.
- Part 24.1: `ConfigurationChanges` (`server/app/logging/configuration_changes.py`) is the audit trail for setting changes.
- Part 24.2: `client/src/pages/SystemStatusPage.tsx` and `components/system-status/StatusSummaryPanel.tsx` show system health; the Remediation page is proposed in Issue #7 Part 7.2.

#### C. Required Changes

**Backend / System**

1. **Part 24.1 (System):** Add `SystemSettings.Remediation_Enabled` *(proposed, default true; actions are still individually disabled by default)* and `Remediation_Retention_Days` *(proposed, bounded, default 90)* with a migration. When the switch is off, the consumer still reads the spool and records every matching event as skipped with reason `kill_switch`, and runs nothing.
2. **Part 24.1 (System):** Extend the skip reasons to cover Maintenance Mode for every action type (not only restarts), scheduled downtime (`Scheduled_Downtime_Depth > 0`, after Issue #9) and an acknowledged problem (after Issue #19). Add `Run_When_Acknowledged` to `RemediationAction` *(proposed, default false)*. Record the specific reason on each skipped run.
3. **Part 24.1 (System):** Extend the existing `retention_purge` job to delete `RemediationRun` rows older than the retention setting and spool files older than a fixed age (with a log line), and cap spool entries (for example 1000), discarding the oldest and recording the number dropped.
4. **Part 24.1 (System):** Store a consumer heartbeat (last tick time, last error) on each run and add `GET /api/system/remediation/health` returning last tick, backlog count, oldest spool entry age, runs and caps hit in the last 24 hours, and a `stalled` flag when the heartbeat is older than three intervals.
5. **Part 24.1 (System):** On consumer start, mark any run left in the started state with no finish time as `interrupted`. Never re-execute an interrupted run.
6. **Part 24.1 (System):** Writes to the kill switch and retention need the Issue #7 permission, are audited in `ConfigurationChanges`, and use the same validation and apply flow as other system settings.

**Frontend / Web Interface**

1. **Part 24.2 (Web-Interface):** Add a health card at the top of the Remediation page: last tick, backlog, runs and caps in 24 hours, and a prominent stalled banner.
2. **Part 24.2 (Web-Interface):** Add the kill switch with a confirmation dialog stating that automatic recovery stops for every action, and show its state on every action row.
3. **Part 24.2 (Web-Interface):** Add a `Run when acknowledged` option to the action form with help text, and show skip reasons in the run log.
4. **Part 24.2 (Web-Interface):** Show loading, error and 403 states.

#### D. Implementation Guidelines

- Skipping must be recorded, never silent: every decision, including a skipped one, produces a run row.
- The kill switch must take effect on the next consumer tick without a restart or config reload.
- Health must be cheap: read one row and a directory listing; do not scan history per request.
- Do not delete spool files the consumer has not yet processed unless the cap is hit, and record when it is.

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

#### E. Acceptance Criteria

- [ ] **Part 24.1 (System):** With the switch off, a HARD failure on a covered service records one run skipped with `kill_switch` and nothing runs.
- [ ] **Part 24.1 (System):** Maintenance Mode, an acknowledged problem and scheduled downtime each skip with their own recorded reason (the last two once Issues #19 and #9 are available).
- [ ] **Part 24.1 (System):** Rows and spool files older than their limits are removed by the existing purge job, and the oversized-spool case records the dropped count.
- [ ] **Part 24.1 (System):** A stopped or failing consumer shows `stalled` in the health response within three intervals.
- [ ] **Part 24.1 (System):** A run interrupted by a crash is marked `interrupted` after restart and is not run again.
- [ ] **Part 24.1 (System):** Changing the switch or retention without the permission returns 403, and each change is audited.
- [ ] **Part 24.2 (Web-Interface):** The health card shows live values and a stalled banner when the consumer is stalled.
- [ ] **Part 24.2 (Web-Interface):** Toggling the kill switch requires confirmation and the state persists after reload.
- [ ] **Part 24.2 (Web-Interface):** Skip reasons are visible in the run log.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Page help text for the health card and kill switch; admin guide section on what to do when the consumer is stalled.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 24.1 (System):** Unit: skip-reason precedence, kill switch, retention boundaries, spool cap, heartbeat and stalled calculation, interrupted-run recovery.
- **Part 24.1 (System):** API: health response, 403 and validation paths.
- **Part 24.1 (System):** Migration up and down.
- **Part 24.1 (System):** Lab (record in `docs/test-runs/`): stop the consumer and watch `stalled`; flip the kill switch during a forced failure.
- **Part 24.2 (Web-Interface):** Frontend: health card states, kill switch confirmation, run log reasons, permission guard.
- Regression: existing retention-purge and scheduler tests still pass.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

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
