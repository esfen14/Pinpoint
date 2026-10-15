# Issue #162: clean lab rebuild and endpoint snapshot restoration

| | |
|---|---|
| Date | 2026-10-15 (Asia/Manila) |
| Guard/harness commit | Marker trial at `f15ff1ab` (implementation `ec9e2517`); final SSH-boundary refinement at `10fcb05f` |
| Application deployed | `82ba9ce9aefda8fbbad93ba500a9cacf23c56409` (`main`) |
| Installer | Clean checkout `697869e`; existing deploy and privilege scripts |
| Plan | [VM Lab Plan](../../plans/VM_Lab_Plan.md), [issue #162](https://github.com/esfen14/Pinpoint/issues/162) |
| Tester | Codex; owner authorized deleting the old configured lab disks and rebuilding |
| Environment | VirtualBox 7.2.14, new Ubuntu 22.04.5 appliance, new Ubuntu 24.04.5 target base and five targets; discovery restricted to `10.77.0.0/28` |
| Raw evidence | Ignored `test-results/issue162/`: creation/provision/deploy logs, `snapshot-marker.log`, `snapshot-marker.json`, setup/scope/smoke/health logs |

## Result

**#162 requirements pass; replacement lab operational.** The snapshot marker
was restored through both SSH and HTTP, the new appliance healthcheck passed,
and a single scoped discovery smoke passed all nine checks with all five targets
monitored and Up. A separate setup-helper compatibility failure was worked
around through the supported API and is tracked in #167.

## Snapshot proof

The new appliance uses a newly created VDI and UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`.
Before provisioning, SSH confirmed the application checkout did not exist.
The old appliance, target VMs and target base were removed only after the owner
accepted the lost edits as unrecoverable and authorized disk retirement. No old
application disk, database, checkout or snapshot was used in the trial.
See the [diagnosis and source-loss record](../2026-10-15-issue-162-recovery/REPORT.md).

A non-secret static marker was written in the fresh application build. Both SSH
and HTTP read it at each stage. The powered-off snapshot was
`issue162-endpoint-marker`, UUID `ebf767b5-9d26-49a9-b76e-ab747084809b`.

| Stage | Value through SSH and HTTP |
|---|---|
| Before snapshot | `issue162-baseline-45f149bcdd471a2c5b3e0d75` |
| Changed after snapshot | `issue162-changed-c17b2e1e6550cf5bd432910f` |
| After restore/restart | `issue162-baseline-45f149bcdd471a2c5b3e0d75` |

The actual restore returned the original marker through both endpoints, with
HTTP 200 and matching guest machine identity. Preflight passed before mutation,
at each powered-off boundary, and after each restart. No duplicate controller,
residual powered-off listener or mismatched runtime forwarding socket was
accepted. The temporary marker was removed after the proof; its snapshot is
retained separately from the OS-only base snapshot.

## Cases

| Case | Result | Observed evidence | Issue |
|---|---|---|---|
| S1 Blank-disk appliance | Pass | New UUID/VDI created from stock ISO; SSH confirmed no existing application checkout. | |
| S2 Runtime ownership | Pass | Sole controller, unique UUID process under it, exclusive loopback ports and active runtime SSH/web forwarding sockets agreed; powered-off checks required no process/listener. | |
| S3 Snapshot change/restore | Pass | Exact marker values above were observed through SSH and HTTP; `snapshot-marker.json` result `pass`. | |
| S4 Targets recreated | Pass | New base and five linked targets created; `targets wall --once` observed all expected SSH/HTTP/HTTPS/SNMP services UP, including legacy SSH/2222. | |
| S5 Appliance health | Pass | Installer healthcheck: 60 passed, 0 warnings, 0 failed before marker trial. | |
| S6 Standard setup helper | Fail | Current installer email label did not match helper parser; stale host credentials were incorrectly reported as configured. No credentials included in this report. | [#167](https://github.com/esfen14/Pinpoint/issues/167) |
| S7 Supported first-run API | Pass | Actual login and complete-setup APIs completed first-run setup; fresh credentials stored privately; one-time guest credential file removed. | |
| S8 Discovery scope | Pass | Environment fallback and persisted settings restricted to the documented /28; explicit TCP service ports and UDP/161 confirmed before starting the only discovery run. | |

| S9 Discovery/monitoring smoke | Pass | `scripts/vmlab smoke --discovery-timeout 600 --hosts-timeout 300`: 9 passed, 0 failed; discovery applied hosts.cfg in 96 seconds and all five target IPs appeared monitored and Up after their normal checks/polls. | |

| S10 Final appliance health | Pass | Healthcheck repeated after setup, snapshot restoration and discovery: 60 passed, 0 warnings, 0 failed. | |

## Setup deviations

The NodeSource download inside the guest was unusually slow. The same
37,783,800-byte package was downloaded in byte ranges on the host and assembled;
its SHA-256 matched the guest's APT repository metadata before caching:
`31eef6210cb50f9031afb59e7f1ed741d40db5d39f0894372b19444f33c4996e`.
Only the pending nodejs APT download was interrupted, before package installation.
The unchanged installer deploy/privilege steps were resumed with that exact
cached package. The interrupted transport attempt is retained separately; no
dependency, signature requirement or application test was weakened.

First-run setup used a one-off API helper after the separate #167 parser defect;
the product's setup-admin parser was not changed in #162.

## Verification and limits

`scripts/verify.sh all`: 2,777 backend passed / 14 skipped; 628 frontend passed;
build/lint passed with 29 existing lint warnings. Eighteen focused ownership
and mutation-gate tests pass, including changed control ownership between
command entry and an SSH/key-bootstrap action. The full verification entry point and final docs stage were repeated after
that boundary refinement; backend/frontend product code was unchanged. No live integration/e2e test suite was run.
External SMTP/inbox acceptance for #79 is outside this recovery task. NCPA
deployment and browser journeys were not repeated as part of the lab rebuild.
The initiating actor that first replaced the old IPC pathname remains unknown;
the split-listener mechanism and control/endpoint disagreement were observed.

## Sanitization

No credentials, host private-key paths, mailbox addresses, raw configurations,
databases or VM images committed. Marker values are random non-secrets. Only
loopback and the documented lab network are named here.
