### Issue #21 — Web-Interface Refinement Reconcile Reports Documentation and Add Availability Target Support

**Category:** Web-Interface

**Work Type:** Refinement

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Availability Reports

**Dependencies:** None

**Plan reference:** Issue #21 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Product decision (2026-10-17, GitHub #134):** The owner rejected availability
> targets: Pinpoint only needs to show measured uptime, which is already
> implemented. Only Part 21.1 is in scope. Parts 21.2 and 21.3 and their target
> settings, migrations, validation, indicators, exports and associated tests /
> deliverables below are historical proposals and are not acceptance gates.
> Scheduled or recurring emailed reports remain outside this issue.

#### A. Problem Description

**Part 21.1 (Web-Interface) — Web-Interface Refinement Reconcile Reports Page Documentation With Implemented Report Views**

`Implementation_Status.md` says the Reports UI exposes only host availability and network-services views. The page actually has six (verified in `client/src/pages/ReportsPage.tsx`): Host Availability, Network Services, Hosts by OS, Device Services, Alerts and Notifications. A stale status file misleads planning and agents.

**Part 21.2 (System) — System Implementation Add Availability Target Setting and Breach Flag to Availability Report**

The availability report shows measured uptime but not whether it met a commitment, so an administrator must compare numbers by eye.

**Part 21.3 (Web-Interface) — Web-Interface Refinement Add Availability Target Control and Breach Indicator to Reports**

Once the backend can compare uptime with a target, the Reports page needs a way to set it and to show which hosts missed it.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 21.1: `client/src/pages/ReportsPage.tsx` defines `VIEW_TABS` for all six views and the periods `last_24h`, `today`, `last_7d`, `last_30d`, `last_90d`, `custom`.
- Part 21.1: `client/src/components/reports/ExtraReports.tsx` implements `hosts-by-os`, `device-services`, `alerts` and `notifications`; `HostAvailabilityReportTable.tsx` and `NetworkServicesReportTable.tsx` implement the other two.
- Part 21.1: `server/app/api/system/report.py` has the six endpoints under `system.report`.
- Part 21.1: `spec files/Implementation_Status.md` (row "Reports frontend breadth"), `Frontend_Modules_and_Routes.md` and `Display_Requirements.md` describe the Reports page.
- Part 21.2: `server/app/api/system/report.py` → `report_host_availability()` (`GET /api/system/report/availability`), `report_hosts_by_os()` and the other reports under `system.report`.
- Part 21.2: `SystemSettings` in `server/app/system_models.py` is where system-wide values live; `api/system/settings.py` handles saves with versions.
- Part 21.3: `client/src/pages/ReportsPage.tsx`, `components/reports/HostAvailabilityReportTable.tsx` and `ExtraReports.tsx`.
- Part 21.3: `client/src/components/settings/SystemSettings.tsx` is where a system-wide control belongs.
- Part 21.3: `client/src/types/report.ts` holds the wire types.

#### C. Required Changes

**Backend / System**

1. **Part 21.2 (System):** Add an availability target setting (percentage, 0 to 100, default empty meaning no target) to `SystemSettings` with a migration.
2. **Part 21.2 (System):** When a target is set, add `target` and `meets_target` to each host row and to the summary of the availability and hosts-by-OS reports. With no target the responses are unchanged.
3. **Part 21.2 (System):** Validate the value on save under `settings.system`.

**Frontend / Web Interface**

1. **Part 21.1 (Web-Interface):** Verify each of the six views against its endpoint and record what each shows, its period handling and its export support.
2. **Part 21.1 (Web-Interface):** Correct `Implementation_Status.md` and the Reports section of `Frontend_Modules_and_Routes.md` to match what is implemented.
3. **Part 21.1 (Web-Interface):** If a view has a defect, file it separately and do not fix it here.
4. **Part 21.3 (Web-Interface):** Add the target control to the System settings card with validation (0 to 100).
5. **Part 21.3 (Web-Interface):** Show a "Meets target" indicator per row and a breach count in the report summary only when a target is set, and include it in exports.

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

- [ ] **Part 21.1 (Web-Interface):** `Implementation_Status.md` and `Frontend_Modules_and_Routes.md` list all six views accurately and no longer say only two exist.
- [ ] **Part 21.1 (Web-Interface):** Each documented view names the API route behind it.
- [ ] **Part 21.1 (Web-Interface):** `scripts/verify.sh docs` passes.
- [ ] **Part 21.2 (System):** With no target, report responses are identical to today's.
- [ ] **Part 21.2 (System):** With a target, each row has `meets_target` computed against the measured uptime and the summary counts breaches.
- [ ] **Part 21.2 (System):** An out-of-range target is rejected with 400.
- [ ] **Part 21.3 (Web-Interface):** A user with `settings.system` can set and clear the target.
- [ ] **Part 21.3 (Web-Interface):** With a target set the report shows the indicator per row and the breach count, and with none it looks as it does today.
- [ ] **Part 21.3 (Web-Interface):** Exports include the new column only when a target is set.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 21.1 (Web-Interface):** `scripts/verify.sh docs` (link and drift checks).
- **Part 21.1 (Web-Interface):** Manual: open each view on a lab appliance and confirm it loads data.
- **Part 21.2 (System):** Unit: report output with and without target, boundary values (exactly at target).
- **Part 21.2 (System):** Migration up and down.
- **Part 21.2 (System):** Regression: `test_report_notifications_alerts.py`, `test_settings_permissions.py`.
- **Part 21.3 (Web-Interface):** Frontend: control validation, indicator visibility, export columns.
- **Part 21.3 (Web-Interface):** Regression: reports and settings tests.

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
