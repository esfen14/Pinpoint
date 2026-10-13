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
2. [ ] Add migration with `flask db migrate --multidb`.
3. [ ] Create `server/app/api/system/notification_policy.py` and register it in `server/app/api/system/__init__.py`.
4. [ ] Create `server/app/network_discovery/templates/timeperiod.cfg.tpl` and update `host.cfg.tpl`, `service.cfg.tpl`, `contact_template.cfg.tpl`.
5. [ ] Update `server/app/network_discovery/create_host_cfg.py` to use `NotificationPolicy`.
6. [ ] Create `client/src/types/notificationPolicy.ts` and `client/src/lib/notificationPolicyApi.ts`.
7. [ ] Create `client/src/components/settings/NotificationPolicySettings.tsx` and integrate it into `SettingsPage.tsx`.
8. [ ] Implement tests and verify.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan created | N/A | N/A |
| resumed | Issue comment approves sensitive-module changes and repository Docker lab | N/A (no prior check run) | in-progress |
| 1 | Added failing model-default test then `NotificationPolicy` model | `.venv/bin/python -m pytest tests/unit/test_notification_policy.py -q`; `scripts/verify.sh backend` | focused green (1 passed); broad check timed out after 45%, not a test failure |

## State for the next session

- Last check run (exact command): `scripts/verify.sh backend` (120000 ms timeout)
- Result (first failing lines, or "green"): Timed out at 45% of pytest; no failure observed. Focused test green (1 passed).
- Hypothesis: Isolated suite needs more than 120 seconds.
- Next action (one specific step, not "continue"): Write failing migration upgrade/downgrade test, then generate and review multi-bind migration.

## Decisions and notes

- Reusing `SystemSettings` singleton pattern for `NotificationPolicy`.
- Need to ensure `flask db migrate` correctly handles the new table.
- Resolved blocker: issue comment from esfen14 on 2026-10-13 approves and instructs use of repository Docker labs. No source code changed yet.
- Pre-existing worktree modification: `client/src/test/SystemSettingsConflict.test.tsx` was already modified at branch creation; do not overwrite or include it.
