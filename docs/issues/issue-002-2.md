### Issue #2.2 — System Refinement Allow Generic SMTP Relay and Report Failed Notification Mail

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Contact Notifications

**Dependencies:** [Issue #2.1](issue-002-1.md) (only for implicit TLS)

**Plan reference:** Issue #2 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #2. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

Mail delivery works only through Gmail. `validate_smtp_settings()` rejects any provider, host, port or TLS mode other than the Gmail preset, even though the root helper already accepts any host and port.

When mail cannot be sent, nothing in PinPoint says so. A lab appliance with an empty `/etc/msmtprc` logged `send-mail: account default not found` and exit code 78 for a real notification, visible only in `nagios.log`.

**Out of scope for this issue:**

- Microsoft 365 and OAuth (declared out of scope in `Implementation_Status.md`).
- Plain SMTP without encryption.
- The settings form (Issue #2.3).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/smtp_settings.py`: `PRESETS = {"gmail": GMAIL}`, `validate_smtp_settings()`, `get_smtp_settings()`, the helper call (`HELPER_PATH`, `sudo -n`), password encryption through `server/app/secrets_store.py`, and the `smtplib` test email.
- `server/app/api/system/smtp_settings.py`: the settings routes under permission `settings.email`.
- `SmtpSettings` model in `server/app/system_models.py`; migration `server/migrations/versions/b6e1d4a8c2f9_smtp_settings.py`.
- Tests: `server/tests/unit/test_smtp_settings.py`, `test_email_alerts.py`.
- `/usr/local/nagios/var/nagios.log` is world-readable on the lab appliance (`-rw-r--r--`), and it contains Nagios's own notification-failure lines.
- `server/app/nagios/notifications.py` reads `archivejson.cgi`; archive events record that a notification was *attempted*, not that mail left the host (not verified for failures, *further investigation required*).

#### C. Required Changes

**Backend / System**

1. Add a `custom` provider preset beside `gmail` in `server/app/smtp_settings.py` that accepts a validated host name or address, a port from 1 to 65535 and a TLS mode of `starttls` (and `tls` only after Issue #2.1 ships). Keep Gmail's fixed values and its messages unchanged.
2. Extend `validate_smtp_settings()` to validate the custom fields with the same character rules the helper enforces (host regex, printable ASCII, lengths), so the web tier never sends the helper a value it will refuse.
3. Add a column for the provider's host, port and TLS mode if the `SmtpSettings` model does not already hold them (it stores `Provider`, `Host`, `Port`, `Tls`; confirm in `system_models.py`) and add a migration only if a new column is needed.
4. Add a failed-notification reader *(proposed, `server/app/nagios/mail_failures.py`)* that scans a bounded tail of `nagios.log` for the `wproc` failure lines of the notification commands and returns the most recent failure time and reason. Cap the bytes read, tolerate a missing or unreadable file, and never return message bodies or addresses beyond the contact name.
5. Expose the result on `GET /api/system/smtp-settings` as a new field (for example `lastMailFailure`) or on a small new route under `settings.email`. Document the field in the route docstring.
6. Keep the password rules: never returned, never logged.

#### D. Implementation Guidelines

- Keep the Gmail path byte-for-byte behaviorally identical. All existing SMTP tests must pass unmodified.
- Parsing `nagios.log` is an assumption to verify on a lab appliance first: confirm the exact failure line format and that the `pinpoint` service user can read the file.

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

- [ ] A custom host, port and `starttls` can be saved, written through the helper and used for a test email.
- [ ] An invalid host, port or TLS mode returns 400 with a message naming the field, and never reaches the helper.
- [ ] The Gmail settings and test email behave exactly as before.
- [ ] After a notification fails because mail is not configured, the API reports a last-failure time and reason within one poll cycle. With no failures the field is empty.
- [ ] A missing or unreadable `nagios.log` yields an empty indicator, not an error.
- [ ] No password appears in any response or log.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Email settings help text and the user guide section on mail.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Unit: custom preset validation (valid, bad host, bad port, bad TLS, unsupported `tls`), unchanged Gmail cases.
- Unit: the log reader with sample `wproc` failure text, a truncated file, a missing file and a large file (byte cap).
- API: `settings.email` permission, 400 and success paths with the helper mocked.
- Lab (record in `docs/test-runs/`): configure a custom relay against a local sink, then clear it and confirm the failure indicator after a forced notification.

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
