### Issue #23 — Web-Interface Implementation Add Per-Service Recover Automatically Toggle With Restart Limit

**Category:** Web-Interface

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Service Recovery; Event Handlers

**Dependencies:** [Issue #7](issue-007.md), [Issue #8](issue-008.md)

**Plan reference:** Issue #23 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Waits for the framework (Issue #7) and at least the local restart action (Part 8.1). Remote services also wait for Part 8.3, which is blocked by investigation. The security review of Issue #7 applies here too, because this issue is how an operator turns automatic action on.

#### A. Problem Description

**Part 23.1 (System) — System Implementation Add a Service-Scoped Recovery Setting API**

The feature-gap plan lists a "per-service 'recover automatically' toggle with the restart limit" as the frontend change for Issue #8, but Issue #8 has no frontend part and Issue #7's screen is a general action list. An operator looking at a failing service has no way to say "recover this one automatically, at most twice an hour" without going to a separate screen and building a scoped action by hand.

**Part 23.2 (Web-Interface) — Web-Interface Implementation Add the Recover Automatically Control to Services**

The control belongs where operators already manage a service's monitoring.

**Out of scope for this issue:**

- Defining new action types (Issues #7 and #8).
- Bulk enabling recovery for many services at once.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 23.1: `server/app/api/system/network_services.py` serves service data and `server/app/api/system/network_hosts.py` serves hosts. The remediation routes and models are proposed in Issue #7.
- Part 23.1: Device state (trusted, paused, retired) is defined by `DeviceState` in `server/app/system_models.py`; Issue #8 Part 8.3 must refuse non-trusted devices and this issue must show why.
- Part 23.2: `client/src/components/device-inventory/DeviceMonitoringSection.tsx`, `SetServiceDialog.tsx` and `monitoringState.ts` handle per-service monitoring on the Device Inventory page, specified in `spec files/Device_Inventory_Requirements.md` (required reading). `client/src/components/system-status/ServiceStatusTable.tsx` lists service status.
- Part 23.2: Page access is defined in `client/src/lib/pageAccess.ts`, `client/src/App.tsx` and `client/src/test/PageAccess.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 23.1 (System):** Add `GET` and `PUT` for one service's recovery setting *(proposed under `server/app/api/system/remediation.py`, for example `/api/system/remediation/services/<service id>`)*. A `PUT` creates, updates or disables exactly one `RemediationAction` scoped to that service, so the Issue #7 consumer needs no new code path.
2. **Part 23.1 (System):** The request carries only: enabled, and `max_restarts_per_hour` (bounded, for example 1 to 6). The server chooses the action type from what is valid for that service (local unit allowlist, or the per-device remote allowlist from Part 8.3). Never accept a unit name, command or script from the request.
3. **Part 23.1 (System):** Return which action type applies, or the reason none does (no allowlist entry, device not trusted, paused or retired, framework not installed). Use `Version` for stale-write detection (409).
4. **Part 23.1 (System):** Require the Issue #7 permission, apply through `regenerate_and_apply_config_status()` and roll back with 422 if Nagios rejects the config.

**Frontend / Web Interface**

1. **Part 23.2 (Web-Interface):** Add a "Recover automatically" switch and a restarts-per-hour field to the service controls on Device Inventory, and a read-only state with a link on the System Status service row.
2. **Part 23.2 (Web-Interface):** Disable the switch with the server's reason when no valid action exists, and warn that enabling it makes the system restart the service on its own.
3. **Part 23.2 (Web-Interface):** Show the last recovery result and a link to the run. Show loading, error, 403 and 409 (reload) states.
4. **Part 23.2 (Web-Interface):** Hide the control from users without the permission. The server check is the real guard.

#### D. Implementation Guidelines

- The toggle must map to the same `RemediationAction` rows as the Remediation screen. Do not create a second storage model; a change made in either place must show in the other.
- Resolve the service by identifier, never by a name taken from the request, and confirm it belongs to a known, monitorable device.
- Disabling must take effect through config regeneration, not only a database flag, so Nagios stops calling the handler for that service.

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

#### E. Acceptance Criteria

- [ ] **Part 23.1 (System):** Enabling recovery for a service creates one scoped action and the generated config adds the handler to that service only; disabling removes it.
- [ ] **Part 23.1 (System):** A request containing a unit name, command or path is rejected with 400.
- [ ] **Part 23.1 (System):** A restart limit outside bounds is rejected with 400; a stale `Version` returns 409; a rejected Nagios config rolls back and returns 422.
- [ ] **Part 23.1 (System):** A paused, retired or untrusted device returns a clear reason and cannot be enabled.
- [ ] **Part 23.1 (System):** Without the permission the route returns 403.
- [ ] **Part 23.2 (Web-Interface):** The switch and limit save and reload, and match what the Remediation screen shows for the same action.
- [ ] **Part 23.2 (Web-Interface):** A service with no valid action shows a disabled switch and the reason.
- [ ] **Part 23.2 (Web-Interface):** Users without the permission cannot see or use the control.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the control; one paragraph in the admin guide.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request.

#### G. Testing and Verification

- **Part 23.1 (System):** Unit: action-type selection per service, bounds, hostile input, device-state refusal, version conflict.
- **Part 23.1 (System):** API: 400, 403, 409, 422.
- **Part 23.2 (Web-Interface):** Frontend: switch and limit validation, disabled reasons, permission hiding, agreement with the Remediation screen.
- Regression: Device Inventory tests, `test_create_host_cfg.py`, page access tests.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

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
