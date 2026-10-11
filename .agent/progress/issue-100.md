# Issue #100: QA: Functional Suitability VM-lab test run (2026-10-12)

Branch: `issue-100-qa-run`
Status: in-progress

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] VM baseline is confirmed and only `10.77.0.0/28` is scanned.
- [ ] Up to five FS cases are observed and recorded.
- [ ] Lab mutations are restored.
- [ ] QA report, traceability, progress record, and documentation verification are complete.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Prepare the appliance and five targets using `scripts/vmlab` | VM baseline confirmed | `scripts/vmlab fresh`, `status`, target-state confirmation |
| Execute up to five unblocked FS cases | FS cases observed | Written QA-plan case steps and sanitized API/UI/Nagios evidence |
| Record results, traceability and lab restoration | Report/docs complete; restoration complete | Report/index/matrix changes, `scripts/verify.sh docs`, restored target/plugin/user state |

## Plan

1. [x] Create the required tracking issue and dedicated worktree/branch; inspect the QA workflow, plans, traceability matrix, lab plan and status inventory.
2. [x] Prepare the VM appliance with `scripts/vmlab fresh`; verify the snapshot stamp and confirm the five required target VMs are running. Remove only the owner-approved inaccessible VirtualBox registrations.
3. [ ] Run the QA entry gate: establish a clean baseline with `scripts/vmlab setup-admin` and `scripts/vmlab smoke`, confirm the configured discovery network is exactly `10.77.0.0/28`, and create the sanitized test-run report.
4. [ ] Execute no more than five unblocked Functional Suitability cases in written-plan order, starting with J1-02 and J2-01; preserve observations, repeat any failure once, and restore mutations.
5. [ ] Update report/index and traceability only for fully observed cases; search/file/link issues per `qa-run.md` as needed.
6. [ ] Run `scripts/verify.sh docs`, update this progress record, checkpoint the QA round, and report restoration/unverified cases.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Created QA tracking issue #100 and dedicated worktree; owner approved removal of inaccessible registrations only. | `scripts/vmlab fresh`; `scripts/vmlab status`; `VBoxManage list runningvms` | Fresh appliance deployment passed healthcheck: 60 passed, 0 warnings, 0 failed. Snapshot stamp matches installer. All five required target VMs are running. |

## State for the next session

- Last check run (exact command): `scripts/vmlab status`
- Result (first failing lines, or "green"): Green: appliance running; `os-nagios-ready` exists and its base-step stamp matches installer commit `2859361`.
- Hypothesis: The fresh appliance is ready. Completing bootstrap setup and the restricted discovery smoke will establish B0 before any FS case is claimed.
- Next action (one specific step, not "continue"): Run `scripts/vmlab setup-admin`, then `scripts/vmlab smoke`, and inspect its sanitized outcome before claiming J1-02 or J2-01.

## Decisions and notes

- User authorized test-VM cleanup and selected only removal of the two inaccessible VirtualBox registrations. They were unregistered without deleting usable VM disks.
- Required Pinpoint lab VMs: `pinpoint-qa-appliance` and targets `pinpoint-demo-web01`, `web02`, `app01`, `snmp01`, `legacy01`. Do not alter other registered test VMs.
- The `qa-run.md` workflow allows at most five test rounds in this session. Human-labelled FS cases (J1-06 and J5-11) remain untested without attributable human evidence.
- Live scans must remain exactly within `10.77.0.0/28`; never run the libvirt harness.
