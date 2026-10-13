### Issue #17.1 — System Implementation Add Manual NCPA Agent Registration for Windows Hosts

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Windows Servers

**Dependencies:** [Issue #16.1](issue-016-1.md)

**Plan reference:** Issue #17 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #17. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Needs a scope decision on Windows hosts, and NCPA's Windows API paths (disk and process names differ from Linux) must be probed on a lab Windows host first. NRPE is out of scope by team decision.

#### A. Problem Description

PinPoint's agent is NCPA, which is cross-platform, but PinPoint can only install it over SSH on Linux, and its metric defaults assume Linux paths. A Windows server has no supported way to be monitored with NCPA in PinPoint.

**Out of scope for this issue:**

- NRPE (not used). Installing NCPA on Windows automatically.
- NSClient++ (`check_nt` remains only an advanced custom check).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/ncpa_deployment/ncpa_deployment.py` installs over SSH with a systemd helper.
- `NCPADeployment` (`Token`, `Agent_Status`, `Deployement_Method`) and `NCPADevicePartition` (`server/app/system_models.py`) store per-device agent state and disk nodes. `DeploymentMethod` is an enum, so a manual value can be added.
- `server/config.py` → `NCPA_METRICS`; disk path `disk/logical/{partition}/used_percent` (Linux node names such as `|` and `|data`).
- `server/app/api/system/ncpa_deployment.py`: device list and refresh-disks route (`POST .../<device_id>/refresh-disks`) already reads an agent's logical disks.
- `custom_checks.py` includes `check_nt` for NSClient++.

#### C. Required Changes

**Backend / System**

1. Add `Manual` to `DeploymentMethod` (migration for the enum if required) and a route *(proposed `POST /api/system/deployment/ncpa/<device_id>/register`)* under `system.deploy.ncpa` that takes the token and port of an agent the administrator installed, verifies it with `verify_ncpa_reachable()`, stores it, reads its disks through the refresh-disks logic, and attaches the NCPA services through `add_ncpa_port()`.
2. Validate the token format used by the existing code (32 hex characters), the port range, and that the device is known and not retired.
3. Make partition and metric handling accept Windows disk node names, after probing a lab Windows host, without changing Linux behavior.
4. Never accept a request for a Windows host the system cannot reach, and never store anything except the token the deployment table already stores (see Issue #16.4 for how it is passed to Nagios).

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

- [ ] A manually installed NCPA agent on a Windows lab host can be registered and its CPU, memory and disk services reach OK.
- [ ] An unreachable agent or a wrong token is rejected with a clear message and nothing is saved.
- [ ] Linux deployments and their generated config are unchanged.
- [ ] The probe results (valid Windows paths) are recorded in the pull request.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #17.2.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit with the agent mocked: registration success and failures, Windows disk names, Linux regression.
- Lab with a Windows VM (record in `docs/test-runs/`).
- Regression: `test_ncpa.py`, `test_ncpa_identity.py`.

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
