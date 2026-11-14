# Settings

This guide covers the **Settings** page and its six tabs.

> **Verification status.** Written on 2026-11-14 from the route specification and the `components/settings/` source. It has not yet been followed step by step on a demo build; items marked **TBC** need that check, and screenshots are not included yet.

## Purpose

Settings holds your personal display preferences (General) and the system-wide rules (the other tabs). Each tab needs its own permission, and a tab you cannot use is hidden.

## Prerequisites

| Tab | Permission |
|---|---|
| General Settings | none beyond signing in |
| Security | `settings.security` |
| System | `settings.system` |
| Network Discovery | `settings.discovery` |
| Plugins | `settings.plugins` |
| Email | `settings.email` |

## Change a setting (every tab)

1. Open **Settings** (`/settings`) and choose a tab.
2. Change the values. **Save Changes** and **Discard Changes** become active once something differs from the saved values.
3. Choose **Save Changes**. A **Saved** confirmation appears briefly; a failed save shows an error and keeps your edits.
4. **Discard Changes** returns the form to the saved values. **Reset to Defaults**, where shown, restores the defaults but does not save until you choose **Save Changes**.

## General Settings

Display preferences: **Theme** (Dark or Light), **Time Zone** (Browser or a fixed offset), **System Font** and **System Font Size**, **Date and Time Format** (DD/MM/YYYY, MM/DD/YYYY or YYYY-MM-DD), **Dashboard Layout** (default, compact or expanded), the notification bell toggle, **Dashboard Refresh Rate** (1, 5 or 15 minutes, or Manual), **Export Formats** (CSV, PDF, XLS) and **Scan Frequency** (the automatic [network discovery](Network_Discovery.md) interval). **TBC:** whether each of these is stored per person or for the whole system.

## Security

**Session Timeout** (15, 30, 60, 120 or 240 minutes), **Security Check Frequency** (how often every plugin's file, permissions and execution are re-validated; see [Plugin Manager](Plugin_Manager.md)), **Strong Password Policy** (see [Sign in, accounts and roles](Login_Accounts_and_Roles.md)), **Failed Login Monitoring** and **Audit Logging** (feeds [System logs](System_Logs.md)).

Precaution: a short timeout signs people out while they work; turning audit logging off leaves no record of changes.

## System

- **System Configuration:** **System Update Frequency** (how often installed plugins are re-scanned for newer versions), **Check interval**, **Data polling interval**, **Retry interval**, **Maximum check attempts**, **Maintenance Mode**, **Automatic Backups** (see [Backup and restore](Backup_and_Restore.md)), **System Log Retention** and **Diagnostic History Retention**.
- **Flap detection:** an on/off switch with **Low flap threshold** and **High flap threshold**. Flap detection stops a device that keeps changing state from sending an alert each time.
- **Notifications** and **Escalations** cards: see [Notification policy](Notification_Policy.md).
- **System Status** shows the current value of each of these at a glance.

Precautions: shorter check intervals add load on Nagios and the monitored devices; shorter retention deletes older data permanently. For planned work use [Maintenance windows](Maintenance_Windows.md) rather than leaving Maintenance Mode on. **TBC:** whether Maintenance Mode here and a maintenance window behave the same.

## Network Discovery

Networks, ports and the Port → Service tables. See [Network discovery](Network_Discovery.md).

## Plugins

Network-wide defaults for plugin checks: the **SNMP OID** and **NCPA metric** tables, and any other plugin with network-wide values. Per-plugin enabling is done in [Plugin Manager](Plugin_Manager.md). **TBC:** the full list of tables on a demo build.

## Email

SMTP details and test message: see [Email settings](Email_Settings.md).
