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

1. [ ] Models + migration: `SystemSettings.Remediation_Enabled` (default true), `Remediation_Retention_Days` (default 90); `RemediationAction.Run_When_Acknowledged` (default false); new `RemediationOutcome` members `SKIPPED_KILL_SWITCH`, `SKIPPED_MAINTENANCE`, `SKIPPED_DOWNTIME`, `SKIPPED_ACKNOWLEDGED`; new singleton table `REMEDIATION_CONSUMER_STATE`. Files: `server/app/system_models.py`, new `server/migrations/versions/*`, `server/tests/unit/test_remediation_migration.py` (+ runner in `tests/support/`).
2. [ ] Skip checks in the consumer: kill switch, Maintenance Mode (all types), scheduled downtime, acknowledged (unless `Run_When_Acknowledged`), then cooldown/cap; one row per skip with its reason. Files: `server/app/remediation.py`, `server/tests/unit/test_remediation_consumer.py`.
3. [ ] Action API: accept and return `runWhenAcknowledged`; outcome filter accepts the new outcomes; run items show them. Files: `server/app/api/system/remediation.py`, `server/tests/unit/test_remediation_api.py`.
4. [ ] Retention: purge uses `Remediation_Retention_Days`; delete spool files older than a fixed age; cap spool entries (oldest dropped, count recorded in the state row and logged). Files: `server/app/scheduler.py`, `server/app/remediation.py`, `server/tests/unit/test_scheduler.py`.
5. [ ] Heartbeat + health: record last tick/error each consumer run; `GET /api/system/remediation/health` (`remediation.view`) with last tick, backlog, oldest spool age, runs and caps in 24 h, `stalled`. Files: `server/app/remediation.py`, `server/app/api/system/remediation.py`, tests.
6. [ ] Settings routes: `GET`/`PUT /api/system/remediation/settings` (`remediation.manage` to write), validation, `ConfigurationChanges` audit, 403 path. Files: `server/app/api/system/remediation.py`, `server/tests/unit/test_remediation_api.py`.
7. [ ] Frontend: types + API client; health card with stalled banner; kill switch with confirmation and per-row state; `Run when acknowledged` option; skip reasons in `RunLog`/`RunDrawer`; loading/error/403 states. Files: `client/src/lib/remediationApi.ts`, `client/src/pages/RemediationPage.tsx`, `client/src/components/remediation/*`, `client/src/test/RemediationPage.test.tsx`.
8. [ ] Docs: spec files (Backend, Data Model, Frontend, Implementation Status), page help text, admin note on a stalled consumer. Run `scripts/verify.sh docs`.
9. [ ] Full verify (`scripts/verify.sh all`), delete progress file, PR. Lab report in `docs/test-runs/` needs the lab appliance: a person must run it (live lab is off limits unless the issue says so; it does, in section G, but ask first).

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Branch created from origin/main; plan written | none | n/a |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: n/a
- Next action (one specific step, not "continue"): plan step 1: write the migration test in `server/tests/unit/test_remediation_migration.py` for the new columns/table/outcome members, watch it fail, then edit `server/app/system_models.py` and add the migration.

## Decisions and notes

- Kill switch / retention are changed via `/api/system/remediation/settings` guarded by `remediation.manage` (the issue says "the Issue #7 permission"), not via the general Settings PUT (`settings.system`). They are not added to `SystemSettings.to_dict()`, so the Settings page is untouched. Audit through `create_configuration_log`.
- Heartbeat in its own one-row table so the 15 s tick does not touch the settings row's `Version`/`Updated_At`.
- Sensitive-module check: no command execution path changes and no untrusted input reaches a shell or Nagios config; spool deletion stays inside `REMEDIATION_SPOOL_DIR` and never follows symlinks. No Nagios config change, so no `regenerate_and_apply_config_status` needed for the new settings.
- Acknowledgement/downtime state is read from the newest `ServiceStatus`/`HostStatus` row (history bind). Open question to confirm in code: that #132 acknowledgements reach `Acknowledgement_Type` via the status poll (the poll is the only writer in `app/nagios/status.py`).
- Known pre-existing Windows failures: `tests/unit/test_automation.py::TestSecurityCheck::test_flags_broken_plugins_and_logs_summary`, `scripts/test_qa_queue.py`. `verify.sh` needs a `python3` shim outside the repo.
