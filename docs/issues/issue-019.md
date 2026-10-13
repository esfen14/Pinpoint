### Issue #19 — System Implementation Add Nagios Command Channel, Acknowledgement Propagation and Check Now

**Category:** System

**Work Type:** Implementation

**Priority:** High

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** External Commands; Contact Notifications; External Commands

**Dependencies:** None

**Plan reference:** Issue #19 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 19.1 (System) — System Implementation Add Nagios Command Channel and Propagate Acknowledgements to Nagios**

A PinPoint acknowledgement is stored only in `system.db`. Nagios is never told, so it keeps sending notifications for a problem an operator has already acknowledged, and its own acknowledgement flag stays unset. More generally PinPoint cannot send any command to Nagios (downtime, forced check, notification control), so Nagios Core's external command capability is unused.

**Part 19.2 (System) — System Implementation Add Check Now Routes Through the Nagios Command Channel**

Operators cannot ask Nagios to re-check a host or service. After fixing a problem they must wait for the next scheduled check (up to the Check interval) before the dashboard changes.

**Part 19.3 (Web-Interface) — Web-Interface Refinement Add Check Now Button and Nagios Acknowledgement Status Indicator**

Operators cannot request a re-check, and the interface cannot tell them whether an acknowledgement reached Nagios (and so whether notifications really stopped).

**Out of scope for this issue:**

- Maintenance windows (Issue #9).
- Changing what PinPoint stores for acknowledgements.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 19.1: `server/app/api/system/dashboard.py`: `acknowledge_alert()`, `acknowledge_all_alerts()`, `unacknowledge_alert()` write `AlertAcknowledgement` and `AckHistory` (`server/app/system_models.py`) and create audit entries. No Nagios call exists anywhere (searched for `cmd.cgi`, `nagios.cmd`, `ACKNOWLEDGE_`).
- Part 19.1: `server/app/api/system/network_hosts.py` and `network_services.py` contain the host and service acknowledge and unacknowledge routes.
- Part 19.1: Verified on a lab appliance: `check_external_commands=1`, `command_file=/usr/local/nagios/var/rw/nagios.cmd` is a pipe `prw-rw---- nagios:nagios`, and the `pinpoint` service user is in group `nagios`, so it can write the pipe. `cgi.cfg` authorizes commands only for `nagiosadmin`, which has no password entry, so the CGI route is not usable.
- Part 19.1: `server/config.py` holds Nagios paths with environment overrides (`NAGIOS_MAIN_CFG`, `NAGIOS_BIN`, `NAGIOS_PLUGIN_DIR`); a command-file path belongs here.
- Part 19.1: `server/app/api/system/statistics.py` → `get_latest_hosts()` and `get_latest_services()` give the set of known hosts and services.
- Part 19.1: Tests: `server/tests/unit/test_dashboard.py`, `test_network_hosts.py`, `test_network_services.py`.
- Part 19.2: No re-check capability exists. The command channel is specified in Part 19.1.
- Part 19.2: `server/app/api/system/network_hosts.py` and `network_services.py` hold the host and service routes and their permission checks.
- Part 19.2: Rate-limit precedent: `POST /api/system/deployment/ncpa/check-credentials` limits one check per device per 3 seconds (`server/app/api/system/ncpa_deployment.py`).
- Part 19.2: Permissions are seeded in `server/app/api/commands/seed.py` and granted with `flask sync-permissions`.
- Part 19.3: `client/src/components/dashboard/AlertCard.tsx`, `components/shared/AlertsSidebar.tsx` and `RecentOutageTable.tsx` show alerts and the acknowledge action.
- Part 19.3: `client/src/components/device-inventory/StatusDetailDrawer.tsx` and `components/system-status/ServiceStatusTable.tsx` show host and service details and acknowledgement actions.
- Part 19.3: `client/src/types/dashboard.ts`, `types/host.ts`, `types/service.ts` hold the wire types.
- Part 19.3: Tests: `DashboardPage.test.tsx`, `StatusDetailDrawer.test.tsx`, `ServiceOverview.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 19.1 (System):** Add `NAGIOS_COMMAND_FILE` to `server/config.py` (default `/usr/local/nagios/var/rw/nagios.cmd`, environment override, documented in the environment drift check).
2. **Part 19.1 (System):** Add `server/app/nagios/commands.py` *(proposed)* with one function per allowed command (acknowledge host or service problem, remove acknowledgement, and the downtime and forced-check commands for Issue #9 and #19.2). Each builds `[epoch] COMMAND;args` from validated parts, opens the pipe non-blocking with a short timeout so a stopped Nagios cannot hang the web request, writes one line, and returns success or a typed error.
3. **Part 19.1 (System):** Reject any host name, service description or comment containing a newline, carriage return or NUL. Check host and service names against the latest snapshot before sending. Escape or reject the field separator in names.
4. **Part 19.1 (System):** Call the module from the acknowledge and unacknowledge routes after the local record is saved. A Nagios failure must not undo or block the local acknowledgement: return the existing response plus `nagios_synced` and a short message, and write an audit entry when the sync fails.
5. **Part 19.1 (System):** Choose and document the acknowledgement type sent (normal or sticky), matching `AcknowledgementType` in `history_models.py` and the requirements in `Display_Requirements.md` §4.
6. **Part 19.1 (System):** Log each command name and target (never the comment body beyond a length limit) at INFO.
7. **Part 19.2 (System):** Add `POST /api/system/network-health/hosts/<hostname>/recheck` and `POST /api/system/network-health/services/<hostname>/<path:service_name>/recheck` *(proposed)*, using `<path:service_name>` because service names can contain `/`.
8. **Part 19.2 (System):** Send a forced check through the Part 19.1 module. Rate-limit per target (for example one request per 10 seconds, 429 beyond it) and refuse targets not in the latest snapshot, paused, retired or merged devices.
9. **Part 19.2 (System):** Add a seeded permission *(proposed `system.recheck`)* and require it with login. Write an audit entry.

**Frontend / Web Interface**

1. **Part 19.3 (Web-Interface):** Add a "Check now" button to the host and service detail views (shown only with `system.recheck`), with a cooldown state and the server's 429 message.
2. **Part 19.3 (Web-Interface):** When an acknowledgement response says `nagios_synced: false`, show a visible notice that the acknowledgement was saved in PinPoint but Nagios was not updated, so notifications may continue.
3. **Part 19.3 (Web-Interface):** Update the types for the new response field.

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

- [ ] **Part 19.1 (System):** Acknowledging a service in PinPoint writes the Nagios acknowledgement command, and on a lab appliance Nagios stops repeat notifications and shows the problem as acknowledged in the next poll (`Acknowledgement_Type` changes).
- [ ] **Part 19.1 (System):** Unacknowledging removes the Nagios acknowledgement.
- [ ] **Part 19.1 (System):** A comment with a newline or NUL is rejected with 400 and nothing is written to the pipe.
- [ ] **Part 19.1 (System):** With Nagios stopped or the pipe missing, the local acknowledgement still succeeds, the response says `nagios_synced: false`, and the request does not hang.
- [ ] **Part 19.1 (System):** A host or service name not in the latest snapshot is refused.
- [ ] **Part 19.1 (System):** Existing acknowledgement history and the acknowledgement tests behave as before.
- [ ] **Part 19.2 (System):** A permitted user can trigger a forced check and the next poll shows the new result sooner than the scheduled interval.
- [ ] **Part 19.2 (System):** A second request inside the rate limit returns 429.
- [ ] **Part 19.2 (System):** Unknown, paused, retired and merged targets are refused.
- [ ] **Part 19.2 (System):** Without the permission the routes return 403.
- [ ] **Part 19.3 (Web-Interface):** A permitted user can trigger a re-check from the host and service views and sees a clear cooldown message when rate limited.
- [ ] **Part 19.3 (Web-Interface):** A failed Nagios sync after acknowledging shows a notice, and a successful sync shows none.
- [ ] **Part 19.3 (Web-Interface):** Users without the permission do not see the button.
- [ ] **Part 19.3 (Web-Interface):** Existing dashboard and drawer tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Alerts_Notifications_History_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 19.1 (System):** Unit: command formatting for every command, injection attempts (newline, semicolon, NUL, very long comment), name validation, timeout and missing-pipe handling using a temporary FIFO.
- **Part 19.1 (System):** API: acknowledge, acknowledge-all and unacknowledge routes with the module mocked (success and failure), unchanged local behavior.
- **Part 19.1 (System):** Lab (record in `docs/test-runs/`): acknowledge a failing service, confirm no further notification and the acknowledgement flag after the next poll.
- **Part 19.1 (System):** Regression: `test_dashboard.py`, `test_network_hosts.py`, `test_network_services.py`.
- **Part 19.2 (System):** Unit and API: permission, rate limit, refused targets, command sent (module mocked).
- **Part 19.2 (System):** Migration of permissions: `flask sync-permissions` adds `system.recheck` (see `test_seed.py`).
- **Part 19.2 (System):** Lab: force a check and observe the result.
- **Part 19.3 (Web-Interface):** Frontend: button visibility, cooldown, sync-failure notice.
- **Part 19.3 (Web-Interface):** Regression: the dashboard and drawer tests listed above.

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
