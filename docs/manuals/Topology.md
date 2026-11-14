# Network topology

This guide covers the **Network Topology** page: reading the map of devices and their parent relationships, and setting a device's parent.

> **Verification status.** Written on 2026-11-14 from the route specification, `Device_Inventory_Requirements.md` §13 and the source. It has not yet been followed step by step on a demo build; items marked **TBC** need that check, and screenshots are not included yet.

## Purpose

Topology draws your devices as a hierarchy. Each line joins a device to its **parent**: the device Nagios should check first, so that when the parent is down its children are reported as unreachable, not as separate failures. These are reachability relationships, not cables.

## Prerequisites

- To view the page: the **system.network_health** permission.
- To change a parent: **system.hosts.edit**.

## Read the map

1. Open **Network Topology** (`/topology`).
2. The layout is automatic. Manual dragging and saved layouts are disabled in this release.
3. Select a device. **Device Information** shows its name, host name, device ID, IP address, operating system, monitoring state, host status, last check and last seen.
4. **Parent Relationship** shows the device's parent and lists its children; select a child to move to it.
5. If loading fails an error appears with **Retry**.

Expected result: a device with no parent sits at the top level.

## Set or change a parent

1. Select the device, then use the parent editor in **Parent Relationship**. The same editor is in the drawer on [Device Inventory](Device_Inventory.md).
2. Choose the new parent, or none, and save.
3. Pinpoint rebuilds the Nagios configuration. **TBC:** how long the map takes to show the change, and the message when Nagios rejects it.

Precautions:
- A parent must really sit in the network path in front of the device. A wrong parent hides real outages as "unreachable".
- A loop (A under B under A) is refused.
- Removing a device's parent does not remove the device.
- Nagios owns reachability; the map only shows what Nagios was given.
