### Issue #8.3 — System Implementation Add Remote Service Restart Through the NCPA Deployment Account

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** High

**Related Nagios Core Feature:** Service Recovery

**Dependencies:** [Issue #7.1](issue-007-1.md); [Issue #8.1](issue-008-1.md)

**Plan reference:** Issue #8 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #8. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Blocked by investigation. PinPoint has a deployment key and account on devices, but what the on-device sudo rule and helper allow was not verified, and an expanded rule on monitored devices is a security decision.

#### A. Problem Description

Most failed services are on monitored devices, not on the PinPoint host. There is no way to restart them automatically.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/ncpa_deployment/ncpa_deployment.py` installs a deployment account and a key (`PRIVATE_KEY_PATH`, `~/.ssh/pinpoint_ncpa_deploy` of the service user) and a sudo rule and helper on each device. `SSHCredentials` records the pinned SSH port, `Key_Installed` and the key fingerprint, never a password (`server/app/system_models.py`).
- The helper and rule currently exist for the NCPA install. What they permit for other commands is *further investigation required*.
- SSH host-key pinning and fingerprint confirmation are mandatory in this module (Engineering Standards "Sensitive modules").

#### C. Required Changes

**Backend / System**

1. First investigate and document exactly what the remote helper and sudo rule allow, in a short design note added to this issue before any code.
2. If acceptable, add an action type `restart_remote_service` *(proposed)* that connects with the deployment key to the pinned SSH port, verifies the stored host-key fingerprint, and runs only a fixed remote restart for a service name from a per-device allowlist.
3. Require an administrator to enable the action per device, record each run, and refuse devices that are not trusted, paused or retired.

#### D. Implementation Guidelines

- Never reuse an SSH session or key for any command outside the allowlist. Never accept a host or service name from a request without matching it to a known device and allowlist entry.

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

- [ ] The design note records what the on-device rule allows and the decision taken.
- [ ] A restart runs only on a trusted device with a matching host-key fingerprint, and a changed fingerprint stops it and is recorded.
- [ ] A service not on the device's allowlist is refused.
- [ ] Every attempt is recorded, and no key or credential appears in a log or response.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Admin guide note.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request.

#### G. Testing and Verification

- Unit with SSH mocked: fingerprint mismatch, untrusted device, allowlist, timeout.
- Security review of the remote command construction.
- VM-lab run against a target (record in `docs/test-runs/`).

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
