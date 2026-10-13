### Issue #20 — System Refinement Clear Acknowledgements on Recovery and Audit the History Page

**Category:** System

**Work Type:** Refinement

**Priority:** Medium

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Problem History; Notification History; Notification History; Problem History

**Dependencies:** None

**Plan reference:** Issue #20 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

#### A. Problem Description

**Part 20.1 (System) — System Refinement Clear Acknowledgements on Recovery and Record AUTO_RESOLVED History**

When a host returns to UP or a service to OK, its Pinpoint acknowledgement stays active and no `AUTO_RESOLVED` history row is written, although the model contract exists (`Implementation_Status.md`, `Data_Model_and_Integrations.md`). A stale acknowledgement then hides a later, different failure of the same service and corrupts the problem history.

**Part 20.2 (Web-Interface) — Web-Interface Refinement Audit History Page Against Requirements and Fix Gaps**

`/history` exists and calls the list and detail routes, but `Implementation_Status.md` states it has not been audited against `spec files/Alerts_Notifications_History_Requirements.md`, so its conformance is unknown.

**Out of scope for this issue:**

- Backend defects found by the audit: raise a separate issue for each.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 20.1: `server/app/system_models.py`: `AlertAcknowledgement` (one active record per hostname and service) and `AckHistory` (append-only); `AckAction.AUTO_RESOLVED` is defined; `AckHistory.ActorUserID` is nullable for system actions.
- Part 20.1: `server/app/nagios/status.py` → `get_status()` runs every 60 seconds from `server/app/scheduler.py` and writes the snapshots that define "latest state".
- Part 20.1: `server/app/api/system/dashboard.py` shows the acknowledge routes and their helper functions (`_new_ack`, `_new_ack_history`, `_serialize_ack`).
- Part 20.1: `spec files/Display_Requirements.md` §4 and `Alerts_Notifications_History_Requirements.md` define the lifecycle.
- Part 20.1: Tests: `server/tests/unit/test_dashboard.py`, `test_status.py`, `test_history.py`.
- Part 20.2: `client/src/pages/HistoryPage.tsx` is routed at `/history` with permission `system.history` (`client/src/lib/pageAccess.ts`) and a sidebar entry.
- Part 20.2: `server/app/api/system/history.py` serves `/api/system/history/alerts`, `.../alerts/detail`, `.../notifications` and `.../notifications/detail` (Nagios events and PinPoint scan events).
- Part 20.2: `client/src/types/notification.ts` holds the wire conversion; `utils/exportData.ts` and `components/shared/ExportMenu.tsx` provide export.
- Part 20.2: No dedicated `HistoryPage` test exists in `client/src/test/` (the listing has none).

#### C. Required Changes

**Backend / System**

1. **Part 20.1 (System):** After each successful poll, find active acknowledgements whose host or service is now UP or OK in the latest snapshot, delete them, and append one `AckHistory` row per deletion with action `AUTO_RESOLVED` and no actor. Do it in one transaction with rollback on failure.
2. **Part 20.1 (System):** Make it idempotent so a repeated poll never writes a second history row, and ignore targets that no longer exist.
3. **Part 20.1 (System):** Keep an acknowledgement when the latest snapshot is missing or stale, so a poll failure never auto-resolves anything.
4. **Part 20.1 (System):** Reuse the helpers in `dashboard.py` or move them to a shared module rather than copying them.

**Frontend / Web Interface**

1. **Part 20.2 (Web-Interface):** Read the requirements document and write an audit table in the pull request (or under `docs/test-runs/`) with one row per requirement: requirement, evidence in the page, result (met, partly met, not met).
2. **Part 20.2 (Web-Interface):** Fix every gap that is confined to the page. Add frontend tests for filters, pagination, detail view, the Nagios and PinPoint sources, empty and error states, and the permission guard.
3. **Part 20.2 (Web-Interface):** For a gap that needs backend work, record it as a new issue and link it from the audit table. Do not hide it.
4. **Part 20.2 (Web-Interface):** Update `Implementation_Status.md` to remove the "not audited" note and state the result.

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

- [ ] **Part 20.1 (System):** When an acknowledged service recovers, the active acknowledgement is removed and exactly one `AUTO_RESOLVED` history row exists after the next poll.
- [ ] **Part 20.1 (System):** A repeated poll adds no further row.
- [ ] **Part 20.1 (System):** A poll that fails or returns no data leaves acknowledgements untouched.
- [ ] **Part 20.1 (System):** An acknowledgement on a still-failing item is kept.
- [ ] **Part 20.1 (System):** Acknowledge, unacknowledge and history routes behave as before.
- [ ] **Part 20.2 (Web-Interface):** An audit table covers every requirement in the requirements document with an evidence-based result.
- [ ] **Part 20.2 (Web-Interface):** Every page-only gap is fixed and covered by a test.
- [ ] **Part 20.2 (Web-Interface):** Every backend-dependent gap is filed as a separate issue and referenced.
- [ ] **Part 20.2 (Web-Interface):** A new `HistoryPage` test file exists and passes.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Display_Requirements.md`, `spec files/Alerts_Notifications_History_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] User-facing documentation: N/A.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request.

#### G. Testing and Verification

- **Part 20.1 (System):** Unit: recovery of host and service, repeated poll, failed poll, still-failing item, deleted target.
- **Part 20.1 (System):** Regression: `test_dashboard.py`, `test_status.py`, `test_history.py`.
- **Part 20.1 (System):** Lab: acknowledge, recover, check history.
- **Part 20.2 (Web-Interface):** Frontend (new `client/src/test/HistoryPage.test.tsx`): list, filters, pagination, detail, source filter, empty and error states, permission guard.
- **Part 20.2 (Web-Interface):** Regression: `PageAccess.test.tsx`, `App.test.tsx`.
- **Part 20.2 (Web-Interface):** Manual: walk the page against a lab appliance with real events (record in `docs/test-runs/`).

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
