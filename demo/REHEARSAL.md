# Defense demo rehearsal runbook

Run each rehearsal from a clean baseline and record the same measurements. Two
clean runs are required; this file says how each number is taken. The walkthrough
itself is [`Pinpoint-Demo-Script.md`](Pinpoint-Demo-Script.md).

## Before a run

1. `Pinpoint-Demo-faults.sh reset` returns the lab to its baseline and checks it. Record how long it takes.
2. `Pinpoint-Demo-faults.sh manifest` must exit 0 (every device consistent), and `demo/demo presenter preflight` must print `Preflight OK`.
3. In Pinpoint, Device Inventory shows 16 hosts UP: the fifteen devices plus the appliance's own `localhost`. Five DHCP clients hold `.20` to `.24` (`Pinpoint-Demo-faults.sh status`).
4. Know the standing alerts. After enabling the SNMP plugin, six interface checks (`snmp-lan_*`) stay UNKNOWN on the two SNMP devices (issue #278). Treat them as part of the baseline.
5. Start the resource sampler in a second terminal:
   `python3 -I demo/defense/sampler.py record /path/samples.txt 5400 5`.

## What to time

| Measure | How |
|---|---|
| Discovery duration | Click **Rescan Network** on the Dashboard and keep that page open. It shows `Scanning… N%`; the time until it disappears is one full scan (about 7.5 minutes in the lab). Reloading pages in between hides the indicator. |
| Fault to alert | Run `Pinpoint-Demo-faults.sh down web03 http`; the time until the Dashboard Active Alerts lists `http-80-tcp` as CRITICAL. |
| Recovery | Run `up web03 http`; the time until that row leaves Active Alerts. |
| Address change | `address-mode static dynweb01 10.77.1.15`, run a scan, then read Device Inventory: the same device (`dev-8fbfd1`) shows `.15` and the host count stays 16. Repeat with `address-mode dhcp dynweb01` and `.20`. |
| New port | `ports open web03 http PORT`, run a scan, then read the device's Ports section for `PORT` as Monitored. `ports close web03 PORT` makes its check CRITICAL. Use a new port each run. |
| Undo | `ports restore all`, then `reset`; `manifest` and `preflight` must pass again and Device Inventory must return to 16 hosts UP. |
| Resources | `python3 -I demo/defense/sampler.py summary /path/samples.txt`: minimum available RAM, swap in and out, peak swap rate, minimum free disk. Required: at least 3 GiB available and no sustained swap. |

## After a run

Remove the test port from Pinpoint: in the device's Ports section choose **Stop monitoring** for it, and acknowledge its alert on the Dashboard. A closed port shows Missing only after five scans that do not see it, and is archived after the configured period, so do not wait for it. Then write the sanitized report under `docs/test-runs/` (no credentials, no raw captures).
