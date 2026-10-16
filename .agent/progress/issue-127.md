# Issue #127: Per-device plugin variables API and SNMP v3 credentials with device form

Branch: `issue127-per_device_plugin_SNMP`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] 14.1 save/read/reset override; generated command changes (test_device_plugin_variables.py)
- [ ] 14.1 404 unknown plugin, 400 unknown key/invalid value, retired/merged refused
- [ ] 14.1 403 without permission
- [ ] 14.1 rejected Nagios config rolled back with 422
- [ ] 14.1 device with no override renders as before
- [ ] 14.2 v2c renders same command as before
- [ ] 14.2 v3 authPriv command uses macros, not literals
- [ ] 14.2 v3 missing field rejected 400 naming the field
- [ ] 14.2 no v3 password in hosts.cfg, responses, logs, snapshots
- [ ] 14.2 lab snmpd v3 monitored (LAB: needs a person)
- [ ] 14.3 drawer form sets version and v3 credentials; secrets never shown
- [ ] 14.3 missing fields per level blocked with message
- [ ] 14.3 Test action reports success or failure
- [ ] 14.3 existing plugin settings and drawer tests pass unchanged
- [ ] Deliverables F: migration (none expected), tests, spec files, help text, lab report (LAB: needs a person)
- [ ] Definition of Done H (PR items are for a person)

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Per-device variables API (C.1-5) | 14.1 items | test_device_plugin_variables.py |
| SNMP version + v3 (C.6-10) | 14.2 items | test_snmp_v3.py, test_create_host_cfg.py |
| Drawer form + Test (Frontend 1-3) | 14.3 items | DeviceSnmpSection.test.tsx |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [x] Registry: SNMP v3 variables, validation, v3 command (plugin_registry.py, new snmp_v3.py)
2. [x] Variables API GET/PUT/DELETE + test endpoint (new api/system/device_plugin_variables.py, register in api/system/__init__.py)
3. [x] Secrets: encrypt v3 passwords, collect into resource slots, render v3 command through adapter (create_host_cfg.py, scripts/pinpoint_check_native.py)
4. [x] Interface discovery: clear message for v3 devices (interface_discovery.py)
5. [x] Frontend: DeviceSnmpSection.tsx, lib api, types, drawer wiring, tests
6. [ ] Specs, Implementation_Status, help text; scripts/verify.sh all

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Registry snmp_v3 definition, enums, validate_snmp_v3; device_plugin_variables.py; tests (written with the code, registry import test was red first) | pytest test_snmp_v3.py | green (45) |
| 2 | v3 command generation: facts, slots, substitution, native adapter check_snmp support | pytest test_snmp_v3.py, test_native_resource_check.py | green |
| 3 | Variables API + snmp_check test action (tests red first: 49 failed) | pytest test_device_plugin_variables.py | green (55) |
| 4 | Interface discovery refuses v3 clearly | pytest test_interface_discovery.py | green |
| 5 | Frontend DeviceSnmpSection + api + types + drawer wiring (tests red first) | vitest full | 745 passed; npm run build ok |
| 6 | Specs (backend routes, data model, frontend, device inventory, status) | scripts/verify.sh docs | OK |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): cd client && npm run test; scripts/verify.sh docs
- Result (first failing lines, or "green"): green. Full backend run in background (deselecting tests/unit/test_ssh_port.py::TestHelperListenerPortEdit: uses GNU sed, fails on macOS BSD sed, unrelated)
- Hypothesis:
- Next action (one specific step, not "continue"): read /private/tmp/claude-501/backend_full.txt; if green run scripts/verify.sh frontend; then a person runs the lab (snmpd v3) and opens the PR

## Decisions and notes

- User said: do not push. Do NOT run scripts/agent_checkpoint.sh (it pushes); commit locally only.
- Branch name does not follow issue-<n>-slug; user chose it, kept.
- check_snmp passwords: use --extra-opts on stdin via pinpoint_check_native.py pattern so argv has no secret.
