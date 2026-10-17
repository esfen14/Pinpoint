### Issue #5 — System Implementation Add Host-Based Service Notification Dependencies

**Category:** System

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Notification Dependencies

**Dependencies:** [Issue #4](issue-004.md)

**Plan reference:** Issue #5 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Dependency satisfied:** Issue #4 was completed in GitHub issue #117. On
> 2026-10-17 the user approved verifying Nagios's native same-host suppression
> and adding a visible NCPA TCP port check as the dependency master. The
> setting specifically defaults on; off preserves the prior generated config.

#### A. Problem Description

When a host is down, every service on it also alerts, and services that depend on others (for example NCPA metrics that need the NCPA port) alert separately. Nagios dependencies suppress this, but PinPoint generates none, so one outage becomes many notifications.

**Out of scope for this issue:**

- A user interface for editing dependencies: the first release is rule-based and automatic.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/network_discovery/create_host_cfg.py` writes hosts, services and contacts but no `hostdependency` or `servicedependency`.
- `server/app/network_discovery/host_config_templates.py` and the templates directory have no dependency template.
- Each NCPA metric service is generated per device by `plugin_registry.py` (`ncpa_checks`), so the relationship between an NCPA service and the device's NCPA port service is known at generation time.

#### C. Required Changes

**Backend / System**

1. Add `servicedependency.cfg.tpl` for NCPA metrics and render in `_create_host_cfg_file()`. Nagios has no host-to-service dependency object, so no `hostdependency` template is generated.
2. Verify on the lab appliance that Nagios suppresses service notifications while their own host is DOWN.
3. When dependency generation is on and NCPA metrics exist, generate a visible TCP service for the device's NCPA port. Each metric depends on that port service being OK, with `notification_failure_criteria c,u`.
4. Generate rules only for services that exist in the same config, and skip a rule whose target is missing, so Nagios never rejects a dangling dependency.
5. Add an on/off application configuration setting for NCPA dependency generation, default on. Apply generated changes through `regenerate_and_apply_config_status()`.

#### D. Implementation Guidelines

- Dependencies suppress notifications only, never checks, so the Dashboard and Network Health keep showing real service states.

General rules for every issue:

- Reuse the existing modules named in section B instead of adding parallel ones.
- Follow `spec files/Engineering_Standards.md`: route docstrings and banners, `success()`/`error()` envelopes, guard-clause validation, `db.session.rollback()` on every failed commit, TypeScript only in `client/src`.
- Keep existing behavior unchanged except for the new NCPA dependency, which explicitly defaults on. With the setting off, an existing test must prove the generated output is unchanged.
- Any change under `app/network_discovery/`, `app/ncpa_deployment/` or a command execution path needs the injection and secret-exposure review required by Engineering Standards "Sensitive modules": no untrusted input in shell commands or Nagios config, no secrets in logs or responses, and Nagios pre-apply validation preserved.
- New permissions are seeded in `server/app/api/commands/seed.py`, granted through `flask sync-permissions`, and wired to client page access where applicable. The client guard never replaces the server check.
- Model changes need a multi-database migration (`flask db migrate --multidb`) that is reviewed, not hand-edited without reason, with a working downgrade.
- Any Nagios config change goes through `regenerate_and_apply_config_status()` in `server/app/network_discovery/create_host_cfg.py`, so it is validated with the Nagios binary and rolled back if rejected.
- Every user-facing control needs loading, error, empty and success states and a plain-language label.
- Consider reliability and cost: bound loops, set timeouts on network calls, and avoid per-poll work that grows with the number of hosts.
- Update the matching file in `spec files/` and `Implementation_Status.md` in the same pull request, as `AGENTS.md` requires.

#### E. Acceptance Criteria

- [ ] Nagios validates the generated config, and a live lab run proves service notifications are suppressed when their own host is DOWN.
- [ ] NCPA metric services carry a dependency on their generated port service when it exists, and none when it does not; the generated port check is visible as a service.
- [ ] With the setting off, config is unchanged from today.
- [ ] On a lab appliance, taking a host down sends one host notification and none for its services.
- [ ] Dashboard and Network Health still show every service's real state.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Short note describing that service alerts are suppressed while their host is down.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: rendering for hosts with and without NCPA, missing-target handling, setting off.
- Lab (record in `docs/test-runs/`): power off a host and count notifications.
- Regression: `test_create_host_cfg.py`, `test_plugin_reconcile.py`.

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
