# Plugin Manager

**Plugin Manager** (`/plugins`) lists the Nagios plugins installed on the Pinpoint server and decides which ones Nagios uses to check your devices. Pinpoint can only monitor a port or service when the plugin that checks it is **enabled** here.

> **Verification status.** Written on 2026-11-14 from the route specification, `Plugins_List.md` and the page source. It has not yet been followed on a demo build; items marked **TBC** need that check, and screenshots are not included. Custom checks that need arguments have their own guide, [Custom checks](Custom_Checks_Manual.md); this guide does not repeat it.

## Purpose

- See which plugins exist, what each one checks, and whether it is monitoring anything.
- Enable or disable a plugin so ports and services found by discovery start or stop being checked.
- Review what a plugin monitors, stop or resume one port, change a command, validate, or update a plugin.

## Prerequisites

| To do this | You need |
|---|---|
| Open the page and read details | `plugin.view` |
| Scan the plugin folder | `plugin.scan` |
| Enable, or resume a stopped service | `plugin.enable` |
| Disable, or stop one service | `plugin.disable` |
| Override or restore a command | `plugin.command_override`, `plugin.command_restore` |
| Validate | `plugin.validate` |
| Update or roll back | `plugin.update`, `plugin.update_rollback` |
| Add and manage custom checks | `plugin.custom_check` |

Plugins are read from the Nagios plugin folder (default `/usr/local/nagios/libexec/`; the `NAGIOS_PLUGIN_DIR` setting). The Pinpoint service account may not write to that folder, so installing new plugin files is done by an administrator on the server.

## Look at the inventory

1. Choose **Plugin Manager** in the sidebar.
2. The cards at the top show **Installed Plugins**, **Active Capabilities** and **Validation Issues**. A banner appears while no plugin is enabled; until one is, nothing discovered is monitored.
3. Use the category tabs (**All**, **Network Services**, **Device Availability**, **Network Protocols**, **Servers**, **Application**, **Other**) and the search, filter and sort controls. Paging stays within the chosen tab.
4. The **Monitoring** column says whether the plugin is currently checking anything.
5. Choose **Scan** to re-read the plugin folder (needs `plugin.scan`). Progress and any error are shown. Installed plugins are also re-scanned for newer versions on the **System Update Frequency** set under **Settings → System**, and every plugin's file, permissions and execution are re-validated on the **Security Check Frequency** set under **Settings → Security**.

Expected result: one row per installed plugin with its category and description. A plugin with no description yet gets one from the bundled catalog after a scan.

## Enable a plugin

1. Select the plugin to open **Plugin Details**.
2. Choose **Enable**. A confirmation previews what will be monitored: how many services and devices it would attach, and any ports that are **held** (left Suggested on purpose) and will not be started.
3. Confirm. Pinpoint attaches the plugin to the matching ports, regenerates the Nagios host file once, validates it with Nagios and reloads Nagios.

Expected result: the plugin shows **Enabled**, then **Active** once it is checking something; new services appear in Nagios, and on Dashboard and Network Health after the next poll.

If Nagios rejects the new configuration the plugin goes back to its previous state and the page shows the reason.

## Disable a plugin

Choose **Disable** and confirm. Its services leave Nagios. The ports keep their state, so enabling the plugin again restores the checks. History is kept.

## See and control what a plugin monitors

The **Services** section of the drawer lists, one row per Nagios service: the service, device, port and protocol, whether it is monitored, since when, and its **live status** from Nagios. You can search and page.

- **Stop** (needs `plugin.disable`) stops monitoring one port on one device; the port becomes Ignored in [Device Inventory](Device_Inventory.md) and the service leaves Nagios.
- **Resume** (needs `plugin.enable`) starts a stopped port again.
- The NCPA port of a device with a deployed agent is protected and cannot be stopped here.

Devices are never picked by hand: a plugin attaches to every matching port that discovery found. To exclude one device or port, stop that port or pause the device.

## Commands, validation and updates

The drawer also shows the plugin's version, executable path, source, dependencies and commands.

- **Override a command** (`plugin.command_override`): replace a command definition used when Pinpoint generates the check, and **Restore default** (`plugin.command_restore`) to undo it. **TBC:** which command fields can be edited in the current release.
- **Validate** (`plugin.validate`): checks the executable, its permissions and its dependencies. Failures count in **Validation Issues**.
- **Update** (`plugin.update`): replace a plugin from an uploaded **Update archive** or an **Update URL**. The previous version is backed up, and **Roll back** (`plugin.update_rollback`) restores it. **TBC:** whether the Pinpoint service account can write to the plugin folder on your installation; the installer deliberately does not grant it, in which case updating is done on the server.

## Custom checks and custom plugins

- Plugins that cannot be attached to a port automatically (for example `check_by_ssh`, `check_ups`, or server-side checks such as `check_apt`) take **custom checks**, added from the drawer with `plugin.custom_check`. Follow [Custom checks](Custom_Checks_Manual.md), including how passwords are stored.
- **Adding your own plugin file from the browser is not available in this release** (the control is disabled). Install the executable in the plugin folder on the server, then choose **Scan**.

## Precautions and troubleshooting

- **Nothing is monitored after discovery:** enable the plugins for your services here first. A port that is open but whose plugin is not enabled stays Suggested, with the reason shown in Device Inventory.
- **A plugin has no monitoring but is enabled:** no discovered port uses it yet, or its ports are held. Check the enable preview.
- **Enable or Disable fails:** the message comes from Nagios's own configuration check. Give it to your system administrator; the previous state is kept.
- **Plugin listed but "validation issue":** run **Validate** and read the message (missing file, wrong permissions, or a missing dependency).
- **A shared library file such as `utils.sh` is not listed:** it is not a plugin and is skipped by the scan.
- The reference for what each Nagios plugin does and its arguments is [`Plugins_List.md`](../../spec%20files/Plugins_List.md).
