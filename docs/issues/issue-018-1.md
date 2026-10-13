### Issue #18.1 — System Refinement Add POP3, IMAP and Expected-Response Options to Mail and Web Service Checks

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Mail Servers; API Monitoring; Application Servers; Directory Services; Database Servers

**Dependencies:** [Issue #14.1](issue-014-1.md)

**Plan reference:** Issue #18 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #18. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

Mail, directory, application and API services are checked only by port or by `check_http` with a URL. POP3 and IMAP get the generic TCP check, which proves a port answers but not that the mail service greets correctly, and web or API checks cannot verify an expected status code or response text. Nagios Core covers these with the standard plugins.

Only plugins already in PinPoint's bundled catalog are in scope. Custom and community plugins are out of scope by team decision, so database engines without a bundled plugin (SQL Server, Oracle, MongoDB) and application servers without one (JBoss, WebLogic, Citrix) stay port-level checks. That limit must be documented rather than left unexplained.

**Out of scope for this issue:**

- Any plugin that is not in the bundled catalog.
- Authentication headers or passwords for web checks (would need Issue #16.4's secret handling first).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/network_discovery/plugin_registry.py`: `PLUGIN_DEFINITIONS` includes `tcp`, `udp`, `snmp`, `ncpa`, `http`, `https`, `ssh`, `ftp`, `smtp`, `mysql`, `pgsql`, `ldap`, `ldaps`, `rpc`, `ircd`, `time`, `ntp_peer`, `dns`, `ntp`. The `http` definition exposes only `url`, `warning` and `critical` options.
- `check_pop` and `check_imap` are **not** in the bundled catalog (`server/app/api/plugin/plugin_catalog_data.py` and `spec files/Plugins_List.md` contain neither). POP3 and IMAP greetings can be verified with the bundled `check_tcp` plugin, which accepts an expected response string.
- `server/config.py`: `TCP_PORT_SERVICES` defaults map only 5666 (`nrpe`), 22, 80 and 443; `UDP_PORT_SERVICES` maps 5666 and 161. NRPE is not used by the team, so the `nrpe` entries are leftovers.
- `NetworkDiscovery.Plugin_Variables` overrides per device, writable through the API of Issue #14.1 once built.
- `server/app/network_discovery/custom_checks.py` marks `check_dbi` and `check_oracle` as unavailable ("credentials") and has no HTTP check fields because `check_http` is port-driven.
- How a definition can carry fixed arguments (such as an expect string) is *further investigation required* in `PluginDefinition`; it currently has `arguments`, `options` and `defaults`.

#### C. Required Changes

**Backend / System**

1. Add `pop3` and `imap` definitions using `check_tcp` with an expect string and port defaults (110 and 143), and TLS variants (995 and 993) using `check_tcp -S`, extending `PluginDefinition` with a fixed-options field if needed. Keep every existing definition's rendered command unchanged.
2. Extend the `http` and `https` definitions with optional variables: expected response text (`-s`), expected status (`-e`), virtual host (`-H`) and method (`-j`), each validated by `validate_variable_value()` and the forbidden-character rule. Defaults must render the same command as today.
3. Add the new service names to the Port to Service defaults in `config.py` only after confirming they do not disturb existing identification (`service_from_nmap()` and the "not used as intended" rule). Decide whether to remove the unused `nrpe` defaults and record the decision.
4. Document in `spec files/Plugins_List.md` or the manual which application types are covered at port level only.

#### D. Implementation Guidelines

- A new service name changes what discovery proposes for a port. Verify with `test_service_identification.py` that existing identification is unaffected.

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

- [ ] A device with port 110 or 143 open can have a protocol-aware check generated and Nagios validates the config.
- [ ] A web check with an expected string and status renders the matching options, and reports CRITICAL on a lab server that returns something else.
- [ ] Existing definitions render byte-identical commands when no new variable is set.
- [ ] Invalid values (forbidden characters, out-of-range status, bad method) are rejected with 400 naming the field.
- [ ] The documentation states clearly which services are port-level only and why.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Plugins_List.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Manual section on supported application checks and their limits.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request.

#### G. Testing and Verification

- Unit: command rendering for each new definition and option, validation, unchanged defaults (`test_plugin_registry.py`).
- Unit: service identification regression (`test_service_identification.py`, `test_create_host_cfg.py`).
- Lab (`lab/` targets, record in `docs/test-runs/`): an IMAP-like and a web target returning OK and wrong responses.

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
