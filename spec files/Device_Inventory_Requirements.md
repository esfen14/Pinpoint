# Device Inventory Requirements — Ports, Monitoring State and Identity Review
**Detech-IT / 4D-G2 Capstone**
**Status:** Approved by the owner with the answers to O1–O3 (2026-10-06): a **Remove pin** action and route are included. Built (backend and drawer); the browser check in light and dark mode is still to do on the lab.
**Companion:** [`docs/plans/Device_Ports_UI_Plan.md`](../docs/plans/Device_Ports_UI_Plan.md) (how and in what order it is built)

---

## Purpose

This document defines what the **Ports** section of the Device Inventory page
shows and what an administrator can do in it. It is the requirement the plan asks
the owner to approve before any code is written (`AGENTS.md`; the same rule is
noted in `docs/plans/DHCP_Device_Identity_Plan.md` §11).

`Display_Requirements.md` covers the Dashboard and Network Health. This file covers
the Ports, Monitoring and manual Parent devices sections of Device Inventory, plus identity
review and manual merging (§14). The rest of that page (the host table, its filters, the
status drawer and acknowledgement) is unchanged.

As in `Display_Requirements.md`, layout, colour and component details are left to the
front-end developers. What is fixed here is the data shown, the grouping, the wording
of reasons and confirmations, who may do what, and the acceptance criteria in §10.

The goal: an administrator can open a device, see every port discovery found on it and
**why each one is or is not monitored**, and change that, without calling the API by
hand.

---

## Definitions

| Term | Meaning |
|---|---|
| **Port** | One TCP or UDP port discovery found open on a device, with the service name discovery decided for it. |
| **Monitored** | The port has a Nagios service, provided the plugin that checks it is enabled in Plugin Manager. |
| **Missing** | A monitored port not seen in the last several scans. It keeps its service, so Nagios reports it as CRITICAL. |
| **Suggested** | Found, but not monitored. It is waiting for a plugin or for an administrator. |
| **Ignored** | An administrator stopped monitoring it. It is hidden from "needs attention". |
| **Archived** | Gone for good (not seen for a long time). Shown only if present; no actions. |
| **Not used as intended** | nmap found a different service on the port than the Port → Service setting expects. Not monitored until an administrator acknowledges it. |
| **Held** | An administrator left the port Suggested on purpose, or an upgrade held it so it would not start being monitored. No plugin promotes a held port. |
| **Pinned** | An administrator fixed the port's service on this device. Scans never rename it. |
| **Check plugin** | The Plugin Manager plugin that checks the port's service (for example `check_ssh`). |

---

## Data Sources

Ports come from the device record (`Open_TCP_Services`, `Open_UDP_Services`); the
reason text is computed by the server. The route contract is in
`Backend_Modules_and_Routes.md` once built. This document defines *what* to show, not
API structure beyond §8.

---

## 1. Where it appears

- In the **device detail drawer** that opens from a row of the Device Inventory host
  table (the existing drawer, below the host state and services). It is not a new page,
  tab or drawer.
- It is shown only when the user has `system.hosts` **and** the host is a discovered
  device. A host that has no device record (for example the monitoring server itself,
  `localhost`) shows no Ports section.
- It is read-only unless the user has `system.hosts.edit` (§5), or the device is
  Retired or Merged (§7).
- Below the Ports section the drawer shows an **Interfaces** section for a device with SNMP
  monitored (nothing for other devices): the interfaces the device reports, a Monitor choice
  for each and a Refresh button, with the same `system.hosts` / `system.hosts.edit` rules.
- Below the Interfaces section the drawer shows an **SNMP** section for a device with an SNMP
  port monitored: the SNMP version (Default, 1, 2c, 3), the community, and for version 3 the
  security level, user, and the authentication and privacy protocols and passwords. Passwords
  are never shown after saving. The section offers Save, Test and Reset to defaults, with the
  same `system.hosts` / `system.hosts.edit` rules (Test needs edit). Routes:
  [`Backend_Modules_and_Routes.md`](Backend_Modules_and_Routes.md) (`device_plugin_variables.py`).
  It is a separate section and does not change the Ports requirements; its behavior is in
  [`Display_Requirements.md`](Display_Requirements.md) §2.5.1 and
  [`Backend_Modules_and_Routes.md`](Backend_Modules_and_Routes.md) (`device_interfaces.py`).

---

## 2. What each port shows

One row per port:

| Item | Notes |
|---|---|
| Protocol and port | for example `tcp/22` |
| Service | the service name; when flagged, "found {service}, expected {expected}" |
| State badge | Monitored, Missing ("not seen lately"), Suggested, Ignored, Archived |
| How it was identified | Fingerprint (nmap probed it), Port rule (the Port → Service setting), Pinned (an administrator), Guess (only from the port number) |
| Check plugin | for example `check_ssh`; "none" when no plugin checks it |
| Flags | "Not used as intended", "Held" |
| Reason | the sentence from §4, for Suggested and Ignored ports, a Missing port and a Monitored port whose plugin is off, and a Monitored port with no service |
| Last seen | relative time, with the exact time on hover |

---

## 3. Grouping and order

Groups are shown in this order, each with a count in its header. A group with no ports
is not shown.

1. **Needs attention**: Suggested ports whose reason is *Not used as intended* or *Held*.
2. **Monitored**: Monitored, then Missing.
3. **Suggested**: the remaining Suggested ports.
4. **Stopped**: Ignored ports.
5. **Archived**: collapsed by default.

Inside a group, ports are ordered by protocol (TCP, then UDP) and port number.

---

## 4. Reasons

Shown for **Suggested** and **Ignored** ports, plus the three Missing and Monitored cases at the end of the table. Exactly one applies; the first match wins.

| Order | Condition | Text |
|---|---|---|
| 1 | Not used as intended, not yet acknowledged | "Not used as intended: expected {expected}, found {service}. Not monitored until acknowledged." |
| 2 | Held | "Held back: left Suggested on purpose, or at an upgrade. No plugin will monitor it until you do." |
| 3 | Identified only by a guess | "Only guessed from the port number, so it is not monitored automatically." |
| 4 | UDP service no plugin can check | "No plugin can check this UDP service." |
| 5 | Its check plugin is not enabled | "{check_plugin} is not enabled in Plugin Manager." |
| 6 | Device is excluded from scanning | "This device is excluded from scanning." |
| 7 | Ignored | "Monitoring stopped by an administrator." |
| 8 | Missing | "Not seen lately: no recent scan found this port. Its service stays in Nagios until the port is archived." |
| 9 | Monitored, but its check plugin is not enabled (the port keeps its frozen plugin) | "{check_plugin} is not enabled in Plugin Manager, so nothing is checking this port." |
| 10 | Monitored, its plugin is enabled, but no Applied Nagios service exists for the port (a configuration problem, for example a rejected config) | "Marked Monitored, but no Nagios service exists for it. This is a configuration problem: check the activity log for a rejected configuration, then run discovery again." |

A Suggested port that matches none of these is about to be monitored by the next
reconcile; the reason reads "Will be monitored by the next update."

---

## 5. Actions

Shown only with `system.hosts.edit`. Without it the section is view-only and says so
once ("You can view ports but not change them.").

| Port | Action | Effect | Confirmation |
|---|---|---|---|
| Suggested, *Not used as intended* | **Acknowledge and monitor** | Accepts the service nmap found and monitors it if its plugin is enabled | none |
| Suggested (any reason except *Not used as intended*) | **Monitor** | Monitors the port (releases a hold, accepts a flag). If its plugin is not enabled it will produce a service only once the plugin is, and the row says so | none |
| Suggested, reason *plugin not enabled* | link **Enable {check_plugin}** | Opens Plugin Manager | none |
| Suggested | **Ignore** | Hides it from "needs attention"; no service | "Ignore {protocol}/{port} on {host}? It will not be monitored." |
| Monitored or Missing | **Stop monitoring** | Becomes Ignored; its Nagios service is removed | "Stop monitoring {service} on {host}? The Nagios service for this port is removed; its history is kept." |
| Monitored or Missing | **Leave suggested** | Becomes Suggested and **held**; its service is removed and no plugin will monitor it again until an administrator does | "Leave {protocol}/{port} suggested? The Nagios service for this port is removed, and no plugin will monitor it again until you do." |
| Ignored | **Resume** | Becomes Monitored again, checked by the plugin for its service | none |
| Any except Archived | **Set service…** | See §6 | see §6 |
| Pinned, any except Archived | **Remove pin** | Lets scans decide the service again (§6) | "Let scans decide the service for {protocol}/{port} on {host} again?" plus the sentence for its state from §6 |

For a *Not used as intended* port, **Acknowledge and monitor** is shown instead of Monitor, because both would do the same thing.

### Check options (issue #131)

A **Monitored or Missing** port whose service is `http`, `https`, `pop3`, `imap`, `pop3s` or `imaps`
also has a **Check options** button, shown to every user who can see the section (it is not one of the
actions above and does not need `system.hosts.edit` to open). It opens a dialog titled
"Check options: {service} on {host}", loaded from `GET /api/system/hosts/<id>/plugin-variables/<service>`:

- `http` and `https`: **Expected text**, **Expected status codes** (for example `200,301`), **Virtual host**
  and **Request method** (Default, GET, HEAD, POST, PUT, DELETE, OPTIONS, PATCH).
- `pop3`, `pop3s`, `imap`, `imaps`: **Expected greeting**, with the default (`+OK` or `* OK`) shown.
- An empty field means the default check. The options belong to the device and the service, so they
  apply to every port of that service on the device; the dialog says so.
- **Save** is checked in the browser as the server checks it (forbidden characters, status codes 100 to 599,
  host name, method) and shows the message instead of sending; the server's 400 and 422 messages are shown as
  they are. **Reset to defaults** removes the override (disabled while nothing is saved). Saving and resetting
  apply the Nagios config, and the saved values are shown again when the dialog is reopened or the page reloaded.
- Without `system.hosts.edit`, or for a retired or merged device, the fields are disabled, Save and Reset are
  not shown, the dialog says "You can view the options but not change them." and the button reads **Close**.
- Loading, load error with **Retry**, saving and success states are shown. Authentication headers and passwords are not offered.
- User guide: [Application checks](../docs/manuals/Application_Checks.md).

Not available:

- **The NCPA port of a device with a deployed agent**: no Stop, Ignore, Leave suggested
  or archive; the row reads "Managed by NCPA deployment". Set service and Remove pin are not offered.
- **Archived ports**: no actions.

---

## 6. Set service (pin)

"Set service…" fixes what the port is **on this device**: "always treat this port as X".

**Dialog** titled "Set service for {protocol}/{port} on {host}":

- A text field for the service name with suggestions of the services Pinpoint knows
  (for example ssh, http, https, snmp, ncpa, ftp, smtp, mysql, dns, ntp). Any other
  valid name is allowed.
- Validation: lowercase letters, digits, `-` or `_`; starts with a letter or digit;
  at most 32 characters. The same rule as the Port → Service setting.
- A live "Checked by" line under the field:
  - a known service: its check plugin (for example "check_http");
  - any other name on TCP: "check_tcp (generic TCP check)";
  - any other name on UDP: "Skipped: no check exists for this UDP service".
- Text always shown: "Scans will no longer change this port's service on this device.
  You can change it again or use Remove pin."
- Extra text when the port is Monitored or Missing: "The Nagios service for this port will be renamed
  (for example http-8080-tcp becomes ssh-8080-tcp). Its history stays under the old name."
- Buttons **Cancel** and **Save**; Save is disabled while the name is invalid or unchanged.

**Effect:** the service name is saved and marked Pinned. A port that is already monitored
is re-checked with the new service's plugin. A Suggested port stays Suggested (and keeps
its hold); pinning never promotes. Pinning clears a "Not used as intended" flag on that
port, because the administrator has decided.

### Remove pin

Shown on a port whose service is Pinned. It undoes "Set service…" and lets scans decide the
service again.

- A **Suggested, Ignored or Archived** port goes back to the service the last scan saw and
  follows scans from now on. Confirmation sentence: "The service goes back to what the last
  scan saw."
- A **Monitored or Missing** port keeps its service and its Nagios service unchanged.
  Confirmation sentence: "The Nagios service for this port is not changed. If a later scan sees a different
  service, the current one is kept and a review item is recorded."
- A hold is never changed by removing a pin, and neither is the port's state.
- It is refused for a port that is not pinned ("This port is not pinned.").

---

## 7. After a change, and states

**After any action:**

- The ports reload from the server; the server's state is what is shown.
- If the change was saved but Nagios was not updated, show the server's message:
  "The change was saved but Nagios was not updated: {message}".
- A refused change (for example the protected NCPA port) shows the server's message and
  changes nothing.
- While an action runs, its button is disabled.

**States of the section:**

| State | Shown |
|---|---|
| Loading | a loading indicator in the section |
| Error | the error text with **Retry** |
| No ports | "No ports discovered yet. Run a scan from Network Discovery." |
| View-only | the note in §5 |
| Retired or Merged device | the list is read-only and says "This device is retired/merged." |
| Plugin Manager link | "Enable {check_plugin}" appears only for users who can view Plugin Manager (`plugin.view`) |

The Plugin Manager enable dialog's "N identified port(s) are held back" gets the added
line "Monitor them from each device's Ports list."

---

## 8. Data the screen needs

(Contract details go in `Backend_Modules_and_Routes.md` when built.)

- **A read route for a device's ports** (`system.hosts`): per port the protocol, number,
  service, observed service, state, source, how identified, check plugin and whether it
  is enabled, expected service and acknowledgement, held flag, first/last seen, missed
  scans and the reason code and text of §4; counts per state; and the list of known
  service names with their check plugin for §6.
- **`device_id` on the Device Inventory host list and host detail**, empty for hosts
  without a device record.
- The existing port-edit route for every action. It gains one option, `unpin`, for Remove pin (§6); nothing else it accepts changes.

---

## 9. Out of scope

`SERVICE_CHANGED` resolution; standalone device confidence badges, retire and
static/DHCP marking; bulk actions;
pagination or a filter box for ports; any change to the Port → Service setting or to
Plugin Manager beyond the one hint line in §7.

---

## 10. Acceptance criteria

1. The Ports section appears in the device drawer for a discovered device when the user
   has `system.hosts`, and not for a host with no device record.
2. Ports are grouped and ordered as in §3, with counts; empty groups are not shown.
3. Each row shows the items in §2.
4. Every reason in §4 is produced for the right port and the first match wins (a port
   that is both held and flagged reads "Not used as intended").
5. Without `system.hosts.edit` no action is shown and the view-only note appears.
6. Each action in §5 sends the matching request and then reloads the list.
7. Stop, Ignore and Leave suggested ask for confirmation with the §5 wording; the
   others do not.
8. Cancelling a confirmation changes nothing.
9. The NCPA port of a deployed agent offers no destructive action and shows "Managed by
   NCPA deployment".
10. Archived ports are collapsed and have no actions.
11. Acknowledge and monitor on a flagged port monitors it (when its plugin is enabled) and
    clears the flag; Monitor on a held port clears the hold.
12. Leave suggested holds the port: after the next scan and after its plugin is disabled
    and enabled again it is still Suggested.
13. Set service: the field validates as §6; the "Checked by" line is correct for a known
    service, an unknown TCP name and an unknown UDP name; the warning texts appear; Save
    is disabled for an invalid or unchanged name.
14. Pinning a monitored port renames its service; pinning a Suggested port does not
    monitor it; a scan does not undo a pin.
15. A saved-but-not-applied change shows the server's message; a refused change shows the
    server's message and changes nothing.
16. Loading, error with Retry, no-ports, view-only and retired/merged states are shown as
    in §7.
17. "Enable {check_plugin}" appears only for users with `plugin.view`.
18. The Plugin Manager enable dialog shows the extra hint when ports are held.
19. Light and dark mode are both usable and the section works at a narrow width.
20. No existing Device Inventory behaviour (host table, filters, acknowledgement,
    services list) changes.
21. Remove pin is shown only on pinned ports (not Archived, not the protected NCPA port) and asks
    for confirmation with the §6 wording for the port's state.
22. Removing a pin on a Suggested port returns it to the last scanned service; on a Monitored
    port the Nagios service is unchanged; the port's state and hold are never changed by it.
23. Remove pin on a port that is not pinned is refused with "This port is not pinned."; a scan
    after the pin is removed may change the service again.
24. Check options (§5) appears only on a Monitored or Missing http, https, pop3, imap, pop3s or imaps
    port; a permitted user can save and reset the options and sees them after reopening; invalid values are
    blocked with a message and server errors are shown; without `system.hosts.edit` the options are read-only.

---

## 12. Monitoring state

Companion plan: [`docs/plans/Device_Monitoring_State_Plan.md`](../docs/plans/Device_Monitoring_State_Plan.md).
Decisions Q1–Q3 of that plan (owner, 2026-10-07): pause keeps the device's ports and
history and scans still track it; a host row stays visible with a chip and a filter;
every non-Active case has a label.

### 12.1 One label per device

Derived by the server, first match wins:

| Label | When |
|---|---|
| Merged | `Device_State` is MERGED |
| Retired | `Device_State` is RETIRED |
| Paused | `Include_Device_In_Scanning` is false |
| Address unknown | `Device_State` is ADDRESS_UNKNOWN |
| Missing | `Device_State` is MISSING |
| Monitored | otherwise |

A host with no device record (for example `localhost`) has no label: no chip, "—" in the
table, and it counts as monitored for the filter.

Reasons (shown in the drawer, and as the chip tooltip in the table):

| Label | Reason |
|---|---|
| Monitored | "Nagios is checking this device." |
| Missing | "Not seen in the last few scans. It is still being checked, so Nagios reports it as down." |
| Address unknown | "Its address now belongs to another device. Checks are off until it is found again." |
| Paused | "An administrator paused monitoring. Scans still track the device, but Nagios does not check it. The status shown is the last one Nagios reported." |
| Retired | "Retired: Nagios no longer checks it. The status shown is the last one Nagios reported." |
| Merged | "Merged into another device: Nagios no longer checks it. The status shown is the last one Nagios reported." |

### 12.2 Where it appears

- **Table:** a Monitoring column with the chip. Paused, Retired and Merged rows add "last
  known status" under the chip, because they are out of the Nagios config and their
  snapshot is stale (Q2 point: the row stays visible but must not be read as live).
- **Filter:** the table's filter menu has a Monitoring group: All, Monitored, Not
  monitored (every label except Monitored), and one option per other label. It combines
  with the state filter, the search and paging. The table opens on **Monitored** (owner,
  2026-10-07); the other hosts are one filter choice away.
- **Summary cards:** Total Hosts, Up and Down / Unreachable count Monitored hosts only
  (the same set the table opens on), so a paused device never counts as up. They reload
  after a pause or resume.
- **Dashboard and Network Health:** a host whose device is Paused, Retired or Merged, and
  its services, are left out of every count, the active-alerts feed and the
  Online / Offline Devices cards (`Display_Requirements.md` §1.2).
- **Drawer:** a Monitoring section (host view, not the service view) for a host with a
  device record, showing the chip, the reason and the action below.

### 12.3 Pause and resume

- Shown only with `system.hosts.edit`, and only for a device that is not Retired or
  Merged. Without the permission the chip and reason are still shown.
- **Pause monitoring** confirms with: "Pause monitoring of {host}? Nagios will stop
  checking the device and all its services. Scans keep tracking it, and you can resume at
  any time." **Resume monitoring** confirms with: "Resume monitoring of {host}? Nagios
  will start checking the device and its services again."
- Pause only clears `Include_Device_In_Scanning`. The device keeps its ports and history
  and scans still follow its address, hostname and identifiers. A scan, a missed-scan
  count or a lifecycle change never turns a pause off; only Resume does.
- Resume puts the device back in the Nagios config in the state it has then (monitored,
  missing or address unknown). A Retired device comes back only by being found again.
- Ports of a paused device: the port-edit route still works and takes effect on resume;
  no port is promoted to monitored while the device is paused.
- A saved-but-not-applied change shows "The change was saved but Nagios was not updated:
  {message}", as for ports. A refused change shows the server's message.
- After a change the drawer and the table load again.

### 12.4 Acceptance criteria

24. The label for every state and combination follows §12.1 (paused beats missing and
    address unknown; retired and merged beat paused).
25. The host list and detail carry `monitoring_state` and `monitored`, and both are null for
    a host with no device record.
26. The Monitoring filter returns the hosts of the chosen label; "Not monitored" returns
    every host with a label other than Monitored; "Monitored" includes hosts with no device
    record; an unknown value is refused with 400.
27. Pause removes the device from the generated Nagios config; Resume puts it back.
28. A scan that moves a paused device, or lets it go missing, leaves it paused.
29. Pause on a Retired or Merged device, a second Pause, and Resume on a device that is not
    paused are each refused with 400 and change nothing.
30. Pause and Resume write a user-log entry and need `system.hosts.edit`.
31. Cancelling the confirmation changes nothing.
32. A Paused, Retired or Merged row shows "last known status".
33. The table opens on the Monitored filter, and its summary cards count Monitored hosts
    only.
34. A paused (or retired or merged) device and its services are not counted as hosts,
    services, online devices or active alerts on the Dashboard and Network Health pages;
    resuming it counts it again.
35. Removing a network from discovery settings and scanning remaining networks leaves
    devices in the unscanned network untouched (or missing) and does not mark existing
    devices in the scanned network as Address Unknown (#67).

---

## 11. Decisions on the open points (owner, 2026-10-06)

| # | Point | Decision |
|---|---|---|
| O1 | A pin cannot be removed | **Add an unpin route.** Remove pin is included (§5, §6, criteria 21–23) |
| O2 | "Ignore" (Suggested port) and "Stop monitoring" (Monitored port) both end Ignored | **Keep both labels** |
| O3 | A held Suggested port can still be pinned and stays held | **Keep** |


## 13. Host email alert recipients

In the host detail drawer, a discovered device shows an **Email alert recipients**
section only with `system.hosts.alerts` (separate from `account.alerts` and
`system.hosts.edit`). It applies to the host and all its generated services, with
one checkbox per user (name, email and eligibility). Only Active users with
email alerts on receive notifications. Ineligible choices may remain selected
and are labelled; no selections, or no eligible selections, uses the default
recipients (all globally eligible users), with explanatory text. If no globally
eligible users exist, no email recipients are generated.

Save is enabled for changed choices and disabled during a request. Successful
save shows confirmation and the server's selections. Failed apply keeps the old
saved selection, displays the server error and leaves the proposed choices
available for retry. Loading, load error with Retry, no accounts and read-only
retired/merged states must be present. Hosts without a discovered-device record
and service-detail views do not show the editor. Choices survive address/hostname
changes and rescans; merges combine selections without duplicates; retiring
removes that device's assignments. Pause preserves them.


## 13. Manual parent devices and topology

The host detail drawer shows **Parent devices** for every discovered device,
including a device with no configured parents. Readers with Inventory access can
see the choices and monitoring warnings; only `system.hosts.edit` may change them.
A host without a discovery record has no parent editor. Retired/merged devices are
read-only. The same editor appears in the Topology selected-device panel.

An operator searches other eligible inventory devices by name/address and selects
zero or more parents using checkboxes, then **Save parents**. **Clear all** clears
the draft; saving an empty set explicitly means no parents. A gateway suggestion is
advisory and never selected automatically. A selected paused/address-unknown parent
warns that Nagios omits it. The server refuses self-links, duplicate IDs, missing/
retired/merged parents and cycles through any parent path, showing its message and
retaining the draft on failure. Loading, retry, empty, saving, failure and success
states are visible. Applying failure rolls back the complete edit.

Topology is supported at `/topology` with Inventory's viewing permission
`system.network_health`. It shows all discovered devices and hosts exposed by
Inventory, including unchecked devices, paused devices and roots. Relationships
are configured reachability parents, not physical cables. The automatic hierarchy
supports multiple parents; manual layout changes are disabled. Device details and
manual parent relationships are the complete panel scope. Interface details,
interface-to-parent mapping, traffic/utilization charts and new telemetry collection
are excluded. Existing Inventory interfaces and Network Health bandwidth keep
their own established behavior.

## 14. Device identity review and manual merging

The **Needs Review (count)** section appears separately from the host table for
users with `system.discover`, including when empty. It loads unresolved discovery
reviews, counting only conflicts, identity changes, IP reuse, duplicate identities
and static-address moves. `SERVICE_CHANGED` is excluded. Host search, monitoring
filters and pagination never restrict these reviews.

Each row shows a plain-language issue and reason, involved records' names and IPs,
the detected time using display preferences, and **Review**. Loading, error with
Retry, and empty ("No device identity issues need review.") states are explicit.
A participating device's information drawer shows **This device needs identity
review**, whose Review action opens the same comparison flow.

Review opens a comparison drawer with the reason and candidate records side by
side (stacked on narrow screens). Each shows stable device ID, Nagios host name,
display name, current IP, monitoring state, identity confidence and available
identifiers. Missing fields/evidence are labelled. Identity details require
`system.hosts` and load when the comparison opens. Address history requires the
same permission and loads only after **Load address history**, with loading,
retryable error and no-history states. Opening, closing and cancellation perform
no persistent write and never resolve a review.

Merging also requires `system.hosts.edit`. Neither direction is preselected: the
administrator chooses **Device record to keep** (target) and **Duplicate record
to merge** (source). Two distinct records are required. Merged sources and retired
or merged targets are excluded. Search discovered devices by name, IP or stable
ID to add records when the candidates are insufficient; this uses application
discovery records, including those outside the default Monitored filter, without
requiring any Nagios snapshot. Up to 20 matches are shown, with a refinement hint
when more match. Lookup errors allow repeating Search.

Guidance explains that merging is appropriate only after verifying both records
represent the same physical device; similar names and matching IPs are not proof.
Keep the record with the intended monitoring settings and current address. An IP
move discovery confidently recognizes continues updating the existing record
without requiring a merge; matching rules are unchanged.

**Review merge** opens confirmation containing both IDs, names and IPs. It says
which record survives, that the target retains its current address, that the
source becomes Merged and leaves monitoring, that target records take precedence
where settings conflict, that historical monitoring snapshots remain under their
original host names and are not transferred, and that no undo action is provided.
Submission and dismissal are disabled while saving; a second submission is blocked.
Evidence responses refresh the candidate summaries used by both selectors and
confirmation, including the current name, address and lifecycle state. The
existing merge route validates stale records and returns errors without
losing the editable choices. A successful merge refreshes reviews, counts and
inventory without a page reload. `config_ok: false` is shown explicitly as
**Merge saved. Nagios configuration warning: {config_message}**; it is never
presented as a failed merge or a reason to retry the merge.

The comparison and confirmation support keyboard focus containment, Escape
(except while saving), focus restoration, and both display themes. Identity
rules, merge validation, Nagios config validation/application, snapshot ownership,
retire controls, static/DHCP editing, port mismatch resolution and undo remain
outside this change.
