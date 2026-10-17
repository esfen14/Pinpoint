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
3. [x] Models and migration: `RemediationAction.Notify_On` (JSON list or three booleans, default all three), `RemediationRun.Notify_State` / `Notify_Error` / `Notify_Attempts` / notified-at, and two bounded `SystemSettings` columns for the repeat count and window; one multi-database migration after `f155a3c7d2b1` with downgrade. Files: `system_models.py`, `server/migrations/versions/<new>.py`, `tests/unit/test_remediation_migration.py` (or a new migration test), runner under `tests/support/`.
4. [x] Escalation logic in a new `remediation_escalation.py`: outcome-to-trigger mapping (failed, timed_out -> failed; skipped_cooldown, skipped_hourly_cap -> capped), `Notify_On` filter, comment builder from fixed text + action name + outcome code + run id, bounded retry, repeat-window detection, idempotency by run id. Tests: `tests/unit/test_remediation_escalation.py`.
5. [x] Wire it into `remediation.py` (`execute` and the skip rows in `record_decisions`), without letting a notification failure stop the consumer. Update `tests/unit/test_remediation_consumer.py`.
6. [x] API: validate and persist `Notify_On` and the two settings; return notification state and error from the runs API. Files: `api/system/remediation.py`, `tests/unit/test_remediation_api.py`. Permission checks unchanged (`remediation.view`, `remediation.manage`).
7. [ ] (BLOCKED on a lab capture, see Decisions) Feed: confirm `normalize_notification` / `collapse_repeats` keep the CUSTOM type and comment; add the label if missing. Files: `api/system/notifications.py` and its helper, `tests/unit/test_notifications.py`.
8. [x] Frontend types and run views: `RunLog.tsx`, `RunDrawer.tsx`, types, tests in `client/src/test/RemediationPage.test.tsx`.
9. [x] Frontend form: `Notify_On` checkboxes in `ActionFormDialog.tsx` with help text; settings fields if placed on the Remediation status panel. Tests.
10a. [x] (added, the original plan missed the data source) Backend: a read route that returns the newest run per host and service for the badge, `remediation.view` only, in `api/system/remediation.py` with tests in `tests/unit/test_remediation_api.py`; update the route catalog test data if `scripts/verify.sh backend` checks it.
10. [ ] Frontend badge and labels: `ServiceStatusTable.tsx` badge linking to the run, `RecentNotifications.tsx`, `HistoryPage.tsx`; 403 and empty states. Tests.
11. [ ] Docs: the four spec files, help text, admin guide section; `scripts/verify.sh docs`.
12. [ ] `scripts/verify.sh all`; injection and secret-exposure review notes in the PR; lab report in `docs/test-runs/`; delete this file and open the PR.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read the issue, specs and sources; wrote this plan; branched from `origin/main` | `gh issue view 153` | Plan written, no code changed |
| 1 | Step 2: `send_custom_host_notification` and `send_custom_service_notification` in `nagios/commands.py` (option fixed at 0), tests in `TestCustomNotifications` | `server/.venv/Scripts/python -m pytest tests/unit/test_nagios_commands.py -q -k CustomNotifications` | 10 failed first (functions missing), then 10 passed |
| 2 | Step 3: `Notify_On`, run `Notify_*` columns, `RemediationNotifyState`, two repeat settings in `system_models.py`; migration `e153c4a8b2d7` after `f155a3c7d2b1`; runner `tests/support/remediation_escalation_migration_runner.py` and two tests. I wrote the migration before its test (wrong order); the test checks defaults, a state write, downgrade and re-upgrade | `pytest tests/unit/test_device_migration.py tests/unit/test_upgrade_rehearsal.py tests/unit/test_remediation_migration.py tests/unit/test_remediation_api.py tests/unit/test_remediation_consumer.py tests/unit/test_forecast_migration.py -q` | 239 passed, 1 skipped, 2 errors (the Windows temp-file lock in the action FK tests, unrelated; also seen before this change) |
| 3 | Step 4: `server/app/remediation_escalation.py` (outcome mapping, `Notify_On` filter, fixed-text comment with a safe-character action name, `deliver` with write-ahead attempt count and 3 bounded attempts, `deliver_pending`, `fail_unfinished`, `check_repeat`); 53 tests in `tests/unit/test_remediation_escalation.py` | `pytest tests/unit/test_remediation_escalation.py -q` | collection error first (module missing), then 53 passed |
| 4 | Step 5: wired into `remediation.py` (`record_decisions` marks cooldown and cap skips; new `mark_notification` after `execute` marks failed, timed out and repeated; `process_spool` calls `deliver_pending`) and `scheduler.py` (`fail_unfinished` at startup); 10 new consumer tests | `pytest tests/unit/test_remediation_consumer.py tests/unit/test_remediation_escalation.py -q` | 8 of 10 failed first (not wired), then 145 passed, 1 skipped |
| 5 | Step 6: `api/system/remediation.py` accepts and returns `notifyOn` (default all three, may be empty, audited), returns `notifyKind/State/Attempts/Error/At` on every run, and the settings route takes `repeatCount` (2 to 20) and `repeatWindowHours` (1 to 168), audited; 10 new tests. Two existing tests that pin exact response shapes were updated for the added keys (settings body, run item fields) | `pytest tests/unit/test_remediation_api.py -q` | 10 failed first, then 128 passed |
| 6 | resumed on a new session (pulled, last check re-run: 128 passed). Step 7 not started: no recorded sample of how the Nagios archive reports a CUSTOM notification, so the feed change needs a lab capture first. Did step 8 instead: `types/remediation.ts` (notify fields, `notifyLabel`, `NOTIFY_KIND_LABELS`), `RunLog.tsx` Operator column, `RunDrawer.tsx` notification rows; 6 new tests | `npx vitest run src/test/RemediationPage.test.tsx` and `npx tsc --noEmit -p tsconfig.app.json` | 6 failed first, then 47 passed; tsc clean after adding `notifyOn` to the fixture in `RemediationParameters.test.tsx` |
| 7 | Step 9: `ActionFormDialog.tsx` fieldset "Tell the operator when" with help text and `notifyOn` in the payload; the enable switch in `RemediationPage.tsx` now keeps `notifyOn` (without it the server default would have reset a saved choice); `StatusPanel.tsx` Repeat recovery section (count and window, save, read-only without manage); types updated; 14 new tests, 2 existing pinned expectations updated (create payload, settings mock) | `npx vitest run src/test/RemediationPage.test.tsx src/test/RemediationParameters.test.tsx` and `npx tsc --noEmit -p tsconfig.app.json` | 9 failed first, then 62 passed; tsc clean |
| 8 | Step 10a: `GET /system/remediation/last-runs` in `api/system/remediation.py` (newest run per host and service, 7 days, max 500, no output, `remediation.view`); 6 tests and the URL added to `READ_URLS`; route rows and the new run, action and settings fields added to `Backend_Modules_and_Routes.md` so the catalog matches | `pytest tests/unit/test_remediation_api.py -q` and `python scripts/check_route_drift.py` | 5 of 6 failed first (route missing), then 135 passed; 170 routes match the catalog |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `pytest tests/unit/test_remediation_api.py -q` (from `server/`) and `python ../scripts/check_route_drift.py`
- Result (first failing lines, or "green"): green, 135 passed; 170 API routes match the catalog.
- Hypothesis: the badge's data source exists; the client does not use it yet. A client drift check (`scripts/check_client_api_drift.py`) will need the new call to match the route.
- Next action: plan step 10 on the client. Failing tests first (a new `client/src/test/ServiceStatusTableRecovery.test.tsx`, modelled on `ServiceStatusTableForecast.test.tsx`): a badge on the service row showing the last recovery outcome and linking to the run, hidden without `remediation.view`, no badge for a service with no run, error and loading handled quietly. Then add `getLastRuns` to `client/src/lib/remediationApi.ts`, the type in `types/remediation.ts`, and the badge in `client/src/components/system-status/ServiceStatusTable.tsx`. Find how the Remediation page opens a specific run (the drawer is opened from `RunLog.tsx` state), so the link can reach it.

## Decisions and notes

Questions for a person. The person said "let's start" without answering, so work proceeds on the proposed answers to 1 and 2; question 3 is asked again before the lab run (plan step 1 and 12):

1. **Sensitive module.** This change adds a command that writes to the Nagios pipe, which Engineering Standards lists as a command execution path needing an explicit injection and secret-exposure review. Confirm that doing the review inside this PR (comment built from fixed text only, closed allowlist, no raw output) is acceptable.
2. **Repeat settings.** Proposed: two bounded `SystemSettings` columns, `Remediation_Repeat_Count` (default 3, range 2 to 20) and `Remediation_Repeat_Window_Hours` (default 24, range 1 to 168), edited next to the existing Remediation settings. Confirm, or say where else they should live.
3. **Lab.** The acceptance criteria and the report in `docs/test-runs/` need a real lab run (service custom notification, downtime suppression, unwritable pipe). The issue's section G asks for it, so confirm which lab to use (`scripts/vmlab` or the Docker lab) and that I may start it when the code is ready. Only the host form of the custom notification was verified on 2026-10-13.

Notes:
- Step 7 (feed) is blocked on data: this repo has no sample of the archivejson entry Nagios writes for a CUSTOM notification (field that holds the type, and where the comment text appears). Capture one on the lab (send a custom notification, query `archivejson.cgi?query=notificationlist`), save it under `docs/test-runs/`, then write the failing test from that real sample.
- Existing tests that pin exact response shapes were updated for the added API fields (settings body and run item fields in `test_remediation_api.py`); the old keys are unchanged.
- Known gap to mention in the PR: `server/tests/unit/test_nagios_commands.py` FIFO tests cannot run on Windows (`os.mkfifo`); the new command tests avoid the FIFO, so they run everywhere.
- A cooldown or cap skip notifies on every blocked event (one per run row), as the issue asks. A flapping service could therefore send several; the cooldown and cap on the action limit the number of runs but not the skips. Raise this in the PR.
- The feed has no PinPoint notification table, so "visible in the in-app feed" is satisfied by Nagios writing the custom notification to its archive.
- Ruled out: a PinPoint-only mail path (out of scope in the issue).
