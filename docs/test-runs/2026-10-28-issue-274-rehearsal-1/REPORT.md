# Test run: issue-274 defense rehearsal 1 (partial)

| | |
|---|---|
| Date | 2026-10-28, Asia/Manila |
| Environment | `Pinpoint-Final` appliance, Windows 10 Home VM and fourteen host-Docker targets on `vboxnet1`; two VMs and fourteen containers running throughout |
| Scope | One scripted run from a clean baseline: reset, discovery, a service fault and recovery, a DHCP-to-static address change and back, and a new port. The issue asks for two full runs; the owner reduced it to one. |

## Result

**Partial; FC7 is not met.** The reset, fault, alert and recovery timings were captured. The address-change and new-port timings were not, and the memory and swap gate failed during the run.

| Step | Result |
|---|---|
| Reset to baseline | 41.6 s; the observed manifest was consistent and preflight passed. |
| Baseline inventory | 16 hosts UP: the 15 catalog devices plus the appliance's own `localhost`. Five DHCP clients on `.20` to `.24`. |
| Full discovery scan | 504 s (about 8.4 minutes). Other scans in the same run took 282 s and 481 s. |
| Fault: `web03` HTTP stopped | CRITICAL alert on the Dashboard after 45 s. |
| Recovery | The alert left Active Alerts 59 s after the service was restored. |
| Address change to static `.15` | **Not captured.** After a 282 s scan `dev-8fbfd1` still showed `.20` within the next 180 s. Earlier manual runs saw the new address after one to two scans, so the driver should scan until it appears. |
| Return to DHCP | Not captured; the scan did not start. |
| New port `8089` | A 481 s scan completed, but the run stopped when the driver could not read the Ports drawer. Not captured. |
| Final undo | Done by hand after the run: `reset` restored the baseline, the manifest was consistent and preflight passed. |

## Host resources (3000 s, 5 s samples)

| Measure | Value |
|---|---|
| Minimum available RAM | **844 MiB** at about 1500 s (requirement: at least 3 GiB) |
| Swap in / out | 181,335 / 931,146 pages |
| Peak swap rate | **74,233 pages per second** (requirement: no sustained swap thrash) |
| Minimum free disk | 49,003 MiB |

Available RAM was between 2.8 and 9.4 GiB for most of the run, with a short collapse near 1500 s. The two VMs, fourteen containers, browser automation and the owner's other applications share 23 GiB of RAM, and the cause of the dip was not isolated. The 3 GiB and no-thrash gate is therefore **not shown** by this run. The earlier all-target `down`/`up` cycle (17 s and 70 s) stayed above 7.3 GiB without swap-out, but ran without a scan or the browser.

## Not covered

No second run, no NCPA registration timing, and no Missing or archive timing (a closed port goes Missing only after five scans that do not see it). Pinpoint's own history shows no IP-address history (#277), and the default SNMP interface checks are UNKNOWN on the two SNMP devices (#278). Raw sample files, the driver script, credentials and captures are not committed.
