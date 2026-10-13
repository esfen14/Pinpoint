### Issue #4.2 — Web-Interface Refinement Add Parent Device Selector to Device Inventory

**Category:** Web-Interface

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Network Host Hierarchy

**Dependencies:** [Issue #4.1](issue-004-1.md)

**Plan reference:** Issue #4 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #4. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Same condition as Issue #4.1.

#### A. Problem Description

Operators cannot say which device sits behind which. Once the backend stores parents, the Device Inventory drawer needs a way to set one and a hint when the choice is risky.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `client/src/pages/DeviceInventoryPage.tsx`, `components/device-inventory/StatusDetailDrawer.tsx`, `HostTable.tsx`, `DeviceMonitoringSection.tsx`, `DevicePortsSection.tsx`.
- `client/src/lib/deviceMonitoringApi.ts` already calls the device pause and resume routes and is the pattern for a device edit call.
- Tests: `client/src/test/StatusDetailDrawer.test.tsx`, `DeviceMonitoringState.test.tsx`, `DeviceInventoryPage.test.tsx`.

#### C. Required Changes

**Frontend / Web Interface**

1. Add a "Parent device" field to the drawer *(a new section component, proposed `DeviceParentSection.tsx` in `components/device-inventory/`)* with a searchable list of other monitored devices, a "None" choice and the suggested gateway.
2. Show a warning when the chosen parent is not monitored, and the server's 400 message for cycles or invalid parents.
3. Show the parent in the drawer and an optional column or tooltip in `HostTable.tsx`.
4. Respect `system.hosts.edit`: read-only without it.

#### D. Implementation Guidelines


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

- [ ] A user with `system.hosts.edit` can set, change and clear a parent, and it persists after reload.
- [ ] Cycle and invalid choices show the server message.
- [ ] A user without the permission sees the parent but cannot change it.
- [ ] Existing drawer and table tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, `spec files/Device_Inventory_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Drawer help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh frontend` output attached to the pull request.

#### G. Testing and Verification

- Frontend: set, clear, error and read-only states.
- Regression: Device Inventory tests listed above.

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
