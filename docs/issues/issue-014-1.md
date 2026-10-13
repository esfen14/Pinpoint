### Issue #14.1 — System Implementation Add Per-Device Plugin Variables API

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** SNMP Monitoring; Network Services

**Dependencies:** None

**Plan reference:** Issue #14 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #14. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

The configuration generator already lets a device override plugin variables (`NetworkDiscovery.Plugin_Variables`), but no route or screen can write them. The override can only be set by editing the database. Every feature that needs a per-device setting (SNMP version and credentials, web-check options, interface choice) is blocked on this.

**Out of scope for this issue:**

- Specific plugin fields (Issues #14.2, #18, #13.1 define their own fields).
- The forms (Issues #14.3, #18.2).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/system_models.py` line 384: `Plugin_Variables: Mapped[Optional[dict]] = mapped_column(sa.JSON())` on `NetworkDiscovery`.
- `server/app/network_discovery/create_host_cfg.py` (around line 1006) passes `device.Plugin_Variables` into service planning as `plugin_variables`, and `plugin_registry.py` → `resolve_plugin_variables()` applies it above the defaults and Settings values.
- `plugin_registry.py` → `validate_variable_value()` and `FORBIDDEN_VALUE_CHARACTERS` validate a value. `PluginDefinition` lists each plugin's variables.
- `server/app/api/system/device_identity.py` holds the device routes and permissions (`system.hosts`, `system.hosts.edit`) and is the pattern for a device sub-resource with a config apply.
- `server/app/network_discovery/plugin_settings.py` documents the order: per-host overrides win over Settings values and `config.py` defaults.

#### C. Required Changes

**Backend / System**

1. Add `GET /api/system/hosts/<id>/plugin-variables/<plugin>` and `PUT /api/system/hosts/<id>/plugin-variables/<plugin>` *(proposed, in `device_identity.py` or a new `device_plugin_variables.py`)* returning and saving one plugin's override. `<plugin>` must be a registry definition name (404 otherwise). Permissions: `system.hosts` to read, `system.hosts.edit` to write.
2. Validate every key against the plugin definition's declared variables and every value with `validate_variable_value()`. Reject unknown keys, retired or merged devices (400) and oversized bodies.
3. Support removing an override (an empty body or an explicit reset) so a device returns to the defaults.
4. Never return secret-typed values. Only report whether one is set. Secret handling itself is defined by the issue that adds a secret field (Issue #14.2).
5. Save, then apply through `regenerate_and_apply_config_status()`. On failure roll the change back and return 422, matching the port-edit routes. Write an activity-log entry.

#### D. Implementation Guidelines

- Review as sensitive: the values reach Nagios commands, so validation must be identical to the registry's, not a copy that can drift.

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

- [ ] A permitted user can save, read and reset a device's override for a registry plugin, and the generated command for that device changes accordingly.
- [ ] An unknown plugin returns 404, an unknown key or an invalid value returns 400 naming the field, and a retired or merged device is refused.
- [ ] Without the permission the routes return 403.
- [ ] A rejected Nagios config is rolled back with 422.
- [ ] A device with no override renders exactly as before.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered with the forms that use it.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: key and value validation against definitions, reset, retired device, secret values never returned.
- API: 403, 404, 400 and 422 paths with the apply mocked.
- Regression: `test_plugin_registry.py`, `test_create_host_cfg.py`, `test_device_identity_routes.py`.
- Lab: set an override for one device and confirm only that device's command changes (record in `docs/test-runs/`).

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
