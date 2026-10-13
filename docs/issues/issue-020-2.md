### Issue #20.2 — Web-Interface Refinement Audit History Page Against Requirements and Fix Gaps

**Category:** Web-Interface

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Notification History; Problem History

**Dependencies:** None

**Plan reference:** Issue #20 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #20. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

`/history` exists and calls the list and detail routes, but `Implementation_Status.md` states it has not been audited against `spec files/Alerts_Notifications_History_Requirements.md`, so its conformance is unknown.

**Out of scope for this issue:**

- Backend defects found by the audit: raise a separate issue for each.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- `client/src/pages/HistoryPage.tsx` is routed at `/history` with permission `system.history` (`client/src/lib/pageAccess.ts`) and a sidebar entry.
- `server/app/api/system/history.py` serves `/api/system/history/alerts`, `.../alerts/detail`, `.../notifications` and `.../notifications/detail` (Nagios events and PinPoint scan events).
- `client/src/types/notification.ts` holds the wire conversion; `utils/exportData.ts` and `components/shared/ExportMenu.tsx` provide export.
- No dedicated `HistoryPage` test exists in `client/src/test/` (the listing has none).

#### C. Required Changes

**Frontend / Web Interface**

1. Read the requirements document and write an audit table in the pull request (or under `docs/test-runs/`) with one row per requirement: requirement, evidence in the page, result (met, partly met, not met).
2. Fix every gap that is confined to the page. Add frontend tests for filters, pagination, detail view, the Nagios and PinPoint sources, empty and error states, and the permission guard.
3. For a gap that needs backend work, record it as a new issue and link it from the audit table. Do not hide it.
4. Update `Implementation_Status.md` to remove the "not audited" note and state the result.

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

- [ ] An audit table covers every requirement in the requirements document with an evidence-based result.
- [ ] Every page-only gap is fixed and covered by a test.
- [ ] Every backend-dependent gap is filed as a separate issue and referenced.
- [ ] A new `HistoryPage` test file exists and passes.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Frontend_Modules_and_Routes.md`, `spec files/Alerts_Notifications_History_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: N/A.
- [ ] Evidence that the functionality works: `scripts/verify.sh frontend` output attached to the pull request.

#### G. Testing and Verification

- Frontend (new `client/src/test/HistoryPage.test.tsx`): list, filters, pagination, detail, source filter, empty and error states, permission guard.
- Regression: `PageAccess.test.tsx`, `App.test.tsx`.
- Manual: walk the page against a lab appliance with real events (record in `docs/test-runs/`).

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
