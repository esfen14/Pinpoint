### Issue #7 — System Implementation Add Allowlisted Event Handler Framework With Remediation Screen and Installer Support

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** High

**Related Nagios Core Feature:** Event Handlers; Proactive Resolution; Event Handlers

**Dependencies:** None

**Plan reference:** Issue #7 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 7.1 (System):** Needs a security review of the design before coding, because it makes Nagios trigger actions. The execution model below (Nagios only records an event, PinPoint decides and runs an allowlisted action) is a proposal that must be confirmed on a lab appliance: spool directory permissions and who can read the spool were not verified.  
> **Part 7.2 (Web-Interface):** Same condition as Part 7.1.  
> **Part 7.3 (Installer):** Design to be confirmed with the security review of Part 7.1. Where the executable should live and its permissions on an installed appliance were not verified: the application directory is owned by another user and the `nagios` user may not be able to traverse it.

#### A. Problem Description

**Part 7.1 (System) — System Implementation Add Allowlisted Event Handler Framework with Remediation Audit Log**

PinPoint observes failures but never reacts. No generated Nagios object defines an `event_handler`, although event handlers are enabled globally on appliances (`enable_event_handlers=1`, verified). The preliminary document's claim that event-handler attempts are "mostly in the system" is not supported by the repository.

Without a framework, administrators cannot define a safe action to run when a service reaches a hard failure state, and there is no audit trail of automated actions.

**Part 7.2 (Web-Interface) — Web-Interface Implementation Add Remediation Actions Screen and Run Log**

Administrators need a safe place to define what runs when a service fails and to review every automated action. No such screen or log view exists.

**Part 7.3 (Installer) — Installer Implementation Install Event Handler Spool Directory and Handler Executable**

Nagios must be able to run a small executable and write a spool file that the PinPoint service can read. Neither exists on an installed appliance today.

**Out of scope for this issue:**

- Specific recovery actions such as restarting a service (Issue #8).
- Running arbitrary commands, scripts or uploaded code. This framework only runs actions chosen from a fixed list.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 7.1: Nagios stores `Current_Attempt`, `Max_Attempts`, `Last_State_Change` per host and service (`server/app/history_models.py`) and PinPoint displays them, but nothing acts on them.
- Part 7.1: `server/app/network_discovery/create_host_cfg.py` and `host_config_templates.py` generate hosts, services and commands; `plugin_registry.py` shows how a command definition is rendered with forbidden-character checks (`FORBIDDEN_VALUE_CHARACTERS`).
- Part 7.1: `server/app/scheduler.py` registers APScheduler jobs (`max_instances=1`, `coalesce=True`) and is the place for a consumer job.
- Part 7.1: Audit logging: `server/app/logging/` and `ActivityLog`; the Logs page reads them through `server/app/api/system/log.py`.
- Part 7.1: The `/usr/local/nagios/var/spool` directory exists on a lab appliance. Whether the `pinpoint` user can read a new subdirectory there, and where an executable for Nagios should live, are *further investigation required* (see Part 7.3).
- Part 7.2: `client/src/pages/SystemLogsPage.tsx` shows five audit categories from `api/system/log.py`.
- Part 7.2: `client/src/pages/PluginsPage.tsx` and `components/plugin-manager/` show how per-plugin administrative actions and drawers are built.
- Part 7.2: `client/src/lib/pageAccess.ts`, `components/layout/Sidebar.tsx`, `client/src/App.tsx` and `client/src/test/PageAccess.test.tsx` define navigation and permissions and must be updated together when a page is added.
- Part 7.3: On a lab appliance: `/usr/local/nagios/var/spool` exists, `pinpoint` is in group `nagios` (`id pinpoint`), and `/usr/local/nagios/etc` is group-writable. `sudoers` for `pinpoint` allows only the SMTP helper and `systemctl reload nagios`.
- Part 7.3: The application code is under `/opt/pinpoint/Network-Diagnosis-System`, and git reports "dubious ownership" for a non-owner, so directory ownership differs between users.
- Part 7.3: The installer code is not in this repository, so its file locations are *further investigation required*.

#### C. Required Changes

**Backend / System**

1. **Part 7.1 (System):** Add models *(proposed, `server/app/system_models.py`)*: `RemediationAction` (name, action type from a fixed enum, scope host or service pattern, parameters JSON validated per type, enabled flag, max runs per hour, cooldown seconds, `Version`, `Updated_By`) and `RemediationRun` (action, host, service, state, state type, attempt, started and finished time, outcome, exit code, truncated redacted output). Migration included.
2. **Part 7.1 (System):** Define one Nagios command `pinpoint_event_handler` *(proposed template)* with arguments `$SERVICESTATE$ $SERVICESTATETYPE$ $SERVICEATTEMPT$ $HOSTNAME$ $SERVICEDESC$` (and the host equivalent) that calls a small Pinpoint-owned executable. The executable only appends one validated JSON line to a spool directory and exits; it never runs an action itself.
3. **Part 7.1 (System):** Add a consumer *(proposed, `server/app/remediation.py`)* run by a short APScheduler job in `scheduler.py` that reads spool lines, ignores anything that is not a HARD state, matches enabled actions, enforces cooldown and the hourly cap, runs the action type's fixed implementation as the `pinpoint` user, and writes a `RemediationRun` row for every decision, including skipped ones.
4. **Part 7.1 (System):** Render `event_handler pinpoint_event_handler` and `event_handler_enabled 1` only on services and hosts covered by at least one enabled action, through `create_service()` and `create_host()`. Services with no matching action are rendered exactly as today.
5. **Part 7.1 (System):** Add routes *(proposed, `server/app/api/system/remediation.py`)* to list, create, update, enable and disable actions and to page through runs, with route docstrings, a new seeded permission *(proposed, for example `remediation.manage`)* in `seed.py`, validation of every parameter, and apply through `regenerate_and_apply_config_status()`.
6. **Part 7.1 (System):** Log each run to the activity log summary without secrets. Cap stored output length.

**Frontend / Web Interface**

1. **Part 7.2 (Web-Interface):** Add a "Remediation" area *(proposed page `client/src/pages/RemediationPage.tsx` with components in `client/src/components/remediation/`)* with an action list, an add and edit form generated from each action type's parameters, an enable switch, and the cooldown and hourly cap fields.
2. **Part 7.2 (Web-Interface):** Add a run log table with filters (action, host, outcome, date), pagination and a detail drawer, showing skipped runs with their reason.
3. **Part 7.2 (Web-Interface):** Add API client and types *(proposed `client/src/lib/remediationApi.ts`, `client/src/types/remediation.ts`)*.
4. **Part 7.2 (Web-Interface):** Add the route, sidebar entry and page permission together, and make the form show a clear warning that actions run automatically.
5. **Part 7.2 (Web-Interface):** Show loading, empty, error and 403 states, and the server's validation messages.

**Installer / Deployment**

1. **Part 7.3 (Installer):** Create a spool directory *(proposed, for example `/usr/local/nagios/var/spool/pinpoint-events`)* owned by `nagios:nagios` with mode 2770 so the `pinpoint` user can read and delete entries and nobody else can.
2. **Part 7.3 (Installer):** Install the handler executable *(proposed)* to a root-owned path both users can execute (for example under `/usr/local/nagios/libexec`), mode 0755, not writable by the web user, with no dependency on the application directory.
3. **Part 7.3 (Installer):** Add upgrade handling so existing appliances get the directory and the executable without losing configuration.
4. **Part 7.3 (Installer):** Do not change `sudoers` unless Issue #8 requires it.

#### D. Implementation Guidelines

- No action type may take a command line or script path from a request. Each action type is code that takes validated, typed parameters.
- Never run anything as the `nagios` user beyond the spool writer. Remediation runs as the `pinpoint` user under its existing privileges (`sudoers` allows only the SMTP helper and `systemctl reload nagios` today).
- Prevent restart loops with the cooldown and hourly cap, and record when a cap stops an action.
- Handle duplicate spool lines and a restart of the consumer without running an action twice.

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

- [ ] **Part 7.1 (System):** With no actions defined, generated config contains no `event_handler` and is unchanged.
- [ ] **Part 7.1 (System):** Enabling an action for a service adds the handler to that service only, and Nagios validates the config.
- [ ] **Part 7.1 (System):** A hard CRITICAL for a covered service produces exactly one `RemediationRun` and at most one execution; a soft state produces none.
- [ ] **Part 7.1 (System):** The cooldown and hourly cap stop repeated runs and the skip is recorded with its reason.
- [ ] **Part 7.1 (System):** A malformed or oversized spool line is discarded and logged without crashing the consumer.
- [ ] **Part 7.1 (System):** Creating an action needs the new permission (403 otherwise) and rejects invalid parameters with 400.
- [ ] **Part 7.1 (System):** No secret or credential appears in a run record, a log line or a response.
- [ ] **Part 7.2 (Web-Interface):** A permitted user can create, edit, enable and disable an action and sees changes after reload.
- [ ] **Part 7.2 (Web-Interface):** The run log lists runs with filters and pagination, including skipped ones.
- [ ] **Part 7.2 (Web-Interface):** Users without the permission do not see the page in navigation and are blocked on direct access.
- [ ] **Part 7.2 (Web-Interface):** Validation errors from the server are shown against the right field.
- [ ] **Part 7.2 (Web-Interface):** Existing navigation and page-access tests pass after being updated for the new page.
- [ ] **Part 7.3 (Installer):** On a fresh install and on an upgraded appliance the spool directory exists with the stated owner and mode.
- [ ] **Part 7.3 (Installer):** The `nagios` user can run the executable and append to the spool, and the `pinpoint` user can read and remove entries.
- [ ] **Part 7.3 (Installer):** The web user cannot modify the executable.
- [ ] **Part 7.3 (Installer):** The upgrade does not alter other Nagios configuration or the SMTP helper.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Engineering_Standards.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Agent_Workflow_and_CI.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Page help text and a short admin guide section; Installer release notes.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 7.1 (System):** Unit: spool parsing (valid, malformed, oversized, duplicate), cooldown and cap logic, state filtering, parameter validation per action type.
- **Part 7.1 (System):** Unit: template output with and without actions.
- **Part 7.1 (System):** API: permission, 400, 409 (stale version) and apply-failure paths.
- **Part 7.1 (System):** Migration up and down; `flask sync-permissions` adds the permission.
- **Part 7.1 (System):** Security: attempts to inject shell characters through every parameter and through the spool line are rejected.
- **Part 7.1 (System):** Lab (record in `docs/test-runs/`): harmless test action on a lab service forced to a hard failure and recovery.
- **Part 7.2 (Web-Interface):** Frontend: form generation per type, validation, enable toggle, log filters, permission guard.
- **Part 7.2 (Web-Interface):** Update `PageAccess.test.tsx` and `App.test.tsx` for the new route.
- **Part 7.3 (Installer):** Installer-side script test for ownership and modes.
- **Part 7.3 (Installer):** VM-lab (`scripts/vmlab`, record under `docs/test-runs/`): install, then run the executable as `nagios` and read the spool as `pinpoint`.
- **Part 7.3 (Installer):** Upgrade test from the previous installer version.

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
