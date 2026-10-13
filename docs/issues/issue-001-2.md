### Issue #1.2 — Web-Interface Refinement Add Notification Policy Settings and Correct the Notifications Toggle Label

**Category:** Web-Interface

**Work Type:** Refinement

**Priority:** High

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Time-Based Alerting; Contact Notifications

**Dependencies:** [Issue #1.1](issue-001-1.md)

**Plan reference:** Issue #1 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #1. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

Administrators have no screen for notification timing, and the existing "Notifications" setting is misleading. It only hides or shows the header bell (`Header.tsx` reads `savedSettings.notifications`). No server code applies it to Nagios, so switching it off does not stop alert email.

**Out of scope for this issue:**

- The policy API and Nagios rendering (Issue #1.1).
- Wiring the toggle to Nagios `enable_notifications`; that needs Issue #19.1 and is a separate decision.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `client/src/pages/SettingsPage.tsx` renders tabs (General, Security, System, Network Discovery, Plugins, Email) filtered by `SETTINGS_TAB_PERMISSIONS` in `client/src/lib/pageAccess.ts`.
- `client/src/components/settings/GeneralSettings.tsx` and `SystemSettings.tsx` hold the existing toggles, with `SettingsCard.tsx`, `SettingsToggle.tsx` and `SettingsSelect.tsx` as shared controls.
- `client/src/contexts/SystemSettingsContext.tsx` and `client/src/types/settings.tsx` carry the settings object, including `notifications`.
- `client/src/components/settings/EmailSettings.tsx` is the closest example of a settings tab with its own API client (`client/src/lib/smtpSettingsApi.ts`).
- `client/src/components/layout/Header.tsx` (around line 270) uses `savedSettings.notifications && hasPermission('system.notifications')`.

#### C. Required Changes

**Frontend / Web Interface**

1. Relabel the existing toggle so it states what it does, for example "Show notification bell in the header", and add help text that email alerts are controlled elsewhere. Keep the setting's stored name and API field unchanged.
2. Add a "Notification policy" card *(proposed `client/src/components/settings/NotificationPolicySettings.tsx`)* to the Email tab or the System tab. Fields: quiet-hour windows (add and remove rows with weekday, start and end), host and service notification option checkboxes with plain names (Down, Unreachable, Recovery, Flapping, Scheduled downtime; Warning, Unknown, Critical, Recovery, Flapping, Scheduled downtime), and the renotify interval.
3. Add an API client *(proposed `client/src/lib/notificationPolicyApi.ts`)* and TypeScript types *(proposed `client/src/types/notificationPolicy.ts`)* using the shared client in `client/src/lib/api.ts`, converting wire names in `types/`.
4. Validate in the form before sending (time format, start before end, overlaps, interval range) and show the server's message on 400, 409 (offer to reload) and 422 (show Nagios's message). Show loading, saving and success states.
5. Show or hide the card by the same permission as the API (`settings.system`) and add it to `SETTINGS_TAB_PERMISSIONS` if a new tab is used.

#### D. Implementation Guidelines

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

- [ ] The old toggle's label and help text say it controls the header bell only.
- [ ] A user with `settings.system` can add, edit and remove quiet-hour windows and change options and interval, and the values reload after a refresh.
- [ ] Invalid input is blocked in the form with a message naming the field, and a server 400, 409 or 422 shows the server's message.
- [ ] A user without the permission does not see the card and cannot reach it by URL.
- [ ] The existing General and System settings tests still pass.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Settings help text in the page, plus a short note under the settings section of the manual.
- [ ] Evidence that the functionality works: `scripts/verify.sh frontend` output attached to the pull request.

#### G. Testing and Verification

- Frontend (Vitest and Testing Library): form validation, add and remove windows, save success, 409 and 422 display, permission hiding. Model on `client/src/test/EmailSettings.test.tsx` and `SystemSettingsConflict.test.tsx`.
- Regression: `LayoutSettings.test.tsx`, `PageAccess.test.tsx`.
- Manual (lab): save a policy through the browser and confirm Issue #1.1's Nagios result.

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
