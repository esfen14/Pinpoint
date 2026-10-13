### Issue #19.1 — System Implementation Add Nagios Command Channel and Propagate Acknowledgements to Nagios

**Category:** System

**Work Type:** Implementation

**Priority:** High

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** External Commands; Contact Notifications

**Dependencies:** None

**Plan reference:** Issue #19 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #19. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

A PinPoint acknowledgement is stored only in `system.db`. Nagios is never told, so it keeps sending notifications for a problem an operator has already acknowledged, and its own acknowledgement flag stays unset. More generally PinPoint cannot send any command to Nagios (downtime, forced check, notification control), so Nagios Core's external command capability is unused.

**Out of scope for this issue:**

- Check-now routes (Issue #19.2).
- Maintenance windows (Issue #9.1).
- Changing what PinPoint stores for acknowledgements.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/api/system/dashboard.py`: `acknowledge_alert()`, `acknowledge_all_alerts()`, `unacknowledge_alert()` write `AlertAcknowledgement` and `AckHistory` (`server/app/system_models.py`) and create audit entries. No Nagios call exists anywhere (searched for `cmd.cgi`, `nagios.cmd`, `ACKNOWLEDGE_`).
- `server/app/api/system/network_hosts.py` and `network_services.py` contain the host and service acknowledge and unacknowledge routes.
- Verified on a lab appliance: `check_external_commands=1`, `command_file=/usr/local/nagios/var/rw/nagios.cmd` is a pipe `prw-rw---- nagios:nagios`, and the `pinpoint` service user is in group `nagios`, so it can write the pipe. `cgi.cfg` authorizes commands only for `nagiosadmin`, which has no password entry, so the CGI route is not usable.
- `server/config.py` holds Nagios paths with environment overrides (`NAGIOS_MAIN_CFG`, `NAGIOS_BIN`, `NAGIOS_PLUGIN_DIR`); a command-file path belongs here.
- `server/app/api/system/statistics.py` → `get_latest_hosts()` and `get_latest_services()` give the set of known hosts and services.
- Tests: `server/tests/unit/test_dashboard.py`, `test_network_hosts.py`, `test_network_services.py`.

#### C. Required Changes

**Backend / System**

1. Add `NAGIOS_COMMAND_FILE` to `server/config.py` (default `/usr/local/nagios/var/rw/nagios.cmd`, environment override, documented in the environment drift check).
2. Add `server/app/nagios/commands.py` *(proposed)* with one function per allowed command (acknowledge host or service problem, remove acknowledgement, and the downtime and forced-check commands for Issues #9.1 and #19.2). Each builds `[epoch] COMMAND;args` from validated parts, opens the pipe non-blocking with a short timeout so a stopped Nagios cannot hang the web request, writes one line, and returns success or a typed error.
3. Reject any host name, service description or comment containing a newline, carriage return or NUL. Check host and service names against the latest snapshot before sending. Escape or reject the field separator in names.
4. Call the module from the acknowledge and unacknowledge routes after the local record is saved. A Nagios failure must not undo or block the local acknowledgement: return the existing response plus `nagios_synced` and a short message, and write an audit entry when the sync fails.
5. Choose and document the acknowledgement type sent (normal or sticky), matching `AcknowledgementType` in `history_models.py` and the requirements in `Display_Requirements.md` §4.
6. Log each command name and target (never the comment body beyond a length limit) at INFO.

#### D. Implementation Guidelines

- This gives the web service control of Nagios. Keep the allowlist closed, and review it as an injection-sensitive path (Engineering Standards "Sensitive modules").

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

- [ ] Acknowledging a service in PinPoint writes the Nagios acknowledgement command, and on a lab appliance Nagios stops repeat notifications and shows the problem as acknowledged in the next poll (`Acknowledgement_Type` changes).
- [ ] Unacknowledging removes the Nagios acknowledgement.
- [ ] A comment with a newline or NUL is rejected with 400 and nothing is written to the pipe.
- [ ] With Nagios stopped or the pipe missing, the local acknowledgement still succeeds, the response says `nagios_synced: false`, and the request does not hang.
- [ ] A host or service name not in the latest snapshot is refused.
- [ ] Existing acknowledgement history and the acknowledgement tests behave as before.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Alerts_Notifications_History_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #19.3.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: command formatting for every command, injection attempts (newline, semicolon, NUL, very long comment), name validation, timeout and missing-pipe handling using a temporary FIFO.
- API: acknowledge, acknowledge-all and unacknowledge routes with the module mocked (success and failure), unchanged local behavior.
- Lab (record in `docs/test-runs/`): acknowledge a failing service, confirm no further notification and the acknowledgement flag after the next poll.
- Regression: `test_dashboard.py`, `test_network_hosts.py`, `test_network_services.py`.

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
