# Test run: issue-113-notification-policy-vm

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | 1ca2c757 |
| Plan | docs/issues/issue-001.md §G; VM lab acceptance |
| Tester | OpenCode agent |
| Environment | Installer-built appliance VM, Nagios Core 4.5.11 |
| Raw evidence | Appliance healthcheck and configuration output |

## Result
**Overall: Pass.** VM appliance configured with quiet hours; `nagios -v` pre-flight check validates the generated `define timeperiod` and notification period references.

## Cases
| Case | Result | Notes | Issue |
|---|---|---|---|
| Config validation | Pass | `nagios -v` indicates zero errors/warnings in generated config. | #113 |
| Policy API apply | Pass | PUT request applied quiet hours successfully. | #113 |

## Sanitization checklist
- [x] No passwords, tokens, keys
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location
