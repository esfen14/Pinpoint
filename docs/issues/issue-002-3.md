### Issue #2.3 — Web-Interface Refinement Add Relay Selection and Mail Failure Notice to Email Settings

**Category:** Web-Interface

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Contact Notifications

**Dependencies:** [Issue #2.2](issue-002-2.md)

**Plan reference:** Issue #2 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #2. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

The Email tab only offers Gmail and shows no sign that notification mail is failing. Once the backend accepts other relays and reports failures (Issue #2.2), administrators need to choose a relay and see problems.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `client/src/components/settings/EmailSettings.tsx` (about 287 lines) renders the Gmail form and test email, with `client/src/lib/smtpSettingsApi.ts` and `client/src/types/smtpSettings.ts`.
- Tests: `client/src/test/EmailSettings.test.tsx`.
- `client/src/pages/SettingsPage.tsx` shows the tab by `settings.email`.

#### C. Required Changes

**Frontend / Web Interface**

1. Add a provider selector (Gmail, Other SMTP relay). For Gmail keep today's fields and help text. For the relay show host, port and TLS mode, and keep the password field's "leave blank to keep" behavior.
2. Extend `types/smtpSettings.ts` and `smtpSettingsApi.ts` with the new fields and the last-failure field.
3. Show a visible notice on the Email tab when `lastMailFailure` is present (time and reason) with a link to run the test email. Clear it when the field is empty.
4. Validate host, port and TLS before sending and show the server's 400 message. Keep the existing success, error and loading states.

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

- [ ] Choosing Gmail shows exactly the current form and saves the same request body as today.
- [ ] Choosing a relay shows host, port and TLS fields, validates them, and saves.
- [ ] When the API reports a mail failure the tab shows its time and reason, and shows nothing when there is none.
- [ ] No password is ever displayed or kept in browser storage.
- [ ] The existing EmailSettings tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the tab.
- [ ] Evidence that the functionality works: `scripts/verify.sh frontend` output attached to the pull request.

#### G. Testing and Verification

- Frontend: provider switch, validation, save, failure notice shown and hidden, password never rendered. Extend `EmailSettings.test.tsx`.
- Regression: `PageAccess.test.tsx`.

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
