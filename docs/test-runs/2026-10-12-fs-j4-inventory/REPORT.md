# Test run: fs-j4-inventory

| | |
|---|---|
| Date | 2026-10-12 |
| Commit tested | `24cac847` (`issue-105-qa-run`) |
| Plan | docs/qa/QA_Test_Plan.md |
| Tester | QA agent (tracking [#105](https://github.com/esfen14/Pinpoint/issues/105)) |
| Environment | Fresh Ubuntu 22.04.5 VirtualBox appliance; Nagios Core 4.5.11; authorized lab network `10.77.0.0/28`; fresh application databases |
| Raw evidence | Private vmlab state and sanitized local command results; not committed |

## Result

**Overall: Pass.** J4-01 was observed on a fresh installer-built appliance after
strictly replacing the installer default discovery network with `10.77.0.0/28`.
The Plugin Manager browser route loaded for the administrator, and its backing
summary and complete inventory agreed on the required 65 installed plugins.

Totals: Pass 1, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| J4-01 | Pass | Following a restricted discovery smoke, `GET /api/plugin/summary` reported 65 installed plugins. The complete `GET /api/plugin?per_page=100&sort_by=name&order=asc` inventory reported total 65 and returned 65 items. The administrator browser smoke loaded the authenticated app route. | — |

## Deviations from the plan

- The installer initially configured its own NAT network. Before discovery, the
  QA preflight read the setting and replaced it with exactly `10.77.0.0/28`; the
  read-back confirmed no other discovery range remained. The restricted smoke
  then completed successfully in 164 seconds with all five targets Up.
- The first restricted smoke used the plan's default 300-second terminal-status
  timeout but the host list had not fully refreshed when it expired. Its run was
  not used as case evidence. The appliance was reverted and freshly deployed;
  the repeated smoke with the written restricted range and an extended timeout
  completed successfully before J4-01 was claimed.
- The UI-specific Plugin Manager tile/table count remains a later browser case:
  J4-01's required inventory and summary observations were made through the
  authenticated application API; the browser smoke establishes the authenticated
  browser lane only.

## Follow-up

- Defects found: none.
- Lab restoration: after the observed case, the temporary restricted account was
  reset and `scripts/vmlab revert` restored the `os-nagios-ready` snapshot.
- Cases to repeat in the next run: J4-02 and browser-specific Plugin Manager
  coverage; do not rely on this restored appliance state.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
