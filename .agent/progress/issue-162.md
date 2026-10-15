# Issue #162: VM control ownership and overwritten-edit recovery

Branch: `issue-162-vm-control-recovery`
Status: in-progress

## Finish condition

- [ ] F1 Recover or explicitly resolve with the owner the two original uncommitted file versions; document recovery source and compare contents.
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
2. [ ] Add failing isolated preflight tests, implement fail-closed identity checks in scripts/vmlab and an owning helper, validate narrow checks.
3. [ ] Perform disposable-only snapshot marker trial if ownership is proved; otherwise record exact blocker and preserve inherited processes.
4. [ ] Update docs/plans/VM_Lab_Plan.md, spec files/Agent_Workflow_and_CI.md and spec files/Implementation_Status.md; verify finish conditions and scripts/verify.sh all; open PR with honest status.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Isolated checkout and issue coverage; owner asked for original edits | Read-only VBoxManage metadata, ps and ss | Two VBoxSVC processes; manager reports poweroff while SSH/web ports listen |

## State for the next session

- Last check run (exact command): VBoxManage showvminfo pinpoint-qa-appliance --machinereadable
- Result: VMState=poweroff; host ports 2250/18080 listening; VBoxSVC PIDs 130559 and 305485.
- Hypothesis: Independent IPC/control contexts share the registered VM; endpoint remains on inherited context. Cause not yet established.
- Next action: Inspect whitelisted process context, IPC sockets and endpoint ownership read-only; search retained source backups without writing to the appliance.

## Decisions and notes

- Workflow requested at .agents/workflows/work-issue.md is absent; canonical .agent/workflows/work-issue.md applies.
- All issue requirements map to finish conditions; no missing coverage.
- No inherited VM start/stop, snapshot, restore, sync or application mutation is authorized until control ownership is established.
- Owner question pending: source/backup or explicit resolution of the two overwritten uncommitted versions.
