### Issue #2.1 — Installer Refinement Allow Implicit TLS in the SMTP Helper for Non-Gmail Relays

**Category:** Installer

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Contact Notifications

**Dependencies:** None

**Plan reference:** Issue #2 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #2. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Conditional. Only needed if the team decides to support a relay that requires implicit TLS (port 465). STARTTLS relays work without any installer change. The helper is maintained in the installer repository, which is outside this repository, so the exact code location there is *further investigation required*.

#### A. Problem Description

`/usr/local/sbin/pinpoint-apply-smtp` writes `/etc/msmtprc` from a JSON object. It accepts any valid host and port but only the TLS mode `starttls` (`TLS_MODES = {"starttls"}`). A relay that needs implicit TLS cannot be configured, even after PinPoint's own validation is relaxed (Issue #2.2).

**Out of scope for this issue:**

- Plain (unencrypted) SMTP. The helper deliberately refuses it because the login is always sent.
- PinPoint application changes (Issue #2.2).

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Verified by reading the installed helper on a lab appliance: it requires exactly the fields `host`, `port`, `tls`, `username`, `password`, `sender`, rejects anything else with exit code 1, writes `/etc/msmtprc` atomically as `root:nagios` mode 0640, and writes `tls on` plus `tls_starttls on`.
- The helper is run by the web service through `sudo -n` (`server/app/smtp_settings.py`, `HELPER_PATH`). The sudoers rule allows only that helper and `systemctl reload nagios`.
- Source of the helper in the installer repository: not present here, *further investigation required*.

#### C. Required Changes

**Installer / Deployment**

1. In the installer repository, extend `TLS_MODES` to include an implicit-TLS value (for example `tls`) and write `tls on` with `tls_starttls off` for it. Keep `starttls` as the default and keep rejecting any mode that sends the password unencrypted.
2. Keep the exact-fields, atomic-write, ownership and mode behavior and the no-password-in-messages rule unchanged.
3. Ship the change through the installer's normal update path so existing appliances receive it, and confirm `/etc/msmtprc` of an existing STARTTLS configuration is not rewritten by the upgrade.

#### D. Implementation Guidelines

- Do not change the JSON field set unless PinPoint's call in `server/app/smtp_settings.py` is changed in the same release, because the helper rejects unknown fields.

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

- [ ] The helper accepts `tls: "tls"` (implicit) and writes a valid msmtp account for it, and still accepts `starttls`.
- [ ] Any other `tls` value, including a plain-text mode, is rejected with exit code 1 and no password in the message.
- [ ] An existing appliance configured for STARTTLS keeps working after upgrade without re-entering the password.
- [ ] File ownership and mode of `/etc/msmtprc` remain `root:nagios` and 0640.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Installer tests or a scripted check in the installer repository (this repository's lab only verifies the result).
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Installer-side script tests for each valid and invalid `tls` value and for the exact-field check.
- VM-lab run (`scripts/vmlab`, recorded under `docs/test-runs/`): save an implicit-TLS configuration and send the PinPoint test email through a local TLS sink.
- Upgrade test: install the previous helper, configure STARTTLS, upgrade, send a test email.

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
