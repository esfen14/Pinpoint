# Test run: issue-182-remote-restart

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `910d6f99` |
| Plan | server/tests/plans/REMOTE_RESTART_ACCEPTANCE.md |
| Tester | Codex agent |
| Environment | Fresh Ubuntu 22.04.5 appliance, Nagios 4.5.11; separate Ubuntu target; exclusive internal virtual network using 10.77.0.0/28; scans restricted to 10.77.0.2/32 |
| Raw evidence | Local host /tmp/issue182-*.log (temporary, uncommitted) |

## Result

**Overall: Partial.** Fresh installation passed all 60 installer health checks, the full local automated gate passed, and supported first-run setup succeeded. Remote execution cases are pending target deployment.

Totals: Pass 1, Fail 0, Blocked 0, Skipped 12.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| ENV-01 | Pass | Fresh pushed issue branch installed at `910d6f99`; migration `a182f6c9d301`; 60 health checks passed; supported first-run setup succeeded. `issue182-vm-fresh.log`; setup output | — |
| RR-01 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-02 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-03 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-04 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-05 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-06 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-07 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-08 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-09 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-10 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-11 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |
| RR-12 | Skipped | Pending acceptance execution in this run | [#182](https://github.com/esfen14/Pinpoint/issues/182) |

## Deviations from the plan

The previous session cloned the disposable target after the new-VM preflight refused creation while the appliance was running. Existing VMs were untouched; this session proved the clone powered off with no endpoint listeners before configuring it, then proved process/controller/runtime-forward ownership after startup. Both guests use a separate issue182 internal network; all pre-existing target VMs remain off.

The setup helper expects an older installer credential label (existing #167). First-run setup was completed with the supported API, parsing the current installer format privately; no product or helper changes were made.

## Follow-up

- Pending: RR-01 through RR-12; human security review and PR CI.
- Existing compatibility finding: [#167](https://github.com/esfen14/Pinpoint/issues/167).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
