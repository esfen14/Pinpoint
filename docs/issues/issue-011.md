### Issue #11 — System Refinement Set Journald Limit, Report Storage Usage and Add Nagios Log Tab

**Category:** System

**Work Type:** Refinement

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Automatic Log Rotation; Automatic Log Rotation; Log File Access

**Dependencies:** None

**Plan reference:** Issue #11 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 11.1 (Installer):** The installer code location is not in this repository, *further investigation required*.

#### A. Problem Description

**Part 11.1 (Installer) — Installer Refinement Set an Explicit Journald Size Limit for PinPoint Logs**

PinPoint's Gunicorn logs go to stdout and therefore to journald, which rotates them under its defaults. On a lab appliance `journald.conf` has no overrides, so the size cap is whatever the OS decides rather than a deliberate limit for a small appliance disk.

**Part 11.2 (System) — System Refinement Add Log and Database Storage Usage and a Read-Only Nagios Log Route**

Administrators cannot see how much disk PinPoint's databases, backups and logs use, so a filling disk is invisible until something fails. The raw Nagios log is also not viewable in PinPoint (System Logs shows PinPoint's own audit categories only), although Nagios Core users expect log access.

**Part 11.3 (Web-Interface) — Web-Interface Refinement Show Storage Usage and Add a Nagios Log Tab to System Logs**

Once the backend reports storage and serves the Nagios log, administrators need to see them. Today the Dashboard shows monitored-server resources only, and System Logs has no Nagios log.

**Out of scope for this issue:**

- Replacing Nagios's own log rotation. The engine owns it.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 11.1: Verified on a lab appliance: `pinpoint-gunicorn.service` uses `--access-logfile -` and `--error-logfile -`, `journald.conf` has no non-comment lines, and journald holds about 40 MB.
- Part 11.1: Nagios rotates its own log daily (`log_rotation_method=d`, archives in `/usr/local/nagios/var/archives`).
- Part 11.1: Installer logs `/var/log/pinpoint-*.log` are written at install time and are not in `/etc/logrotate.d`.
- Part 11.2: `server/app/api/system/dashboard.py` → `GET /api/system/dashboard/status` returns Nagios process state and the monitored server's resources from check results (`statistics.py` → `nagios_server_resources()`: load, disk mounts and swap from `check_load`, `check_disk`, `check_swap`). It does not report PinPoint's own storage.
- Part 11.2: `server/app/automation.py` → `backup_databases()` keeps `DATABASE_BACKUP_KEEP` (7) folders under `DATABASE_BACKUP_DIR` (`server/config.py`). `database_file_paths()` lists the SQLite files.
- Part 11.2: `server/app/scheduler.py` → `_purge_old_data()` applies the retention settings.
- Part 11.2: `server/app/api/system/log.py` serves the five PinPoint log categories under `system.logs`.
- Part 11.2: On a lab appliance `/usr/local/nagios/var/nagios.log` is world-readable.
- Part 11.3: `client/src/components/dashboard/ResourceUtilizationSection.tsx` and `NetworkStatusOverview.tsx` show status data.
- Part 11.3: `client/src/pages/SystemLogsPage.tsx` shows five log categories and uses `client/src/utils/exportData.ts` and `components/shared/ExportMenu.tsx`.
- Part 11.3: `client/src/types/log.ts` holds the log types.

#### C. Required Changes

**Backend / System**

1. **Part 11.2 (System):** Add a helper *(proposed, `server/app/storage_usage.py`)* returning the size of each database file, the backup folder, the Nagios archive folder, and free space of the filesystem that holds them, using `os.stat` and `shutil.disk_usage`. Tolerate missing paths.
2. **Part 11.2 (System):** Expose it on a new route or as extra fields on `GET /api/system/dashboard/status`, documented in the docstring, under `system.dashboard`.
3. **Part 11.2 (System):** Add `GET /api/system/log/nagios?lines=&after=` *(proposed, in `log.py`)* under `system.logs` that returns a bounded tail of `nagios.log`: cap lines (for example 500) and bytes, read from the end without loading the file, and never accept a path from the request.
4. **Part 11.2 (System):** Redact anything that could be a secret in returned lines (for example command arguments after `check_command=`), and document that the log can contain hostnames and addresses.

**Frontend / Web Interface**

1. **Part 11.3 (Web-Interface):** Add a compact storage card to the Dashboard status area showing database, backup and archive sizes and free disk, with a warning style below a threshold stated in the UI text.
2. **Part 11.3 (Web-Interface):** Add a "Nagios log" tab to `SystemLogsPage.tsx` that shows the bounded tail, with a refresh control and a clear note that only the latest lines are shown. Reuse the export menu if it fits.
3. **Part 11.3 (Web-Interface):** Add types and API calls and handle loading, empty, error and 403 states.

**Installer / Deployment**

1. **Part 11.1 (Installer):** Install a drop-in (for example `/etc/systemd/journald.conf.d/pinpoint.conf`) setting `SystemMaxUse` and `MaxRetentionSec` to documented values, and restart journald.
2. **Part 11.1 (Installer):** Add the installer logs to a logrotate rule, or document why they are exempt.
3. **Part 11.1 (Installer):** Make the upgrade idempotent and keep any administrator-edited journald settings.

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

- [ ] **Part 11.1 (Installer):** A fresh install has the drop-in with the documented limits and `journalctl --disk-usage` stays within them.
- [ ] **Part 11.1 (Installer):** An upgrade does not overwrite an administrator's own journald settings.
- [ ] **Part 11.1 (Installer):** Installer logs are rotated or the exemption is documented.
- [ ] **Part 11.2 (System):** The status data lists database, backup and archive sizes and free disk space, and handles missing paths without error.
- [ ] **Part 11.2 (System):** The Nagios log route returns at most the configured lines and bytes, newest last, and returns an empty list if the file is unreadable.
- [ ] **Part 11.2 (System):** The route cannot be used to read any other file.
- [ ] **Part 11.2 (System):** Both require login and the stated permission (403 otherwise).
- [ ] **Part 11.3 (Web-Interface):** The Dashboard shows storage sizes and free disk and a warning when space is low.
- [ ] **Part 11.3 (Web-Interface):** The Nagios log tab shows the latest lines, refreshes, and shows a clear state when the log is unavailable.
- [ ] **Part 11.3 (Web-Interface):** Users without `system.logs` or `system.dashboard` do not see the matching element.
- [ ] **Part 11.3 (Web-Interface):** Existing dashboard and logs tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Display_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes; Help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 11.1 (Installer):** VM-lab: fresh install, check the drop-in and disk usage after generating log volume (record in `docs/test-runs/`).
- **Part 11.1 (Installer):** Upgrade test with a pre-existing custom `journald.conf.d` file.
- **Part 11.2 (System):** Unit: size helper with temp files and missing paths; tail reader with small, large and unterminated files; redaction.
- **Part 11.2 (System):** API: permission and bounds (`lines` and `after` validation returns 400).
- **Part 11.2 (System):** Security: path and parameter injection attempts.
- **Part 11.3 (Web-Interface):** Frontend: storage card states, log tab states, permission hiding.
- **Part 11.3 (Web-Interface):** Regression: `DashboardPage.test.tsx`.

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
