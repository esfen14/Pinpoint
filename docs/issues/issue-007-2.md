### Issue #7.2 — Web-Interface Implementation Add Remediation Actions Screen and Run Log

**Category:** Web-Interface

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Event Handlers; Proactive Resolution

**Dependencies:** [Issue #7.1](issue-007-1.md)

**Plan reference:** Issue #7 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #7. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Same condition as Issue #7.1.

#### A. Problem Description

Administrators need a safe place to define what runs when a service fails and to review every automated action. No such screen or log view exists.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `client/src/pages/SystemLogsPage.tsx` shows five audit categories from `api/system/log.py`.
- `client/src/pages/PluginsPage.tsx` and `components/plugin-manager/` show how per-plugin administrative actions and drawers are built.
- `client/src/lib/pageAccess.ts`, `components/layout/Sidebar.tsx`, `client/src/App.tsx` and `client/src/test/PageAccess.test.tsx` define navigation and permissions and must be updated together when a page is added.

#### C. Required Changes

**Frontend / Web Interface**

1. Add a "Remediation" area *(proposed page `client/src/pages/RemediationPage.tsx` with components in `client/src/components/remediation/`)* with an action list, an add and edit form generated from each action type's parameters, an enable switch, and the cooldown and hourly cap fields.
2. Add a run log table with filters (action, host, outcome, date), pagination and a detail drawer, showing skipped runs with their reason.
3. Add API client and types *(proposed `client/src/lib/remediationApi.ts`, `client/src/types/remediation.ts`)*.
4. Add the route, sidebar entry and page permission together, and make the form show a clear warning that actions run automatically.
5. Show loading, empty, error and 403 states, and the server's validation messages.

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

- [ ] A permitted user can create, edit, enable and disable an action and sees changes after reload.
- [ ] The run log lists runs with filters and pagination, including skipped ones.
- [ ] Users without the permission do not see the page in navigation and are blocked on direct access.
- [ ] Validation errors from the server are shown against the right field.
- [ ] Existing navigation and page-access tests pass after being updated for the new page.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Page help text and a short admin guide section.
- [ ] Evidence that the functionality works: `scripts/verify.sh frontend` output attached to the pull request.

#### G. Testing and Verification

- Frontend: form generation per type, validation, enable toggle, log filters, permission guard.
- Update `PageAccess.test.tsx` and `App.test.tsx` for the new route.

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
