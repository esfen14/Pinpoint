### Issue #8 — System Implementation Add Local and Remote Service Recovery Actions With Restricted Sudo Rule

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** High

**Related Nagios Core Feature:** Service Recovery

**Dependencies:** [Issue #7](issue-007.md)

**Plan reference:** Issue #8 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 8.1 (System):** Waits for the event handler framework (Issue #7).  
> **Part 8.2 (Installer):** Waits for the security review of Issue #7. The code location is known (installer repository, `setup/configure-pinpoint-privileges.sh`).  
> **Part 8.3 (System):** Blocked by investigation. PinPoint has a deployment key and account on devices, but what the on-device sudo rule and helper allow was not verified, and an expanded rule on monitored devices is a security decision.

#### A. Problem Description

**Part 8.1 (System) — System Implementation Add Local Service Restart Action Type for Service Recovery**

Nagios Core can automatically restart a failed service through an event handler. PinPoint has no recovery action at all. The first useful case is a service that runs on the PinPoint/Nagios host itself, such as Nagios or the PinPoint web service.

**Part 8.2 (Installer) — Installer Implementation Add Restricted Sudo Rule for Allowlisted Local Service Restarts**

`pinpoint` may not restart services. A recovery action needs a rule that allows exactly the permitted restarts and nothing more.

**Part 8.3 (System) — System Implementation Add Remote Service Restart Through the NCPA Deployment Account**

Most failed services are on monitored devices, not on the PinPoint host. There is no way to restart them automatically.

**Out of scope for this issue:**

- Arbitrary unit names or commands.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 8.1: No remediation module exists. The framework is specified in Issue #7.
- Part 8.1: The `pinpoint` user may run only `/usr/local/sbin/pinpoint-apply-smtp` and `systemctl reload nagios` through `sudo` (verified on a lab appliance), so a restart needs a new, narrow rule (Part 8.2).
- Part 8.1: Server-side check support: `server/app/network_discovery/custom_checks.py` → `SERVER_CHECK_FIELDS` defines checks that run on the Nagios host (`check_apt`, `check_uptime`, ...). `check_nagios` is one of them.
- Part 8.2: Verified `sudoers` on a lab appliance: `pinpoint ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-apply-smtp ""` and `pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl reload nagios, /bin/systemctl reload nagios`.
- Part 8.2: The SMTP helper pattern (fixed path, exact-field input, root-owned) is the model for a narrow privilege.
- Part 8.3: `server/app/ncpa_deployment/ncpa_deployment.py` installs a deployment account and a key (`PRIVATE_KEY_PATH`, `~/.ssh/pinpoint_ncpa_deploy` of the service user) and a sudo rule and helper on each device. `SSHCredentials` records the pinned SSH port, `Key_Installed` and the key fingerprint, never a password (`server/app/system_models.py`).
- Part 8.3: The helper and rule currently exist for the NCPA install. What they permit for other commands is *further investigation required*.
- Part 8.3: SSH host-key pinning and fingerprint confirmation are mandatory in this module (Engineering Standards "Sensitive modules").

#### C. Required Changes

**Backend / System**

1. **Part 8.1 (System):** Add an action type `restart_local_service` *(proposed, in `server/app/remediation.py`)* whose only parameter is a unit name chosen from a fixed list in code (for example `nagios`), never from a request.
2. **Part 8.1 (System):** Execute with an argument list (no shell) through `sudo -n /usr/bin/systemctl restart <unit>`, with a timeout, and record the exit code and a redacted, truncated output in `RemediationRun`.
3. **Part 8.1 (System):** Refuse the action when the unit is not in the list, when the cooldown or hourly cap applies, or when Maintenance Mode is on (`SystemSettings.Maintenance_Mode`), and record the reason.
4. **Part 8.1 (System):** Expose the list of permitted units through the actions API so the UI can offer only valid choices.
5. **Part 8.3 (System):** First investigate and document exactly what the remote helper and sudo rule allow, in a short design note added to this issue before any code.
6. **Part 8.3 (System):** If acceptable, add an action type `restart_remote_service` *(proposed)* that connects with the deployment key to the pinned SSH port, verifies the stored host-key fingerprint, and runs only a fixed remote restart for a service name from a per-device allowlist.
7. **Part 8.3 (System):** Require an administrator to enable the action per device, record each run, and refuse devices that are not trusted, paused or retired.

**Installer / Deployment**

1. **Part 8.2 (Installer):** Add a drop-in under `/etc/sudoers.d/` that allows `pinpoint` to run `systemctl restart` for each allowlisted unit as separate full command lines (no wildcards), validated with `visudo -c` during install.
2. **Part 8.2 (Installer):** Keep the list identical to the list in Part 8.1's code and document where both must change together.
3. **Part 8.2 (Installer):** Follow the existing pattern in `setup/configure-pinpoint-privileges.sh` (installer repository): write the rule to a `mktemp` file, run `visudo -cf`, on failure delete the temp file and exit so the previous rule stays, otherwise `install -m 440 -o root -g root`. The script rewrites its own sudoers files on every run, which is the upgrade handling.
4. **Part 8.2 (Installer):** Update the step 9 sudo check in the same script. It currently asserts that `systemctl restart`, `stop` and `start` are **not** allowed for `pinpoint`; it must still refuse every unit that is not allowlisted and accept the allowlisted ones, otherwise the installer fails its own verification.

#### D. Implementation Guidelines

- Restarting `pinpoint-gunicorn` from inside itself can kill the consumer mid-run. Either exclude it from the first release or run it detached and record the outcome on the next start.
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

- [ ] **Part 8.1 (System):** An action for a unit outside the fixed list is rejected with 400 at creation and refused at run time.
- [ ] **Part 8.1 (System):** A hard failure of a covered check triggers at most one restart within the cooldown, and the run is recorded with the exit code.
- [ ] **Part 8.1 (System):** Maintenance Mode and the hourly cap block the restart and record why.
- [ ] **Part 8.1 (System):** No shell is used, and the command output contains no secrets.
- [ ] **Part 8.2 (Installer):** `sudo -n systemctl restart <allowlisted unit>` works for `pinpoint` and any other unit is refused.
- [ ] **Part 8.2 (Installer):** No wildcard or shell is permitted by the rule, and `visudo -c` passes.
- [ ] **Part 8.2 (Installer):** Existing sudo rules are unchanged.
- [ ] **Part 8.3 (System):** The design note records what the on-device rule allows and the decision taken.
- [ ] **Part 8.3 (System):** A restart runs only on a trusted device with a matching host-key fingerprint, and a changed fingerprint stops it and is recorded.
- [ ] **Part 8.3 (System):** A service not on the device's allowlist is refused.
- [ ] **Part 8.3 (System):** Every attempt is recorded, and no key or credential appears in a log or response.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Admin guide note on what can be restarted automatically; Installer release notes; Admin guide note.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 8.1 (System):** Unit: allowlist enforcement, argument construction (list form), timeout, cooldown, cap, Maintenance Mode.
- **Part 8.1 (System):** Security: unit names containing shell characters or path separators are rejected.
- **Part 8.1 (System):** Lab (record in `docs/test-runs/`): stop a test unit, force the failure, and confirm one restart and one audit row.
- **Part 8.2 (Installer):** Installer script test with `visudo -c`.
- **Part 8.2 (Installer):** VM-lab: positive and negative `sudo -n` commands as `pinpoint`, recorded under `docs/test-runs/`.
- **Part 8.3 (System):** Unit with SSH mocked: fingerprint mismatch, untrusted device, allowlist, timeout.
- **Part 8.3 (System):** Security review of the remote command construction.
- **Part 8.3 (System):** VM-lab run against a target (record in `docs/test-runs/`).

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
