### Issue #4 — System Implementation Add Parent Device Relationships and Nagios Parents Rendering With Device Selector

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Network Host Hierarchy

**Dependencies:** None

**Plan reference:** Issue #4 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 4.1 (System):** Needs a scope decision first. `Implementation_Status.md` excludes backend topology computation and the topology view from the current release. Parent links (data and Nagios `parents` only, no map) are a different thing, but the team must confirm that before work starts.  
> **Part 4.2 (Web-Interface):** Same condition as Part 4.1.

#### A. Problem Description

**Part 4.1 (System) — System Implementation Add Parent Device Relationships and Nagios Parents Rendering**

PinPoint-generated hosts have no `parents`, so Nagios treats every host as directly reachable. When a router fails, every host behind it is reported DOWN instead of UNREACHABLE, which produces an alert storm and hides the root cause. UNREACHABLE is only counted in `statistics.py` and cannot arise from the generated config.

**Part 4.2 (Web-Interface) — Web-Interface Refinement Add Parent Device Selector to Device Inventory**

Operators cannot say which device sits behind which. Once the backend stores parents, the Device Inventory drawer needs a way to set one and a hint when the choice is risky.

**Out of scope for this issue:**

- A topology map or any visualization (excluded from the release).
- Automatic parent inference beyond a suggestion.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 4.1: `server/app/network_discovery/templates/host.cfg.tpl` has no `parents` line, and `host_config_templates.create_host()` takes no parent argument.
- Part 4.1: `NetworkDiscovery` in `server/app/system_models.py` is the device record. `server/app/network_discovery/device_identity.py` handles merge, retire and lifecycle; `server/app/api/system/device_identity.py` holds the device routes (`PUT /api/system/hosts/<id>`, merge, retire, pause, resume).
- Part 4.1: `GET /api/system/network-profile` (`server/app/api/system/network_profile.py`) already derives a gateway device, which can serve as the suggested parent.
- Part 4.1: `server/app/api/system/statistics.py` → `host_counts()` counts UP, DOWN and UNREACHABLE.
- Part 4.2: `client/src/pages/DeviceInventoryPage.tsx`, `components/device-inventory/StatusDetailDrawer.tsx`, `HostTable.tsx`, `DeviceMonitoringSection.tsx`, `DevicePortsSection.tsx`.
- Part 4.2: `client/src/lib/deviceMonitoringApi.ts` already calls the device pause and resume routes and is the pattern for a device edit call.
- Part 4.2: Tests: `client/src/test/StatusDetailDrawer.test.tsx`, `DeviceMonitoringState.test.tsx`, `DeviceInventoryPage.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 4.1 (System):** Add a nullable self-referencing `Parent_Device_ID` column on `NetworkDiscovery` and a migration.
2. **Part 4.1 (System):** Validate on write: the parent exists and is not the device itself, is not retired or merged, and the link creates no cycle. Return 400 with a clear message.
3. **Part 4.1 (System):** Extend `PUT /api/system/hosts/<id>` (permission `system.hosts.edit`) to accept `parent_device_id`, and include the parent in the device summary returned by the host routes.
4. **Part 4.1 (System):** Render `parents <host_name>` in `host.cfg.tpl` when the parent is monitored. If the parent is paused, retired, merged or address-unknown, omit `parents` for that host and report it in the response, so a bad parent never hides a real outage or breaks the config.
5. **Part 4.1 (System):** On merge and retire (`device_identity.py`), re-point or clear children of the affected device in the same transaction.
6. **Part 4.1 (System):** Apply through `regenerate_and_apply_config_status()` with rollback on failure.

**Frontend / Web Interface**

1. **Part 4.2 (Web-Interface):** Add a "Parent device" field to the drawer *(a new section component, proposed `DeviceParentSection.tsx` in `components/device-inventory/`)* with a searchable list of other monitored devices, a "None" choice and the suggested gateway.
2. **Part 4.2 (Web-Interface):** Show a warning when the chosen parent is not monitored, and the server's 400 message for cycles or invalid parents.
3. **Part 4.2 (Web-Interface):** Show the parent in the drawer and an optional column or tooltip in `HostTable.tsx`.
4. **Part 4.2 (Web-Interface):** Respect `system.hosts.edit`: read-only without it.

#### D. Implementation Guidelines

- Preserve the existing meaning of DOWN for hosts with no parent.

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

- [ ] **Part 4.1 (System):** Setting a parent makes the generated host definition contain a `parents` line, and Nagios validates it.
- [ ] **Part 4.1 (System):** A self-parent, a cycle, or a retired or merged parent is refused with 400.
- [ ] **Part 4.1 (System):** Retiring or merging a parent leaves no dangling reference and the config still validates.
- [ ] **Part 4.1 (System):** A host whose parent is paused still gets a valid config, without `parents`.
- [ ] **Part 4.1 (System):** On a lab network, powering off a parent makes its children UNREACHABLE and only the parent raises a DOWN alert.
- [ ] **Part 4.1 (System):** Hosts without a parent behave exactly as before.
- [ ] **Part 4.2 (Web-Interface):** A user with `system.hosts.edit` can set, change and clear a parent, and it persists after reload.
- [ ] **Part 4.2 (Web-Interface):** Cycle and invalid choices show the server message.
- [ ] **Part 4.2 (Web-Interface):** A user without the permission sees the parent but cannot change it.
- [ ] **Part 4.2 (Web-Interface):** Existing drawer and table tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Device_Inventory_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Drawer help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 4.1 (System):** Unit: cycle detection, merge and retire re-pointing, template output with and without a parent, paused-parent handling.
- **Part 4.1 (System):** API: permission and 400 paths for the extended device route.
- **Part 4.1 (System):** Migration up and down.
- **Part 4.1 (System):** Lab (record in `docs/test-runs/`): gateway and two children, power off the gateway.
- **Part 4.1 (System):** Regression: `test_device_identity.py`, `test_device_identity_routes.py`, `test_create_host_cfg.py`.
- **Part 4.2 (Web-Interface):** Frontend: set, clear, error and read-only states.
- **Part 4.2 (Web-Interface):** Regression: Device Inventory tests listed above.

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
