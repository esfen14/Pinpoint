# Issue #101: QA: Functional Suitability plugin-manager VM-lab run (2026-10-12)

Branch: `issue-101-qa-run`
Status: in-progress

## Finish condition

- [ ] The exclusive VM-lab baseline and `10.77.0.0/28` scan restriction are revalidated.
- [ ] Up to five claimed FS cases are observed and recorded.
- [ ] Mutable plugin/lab state is restored.
- [ ] Report, traceability, progress record and docs verification are complete.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Revalidate safe baseline and discovery guard | Baseline restriction revalidated | `scripts/vmlab status`, target status, authenticated settings/status readback |
| Execute up to five unblocked FS plugin cases | Cases observed and recorded | J4-01 through J4-07 as prerequisites permit, with live API/Nagios evidence |
| Restore mutable state | Plugin/lab state restored | Disable enabled plugins after observations or document retained prerequisite state |
| Record test outcome | Report/docs complete | Sanitized report/index/matrix, `scripts/verify.sh docs`, checkpoint |

## Plan

1. [x] Create the tracking issue and dedicated worktree; read QA workflow, plugin requirements/plans and current lab state.
2. [ ] Authenticate to the running appliance and read discovery networks/status; reject the run if any configured scan range is outside `10.77.0.0/28` or a scan is active.
3. [ ] Claim and execute J4-01, J4-02 and J4-03, including live inventory/scan/enable observations and Nagios config/status evidence.
4. [ ] Execute the next prerequisite-satisfied FS cases, at most five total, restore plugin/lab state, and repeat any failure once before issue triage.
5. [ ] Create a sanitized report; update index and traceability for only full observations; verify docs and checkpoint.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Created tracking issue #101 and a dedicated worktree; reviewed plugin and QA requirements. | `scripts/vmlab status`; `scripts/vmlab targets up` | Appliance is running, base snapshot stamp matches; all five required targets are already running. |

## State for the next session

- Last check run (exact command): `scripts/vmlab targets up`
- Result (first failing lines, or "green"): Green: all five target VMs already running.
- Hypothesis: The appliance retained the restricted discovery baseline from the preceding FS round; it must be read back before a mutating plugin case.
- Next action (one specific step, not "continue"): Authenticate to the appliance and read `/api/system/discovery-settings` and `/api/system/discover/status` to establish the required guard.

## Decisions and notes

- The previous FS run (#100) is recorded separately and established a fresh appliance baseline. This run may alter plugin state only after the guard is read back.
- Scan scope is only `10.77.0.0/28`; never use the libvirt harness.
- The lab's existing NCPA deployment/cert state is not evidence that a plugin is already enabled; read the live plugin summary before case selection.
- Human-only FS cases are not eligible without attributable human evidence.
