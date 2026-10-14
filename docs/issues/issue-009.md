### Issue #9 — System Implementation Add Maintenance Windows That Create Nagios Scheduled Downtime and a Management Page

**Category:** System

**Work Type:** Implementation

**Priority:** High

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Scheduled Operations

**Dependencies:** [Issue #19](issue-019.md)

**Plan reference:** Issue #9 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 9.1 (System) — System Implementation Add Maintenance Windows That Create Nagios Scheduled Downtime**

PinPoint's "Maintenance Mode" only pauses PinPoint's own background jobs (`server/app/automation.py`). It does not create Nagios downtime, so planned work still raises alerts and notifications. PinPoint can display downtime (`Scheduled_Downtime_Depth`) but cannot create it, and pausing a device (`POST /api/system/hosts/<id>/pause`) removes it from Nagios entirely, which is a different action.

**Part 9.2 (Web-Interface) — Web-Interface Implementation Add Maintenance Windows Page**

Administrators have no way to schedule planned maintenance. The only related control is the System "Maintenance Mode" toggle, which does not silence alerts.

**Out of scope for this issue:**

- Changing what Maintenance Mode does for PinPoint's own jobs.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 9.1: `server/app/automation.py` and `SystemSettings.Maintenance_Mode`: pauses scans, update checks and security checks; backups continue.
- Part 9.1: `server/app/history_models.py`: `Scheduled_Downtime_Depth` on host and service snapshots. `RecentOutageTable.tsx`, `ServiceOverview.tsx` and `HostTable.tsx` already display downtime.
- Part 9.1: `server/app/scheduler.py`: APScheduler jobs, the place for a window dispatcher.
- Part 9.1: `server/app/api/system/device_identity.py`: pause and resume routes show the established pattern for device actions with config apply.
- Part 9.1: The command channel that issues Nagios commands is specified in Issue #19 (not built).
- Part 9.2: `client/src/components/layout/MaintenanceBanner.tsx` and the Maintenance Mode toggle in `SystemSettings.tsx` reflect PinPoint's own mode.
- Part 9.2: Downtime is displayed in `ServiceOverview.tsx`, `RecentOutageTable.tsx` and `HostTable.tsx`.
- Part 9.2: Navigation and permission files: `Sidebar.tsx`, `App.tsx`, `client/src/lib/pageAccess.ts`, `client/src/test/PageAccess.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 9.1 (System):** Add a `MaintenanceWindow` model *(proposed, `server/app/system_models.py`)*: scope (a device, or all devices), start, end, recurrence (none, daily, weekly), comment, `Created_By`, status, and the last occurrence sent. Migration included.
2. **Part 9.1 (System):** Add a dispatcher job in `scheduler.py` that, for each active window, sends the Nagios downtime commands through the command module of Issue #19 (host and service downtime for the scope) shortly before each occurrence, with a fixed start and end so Nagios ends the downtime itself. Record the occurrence sent so a restart or overlapping poll never schedules it twice.
3. **Part 9.1 (System):** Add routes *(proposed, `server/app/api/system/maintenance.py`)*: list, create, update and cancel a window, with validation (end after start, recurrence limits, device exists and is monitored) and a new seeded permission *(proposed, for example `maintenance.manage`)*. Cancelling removes downtime already scheduled for the occurrence. Verify the exact Nagios 4.5.11 cancellation command on a lab appliance before implementing.
4. **Part 9.1 (System):** Handle failure: if Nagios does not accept the command, mark the occurrence failed, retry a bounded number of times and show the failure to administrators.
5. **Part 9.1 (System):** Add audit entries for create, update, cancel and each dispatch.

**Frontend / Web Interface**

1. **Part 9.2 (Web-Interface):** Add a Maintenance page *(proposed `client/src/pages/MaintenancePage.tsx`, components in `client/src/components/maintenance/`)* listing windows (scope, next occurrence, recurrence, status) with create, edit and cancel.
2. **Part 9.2 (Web-Interface):** The form chooses the scope (a device from the existing device list, or all), start and end in the user's display time zone (`useDisplayTime`), and recurrence, with validation matching the server.
3. **Part 9.2 (Web-Interface):** Clarify wording: label the System toggle as pausing PinPoint's background jobs, and the new page as silencing alerts, with a link between them.
4. **Part 9.2 (Web-Interface):** Add API client and types *(proposed `client/src/lib/maintenanceApi.ts`, `client/src/types/maintenance.ts`)*. Show failed occurrences clearly.
5. **Part 9.2 (Web-Interface):** Add the route, sidebar entry and page permission together.

#### D. Implementation Guidelines

- Time zones: store UTC, show local, and use the Nagios server's clock for scheduling. Test a daylight-saving change.

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

- [ ] **Part 9.1 (System):** A one-off window creates Nagios downtime before it starts, `Scheduled_Downtime_Depth` becomes non-zero for the scope, notifications for it stop, and the downtime ends at the window end.
- [ ] **Part 9.1 (System):** A recurring window creates the next occurrence once, even after a PinPoint restart.
- [ ] **Part 9.1 (System):** Cancelling a window removes pending and active downtime for it.
- [ ] **Part 9.1 (System):** A Nagios failure is retried a bounded number of times, then shown as failed.
- [ ] **Part 9.1 (System):** Invalid windows are rejected with 400, and users without the permission get 403.
- [ ] **Part 9.1 (System):** PinPoint's own Maintenance Mode behaves exactly as before.
- [ ] **Part 9.2 (Web-Interface):** A permitted user can create, edit and cancel a window and see its status and next occurrence.
- [ ] **Part 9.2 (Web-Interface):** Times are entered and shown in the user's display time zone and stored correctly.
- [ ] **Part 9.2 (Web-Interface):** A failed occurrence is visible with its reason.
- [ ] **Part 9.2 (Web-Interface):** The two maintenance concepts are labelled so they cannot be confused.
- [ ] **Part 9.2 (Web-Interface):** Navigation and page-access tests pass after being updated for the new page.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Page help text and admin guide section.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 9.1 (System):** Unit: recurrence expansion, de-duplication across restarts, daylight-saving edges, failure retry.
- **Part 9.1 (System):** API: permission, 400 and cancel paths with the command module mocked.
- **Part 9.1 (System):** Migration up and down; `flask sync-permissions`.
- **Part 9.1 (System):** Lab (record in `docs/test-runs/`): create a window, observe downtime in the next poll, observe suppressed notification, cancel another window.
- **Part 9.1 (System):** Regression: `test_automation.py`, `test_scheduler.py`.
- **Part 9.2 (Web-Interface):** Frontend: form validation, time zone handling, create, cancel, failed state, permission guard.
- **Part 9.2 (Web-Interface):** Update `PageAccess.test.tsx` and `App.test.tsx`.

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
