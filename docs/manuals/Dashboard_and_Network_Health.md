# Dashboard, Network Health and Network Status

Three pages show the current state of the monitored network: the **Dashboard** (the first page after sign-in: is anything broken right now?), **Network Health** (a deeper look at hosts, services and trends) and **Network Status** (a service table with acknowledgement). This guide also covers acknowledging alerts and the **Check now** button.

> **Verification status.** Written on 2026-11-14 from `Display_Requirements.md`, the route specification and the page source. It has not yet been followed on a demo build; items marked **TBC** need that check, and screenshots are not included.

## Purpose

Nagios Core does the checking; Pinpoint reads the results and presents them. These pages show the latest results, not history. For past events use [Alerts and notification history](Alerts_and_Notification_History.md); for availability over a period use [Service reports](Service_Reports.md).

## Prerequisites

| To use | You need |
|---|---|
| Dashboard | `system.dashboard` |
| Network Health, Network Status, Device Inventory, Topology | `system.network_health` |
| Acknowledge and unacknowledge alerts | `system.acknowledge_alerts` (without it you see the acknowledged state but no controls) |
| **Check now** | `system.recheck` |

At least one monitored host, discovered through [Network Discovery](Network_Discovery.md), is needed for data to appear. Resource figures (CPU, memory, disk) need the NCPA agent on the hosts; see [NCPA deployment](NCPA_Deployment.md).

## Read the Dashboard

1. Choose **Dashboard** in the sidebar.
2. **Monitoring System** (top): whether the Nagios process is running, its version and start time, when its status data was last updated, and whether active checks, notifications and flap detection are on. If Nagios is stopped this section says so and the rest of the page may be stale.
3. **Summary cards:** total hosts (up, down, unreachable), total services (ok, warning, critical, unknown), **Active Alerts** (everything not OK or UP) and hosts in downtime. A zero in Active Alerts means all clear.
4. **Active Alerts** list: each problem host or service with its state, soft or hard, how long, the plugin output, and badges for acknowledged and in downtime. Order: critical first, then warning, then unknown; unacknowledged before acknowledged; devices in scheduled downtime last. Choose **View all** to go to the full tables.
5. **Service overview, network status overview and network performance:** proportions of states, latency and packet loss, and bandwidth where configured. A section that needs a plugin that is not set up says "Plugin not configured" with what to add.
6. **Average resource utilization:** CPU, memory and disk averaged over hosts with the NCPA agent. It is hidden when no host has the agent. An average shows "Insufficient data" when fewer than two hosts report.
7. **Running out soon:** disk and memory that are on course to reach a warning or critical level, with an estimate. **TBC:** how many days ahead it looks.
8. **Appliance storage:** size of the databases, backups and Nagios archives and free space on each disk; a warning appears when a disk has less than 10% free.
9. **Recent Notifications:** the latest notifications Nagios sent.

Freshness: the page shows when the data was last updated and warns when it is older than the Nagios check interval plus the polling interval (**Settings → System**). It refreshes by itself at the rate set in **Settings → General → Dashboard Refresh Rate** (Manual, 1, 5 or 15 minutes), and you can refresh by hand.

Colors: green is OK or UP, yellow is WARNING, red is CRITICAL or DOWN, orange or gray is UNKNOWN or UNREACHABLE, a muted color is acknowledged, blue or purple is scheduled downtime.

## Acknowledge an alert

Acknowledging tells your team a problem is known and being handled. It does not fix the problem and does not stop Nagios checking.

1. In the Active Alerts list (or a Network Health or Network Status row), choose **Acknowledge**.
2. Type the required **comment** and confirm.
3. The row turns muted with an Acknowledged badge. To undo, choose **Unacknowledge** and confirm; no comment is needed.
4. To acknowledge many at once on the Dashboard, set the acknowledgement filter (**Show all**, **Hide acknowledged**, **Show only acknowledged**), then choose **Acknowledge all**. It acts only on the rows currently visible, with one comment for all.

Expected result: who acknowledged, when and the comment are kept and appear on the matching event in [History](Alerts_and_Notification_History.md). When a problem recovers, its acknowledgement is closed automatically.

## Check now

Open a host or service in its detail drawer and choose **Check now** (needs `system.recheck`). Nagios runs the check immediately and the new result appears after the next poll. A target can be re-checked once every 10 seconds. It is refused for devices that are paused, retired or merged, and fails if Nagios cannot be reached.

## Network Health

1. Choose **Network Health**. The top strip repeats the key counts: online and offline devices, issues and average response time.
2. **Host status** and **service status** tables: search by name, filter by state or acknowledgement, and select a row to see its performance data with warning and critical thresholds, last state change and last up or down times. Badges mark acknowledged, in downtime and flapping; a **Flapping only** filter lists unstable items. For users with `system.network_health`, the detail drawer also shows how often an item flapped in the last 1, 6, 24 or 168 hours.
3. **Trends:** average latency and packet loss, bandwidth, and CPU, memory and disk where the NCPA agent is deployed. Choose a time range to change the charts.
4. **Services by plugin type:** health grouped by kind of check (for example HTTP, SSH, SNMP). Groups with no services are not shown.
5. **Interface Bandwidth:** pick a device and one of its monitored interfaces and a range (1 hour, 6 hours, 24 hours or 7 days) to see in and out rates and the share of the link in use. Interfaces are chosen in [Device Inventory](Device_Inventory.md) (Interfaces section). Messages explain when there is no SNMP device, no monitored interface or too few readings.

## Network Status

**Network Status** (`/system-status`, heading **Network Service Overview**) is a service table with counts of OK, Warning, Unknown and Critical, search, a state filter, sorting, paging and acknowledgement. Users with `remediation.view` also see a **Recovers automatically** mark on services that have an enabled restart action; it links to [Automatic recovery](Automatic_Recovery.md).

## Precautions and troubleshooting

- **A device is missing from counts:** devices that are paused, retired or merged are not checked by Nagios and are left out of every count. See [Device Inventory](Device_Inventory.md).
- **Data looks old:** read the freshness line. Check Nagios is running (Monitoring System section), then the polling and check intervals under **Settings → System**.
- **A value says "Not configured" or "Plugin not configured":** the check is not set up for any host. Enable the plugin in [Plugin Manager](Plugin_Manager.md) or add the NCPA metric under **Settings → Plugins**.
- Averages count only hosts that reported in the last check cycle, and say how many.
- **TBC:** the exact card order and labels differ by **Settings → General → Dashboard Layout** (default, compact or expanded).
