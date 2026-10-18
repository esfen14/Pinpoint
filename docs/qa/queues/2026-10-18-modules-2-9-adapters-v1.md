# Prepared module QA queue

Waiting for explicit start. No tests have started.
Target revision: `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`; scope: `efdc3c649459817d266e2072258d7961dd65456e42bc68e8df1802cda4a58b6a`

## modules-2-9-adapters-v1 — Paeng

Modules: ACC, DASH, DI, HIS, ROL; purpose: untested.
Five batches per session; at most five ordinary IDs per batch.

| Batch | Exact IDs |
|---|---|
| modules-2-9-adapters-v1-001 | TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03, TC-DASH-07 |
| modules-2-9-adapters-v1-002 | TC-DI-08, TC-HIS-04 |

### Exclusions


### Card: TC-ACC-08 — "Send this user email alerts" depends on permission

Historical summary: Not run; detail: Not run.
Phase: 2; singleton: False; requirements: REQ-ACC-07
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 2 – Manage Accounts (`/accounts`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-ACC-01 | Add an account | ACC-01 | EP | H | PASS |
| TC-ACC-02 | Duplicate and invalid emails are refused | ACC-01 | EP | M | PASS |
| TC-ACC-03 | "Require password change at first sign-in" | ACC-02 | EG | M | PASS |
| TC-ACC-04 | Inactive and suspended users cannot sign in | ACC-03 | DT | H | PASS |
| TC-ACC-05 | Editing a signed-in user signs them out | ACC-04 | ST | M | FAIL |
| TC-ACC-06 | Administrator resets another user's password | ACC-05 | ST | H | FAIL |
| TC-ACC-07 | The first (bootstrap) account is protected | ACC-06 | DT | H | PASS |
| TC-ACC-08 | "Send this user email alerts" depends on permission | ACC-07 | DT | L | Not run |
| TC-ACC-09 | The accounts page needs permission | ACC-08 | DT | H | Not run |
| TC-ACC-10 | Add User uses the default role (issue #191) | ACC-09 | EG | M | Not run |



Prerequisites:
| TC-ACC-08 | TC-ROL-01 | Needs a role `qa-accounts` and a user with it, made the same way |

#### TC-ACC-08 – "Send this user email alerts" depends on permission

**Requirement:** REQ-ACC-07 · **Technique:** DT · **Priority:** L · **Result:** Not run

**Before you start:** a role `qa-accounts` with `account.view` and `account.edit` but not `account.alerts`, and a user with that role.

**Steps**

1. As Super Admin press **+ Add User** and look for the checkbox **Send this user email alerts**. Look at the **Email Alerts** column in the table.
2. Sign in as the `qa-accounts` user, open **Manage Accounts**, and press **+ Add User**.

**Expected result**

- Super Admin sees the checkbox and the column shows On or Off per user.
- The `qa-accounts` user does not see the checkbox.

Expected-item evidence checklist:

- E1: Super Admin sees the checkbox and the column shows On or Off per user.
- E2: The `qa-accounts` user does not see the checkbox.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Card: TC-ROL-04 — A dashboard-only user is limited to the Dashboard

Historical summary: Not run; detail: Not run.
Phase: 2; singleton: False; requirements: REQ-ROL-04
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 3 – Manage Roles (`/manage-roles`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-ROL-01 | Create a role | ROL-01 | EP | H | PASS |
| TC-ROL-02 | The Super Admin role is read-only | ROL-02 | EG | M | PASS |
| TC-ROL-03 | The bootstrap administrator's role is locked | ROL-03 | DT | H | PASS |
| TC-ROL-04 | A dashboard-only user is limited to the Dashboard | ROL-04 | DT | H | Not run |
| TC-ROL-05 | A Staff user can open only Settings | ROL-04 | DT | H | PASS |
| TC-ROL-06 | Settings tabs follow their own permissions | ROL-05 | DT | M | PASS |



Prerequisites:
| TC-ROL-04 | TC-ROL-01, TC-ACC-01 | Needs the role `qa-view` and a user with it |

#### TC-ROL-04 – A dashboard-only user is limited to the Dashboard

**Requirement:** REQ-ROL-04 · **Technique:** DT · **Priority:** H · **Result:** Not run

**Before you start:** the role `qa-view` (TC-ROL-01) and a user with that role, for example `qa.view@mail-lab.com`.

**Steps**

1. Sign in as that user and read the sidebar.
2. Type each of these addresses one at a time: `/network-health`, `/device-inventory`, `/topology`, `/system-status`, `/plugins`, `/ncpa-deployment`, `/maintenance`, `/remediation`, `/history`, `/reports`, `/system-logs`, `/accounts`, `/manage-roles`.
3. Open these API addresses in the address bar: `/api/system/log`, `/api/system/report/availability`, `/api/user/accounts`.

**Expected result**

- The sidebar shows **Overview** (and **Settings**) only.
- Every address in step 2 redirects back to the Dashboard.
- Every API address in step 3 returns 403.

Expected-item evidence checklist:

- E1: The sidebar shows **Overview** (and **Settings**) only.
- E2: Every address in step 2 redirects back to the Dashboard.
- E3: Every API address in step 3 returns 403.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Card: TC-DI-02 — Port groups and their order

Historical summary: Not run; detail: Not run.
Phase: 5; singleton: False; requirements: REQ-DI-02
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 9 – Device Inventory (`/device-inventory`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DI-01 | Who sees the Ports section | DI-01 | DT | H | PASS |
| TC-DI-02 | Port groups and their order | DI-02 | EP | M | Not run |
| TC-DI-03 | One reason per port | DI-03 | DT | M | Not run |
| TC-DI-04 | View-only without edit permission | DI-04 | DT | H | PASS |
| TC-DI-05 | Stop and resume monitoring | DI-05, DI-06 | ST | H | Not run |
| TC-DI-06 | Leave suggested holds the port | DI-07 | ST | M | Not run |
| TC-DI-07 | Service name rules in Set service | DI-08 | BVA | H | Not run |
| TC-DI-08 | The "Checked by" line | DI-08 | EP | M | Not run |
| TC-DI-09 | Pin and Remove pin | DI-09 | ST | M | Not run |
| TC-DI-10 | The NCPA port is protected | DI-10 | EG | M | Not run |
| TC-DI-11 | One monitoring label per device | DI-11 | DT | H | Not run |
| TC-DI-12 | Monitoring filter | DI-11 | EP | M | Not run |
| TC-DI-13 | Pause and resume | DI-12 | ST | H | Not run |
| TC-DI-14 | Invalid pause and resume | DI-12 | DT | M | Not run |
| TC-DI-15 | Out-of-config devices show "last known status" | DI-13 | EG | M | Not run |
| TC-DI-16 | Needs Review section | DI-14 | DT | M | Not run |
| TC-DI-17 | The review drawer writes nothing | DI-14 | EP | M | Not run |
| TC-DI-18 | Merging needs edit permission and two distinct records | DI-14 | DT | H | Not run |
| TC-DI-19 | Merge confirmation | DI-14 | ST | H | Not run |

To open a host's drawer press **View host details** on its row. The drawer has the **Services** list, **Performance data**, **Timestamps**, **Acknowledgement**, and, for a discovered device, sections such as **Monitoring**, **Ports**, **SNMP**, **Interfaces**, **Email alert recipients**, and **Parent devices**. Pressing a service in the list shows the service view, and **Back to host** returns.

**9a. Ports**



Prerequisites:
| TC-DI-01 to 04, 11 to 13, TC-TOP-01 to 06 | TC-DSC-01 | They need discovered devices |

#### TC-DI-02 – Port groups and their order

**Requirement:** REQ-DI-02 · **Technique:** EP · **Priority:** M · **Result:** Not run

**Before you start:** a device with ports in several states (Monitored, Suggested, Ignored, Archived).

**Steps**

1. Open that device's drawer and read the **Ports** groups from top to bottom.
2. Read the count in each group header and the order inside a group.

**Expected result**

- Groups appear in this order: **Needs attention**, **Monitored**, **Suggested**, **Stopped**, **Archived** (collapsed).
- Each header has a count, and a group with no ports is not shown.
- Inside a group, TCP ports come before UDP, each by port number.

Expected-item evidence checklist:

- E1: Groups appear in this order: **Needs attention**, **Monitored**, **Suggested**, **Stopped**, **Archived** (collapsed).
- E2: Each header has a count, and a group with no ports is not shown.
- E3: Inside a group, TCP ports come before UDP, each by port number.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Card: TC-DI-03 — One reason per port

Historical summary: Not run; detail: Not run.
Phase: 5; singleton: False; requirements: REQ-DI-03
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 9 – Device Inventory (`/device-inventory`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DI-01 | Who sees the Ports section | DI-01 | DT | H | PASS |
| TC-DI-02 | Port groups and their order | DI-02 | EP | M | Not run |
| TC-DI-03 | One reason per port | DI-03 | DT | M | Not run |
| TC-DI-04 | View-only without edit permission | DI-04 | DT | H | PASS |
| TC-DI-05 | Stop and resume monitoring | DI-05, DI-06 | ST | H | Not run |
| TC-DI-06 | Leave suggested holds the port | DI-07 | ST | M | Not run |
| TC-DI-07 | Service name rules in Set service | DI-08 | BVA | H | Not run |
| TC-DI-08 | The "Checked by" line | DI-08 | EP | M | Not run |
| TC-DI-09 | Pin and Remove pin | DI-09 | ST | M | Not run |
| TC-DI-10 | The NCPA port is protected | DI-10 | EG | M | Not run |
| TC-DI-11 | One monitoring label per device | DI-11 | DT | H | Not run |
| TC-DI-12 | Monitoring filter | DI-11 | EP | M | Not run |
| TC-DI-13 | Pause and resume | DI-12 | ST | H | Not run |
| TC-DI-14 | Invalid pause and resume | DI-12 | DT | M | Not run |
| TC-DI-15 | Out-of-config devices show "last known status" | DI-13 | EG | M | Not run |
| TC-DI-16 | Needs Review section | DI-14 | DT | M | Not run |
| TC-DI-17 | The review drawer writes nothing | DI-14 | EP | M | Not run |
| TC-DI-18 | Merging needs edit permission and two distinct records | DI-14 | DT | H | Not run |
| TC-DI-19 | Merge confirmation | DI-14 | ST | H | Not run |

To open a host's drawer press **View host details** on its row. The drawer has the **Services** list, **Performance data**, **Timestamps**, **Acknowledgement**, and, for a discovered device, sections such as **Monitoring**, **Ports**, **SNMP**, **Interfaces**, **Email alert recipients**, and **Parent devices**. Pressing a service in the list shows the service view, and **Back to host** returns.

**9a. Ports**



Prerequisites:
| TC-DI-01 to 04, 11 to 13, TC-TOP-01 to 06 | TC-DSC-01 | They need discovered devices |

#### TC-DI-03 – One reason per port

**Requirement:** REQ-DI-03 · **Technique:** DT · **Priority:** M · **Result:** Not run

**Before you start:** a Suggested port that is both held (**Leave suggested**) and flagged **Not used as intended**.

**Steps**

1. Open the device drawer and find that port in **Ports**.
2. Read the reason text under it.

**Expected result**

- Exactly one reason shows.
- It is "Not used as intended: expected …, found …. Not monitored until acknowledged." (the first matching reason wins), not the "Held back" reason.

Expected-item evidence checklist:

- E1: Exactly one reason shows.
- E2: It is "Not used as intended: expected …, found …. Not monitored until acknowledged." (the first matching reason wins), not the "Held back" reason.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Card: TC-DASH-07 — "No data" instead of blank cards

Historical summary: Not run; detail: Not run.
Phase: 6; singleton: False; requirements: REQ-DASH-06
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 4 – Dashboard (sidebar: Overview, `/dashboard`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DASH-01 | The four summary cards | DASH-01 | EP | H | PASS |
| TC-DASH-02 | A paused device is left out of the counts | DASH-02 | ST | H | PASS |
| TC-DASH-03 | The Active Alerts table matches the cards | DASH-03 | DT | H | PASS |
| TC-DASH-04 | All-clear state | DASH-03 | EG | M | PASS |
| TC-DASH-05 | Service Overview panel | DASH-04 | EP | M | PASS |
| TC-DASH-06 | Refresh text and stale Nagios warning | DASH-05 | BVA | M | Not run |
| TC-DASH-07 | "No data" instead of blank cards | DASH-06 | EG | M | Not run |
| TC-DASH-08 | The Dashboard needs permission | DASH-07 | DT | H | PASS |
| TC-DASH-09 | "Running out soon" forecast list (issue #156) | DASH-08 | EP | M | Not run |

The page has: the header with the refresh text and the **Rescan Network** button, the **Appliance storage** card, four cards (**Total Hosts**, **Network Latency**, **Active Warnings**, **Critical Issues**), **Network Status Overview** (Online and Offline), **Network Performance**, **Average Resource Utilization** (only when an NCPA host reports), **Running out soon**, the **Active Alerts** table, **Recent Notifications**, and the **Service Overview** panel on the right.



Prerequisites:

#### TC-DASH-07 – "No data" instead of blank cards

**Requirement:** REQ-DASH-06 · **Technique:** EG · **Priority:** M · **Result:** Not run

**Before you start:** a lab with no ping check on any host and no NCPA host.

**Steps**

1. Open **Overview**.
2. Read **Network Latency**, **Network Performance**, and look for **Average Resource Utilization**.

**Expected result**

- **Network Latency** and **Network Performance** show "No data", not an empty box.
- **Average Resource Utilization** is not shown at all.

Expected-item evidence checklist:

- E1: **Network Latency** and **Network Performance** show "No data", not an empty box.
- E2: **Average Resource Utilization** is not shown at all.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Card: TC-DI-08 — The "Checked by" line

Historical summary: Not run; detail: Not run.
Phase: 7; singleton: False; requirements: REQ-DI-08
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 9 – Device Inventory (`/device-inventory`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-DI-01 | Who sees the Ports section | DI-01 | DT | H | PASS |
| TC-DI-02 | Port groups and their order | DI-02 | EP | M | Not run |
| TC-DI-03 | One reason per port | DI-03 | DT | M | Not run |
| TC-DI-04 | View-only without edit permission | DI-04 | DT | H | PASS |
| TC-DI-05 | Stop and resume monitoring | DI-05, DI-06 | ST | H | Not run |
| TC-DI-06 | Leave suggested holds the port | DI-07 | ST | M | Not run |
| TC-DI-07 | Service name rules in Set service | DI-08 | BVA | H | Not run |
| TC-DI-08 | The "Checked by" line | DI-08 | EP | M | Not run |
| TC-DI-09 | Pin and Remove pin | DI-09 | ST | M | Not run |
| TC-DI-10 | The NCPA port is protected | DI-10 | EG | M | Not run |
| TC-DI-11 | One monitoring label per device | DI-11 | DT | H | Not run |
| TC-DI-12 | Monitoring filter | DI-11 | EP | M | Not run |
| TC-DI-13 | Pause and resume | DI-12 | ST | H | Not run |
| TC-DI-14 | Invalid pause and resume | DI-12 | DT | M | Not run |
| TC-DI-15 | Out-of-config devices show "last known status" | DI-13 | EG | M | Not run |
| TC-DI-16 | Needs Review section | DI-14 | DT | M | Not run |
| TC-DI-17 | The review drawer writes nothing | DI-14 | EP | M | Not run |
| TC-DI-18 | Merging needs edit permission and two distinct records | DI-14 | DT | H | Not run |
| TC-DI-19 | Merge confirmation | DI-14 | ST | H | Not run |

To open a host's drawer press **View host details** on its row. The drawer has the **Services** list, **Performance data**, **Timestamps**, **Acknowledgement**, and, for a discovered device, sections such as **Monitoring**, **Ports**, **SNMP**, **Interfaces**, **Email alert recipients**, and **Parent devices**. Pressing a service in the list shows the service view, and **Back to host** returns.

**9a. Ports**



Prerequisites:
| TC-DI-05 to 09, TC-DX-01 to 05 | TC-PLG-03 | They need monitored ports and the plugins for them |

#### TC-DI-08 – The "Checked by" line

**Requirement:** REQ-DI-08 · **Technique:** EP · **Priority:** M · **Result:** Not run

**Steps**

1. In **Set service…** on a TCP port type `http`.
2. Type an unknown name such as `myapp` on the same TCP port.
3. Open the dialog on a UDP port and type `myapp`.

**Expected result**

- `http` shows the plugin `check_http`.
- The unknown TCP name shows "check\_tcp (generic TCP check)".
- The unknown UDP name shows "Skipped: no check exists for this UDP service".
- The text "Scans will no longer change this port's service on this device." is always shown.

Expected-item evidence checklist:

- E1: `http` shows the plugin `check_http`.
- E2: The unknown TCP name shows "check\_tcp (generic TCP check)".
- E3: The unknown UDP name shows "Skipped: no check exists for this UDP service".
- E4: The text "Scans will no longer change this port's service on this device." is always shown.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Card: TC-HIS-04 — Date range rules (API)

Historical summary: Not run; detail: Not run.
Phase: 8; singleton: False; requirements: REQ-HIS-03
Source adapter coverage: implemented / scripted automation (not a runtime result).

Module setup/notes:
### Module 8 – History (`/history`)

**Summary of cases**

| TC | Case | Req | Tech | Pri | Result |
| --- | --- | --- | --- | --- | --- |
| TC-HIS-01 | History needs permission | HIS-01 | DT | H | PASS |
| TC-HIS-02 | Time presets | HIS-02 | EP | M | PASS |
| TC-HIS-03 | Filters work together | HIS-02 | DT | M | PASS |
| TC-HIS-04 | Date range rules (API) | HIS-03 | BVA | M | Not run |
| TC-HIS-05 | Sorting | HIS-04 | EP | L | PASS |
| TC-HIS-06 | Rows per page | HIS-05 | BVA | L | PASS |
| TC-HIS-07 | Row detail and the link between tabs | HIS-06 | EP | M | PASS |
| TC-HIS-08 | Filters with no results | HIS-02 | EG | L | PASS |

The page has two tabs, **Alerts** and **Notifications**. Filters: **Time range**, **Type**, **Host**, **Service**, **New state**, **Acknowledged**, **State type**, **Source** (notifications), **Apply**, **Clear filters**, and **Rows per page**.



Prerequisites:
| TC-HIS-02 to 08 | TC-ACK-08, TC-SET-07 | Alert and notification events must exist |

#### TC-HIS-04 – Date range rules (API)

**Requirement:** REQ-HIS-03 · **Technique:** BVA · **Priority:** M · **Result:** Not run

**Steps**

1. Open `/api/system/history/alerts?start_date=2026-10-01&end_date=2026-10-02`.
2. Open it with only `start_date`.
3. Open it with `start_date=2026-10-02&end_date=2026-10-01` (reversed).
4. Open it with `start_date=abc&end_date=def`.

**Expected result**

- Step 1 returns events (or an empty list).
- Steps 2, 3, and 4 are refused with an error and no data.
- With no dates and no preset the range is the past 24 hours.

Expected-item evidence checklist:

- E1: Step 1 returns events (or an empty list).
- E2: Steps 2, 3, and 4 are refused with an error and no data.
- E3: With no dates and no preset the range is the past 24 hours.

Execution adapter/card (empty means BLOCKED):
```json
{}
```

### Global setup and dependency source snapshot

# Pinpoint - Black-Box Test Cases by Module with Traceability Matrix

Oct 16, 2026 · @Raf

## Scope and approach

This suite tests Pinpoint module by module, the way a user (or an API client) sees it, with no knowledge of the code. Every test case tells you what to prepare, the exact steps to follow, and what you should see. Every case traces to a requirement taken from the repository's `spec files/` (see the traceability matrix at the end). It covers 23 modules plus 8 end-to-end scenarios, and it was checked against the repository's `main` branch at commit `4b1ad9f` (merged 2026-10-17).

**Black-box techniques used**

- **EP**: equivalence partitioning, one valid and one invalid class per input
- **BVA**: boundary value analysis, on limits the spec states (for example flap thresholds 0 to 100, retry interval 1 to 10 minutes)
- **DT**: decision table, for permission and state combinations
- **ST**: state transition, for pause/resume, acknowledge/unacknowledge, and enable/disable flows
- **EG**: error guessing, for empty states, cancelled dialogs, and double submits

**Conventions**

- **Test case ID:** `TC-<MODULE>-<nn>`, such as `TC-AUTH-03`.
- **Requirement ID:** `REQ-<MODULE>-<nn>`. The specs have no requirement IDs of their own, so each one here is a short statement of a spec rule and names its source section in the traceability matrix.
- **Priority:** H = a failure blocks the module or is a security issue, M = a failure breaks a feature, L = a cosmetic or edge case.
- **Result values:** PASS, FAIL (write what you saw), PARTIALLY PASS (write what was missing), BLOCKED (write which case blocked it), or Not run. Results already recorded by the tester are kept in this revision.
- **Passwords for test accounts:** use a value such as `Lab-Pinpoint-2026!`. It has 12 or more characters with upper and lower case letters, a number, and a symbol, so it passes both the strong policy (Settings, Security) and the relaxed policy (8 or more characters).
- **Data setup:** unless a case says otherwise, the lab has at least one host Up, one host Down, one service Critical, and one acknowledged alert.

The repository's `docs/qa/QA_Test_Plan.md` is organized by user journey (J1 to J9). This document regroups coverage by module and adds boundary, negative, and permission cases. Where a journey case covers the same check, the traceability matrix names it in the Source column (for example QA J1-03).

**How to read a test case**

- The first line gives the requirement, the technique, the priority, and the result.
- **Before you start** lists what must be ready. Skip it only if the case does not have one.
- **Steps** are done in order. Button, tab, and field names are in **bold** exactly as they appear on screen. Addresses and API paths are in `code`.
- **Expected result** is a list. Every item must be true for PASS.
- **Note** appears where the spec and the real app differ. The app's behavior is what you test, and the difference is reported as a finding.

**Test accounts and lab**

- **Super Admin:** the built-in role with every permission. It was called "Administrator" before issue #112. `flask sync-permissions` renames an existing one. If a different role already used the name "Super Admin", the old one is kept as "Administrator (Legacy)". On a development database filled by `flask seed`, the account is `admin@test.com` with password `Password123!` (development only).
- **Staff user:** any user whose role is the built-in **Staff** role. Staff holds no permissions, so after signing in the user can open only **Settings**, and only the **General Settings** tab. This one account is used wherever a case needs a user who is denied everything. On a development database use `emily.davis@test.com` with `Password123!`. On any other install create one in TC-ACC-01.
- **Dashboard-only user:** only a few cases need a user who can open the Dashboard and nothing else. Create the role `qa-view` with only `system.dashboard` (TC-ROL-01) and a user with that role.
- **Lab:** the Pinpoint appliance, a web VM (HTTP on port 80, SSH on port 22), a second Linux VM, an SMTP test mailbox, and a browser plus a private window for second sessions.

**Where to find each page**

| Sidebar label | Address | Permission needed |
| --- | --- | --- |
| Overview | `/dashboard` | `system.dashboard` |
| Network Health | `/network-health` | `system.network_health` |
| Device Inventory | `/device-inventory` | `system.network_health` |
| Topology | `/topology` | `system.network_health` |
| System Status | `/system-status` | `system.network_health` |
| Plugins | `/plugins` | `plugin.view` |
| NCPA Deployment | `/ncpa-deployment` | `system.deploy.ncpa` |
| Maintenance | `/maintenance` | `maintenance.manage` |
| Remediation | `/remediation` | `remediation.view` |
| History | `/history` | `system.history` |
| Report | `/reports` | `system.report` |
| System Logs | `/system-logs` | `system.logs` |
| Manage Accounts | `/accounts` | `account.view` |
| Manage Roles | `/manage-roles` | `role.view` |
| Settings | `/settings` | none. Tabs: General Settings (everyone), Security (`settings.security`), System (`settings.system`), Network Discovery (`settings.discovery`), Plugins (`settings.plugins`), Email (`settings.email`) |

A user who opens a page they may not use is sent to the first page they can use (a Staff user lands on Settings).

**What changed in this revision**

- **Role name:** "Administrator" is now "Super Admin" (#112).
- **Test users:** the old `viewer` and `noperm` are replaced by the Staff user, and a dashboard-only user only where a case needs one.
- **Steps:** every case now has numbered steps using the button and tab names in the app code.
- **Spec and app differ (marked Note in the case):** the Dashboard has four cards (Total Hosts, Network Latency, Active Warnings, Critical Issues), not the spec's Active Alerts and Hosts in Downtime cards. Unacknowledge asks no confirmation. The Active Alerts list has no acknowledgement filter. Rescan Network starts at once with no confirmation. The host table and host drawer are on Device Inventory, not Network Health.
- **New in `main` since the first revision:** resource forecast "Running out soon" (#156), remote service restart (#182), remediation safety controls and the kill switch (#155), the Add User default role fix (#191), and Clean up now offered on deployed devices.

## Run order and prerequisites

Some cases need something an earlier case creates, for example a user, a role, an active alert, or a deployed agent. Run the cases in the order below. Each case appears once, and the numbers continue within the same module ("TC-ACC-01, 02, 03" means TC-ACC-01, TC-ACC-02, TC-ACC-03). Run the 8 end-to-end scenarios afterwards on a freshly built (or restored) appliance.

### Run order

| Phase | Goal | Run these cases in this order |
| --- | --- | --- |
| 1 | Fresh install and first login (clean appliance) | TC-AUTH-05, 06, 07, 01, 02, 03, 04, 09, 12 |
| 2 | Roles and accounts (this creates the test users used later) | TC-ROL-01, 02, 03, TC-ACC-01, 02, 03, TC-AUTH-08, TC-ACC-04, 05, 06, 07, 09, 10, 08, TC-ROL-04, 05, 06, TC-AUTH-10, 11, TC-SHL-09, 04, 10 |
| 3 | Permission checks with the Staff user | TC-DASH-08, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07, TC-LOG-05, TC-SHL-06, TC-NFR-01, 02 |
| 4 | Settings the lab needs (email first) | TC-SET-07, 01, 02, 03, 04, 05, 06, TC-SHL-01, 02, 03 |
| 5 | Discover the network and enable plugins | TC-DSC-01, 02, 03, 04, 05, 08, 09, TC-PLG-01, 02, 03, 04, 05, 06, TC-DI-01, 02, 03, 04 |
| 6 | Views with live data, device extras, topology | TC-DASH-01, 05, 07, TC-NH-01, 02, 03, 04, 05, TC-SS-01, 02, 03, TC-DX-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, TC-NH-06, 07, TC-TOP-01, 02, 03, 04, 05, 06 |
| 7 | Device changes | TC-DI-05, 06, 07, 08, 09, 11, 12, 13, TC-DASH-02, TC-DI-14, 15, 16, 17, 18, 19, TC-DSC-06, 07 |
| 8 | Faults, alerts, history, and maintenance | TC-DASH-03, TC-ACK-01, 02, 03, 04, 05, 06, 07, 08, TC-DASH-04, TC-HIS-02, 03, 04, 05, 06, 07, 08, TC-SHL-07, 08, TC-MNT-01, 02, 03, 04, 05, 06, 07, 09, 10 |
| 9 | NCPA and automatic recovery | TC-NCPA-01, 02, 03, 04, 05, 06, 07, 09, 10, 11, TC-DI-10, TC-DASH-09, TC-SS-05, TC-REM-02, 01, 04, 03, 05, 07, 09, 06, 08, 10 |
| 10 | Reports and logs (after incidents exist) | TC-RPT-01, 02, 03, 04, 05, 06, TC-LOG-01, 02, 03, 04, TC-SHL-05 |
| 11 | Cases that stop or break services (last, then restore everything) | TC-DASH-06, TC-MNT-08, TC-SET-08, 09 |
| 12 | Quality and performance | TC-NFR-03, 04, 05, 06, 07, 08, 09, 10, 11 |
| 13 | Edge cases | TC-EDG-01 to 18 |
| 14 | Order of events (one at a time, restore the lab after each) | TC-SEQ-01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24 |
| 15 | Cases that need a fresh appliance (restore the clean snapshot before each one) | TC-SEQ-09, TC-SEQ-17, then E2E-01 to 08 |

### What each case needs first

Cases not listed here need only a finished setup (TC-AUTH-07) and the lab described above.

| Case | Do these first | Why |
| --- | --- | --- |
| TC-AUTH-06 | TC-AUTH-05 | The setup window must already be open |
| TC-AUTH-07 | TC-AUTH-06 | It uses the same window, now with correct values |
| TC-AUTH-01 to 04, 09, 12 | TC-AUTH-07 | They need a finished setup and a known login |
| TC-AUTH-08 | TC-ACC-03 | It needs a user created with "Require password change at first sign-in" ticked |
| TC-ACC-03 | (pair with TC-AUTH-08) | Create users A and B here, then sign in as them in TC-AUTH-08 |
| TC-ACC-04, 05, 07, 09, 10 | TC-ACC-01 | They need the Staff user |
| TC-ACC-06 | TC-ACC-01, TC-AUTH-08 | After a reset the user sees the forced password change |
| TC-ACC-08 | TC-ROL-01 | Needs a role `qa-accounts` and a user with it, made the same way |
| TC-ROL-04 | TC-ROL-01, TC-ACC-01 | Needs the role `qa-view` and a user with it |
| TC-ROL-05, TC-DASH-08, TC-SS-04, TC-HIS-01, TC-PLG-07, TC-NCPA-08, TC-RPT-07, TC-LOG-05, TC-MNT-09 | TC-ACC-01 | They use the Staff user |
| TC-ROL-06, TC-SHL-10 | TC-ROL-01 | Each needs a role with one permission and a user with it, made the same way |
| TC-AUTH-11 | TC-ACC-01 | A registered user must exist |
| TC-SHL-09 | TC-AUTH-11 | It reads the password request made there |
| TC-SHL-06 | TC-ROL-04 | It uses the dashboard-only user |
| TC-SET-01 to 06 | TC-AUTH-07 | They need a Super Admin sign-in |
| TC-MNT-10, TC-SHL-08 | TC-SET-07 | They need working email |
| TC-DSC-02 to 05, 08, 09 | TC-DSC-01 | They need a scan that has found devices |
| TC-DSC-06 | TC-DSC-01 | Needs two networks with devices |
| TC-DSC-07 | TC-DSC-01, TC-PLG-03 | Needs a monitored port that you then close |
| TC-PLG-03 | TC-DSC-01 | Enabling a plugin needs discovered devices |
| TC-PLG-04, 05, 06 | TC-PLG-03 | They need an enabled plugin with services |
| TC-DI-01 to 04, 11 to 13, TC-TOP-01 to 06 | TC-DSC-01 | They need discovered devices |
| TC-DI-05 to 09, TC-DX-01 to 05 | TC-PLG-03 | They need monitored ports and the plugins for them |
| TC-DX-06, 07 | TC-DSC-01 | Need a device that answers SNMP |
| TC-NH-06 | TC-DX-07 | An interface must already be monitored |
| TC-DI-10 | TC-NCPA-04 | The NCPA port is protected only after a deployment |
| TC-DI-14, 15 | TC-DI-13 | They use a paused device |
| TC-DASH-02 | TC-DI-13 | The pause is made there |
| TC-DI-16 to 19 | TC-DSC-01 | Need identity review items (two records for one device) |
| TC-DASH-03 | TC-DSC-01, TC-PLG-03 | You need monitored services to break |
| TC-ACK-01, 03, 04, 06, 07, 08 | TC-DASH-03 | They need active alerts |
| TC-ACK-02 | TC-ROL-04, TC-DASH-03 | Needs the dashboard-only user and an active alert |
| TC-ACK-05 | TC-ACK-01 | An acknowledgement must exist to remove |
| TC-HIS-02 to 08 | TC-ACK-08, TC-SET-07 | Alert and notification events must exist |
| TC-SHL-07 | TC-DSC-02 | The bell needs a new notification, such as a finished scan |
| TC-MNT-03 to 06 | TC-MNT-02 | They reuse the same form |
| TC-MNT-07 | TC-MNT-02 | A window must exist to cancel |
| TC-MNT-08 | TC-MNT-07 | Same cancel flow, with Nagios stopped |
| TC-NCPA-02 | TC-DSC-01, TC-NCPA-01 | Needs a discovered Linux VM and `check_ncpa` enabled |
| TC-NCPA-03 | TC-NCPA-02 | The wizard is open from there |
| TC-NCPA-04 | TC-NCPA-03 | Needs a correct login |
| TC-NCPA-05, 06, 07, 10 | TC-NCPA-04 | They need a finished (or failed) deployment |
| TC-NCPA-09 | TC-NCPA-02 | Needs a trusted host key |
| TC-NCPA-11 | TC-NCPA-04, TC-NCPA-09 | Needs a deployed device with remote restart set |
| TC-DASH-09, TC-SS-05 | TC-NCPA-04 | Need NCPA data for about 3 days |
| TC-REM-01, 03, 04, 05 | TC-REM-02 | They need an action to look at or change |
| TC-REM-07, 08, 09 | TC-REM-02, TC-PLG-03 | They need an action and a service to break |
| TC-REM-06 | TC-REM-07, TC-REM-09 | The run log needs runs and skipped runs |
| TC-RPT-01 to 06 | TC-DASH-03, TC-ACK-08, TC-MNT-10 | A report needs incident data |
| TC-RPT-05 | TC-RPT-03, TC-RPT-04 | The exports must exist |
| TC-LOG-02 to 04 | TC-ACC-01, TC-DSC-02 | Log entries must exist |
| TC-DASH-06, TC-MNT-08, TC-SET-08 | everything above | They stop Nagios or break its config, so run them last and restore |
| TC-NFR-08, 09 | TC-DSC-01 | Need 10 and 15 monitored hosts |
| TC-NFR-10 | TC-DASH-03 | Needs a target to break |
| TC-EDG-01 to 18 | TC-ACC-01, TC-DSC-01, TC-DI-13 | They reuse the accounts, scans, and devices from earlier phases |

**Order-of-events cases (TC-SEQ) need first**

| Case | Do these first | Why |
| --- | --- | --- |
| TC-SEQ-01, 02, 06, 23 | TC-DASH-03, TC-PLG-03 | You need a monitored service to stop and start |
| TC-SEQ-03, 04, 05 | TC-MNT-02, TC-SET-07 | You need the window form and working email |
| TC-SEQ-06, 07 | TC-DI-13 | Pause and resume work |
| TC-SEQ-08, 24 | TC-DSC-02 | A scan can be started |
| TC-SEQ-09 | a fresh appliance | `check_http` disabled and no scan yet |
| TC-SEQ-10, 11 | TC-PLG-03, TC-DI-05 | A plugin is monitoring a port |
| TC-SEQ-12 | TC-ROL-04 | The role `qa-view` and its user exist |
| TC-SEQ-13 | TC-ROL-01 | Make a role with two permissions and a user |
| TC-SEQ-14, 15 | TC-ACC-01 | The Staff user exists |
| TC-SEQ-16 | TC-ACC-03 | A user with the forced change exists |
| TC-SEQ-17 | a fresh appliance | The bootstrap login is not used yet |
| TC-SEQ-18, 19, 20 | TC-REM-02, TC-PLG-03 | An action and a service to break |
| TC-SEQ-21 | TC-NCPA-04 | A deployed NCPA device |
| TC-SEQ-22 | TC-NCPA-09, TC-REM-10, TC-NCPA-04 | A deployed device with remote restart set |

