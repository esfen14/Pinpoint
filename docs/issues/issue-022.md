### Issue #22 — System Implementation Add Failure Escalation and Outcome Visibility for Automatic Recovery

**Category:** System

**Work Type:** Implementation

**Priority:** Medium

**Estimated Complexity:** Medium

**Related Nagios Core Feature:** Event Handlers; Proactive Resolution; Notifications

**Dependencies:** [Issue #7](issue-007.md), [Issue #8](issue-008.md), [Issue #19](issue-019.md). Benefits from [Issue #1](issue-001.md) and [Issue #3](issue-003.md) but does not require them.

**Plan reference:** Issue #22 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** **Part 22.1 (System):** Waits for the event handler framework (Issue #7) and the Nagios command channel (Issue #19). Whether the appliance's Nagios accepts custom notification external commands (`check_external_commands`, the command file path and its permissions) was not verified, *further investigation required* on a lab appliance.
> **Part 22.2 (Web-Interface):** Same condition as Part 22.1.

#### A. Problem Description

**Part 22.1 (System) — System Implementation Add Escalation Through Nagios Custom Notifications When Automatic Recovery Fails or Repeats**

The plan's acceptance criterion for Issue #8 is "a failed restart escalates as a normal alert", and Issue #7 lists a retry policy limit. Neither issue specifies how. As written, a failed, timed-out or capped recovery is only recorded in `RemediationRun`. An operator who relies on automatic recovery is never told it stopped working, and a service that is "recovered" every hour hides a fault that keeps coming back.

**Part 22.2 (Web-Interface) — Web-Interface Implementation Show Recovery Outcomes Next to the Alerts They Relate To**

The only place a recovery outcome will be visible is the Remediation run log from Issue #7. An operator looking at an alert or a service row cannot tell whether automatic recovery was attempted, succeeded or failed.

**Out of scope for this issue:**

- New recovery actions (Issues #7 and #8).
- A second, PinPoint-only mail or chat path. Escalation must reuse Nagios contacts, timeperiods and escalations.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Part 22.1: `server/app/api/system/notifications.py` builds the in-app feed from Nagios `archivejson.cgi` with a per-user cursor (`NotificationCursor`, `server/app/system_models.py`). There is **no PinPoint-owned notification table**, so a notification created only inside PinPoint would never appear in the bell or on the Dashboard. A Nagios custom notification does, because it is written to the Nagios archive.
- Part 22.1: No code writes to the Nagios command pipe today (plan "Major architectural gaps"). Issue #19 adds that channel and is the transport used here.
- Part 22.1: `RemediationRun` and its outcomes are proposed in Issue #7 *(proposed, `server/app/system_models.py`)*; the consumer is `server/app/remediation.py` *(proposed)*.
- Part 22.1: `AlertAcknowledgement` and `AckHistory` (`server/app/system_models.py`) and `ServiceStatus.Acknowledgement_Type` and `Scheduled_Downtime_Depth` (`server/app/history_models.py`) describe whether an operator already owns the problem.
- Part 22.2: `client/src/components/dashboard/RecentNotifications.tsx`, `client/src/pages/HistoryPage.tsx` and `client/src/components/system-status/ServiceStatusTable.tsx` render alerts and service rows; the run log drawer is specified in Issue #7 Part 7.2.

#### C. Required Changes

**Backend / System**

1. **Part 22.1 (System):** When the consumer finishes a `RemediationRun` with outcome failed, timed out or refused-by-cap, send one Nagios custom service (or host) notification for that object through the command channel from Issue #19. The comment is built from fixed text plus the action name, outcome code and run id only. It never contains plugin output or command output.
2. **Part 22.1 (System):** Send custom notifications **without** the force option, so Nagios still applies notification-enabled flags, scheduled downtime, timeperiods (Issue #1) and escalations (Issue #3). Confirm the option bitmask against the Nagios external commands documentation on a lab appliance before coding.
3. **Part 22.1 (System):** Detect repeat recovery: when the same action succeeds `N` times for the same object inside a window (proposed defaults 3 in 24 hours, stored as bounded settings), send one custom notification "recovered automatically N times, underlying fault persists", at most once per window.
4. **Part 22.1 (System):** Add `Notify_On` to `RemediationAction` *(proposed, flags: failed, capped, repeated; default all three)* with a migration that preserves existing rows.
5. **Part 22.1 (System):** Record on the `RemediationRun` whether the operator notification was sent and any send error, and expose both through the runs API. A failed send is retried a bounded number of times, then recorded and abandoned.
6. **Part 22.1 (System):** Make the notification idempotent: a consumer restart or duplicate spool line must not notify twice for the same run.

**Frontend / Web Interface**

1. **Part 22.2 (Web-Interface):** In the Remediation run log and drawer, show "operator notified", "notification failed" or "not required", with the send error if any.
2. **Part 22.2 (Web-Interface):** Add the `Notify_On` checkboxes to the action form with plain-language help text.
3. **Part 22.2 (Web-Interface):** Show the last recovery outcome as a compact badge on a service row in `ServiceStatusTable.tsx` that links to the run, and make sure `RecentNotifications.tsx` and `HistoryPage.tsx` label a custom notification and display its comment text.
4. **Part 22.2 (Web-Interface):** Show loading, empty, error and 403 states for every new element.

#### D. Implementation Guidelines

- Nagios, not PinPoint, decides who is told. Do not add a recipient list, a mail call or a second channel for remediation.
- A custom notification must not reset or hide the original problem notification. If the underlying service is acknowledged, Nagios applies its own rules; do not override them.
- Bound every loop and give the command channel write a timeout. A missing or unwritable command file must never crash the consumer.
- Never put raw plugin or command output in the comment; it can contain secrets and shell metacharacters.

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

#### E. Acceptance Criteria

- [ ] **Part 22.1 (System):** A failed recovery produces exactly one custom notification for that service, visible in the in-app feed and sent by email through the existing path.
- [ ] **Part 22.1 (System):** A recovery blocked by the cooldown or hourly cap produces one notification and records that it did.
- [ ] **Part 22.1 (System):** `N` successful recoveries in the window produce one "repeated" notification and no more until the window passes.
- [ ] **Part 22.1 (System):** A service in scheduled downtime or with notifications disabled does not send the operator an email, because the force option is not used.
- [ ] **Part 22.1 (System):** An unwritable command file marks the run "notification failed", does not crash the consumer, and is retried only a bounded number of times.
- [ ] **Part 22.1 (System):** No plugin output, command output or secret appears in the notification comment, a log line or a response.
- [ ] **Part 22.2 (Web-Interface):** The run log and drawer show the notification state and any error, and the service row badge links to the run.
- [ ] **Part 22.2 (Web-Interface):** A custom notification appears in the bell, on the Dashboard and in History with its comment text.
- [ ] **Part 22.2 (Web-Interface):** Users without the Remediation permission do not see run details, and existing page-access tests pass.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Page help text for Notify on; admin guide section on how recovery failures reach contacts.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 22.1 (System):** Unit: outcome-to-notification mapping, `Notify_On` filtering, repeat-window logic, comment construction with hostile action names and outcomes, idempotency on duplicate spool lines.
- **Part 22.1 (System):** Unit: command-channel failure paths (missing file, permission denied, timeout).
- **Part 22.1 (System):** Migration up and down.
- **Part 22.1 (System):** Lab (record in `docs/test-runs/`): force a recovery failure on a lab service, confirm one custom notification arrives by email and in the feed, and that none is sent during scheduled downtime.
- **Part 22.2 (Web-Interface):** Frontend: notification state rendering, badge link, form checkboxes, permission guard.
- Regression: notification feed tests and `RecentNotifications` tests still pass.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

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
