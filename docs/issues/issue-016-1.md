### Issue #16.1 — System Refinement Track the Deployed NCPA Port Per Device

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Linux/Unix Servers

**Dependencies:** None

**Plan reference:** Issue #16 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #16. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

`NCPA_PORT` is one global setting. An agent deployed on another port is not tracked, so checks, probes and relocation use the wrong port. `Implementation_Status.md` lists this as a known gap.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/config.py` → `NCPA_PORT = "5693"`, used by `plugin_registry.py` (`config_defaults` for `ncpa`), `ncpa_deployment.py` (the remote helper sets the listener port to it) and `network_discovery/ncpa_relocation.py`.
- `NCPADeployment` in `server/app/system_models.py` stores the per-device `Token`, `Agent_Status` and `Error` but no port.
- `server/app/network_discovery/create_host_cfg.py` → `add_ncpa_port()` attaches the NCPA service after a deployment.
- Per-device SSH port precedent: `SSHCredentials.SSH_Port` and `port_lifecycle.device_ssh_port()`.
- Tests: `test_ncpa.py`, `test_ncpa_deployment_runs.py`, `test_ncpa_identity.py`, `test_port_lifecycle.py`.

#### C. Required Changes

**Backend / System**

1. Add a nullable `Port` column to `NCPADeployment` with a migration that backfills existing deployed rows with the current `NCPA_PORT` value.
2. Record the port at deployment time and make `ncpa_checks()`, the relocation job, the certificate and reachability probes (`verify_ncpa_reachable`) and the skipped-service logic read the per-device port, falling back to `NCPA_PORT` when it is empty.
3. Keep the rule that the NCPA port always maps to `ncpa` in the Port to Service table, and keep the NCPA port of a deployed agent protected from edits.
4. Add a re-port action only if the port can become user-configurable; otherwise document that the column exists for tracking.

#### D. Implementation Guidelines

- Preserve behavior for every existing deployment: after the migration, generated config must be byte-identical.

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

- [ ] After the migration, generated Nagios config for existing NCPA devices is unchanged.
- [ ] A device deployed on a non-default port is monitored, probed and relocated on that port.
- [ ] A device with no stored port uses `NCPA_PORT`.
- [ ] The migration downgrades cleanly.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: port resolution (stored, missing), command rendering, relocation and probes with a non-default port.
- Migration up and down with backfill (see `test_ncpa_results_migration.py`).
- Lab NCPA run on a non-default port (record in `docs/test-runs/`).
- Regression: the NCPA tests listed above.

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
