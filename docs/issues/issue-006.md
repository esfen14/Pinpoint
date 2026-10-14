### Issue #6 — System Refinement Add Flap Detection Settings, Flapping Filter and Flap History

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Flap Detection

**Dependencies:** [Issue #10](issue-010.md)

**Plan reference:** Issue #6 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 6.1 (System) — System Refinement Add Flap Detection Settings and Flap History Reporting**

Nagios flap detection is already on for PinPoint-generated hosts and services (verified on a lab appliance: global `enable_flap_detection=1`, thresholds 5.0 and 20.0, and the generated host resolves to `flap_detection_enabled 1`). PinPoint stores and shows the current flapping flag, but administrators cannot change the thresholds or switch it off for noisy devices, and nothing records how often or how long a host or service has flapped.

**Part 6.2 (Web-Interface) — Web-Interface Refinement Add Flap Detection Settings Card and Flapping History View**

Flapping is shown only as a yellow label or a count. An administrator cannot tune it, filter for flapping items, or see how long they have been flapping.

**Out of scope for this issue:**

- Changing the global values in `nagios.cfg`, which belongs to the installer.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 6.1: `server/app/history_models.py`: `HostStatus.Is_Flapping`, `ServiceStatus.Is_Flapping`, `ProgramStatus.Enable_Flap_Detection`, each written by the poller `server/app/nagios/status.py` (`get_status()`).
- Part 6.1: `server/app/api/system/network_hosts.py`, `network_services.py`: return `is_flapping` per item. `statistics.py` and the dashboard summary return `flapping` counts.
- Part 6.1: `server/app/api/system/network_health_activity.py` (around line 678) adds a flapping observation to the insights.
- Part 6.1: `server/app/network_discovery/templates/host.cfg.tpl` and `service.cfg.tpl` set no flap fields, so Nagios defaults apply.
- Part 6.1: Check interval is the precedent for a system setting that changes generated config: `SystemSettings.Check_Interval`, `host_config_templates.check_interval()`, `server/app/api/system/settings.py`.
- Part 6.1: History retention: `server/app/scheduler.py` → `_purge_old_data()` governs how long snapshots exist, which bounds any history computed from them.
- Part 6.2: `client/src/components/dashboard/ServiceOverview.tsx` (Flapping Hosts, Flapping Services, the Flap Detection switch row) and `client/src/types/dashboard.ts`.
- Part 6.2: `client/src/components/device-inventory/HostTable.tsx` and `StatusDetailDrawer.tsx`; `client/src/components/system-status/ServiceStatusTable.tsx` show a flapping label.
- Part 6.2: `client/src/components/settings/SystemSettings.tsx` holds the system settings card pattern.
- Part 6.2: Tests: `ServiceOverview.test.tsx`, `StatusDetailDrawer.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 6.1 (System):** Add system settings *(proposed fields on `SystemSettings`)*: flap detection enabled (default true), low threshold and high threshold (default empty meaning "use Nagios's global values"), with a migration whose defaults leave generated config unchanged.
2. **Part 6.1 (System):** Render `flap_detection_enabled`, and `low_flap_threshold` and `high_flap_threshold` only when a value is set, in `host.cfg.tpl` and `service.cfg.tpl` through `host_config_templates.py`. Validate thresholds: numbers from 0 to 100, low less than high.
3. **Part 6.1 (System):** Extend `PUT /api/system` (`settings.py`) to accept the fields under the `settings.system` permission, apply through `regenerate_and_apply_config_status()` and roll back with 422 on failure, mirroring `Check_Interval`.
4. **Part 6.1 (System):** Add `GET /api/system/network-health/flapping?hours=` *(proposed, in `network_health_activity.py`)* returning, per host and service that was flapping in the window, the number of snapshots flagged, first and last time, and current state. Use only the existing windows (1, 6, 24, 168 hours) and the permission `system.network_health`.
5. **Part 6.1 (System):** When `ProgramStatus.Enable_Flap_Detection` is false, return that fact so the UI can warn that per-object settings have no effect.

**Frontend / Web Interface**

1. **Part 6.2 (Web-Interface):** Add a "Flap detection" card to `SystemSettings.tsx`: on/off toggle, low and high threshold inputs (empty means Nagios default, with the default values shown as help text), validation matching the server (0 to 100, low less than high), save with the existing conflict handling.
2. **Part 6.2 (Web-Interface):** Add a "Flapping only" filter to `ServiceStatusTable.tsx` and the host table, using the existing `is_flapping` field.
3. **Part 6.2 (Web-Interface):** Add a "Flap history" list *(proposed section in `StatusDetailDrawer.tsx` or a small new component)* calling the new flapping endpoint for the selected window, showing snapshot count and first and last time, with loading, empty and error states.
4. **Part 6.2 (Web-Interface):** Show the server's warning when global flap detection is disabled.

#### D. Implementation Guidelines

- Flap history is computed from periodic snapshots (every 60 s), so it can miss very fast flaps. State that in the route docstring and in the spec; do not describe it as exact.

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

- [ ] **Part 6.1 (System):** With default settings, generated host and service definitions are unchanged.
- [ ] **Part 6.1 (System):** Saving custom thresholds writes `low_flap_threshold` and `high_flap_threshold`, and Nagios validates the config. Invalid values return 400.
- [ ] **Part 6.1 (System):** Turning flap detection off writes `flap_detection_enabled 0` and a rejected config is rolled back with 422.
- [ ] **Part 6.1 (System):** The flapping endpoint returns the right items for a seeded history and honors the allowed windows only (400 otherwise).
- [ ] **Part 6.1 (System):** The response reports when global flap detection is disabled.
- [ ] **Part 6.2 (Web-Interface):** A user with `settings.system` can enable, disable and set thresholds, and sees them after reload.
- [ ] **Part 6.2 (Web-Interface):** Invalid thresholds are blocked with a message, and a 422 shows Nagios's message.
- [ ] **Part 6.2 (Web-Interface):** The "Flapping only" filter lists exactly the flapping items.
- [ ] **Part 6.2 (Web-Interface):** The drawer lists flap history for the chosen window and shows an empty state when there is none.
- [ ] **Part 6.2 (Web-Interface):** Existing dashboard and drawer tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the card.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 6.1 (System):** Unit: template output for default, custom and disabled settings; threshold validation.
- **Part 6.1 (System):** API: `settings.system` permission, 400, 422 paths; flapping endpoint with seeded `HostStatus`/`ServiceStatus` rows (`server/tests/unit/test_network_health_activity.py` patterns).
- **Part 6.1 (System):** Migration up and down.
- **Part 6.1 (System):** Lab (record in `docs/test-runs/`): toggle a service rapidly and confirm the flag and the history entry.
- **Part 6.1 (System):** Regression: `test_status.py`, `test_network_hosts.py`, `test_network_services.py`, `test_create_host_cfg.py`.
- **Part 6.2 (Web-Interface):** Frontend: settings card validation and save, filter behavior, history states.
- **Part 6.2 (Web-Interface):** Regression: `ServiceOverview.test.tsx`, `StatusDetailDrawer.test.tsx`, `SystemSettingsConflict.test.tsx`.

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
