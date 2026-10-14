# Test run: issue-128-ncpa-services

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | `fa728583` for initial defaults/process/load; `f00926f7`, integrated `714f4f03` and final hardened `ba4451ce` synced for settings/skipping/process repeats |
| Plan | Issue [#128](https://github.com/esfen14/Pinpoint/issues/128), sections E and G |
| Tester | Codex |
| Environment | Fresh Docker lab Ubuntu 22.04, Nagios Core 4.5.11/plugins 2.4.12; two NCPA 3.5.0 runtime targets on documented isolated network `10.78.0.0/24`; fresh seeded database |
| Raw evidence | Local git-ignored `test-results/issue-128/`: `live-seed.log`, `live-default-states.json`, `live-process-states.json`, `live-settings-skips.log`, `live-load.json`, `live-final-settings.log`, `live-final-states.log`, `live-merged-settings.log`, `live-merged-states.log`, `live-hardened-settings.log`, `live-hardened-states.log` |

## Result

**Overall: Pass for the scoped Docker metric/process/skipping cases.** Both targets reached OK for all six defaults and the process check. A deliberately unsupported path produced two skipped-service reasons and no Nagios service. This is not installer, independent-host scale, browser walkthrough or reviewer approval evidence.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Generate confirmed defaults through shared reconciler/writer | Pass | Validation/reload succeeded as the appliance service user; initial apply 0.216 seconds | |
| Original metrics/names | Pass | `ncpa-cpu-5693-tcp`, `ncpa-memory-5693-tcp`, `ncpa-disk_root-5693-tcp` preserved on both agents | |
| New default services | Pass | `ncpa-swap-5693-tcp`, `ncpa-disk_read-5693-tcp`, `ncpa-disk_write-5693-tcp`, all state 0/OK on both targets; counter units MiB/s | |
| Default service count | Pass | Six per target with one partition and sda, previously three; formula 5 + partition count where both sda counter paths exist | |
| Process API save and actual check | Pass | Existing protected settings route accepted generated `processes`, `name=sshd`, warning/critical `1:1`; Nagios process count 1/OK on both targets; final source repeated save/apply | |
| Unsupported-path skipping | Pass | Added `disk/physical/no_such_device/read_bytes`; planner omitted only that metric on each target, with a reason; existing SkippedService logging helper persisted reasons; actual Nagios has no unavailable service | |
| Lab Nagios load | Pass | Three samples ten seconds apart: eight Nagios processes, aggregate CPU 0.0% at ps display precision, summed RSS 38,500 KiB; 14 target services OK, max execution 0.720 s, max latency 0.001 s | |
| NCPA installation/systemd | Skipped | Official package runtime extracted and started directly; container lacks systemd; this issue verifies metric paths/checks, not deployment installation | |
| Independent-host scale | Skipped | Targets share the Docker host kernel/disks; load sample shows this small lab only | |
| Browser walkthrough | Skipped | Guided UI covered by interaction tests; lab save used authenticated Flask client against real lab database and writer | |

## Deviations from the plan

Agents were initially probed with networking disabled, then recreated on the isolated lab network for real Nagios checks. Targets were seeded as discovered/deployed records without a network scan or SSH install. The official `check_ncpa.py` from tag v3.5.0 was installed in the disposable appliance with its shebang pointing to the appliance Python environment, because the lab image does not bundle it. The first apply attempted as root could not validate a root-only temporary config after Nagios dropped privileges; rerunning as the normal `pinpoint` service user succeeded. No application security or validation path was bypassed.

The agent exposes no confirmed load-average node; no such default was added, as permitted by issue C.2. See [the capability report](../2026-10-14-issue-128-ncpa-probe/REPORT.md).

## Follow-up

Full automated verification and GitHub CI results belong on the PR. Reviewer approvals remain a human merge requirement. Disk-rate thresholds are editable starting points; validate them for production hardware/workload.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
