### Issue #1.1 — System Implementation Add Notification Policy Model and Nagios Timeperiod Rendering

**Category:** System

**Work Type:** Implementation

**Priority:** High

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Time-Based Alerting; Contact Notifications

**Dependencies:** None

**Plan reference:** Issue #1 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #1. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

Notification timing is fixed in the Nagios templates PinPoint generates. Every host and contact uses the `24x7` period, the notification options are fixed, and the renotify interval is fixed at 30 minutes. An administrator cannot set quiet hours, choose which states notify, or change how often a problem renotifies.

Nagios Core supports time-based alerting through timeperiod objects and notification options. PinPoint generates the hosts, services and contacts but never generates a timeperiod, so the capability cannot be used.

**Out of scope for this issue:**

- The settings screen (see Issue #1.2).
- Escalations (Issue #3.1) and per-host recipients (open GitHub issue #79).
- Any new notification channel.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/network_discovery/templates/contact_template.cfg.tpl` hardcodes `service_notification_period 24x7`, `host_notification_period 24x7`, options `w,u,c,r,f,s` and `d,u,r,f,s`, and the two email commands.
- `server/app/network_discovery/templates/host.cfg.tpl` hardcodes `notification_interval 30` and `notification_period 24x7`. `service.cfg.tpl` has no notification fields.
- `server/app/network_discovery/host_config_templates.py`: `create_host()`, `create_service()` and `check_interval()` render the templates. `check_interval()` already reads a system setting, which is the pattern to follow.
- `server/app/network_discovery/create_host_cfg.py`: `_create_host_cfg_file()` writes contacts (Active users with `Receive_Email_Alerts`) and the `system_users` group. `regenerate_and_apply_config_status()` validates with the Nagios binary and applies or rolls back.
- `server/app/api/system/settings.py` shows the apply-and-rollback pattern for `Check_Interval` (flush, regenerate, rollback and 422 on failure), `FIELD_PERMISSIONS` and `PERMISSION_LABELS`.
- `server/app/system_models.py`: `SystemSettings` (singleton, `Version` and `Updated_By`). Live check on a VM appliance: Nagios loads the stock `timeperiods.cfg` (including `24x7`) through `cfg_file`.

#### C. Required Changes

**Backend / System**

1. Add a singleton `NotificationPolicy` model *(proposed, `server/app/system_models.py`)* holding: quiet-hour windows (weekday, start `HH:MM`, end `HH:MM`), host notification options (subset of `d,u,r,f,s`), service notification options (subset of `w,u,c,r,f,s`), and the renotify interval in minutes (bounded, for example 0 to 1440). Add `Version` and `Updated_By` like `SystemSettings`.
2. Add a migration (`flask db migrate --multidb`) that creates the table and seeds one row whose values reproduce today's behavior exactly (`24x7`, current options, 30 minutes, no quiet hours).
3. Add a `timeperiod.cfg.tpl` template *(proposed)* and render one timeperiod, named by a fixed constant (for example `pinpoint_notify`), covering the allowed hours as the complement of the quiet windows. Emit nothing new when no quiet hours are set.
4. Parameterize `contact_template.cfg.tpl`, `host.cfg.tpl` and `service.cfg.tpl` with the period, options and interval. Add notification fields to `service.cfg.tpl`. Update `create_contact_template()`, `create_host()` and `create_service()` accordingly.
5. Add `GET /api/system/notification-policy` and `PUT /api/system/notification-policy` *(proposed, new `server/app/api/system/notification_policy.py`, registered in `server/app/api/system/__init__.py`)* with route docstrings, optimistic `version` handling (409 on a stale version, as for system settings) and a login plus `settings.system` permission check.
6. On save, flush, call `regenerate_and_apply_config_status()`, and on `failed` roll back and return 422 with the message, exactly as the Check interval does. Write a Configuration Change log entry when audit logging is on.
7. Validate every value on the server: weekday names from a fixed set, `HH:MM` 24-hour times, `start` before `end`, no overlapping windows, option letters from the allowed sets, and interval bounds. Never put user text into the Nagios config.

#### D. Implementation Guidelines

- The default policy must render config that is identical to today's, so the existing `server/tests/unit/test_create_host_cfg.py` expectations hold.
- A time zone is needed to interpret quiet hours. Use the Nagios server's local time and say so in the API and UI, or store an explicit zone. Do not guess.

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

- [ ] A policy with quiet hours produces a valid `define timeperiod` block, and hosts, services and contacts reference it.
- [ ] With the default policy, generated `hosts.cfg` is byte-identical to the output before this change.
- [ ] Saving an invalid policy (bad time, overlap, unknown option letter, interval out of range) returns 400 with a message that names the field.
- [ ] A stale `version` returns 409. A policy that Nagios rejects is rolled back and returns 422 with Nagios's message.
- [ ] Without `settings.system` the API returns 403.
- [ ] On a lab appliance, a forced state change inside a quiet window sends no notification, and the same change outside it does.
- [ ] Existing hosts, services, contacts and Check interval behavior are unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; the user-facing text is delivered by Issue #1.2.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: template rendering for default, quiet-hour and option-subset policies; validation edge cases (midnight crossing, overlap, empty windows, bad letters).
- API: 400, 403, 409 and 422 paths with a mocked `regenerate_and_apply_config_status()`.
- Migration: upgrade creates one default row, downgrade removes it (follow `server/tests/unit/test_upgrade_rehearsal.py` and `test_custom_check_migration.py`).
- Regression: `test_create_host_cfg.py` and `test_settings_permissions.py` still pass unchanged.
- Lab (VM, record in `docs/test-runs/`): `nagios -v` accepts the config and a forced CRITICAL inside and outside the window behaves as expected.

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
