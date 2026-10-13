### Issue #7.1 — System Implementation Add Allowlisted Event Handler Framework with Remediation Audit Log

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** High

**Related Nagios Core Feature:** Event Handlers; Proactive Resolution

**Dependencies:** [Issue #7.3](issue-007-3.md)

**Plan reference:** Issue #7 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #7. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Needs a security review of the design before coding, because it makes Nagios trigger actions. The execution model below (Nagios only records an event, PinPoint decides and runs an allowlisted action) is a proposal that must be confirmed on a lab appliance: spool directory permissions and who can read the spool were not verified.

#### A. Problem Description

PinPoint observes failures but never reacts. No generated Nagios object defines an `event_handler`, although event handlers are enabled globally on appliances (`enable_event_handlers=1`, verified). The preliminary document's claim that event-handler attempts are "mostly in the system" is not supported by the repository.

Without a framework, administrators cannot define a safe action to run when a service reaches a hard failure state, and there is no audit trail of automated actions.

**Out of scope for this issue:**

- Specific recovery actions such as restarting a service (Issues #8.x).
- Running arbitrary commands, scripts or uploaded code. This framework only runs actions chosen from a fixed list.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Nagios stores `Current_Attempt`, `Max_Attempts`, `Last_State_Change` per host and service (`server/app/history_models.py`) and PinPoint displays them, but nothing acts on them.
- `server/app/network_discovery/create_host_cfg.py` and `host_config_templates.py` generate hosts, services and commands; `plugin_registry.py` shows how a command definition is rendered with forbidden-character checks (`FORBIDDEN_VALUE_CHARACTERS`).
- `server/app/scheduler.py` registers APScheduler jobs (`max_instances=1`, `coalesce=True`) and is the place for a consumer job.
- Audit logging: `server/app/logging/` and `ActivityLog`; the Logs page reads them through `server/app/api/system/log.py`.
- The `/usr/local/nagios/var/spool` directory exists on a lab appliance. Whether the `pinpoint` user can read a new subdirectory there, and where an executable for Nagios should live, are *further investigation required* (see Issue #7.3).

#### C. Required Changes

**Backend / System**

1. Add models *(proposed, `server/app/system_models.py`)*: `RemediationAction` (name, action type from a fixed enum, scope host or service pattern, parameters JSON validated per type, enabled flag, max runs per hour, cooldown seconds, `Version`, `Updated_By`) and `RemediationRun` (action, host, service, state, state type, attempt, started and finished time, outcome, exit code, truncated redacted output). Migration included.
2. Define one Nagios command `pinpoint_event_handler` *(proposed template)* with arguments `$SERVICESTATE$ $SERVICESTATETYPE$ $SERVICEATTEMPT$ $HOSTNAME$ $SERVICEDESC$` (and the host equivalent) that calls a small Pinpoint-owned executable. The executable only appends one validated JSON line to a spool directory and exits; it never runs an action itself.
3. Add a consumer *(proposed, `server/app/remediation.py`)* run by a short APScheduler job in `scheduler.py` that reads spool lines, ignores anything that is not a HARD state, matches enabled actions, enforces cooldown and the hourly cap, runs the action type's fixed implementation as the `pinpoint` user, and writes a `RemediationRun` row for every decision, including skipped ones.
4. Render `event_handler pinpoint_event_handler` and `event_handler_enabled 1` only on services and hosts covered by at least one enabled action, through `create_service()` and `create_host()`. Services with no matching action are rendered exactly as today.
5. Add routes *(proposed, `server/app/api/system/remediation.py`)* to list, create, update, enable and disable actions and to page through runs, with route docstrings, a new seeded permission *(proposed, for example `remediation.manage`)* in `seed.py`, validation of every parameter, and apply through `regenerate_and_apply_config_status()`.
6. Log each run to the activity log summary without secrets. Cap stored output length.

#### D. Implementation Guidelines

- No action type may take a command line or script path from a request. Each action type is code that takes validated, typed parameters.
- Never run anything as the `nagios` user beyond the spool writer. Remediation runs as the `pinpoint` user under its existing privileges (`sudoers` allows only the SMTP helper and `systemctl reload nagios` today).
- Prevent restart loops with the cooldown and hourly cap, and record when a cap stops an action.
- Handle duplicate spool lines and a restart of the consumer without running an action twice.

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

- [ ] With no actions defined, generated config contains no `event_handler` and is unchanged.
- [ ] Enabling an action for a service adds the handler to that service only, and Nagios validates the config.
- [ ] A hard CRITICAL for a covered service produces exactly one `RemediationRun` and at most one execution; a soft state produces none.
- [ ] The cooldown and hourly cap stop repeated runs and the skip is recorded with its reason.
- [ ] A malformed or oversized spool line is discarded and logged without crashing the consumer.
- [ ] Creating an action needs the new permission (403 otherwise) and rejects invalid parameters with 400.
- [ ] No secret or credential appears in a run record, a log line or a response.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Engineering_Standards.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #7.2.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: spool parsing (valid, malformed, oversized, duplicate), cooldown and cap logic, state filtering, parameter validation per action type.
- Unit: template output with and without actions.
- API: permission, 400, 409 (stale version) and apply-failure paths.
- Migration up and down; `flask sync-permissions` adds the permission.
- Security: attempts to inject shell characters through every parameter and through the spool line are rejected.
- Lab (record in `docs/test-runs/`): harmless test action on a lab service forced to a hard failure and recovery.

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
