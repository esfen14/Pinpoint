### Issue #7.3 — Installer Implementation Install Event Handler Spool Directory and Handler Executable

**Category:** Installer

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Event Handlers

**Dependencies:** None

**Plan reference:** Issue #7 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #7. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Design to be confirmed with the security review of Issue #7.1. Where the executable should live and its permissions on an installed appliance were not verified: the application directory is owned by another user and the `nagios` user may not be able to traverse it.

#### A. Problem Description

Nagios must be able to run a small executable and write a spool file that the PinPoint service can read. Neither exists on an installed appliance today.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- On a lab appliance: `/usr/local/nagios/var/spool` exists, `pinpoint` is in group `nagios` (`id pinpoint`), and `/usr/local/nagios/etc` is group-writable. `sudoers` for `pinpoint` allows only the SMTP helper and `systemctl reload nagios`.
- The application code is under `/opt/pinpoint/Network-Diagnosis-System`, and git reports "dubious ownership" for a non-owner, so directory ownership differs between users.
- The installer code is not in this repository, so its file locations are *further investigation required*.

#### C. Required Changes

**Installer / Deployment**

1. Create a spool directory *(proposed, for example `/usr/local/nagios/var/spool/pinpoint-events`)* owned by `nagios:nagios` with mode 2770 so the `pinpoint` user can read and delete entries and nobody else can.
2. Install the handler executable *(proposed)* to a root-owned path both users can execute (for example under `/usr/local/nagios/libexec`), mode 0755, not writable by the web user, with no dependency on the application directory.
3. Add upgrade handling so existing appliances get the directory and the executable without losing configuration.
4. Do not change `sudoers` unless Issue #8.2 requires it.

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

- [ ] On a fresh install and on an upgraded appliance the spool directory exists with the stated owner and mode.
- [ ] The `nagios` user can run the executable and append to the spool, and the `pinpoint` user can read and remove entries.
- [ ] The web user cannot modify the executable.
- [ ] The upgrade does not alter other Nagios configuration or the SMTP helper.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Installer tests or a scripted check in the installer repository (this repository's lab only verifies the result).
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Agent_Workflow_and_CI.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Installer-side script test for ownership and modes.
- VM-lab (`scripts/vmlab`, record under `docs/test-runs/`): install, then run the executable as `nagios` and read the spool as `pinpoint`.
- Upgrade test from the previous installer version.

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
