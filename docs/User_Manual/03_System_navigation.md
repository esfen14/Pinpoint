## 3. System navigation

### 3.1 Main dashboard

The **Dashboard** (sidebar entry **Overview**) is the first page after
sign-in. From top to bottom it shows: when it was last updated and **Rescan
Network**, summary cards (hosts, latency, warnings, critical issues),
appliance storage, status and performance overviews, average CPU use (only
when the NCPA agent is installed on some hosts), **Running out soon**
forecasts, the **Active Alerts** list and **Recent Notifications**. On wide
screens a **Service Overview** panel on the right shows whether Nagios is
running. Details are in
[Dashboard, Network Health and Network Status](guides/Dashboard_and_Network_Health.md).

### 3.2 Menus and navigation controls

Sidebar pages (shown only with the right permission):

| Sidebar entry | Address | What it is for |
|---|---|---|
| Overview | `/dashboard` | Current overall status |
| Network Health | `/network-health` | Network-wide summary, trends, bandwidth |
| Device Inventory | `/device-inventory` | Every device, its ports and monitoring state |
| Network Status | `/system-status` | Service table with acknowledgement (heading "Network Service Overview") |
| Topology | `/topology` | Parent-child map of devices |
| Plugins | `/plugins` | Which kinds of checks are switched on (Plugin Manager) |
| NCPA Deployment | `/ncpa-deployment` | Install and track the NCPA agent |
| Maintenance | `/maintenance` | Planned maintenance windows |
| Remediation | `/remediation` | Automatic recovery actions and their run log |
| History | `/history` | Past alerts and notifications |
| Report | `/reports` | Availability and event reports, with export |
| System Logs | `/system-logs` | Audit logs and the Nagios log |
| Manage Accounts | `/accounts` | User accounts |
| Manage Roles | `/manage-roles` | Roles and permissions |
| Settings | `/settings` | Personal display preferences and system settings |

The entries appear in this order.

Other controls you will meet on most pages:

| Control | Use |
|---|---|
| Search box | Filters a table by text; what it matches depends on the page (Device Inventory matches hostnames only) |
| Filter menus | Limit a table to a state, acknowledgement or monitoring label |
| Column headings | Choose a heading to sort by it, where supported |
| Paging controls | Move between pages of a long table |
| Row or **detail drawer** | Choose a row to open a panel with details and actions |
| **Refresh** | Reload the page's data now |

### 3.3 Buttons, icons and their functions

| Button or icon | Where | Function |
|---|---|---|
| **Acknowledge** | Alert rows | Mark a problem as known; asks for a comment |
| **Unacknowledge** | Acknowledged rows | Remove the acknowledgement |
| **Acknowledge all** | Dashboard Active Alerts | Acknowledge every visible unacknowledged alert with one comment |
| **Check now** | Host or service drawer | Ask Nagios to check the item immediately |
| **Toggle sidebar** | Header | Hide or show the sidebar so the page can use the full width. It is shown again when the page is reloaded; sign out stays available in the header's account menu |
| Bell | Header | Recent notifications; a count shows unread items |
| **Save Changes** / **Discard Changes** | Settings | Save or undo edits on the current tab |
| **Reset to Defaults** | Some settings | Restore defaults (not saved until you choose **Save Changes**) |
| **Export** | Reports, logs | Download the current view (CSV, PDF or XLS where allowed) |
| **Scan device** / **Rescan Network** | Settings → Network Discovery | Scan one address, or all saved networks |
| **Pause** / **Resume** | Device drawer | Stop or restart monitoring of one device |

State colours used throughout:

| Colour | Meaning |
|---|---|
| Green | OK or UP |
| Yellow | WARNING |
| Red | CRITICAL or DOWN |
| Orange or grey | UNKNOWN or UNREACHABLE |
| Muted | Acknowledged |
| Blue or purple | In scheduled downtime (maintenance) |

### 3.4 Available modules

Each page in [3.2](#32-menus-and-navigation-controls) has its own section in
[Step-by-step operating instructions](04_Step_by_step_operating_instructions.md).
