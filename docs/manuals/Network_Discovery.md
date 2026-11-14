# Network discovery

This guide covers choosing which networks and ports Pinpoint scans, running a scan on demand, and what happens to the devices and ports it finds.

> **Verification status.** Written on 2026-11-14 from the route specification, `DiscoverySettings.tsx` and the discovery code. It has not yet been followed step by step on a demo build; items marked **TBC** need that check, and screenshots are not included yet.

## Purpose

Discovery finds the devices and open ports on your networks and records them in [Device Inventory](Device_Inventory.md). Ports whose service Pinpoint can identify, and whose plugin is enabled in [Plugin Manager](Plugin_Manager.md), are then monitored by Nagios.

## Prerequisites

- To run a scan or rescan: the **system.discover** permission.
- To change networks, ports and the Port → Service tables: **settings.discovery** (the **Network Discovery** tab of Settings).
- Permission to scan every network you list. Scan only networks you are authorised to scan.

## Choose what to scan

1. Open **Settings → Network Discovery**.
2. Under **Networks & Ports**, list the **Networks** as IPv4 ranges in CIDR form, for example `192.168.1.0/24`. Ranges larger than a /16 are refused, and localhost is never scanned.
3. Enter the **TCP Ports** and **UDP Ports** to probe, as single ports or ranges. Leave a field empty to use the nmap defaults. Keep the UDP list short: UDP scans are slow.
4. Under **Port → Service**, review the **Expected service** for each port and the plugin that checks it (**Checked by**). Pinpoint flags a port whose fingerprint contradicts the expected service as "not used as intended" and does not monitor it until someone acknowledges it.
5. Save.

Expected result: the saved list is used by the next scheduled scan and by **Rescan Network**.

## Run a scan now

Under **Run Network Discovery**:

1. To scan one device, enter its address in **Device IPv4 address** and choose the device scan button. A device scan does not change the saved network list or the scheduled scans.
2. To scan every saved network, choose **Rescan Network** (also available from the Dashboard). The button shows **Scanning…** with a percentage while it runs.
3. To stop a running scan, use the stop control. **TBC:** what is kept from a scan that is stopped part way.
4. When it finishes, open [Device Inventory](Device_Inventory.md) to see new and changed devices.

Expected result: new devices appear in the inventory; ports seen again keep their state.

## Scheduled scans

The automatic scan interval is **Scan Frequency** under **Settings → General** (every 1, 3, 6, 12 or 24 hours); **Current Scan Schedule** beside it shows the result. Changing it needs the settings permission for that tab.

## What happens to ports

- A new port whose service was identified by more than its port number, and whose plugin is enabled, starts **monitored**. Otherwise it is **suggested** and waits for you.
- A port missing from several scans in a row becomes **missing**, and later archived. A port seen again returns to monitored (missing) or suggested (archived). The number of missed scans before a port is marked missing is **TBC** on the live system.
- A port you ignored stays ignored. A service name you pinned stays pinned.
- Ports in the ephemeral range are not recorded.

## Precautions

- Scanning generates traffic; run large scans outside busy hours.
- Port scans can trigger intrusion alarms on networks you do not own.
- A wide port range on a large network takes a long time. Start narrow.
- If a device appears twice after a scan, use the identity review in [Device identity review](Device_Identity_Review.md).
- To install NCPA on a device so more checks become possible, see [NCPA deployment](NCPA_Deployment.md).
