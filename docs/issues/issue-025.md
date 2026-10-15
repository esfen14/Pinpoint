### Issue #25 — System Implementation Add Disk and Resource Trend Forecast Warnings From Stored Performance Data

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** High

**Related Nagios Core Feature:** Proactive Resolution; Performance Data

**Dependencies:** None to compute forecasts. Delivering a forecast as a notification depends on [Issue #19](issue-019.md) and [Issue #22](issue-022.md).

**Plan reference:** Issue #25 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Awaiting a product decision.** Nagios Core only reacts to thresholds that have already been crossed. A forecast ("disk full in about 6 days") goes beyond Nagios Core and is new PinPoint behavior, so the team must confirm it wants it and whether a forecast may notify or only display. Do not start until that is decided. Part 25.1's computation also needs *further investigation*: confirm on a lab appliance how many samples per check exist and how long history is kept.

#### A. Problem Description

**Part 25.1 (System) — System Implementation Compute Forecasts of When a Metric Will Cross Its Threshold**

The other issues react after a HARD failure. A proactive solution also warns before the failure. PinPoint already stores each check's measured value and its warning and critical thresholds, but it only ever compares the latest value with the threshold. A disk that fills 1 percent a day looks healthy until it turns CRITICAL.

**Part 25.2 (Web-Interface) — Web-Interface Implementation Show Forecasts on the Dashboard and Service Status**

Operators need to see which resources are on course to fail and when.

**Out of scope for this issue:**

- Machine learning or anomaly detection. A simple, explainable trend (a linear fit over a bounded window) is the limit of this issue.
- Taking an automatic action on a forecast. That is a separate decision; the first useful step is a warning.
- Third-party metrics systems (out of scope for the plan).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 25.1: `ServicePerfData` holds `Metric`, `Measured_Value`, `Unit`, `Warning_Threshold`, `Critical_Threshold`, `Minimum` and `Maximum` per check, linked to `ServiceStatus`, which carries `Timestamp`, `Hostname`, `Service` and the state (`server/app/history_models.py`). That gives a time series per host, service and metric.
- Part 25.1: `server/app/scheduler.py` has the `retention_purge` job that prunes `ServicePerfData`. Its retention window limits how far back a trend can look; the configured value was not verified here.
- Part 25.1: `server/app/api/system/statistics.py` and `network_health.py` already query perf data for charts and are the place to reuse query helpers.
- Part 25.2: `client/src/components/dashboard/ResourceUtilizationSection.tsx` and `ServiceOverview.tsx` show resource values; `client/src/components/system-status/ServiceStatusTable.tsx` lists services.

#### C. Required Changes

**Backend / System**

1. **Part 25.1 (System):** Add a forecast module *(proposed, `server/app/forecast.py`)* that, for a bounded set of metrics (disk usage percent and memory usage percent first), fits a straight line to the last `W` hours of samples and estimates when the line crosses the warning and critical thresholds. Return nothing when there are too few samples, the trend is flat or falling, the fit is poor, or the value is already past the threshold.
2. **Part 25.1 (System):** Run it from a short APScheduler job (`max_instances=1`, `coalesce=True`) over a bounded set of services, store only the latest forecast per host, service and metric, and never keep a long history of forecasts.
3. **Part 25.1 (System):** Add a read route *(proposed, `server/app/api/system/forecast.py`)* returning forecasts sorted by soonest crossing, with the window, sample count and slope so the number is explainable. Reuse the existing view permissions.
4. **Part 25.1 (System):** If the team approves notifications, send one custom notification per forecast that crosses the configured horizon (for example 7 days) through the Issue #19 channel, once per crossing, with settings for horizon and on/off defaulting to off.

**Frontend / Web Interface**

1. **Part 25.2 (Web-Interface):** Add a "Running out soon" list to the Dashboard and a forecast badge to the service table, each showing the metric, the estimated date and the plain-language basis ("based on the last 3 days").
2. **Part 25.2 (Web-Interface):** Show an explicit empty state when there is nothing to forecast and a "not enough data yet" state for new services.
3. **Part 25.2 (Web-Interface):** Add the horizon and notification settings to the Settings page if step 4 of Part 25.1 is approved.

#### D. Implementation Guidelines

- Bound the cost: a fixed window, a fixed metric list and a cap on services per run, with queries that use the existing `Timestamp` index and avoid per-service full scans.
- A forecast is an estimate. Label it as one everywhere, never present it as a failure, and never let it change a service's Nagios state.
- A counter reset, a deleted file or a recent cleanup produces a falling or noisy series; the module must return no forecast rather than an alarming number.
- Do not keep a forecast for a retired or paused device.

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

- [ ] **Part 25.1 (System):** For a synthetic series that rises steadily, the forecast returns a crossing date within the stated tolerance of the true value.
- [ ] **Part 25.1 (System):** A flat, falling, noisy, too-short or already-crossed series returns no forecast.
- [ ] **Part 25.1 (System):** Run time and query count stay bounded as the number of services grows (checked with a seeded dataset).
- [ ] **Part 25.1 (System):** A forecast never changes any Nagios state or generated config.
- [ ] **Part 25.1 (System):** With notifications off (the default) nothing is sent; with them on, one notification is sent per crossing.
- [ ] **Part 25.2 (Web-Interface):** The Dashboard and service table show forecasts, the basis, and the empty and not-enough-data states.
- [ ] **Part 25.2 (Web-Interface):** The settings, if approved, save and reload.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text explaining how the estimate is calculated and its limits.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 25.1 (System):** Unit: line fit on rising, flat, falling, noisy, reset and short series; threshold-crossing arithmetic; horizon filtering.
- **Part 25.1 (System):** Performance: seeded history for many services, measure job duration and query count.
- **Part 25.1 (System):** API: ordering, empty result, permission.
- **Part 25.1 (System):** Lab (record in `docs/test-runs/`): fill a disk on a lab device at a known rate and compare the forecast with the real time to threshold.
- **Part 25.2 (Web-Interface):** Frontend: list, badge and the three states.
- Regression: dashboard and statistics tests still pass.

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
