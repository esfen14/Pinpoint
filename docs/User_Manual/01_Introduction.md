## 1. Introduction

### 1.1 Overview and purpose

PinPoint is a web application that shows the health of an organisation's
network in one place. It answers questions such as:

- Is any device or service down right now?
- What went wrong yesterday, and who handled it?
- Which devices are on the network, and which of them are being watched?

PinPoint does not do the checking itself. A proven monitoring program called
**Nagios Core** runs on the same server and checks each device every few
minutes. PinPoint reads Nagios's results, stores them, and presents them in
plain pages, so you do not need to learn Nagios's own screens.

PinPoint runs on one server inside your network. It has no cloud component:
your monitoring data stays on that server.

### 1.2 Main features

| Feature | What it does for you | Page |
|---|---|---|
| Dashboard | One-page answer to "is anything broken right now?" | Dashboard |
| Network health | Deeper view of hosts, services, trends and bandwidth | Network Health, Network Status |
| Device inventory | Every device found on the network and why each port is or is not watched | Device Inventory |
| Network discovery | Scans your networks and finds devices and open ports automatically | Settings → Network Discovery |
| Alert acknowledgement | Mark a problem as "known and being handled", with a comment | Dashboard, Network Health, Network Status |
| History | Past alerts and notifications, with who acknowledged them | History |
| Topology | Picture of which device depends on which (parents you set) | Topology |
| Email alerts | Sends formatted alert email to chosen people | Settings → Email, Manage Accounts |
| Maintenance windows | Silences alerts during planned work | Maintenance |
| Automatic recovery | Restarts a failed service by itself, within safe limits | Remediation |
| Reports | Availability and event reports for a period, with export | Reports |
| Plugin Manager | Chooses which kinds of checks are switched on | Plugin Manager |
| NCPA deployment | Installs a small agent on servers so CPU, memory and disk can be watched | NCPA Deployment |
| Accounts and roles | Controls who can sign in and what each person can see and do | Manage Accounts, Manage Roles |

### 1.3 Intended users

| User | Typical tasks |
|---|---|
| Network administrator | Watches the Dashboard, acknowledges alerts, scans networks, manages devices and checks |
| IT staff / help desk | Reads current status and history, acknowledges alerts they are handling |
| Supervisor or manager | Reads the Dashboard and Reports |
| System administrator (Super Admin) | Manages accounts, roles, settings, email and backups |

The exact pages each person sees depend on their **role** (see
[User roles and permissions](05_User_roles_and_permissions.md#5-user-roles-and-permissions)).

### 1.4 Benefits and practical applications

- **Faster response:** problems appear on the Dashboard within minutes, and
  alert email can reach the right person.
- **Less noise:** acknowledgement, maintenance windows, quiet hours and
  flap detection reduce repeated or unwanted alerts.
- **Accountability:** every acknowledgement records who, when and why, and
  System Logs record configuration changes.
- **No Nagios training needed:** staff use PinPoint's pages instead of Nagios's
  native interface.

Practical examples: a school computer laboratory watching its switches and
servers; a small office checking that its file server, web server and printer
stay reachable; an IT team proving service availability for a month with a
report.
