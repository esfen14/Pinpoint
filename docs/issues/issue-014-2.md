### Issue #14.2 — System Refinement Add SNMP Version Choice and v3 Credential Support

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** SNMP Monitoring

**Dependencies:** [Issue #14.1](issue-014-1.md); [Issue #16.4](issue-016-4.md)

**Plan reference:** Issue #14 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #14. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

SNMP monitoring works for community-based devices only. SNMP v3 (user, authentication, privacy) is not defined, and the community string is a global default with an optional per-device override. Nagios Core monitors v1, v2c and v3.

**Out of scope for this issue:**

- The per-device form (Issue #14.3).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/network_discovery/plugin_registry.py`: the `snmp` definition uses `check_snmp` with arguments `-p port`, `-C community`, `-o oid` and options `-P` (protocol), `-w`, `-c`, `-l`, `-u`; defaults `port 161`, `community public`; `config_defaults` from `SNMP_PORT`, `SNMP_COMMUNITY_STRING`, `SNMP_OIDS`.
- `server/config.py`: `SNMP_COMMUNITY_STRING` (environment override), `SNMP_OIDS`.
- `server/app/network_discovery/plugin_settings.py` and `server/app/api/system/plugin_settings.py`: OID table saved per plugin. `NetworkDiscovery.Plugin_Variables` overrides per device when generating config, but nothing in the API or UI writes it today (Issue #14.1).
- `server/app/secrets_store.py`: Fernet encryption used for custom-check passwords (`PINPOINT_SECRETS_KEY` or `SECRET_KEY`). `Implementation_Status.md` records that passwords are written to `hosts.cfg` in plain text because Nagios needs them in the command.
- On a lab appliance `hosts.cfg` is mode 0664 (readable by every local user), which makes command-line secrets world-readable (see Issue #16.4).

#### C. Required Changes

**Backend / System**

1. Add an SNMP version (1, 2c, 3) to the `snmp` definition and the per-device variables, defaulting to the current behavior. For v3 add security level (`noAuthNoPriv`, `authNoPriv`, `authPriv`), user, authentication protocol and password, and privacy protocol and password, mapped to `check_snmp` options (`-P 3 -L -U -a -A -x -X`).
2. Store v3 passwords encrypted with `secrets_store.py`, never return them from any API, and write them into the Nagios command through resource macros (`$USERn$` in `resource.cfg`) using the writer from Issue #16.4, so they are not in `hosts.cfg` or process listings.
3. Validate every field against the registry's forbidden-character rules and fixed enumerations, and reject a v3 device without the fields its level needs.
4. Keep v1 and v2c devices rendering exactly as today.
5. Use the per-device plugin variables API from Issue #14.1 to save version and credentials, extend the `plugin-settings` validation for the new fields, and add a test-query endpoint or reuse the plugin run check so an administrator can confirm credentials.

#### D. Implementation Guidelines

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

- [ ] A v2c device renders the same command as before.
- [ ] A v3 authPriv device renders a valid `check_snmp` command whose passwords are macros, not literals, and Nagios validates the config.
- [ ] A v3 device missing a required field is rejected with 400 naming the field.
- [ ] No v3 password appears in `hosts.cfg`, any API response, any log line or a stored snapshot.
- [ ] A lab device with `snmpd` v3 is monitored successfully.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #14.3.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: command rendering per version and level, validation matrix, forbidden characters, macro substitution.
- Security: grep generated config, logs and API responses for the password in tests.
- Lab (record in `docs/test-runs/`): `snmpd` configured for v3 authPriv.
- Regression: `test_plugin_registry.py`, `test_plugin_settings.py`, `test_create_host_cfg.py`.

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
