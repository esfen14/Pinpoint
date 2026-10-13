### Issue #14 — System Implementation Add Per-Device Plugin Variables API and SNMP v3 Credential Support With Device Form

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** SNMP Monitoring; Network Services; SNMP Monitoring

**Dependencies:** [Issue #16](issue-016.md)

**Plan reference:** Issue #14 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 14.1 (System) — System Implementation Add Per-Device Plugin Variables API**

The configuration generator already lets a device override plugin variables (`NetworkDiscovery.Plugin_Variables`), but no route or screen can write them. The override can only be set by editing the database. Every feature that needs a per-device setting (SNMP version and credentials, web-check options, interface choice) is blocked on this.

**Part 14.2 (System) — System Refinement Add SNMP Version Choice and v3 Credential Support**

SNMP monitoring works for community-based devices only. SNMP v3 (user, authentication, privacy) is not defined, and the community string is a global default with an optional per-device override. Nagios Core monitors v1, v2c and v3.

**Part 14.3 (Web-Interface) — Web-Interface Refinement Add Per-Device SNMP Version and Credential Form**

Administrators can edit the global SNMP OID table but cannot set a device's SNMP version or v3 credentials from the interface.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 14.1: `server/app/system_models.py` line 384: `Plugin_Variables: Mapped[Optional[dict]] = mapped_column(sa.JSON())` on `NetworkDiscovery`.
- Part 14.1: `server/app/network_discovery/create_host_cfg.py` (around line 1006) passes `device.Plugin_Variables` into service planning as `plugin_variables`, and `plugin_registry.py` → `resolve_plugin_variables()` applies it above the defaults and Settings values.
- Part 14.1: `plugin_registry.py` → `validate_variable_value()` and `FORBIDDEN_VALUE_CHARACTERS` validate a value. `PluginDefinition` lists each plugin's variables.
- Part 14.1: `server/app/api/system/device_identity.py` holds the device routes and permissions (`system.hosts`, `system.hosts.edit`) and is the pattern for a device sub-resource with a config apply.
- Part 14.1: `server/app/network_discovery/plugin_settings.py` documents the order: per-host overrides win over Settings values and `config.py` defaults.
- Part 14.2: `server/app/network_discovery/plugin_registry.py`: the `snmp` definition uses `check_snmp` with arguments `-p port`, `-C community`, `-o oid` and options `-P` (protocol), `-w`, `-c`, `-l`, `-u`; defaults `port 161`, `community public`; `config_defaults` from `SNMP_PORT`, `SNMP_COMMUNITY_STRING`, `SNMP_OIDS`.
- Part 14.2: `server/config.py`: `SNMP_COMMUNITY_STRING` (environment override), `SNMP_OIDS`.
- Part 14.2: `server/app/network_discovery/plugin_settings.py` and `server/app/api/system/plugin_settings.py`: OID table saved per plugin. `NetworkDiscovery.Plugin_Variables` overrides per device when generating config, but nothing in the API or UI writes it today (Part 14.1).
- Part 14.2: `server/app/secrets_store.py`: Fernet encryption used for custom-check passwords (`PINPOINT_SECRETS_KEY` or `SECRET_KEY`). `Implementation_Status.md` records that passwords are written to `hosts.cfg` in plain text because Nagios needs them in the command.
- Part 14.2: On a lab appliance `hosts.cfg` is mode 0664 (readable by every local user), which makes command-line secrets world-readable (see Issue #16).
- Part 14.3: `client/src/components/settings/PluginSettings.tsx` (SNMP OID table) with `client/src/lib/pluginSettingsApi.ts` and `types/pluginSettings.ts`.
- Part 14.3: `client/src/components/plugin-manager/CustomCheckDialog.tsx` already handles secret fields with "leave blank to keep" and clear actions, and is the pattern for secrets in a form.
- Part 14.3: `client/src/components/device-inventory/StatusDetailDrawer.tsx` is the per-device surface.
- Part 14.3: Tests: `PluginSettings.test.tsx`, `PluginCustomChecksSection.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 14.1 (System):** Add `GET /api/system/hosts/<id>/plugin-variables/<plugin>` and `PUT /api/system/hosts/<id>/plugin-variables/<plugin>` *(proposed, in `device_identity.py` or a new `device_plugin_variables.py`)* returning and saving one plugin's override. `<plugin>` must be a registry definition name (404 otherwise). Permissions: `system.hosts` to read, `system.hosts.edit` to write.
2. **Part 14.1 (System):** Validate every key against the plugin definition's declared variables and every value with `validate_variable_value()`. Reject unknown keys, retired or merged devices (400) and oversized bodies.
3. **Part 14.1 (System):** Support removing an override (an empty body or an explicit reset) so a device returns to the defaults.
4. **Part 14.1 (System):** Never return secret-typed values. Only report whether one is set. Secret handling itself is defined by the issue that adds a secret field (Part 14.2).
5. **Part 14.1 (System):** Save, then apply through `regenerate_and_apply_config_status()`. On failure roll the change back and return 422, matching the port-edit routes. Write an activity-log entry.
6. **Part 14.2 (System):** Add an SNMP version (1, 2c, 3) to the `snmp` definition and the per-device variables, defaulting to the current behavior. For v3 add security level (`noAuthNoPriv`, `authNoPriv`, `authPriv`), user, authentication protocol and password, and privacy protocol and password, mapped to `check_snmp` options (`-P 3 -L -U -a -A -x -X`).
7. **Part 14.2 (System):** Store v3 passwords encrypted with `secrets_store.py`, never return them from any API, and write them into the Nagios command through resource macros (`$USERn$` in `resource.cfg`) using the writer from Issue #16, so they are not in `hosts.cfg` or process listings.
8. **Part 14.2 (System):** Validate every field against the registry's forbidden-character rules and fixed enumerations, and reject a v3 device without the fields its level needs.
9. **Part 14.2 (System):** Keep v1 and v2c devices rendering exactly as today.
10. **Part 14.2 (System):** Use the per-device plugin variables API from Part 14.1 to save version and credentials, extend the `plugin-settings` validation for the new fields, and add a test-query endpoint or reuse the plugin run check so an administrator can confirm credentials.

**Frontend / Web Interface**

1. **Part 14.3 (Web-Interface):** Add an SNMP section to the device drawer *(proposed `DeviceSnmpSection.tsx`)* with version choice and, for v3, the fields from Part 14.2, with secret fields that are never shown and keep or clear semantics as in `CustomCheckDialog.tsx`.
2. **Part 14.3 (Web-Interface):** Validate required fields per security level before sending and show the server's message.
3. **Part 14.3 (Web-Interface):** Add a "Test" action that reports success or the failure reason.

#### D. Implementation Guidelines

- Review as sensitive: the values reach Nagios commands, so validation must be identical to the registry's, not a copy that can drift.
- Review this under Engineering Standards "Sensitive modules": no credentials in logs, responses or snapshots. `server/app/nagios/status.py` already strips check-command arguments before storing snapshots; keep that true for v3 options.

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

- [ ] **Part 14.1 (System):** A permitted user can save, read and reset a device's override for a registry plugin, and the generated command for that device changes accordingly.
- [ ] **Part 14.1 (System):** An unknown plugin returns 404, an unknown key or an invalid value returns 400 naming the field, and a retired or merged device is refused.
- [ ] **Part 14.1 (System):** Without the permission the routes return 403.
- [ ] **Part 14.1 (System):** A rejected Nagios config is rolled back with 422.
- [ ] **Part 14.1 (System):** A device with no override renders exactly as before.
- [ ] **Part 14.2 (System):** A v2c device renders the same command as before.
- [ ] **Part 14.2 (System):** A v3 authPriv device renders a valid `check_snmp` command whose passwords are macros, not literals, and Nagios validates the config.
- [ ] **Part 14.2 (System):** A v3 device missing a required field is rejected with 400 naming the field.
- [ ] **Part 14.2 (System):** No v3 password appears in `hosts.cfg`, any API response, any log line or a stored snapshot.
- [ ] **Part 14.2 (System):** A lab device with `snmpd` v3 is monitored successfully.
- [ ] **Part 14.3 (Web-Interface):** A user with the needed permission can set version and v3 credentials for a device, and secrets are never displayed after saving.
- [ ] **Part 14.3 (Web-Interface):** Missing fields for the chosen level are blocked with a message.
- [ ] **Part 14.3 (Web-Interface):** The test action reports success or a clear failure.
- [ ] **Part 14.3 (Web-Interface):** Existing plugin settings and drawer tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 14.1 (System):** Unit: key and value validation against definitions, reset, retired device, secret values never returned.
- **Part 14.1 (System):** API: 403, 404, 400 and 422 paths with the apply mocked.
- **Part 14.1 (System):** Regression: `test_plugin_registry.py`, `test_create_host_cfg.py`, `test_device_identity_routes.py`.
- **Part 14.1 (System):** Lab: set an override for one device and confirm only that device's command changes (record in `docs/test-runs/`).
- **Part 14.2 (System):** Unit: command rendering per version and level, validation matrix, forbidden characters, macro substitution.
- **Part 14.2 (System):** Security: grep generated config, logs and API responses for the password in tests.
- **Part 14.2 (System):** Lab (record in `docs/test-runs/`): `snmpd` configured for v3 authPriv.
- **Part 14.2 (System):** Regression: `test_plugin_registry.py`, `test_plugin_settings.py`, `test_create_host_cfg.py`.
- **Part 14.3 (Web-Interface):** Frontend: conditional fields, secret handling, validation, test action.
- **Part 14.3 (Web-Interface):** Regression: `PluginSettings.test.tsx`, `StatusDetailDrawer.test.tsx`.

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
