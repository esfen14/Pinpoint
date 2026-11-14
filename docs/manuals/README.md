# Pinpoint guides

How-to guides for operators and users. Each guide gives the purpose, prerequisites, numbered steps, the expected result and precautions. A guide marked **TBC** inside has items not yet checked step by step on a demo build.

A future User Manual (issue #181) should link to these guides rather than copy them.

## Guide for each page

Every route in the web interface (`client/src/App.tsx`) is listed here.

| Page (route) | Guide | Notes |
|---|---|---|
| Sign in (`/login`) | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) | |
| Dashboard (`/dashboard`) | [Dashboard and Network Health](Dashboard_and_Network_Health.md) | |
| Network Health (`/network-health`) | [Dashboard and Network Health](Dashboard_and_Network_Health.md) | |
| Network Status (`/system-status`) | [Dashboard and Network Health](Dashboard_and_Network_Health.md) | |
| Device Inventory (`/device-inventory`) | [Device Inventory](Device_Inventory.md) | Merging duplicates: [Device identity review](Device_Identity_Review.md) |
| History (`/history`) | [Alerts and notification history](Alerts_and_Notification_History.md) | |
| Topology (`/topology`) | [Network topology](Topology.md) | |
| Plugin Manager (`/plugins`) | [Plugin Manager](Plugin_Manager.md) | Your own checks: [Custom checks](Custom_Checks_Manual.md), [Application checks](Application_Checks.md) |
| NCPA Deployment (`/ncpa-deployment`) | [NCPA deployment](NCPA_Deployment.md) | |
| Maintenance (`/maintenance`) | [Maintenance windows](Maintenance_Windows.md) | |
| Remediation (`/remediation`) | [Automatic recovery](Automatic_Recovery.md), [Remote service restart](Remote_Service_Restart.md) | **TBC:** no single walkthrough of the page itself |
| Reports (`/reports`) | [Service reports](Service_Reports.md) | |
| System Logs (`/system-logs`) | [System logs](System_Logs.md) | Nagios log: [Storage and Nagios logs](Storage_and_Nagios_Logs.md) |
| Manage Accounts (`/accounts`) | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) | |
| Manage Roles (`/manage-roles`) | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) | |
| Settings (`/settings`) | [Settings](Settings.md) | Tabs: [Network discovery](Network_Discovery.md), [Email settings](Email_Settings.md), [Notification policy](Notification_Policy.md) |

## Tasks

| Task | Guide |
|---|---|
| Find and inspect a host | [Device Inventory](Device_Inventory.md) |
| Resolve a duplicate device identity | [Device identity review](Device_Identity_Review.md) |
| Acknowledge an alert | [Dashboard and Network Health](Dashboard_and_Network_Health.md) |
| Scan the network | [Network discovery](Network_Discovery.md) |
| Reset a forgotten password | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) |
| Back up and restore | [Backup and restore](Backup_and_Restore.md) |
| Build a local test lab | [Local lab](Local_Lab.md) |
