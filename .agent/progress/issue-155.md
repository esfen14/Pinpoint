# Issue #155: Add Remediation Safety Controls, Run Retention and Consumer Health Reporting

Branch: `issue-155-remediation-safety-controls`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

(GitHub #155 is "plan issue #24" in `docs/issues/issue-024.md`.)

## Finish condition

The issue says: every box in sections E, F and H. Section E (acceptance) is below; F and H are the
deliverables and merge checklist, tracked in the last items.

- [ ] E1 Kill switch off: a HARD failure on a covered service records one run skipped with `kill_switch`; nothing runs.
- [ ] E2 Maintenance Mode, an acknowledged problem and scheduled downtime each skip with their own recorded reason.
- [ ] E3 Rows and spool files older than their limits are removed by the existing purge job; an oversized spool records the dropped count.
- [ ] E4 A stopped or failing consumer shows `stalled` in the health response within three intervals.
- [ ] E5 A run interrupted by a crash is marked `interrupted` after restart and is not run again.
- [ ] E6 Changing the switch or retention without the permission returns 403, and each change is audited.
- [ ] E7 Health card shows live values and a stalled banner when stalled.
- [ ] E8 Kill switch needs confirmation; state persists after reload.
- [ ] E9 Skip reasons are visible in the run log.
- [ ] F Deliverables: source, endpoints with docstrings, multi-db migration with downgrade, frontend, unit/frontend/regression tests, spec updates, help text + admin note, `scripts/verify.sh all` output, lab report in `docs/test-runs/`.
- [ ] H Definition of done: PR references #155, CI green, checklist ticked honestly.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Single switch stops all automatic action (24.1 item 1) | E1, E8 | `test_remediation_consumer.py` kill switch test; frontend test |
| Do not act on acknowledged / downtime problems (item 2) | E2 | consumer tests for each reason and precedence |
| `Run_When_Acknowledged` on the action, default false | E2, E9 (form) | model/API test, `ActionFormDialog` test |
| Maintenance Mode skips every action type, not only restarts | E2 | consumer test with `record_only` |
| Rows and spool files grow without bound (item 3) | E3 | scheduler retention tests, spool cap test |
| Heartbeat + `GET /api/system/remediation/health` (item 4) | E4, E7 | API test, frontend card test |
| Interrupted runs never re-executed (item 5) | E5 | consumer test (process after `mark_interrupted`) |
| Switch/retention writes need permission, audited, same validation flow (item 6) | E6 | API 403 + audit tests |
| Skipping is never silent: every decision has a run row (guidelines) | E1, E2 | tests assert a row per skip |
| Kill switch takes effect on next tick, no restart (guidelines) | E1 | consumer test flips the setting between ticks |
| Health is cheap: one row + directory listing (guidelines) | E4 | code review; test counts queries not required |
| Defaults unchanged; an existing test proves default output unchanged | all | existing consumer/scheduler/API tests unchanged and green |
| Out of scope: email alert on health (#153), changing cooldown/cap rules | none | not touched |

## Plan

Design decisions (see notes): kill switch and retention live on `SystemSettings` and are changed
through new `remediation.manage` routes, not the general Settings PUT; heartbeat lives in a new
one-row table; new skip outcomes are new `RemediationOutcome` members.

1. [x] Models + migration: `SystemSettings.Remediation_Enabled` (default true), `Remediation_Retention_Days` (default 90); `RemediationAction.Run_When_Acknowledged` (default false); new `RemediationOutcome` members `SKIPPED_KILL_SWITCH`, `SKIPPED_MAINTENANCE`, `SKIPPED_DOWNTIME`, `SKIPPED_ACKNOWLEDGED`; new singleton table `REMEDIATION_CONSUMER_STATE`. Files: `server/app/system_models.py`, new `server/migrations/versions/*`, `server/tests/unit/test_remediation_migration.py` (+ runner in `tests/support/`).
2. [x] Skip checks in the consumer: kill switch, Maintenance Mode (all types), scheduled downtime, acknowledged (unless `Run_When_Acknowledged`), then cooldown/cap; one row per skip with its reason. Files: `server/app/remediation.py`, `server/tests/unit/test_remediation_consumer.py`.
3. [x] Action API: accept and return `runWhenAcknowledged`; outcome filter accepts the new outcomes; run items show them. Files: `server/app/api/system/remediation.py`, `server/tests/unit/test_remediation_api.py`.
4. [x] Retention: purge uses `Remediation_Retention_Days`; delete spool files older than a fixed age; cap spool entries (oldest dropped, count recorded in the state row and logged). Files: `server/app/scheduler.py`, `server/app/remediation.py`, `server/tests/unit/test_scheduler.py`.
5. [x] Heartbeat + health: record last tick/error each consumer run; `GET /api/system/remediation/health` (`remediation.view`) with last tick, backlog, oldest spool age, runs and caps in 24 h, `stalled`. Files: `server/app/remediation.py`, `server/app/api/system/remediation.py`, tests.
6. [x] Settings routes: `GET`/`PUT /api/system/remediation/settings` (`remediation.manage` to write), validation, `ConfigurationChanges` audit, 403 path. Files: `server/app/api/system/remediation.py`, `server/tests/unit/test_remediation_api.py`.
7. [x] Frontend: types + API client; health card with stalled banner; kill switch with confirmation and per-row state; `Run when acknowledged` option; skip reasons in `RunLog`/`RunDrawer`; loading/error/403 states. Files: `client/src/lib/remediationApi.ts`, `client/src/pages/RemediationPage.tsx`, `client/src/components/remediation/*`, `client/src/test/RemediationPage.test.tsx`.
8. [x] Docs: spec files (Backend, Data Model, Frontend, Implementation Status), page help text, admin note on a stalled consumer. Run `scripts/verify.sh docs`.
9. [ ] Full verify (`scripts/verify.sh all`), delete progress file, PR. Lab report in `docs/test-runs/` needs the lab appliance: a person must run it (live lab is off limits unless the issue says so; it does, in section G, but ask first).

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Branch created from origin/main; plan written | none | n/a |
| 1 | Step 1: models (`Remediation_Enabled`, `Remediation_Retention_Days`, `Run_When_Acknowledged`, 4 skip outcomes, `RemediationConsumerState`) + migration `f155a3c7d2b1` + runner/tests | `pytest tests/unit/test_remediation_migration.py` (red: revision missing) then green | 12 passed; consumer/API/scheduler/rehearsal tests 165 passed; `test_escalation_merge_migration.py` fails the same on clean main (Windows temp-file lock) |
| 2 | Step 2: `safety_state`/`safety_skip` in `remediation.py`; kill switch, Maintenance (all types), downtime, acknowledged, then cooldown/cap; 10 new consumer tests; existing Maintenance test now expects `SKIPPED_MAINTENANCE` (issue requires it for every type) | `pytest tests/unit/test_remediation_consumer.py` (red: 9 failed) then green; plus actions/api/scheduler suites | 76 passed; 184 passed across 4 files |
| 3 | Step 3: `runWhenAcknowledged` in `serialize_action`/`validate_action`/audit fields; new outcomes already filterable via enum; 7 new API tests | `pytest tests/unit/test_remediation_api.py` (red: 3 failed) then green | 77 passed |
| 4 | Step 4: purge uses `Remediation_Retention_Days`; `purge_old_spool_files` (7 days) called from `_purge_old_data`; `drop_over_cap` (SPOOL_CAP 1000) in `process_spool` records `Dropped_Count`/`Dropped_At`; 6 new + 2 updated scheduler tests | `pytest tests/unit/test_scheduler.py tests/unit/test_remediation_consumer.py` (red: 6 failed) then green | 89 passed 1 skipped |
| 5 | Step 5: `record_tick` heartbeat (good tick clears error; unreadable folder sets a fixed-sentence error), `health_snapshot`, `GET /api/system/remediation/health` (`remediation.view`); 12 new tests, health URL added to the login/permission list | `pytest tests/unit/test_remediation_consumer.py tests/unit/test_remediation_api.py` (red: 11 failed) then green | 167 passed 1 skipped |
| 6 | resumed (new session); branch had no new commits on origin/main; re-ran remediation api+consumer tests | `pytest tests/unit/test_remediation_api.py tests/unit/test_remediation_consumer.py` | 167 passed 1 skipped |
| 7 | Step 6: `GET`/`PUT /api/system/remediation/settings` (`enabled`, `retentionDays` 7 to 3650), per-field 400s, audit as `remediation_setting`, Settings page version untouched; 13 new tests | `pytest tests/unit/test_remediation_api.py -k settings` (red: 12 failed) then full file | 103 passed |
| 8 | Step 7: types + API client; new `StatusPanel` (health values, stalled banner, kill switch with confirm both ways, view-only disabled); per-row "Paused by the kill switch"; `Run when acknowledged` checkbox + help text (and the enable switch now keeps it); new skip outcomes in labels/filter; 14 new tests, 2 existing adjusted | `npx vitest run src/test/RemediationPage.test.tsx` (red: 17 failed) then green; `npx tsc -b`; `npx eslint` on touched files | 41 passed; tsc clean; eslint 0 errors, 2 warnings (1 pre-existing `set-state-in-effect`, 1 same kind added) |
| 9 | Step 8: spec files (Backend routes/outcomes/consumer, Data Model columns/state table/purge/migration, Frontend panel, Implementation Status incl. stale Maintenance `failed` note) and `docs/manuals/Automatic_Recovery.md` (kill switch, acknowledged, health panel, stalled checklist) | `scripts/verify.sh docs` | all docs checks pass except the known Windows `test_qa_queue.py` backslash failure |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): only `scripts/test_qa_queue.py::test_shared_preview_rebases_relative_evidence_links` (known Windows backslash failure on untouched main)
- Hypothesis: n/a. Steps 1-8 done.
- Next action (one specific step, not "continue"): plan step 9: run `scripts/verify.sh all` (backend + frontend), note only known Windows failures; re-read `gh issue view 155` and prove each requirement; a person runs the lab case (stop the consumer and watch `stalled`; flip the kill switch during a forced failure) and `docs/test-runs/` report from `TEMPLATE.md`; then delete this progress file and open the PR (compare link, no Claude attribution).

## Decisions and notes

- Kill switch / retention are changed via `/api/system/remediation/settings` guarded by `remediation.manage` (the issue says "the Issue #7 permission"), not via the general Settings PUT (`settings.system`). They are not added to `SystemSettings.to_dict()`, so the Settings page is untouched. Audit through `create_configuration_log`.
- Heartbeat in its own one-row table so the 15 s tick does not touch the settings row's `Version`/`Updated_At`.
- Sensitive-module check: no command execution path changes and no untrusted input reaches a shell or Nagios config; spool deletion stays inside `REMEDIATION_SPOOL_DIR` and never follows symlinks. No Nagios config change, so no `regenerate_and_apply_config_status` needed for the new settings.
- Acknowledgement/downtime state is read from the newest `ServiceStatus`/`HostStatus` row (history bind). Open question to confirm in code: that #132 acknowledgements reach `Acknowledgement_Type` via the status poll (the poll is the only writer in `app/nagios/status.py`).
- Known pre-existing Windows failures: `tests/unit/test_automation.py::TestSecurityCheck::test_flags_broken_plugins_and_logs_summary`, `scripts/test_qa_queue.py`. `verify.sh` needs a `python3` shim outside the repo.
- `test_escalation_merge_migration.py` (2 cases) fails on clean main under Windows: `PermissionError` deleting a locked temp `history.db` at subprocess exit; migrations themselves run. Not caused by this issue.
- Spec text to fix in step 8: Data Model says the daily purge uses `Diagnostic_History_Retention_Days` for runs; it now uses `Remediation_Retention_Days`. Spool files older than 7 days are purged; the cap (1000) is enforced on every consumer tick, not daily, so a flood is bounded within 15 s.
- Health `stalled` threshold uses `app.scheduler.REMEDIATION_POLL_SECONDS` (15) x 3 = 45 s; `lastError` is always a fixed sentence (no paths). Backlog/oldest age use one listing plus one `lstat` of the oldest file.
- Frontend uses `window.confirm` for the kill switch, matching the existing delete confirmation on this page. The health card refreshes every 15 s.
