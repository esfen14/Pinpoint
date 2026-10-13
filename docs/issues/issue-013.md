### Issue #13 — System Implementation Add Interface Bandwidth Rates, Interface Discovery and Bandwidth Chart

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Bandwidth Monitoring

**Dependencies:** [Issue #14](issue-014.md)

**Plan reference:** Issue #13 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 13.1 (System) — System Implementation Add Interface Bandwidth Rate Calculation and Interface Discovery**

PinPoint collects raw SNMP octet counters for one hardcoded interface (index 3) but never turns them into a rate or lets a device choose its interfaces. Counters alone say nothing about bandwidth, so the Nagios Core bandwidth-monitoring capability is effectively unavailable.

**Part 13.2 (Web-Interface) — Web-Interface Refinement Add Interface Selector and Bandwidth Chart to Network Health**

Operators cannot see bandwidth or choose which interface to watch.

**Out of scope for this issue:**

- SNMP v3 (Issue #14).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 13.1: `server/config.py` → `SNMP_OIDS` includes `lan_in_octets` (`1.3.6.1.2.1.2.2.1.10.3`) and `lan_out_octets` (`...16.3`), editable in Settings → Plugins (`server/app/network_discovery/plugin_settings.py`, `PluginSettings`).
- Part 13.1: `server/app/network_discovery/plugin_registry.py` → `snmp_checks()` builds one Nagios service per OID; per-host overrides come from `NetworkDiscovery.Plugin_Variables["snmp"]`.
- Part 13.1: `ServicePerfData` and `ServiceStatus` in `server/app/history_models.py` hold each poll's `Measured_Value` and `Timestamp`; `server/app/nagios/status.py` writes them.
- Part 13.1: Trend queries: `server/app/api/system/network_health.py` and `statistics.py` → `perf_trends()` with the fixed windows 1, 6, 24, 168 hours.
- Part 13.1: How to list a device's interfaces (net-snmp `snmpwalk`, a Python SNMP library, or the `check_ifstatus` plugin) is *further investigation required*; no interface discovery exists in the repository.
- Part 13.2: `client/src/pages/NetworkHealthPage.tsx` with `components/network-health/` (`NetworkChart`, `MetricGraphModal.tsx`, `TimeRangeSelect.tsx`, `SparklineMetricCard.tsx`, `TrendStatCard.tsx`) and `client/src/utils/trendHours.ts`.
- Part 13.2: `client/src/components/device-inventory/StatusDetailDrawer.tsx` shows per-device details.
- Part 13.2: Tests: `NetworkHealthPage.test.tsx`, `NetworkHealthWidgets.test.tsx`, `TimeRangeSelect.test.tsx`.

#### C. Required Changes

**Backend / System**

1. **Part 13.1 (System):** Add a rate calculator *(proposed `server/app/bandwidth.py`)* that converts consecutive counter samples to bits per second, handling counter wrap for 32-bit and 64-bit counters, device restarts (a decrease larger than the wrap allowance) and gaps. Return `null` for a window with fewer than two valid samples.
2. **Part 13.1 (System):** Add `GET /api/system/network-health/bandwidth?hostname=&interface=&hours=` *(proposed, `network_health_activity.py`)* under `system.network_health`, using only the allowed windows, returning in and out series and the latest utilisation when the interface speed is known.
3. **Part 13.1 (System):** Investigate and implement interface discovery for a device (name, index, speed, status), stored per device *(proposed table `DeviceInterface`)* and refreshed on demand and on scan. Decide the mechanism during implementation and record it in the pull request.
4. **Part 13.1 (System):** Generate the in and out octet services per selected interface instead of the single fixed index, reusing `snmp_checks()` and the per-device plugin variables saved through the API of Issue #14. Keep the default services unchanged when no interface is selected.

**Frontend / Web Interface**

1. **Part 13.2 (Web-Interface):** Add a bandwidth card *(proposed `components/network-health/BandwidthCard.tsx`)* with a device and interface selector, in and out lines, units that scale (bit/s to Gbit/s) and the existing time-range control.
2. **Part 13.2 (Web-Interface):** In the device drawer add an interface list with a monitor on/off choice using the backend from Part 13.1.
3. **Part 13.2 (Web-Interface):** Show clear states for no SNMP device, no data, insufficient data and server errors, following the existing "Insufficient data" convention.
4. **Part 13.2 (Web-Interface):** Add types and API calls.

#### D. Implementation Guidelines

- Compute rates from stored samples, not by changing the check, so Nagios behavior is untouched.
- Interface selection changes the generated config, so apply it through `regenerate_and_apply_config_status()`.

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

- [ ] **Part 13.1 (System):** For synthetic counters the calculator returns the expected bit rate, handles 32-bit and 64-bit wrap and a counter reset, and returns `null` for insufficient data.
- [ ] **Part 13.1 (System):** The bandwidth endpoint returns in and out rates for an interface and rejects windows other than 1, 6, 24, 168 hours with 400.
- [ ] **Part 13.1 (System):** A device can have several interfaces monitored, each with in and out services, and Nagios validates the config.
- [ ] **Part 13.1 (System):** With no interface selected, generated config matches today's.
- [ ] **Part 13.1 (System):** On a lab device with SNMP, the reported rate matches a known traffic generator within a stated tolerance.
- [ ] **Part 13.2 (Web-Interface):** A user can pick a device and interface and see in and out bandwidth for the allowed ranges.
- [ ] **Part 13.2 (Web-Interface):** Units scale correctly and axes are labelled.
- [ ] **Part 13.2 (Web-Interface):** Missing or insufficient data shows a message, not a broken chart.
- [ ] **Part 13.2 (Web-Interface):** Existing Network Health tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the card.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request.

#### G. Testing and Verification

- **Part 13.1 (System):** Unit: rate calculation (wrap at 2^32 and 2^64, reset, gap, single sample), API validation, config generation for several interfaces.
- **Part 13.1 (System):** Lab (record in `docs/test-runs/`): generate known traffic with a tool such as `iperf3` and compare.
- **Part 13.1 (System):** Regression: `test_plugin_registry.py`, `test_plugin_settings.py`, `test_network_health.py`.
- **Part 13.2 (Web-Interface):** Frontend: selector, scaling, empty and insufficient states.
- **Part 13.2 (Web-Interface):** Regression: Network Health tests listed above.

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
