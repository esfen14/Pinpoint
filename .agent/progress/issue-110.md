# Issue #110: Configurable Pinpoint-to-Nagios data polling interval

Branch: `issue-110-data-polling`
Status: in-progress

## Finish condition

- [ ] System UI offers exactly 30/60/120/300 seconds, default 60, permission settings.system, persisted across reload/restart with an upgrade migration.
- [ ] API strictly validates integers, protects writes, preserves omitted fields, version conflicts and audit policy.
- [ ] Saves reschedule one existing nagios_poll job; startup uses persisted interval with prompt first poll; no overlapping/interrupted polls.
- [ ] Reschedule/persistence failures restore saved value and job schedule; disabled scheduler stays disabled.
- [ ] General explains actual independent check/poll/browser values, including Manual.
- [ ] Automated coverage of all behavior, scripts/verify.sh all and green PR CI.
- [ ] Sanitized local-lab report identifies commit, start/end/skipped/coalesced runs at 30 and another supported value, live change and restart persistence.
- [ ] Update five issue-named specifications.

Requirement coverage (every issue requirement is included):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Exact options, defaults, persistence, migration and permission | 1, 2 | polling API, migration and UI tests |
| Validation, omitted compatibility, authorization, version and audit | 2 | polling API tests |
| Runtime reschedule, prompt startup, singleton job, non-overlap | 3 | real APScheduler isolated tests and local lab |
| Persistence/reschedule rollback and disabled scheduler | 4 | injected-failure tests |
| Independent discovery/check/retry/browser schedules and current descriptions | 5 | API and UI tests |
| Full automated verification and CI | 6 | scripts/verify.sh all; gh pr checks |
| Fixed owner-approved choices; lab verifies runtime | 7 | docs/test-runs polling report |
| Setting, permissions, independent schedules, runtime/failure docs | 8 | five specifications; scripts/verify.sh docs |

## Plan

1. [ ] Add failing backend API/scheduler/migration tests; implement Data_Polling_Interval model, multi-bind migration, scheduler reschedule/rollback service and settings API integration (server/app/{scheduler,system_models}.py, server/app/api/system/settings.py, server/migrations/versions/, server/tests/).
2. [ ] Add failing UI/context tests; implement typed default/control and saved schedule description (client/src/types/settings/, contexts/SystemSettingsContext.tsx, components/settings/{SystemSettings,GeneralSettings}.tsx, test/).
3. [ ] Update five owning specifications and server/tests/README.md; verify docs and all stages.
4. [ ] Run authorized local Docker lab polling cadence/change/restart checks; commit sanitized report and index (docs/test-runs/); verify finish conditions and open PR, monitor CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Backend API/model/migration and in-place scheduling implemented; regression tests first failed on missing field/revision, now green | FLASK_DEBUG=1 server/.venv/bin/python -m pytest server/tests/unit/test_data_polling.py server/tests/unit/test_data_polling_migration.py -q | 29 passed; full backend stage still running |
| Intake | Read issue/workflow/specifications and settings/scheduler sources; isolated checkout | gh issue view 110 --json number,title,body,state,labels,url,comments | Finish condition covers all requirements |

## State for the next session

- Last check run (exact command): FLASK_DEBUG=1 server/.venv/bin/python -m pytest server/tests/unit/test_data_polling.py server/tests/unit/test_data_polling_migration.py -q
- Result (first failing lines, or "green"): green (29 passed); backend stage in /tmp/issue-110-backend.log still running and has failures to inspect.
- Hypothesis: Reschedule the existing job under a shared settings-save lock, snapshot trigger/next_run_time for compensation on failed commit; do not recreate jobs or start a disabled scheduler.
- Next action (one specific step, not "continue"): Inspect completed backend/frontend stage logs, resolve regressions, then run scripts/verify.sh all.

## Decisions and notes

- Issue explicitly authorizes the schema migration and local-lab measurements. No sensitive network/config execution module changes are planned.
- Use isolated /tmp/Pinpoint-issue-110 checkout; main checkout stays untouched.
- Lab choices are fixed by owner at 30/60/120/300 seconds, not inferred from measurements.

- Continuation: UI tests first failed for missing polling default/control/hint; implemented all three, focused UI now 29 passed. Five issue-named specifications and tests README updated; docs stage green. Docker socket denied even outside sandbox; sudo requires authentication. User is enabling Docker access; live measurements must wait.
