## 5. User roles and permissions

### 5.1 User types

An account has exactly one **role**. A role is a named set of
**permissions**. A fresh installation has three built-in roles:

| Role | Intended for | Permissions |
|---|---|---|
| **Super Admin** | System administrator | Every permission. Its name and permissions cannot be changed |
| **Manager** | Supervisor or senior staff | None until an administrator grants them |
| **Staff** | Day-to-day operators | None until an administrator grants them |

Administrators can create more roles in **Manage Roles**.

### 5.2 Features per permission

| Area | Permission | Allows |
|---|---|---|
| Dashboard | `system.dashboard` | Open the Dashboard |
| Monitoring pages | `system.network_health` | Network Health, Network Status, Device Inventory, Topology |
| History | `system.history` | History page |
| Reports | `system.report` | Reports page |
| Logs | `system.logs` | System Logs page |
| Alerts | `system.acknowledge_alerts` | Acknowledge and unacknowledge |
| Alerts | `system.recheck` | **Check now** |
| Devices | `system.hosts` | See ports, interfaces, SNMP and address history |
| Devices | `system.hosts.edit` | Change ports, pause/resume, interfaces, SNMP, parents |
| Devices | `system.hosts.alerts` | Choose alert email recipients per device |
| Discovery | `system.discover` | Run scans; review duplicate devices |
| NCPA | `system.deploy.ncpa` | NCPA Deployment page |
| Maintenance | `maintenance.manage` | Maintenance page |
| Remediation | `remediation.view`, `remediation.manage` | See, and change, automatic recovery |
| Plugins | `plugin.view`, `plugin.enable`, `plugin.disable`, other `plugin.*` | Plugin Manager |
| Accounts | `account.view`, `account.info`, `account.edit`, `account.alerts` | Manage Accounts |
| Roles | `role.view`, `role.info`, `role.edit`, `role.list` | Manage Roles |
| Settings | `settings.security`, `settings.system`, `settings.discovery`, `settings.plugins`, `settings.email` | The matching Settings tab |

The **Manage Roles** page is the authoritative list on a running system.

### 5.3 Access restrictions

- Pages you have no permission for are hidden from the sidebar, and typing
  their address shows an access message.
- The server checks every request again, so hiding a page is not the only
  protection.
- Only **Active** accounts can sign in.
- The first administrator account cannot be suspended, made inactive, or
  given a role that lacks account and role administration.

### 5.4 Account and password management

| Task | Who | How |
|---|---|---|
| Change own password | Any user | No self-service screen exists; only the forced change at first sign-in. Ask an administrator for a reset |
| Forced password change | Any user | Appears at sign-in when flagged |
| Reset someone's password | `account.edit` | [Sign in, accounts and roles](guides/Login_Accounts_and_Roles.md) |
| Deactivate an account | `account.edit` | Edit Account → Status **Inactive** or **Suspended** |

Password rules (set in **Settings → Security → Strong Password Policy**):

| Policy | Rule |
|---|---|
| Off | At least 8 characters |
| On | At least 12 characters, with an uppercase letter, a lowercase letter, a number and a special character |

A new password may not be the same as the current one.
