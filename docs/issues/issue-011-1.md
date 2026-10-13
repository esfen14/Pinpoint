### Issue #11.1 — Installer Refinement Set an Explicit Journald Size Limit for PinPoint Logs

**Category:** Installer

**Work Type:** Refinement

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Automatic Log Rotation

**Dependencies:** None

**Plan reference:** Issue #11 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #11. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** The installer code location is not in this repository, *further investigation required*.

#### A. Problem Description

PinPoint's Gunicorn logs go to stdout and therefore to journald, which rotates them under its defaults. On a lab appliance `journald.conf` has no overrides, so the size cap is whatever the OS decides rather than a deliberate limit for a small appliance disk.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Verified on a lab appliance: `pinpoint-gunicorn.service` uses `--access-logfile -` and `--error-logfile -`, `journald.conf` has no non-comment lines, and journald holds about 40 MB.
- Nagios rotates its own log daily (`log_rotation_method=d`, archives in `/usr/local/nagios/var/archives`).
- Installer logs `/var/log/pinpoint-*.log` are written at install time and are not in `/etc/logrotate.d`.

#### C. Required Changes

**Installer / Deployment**

1. Install a drop-in (for example `/etc/systemd/journald.conf.d/pinpoint.conf`) setting `SystemMaxUse` and `MaxRetentionSec` to documented values, and restart journald.
2. Add the installer logs to a logrotate rule, or document why they are exempt.
3. Make the upgrade idempotent and keep any administrator-edited journald settings.

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

- [ ] A fresh install has the drop-in with the documented limits and `journalctl --disk-usage` stays within them.
- [ ] An upgrade does not overwrite an administrator's own journald settings.
- [ ] Installer logs are rotated or the exemption is documented.

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

- VM-lab: fresh install, check the drop-in and disk usage after generating log volume (record in `docs/test-runs/`).
- Upgrade test with a pre-existing custom `journald.conf.d` file.

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
