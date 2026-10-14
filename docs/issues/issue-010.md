### Issue #10 — System Refinement Add Retry Interval and Maximum Check Attempts Settings

**Category:** System

**Work Type:** Refinement

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Flap Detection; Event Handlers (state tuning)

**Dependencies:** None

**Plan reference:** Issue #10 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

The system Check interval is configurable (1, 2, 5, 10 or 15 minutes), but the retry interval and the number of attempts before a problem becomes HARD are fixed in the templates (`retry_interval 1`, `max_check_attempts 3`). Administrators cannot trade alert speed against false alarms, and the Nagios tuning guidance the project cites depends on these values.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/network_discovery/templates/service.cfg.tpl`: `max_check_attempts 3`, `check_interval {check_interval}`, `retry_interval 1`. `host.cfg.tpl`: `max_check_attempts 3`.
- `server/app/network_discovery/host_config_templates.py` → `check_interval()` reads `SystemSettings.Check_Interval`.
- `server/app/api/system/settings.py`: validates the interval (1, 2, 5, 10, 15), flushes, calls `regenerate_and_apply_config_status()` and returns 422 with rollback on failure; migration `server/migrations/versions/a6f4d2c8e190_check_interval.py` is the precedent.
- `client/src/components/settings/SystemSettings.tsx` renders the Check interval control, and `client/src/types/settings.tsx` carries the value.
- Tests: `server/tests/unit/test_settings_permissions.py`, `test_create_host_cfg.py`, `client/src/test/SystemSettingsConflict.test.tsx`.

#### C. Required Changes

**Backend / System**

1. Add `Retry_Interval` (minutes, bounded, for example 1 to 10 and not greater than the check interval) and `Max_Check_Attempts` (for example 1 to 10) to `SystemSettings` with a migration whose defaults are 1 and 3.
2. Pass both into `create_host()` and `create_service()` and replace the literals in the two templates.
3. Extend `PUT /api/system` validation and the apply-and-rollback flow exactly as for `Check_Interval`, under `settings.system`.

**Frontend / Web Interface**

1. Add two controls beside the Check interval in `SystemSettings.tsx` with help text on the effect (more attempts means slower alerts and fewer false alarms), and update `types/settings.tsx`.
2. Validate in the form with the same bounds and show server errors, including the 422 apply failure.

#### D. Implementation Guidelines

- Defaults must reproduce current generated config exactly. Do not add a per-device override in this issue.

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

- [ ] With defaults, generated config is identical to today's.
- [ ] Saved values appear in every generated host and service definition and Nagios validates the config.
- [ ] A retry interval above the check interval, or any out-of-range value, is rejected with 400.
- [ ] A rejected Nagios config rolls the settings back and returns 422 with the message.
- [ ] The UI shows, saves and reloads the values, and users without `settings.system` cannot change them.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the controls.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request.

#### G. Testing and Verification

- Unit: template output (default and custom), validation matrix.
- API: permission, 400, 409, 422.
- Migration up and down.
- Frontend: control validation and conflict handling (extend `SystemSettingsConflict.test.tsx`).
- Regression: `test_create_host_cfg.py`, `test_settings_permissions.py`.

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
