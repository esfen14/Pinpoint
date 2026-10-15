# Issue #162: VM control ownership and overwritten-edit recovery

Branch: `issue-162-vm-control-recovery`
Status: in-progress

## Finish condition

- [x] F1 Recover or explicitly resolve with the owner the two original uncommitted file versions; document recovery source and compare contents.
- [ ] F2 Identify why separate VBoxSVC instances could control the same registered appliance UUID while SSH remained attached to the inherited process.
- [ ] F3 Before mutation, preflight proves the controlled VM process owns intended loopback SSH/web endpoints; fail closed on duplicate control/processes or ambiguous ownership.
- [ ] F4 Verify snapshot take/change/restore through an endpoint marker in a disposable lab without inherited application data.
- [ ] F5 Record sanitized recovery evidence, update VM preflight documentation, and pass relevant verification.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Recover dashboard.py and nagios/status.py at inactive 1ca2c75 checkout | F1 | Read-only retained-file search, hashes and comparison; owner decision if no exact source |
| Explain duplicate managers and endpoint mismatch | F2 | Read-only process, IPC namespace/socket and listener ownership inspection |
| Enforce control/endpoint identity before mutation | F3 | Isolated preflight regression tests and live read-only preflight |
| Endpoint snapshot marker in disposable lab | F4 | Dedicated new VM and marker report, only after ownership established |
| Sanitized evidence and documentation | F5 | docs/test-runs report; scripts/verify.sh docs and all |
| Preserve inherited work; no destructive reproduction or VM mutation before ownership | F2/F4 | Read-only diagnosis; distinct disposable VM identity/ports for any trial |
| #79 external inbox acceptance separate | Out of scope | No recipient-feature or external-mail changes |

## Plan

1. [ ] Diagnose ownership and search recovery sources read-only; record sanitized evidence in docs/test-runs/2026-10-15-issue-162-recovery/REPORT.md.
2. [x] Add failing isolated preflight tests, implement fail-closed identity checks in scripts/vmlab and an owning helper, validate narrow checks.
3. [ ] Perform disposable-only snapshot marker trial if ownership is proved; otherwise record exact blocker and preserve inherited processes.
4. [ ] Update docs/plans/VM_Lab_Plan.md, spec files/Agent_Workflow_and_CI.md and spec files/Implementation_Status.md; verify finish conditions and scripts/verify.sh all; open PR with honest status.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Isolated checkout and issue coverage; owner asked for original edits | Read-only VBoxManage metadata, ps and ss | Two VBoxSVC processes; manager reports poweroff while SSH/web ports listen |

| 1 | Added preflight helper, gated mutation commands and CI docs-stage tests | python3 -I scripts/test_vmlab_preflight.py; scripts/verify.sh docs; scripts/vmlab preflight (host) | 13 tests and docs green; live preflight correctly rejects existing duplicate managers |

## State for the next session

- Last check run (exact command): scripts/vmlab preflight
- Result: expected failure, ownership ambiguous; two VBoxSVC processes still present. Isolated 13 tests and scripts/verify.sh docs green.
- Hypothesis: Two distinct listening IPC socket inodes at the same pathname establish a split service context after pathname replacement/rebind; actor is unknown. Protected VM fd metadata prevents endpoint attribution.
- Next action: Record sanitized process/source comparisons and blocked disposable marker trial; update owning documentation and run all verification.

## Decisions and notes

- Workflow requested at .agents/workflows/work-issue.md is absent; canonical .agent/workflows/work-issue.md applies.
- All issue requirements map to finish conditions; no missing coverage.
- No inherited VM start/stop, snapshot, restore, sync or application mutation is authorized until control ownership is established.
- Owner question pending: source/backup or explicit resolution of the two overwritten uncommitted versions.

- Owner has no backup and confirms the edits should have been preserved; this is not acceptance of lost edits. Recovery remains unresolved.
- Guest read-only search found the same dashboard/status SHA-256 in all three retained checkouts, no independent backup in searched paths.
- Host sudo read-only fd inspection unavailable (sudo requires a password); do not weaken guard or kill inherited processes.
- Command-execution review: new helper uses subprocess argument lists, no shell interpolation, no credentials or raw command output logged. Missing metadata fails closed.

- 2026-10-15 owner explicitly authorized: "Remove the old disks and remake the Lab"; acceptance of loss separately confirmed: "Accept as unrecoverable but document loss". F1 resolved by owner decision, not by recovery. Old lab disks may be removed; unrelated VMs remain outside scope.
- Plan revision after owner decision: retire old appliance and pinpoint-demo-* lab VMs, reset split controllers after children are stopped, build clean appliance/targets, and perform endpoint marker trial. Record exact target UUID inventory before teardown.
