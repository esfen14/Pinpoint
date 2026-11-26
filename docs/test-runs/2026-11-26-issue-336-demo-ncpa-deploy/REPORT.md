# Test run: issue-336-demo-ncpa-deploy

| | |
|---|---|
| Date | 2026-11-26 (local); times below are 2026-11-25 UTC |
| Commit tested | `a069ee79` for the appliance, the containers and every page step; `b53662e7` for the second `demo/demo preflight` run (presenter-only change) |
| Plan | Finish condition of [issue #336](https://github.com/esfen14/Pinpoint/issues/336) |
| Tester / executor mode | AI-executed (Claude Code) scripted Playwright browser run; the repository owner ran the `sudo` lab rebuild and approved the threshold change and adapter detach |
| Catalog revision and SHA-256 | Not a queued catalog case |
| Queue / set / session / batch | None |
| Deployed application / installer revision | Application `issue-336-demo-ssh-ncpa` at `a069ee79`; installer checkout `3a97733` |
| Baseline / preflight / restoration | `qa-pinpoint-appliance` restored to `os-nagios-ready`, then installed; health check 61 passed, 0 failed. See Restoration |
| Start / end / time zone | 16:11 to 23:59 UTC, with a wait for owner decisions between 17:22 and 23:50 |
| Environment | Debian 13 host, VirtualBox host-only `10.77.1.0/27`, Ubuntu 22.04 appliance, fourteen Ubuntu 24.04 Docker targets, fresh databases |
| Raw evidence | Lab host, `~/pinpoint-test-results/2026-11-26-issue-336/` (screenshots, scripts, logs) |

## Result

**Overall: Pass, with two stated conditions.** The NCPA Deployment page deployed
NCPA 3.5.1 to `ssh-alt02`, and every listed failure path behaved as expected.

1. All five NCPA checks showed **OK only after the memory and disk thresholds
   were raised** on this disposable appliance (owner decision). With the shipped
   thresholds, memory and disk were WARNING, because the container reports the
   host laptop's memory and disk use.
2. `demo/demo preflight` printed the deploy target but **did not pass**: its
   existing VM check blocks while the QA appliance is on the lab network.

Not a catalog run: no TC or E2E case is claimed.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Image build and lab rebuild | Pass | `demo/demo setup --apply` built both images and created fourteen containers. The first start was refused because the appliance install held the lab lock; `demo/demo up` then reported all fourteen ready | #336 |
| `demo/demo setup` reports the target | Pass | Plan step 2 and the checklist name `ssh-alt02`, `labadmin` and the password file | #336 |
| `demo/demo preflight` reports the target | Pass (report); command exit 1 | At `a069ee79` no report line appeared, because the command stopped at "Host-only VM membership changed". At `b53662e7` it prints the target, port, user and password command first, then the same blocker | #336 |
| Other thirteen targets unchanged | Pass (sampled) | `web03` and `db01`: lab image, 64 and 192 MB, 96 processes, no `sudo`. The other targets: offline tests only | #336 |
| Discovery | Pass after wait | `vmlab smoke` 16 of 18: `10.77.1.11` and `.21` had not had a first host check; both Up about 10 minutes later | |
| Verify host key | Pass | Page fingerprint equalled the container's key; device became Trusted (`01-`, `02-`) | #336 |
| Wrong password | Pass | "Rejected this username or password"; wizard did not continue (`check-login-wrong-`) | #336 |
| Changed host key | Pass | Container key replaced: "Its host key changed", with Remove. Original key restored; no deployment account existed afterwards | #336 |
| Failed deploy | Pass | Local mirror stopped: result Failed, "Privileged command failed", appliance log shows `repo.nagios.com` connection refused (`04-`) | #336 |
| Clean up after the failed deploy | Pass | Five steps complete; device Pending; sudo rules and helpers gone, deployment key file empty, account kept as chosen (`05-`) | #336 |
| Deploy NCPA | Pass | Deployed in 14 s; `ncpa` 3.5.1-1, listening on 5693 as `nagios`; memory peak 266 MiB of 512 (`06-`) | #336 |
| Enable `check_ncpa` | Pass | Preview: 5 services on 1 device (`07-`, `08-`) | #336 |
| Checks, shipped thresholds | Fail against "OK" | CPU OK 0.50%, swap OK 19.0%; memory WARNING 61.8% (warn 50); disk `data` and `identity` WARNING 94.1% (warn 70) | #336 |
| Checks, raised lab thresholds | Pass | Memory 75/90, disk 97/99: CPU OK 0.50%, memory OK 61.2%, disk `data` and `identity` OK 94.1%, swap OK 20.1% (`thresholds-*`) | #336 |
| Clean up a deployed device, with account removal | Pass | Six steps complete; account gone | #336 |
| Redeploy | Pass | Deployed again in 9 s (`10-`) | #336 |
| Target restart | Pass | `demo/demo down` and `up ssh-alt02 host`: agent active and listening; later checks returned results | #336 |
| Password stays private | Pass | 0 lines containing it in the appliance journal (last hour) and the container's `/data` logs | #336 |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| Deploy | Status Deployed NCPA | Agent column "Deployed" | Pass | `06-deploy-result.png` | Not needed |
| Checks, attempt 1 | CPU, memory, disk OK | Memory and disk WARNING | Fail | Observed through the plugin services API | Not needed |
| Checks, attempt 2 | CPU, memory, disk OK | All OK with raised thresholds | Pass | `thresholds-saved.png` | Appliance is disposable; thresholds not reverted |
| Changed host key | Refused | Refused | Pass | `check-login-right-changedkey.png` | Original key fingerprint confirmed |
| Preflight adapter detach | Appliance adapter 2 unchanged afterwards | Identical settings | Pass | | Yes |

## Deviations from the plan

- The first appliance install stopped at "Could not install nmap": Ubuntu's
  `unattended-upgrades` held the package lock for about 37 minutes. The remaining
  installer step (`configure-pinpoint-privileges.sh`) was run again by hand and passed.
- Memory and disk thresholds were raised through **Settings > Plugins** (owner decision).
- The QA appliance's second adapter was detached for one preflight run and restored
  (owner approval). Preflight still blocked: it also needs both demo VMs running,
  and the saved demo appliance pin does not match the current `Pinpoint-Final` VM.
- The **Verify** step was run from the device row, then **Deploy selected**.

## Restoration

`qa-pinpoint-appliance` is powered off with its adapters unchanged. The fourteen
containers were left running; `ssh-alt02` still has NCPA installed (see the demo
targets guide to recreate it).

## Follow-up

- No product defect blocked this issue. Seen outside its scope, not yet filed:
  the deploy wizard text says "port 22" for a device on another port (inspected in
  `DeployWizard.tsx`); `qa reset` can fail on the appliance's package lock;
  `vmlab smoke` can time out before the last first host checks.
- Not tested: a download from the real Nagios server, a device with systemd or a
  firewall, and remote service restart (#322 stays open).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
