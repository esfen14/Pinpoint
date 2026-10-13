### Issue #21.1 — Web-Interface Refinement Reconcile Reports Page Documentation With Implemented Report Views

**Category:** Web-Interface

**Work Type:** Refinement

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Availability Reports

**Dependencies:** None

**Plan reference:** Issue #21 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #21. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

`Implementation_Status.md` says the Reports UI exposes only host availability and network-services views. The page actually has six (verified in `client/src/pages/ReportsPage.tsx`): Host Availability, Network Services, Hosts by OS, Device Services, Alerts and Notifications. A stale status file misleads planning and agents.

**Out of scope for this issue:**

- Any new report behavior, availability targets (Issue #21.2) and scheduled reports.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `client/src/pages/ReportsPage.tsx` defines `VIEW_TABS` for all six views and the periods `last_24h`, `today`, `last_7d`, `last_30d`.
- `client/src/components/reports/ExtraReports.tsx` implements `hosts-by-os`, `device-services`, `alerts` and `notifications`; `HostAvailabilityReportTable.tsx` and `NetworkServicesReportTable.tsx` implement the other two.
- `server/app/api/system/report.py` has the six endpoints under `system.report`.
- `spec files/Implementation_Status.md` (row "Reports frontend breadth"), `Frontend_Modules_and_Routes.md` and `Display_Requirements.md` describe the Reports page.

#### C. Required Changes

**Frontend / Web Interface**

1. Verify each of the six views against its endpoint and record what each shows, its period handling and its export support.
2. Correct `Implementation_Status.md` and the Reports section of `Frontend_Modules_and_Routes.md` to match what is implemented.
3. If a view has a defect, file it separately and do not fix it here.

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

- [ ] `Implementation_Status.md` and `Frontend_Modules_and_Routes.md` list all six views accurately and no longer say only two exist.
- [ ] Each documented view names the API route behind it.
- [ ] `scripts/verify.sh docs` passes.

#### F. Required Deliverables

- [ ] Corrected documentation (paths in section C).
- [ ] Source code, API, migration and frontend changes: N/A.
- [ ] Unit tests: N/A (documentation only); the docs link and drift checks must pass.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] User-facing documentation: N/A.
- [ ] Evidence: `scripts/verify.sh docs` output attached to the pull request.

#### G. Testing and Verification

- `scripts/verify.sh docs` (link and drift checks).
- Manual: open each view on a lab appliance and confirm it loads data.

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
