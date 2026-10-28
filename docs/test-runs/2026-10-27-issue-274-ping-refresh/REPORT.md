# Test run: 2026-10-27-issue-274-ping-refresh

| | |
|---|---|
| Date | 2026-10-27 |
| Commit tested | `e0cb5047` |
| Plan | [Defense demo lab plan](../../plans/Defense_Demo_Lab_Plan.md) |
| Tester / executor mode | Codex, AI-assisted scripted host/guest controls |
| Catalog revision and SHA-256 | `e0cb5047`; `demo/defense/manifest.json` SHA-256 `7a2ab626fb66bc71ff660347fd6ba8d118d2c67e600041c84575fa7d47fdc1f8` |
| Queue / set / session / batch | Issue #274, stage 2 restoration and stage 3 ping-only pass |
| Deployed application / installer revision | No appliance/app was started or scanned |
| Baseline / preflight / restoration | Target-host source/image refreshed through the pinned stock-ISO path. Target-host safety status passed (forwarding IPv4/IPv6 off, management restricted, image current). The read-only presenter preflight remained blocked by absent controller pins. Two exact VMs and the 14-container catalog were left running for demo use; KVM remains unloaded while VirtualBox is active. |
| Start / end / time zone | 2026-10-27, Asia/Manila; approximate 18:00–18:21 (not formally timed) |
| Environment | Linux host; VirtualBox 7.2.14; Ubuntu Server 24.04.5 target-host; Windows 10 Home build 19045; isolated `10.77.1.0/27`; appliance powered off |
| Raw evidence | No raw output or packet evidence retained; sanitized totals below and in the issue progress log |

## Result

**Overall: Partial.** The target-host refresh and stage 2 Linux setup passed, including fourteen attached targets, baseline services and five DHCP leases. The ping-only reachability gate failed in both directions, and the presenter preflight still lacks its private VM pin file.

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 2, Fail 2, Partial 0, Blocked 1, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; link reviewed mappings separately.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| E2E-LAB-01 catalog startup | Pass | Fixed `lab-up` helper created and attached all fourteen catalog Linux targets with their pinned MACs. Baseline daemons were started. No appliance scan or service probe ran. | |
| E2E-DHCP-01 five clients | Pass | Five distinct clients acquired reserved leases: `dynweb01` .20, `dynapp01` .21, `dynmail01` .22, `dynsnmp01` .23, `dynweb02` .24. | |
| E2E-PING-01 Windows to catalog | Fail | Corrected `PING.EXE` pass: Windows self-address `.3` replied; none of fourteen Linux target addresses replied (1/15 total). | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| E2E-PING-02 Linux to Windows | Fail | Fixed Linux peer-ping returned no reply for thirteen Linux targets. `dns01` helper refused before sending ping, so that target was not tested. Total replies 0/14. | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| E2E-PREFLIGHT-01 presenter readiness | Blocked | `bash demo/demo preflight --json` reported missing private pins for appliance, target-host and Windows. It did not authorize lifecycle; no presenter lifecycle command is wired. | [#274](https://github.com/esfen14/Pinpoint/issues/274) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| E2E-LAB-01 | Fourteen attached Linux targets | 14 attached; baseline services started | Pass | No raw file retained | Left running for demo |
| E2E-DHCP-01 | Five simultaneous distinct leases | .20–.24, one per client | Pass | No raw file retained | Left running for demo |
| E2E-PING-01 | Windows can ping all 14 Linux targets | 0/14 Linux replied; Windows self-ping passed | Fail | No raw file retained | Network state left unchanged |
| E2E-PING-02 | All 14 Linux targets can ping Windows | 0 replies; 13 ping timeouts and one helper refusal | Fail | No raw file retained | Network state left unchanged |
| E2E-PREFLIGHT-01 | Presenter preflight ready | Blocked by three absent VM pins | Blocked | No raw file retained | No lifecycle started through presenter CLI |

The first Windows guest-control invocation accidentally included the executable
path as a ping destination and was excluded from the result; the corrected pass
used only `PING.EXE`. No ARP, port/service test, scan, packet capture or product
discovery was run in stage 3. Target-host source refresh retained the installed
disk and private identity; `reset-lab` removed fourteen validated containers,
kept identity/data volumes and DHCP lease files, and rebuilt the image. The lab
was then recreated from the fixed helper controls.

## Deviations from the plan

- The appliance was not started because its private pin is absent from the
  presenter controller state. Product discovery, NCPA registration and
  monitoring were not attempted.
- Ping failure after the source refresh shows the current macvlan path remains
  unsuitable. Further network acceptance is deferred until an offline-reviewed
  bridge/veth alternative is prepared.
- The requested no-extra-network-test constraint was followed: stage 3 used
  ping only.

## Follow-up

- Defects found: issue #274 remains open for the failed macvlan reachability
  gate and the missing presenter controller pins/lifecycle.
- Cases to repeat in the next run: both ping directions after the topology
  revision; controller preflight after exact private VM pins are wired.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
