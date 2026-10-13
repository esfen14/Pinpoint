### Issue #16 — System Refinement Harden NCPA Deployment With Per-Device Port, Cleanup Action and Macro Secrets

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Linux/Unix Servers

**Dependencies:** None

**Plan reference:** Issue #16 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 16.1 (System) — System Refinement Track the Deployed NCPA Port Per Device**

`NCPA_PORT` is one global setting. An agent deployed on another port is not tracked, so checks, probes and relocation use the wrong port. `Implementation_Status.md` lists this as a known gap.

**Part 16.2 (System) — System Implementation Add NCPA Deployment Cleanup Action**

A failed NCPA install leaves the deployment account, its key, sudo rule and helper on the device. The error message says so (`LEFTOVER_NOTE`), but nothing removes them, so a failed device keeps a privileged account indefinitely.

**Part 16.3 (Web-Interface) — Web-Interface Refinement Add Cleanup Action to NCPA Deployment History**

Operators see that a failed device is left with a privileged account but have no way to clean it up from the interface.

**Part 16.4 (System) — System Refinement Move Check Secrets From Command Lines Into Nagios Resource Macros**

The NCPA token is a positional argument of the generated Nagios command, so it is visible in `hosts.cfg` and in process listings. On a lab appliance `hosts.cfg` is mode 0664, so every local user can read every device token. `Implementation_Status.md` already lists the token issue. Passwords for custom checks have the same exposure.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 16.1: `server/config.py` → `NCPA_PORT = "5693"`, used by `plugin_registry.py` (`config_defaults` for `ncpa`), `ncpa_deployment.py` (the remote helper sets the listener port to it) and `network_discovery/ncpa_relocation.py`.
- Part 16.1: `NCPADeployment` in `server/app/system_models.py` stores the per-device `Token`, `Agent_Status` and `Error` but no port.
- Part 16.1: `server/app/network_discovery/create_host_cfg.py` → `add_ncpa_port()` attaches the NCPA service after a deployment.
- Part 16.1: Per-device SSH port precedent: `SSHCredentials.SSH_Port` and `port_lifecycle.device_ssh_port()`.
- Part 16.1: Tests: `test_ncpa.py`, `test_ncpa_deployment_runs.py`, `test_ncpa_identity.py`, `test_port_lifecycle.py`.
- Part 16.2: `server/app/ncpa_deployment/ncpa_deployment.py`: `LEFTOVER_NOTE` (line 33), the bootstrap and install steps, SSH helpers with `expected_exit_codes`, host-key fingerprint checks, and `PRIVATE_KEY_PATH`.
- Part 16.2: `server/app/api/system/ncpa_deployment.py`: routes under `system.deploy.ncpa` (fingerprint, confirm-trust, check-credentials, start, stop, status, runs).
- Part 16.2: Credentials are accepted only in request bodies, used for one SSH session and never stored, logged or returned (`Backend_Modules_and_Routes.md`).
- Part 16.2: `NCPADeployment.Agent_Status` records `Deployment Failed` and `Pending NCPA`.
- Part 16.3: `client/src/pages/NcpaDeploymentPage.tsx` with `components/ncpa-deployment/` (`DeployWizard.tsx`, `NcpaDevicesTable.tsx`, `DeploymentHistoryTable.tsx`, `DeploymentRunDrawer.tsx`, `DeploymentBadges.tsx`).
- Part 16.3: `client/src/lib/ncpaDeploymentApi.ts`, `types/ncpaDeployment.ts`. The wizard already collects credentials and verifies the host key per device.
- Part 16.3: Tests: `NcpaDeployWizard.test.tsx`, `NcpaDeploymentPage.test.tsx`.
- Part 16.4: `server/app/network_discovery/plugin_registry.py`: the `ncpa` definition has `arguments=(("-P", "port"), ("-t", "token"), ("-M", "metric_path"))`; the token is stored in `NCPADeployment.Token` (`server/app/system_models.py`).
- Part 16.4: `server/app/network_discovery/custom_checks.py` and `secrets_store.py`: custom-check passwords are encrypted at rest and written to `hosts.cfg` in plain text.
- Part 16.4: `server/app/nagios/status.py` strips check-command arguments before storing snapshots in `history.db`.
- Part 16.4: Verified on a lab appliance: `/usr/local/nagios/etc/resource.cfg` is `nagios:nagios` mode 0660, the `pinpoint` user is in group `nagios`, `hosts.cfg` is `pinpoint:nagios` mode 0664, and `sudoers` allows `systemctl reload nagios`.
- Part 16.4: Nagios resource files define `$USER1$` to `$USER256$`, which limits the number of distinct secret macros to 256 (a documented Nagios limit, to be confirmed on 4.5.11).

#### C. Required Changes

**Backend / System**

1. **Part 16.1 (System):** Add a nullable `Port` column to `NCPADeployment` with a migration that backfills existing deployed rows with the current `NCPA_PORT` value.
2. **Part 16.1 (System):** Record the port at deployment time and make `ncpa_checks()`, the relocation job, the certificate and reachability probes (`verify_ncpa_reachable`) and the skipped-service logic read the per-device port, falling back to `NCPA_PORT` when it is empty.
3. **Part 16.1 (System):** Keep the rule that the NCPA port always maps to `ncpa` in the Port to Service table, and keep the NCPA port of a deployed agent protected from edits.
4. **Part 16.1 (System):** Add a re-port action only if the port can become user-configurable; otherwise document that the column exists for tracking.
5. **Part 16.2 (System):** Add `POST /api/system/deployment/ncpa/<device_id>/cleanup` *(proposed, in `api/system/ncpa_deployment.py`)* under `system.deploy.ncpa`, requiring the same request-body credentials and a trusted, fingerprint-confirmed device as deployment does.
6. **Part 16.2 (System):** Implement a cleanup routine *(proposed, in `ncpa_deployment.py`)* that removes the key from `authorized_keys`, the sudo rule and the helper, and optionally the account, using argument lists and the existing SSH wrappers. Report each removed item and each failure.
7. **Part 16.2 (System):** Refuse when the agent is deployed and healthy, when the device is not trusted, or when a deployment is running for it. Write an activity-log entry and update `Agent_Status` and `Error` without leaking credentials.
8. **Part 16.4 (System):** Add a writer *(proposed `server/app/network_discovery/resource_macros.py`)* that maintains a PinPoint-owned block in `resource.cfg` mapping secrets to `$USERn$` slots from a reserved range, writes atomically with owner `nagios:nagios` and mode 0660, and never touches lines outside its block.
9. **Part 16.4 (System):** Render the NCPA token and custom-check passwords as `$USERn$` macros in the generated commands, so literals never reach `hosts.cfg`. Allocate slots deterministically per device and secret, and reclaim them when a device or check is removed.
10. **Part 16.4 (System):** Write `hosts.cfg` with mode 0640 (group `nagios` can read, others cannot) when it is generated.
11. **Part 16.4 (System):** Handle the 256-slot limit: refuse to create more with a clear error, or fall back with a documented warning. Decide during implementation and record it.
12. **Part 16.4 (System):** Apply in the existing order: write resource file, regenerate and validate `hosts.cfg`, reload through the existing apply path, and roll both back when validation fails.

**Frontend / Web Interface**

1. **Part 16.3 (Web-Interface):** Add a "Clean up" action for devices in `Deployment Failed` state, reusing the credential and host-key steps of the wizard, with a confirmation that lists what will be removed.
2. **Part 16.3 (Web-Interface):** Show the per-step result and failures, and update the device's status without a page reload.
3. **Part 16.3 (Web-Interface):** Do not keep credentials in component state after the call completes.

#### D. Implementation Guidelines

- Preserve behavior for every existing deployment: after the migration, generated config must be byte-identical.
- Review as a privileged remote operation: every command constructed from validated, fixed pieces; verify the host-key fingerprint before connecting; never log credentials.
- This changes the contents of config for every NCPA device. Prove with tests that the rendered command resolves to the same effective command when macros are expanded, and test an upgrade from literal tokens to macros.
- Keep stripping arguments from stored snapshots. Do not log macro values.

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

- [ ] **Part 16.1 (System):** After the migration, generated Nagios config for existing NCPA devices is unchanged.
- [ ] **Part 16.1 (System):** A device deployed on a non-default port is monitored, probed and relocated on that port.
- [ ] **Part 16.1 (System):** A device with no stored port uses `NCPA_PORT`.
- [ ] **Part 16.1 (System):** The migration downgrades cleanly.
- [ ] **Part 16.2 (System):** Cleanup after a failed install removes the key, rule, helper and (if requested) account, and reports each step.
- [ ] **Part 16.2 (System):** Cleanup is refused for a healthy deployed agent, an untrusted device and a device with a running deployment.
- [ ] **Part 16.2 (System):** A changed host key stops the operation before any command runs.
- [ ] **Part 16.2 (System):** No credential appears in any response, log line or database row.
- [ ] **Part 16.3 (Web-Interface):** A permitted user can run cleanup for a failed device after confirming its host key and entering credentials, and sees each step's result.
- [ ] **Part 16.3 (Web-Interface):** The action is not offered for healthy, deployed devices.
- [ ] **Part 16.3 (Web-Interface):** Credentials are cleared after the request.
- [ ] **Part 16.3 (Web-Interface):** Existing wizard and page tests pass unchanged.
- [ ] **Part 16.4 (System):** After the change, no NCPA token and no custom-check password appears in `hosts.cfg`, in the process list while a check runs, or in the stored snapshot.
- [ ] **Part 16.4 (System):** NCPA services report the same results as before on a lab appliance.
- [ ] **Part 16.4 (System):** `resource.cfg` content outside PinPoint's block is unchanged, and its owner and mode are kept.
- [ ] **Part 16.4 (System):** `hosts.cfg` has mode 0640 and Nagios still reads it.
- [ ] **Part 16.4 (System):** Removing a device frees its macro slot. Exceeding the limit produces a clear message and no invalid config.
- [ ] **Part 16.4 (System):** A failed validation restores the previous `resource.cfg` and `hosts.cfg`.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Engineering_Standards.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text; Admin note describing where secrets are stored.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 16.1 (System):** Unit: port resolution (stored, missing), command rendering, relocation and probes with a non-default port.
- **Part 16.1 (System):** Migration up and down with backfill (see `test_ncpa_results_migration.py`).
- **Part 16.1 (System):** Lab NCPA run on a non-default port (record in `docs/test-runs/`).
- **Part 16.1 (System):** Regression: the NCPA tests listed above.
- **Part 16.2 (System):** Unit with SSH mocked: each step's success and failure, fingerprint mismatch, refusal states.
- **Part 16.2 (System):** Security review of command construction.
- **Part 16.2 (System):** VM-lab (record in `docs/test-runs/`): fail an install on purpose, run cleanup, confirm the device is clean.
- **Part 16.2 (System):** Regression: `test_ncpa_deployment_runs.py`, `test_ncpa_command_logging.py`.
- **Part 16.3 (Web-Interface):** Frontend: action visibility, confirmation, step results, credential clearing.
- **Part 16.3 (Web-Interface):** Regression: NCPA page and wizard tests.
- **Part 16.4 (System):** Unit: slot allocation, reclamation, block-only editing, atomic write, limit handling, rendering with macros.
- **Part 16.4 (System):** Security: assert the token and password are absent from rendered `hosts.cfg`, logs and responses.
- **Part 16.4 (System):** Upgrade: literal-token config migrates to macros with identical check results.
- **Part 16.4 (System):** Lab (record in `docs/test-runs/`): NCPA services OK after the change, `ps` shows no token, file modes as stated.
- **Part 16.4 (System):** Regression: `test_create_host_cfg.py`, `test_custom_checks.py`, `test_ncpa.py`, `test_status.py`.

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
