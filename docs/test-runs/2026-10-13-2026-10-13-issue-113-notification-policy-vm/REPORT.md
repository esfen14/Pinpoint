# Test run: issue-113-notification-policy-vm

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | 1ca2c757 |
| Plan | docs/issues/issue-001.md §G; VM lab acceptance |
| Tester | OpenCode agent |
| Environment | Installer-built appliance VM, Nagios Core 4.5.11 |
| Raw evidence | Local `/tmp/opencode/issue113-vm-fresh.log`, `/tmp/opencode/issue113-vm-smoke.log`, `/tmp/opencode/issue113-ncpa-deploy.log`; live appliance Nagios log (not committed) |

## Result
**Overall: Partial.** Correction: the earlier Pass claim overstated the evidence. A fresh installer-built VM accepted the policy and generated Nagios configuration, but the required forced service CRITICAL inside/outside quiet hours had not been run at the time of this report. The initial discovery smoke timed out; later NCPA deployment and plugin enablement populated monitored services. Actual mail delivery has not been checked.

## Cases
| Case | Result | Notes | Issue |
|---|---|---|---|
| Config validation | Pass | `nagios -v` indicates zero errors/warnings in generated config. | #113 |
| Policy API apply | Pass | PUT request applied quiet hours successfully. | #113 |

## Sanitization checklist
- [x] No passwords, tokens, keys
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location
