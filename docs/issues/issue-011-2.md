### Issue #11.2 — System Refinement Add Log and Database Storage Usage and a Read-Only Nagios Log Route

**Category:** System

**Work Type:** Refinement

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Automatic Log Rotation; Log File Access

**Dependencies:** None

**Plan reference:** Issue #11 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #11. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

Administrators cannot see how much disk PinPoint's databases, backups and logs use, so a filling disk is invisible until something fails. The raw Nagios log is also not viewable in PinPoint (System Logs shows PinPoint's own audit categories only), although Nagios Core users expect log access.

**Out of scope for this issue:**

- Replacing Nagios's own log rotation. The engine owns it.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `server/app/api/system/dashboard.py` → `GET /api/system/dashboard/status` returns Nagios process state and the monitored server's resources from check results (`statistics.py` → `nagios_server_resources()`: load, disk mounts and swap from `check_load`, `check_disk`, `check_swap`). It does not report PinPoint's own storage.
- `server/app/automation.py` → `backup_databases()` keeps `DATABASE_BACKUP_KEEP` (7) folders under `DATABASE_BACKUP_DIR` (`server/config.py`). `database_file_paths()` lists the SQLite files.
- `server/app/scheduler.py` → `_purge_old_data()` applies the retention settings.
- `server/app/api/system/log.py` serves the five PinPoint log categories under `system.logs`.
- On a lab appliance `/usr/local/nagios/var/nagios.log` is world-readable.

#### C. Required Changes

**Backend / System**

1. Add a helper *(proposed, `server/app/storage_usage.py`)* returning the size of each database file, the backup folder, the Nagios archive folder, and free space of the filesystem that holds them, using `os.stat` and `shutil.disk_usage`. Tolerate missing paths.
2. Expose it on a new route or as extra fields on `GET /api/system/dashboard/status`, documented in the docstring, under `system.dashboard`.
3. Add `GET /api/system/log/nagios?lines=&after=` *(proposed, in `log.py`)* under `system.logs` that returns a bounded tail of `nagios.log`: cap lines (for example 500) and bytes, read from the end without loading the file, and never accept a path from the request.
4. Redact anything that could be a secret in returned lines (for example command arguments after `check_command=`), and document that the log can contain hostnames and addresses.

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

- [ ] The status data lists database, backup and archive sizes and free disk space, and handles missing paths without error.
- [ ] The Nagios log route returns at most the configured lines and bytes, newest last, and returns an empty list if the file is unreadable.
- [ ] The route cannot be used to read any other file.
- [ ] Both require login and the stated permission (403 otherwise).

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Unit tests for new or modified logic.
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A here; delivered by Issue #11.3.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request.

#### G. Testing and Verification

- Unit: size helper with temp files and missing paths; tail reader with small, large and unterminated files; redaction.
- API: permission and bounds (`lines` and `after` validation returns 400).
- Security: path and parameter injection attempts.

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
