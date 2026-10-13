### Issue #19.2 — System Implementation Add Check Now Routes Through the Nagios Command Channel

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** External Commands

**Dependencies:** [Issue #19.1](issue-019-1.md)

**Plan reference:** Issue #19 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #19. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

Operators cannot ask Nagios to re-check a host or service. After fixing a problem they must wait for the next scheduled check (up to the Check interval) before the dashboard changes.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- No re-check capability exists. The command channel is specified in Issue #19.1.
- `server/app/api/system/network_hosts.py` and `network_services.py` hold the host and service routes and their permission checks.
- Rate-limit precedent: `POST /api/system/deployment/ncpa/check-credentials` limits one check per device per 3 seconds (`server/app/api/system/ncpa_deployment.py`).
- Permissions are seeded in `server/app/api/commands/seed.py` and granted with `flask sync-permissions`.

#### C. Required Changes

**Backend / System**

1. Add `POST /api/system/network-health/hosts/<hostname>/recheck` and `POST /api/system/network-health/services/<hostname>/<path:service_name>/recheck` *(proposed)*, using `<path:service_name>` because service names can contain `/`.
2. Send a forced check through the Issue #19.1 module. Rate-limit per target (for example one request per 10 seconds, 429 beyond it) and refuse targets not in the latest snapshot, paused, retired or merged devices.
3. Add a seeded permission *(proposed `system.recheck`)* and require it with login. Write an audit entry.

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

- [ ] A permitted user can trigger a forced check and the next poll shows the new result sooner than the scheduled interval.
- [ ] A second request inside the rate limit returns 429.
- [ ] Unknown, paused, retired and merged targets are refused.
- [ ] Without the permission the routes return 403.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #19.3.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit and API: permission, rate limit, refused targets, command sent (module mocked).
- Migration of permissions: `flask sync-permissions` adds `system.recheck` (see `test_seed.py`).
- Lab: force a check and observe the result.

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
