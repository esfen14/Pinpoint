# Issue #154: Web-Interface Implementation Add Per-Service Recover Automatically Toggle With Restart Limit

Branch: `issue-154-recover-automatically`
Status: in-progress

## Finish condition

- [ ] 23.1 Enabling recovery creates one scoped action; generated config adds the handler to that service only; disabling removes it.
- [ ] 23.1 A request containing a unit name, command or path is rejected with 400.
- [ ] 23.1 A restart limit outside bounds is 400; stale `Version` is 409; Nagios-rejected config rolls back with 422.
- [ ] 23.1 A paused, retired or untrusted device returns a clear reason and cannot be enabled.
- [ ] 23.1 Without the permission the route returns 403.
- [ ] 23.2 The switch and limit save and reload, and match the Remediation screen for the same action.
- [ ] 23.2 A service with no valid action shows a disabled switch and the reason.
- [ ] 23.2 Users without the permission cannot see or use the control.
- [ ] Deliverables (section F): code, route docstrings, unit + API tests, frontend tests, spec updates (Backend, Data Model, Frontend, Implementation_Status), help text on the control, one admin-guide paragraph, `scripts/verify.sh all` green. No migration and no new permission (reuses remediation.view / remediation.manage, no model change).

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| GET/PUT per-service route, one scoped RemediationAction | 23.1 enabling | server/tests/unit/test_remediation_service_recovery.py |
| Request carries only enabled + max restarts; server picks type/unit | 23.1 unit/command 400 | same file |
| Return type or reason; Version 409 | 23.1 limit/409/422, device reason | same file |
| Issue #7 permission, regenerate_and_apply_config_status, 422 rollback | 23.1 403, 422 | same file |
| Switch + limit on Device Inventory service view, read-only on System Status row | 23.2 | client/src/test/ServiceRecoverySection.test.tsx |
| Disabled with server reason; warning text | 23.2 disabled | same |
| Last result + run link; loading/error/403/409 states | 23.2 | same |
| Hide without permission | 23.2 hide | same |
| Disabling takes effect via config regeneration | 23.1 disabling | test_event_handler_config.py style test in new file |
| Default config output unchanged | regression | existing test_event_handler_config.py / test_create_host_cfg.py |
| Not in issue: new action types, bulk enable | out of scope | n/a |

## Plan

1. [x] Backend tests first: server/tests/unit/test_remediation_service_recovery.py
2. [x] Backend: GET/PUT /system/remediation/services/<host>/<path:service> in server/app/api/system/remediation.py (unit choice helper, docs)
3. [ ] Frontend tests first: client/src/test/ServiceRecoverySection.test.tsx
4. [ ] Frontend: types/remediation.ts, lib/remediationApi.ts, components/device-inventory/ServiceRecoverySection.tsx, StatusDetailDrawer.tsx (service view), ServiceStatusTable read-only state
5. [ ] Specs: Backend_Modules_and_Routes.md, Data_Model_and_Integrations.md, Frontend_Modules_and_Routes.md, Implementation_Status.md, admin guide paragraph
6. [ ] scripts/verify.sh all, delete progress file, PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan | - | - |
| 1 | backend tests (67) then route + unit choice in api/system/remediation.py and app/remediation.py | pytest test_remediation_service_recovery + remediation/event handler/remote restart suites | 67 passed; 358 passed 1 skipped across related suites |

## State for the next session

- Last check run (exact command): cd server; python -m pytest tests/unit/test_remediation_service_recovery.py tests/unit/test_remediation_api.py tests/unit/test_remediation_consumer.py tests/unit/test_event_handler_config.py tests/unit/test_remote_restart.py -q
- Result: green
- Hypothesis: n/a
- Next action: step 3, write client/src/test/ServiceRecoverySection.test.tsx (drawer service view + System Status row)

## Decisions and notes

- Unit choice (owner decision 2026-10-18): match by name. Candidates for a service are its first dash-separated token (service names look like `ssh-22-tcp`) plus a small fixed alias table in code; the first candidate on the device's own restart list (remote) or on RESTARTABLE_UNITS (host `localhost`) wins. No request input picks the unit.
- Route is keyed by Nagios (hostname, service name), matching the existing network-health service routes; the pair must exist in the latest ServiceStatus snapshot (404 otherwise).
