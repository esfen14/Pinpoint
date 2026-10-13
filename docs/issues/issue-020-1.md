### Issue #20.1 — System Refinement Clear Acknowledgements on Recovery and Record AUTO_RESOLVED History

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Problem History; Notification History

**Dependencies:** None

**Plan reference:** Issue #20 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #20. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

When a host returns to UP or a service to OK, its Pinpoint acknowledgement stays active and no `AUTO_RESOLVED` history row is written, although the model contract exists (`Implementation_Status.md`, `Data_Model_and_Integrations.md`). A stale acknowledgement then hides a later, different failure of the same service and corrupts the problem history.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/system_models.py`: `AlertAcknowledgement` (one active record per hostname and service) and `AckHistory` (append-only); `AckAction.AUTO_RESOLVED` is defined; `AckHistory.ActorUserID` is nullable for system actions.
- `server/app/nagios/status.py` → `get_status()` runs every 60 seconds from `server/app/scheduler.py` and writes the snapshots that define "latest state".
- `server/app/api/system/dashboard.py` shows the acknowledge routes and their helper functions (`_new_ack`, `_new_ack_history`, `_serialize_ack`).
- `spec files/Display_Requirements.md` §4 and `Alerts_Notifications_History_Requirements.md` define the lifecycle.
- Tests: `server/tests/unit/test_dashboard.py`, `test_status.py`, `test_history.py`.

#### C. Required Changes

**Backend / System**

1. After each successful poll, find active acknowledgements whose host or service is now UP or OK in the latest snapshot, delete them, and append one `AckHistory` row per deletion with action `AUTO_RESOLVED` and no actor. Do it in one transaction with rollback on failure.
2. Make it idempotent so a repeated poll never writes a second history row, and ignore targets that no longer exist.
3. Keep an acknowledgement when the latest snapshot is missing or stale, so a poll failure never auto-resolves anything.
4. Reuse the helpers in `dashboard.py` or move them to a shared module rather than copying them.

#### D. Implementation Guidelines


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

- [ ] When an acknowledged service recovers, the active acknowledgement is removed and exactly one `AUTO_RESOLVED` history row exists after the next poll.
- [ ] A repeated poll adds no further row.
- [ ] A poll that fails or returns no data leaves acknowledgements untouched.
- [ ] An acknowledgement on a still-failing item is kept.
- [ ] Acknowledge, unacknowledge and history routes behave as before.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Alerts_Notifications_History_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request.

#### G. Testing and Verification

- Unit: recovery of host and service, repeated poll, failed poll, still-failing item, deleted target.
- Regression: `test_dashboard.py`, `test_status.py`, `test_history.py`.
- Lab: acknowledge, recover, check history.

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
