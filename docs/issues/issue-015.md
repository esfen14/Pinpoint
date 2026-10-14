### Issue #15 — System Refinement Add Load Average, Swap and Disk I/O Defaults and Guided Process Check

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Processor Load; Disk Usage; Memory Monitoring; Process Monitoring; Process Monitoring

**Dependencies:** None

**Plan reference:** Issue #15 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 15.1 (System) — System Refinement Add Load Average, Swap and Disk I/O NCPA Defaults**

Remote hosts get only CPU percent, memory percent and per-partition disk usage by default. Nagios Core covers load averages, swap, disk I/O and critical-process checks. PinPoint can monitor these through the editable NCPA metric table, but no defaults exist and nothing guides an administrator to a valid path.

**Part 15.2 (Web-Interface) — Web-Interface Refinement Add Guided Process Check Entry to Plugin Settings**

Checking that a process is running needs an administrator to hand-write an NCPA path and query arguments in the metric table. There is no guided form.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 15.1: `server/config.py` → `NCPA_METRICS`: `cpu` (`cpu/percent`, `aggregate=avg`), `memory` (`memory/virtual/percent`) and `disk` (`disk/logical/{partition}/used_percent`).
- Part 15.1: `server/app/network_discovery/plugin_registry.py` → `ncpa_checks()` expands a metric into services and `{partition}` into one service per recorded partition (`NCPADevicePartition`); `plugin_settings.py` and `api/system/plugin_settings.py` validate NCPA paths (letters, digits, `_ - . |`, or `{partition}`) and queryargs.
- Part 15.1: `server/app/api/system/network_health_activity.py` reads server-side `check_procs` and `check_users` results.
- Part 15.1: `server/app/ncpa_deployment/ncpa_deployment.py` queries the agent (`GET /api/disk/logical`) during deployment, which shows how to probe an agent's nodes.
- Part 15.1: NCPA version deployed is 3.5.0 (`docs` and `Implementation_Status.md`). Which API paths exist for load average, swap and disk I/O in that version is *further investigation required*; verify against a deployed agent before adding defaults.
- Part 15.2: `client/src/components/settings/PluginSettings.tsx` edits the NCPA metric table (metric, path, warning, critical, units, query args) with validation mirroring the server.
- Part 15.2: `client/src/lib/pluginSettingsApi.ts`, `client/src/types/pluginSettings.ts`; test `client/src/test/PluginSettings.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 15.1 (System):** Probe a lab agent and record the valid NCPA paths and units for load, swap usage and disk I/O in the pull request.
2. **Part 15.1 (System):** Add default entries to `NCPA_METRICS` only for paths confirmed to exist, with sensible warning and critical thresholds, keeping the three current entries unchanged. Metric names must pass the existing rules (lowercase letters, digits, `_`, at most 32).
3. **Part 15.1 (System):** Keep new defaults off for hosts where a check cannot run: a path that returns an error must produce a skipped-service reason (existing `SkippedService` mechanism), not a CRITICAL storm.
4. **Part 15.1 (System):** Document the process-check pattern (NCPA path with `queryargs`) in the manual and add a validator test for a typical process path so it is accepted.

**Frontend / Web Interface**

1. **Part 15.2 (Web-Interface):** Add an "Add process check" action to the NCPA table that asks for a process name and expected count, and fills the metric name, path and query arguments with the pattern documented in Part 15.1.
2. **Part 15.2 (Web-Interface):** Show the generated row for review before saving and keep all existing validation.

#### D. Implementation Guidelines

- Adding defaults increases the number of Nagios services per device. State the new per-device service count in the pull request and confirm Nagios load on the lab.

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

- [ ] **Part 15.1 (System):** The new default metrics appear as services for a device with an NCPA agent and report OK on a lab host.
- [ ] **Part 15.1 (System):** The three existing metrics and their service names are unchanged.
- [ ] **Part 15.1 (System):** A metric whose path the agent does not provide is reported as skipped, not as a failing service.
- [ ] **Part 15.1 (System):** A documented process-check path is accepted by the settings validator.
- [ ] **Part 15.2 (Web-Interface):** An administrator can add a process check without typing a path, and the row appears in the table and saves.
- [ ] **Part 15.2 (Web-Interface):** Invalid process names are blocked with a message.
- [ ] **Part 15.2 (Web-Interface):** Existing table behavior and tests are unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Manual section on available host metrics and process checks; Help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request.

#### G. Testing and Verification

- **Part 15.1 (System):** Unit: `ncpa_checks()` output with the new defaults; validator acceptance of the process path.
- **Part 15.1 (System):** Lab NCPA run (record in `docs/test-runs/`): new services reach OK on two targets.
- **Part 15.1 (System):** Regression: `test_plugin_registry.py`, `test_plugin_settings.py`, `test_ncpa.py`.
- **Part 15.2 (Web-Interface):** Frontend: guided add, validation, generated row, save.
- **Part 15.2 (Web-Interface):** Regression: `PluginSettings.test.tsx`.

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
