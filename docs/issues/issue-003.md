### Issue #3 — System Implementation Add Alert Contact Groups and Nagios Escalations With Management Screen

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Escalation Paths

**Dependencies:** [Issue #1](issue-001.md)

**Plan reference:** Issue #3 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 3.1 (System):** Coordinate with the already open GitHub issue #79 (per-host alert recipients). Do not start before #79's data model is decided, to avoid two competing recipient models.  
> **Part 3.2 (Web-Interface):** Same condition as Part 3.1.

#### A. Problem Description

**Part 3.1 (System) — System Implementation Add Alert Contact Groups and Nagios Escalation Rendering**

Every host and service notifies the single `system_users` contact group. There is no way to route an alert to different people by host or severity, and no escalation when a problem stays unacknowledged. Nagios Core provides this through contact groups and escalation objects, none of which PinPoint generates.

**Part 3.2 (Web-Interface) — Web-Interface Implementation Add Escalation Management Screen**

Once escalations exist in the backend, administrators need a screen to define who is notified after how many alerts. No such screen exists.

**Out of scope for this issue:**

- New notification channels.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 3.1: `server/app/network_discovery/create_host_cfg.py` (`_create_host_cfg_file()`): contacts are Active users with `Receive_Email_Alerts`; one group `system_users` (omitted if nobody qualifies) is the `contact_groups` of every host, service and server check.
- Part 3.1: `server/app/network_discovery/host_config_templates.py`: `_drop_empty_contact_groups()`, `create_contactgroup()`.
- Part 3.1: Templates `contactgroup.cfg.tpl`, `host.cfg.tpl`, `service.cfg.tpl`.
- Part 3.1: `Implementation_Status.md` lists "Per-host alert recipients (#79)" as the planned first step.
- Part 3.1: Account changes that affect a contact already rebuild the Nagios config (#80, verified in `Implementation_Status.md`).
- Part 3.2: `client/src/pages/SettingsPage.tsx` and its tab components are the established place for system configuration.
- Part 3.2: `client/src/pages/ManageRolesPage.tsx` and `ManageAccountsPage.tsx` already list users and show the email-alert opt-in.
- Part 3.2: `client/src/lib/api.ts` is the shared API client; `client/src/lib/pageAccess.ts` holds page and tab permissions.

#### C. Required Changes

**Backend / System**

1. **Part 3.1 (System):** After #79 lands, add an escalation model *(proposed, `server/app/system_models.py`)*: first notification, last notification, interval in minutes, escalation contact group, and a scope (all hosts and services, or a host). Add the migration.
2. **Part 3.1 (System):** Add templates `hostescalation.cfg.tpl` and `serviceescalation.cfg.tpl` *(proposed)* and render escalations in `_create_host_cfg_file()` only for groups that have members, since Nagios rejects an empty contact group.
3. **Part 3.1 (System):** Add routes *(proposed, `server/app/api/system/escalations.py`)* to list, create, update and delete escalations with route docstrings, validation (first less than or equal to last, interval bounds, the group exists and has members) and `settings.system` permission, applying through `regenerate_and_apply_config_status()` with rollback on failure.
4. **Part 3.1 (System):** Ensure a user deactivation or opt-out that empties an escalation group removes that escalation from the generated config instead of failing the apply.

**Frontend / Web Interface**

1. **Part 3.2 (Web-Interface):** Add an "Escalations" card *(proposed `client/src/components/settings/EscalationSettings.tsx`)* to the System or Email settings tab. Rows show the group, first and last notification count, interval, and a delete action; an add form creates one.
2. **Part 3.2 (Web-Interface):** Add API client and types *(proposed `client/src/lib/escalationApi.ts`, `client/src/types/escalation.ts`)*.
3. **Part 3.2 (Web-Interface):** Disable the form and explain why when no group has members. Show the server's 400 and 422 messages. Confirm before deleting.
4. **Part 3.2 (Web-Interface):** Gate the card by `settings.system` and update `pageAccess.ts` if a new tab is added.

#### D. Implementation Guidelines

- Reuse the group-building code that #79 introduces. Do not add a second way to compute recipients.

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

- [ ] **Part 3.1 (System):** A saved escalation appears as a valid `define serviceescalation` or `hostescalation` block and Nagios validates the config.
- [ ] **Part 3.1 (System):** An escalation whose group has no eligible member is not written, and saving it explains why.
- [ ] **Part 3.1 (System):** Invalid values (first greater than last, unknown group, out-of-range interval) return 400.
- [ ] **Part 3.1 (System):** Deleting an escalation removes it from the live config.
- [ ] **Part 3.1 (System):** With no escalations defined, generated config is unchanged.
- [ ] **Part 3.2 (Web-Interface):** An administrator can add, edit and delete an escalation and sees it after reload.
- [ ] **Part 3.2 (Web-Interface):** Invalid input is blocked in the form and server errors are shown.
- [ ] **Part 3.2 (Web-Interface):** Users without permission do not see the card.
- [ ] **Part 3.2 (Web-Interface):** The settings page tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the card.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 3.1 (System):** Unit: template rendering, empty-group handling, validation.
- **Part 3.1 (System):** API: permission, 400 and rollback-on-422 paths with the apply mocked.
- **Part 3.1 (System):** Lab: two contacts, an unacknowledged CRITICAL, and the second contact is notified after the configured count (record in `docs/test-runs/`).
- **Part 3.1 (System):** Regression: `test_create_host_cfg.py`, `test_email_alerts.py`.
- **Part 3.2 (Web-Interface):** Frontend: add, edit, delete, validation, empty-group state, permission hiding.
- **Part 3.2 (Web-Interface):** Regression: `PageAccess.test.tsx`, `LayoutSettings.test.tsx`.

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
