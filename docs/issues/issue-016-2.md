### Issue #16.2 — System Implementation Add NCPA Deployment Cleanup Action

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Linux/Unix Servers

**Dependencies:** None

**Plan reference:** Issue #16 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #16. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

A failed NCPA install leaves the deployment account, its key, sudo rule and helper on the device. The error message says so (`LEFTOVER_NOTE`), but nothing removes them, so a failed device keeps a privileged account indefinitely.

**Out of scope for this issue:**

- The button (Issue #16.3).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/ncpa_deployment/ncpa_deployment.py`: `LEFTOVER_NOTE` (line 33), the bootstrap and install steps, SSH helpers with `expected_exit_codes`, host-key fingerprint checks, and `PRIVATE_KEY_PATH`.
- `server/app/api/system/ncpa_deployment.py`: routes under `system.deploy.ncpa` (fingerprint, confirm-trust, check-credentials, start, stop, status, runs).
- Credentials are accepted only in request bodies, used for one SSH session and never stored, logged or returned (`Backend_Modules_and_Routes.md`).
- `NCPADeployment.Agent_Status` records `Deployment Failed` and `Pending NCPA`.

#### C. Required Changes

**Backend / System**

1. Add `POST /api/system/deployment/ncpa/<device_id>/cleanup` *(proposed, in `api/system/ncpa_deployment.py`)* under `system.deploy.ncpa`, requiring the same request-body credentials and a trusted, fingerprint-confirmed device as deployment does.
2. Implement a cleanup routine *(proposed, in `ncpa_deployment.py`)* that removes the key from `authorized_keys`, the sudo rule and the helper, and optionally the account, using argument lists and the existing SSH wrappers. Report each removed item and each failure.
3. Refuse when the agent is deployed and healthy, when the device is not trusted, or when a deployment is running for it. Write an activity-log entry and update `Agent_Status` and `Error` without leaking credentials.

#### D. Implementation Guidelines

- Review as a privileged remote operation: every command constructed from validated, fixed pieces; verify the host-key fingerprint before connecting; never log credentials.

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

- [ ] Cleanup after a failed install removes the key, rule, helper and (if requested) account, and reports each step.
- [ ] Cleanup is refused for a healthy deployed agent, an untrusted device and a device with a running deployment.
- [ ] A changed host key stops the operation before any command runs.
- [ ] No credential appears in any response, log line or database row.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #16.3.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit with SSH mocked: each step's success and failure, fingerprint mismatch, refusal states.
- Security review of command construction.
- VM-lab (record in `docs/test-runs/`): fail an install on purpose, run cleanup, confirm the device is clean.
- Regression: `test_ncpa_deployment_runs.py`, `test_ncpa_command_logging.py`.

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
