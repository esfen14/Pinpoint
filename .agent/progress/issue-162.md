# Issue #162: VM control ownership and overwritten-edit recovery

Branch: `issue-162-vm-control-recovery`
Status: ready-for-review

## Finish condition

- [x] F1 Recover or explicitly resolve with the owner the two original uncommitted file versions; document recovery source and compare contents.
- [x] F2 Identify why separate VBoxSVC instances could control the same registered appliance UUID while SSH remained attached to the inherited process.
- [x] F3 Before mutation, preflight proves the controlled VM process owns intended loopback SSH/web endpoints; fail closed on duplicate control/processes or ambiguous ownership.
- [x] F4 Verify snapshot take/change/restore through an endpoint marker in a disposable lab without inherited application data.
- [x] F5 Record sanitized recovery evidence, update VM preflight documentation, and pass relevant verification.

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

1. [x] Diagnose ownership and search recovery sources read-only; record sanitized evidence in docs/test-runs/2026-10-15-issue-162-recovery/REPORT.md.
2. [x] Add failing isolated preflight tests, implement fail-closed identity checks in scripts/vmlab and an owning helper, validate narrow checks.
3. [x] Perform disposable-only snapshot marker trial if ownership is proved; otherwise record exact blocker and preserve inherited processes.
4. [x] Update docs/plans/VM_Lab_Plan.md, spec files/Agent_Workflow_and_CI.md and spec files/Implementation_Status.md; verify finish conditions and scripts/verify.sh all; open PR with honest status.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Isolated checkout and issue coverage; owner asked for original edits | Read-only VBoxManage metadata, ps and ss | Two VBoxSVC processes; manager reports poweroff while SSH/web ports listen |

| 1 | Added preflight helper, gated mutation commands and CI docs-stage tests | python3 -I scripts/test_vmlab_preflight.py; scripts/verify.sh docs; scripts/vmlab preflight (host) | 13 tests and docs green; live preflight correctly rejects existing duplicate managers |

| 2 | Owner accepted loss and authorized deleting/rebuilding old lab; retired seven VMs/disks; rebuilt appliance from ISO. Replaced unsupported SessionPID/fd requirement with unique same-controller VM process plus live NAT HOST_FORWARD socket proof | python3 -I scripts/test_vmlab_preflight.py; scripts/verify.sh docs; scripts/vmlab preflight | 15 tests/docs green; positive live preflight passed for new UUID 351eb491-f5e1-4854-a7e4-68309ad774ad |

| 3 | Added runtime-forward edge cases, completed sanitized diagnosis/source-loss report and owning documentation | scripts/verify.sh all; scripts/verify.sh docs; python3 -I scripts/test_vmlab_preflight.py; git diff --check | All green: 2777 backend passed/14 skipped, 628 frontend passed, build/lint green (29 existing warnings), 17 ownership tests |

| resumed | User continued after interrupted wait; retained running installs and completed work | Existing logs and process inventory | Continued without restarting installs |
| 4 | Rebuilt all five targets/base and clean appliance, provisioned Nagios and deployed main; verified real SSH+HTTP snapshot marker change/restore | python3 /tmp/issue162-marker-trial.py; scripts/vmlab health; scripts/vmlab targets wall --once | Endpoint restore PASS; snapshot ebf767b5-9d26-49a9-b76e-ab747084809b; 60 health checks pass; all target services UP |

| 5 | Recheck preflight immediately before SSH and key-bootstrap actions and forced power-off; regression proves a changed controller cannot fall through to SSH even in Bash conditional contexts | python3 -I scripts/test_vmlab_preflight.py; bash -n scripts/vmlab; scripts/vmlab preflight; scripts/verify.sh docs | 18 tests, syntax, live positive ownership and docs green; original full suites/CI green, final CI pending updated commit |

| finish | Re-read unchanged issue requirements; finalized reports, index and owning specifications after health/smoke proof | scripts/verify.sh all; scripts/verify.sh docs; git diff --check | Final full verification green; 18 ownership tests green; all finish items proven |

## State for the next session

- Last check run (exact command): scripts/verify.sh all
- Result: green on the final implementation and documentation. Real SSH/HTTP marker restore, 9/9 discovery smoke and 60/60 final health checks passed. Latest implementation CI passed; final evidence/progress-removal commit CI remains to run.
- Hypothesis: All finish conditions are proven; no implementation or lab work remains.
- Next action: Delete this progress file, commit/push the final branch, update PR #165 from the template and mark ready after final CI passes.

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

- Live evidence changed the guard design: VirtualBox 7.2 omits SessionPID from showvminfo and SUID VM launchers protect /proc/PID/fd even for their owner. The runtime `VBoxManage debugvm ... info nat0` table exposes active TCP HOST_FORWARD socket descriptors. Guard now requires these exact SSH/web listeners and destination services plus exclusive host listeners, the unique UUID process and its sole parent controller. Unsupported/missing NAT output rejects; no sudo requirement was introduced.
- Retired UUID inventory saved privately in test-results/issue162/retired-inventory.json. Retired only configured appliance, demo base and five targets; unrelated/legacy registered VMs retained.

- Main deployment needed a transport workaround: the NodeSource single-stream download was exceptionally slow. Downloaded byte ranges on host, assembled the exact 37,783,800-byte package and verified SHA-256 31eef6210cb50f9031afb59e7f1ed741d40db5d39f0894372b19444f33c4996e against guest APT metadata, cached it, interrupted only the pending nodejs download, and resumed the unchanged installer deploy/privilege scripts. Original failed transport attempt is retained in ignored logs.
- Installer clean checkout is 697869e. No inherited application disk/database was used; positive blank /opt/pinpoint check observed before deployment. Appliance PINPOINT_NETWORKS fallback restricted to 10.77.0.0/28 before any discovery.
- Marker trial used a non-secret file under fresh client/dist and required the same value via SSH and HTTP. Powered-off snapshot restores avoid saved/transitional-state ambiguity. Guest machine identity and HTTP status also match after restore.

- Current user-authorized continuation resumed after the first three logged rounds; rounds 4 and 5 are the two implementation/validation rounds since that continuation.
- #167 is a separate existing lab setup-helper compatibility defect: current installer email label changed. No parser product-code fix included here. Supported login/complete-setup API workaround succeeded, private credentials replaced stale host state, and temporary marker/one-time guest credentials were removed.

- Finish verification: single tightly scoped discovery smoke completed with 9 passed, zero failed; initial host-check/poll cadence delayed two targets, and both appeared Up without forcing checks or altering product data.
