### Issue #1 — System Implementation Add Configurable Notification Policy With Nagios Timeperiods and Settings Screen

**Category:** System

**Work Type:** Implementation

**Priority:** High

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Time-Based Alerting; Contact Notifications

**Dependencies:** None

**Plan reference:** Issue #1 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 1.1 (System) — System Implementation Add Notification Policy Model and Nagios Timeperiod Rendering**

Notification timing is fixed in the Nagios templates PinPoint generates. Every host and contact uses the `24x7` period, the notification options are fixed, and the renotify interval is fixed at 30 minutes. An administrator cannot set quiet hours, choose which states notify, or change how often a problem renotifies.

Nagios Core supports time-based alerting through timeperiod objects and notification options. PinPoint generates the hosts, services and contacts but never generates a timeperiod, so the capability cannot be used.

**Part 1.2 (Web-Interface) — Web-Interface Refinement Add Notification Policy Settings and Correct the Notifications Toggle Label**

Administrators have no screen for notification timing, and the existing "Notifications" setting is misleading. It only hides or shows the header bell (`Header.tsx` reads `savedSettings.notifications`). No server code applies it to Nagios, so switching it off does not stop alert email.

**Out of scope for this issue:**

- Escalations (Issue #3) and per-host recipients (open GitHub issue #79).
- Any new notification channel.
- Wiring the toggle to Nagios `enable_notifications`; that needs Issue #19 and is a separate decision.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 1.1: `server/app/network_discovery/templates/contact_template.cfg.tpl` hardcodes `service_notification_period 24x7`, `host_notification_period 24x7`, options `w,u,c,r,f,s` and `d,u,r,f,s`, and the two email commands.
- Part 1.1: `server/app/network_discovery/templates/host.cfg.tpl` hardcodes `notification_interval 30` and `notification_period 24x7`. `service.cfg.tpl` has no notification fields.
- Part 1.1: `server/app/network_discovery/host_config_templates.py`: `create_host()`, `create_service()` and `check_interval()` render the templates. `check_interval()` already reads a system setting, which is the pattern to follow.
- Part 1.1: `server/app/network_discovery/create_host_cfg.py`: `_create_host_cfg_file()` writes contacts (Active users with `Receive_Email_Alerts`) and the `system_users` group. `regenerate_and_apply_config_status()` validates with the Nagios binary and applies or rolls back.
- Part 1.1: `server/app/api/system/settings.py` shows the apply-and-rollback pattern for `Check_Interval` (flush, regenerate, rollback and 422 on failure), `FIELD_PERMISSIONS` and `PERMISSION_LABELS`.
- Part 1.1: `server/app/system_models.py`: `SystemSettings` (singleton, `Version` and `Updated_By`). Live check on a VM appliance: Nagios loads the stock `timeperiods.cfg` (including `24x7`) through `cfg_file`.
- Part 1.2: `client/src/pages/SettingsPage.tsx` renders tabs (General, Security, System, Network Discovery, Plugins, Email) filtered by `SETTINGS_TAB_PERMISSIONS` in `client/src/lib/pageAccess.ts`.
- Part 1.2: `client/src/components/settings/GeneralSettings.tsx` and `SystemSettings.tsx` hold the existing toggles, with `SettingsCard.tsx`, `SettingsToggle.tsx` and `SettingsSelect.tsx` as shared controls.
- Part 1.2: `client/src/contexts/SystemSettingsContext.tsx` and `client/src/types/settings.tsx` carry the settings object, including `notifications`.
- Part 1.2: `client/src/components/settings/EmailSettings.tsx` is the closest example of a settings tab with its own API client (`client/src/lib/smtpSettingsApi.ts`).
- Part 1.2: `client/src/components/layout/Header.tsx` (around line 270) uses `savedSettings.notifications && hasPermission('system.notifications')`.

#### C. Required Changes

**Backend / System**

1. **Part 1.1 (System):** Add a singleton `NotificationPolicy` model *(proposed, `server/app/system_models.py`)* holding: quiet-hour windows (weekday, start `HH:MM`, end `HH:MM`), host notification options (subset of `d,u,r,f,s`), service notification options (subset of `w,u,c,r,f,s`), and the renotify interval in minutes (bounded, for example 0 to 1440). Add `Version` and `Updated_By` like `SystemSettings`.
2. **Part 1.1 (System):** Add a migration (`flask db migrate --multidb`) that creates the table and seeds one row whose values reproduce today's behavior exactly (`24x7`, current options, 30 minutes, no quiet hours).
3. **Part 1.1 (System):** Add a `timeperiod.cfg.tpl` template *(proposed)* and render one timeperiod, named by a fixed constant (for example `pinpoint_notify`), covering the allowed hours as the complement of the quiet windows. Emit nothing new when no quiet hours are set.
4. **Part 1.1 (System):** Parameterize `contact_template.cfg.tpl`, `host.cfg.tpl` and `service.cfg.tpl` with the period, options and interval. Add notification fields to `service.cfg.tpl`. Update `create_contact_template()`, `create_host()` and `create_service()` accordingly.
5. **Part 1.1 (System):** Add `GET /api/system/notification-policy` and `PUT /api/system/notification-policy` *(proposed, new `server/app/api/system/notification_policy.py`, registered in `server/app/api/system/__init__.py`)* with route docstrings, optimistic `version` handling (409 on a stale version, as for system settings) and a login plus `settings.system` permission check.
6. **Part 1.1 (System):** On save, flush, call `regenerate_and_apply_config_status()`, and on `failed` roll back and return 422 with the message, exactly as the Check interval does. Write a Configuration Change log entry when audit logging is on.
7. **Part 1.1 (System):** Validate every value on the server: weekday names from a fixed set, `HH:MM` 24-hour times, `start` before `end`, no overlapping windows, option letters from the allowed sets, and interval bounds. Never put user text into the Nagios config.

**Frontend / Web Interface**

1. **Part 1.2 (Web-Interface):** Relabel the existing toggle so it states what it does, for example "Show notification bell in the header", and add help text that email alerts are controlled elsewhere. Keep the setting's stored name and API field unchanged.
2. **Part 1.2 (Web-Interface):** Add a "Notification policy" card *(proposed `client/src/components/settings/NotificationPolicySettings.tsx`)* to the Email tab or the System tab. Fields: quiet-hour windows (add and remove rows with weekday, start and end), host and service notification option checkboxes with plain names (Down, Unreachable, Recovery, Flapping, Scheduled downtime; Warning, Unknown, Critical, Recovery, Flapping, Scheduled downtime), and the renotify interval.
3. **Part 1.2 (Web-Interface):** Add an API client *(proposed `client/src/lib/notificationPolicyApi.ts`)* and TypeScript types *(proposed `client/src/types/notificationPolicy.ts`)* using the shared client in `client/src/lib/api.ts`, converting wire names in `types/`.
4. **Part 1.2 (Web-Interface):** Validate in the form before sending (time format, start before end, overlaps, interval range) and show the server's message on 400, 409 (offer to reload) and 422 (show Nagios's message). Show loading, saving and success states.
5. **Part 1.2 (Web-Interface):** Show or hide the card by the same permission as the API (`settings.system`) and add it to `SETTINGS_TAB_PERMISSIONS` if a new tab is used.

#### D. Implementation Guidelines

- The default policy must render config that is identical to today's, so the existing `server/tests/unit/test_create_host_cfg.py` expectations hold.
- A time zone is needed to interpret quiet hours. Use the Nagios server's local time and say so in the API and UI, or store an explicit zone. Do not guess.
- Do not rename the `notifications` field in `types/settings.tsx` or the API. Only change the user-visible label and help text.

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

- [ ] **Part 1.1 (System):** A policy with quiet hours produces a valid `define timeperiod` block, and hosts, services and contacts reference it.
- [ ] **Part 1.1 (System):** With the default policy, generated `hosts.cfg` is byte-identical to the output before this change.
- [ ] **Part 1.1 (System):** Saving an invalid policy (bad time, overlap, unknown option letter, interval out of range) returns 400 with a message that names the field.
- [ ] **Part 1.1 (System):** A stale `version` returns 409. A policy that Nagios rejects is rolled back and returns 422 with Nagios's message.
- [ ] **Part 1.1 (System):** Without `settings.system` the API returns 403.
- [ ] **Part 1.1 (System):** On a lab appliance, a forced state change inside a quiet window sends no notification, and the same change outside it does.
- [ ] **Part 1.1 (System):** Existing hosts, services, contacts and Check interval behavior are unchanged.
- [ ] **Part 1.2 (Web-Interface):** The old toggle's label and help text say it controls the header bell only.
- [ ] **Part 1.2 (Web-Interface):** A user with `settings.system` can add, edit and remove quiet-hour windows and change options and interval, and the values reload after a refresh.
- [ ] **Part 1.2 (Web-Interface):** Invalid input is blocked in the form with a message naming the field, and a server 400, 409 or 422 shows the server's message.
- [ ] **Part 1.2 (Web-Interface):** A user without the permission does not see the card and cannot reach it by URL.
- [ ] **Part 1.2 (Web-Interface):** The existing General and System settings tests still pass.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Settings help text in the page, plus a short note under the settings section of the manual.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 1.1 (System):** Unit: template rendering for default, quiet-hour and option-subset policies; validation edge cases (midnight crossing, overlap, empty windows, bad letters).
- **Part 1.1 (System):** API: 400, 403, 409 and 422 paths with a mocked `regenerate_and_apply_config_status()`.
- **Part 1.1 (System):** Migration: upgrade creates one default row, downgrade removes it (follow `server/tests/unit/test_upgrade_rehearsal.py` and `test_custom_check_migration.py`).
- **Part 1.1 (System):** Regression: `test_create_host_cfg.py` and `test_settings_permissions.py` still pass unchanged.
- **Part 1.1 (System):** Lab (VM, record in `docs/test-runs/`): `nagios -v` accepts the config and a forced CRITICAL inside and outside the window behaves as expected.
- **Part 1.2 (Web-Interface):** Frontend (Vitest and Testing Library): form validation, add and remove windows, save success, 409 and 422 display, permission hiding. Model on `client/src/test/EmailSettings.test.tsx` and `SystemSettingsConflict.test.tsx`.
- **Part 1.2 (Web-Interface):** Regression: `LayoutSettings.test.tsx`, `PageAccess.test.tsx`.
- **Part 1.2 (Web-Interface):** Manual (lab): save a policy through the browser and confirm Part 1.1's Nagios result.

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
