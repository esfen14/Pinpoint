# Test run: issue-274-windows-registration-followup

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila; checks after 21:25 |
| Controller and documentation revision | `d4f69043`; application revision on the owner's VM not observed |
| Plan | [Defense demo lab](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor | Owner performed Windows registration; AI-assisted status and ping observations |
| Catalog | `manifest.json` SHA-256 `7a2ab626fb66bc71ff660347fd6ba8d118d2c67e600041c84575fa7d47fdc1f8` |
| Environment | Owner's `Pinpoint-Final` VM, Windows VM, laptop Docker pilot on host-only `10.77.1.0/27` |
| Baseline | Fourteen Linux containers reported running and five reserved DHCP leases present |
| Raw evidence | Owner's registration report and console observations; no raw log retained |

## Result

**Partial.** The owner reports adding the Windows NCPA device to Pinpoint. The
registration result and a metric have not been independently observed. The
appliance VM was running with its host-only adapter; Windows successfully
pinged the appliance `.1` and web container `.4`. A persistent-address check
across reboot has not been confirmed by the owner. No QA catalog or E2E cases
are claimed.

| Check | Result | Observation |
|---|---|---|
| Windows manual registration | Owner reported | Owner said Windows NCPA device was added; status and metric await observation. |
| Windows to appliance ping | Pass | Windows pinged `10.77.1.1` while `Pinpoint-Final` was running. |
| Windows to Linux ping | Pass | Windows pinged web03 at `10.77.1.4`. |
| Pilot baseline | Pass | Presenter status showed 14 containers running and five clients on `.20` through `.24`. |
| Address persistence | Not run | VM state-change time indicates a restart; the owner has not confirmed whether the cloud-init network setting was applied or the address persisted across that restart. |
| Product checks and alert recovery | Not run | Actual Windows metric, full device count, checks and alert recovery remain pending under [#274](https://github.com/esfen14/Pinpoint/issues/274). |

No credentials, tokens, key material, SNMP community or addresses outside the
lab range are included. Windows and all pilot targets remain running.
