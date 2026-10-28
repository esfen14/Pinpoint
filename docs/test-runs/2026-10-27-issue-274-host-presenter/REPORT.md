# Test run: issue-274-host-presenter

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila |
| Commit / candidate tested | Base `6cd788d3` plus uncommitted presenter candidate; candidate used for the last live `up`: `demo/defense/presenter.py` SHA-256 `d39d9f319f01870dbd909bb8916aacfcd576eb6de51e2b7aed8862bfca0bbf48`. The full down/up was run on an earlier candidate; that candidate repeated `up` with one DHCP target stopped. |
| Plan | [Defense demo lab](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor | AI-assisted, scripted live pilot |
| Catalog revision | `manifest.json` SHA-256 `7a2ab626fb66bc71ff660347fd6ba8d118d2c67e600041c84575fa7d47fdc1f8` |
| Queue / set / session | Issue-specific presenter pilot, not a QA case queue |
| Application / installer revision | Not observed; product acceptance was not run |
| Environment | Laptop Docker pilot, VirtualBox Windows VM, isolated `10.77.1.0/27` host-only segment |
| Baseline and restoration | 14 Linux pilot containers active, Windows running; all 14 restored active and five reserved leases reacquired |
| Raw evidence | Console observations during the run; no raw log retained |

## Result

**Overall: Partial.** Status, one service fault and recovery, a full stop/start,
five DHCP leases and ping from Windows to all fourteen Linux targets were
observed. A later candidate restored a separately stopped DHCP target and
Windows pinged it. Reboot, Docker daemon restart, full fault coverage and
Pinpoint appliance integration were not tested. No product QA catalog cases or
E2E cases are claimed; totals for each are zero.

## Observations

| Check | Result | Observed |
|---|---|---|
| Pilot status | Pass | Fourteen target addresses and local Supervisor service states reported. |
| Service fault | Pass | `web03` HTTP service stopped and restored; HTTP and HTTPS share nginx. Restoration was performed in a `finally` block. |
| Pilot lifecycle | Pass for earlier candidate | All fourteen stopped, then restarted; five DHCP clients returned to `.20`–`.24`. |
| Windows reachability after lifecycle | Pass | One ping reply from each of the fourteen Linux addresses. No other connectivity probes were used. |
| DHCP target recovery on later candidate | Pass | Stopped `dynweb02`, ran `up`, observed `.24` and Windows ping reply. |
| Host reboot and Docker daemon restart | Not run | Neither was performed. |
| Appliance, plugin and fault acceptance | Not run | Product integration and full fault controls remain issue [#274](https://github.com/esfen14/Pinpoint/issues/274). |

## Deviations and follow-up

This is a host Docker pilot replacing the earlier target-host topology; it does
not establish the complete issue acceptance. Existing original VM data was not
migrated. Test reboot and daemon recovery before relying on an unattended
restart, and complete appliance integration and remaining controls.

## Sanitization

No credentials, keys, SNMP communities or addresses outside the documented lab
range are included. The run left Windows and the fourteen pilot containers up.
