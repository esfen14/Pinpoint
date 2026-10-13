# Issue #113: System Implementation Add Configurable Notification Policy With Nagios Timeperiods and Settings Screen

Branch: `issue-113-notification-policy`
Status: in-progress

## Finish condition

- [ ] **Part 1.1 (System):** A policy with quiet hours produces a valid `define timeperiod` block, and hosts, services and contacts reference it.
- [ ] **Part 1.1 (System):** With the default policy, generated `hosts.cfg` is byte-identical to the output before this change.
- [ ] **Part 1.1 (System):** Saving an invalid policy (bad time, overlap, unknown option letter, interval out of range) returns 400 with a message that names the field.
- [ ] **Part 1.1 (System):** A stale `version` returns 409. A policy that Nagios rejects is rolled back and returns 422 with Nagios's message.
- [ ] **Part 1.1 (System):** Without `settings.system` the API returns 403.
- [ ] **Part 1.1 (System):** On a lab appliance, a forced state change inside a quiet window sends no notification, and the same change outside it does.
- [ ] **Part 1.1 (System):** Existing hosts, services, contacts and Check interval behavior are unchanged.
- [ ] **Part 1.2 (Web-Interface):** The old toggle's label and help text say it controls the header bell only.
- [ ] **Part 1.2 (Web-Interface):** A user with `settings.system` can add, edit and remove quiet-hour windows and change options and interval, and the values reload after a refresh.
- [ ] **Part 1.2 (Web-Interface):** Invalid input is blocked in the form with a message naming the field, and a server 400, 409 or 422 shows the server's message.
- [ ] **Part 1.2 (Web-Interface):** A user without the permission does not see the card and cannot reach it by URL.
- [ ] **Part 1.2 (Web-Interface):** The existing General and System settings tests still pass.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Implement NotificationPolicy model | Model creation | Unit test |
| Migration | Database migration | DB check |
| Timeperiod rendering | Nagios config | `nagios -v` |
| Parameterize templates | Template update | `test_create_host_cfg.py` |
| API endpoints | API endpoints | `test_notification_policy_api.py` |
| UI settings card | Frontend settings | Manual/automated test |
| Permissions check | Permission check | API test |

## Plan

1. [x] Create `NotificationPolicy` model in `server/app/system_models.py`.
2. [x] Add multi-bind migration via `flask db migrate` (the `--multidb` flag is unsupported in this repository's initialized multi-bind Alembic environment).
3. [x] Create `server/app/api/system/notification_policy.py` and register it in `server/app/api/system/__init__.py`.
4. [x] Create `server/app/network_discovery/templates/timeperiod.cfg.tpl` and update `host.cfg.tpl`, `service.cfg.tpl`, `contact_template.cfg.tpl` and rendering in `host_config_templates.py`.
5. [x] Update `server/app/network_discovery/create_host_cfg.py` to render the timeperiod in the candidate file.
6. [x] Create `client/src/types/notificationPolicy.ts` and `client/src/lib/notificationPolicyApi.ts`.
7. [x] Create `client/src/components/settings/NotificationPolicySettings.tsx`, place in permission-gated System tab through `SystemSettings.tsx`, and relabel General bell toggle.
8. [x] Strengthen generated-config regression and full contact/service propagation in `server/tests/unit/test_notification_policy_templates.py`, `server/app/network_discovery/create_host_cfg.py`, `server/app/network_discovery/host_config_templates.py`.
9. [x] Expand frontend permission/label tests in `client/src/test/NotificationPolicySettings.test.tsx` and related Settings tests; correct UI as needed.
10. [x] Review backend validation/apply edge cases and default byte parity in `server/tests/unit/test_notification_policy_api.py`, `server/tests/unit/test_notification_policy_templates.py` and owning backend modules.
11. [ ] Run approved Docker lab for `nagios -v` and inside/outside notification events; record sanitized evidence under `docs/test-runs/`.
12. [ ] Update manual and owning specs (`spec files/Backend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`), then verify finish conditions.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan created | N/A | N/A |
| resumed | Issue comment approves sensitive-module changes and repository Docker lab | N/A (no prior check run) | in-progress |
| 1 | Added failing model-default test then `NotificationPolicy` model | `.venv/bin/python -m pytest tests/unit/test_notification_policy.py -q`; `scripts/verify.sh backend` | focused green (1 passed); broad check timed out after 45%, not a test failure |
| 2 | Added failing migration round-trip test, generated multi-bind revision, manually seeded singleton | `.venv/bin/python -m pytest tests/unit/test_notification_policy_migration.py -q`; `scripts/verify.sh backend` | 1 passed; 2354 passed, 14 skipped |
| 3 | Added failing API cases; implemented guarded GET/PUT, validation and rollback; updated route catalog for drift check | `.venv/bin/python -m pytest tests/unit/test_notification_policy_api.py -q`; `scripts/verify.sh backend` | 11 passed; 2365 passed, 14 skipped |
| 4 | Added failing rendering test, conditional period and template directives preserving default | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend` | 2 passed; 2367 passed, 14 skipped |
| 5 | Added failing full-file test; render custom period in shared candidate config | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend` | 3 passed; 2368 passed, 14 skipped |
| resumed | No earlier plan steps repeated | `scripts/verify.sh backend` | green: 2368 passed, 14 skipped |
| 1 | Added failing client adapter test, typed wire contract and shared GET/PUT wrapper; fixed test typing after build exposed widened literals | `npm run test -- src/test/NotificationPolicyApi.test.ts`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-round1.log 2>&1` | green; 505 frontend tests and build/lint pass (25 warnings) |
| 2 | Added failing interaction suite, policy card on System tab and corrected bell-only label | `npm run test -- src/test/NotificationPolicySettings.test.tsx`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-round2.log 2>&1` | green: focused 5 passed; full frontend stage passed (26 warnings) |
| 3 | Added failing contact propagation/template-registration test; custom contacts inherit a non-registering policy template while default users retain generic-contact | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend > /tmp/opencode/issue113-backend-round3b.log 2>&1` | green: 4 focused; 2369 passed, 14 skipped |
| 4 | Added Settings permission/fragment and bell-label regression assertions; existing tab guard and corrected label already satisfied them | `npm run test -- src/test/SystemSettingsConflict.test.tsx src/test/PageAccess.test.tsx`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-round4.log 2>&1` | green: 27 focused tests; frontend stage green (26 warnings) |
| 5 | Reproduced boolean-version optimistic-lock bypass and rejected it before Nagios apply | `.venv/bin/python -m pytest tests/unit/test_notification_policy_api.py -q`; `scripts/verify.sh backend > /tmp/opencode/issue113-backend-round5.log 2>&1` | green: 12 focused; 2370 passed, 14 skipped |
| resumed | Re-read issue and continued at default byte-parity proof | `scripts/verify.sh backend > /tmp/opencode/issue113-resume-backend.log 2>&1` | green: 2370 passed, 14 skipped |
| 1 | Rendered identical isolated fixture on pre-change commit `92a896d5`; checked normalized output with `cmp`; added golden-file byte comparison with active email contact | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend > /tmp/opencode/issue113-backend-parity.log 2>&1` | green: 5 focused; 2371 passed, 14 skipped |

## State for the next session

- Last check run (exact command): `scripts/verify.sh backend > /tmp/opencode/issue113-backend-parity.log 2>&1`
- Result (first failing lines, or "green"): green: 2371 passed, 14 skipped.
- Hypothesis: Custom contact inheritance and timeperiod syntax require actual Nagios lab validation.
- Next action (one specific step, not "continue"): Read lab instructions and run approved Docker lab to check `nagios -v` on generated custom policy, then exercise quiet-window notifications.

## Decisions and notes

- Reusing `SystemSettings` singleton pattern for `NotificationPolicy`.
- `flask db migrate --multidb` and `flask db upgrade --multidb` are not recognized by installed Flask-Migrate; `flask db migrate` generated both default and history functions. Reviewed generated schema; manual seed necessary because autogenerate does not populate singleton data. Migration round trip tested on disposable databases.
- Resolved blocker: issue comment from esfen14 on 2026-10-13 approves and instructs use of repository Docker labs. No source code changed yet.
- The earlier pre-existing worktree modification to `client/src/test/SystemSettingsConflict.test.tsx` was not included in issue commits; inspect status before touching it.
- Prior session stopped at five rounds; step 10 now has an independent fixture from pre-change commit `92a896d5` and a byte comparison (timestamp normalized only). Plan revised because the original final step omitted explicit lab, documentation and regression stages; these are required deliverables. This session must verify actual default generated-file byte parity against pre-change output, not only template-level assertions. Also review timeperiod syntax against Nagios (`24:00` and comma-separated ranges) in the Docker lab, and review whether service default directives must be explicit without violating byte parity.
- Sensitive-module review pending: API validation whitelists weekday/time/option values, no shell interpolation introduced, generated file uses fixed destination and existing Nagios pre-apply validation; verify no secrets enter new logs or response. Lab acceptance and documentation remain unverified.
