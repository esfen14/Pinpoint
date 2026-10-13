### Issue #8.1 — System Implementation Add Local Service Restart Action Type for Service Recovery

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Service Recovery

**Dependencies:** [Issue #7.1](issue-007-1.md); [Issue #8.2](issue-008-2.md)

**Plan reference:** Issue #8 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #8. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Waits for the event handler framework (Issue #7.1).

#### A. Problem Description

Nagios Core can automatically restart a failed service through an event handler. PinPoint has no recovery action at all. The first useful case is a service that runs on the PinPoint/Nagios host itself, such as Nagios or the PinPoint web service.

**Out of scope for this issue:**

- Restarting services on monitored devices (Issue #8.3).
- Arbitrary unit names or commands.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- No remediation module exists. The framework is specified in Issue #7.1.
- The `pinpoint` user may run only `/usr/local/sbin/pinpoint-apply-smtp` and `systemctl reload nagios` through `sudo` (verified on a lab appliance), so a restart needs a new, narrow rule (Issue #8.2).
- Server-side check support: `server/app/network_discovery/custom_checks.py` → `SERVER_CHECK_FIELDS` defines checks that run on the Nagios host (`check_apt`, `check_uptime`, ...). `check_nagios` is one of them.

#### C. Required Changes

**Backend / System**

1. Add an action type `restart_local_service` *(proposed, in `server/app/remediation.py`)* whose only parameter is a unit name chosen from a fixed list in code (for example `nagios`), never from a request.
2. Execute with an argument list (no shell) through `sudo -n /usr/bin/systemctl restart <unit>`, with a timeout, and record the exit code and a redacted, truncated output in `RemediationRun`.
3. Refuse the action when the unit is not in the list, when the cooldown or hourly cap applies, or when Maintenance Mode is on (`SystemSettings.Maintenance_Mode`), and record the reason.
4. Expose the list of permitted units through the actions API so the UI can offer only valid choices.

#### D. Implementation Guidelines

- Restarting `pinpoint-gunicorn` from inside itself can kill the consumer mid-run. Either exclude it from the first release or run it detached and record the outcome on the next start.

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

- [ ] An action for a unit outside the fixed list is rejected with 400 at creation and refused at run time.
- [ ] A hard failure of a covered check triggers at most one restart within the cooldown, and the run is recorded with the exit code.
- [ ] Maintenance Mode and the hourly cap block the restart and record why.
- [ ] No shell is used, and the command output contains no secrets.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Admin guide note on what can be restarted automatically.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request.

#### G. Testing and Verification

- Unit: allowlist enforcement, argument construction (list form), timeout, cooldown, cap, Maintenance Mode.
- Security: unit names containing shell characters or path separators are rejected.
- Lab (record in `docs/test-runs/`): stop a test unit, force the failure, and confirm one restart and one audit row.

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
