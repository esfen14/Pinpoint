### Issue #2 — System Refinement Broaden Notification Mail Delivery Beyond Gmail and Report Failed Mail

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Contact Notifications

**Dependencies:** None

**Plan reference:** Issue #2 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 2.1 (Installer):** Conditional. Only needed if the team decides to support a relay that requires implicit TLS (port 465). STARTTLS relays work without any installer change. The helper is maintained in the installer repository, which is outside this repository, so the exact code location there is *further investigation required*.

#### A. Problem Description

**Part 2.1 (Installer) — Installer Refinement Allow Implicit TLS in the SMTP Helper for Non-Gmail Relays**

`/usr/local/sbin/pinpoint-apply-smtp` writes `/etc/msmtprc` from a JSON object. It accepts any valid host and port but only the TLS mode `starttls` (`TLS_MODES = {"starttls"}`). A relay that needs implicit TLS cannot be configured, even after PinPoint's own validation is relaxed (Part 2.2).

**Part 2.2 (System) — System Refinement Allow Generic SMTP Relay and Report Failed Notification Mail**

Mail delivery works only through Gmail. `validate_smtp_settings()` rejects any provider, host, port or TLS mode other than the Gmail preset, even though the root helper already accepts any host and port.

When mail cannot be sent, nothing in PinPoint says so. A lab appliance with an empty `/etc/msmtprc` logged `send-mail: account default not found` and exit code 78 for a real notification, visible only in `nagios.log`.

**Part 2.3 (Web-Interface) — Web-Interface Refinement Add Relay Selection and Mail Failure Notice to Email Settings**

The Email tab only offers Gmail and shows no sign that notification mail is failing. Once the backend accepts other relays and reports failures (Part 2.2), administrators need to choose a relay and see problems.

**Out of scope for this issue:**

- Plain (unencrypted) SMTP. The helper deliberately refuses it because the login is always sent.
- Microsoft 365 and OAuth (declared out of scope in `Implementation_Status.md`).
- Plain SMTP without encryption.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 2.1: Verified by reading the installed helper on a lab appliance: it requires exactly the fields `host`, `port`, `tls`, `username`, `password`, `sender`, rejects anything else with exit code 1, writes `/etc/msmtprc` atomically as `root:nagios` mode 0640, and writes `tls on` plus `tls_starttls on`.
- Part 2.1: The helper is run by the web service through `sudo -n` (`server/app/smtp_settings.py`, `HELPER_PATH`). The sudoers rule allows only that helper and `systemctl reload nagios`.
- Part 2.1: Source of the helper in the installer repository: not present here, *further investigation required*.
- Part 2.2: `server/app/smtp_settings.py`: `PRESETS = {"gmail": GMAIL}`, `validate_smtp_settings()`, `get_smtp_settings()`, the helper call (`HELPER_PATH`, `sudo -n`), password encryption through `server/app/secrets_store.py`, and the `smtplib` test email.
- Part 2.2: `server/app/api/system/smtp_settings.py`: the settings routes under permission `settings.email`.
- Part 2.2: `SmtpSettings` model in `server/app/system_models.py`; migration `server/migrations/versions/b6e1d4a8c2f9_smtp_settings.py`.
- Part 2.2: Tests: `server/tests/unit/test_smtp_settings.py`, `test_email_alerts.py`.
- Part 2.2: `/usr/local/nagios/var/nagios.log` is world-readable on the lab appliance (`-rw-r--r--`), and it contains Nagios's own notification-failure lines.
- Part 2.2: `server/app/nagios/notifications.py` reads `archivejson.cgi`; archive events record that a notification was *attempted*, not that mail left the host (not verified for failures, *further investigation required*).
- Part 2.3: `client/src/components/settings/EmailSettings.tsx` (about 287 lines) renders the Gmail form and test email, with `client/src/lib/smtpSettingsApi.ts` and `client/src/types/smtpSettings.ts`.
- Part 2.3: Tests: `client/src/test/EmailSettings.test.tsx`.
- Part 2.3: `client/src/pages/SettingsPage.tsx` shows the tab by `settings.email`.

#### C. Required Changes

**Backend / System**

1. **Part 2.2 (System):** Add a `custom` provider preset beside `gmail` in `server/app/smtp_settings.py` that accepts a validated host name or address, a port from 1 to 65535 and a TLS mode of `starttls` (and `tls` only after Part 2.1 ships). Keep Gmail's fixed values and its messages unchanged.
2. **Part 2.2 (System):** Extend `validate_smtp_settings()` to validate the custom fields with the same character rules the helper enforces (host regex, printable ASCII, lengths), so the web tier never sends the helper a value it will refuse.
3. **Part 2.2 (System):** Add a column for the provider's host, port and TLS mode if the `SmtpSettings` model does not already hold them (it stores `Provider`, `Host`, `Port`, `Tls`; confirm in `system_models.py`) and add a migration only if a new column is needed.
4. **Part 2.2 (System):** Add a failed-notification reader *(proposed, `server/app/nagios/mail_failures.py`)* that scans a bounded tail of `nagios.log` for the `wproc` failure lines of the notification commands and returns the most recent failure time and reason. Cap the bytes read, tolerate a missing or unreadable file, and never return message bodies or addresses beyond the contact name.
5. **Part 2.2 (System):** Expose the result on `GET /api/system/smtp-settings` as a new field (for example `lastMailFailure`) or on a small new route under `settings.email`. Document the field in the route docstring.
6. **Part 2.2 (System):** Keep the password rules: never returned, never logged.

**Frontend / Web Interface**

1. **Part 2.3 (Web-Interface):** Add a provider selector (Gmail, Other SMTP relay). For Gmail keep today's fields and help text. For the relay show host, port and TLS mode, and keep the password field's "leave blank to keep" behavior.
2. **Part 2.3 (Web-Interface):** Extend `types/smtpSettings.ts` and `smtpSettingsApi.ts` with the new fields and the last-failure field.
3. **Part 2.3 (Web-Interface):** Show a visible notice on the Email tab when `lastMailFailure` is present (time and reason) with a link to run the test email. Clear it when the field is empty.
4. **Part 2.3 (Web-Interface):** Validate host, port and TLS before sending and show the server's 400 message. Keep the existing success, error and loading states.

**Installer / Deployment**

1. **Part 2.1 (Installer):** In the installer repository, extend `TLS_MODES` to include an implicit-TLS value (for example `tls`) and write `tls on` with `tls_starttls off` for it. Keep `starttls` as the default and keep rejecting any mode that sends the password unencrypted.
2. **Part 2.1 (Installer):** Keep the exact-fields, atomic-write, ownership and mode behavior and the no-password-in-messages rule unchanged.
3. **Part 2.1 (Installer):** Ship the change through the installer's normal update path so existing appliances receive it, and confirm `/etc/msmtprc` of an existing STARTTLS configuration is not rewritten by the upgrade.

#### D. Implementation Guidelines

- Do not change the JSON field set unless PinPoint's call in `server/app/smtp_settings.py` is changed in the same release, because the helper rejects unknown fields.
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

- [ ] **Part 2.1 (Installer):** The helper accepts `tls: "tls"` (implicit) and writes a valid msmtp account for it, and still accepts `starttls`.
- [ ] **Part 2.1 (Installer):** Any other `tls` value, including a plain-text mode, is rejected with exit code 1 and no password in the message.
- [ ] **Part 2.1 (Installer):** An existing appliance configured for STARTTLS keeps working after upgrade without re-entering the password.
- [ ] **Part 2.1 (Installer):** File ownership and mode of `/etc/msmtprc` remain `root:nagios` and 0640.
- [ ] **Part 2.2 (System):** A custom host, port and `starttls` can be saved, written through the helper and used for a test email.
- [ ] **Part 2.2 (System):** An invalid host, port or TLS mode returns 400 with a message naming the field, and never reaches the helper.
- [ ] **Part 2.2 (System):** The Gmail settings and test email behave exactly as before.
- [ ] **Part 2.2 (System):** After a notification fails because mail is not configured, the API reports a last-failure time and reason within one poll cycle. With no failures the field is empty.
- [ ] **Part 2.2 (System):** A missing or unreadable `nagios.log` yields an empty indicator, not an error.
- [ ] **Part 2.2 (System):** No password appears in any response or log.
- [ ] **Part 2.3 (Web-Interface):** Choosing Gmail shows exactly the current form and saves the same request body as today.
- [ ] **Part 2.3 (Web-Interface):** Choosing a relay shows host, port and TLS fields, validates them, and saves.
- [ ] **Part 2.3 (Web-Interface):** When the API reports a mail failure the tab shows its time and reason, and shows nothing when there is none.
- [ ] **Part 2.3 (Web-Interface):** No password is ever displayed or kept in browser storage.
- [ ] **Part 2.3 (Web-Interface):** The existing EmailSettings tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes; Email settings help text and the user guide section on mail; Help text on the tab.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 2.1 (Installer):** Installer-side script tests for each valid and invalid `tls` value and for the exact-field check.
- **Part 2.1 (Installer):** VM-lab run (`scripts/vmlab`, recorded under `docs/test-runs/`): save an implicit-TLS configuration and send the PinPoint test email through a local TLS sink.
- **Part 2.1 (Installer):** Upgrade test: install the previous helper, configure STARTTLS, upgrade, send a test email.
- **Part 2.2 (System):** Unit: custom preset validation (valid, bad host, bad port, bad TLS, unsupported `tls`), unchanged Gmail cases.
- **Part 2.2 (System):** Unit: the log reader with sample `wproc` failure text, a truncated file, a missing file and a large file (byte cap).
- **Part 2.2 (System):** API: `settings.email` permission, 400 and success paths with the helper mocked.
- **Part 2.2 (System):** Lab (record in `docs/test-runs/`): configure a custom relay against a local sink, then clear it and confirm the failure indicator after a forced notification.
- **Part 2.3 (Web-Interface):** Frontend: provider switch, validation, save, failure notice shown and hidden, password never rendered. Extend `EmailSettings.test.tsx`.
- **Part 2.3 (Web-Interface):** Regression: `PageAccess.test.tsx`.

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
