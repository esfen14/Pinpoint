### Issue #16.4 — System Refinement Move Check Secrets From Command Lines Into Nagios Resource Macros

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Linux/Unix Servers

**Dependencies:** None

**Plan reference:** Issue #16 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #16. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

The NCPA token is a positional argument of the generated Nagios command, so it is visible in `hosts.cfg` and in process listings. On a lab appliance `hosts.cfg` is mode 0664, so every local user can read every device token. `Implementation_Status.md` already lists the token issue. Passwords for custom checks have the same exposure.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/network_discovery/plugin_registry.py`: the `ncpa` definition has `arguments=(("-P", "port"), ("-t", "token"), ("-M", "metric_path"))`; the token is stored in `NCPADeployment.Token` (`server/app/system_models.py`).
- `server/app/network_discovery/custom_checks.py` and `secrets_store.py`: custom-check passwords are encrypted at rest and written to `hosts.cfg` in plain text.
- `server/app/nagios/status.py` strips check-command arguments before storing snapshots in `history.db`.
- Verified on a lab appliance: `/usr/local/nagios/etc/resource.cfg` is `nagios:nagios` mode 0660, the `pinpoint` user is in group `nagios`, `hosts.cfg` is `pinpoint:nagios` mode 0664, and `sudoers` allows `systemctl reload nagios`.
- Nagios resource files define `$USER1$` to `$USER256$`, which limits the number of distinct secret macros to 256 (a documented Nagios limit, to be confirmed on 4.5.11).

#### C. Required Changes

**Backend / System**

1. Add a writer *(proposed `server/app/network_discovery/resource_macros.py`)* that maintains a PinPoint-owned block in `resource.cfg` mapping secrets to `$USERn$` slots from a reserved range, writes atomically with owner `nagios:nagios` and mode 0660, and never touches lines outside its block.
2. Render the NCPA token and custom-check passwords as `$USERn$` macros in the generated commands, so literals never reach `hosts.cfg`. Allocate slots deterministically per device and secret, and reclaim them when a device or check is removed.
3. Write `hosts.cfg` with mode 0640 (group `nagios` can read, others cannot) when it is generated.
4. Handle the 256-slot limit: refuse to create more with a clear error, or fall back with a documented warning. Decide during implementation and record it.
5. Apply in the existing order: write resource file, regenerate and validate `hosts.cfg`, reload through the existing apply path, and roll both back when validation fails.

#### D. Implementation Guidelines

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

- [ ] After the change, no NCPA token and no custom-check password appears in `hosts.cfg`, in the process list while a check runs, or in the stored snapshot.
- [ ] NCPA services report the same results as before on a lab appliance.
- [ ] `resource.cfg` content outside PinPoint's block is unchanged, and its owner and mode are kept.
- [ ] `hosts.cfg` has mode 0640 and Nagios still reads it.
- [ ] Removing a device frees its macro slot. Exceeding the limit produces a clear message and no invalid config.
- [ ] A failed validation restores the previous `resource.cfg` and `hosts.cfg`.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Engineering_Standards.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Admin note describing where secrets are stored.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: slot allocation, reclamation, block-only editing, atomic write, limit handling, rendering with macros.
- Security: assert the token and password are absent from rendered `hosts.cfg`, logs and responses.
- Upgrade: literal-token config migrates to macros with identical check results.
- Lab (record in `docs/test-runs/`): NCPA services OK after the change, `ps` shows no token, file modes as stated.
- Regression: `test_create_host_cfg.py`, `test_custom_checks.py`, `test_ncpa.py`, `test_status.py`.

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
