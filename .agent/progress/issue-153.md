# Issue #153: System Implementation Add Failure Escalation and Outcome Visibility for Automatic Recovery

Branch: `issue-153-failure-escalation`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

Plan issue #22 (Parts 22.1 System and 22.2 Web-Interface). Branched from `origin/main` at `7f5bc167`, which already contains #155 (#194), #156 and #182, so the migration head to extend is `f155a3c7d2b1`.

## Finish condition

Copied from the issue (sections E, F and H). Tick an item only when a check proves it.

- [ ] E1 A failed recovery produces exactly one custom notification for that service, visible in the in-app feed and sent by email through the existing path.
- [ ] E2 A recovery blocked by the cooldown or hourly cap produces one notification and records that it did.
- [ ] E3 `N` successful recoveries in the window produce one "repeated" notification and no more until the window passes.
- [ ] E4 A service in scheduled downtime or with notifications disabled does not send the operator an email (the force option is not used).
- [ ] E5 An unwritable command file marks the run "notification failed", does not crash the consumer, and is retried only a bounded number of times.
- [ ] E6 No plugin output, command output or secret appears in the notification comment, a log line or a response.
- [ ] E7 The run log and drawer show the notification state and any error, and the service row badge links to the run.
- [ ] E8 A custom notification appears in the bell, on the Dashboard and in History with its comment text.
- [ ] E9 Users without the Remediation permission do not see run details, and existing page-access tests pass.
- [ ] F1 Source code, API changes with route docstrings and permission checks, multi-database migration with downgrade, frontend components/types, unit tests, frontend interaction tests, integration/regression tests.
- [ ] F2 Docs: `Backend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`; page help text for Notify on; admin guide section on how recovery failures reach contacts.
- [ ] F3 `scripts/verify.sh all` output on the PR, and a sanitized lab report in `docs/test-runs/` from its `TEMPLATE.md`.
- [ ] H Definition of Done items (CI green, PR references the issue, docs, security review).

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| C1.1 send one custom notification on failed, timed out or capped run, comment from fixed text + action name + outcome code + run id only | E1, E2, E6 | unit: outcome-to-notification mapping and comment builder with hostile names (new `test_remediation_escalation.py`); lab report |
| C1.2 send without the force option; confirm the option bitmask on a lab appliance | E4 | unit: command line has options `0`; lab: service form `SEND_CUSTOM_SVC_NOTIFICATION` and a downtime case |
| C1.3 repeat recovery: same action succeeds N times for the same object in a window, one notification per window, bounded settings | E3 | unit: repeat-window logic |
| C1.4 `Notify_On` on `RemediationAction` (failed, capped, repeated, default all three), migration preserves rows | E1-E3, F1 | unit: `Notify_On` filtering; migration up/down test |
| C1.5 record on the run whether the notification was sent and any send error, expose through the runs API; bounded retry then abandon | E5, E7 | unit: command-channel failure paths (missing file, permission denied, timeout); API test |
| C1.6 idempotent: restart or duplicate spool line must not notify twice | E1 | unit: duplicate spool line and consumer restart |
| C2.1 run log and drawer show "operator notified", "notification failed", "not required", with error | E7 | frontend test on `RunLog.tsx`, `RunDrawer.tsx` |
| C2.2 `Notify_On` checkboxes with help text | F1, F2 | frontend test on `ActionFormDialog.tsx` |
| C2.3 last-outcome badge on `ServiceStatusTable.tsx` linking to the run; `RecentNotifications.tsx` and `HistoryPage.tsx` label a custom notification and show its comment | E7, E8 | frontend tests; backend test that `normalize_notification` keeps the custom type and comment |
| C2.4 loading, empty, error and 403 states for each new element | E9 | frontend tests |
| D: no recipient list, mail call or second channel; do not override acknowledgement; bound loops; command write timeout; never raw output in the comment | E5, E6 | code review plus tests above |
| Out of scope: new recovery actions; a PinPoint-only mail or chat path | n/a | n/a |
| G regression: notification feed and `RecentNotifications` tests still pass | H | `scripts/verify.sh all` |

## Plan

Files are relative to `server/app` unless stated.

1. [ ] Lab check first (needs a person, see Decisions): confirm `SEND_CUSTOM_SVC_NOTIFICATION;host;service;0;author;comment` is accepted by the lab Nagios, shows in `archivejson.cgi` as a CUSTOM notification, and is suppressed in downtime. Only the host form is verified so far (plan status log 2026-10-13).
2. [x] Command channel: add `send_custom_host_notification` and `send_custom_service_notification` to `nagios/commands.py` (closed allowlist, options fixed at 0, comment through `_wire_comment`, validated target). Tests in `tests/unit/test_nagios_commands.py`.
3. [ ] Models and migration: `RemediationAction.Notify_On` (JSON list or three booleans, default all three), `RemediationRun.Notify_State` / `Notify_Error` / `Notify_Attempts` / notified-at, and two bounded `SystemSettings` columns for the repeat count and window; one multi-database migration after `f155a3c7d2b1` with downgrade. Files: `system_models.py`, `server/migrations/versions/<new>.py`, `tests/unit/test_remediation_migration.py` (or a new migration test), runner under `tests/support/`.
4. [ ] Escalation logic in a new `remediation_escalation.py`: outcome-to-trigger mapping (failed, timed_out -> failed; skipped_cooldown, skipped_hourly_cap -> capped), `Notify_On` filter, comment builder from fixed text + action name + outcome code + run id, bounded retry, repeat-window detection, idempotency by run id. Tests: `tests/unit/test_remediation_escalation.py`.
5. [ ] Wire it into `remediation.py` (`execute` and the skip rows in `record_decisions`), without letting a notification failure stop the consumer. Update `tests/unit/test_remediation_consumer.py`.
6. [ ] API: validate and persist `Notify_On` and the two settings; return notification state and error from the runs API. Files: `api/system/remediation.py`, `tests/unit/test_remediation_api.py`. Permission checks unchanged (`remediation.view`, `remediation.manage`).
7. [ ] Feed: confirm `normalize_notification` / `collapse_repeats` keep the CUSTOM type and comment; add the label if missing. Files: `api/system/notifications.py` and its helper, `tests/unit/test_notifications.py`.
8. [ ] Frontend types and run views: `RunLog.tsx`, `RunDrawer.tsx`, types, tests in `client/src/test/RemediationPage.test.tsx`.
9. [ ] Frontend form: `Notify_On` checkboxes in `ActionFormDialog.tsx` with help text; settings fields if placed on the Remediation status panel. Tests.
10. [ ] Frontend badge and labels: `ServiceStatusTable.tsx` badge linking to the run, `RecentNotifications.tsx`, `HistoryPage.tsx`; 403 and empty states. Tests.
11. [ ] Docs: the four spec files, help text, admin guide section; `scripts/verify.sh docs`.
12. [ ] `scripts/verify.sh all`; injection and secret-exposure review notes in the PR; lab report in `docs/test-runs/`; delete this file and open the PR.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read the issue, specs and sources; wrote this plan; branched from `origin/main` | `gh issue view 153` | Plan written, no code changed |
| 1 | Step 2: `send_custom_host_notification` and `send_custom_service_notification` in `nagios/commands.py` (option fixed at 0), tests in `TestCustomNotifications` | `server/.venv/Scripts/python -m pytest tests/unit/test_nagios_commands.py -q -k CustomNotifications` | 10 failed first (functions missing), then 10 passed |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `server/.venv/Scripts/python -m pytest tests/unit/test_nagios_commands.py -q -k CustomNotifications`
- Result (first failing lines, or "green"): green, 10 passed. The older FIFO tests in the same file error on Windows (`os.mkfifo` missing); they run on Linux CI only.
- Hypothesis: the command layer is done; the rest builds on it.
- Next action: plan step 3, write the failing migration test, then add `Notify_On`, the run notification fields and the two settings columns in `system_models.py` and a migration after `f155a3c7d2b1`.

## Decisions and notes

Questions for a person. The person said "let's start" without answering, so work proceeds on the proposed answers to 1 and 2; question 3 is asked again before the lab run (plan step 1 and 12):

1. **Sensitive module.** This change adds a command that writes to the Nagios pipe, which Engineering Standards lists as a command execution path needing an explicit injection and secret-exposure review. Confirm that doing the review inside this PR (comment built from fixed text only, closed allowlist, no raw output) is acceptable.
2. **Repeat settings.** Proposed: two bounded `SystemSettings` columns, `Remediation_Repeat_Count` (default 3, range 2 to 20) and `Remediation_Repeat_Window_Hours` (default 24, range 1 to 168), edited next to the existing Remediation settings. Confirm, or say where else they should live.
3. **Lab.** The acceptance criteria and the report in `docs/test-runs/` need a real lab run (service custom notification, downtime suppression, unwritable pipe). The issue's section G asks for it, so confirm which lab to use (`scripts/vmlab` or the Docker lab) and that I may start it when the code is ready. Only the host form of the custom notification was verified on 2026-10-13.

Notes:
- The feed has no PinPoint notification table, so "visible in the in-app feed" is satisfied by Nagios writing the custom notification to its archive.
- Ruled out: a PinPoint-only mail path (out of scope in the issue).
