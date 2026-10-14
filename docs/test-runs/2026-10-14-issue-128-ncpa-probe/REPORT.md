# Test run: issue-128-ncpa-probe

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | `c006935b` (application unchanged; agent capability probe) |
| Tester | Codex |
| Environment | Two Ubuntu 22.04 Docker targets, network disabled, official NCPA 3.5.0 DEB extracted and started directly; no systemd/install acceptance implied |
| Raw evidence | Local `test-results/issue-128/agent01-probe.json`, `agent02-probe.json`, `agent01-extra.json`, `agent02-extra.json` (git-ignored) |

## Result

**Overall: Partial.** Agent paths and process-count syntax were observed on two targets. Application defaults, generated Nagios services and load have not yet been tested.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Agent version on both targets | Pass | `system/agent_version` returns 3.5.0 | |
| Swap usage on both targets | Pass | `memory/swap/percent` returns 0.0, unit `%` | |
| Disk read/write counters on both targets | Pass | `disk/physical/sda/read_bytes` and `write_bytes` return numeric values; raw default unit GiB; root lists sda and other physical nodes | |
| Process count on both targets | Pass | `processes`, query `name=sshd`, exact match by default, warning/critical `1:1`, check=1 returns code 0 and count 1 | |
| Load-average candidates | Skipped | Root has no load-average node; `load`, `load_average`, `cpu/loadavg`, `cpu/load_average`, `system/load` return error 100. Issue permits only confirmed paths as defaults | |
| Generated services and Nagios load | Skipped | Probe only; implementation and later acceptance run pending | [#128](https://github.com/esfen14/Pinpoint/issues/128) |

## Deviations from the plan

The existing targets lack init, so the official package runtime was started directly in isolated containers. This verifies API behavior, not deployment installation. Both containers share the host kernel and disks; they are not independent performance targets.

## Follow-up

Test counter rates with `units=Mi,delta=1`, application skipping, generated services and Nagios load after implementation. No load-average default is justified by these agents.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
