# Frontend Modules and Routes

**Last verified against the repository:** 2026-10-08

## Application shell

The client is a React/TypeScript Vite application. `src/App.tsx` owns browser
routes. `AdminLayout` supplies the authenticated shell, and `Sidebar`, `Header`,
`PageAccessGuard`, `SessionTimeoutWatcher`, and `MaintenanceBanner` implement
cross-page behavior.

All API calls are same-origin and send the Flask session cookie. Shared JSON
requests use `src/lib/api.ts`; Plugin Manager wrappers live in
`src/lib/pluginApi.ts`.

## Browser route catalog

| Browser path | Page | Required client permission | Current data source/status |
|---|---|---|---|
| `/login` | `LoginPage` | Public | Connected to `/api/user/login`. "Forgot Password?" opens a dialog that posts the email to `/api/user/forgot-password`; an administrator is notified and sets the password |
| `/dashboard` | `DashboardPage` | `system.dashboard` | Connected to dashboard, trends, service, and acknowledgement APIs |
| `/network-health` | `NetworkHealthPage` | `system.network_health` | Connected to summary and trends APIs; detailed host/service UI is supplied elsewhere |
| `/device-inventory` | `DeviceInventoryPage` | `system.network_health` | Connected to the latest-host endpoints and acknowledgement API. The host table has an IP Address column (`—` for a host with no discovered device). The host drawer also shows a Ports section (see `Device_Inventory_Requirements.md`) for users with `system.hosts` when the host has a `device_id`; actions need `system.hosts.edit`. The host table has a Monitoring column and filter, and the drawer a Monitoring section with Pause / Resume (`Device_Inventory_Requirements.md` §12) |
| `/history` | `HistoryPage` | `system.history` | Connected to the alert and notification history list and detail routes (`/api/system/history/...`); sidebar entry "History". Audited against `Alerts_Notifications_History_Requirements.md` in `docs/test-runs/2026-10-14-issue-133-history-audit/AUDIT.md`; supported sorting controls are present and cross-tab links now use Nagios `event_id` locators to expand the exact row beyond the default 24h range (#143); remaining history gaps are tracked in #142 and #144 |
| `/topology` | `TopologyPage` | `system.network_health` | Real backend inventory and configured parent edges from `/api/system/topology`; automatic hierarchy including disconnected devices and shared children, read-only positions, device/relationship selection panels. Parent editing uses `system.hosts.edit` |
| `/system-status` | `SystemStatusPage` | `system.network_health` | The **System Status** page (sidebar label “System Status”): a service-status table with OK / Warning / Unknown / Critical counts, search, state filter, sort, paging and acknowledgement. It is a supported page. Topology is a separate supported page. |
| `/plugins` | `PluginsPage` | `plugin.view` | Connected to Plugin Manager inventory (category tabs All / Network Services / Device Availability / Network Protocols / Servers / Application / Other, filtered by the `group` query parameter so paging stays per tab; a Monitoring column and a banner while no plugin is enabled), plugin details with an enable confirmation that previews what will be monitored, the plugin's monitored services with live status and per-device stop/resume, scanning, and mutation APIs. There is no Currently Running tab (the tabs are categories only) and devices are never picked by hand |
| `/ncpa-deployment` | `NcpaDeploymentPage` | `system.deploy.ncpa` | Warns, through `useNcpaPluginState`, when `check_ncpa` is not enabled in Plugin Manager (the agent's checks are monitored only while it is). Connected to the NCPA deployment routes: device list, deploy wizard (host-key trust, login checks, start), live run banner, Deployment History tab and run review drawer (`?tab=history&run=<id>`) |
| `/maintenance` | `MaintenancePage` | `maintenance.manage` | **Maintenance** (sidebar). Lists maintenance windows (devices, next occurrence, repeats, status, reason) with create, edit and a two-step cancel, through `lib/maintenanceApi.ts` and `types/maintenance.ts`. Times are typed and shown in the Time Zone setting (`useDisplayTime`, `utils/maintenanceTime.ts`) and sent as UTC; the form checks what the server checks. A failed or retrying occurrence is shown with its reason, and a `nagios_synced: false` result is shown as a notice. A note explains that a window silences alerts and links to Settings → System, where the Maintenance Mode switch and the global banner say it only pauses PinPoint's jobs and link back here |
| `/ncpa-deployment` | `NcpaDeploymentPage` | `system.deploy.ncpa` | Warns, through `useNcpaPluginState`, when `check_ncpa` is not enabled in Plugin Manager (the agent's checks are monitored only while it is). Connected to the NCPA deployment routes: device list, deploy wizard (host-key trust, login checks, start), live run banner, Deployment History tab and run review drawer (`?tab=history&run=<id>`). Trusted failed and deployed devices have a Clean up dialog: it accepts ephemeral SSH credentials, optionally removes the deployment account after artifact removal, shows each cleanup step and refreshes the list; fields clear after every request. |
| `/remediation` | `RemediationPage` | `remediation.view` | Connected to `/api/system/remediation/...`; sidebar entry "Remediation". Above both tabs a status panel shows the consumer's health (last check-in, events waiting, runs, limits hit, skipped and dropped in 24 hours, refreshed every 15 seconds), a red banner when the consumer has stopped checking in, and the automatic recovery switch (the kill switch): changing it asks for confirmation in both directions, needs `remediation.manage` (view-only users see it disabled) and its saved state shows after a reload. An Actions tab (banner "Actions run automatically when a service reaches a hard failure", an enable switch per action, an add/edit form built from the action types with server messages shown against the right field, delete with confirmation; with only `remediation.view` the list is read-only) and a Run log tab (filters for action, outcome, host and dates, pagination, skipped runs show their reason (including kill switch, maintenance, downtime and acknowledged), a drawer with the redacted output). Changes need `remediation.manage`; 409 offers a reload and 422 shows the Nagios message |
| `/reports` | `ReportsPage` | `system.report` | Six connected views: Host Availability, Network Services, Hosts by OS, Device Services, Alerts and Notifications; see Reports below |
| `/system-logs` | `SystemLogsPage` | `system.logs` | Connected to five audit log categories and a bounded Nagios log tab |
| `/accounts` | `ManageAccountsPage` | `account.view` | Connected to account/role APIs. The table shows each user's Email Alerts (On/Off); the add and edit forms show a "Send this user email alerts" checkbox only with `account.alerts`, and a failed Nagios apply is shown as a notice. The first account is marked by the account API as `is_super_admin`; its edit form keeps Status Active, disables the status selector, explains that the bootstrap administrator must retain account/role administration, and disables role options whose `preserves_bootstrap_admin_access` value is false |
| `/manage-roles` | `ManageRolesPage` | `role.view` | Connected to role and permission APIs. The built-in `Super Admin` role shows every permission as read-only with an explanation, and its name cannot be edited. The bootstrap administrator's assigned role is marked as locked; its edit form disables the seven account/role administration permission controls and role deactivation, even when assigned to a different role |
| `/settings` | `SettingsPage` | Any logged-in user; tabs are separately gated | Connected to system settings and user preferences. Tabs: General Settings, Security, System, Network Discovery, Plugins and Email; the System tab includes the notification-policy card |
| `/` | Redirect | — | Redirects to `/login` |
| unmatched path | Redirect | — | Redirects to `/login` |

## Page access rules

`src/lib/pageAccess.ts` is the client route-to-permission map. The sidebar hides
pages the user cannot access, and `PageAccessGuard` prevents direct URL access.
This is usability protection only; backend permission checks remain mandatory.

The Settings page is generally available to logged-in users. Its Security,
System, Network Discovery, Plugins and Email tabs require `settings.security`,
`settings.system`, `settings.discovery`, `settings.plugins` and `settings.email`, respectively. General's `notifications` toggle only shows/hides the header bell; it does not stop email or change Nagios' `enable_notifications`. The System tab's `NotificationPolicySettings` card is visible only with `settings.system` and reads/writes `/api/system/notification-policy` through `lib/notificationPolicyApi.ts` and `types/notificationPolicy.ts`. Quiet-hour weekdays and 24-hour times are interpreted in Nagios server local time. The card validates time format, order, overlap, options and interval; 409 offers a reload and 400/422 display the server's message.

`AdminLayout` replaces the whole shell with a blocking window while the account
is flagged: `FirstRunSetup` when `needsSetup` (bootstrap administrator: current
password, new email, new password with confirmation; cannot be skipped, only
signed out of; a failed Nagios apply is shown as a warning after the account is
saved) and otherwise `ForcePasswordChange` when `mustChangePassword`. The Add
User form has a "Require password change at first sign-in" checkbox, ticked by
default, sent as `require_password_change`.

Manage Accounts → Add User uses the first loaded active role as its default,
including when the dialog was opened before role options arrived. Rendering,
validation and submission use the same role ID; explicit role selections are
preserved. Save remains disabled without an available role, with guidance to
wait for loading or check active roles. Matching passwords must meet the active
password policy. Successful creation closes the dialog and refreshes the list;
a rejected save retains the draft and displays the server message. Further
accounts can be created without reloading the page.

When adding a page:

1. Add the page component under `src/pages/`.
2. Add its route in `App.tsx`.
3. Add the sidebar entry if it is navigable.
4. Add the permission mapping in `pageAccess.ts`.
5. Add or update route/access tests.
6. Update this specification and `Implementation_Status.md`.

## Component ownership

| Path | Responsibility |
|---|---|
| `components/dashboard/` | Dashboard metrics, resource views, alerts, charts, and outage presentation; `ForecastList` ("Running out soon": disk and memory metrics on course to reach a warning or critical level, each with the estimated date, "in about N days" and its basis such as "based on the last 3 days"; loading, error, empty and "not enough data yet" states; a "How is this calculated?" note on the method and limits; data from `hooks/useForecasts.ts`, `types/forecast.ts` and `GET /api/system/forecast`, refreshed every 5 minutes) |
| `components/network-health/` | Trend/metric cards, network health summaries, insight panels, and graph modal; `BandwidthCard` / `BandwidthChart` (Interface Bandwidth: device and interface selectors, a time range of 1 hour to 7 days, in and out lines whose unit scales from bit/s to Tbit/s, loading / error / no-device / no-interface / insufficient-data / no-data states and help text; loads its own data from `lib/bandwidthApi.ts`, so a failure never blanks the rest of the page, and reports the reading on screen to the page (`onReading`) for the side Bandwidth widget; the choosers are `components/shared/DropdownSelect.tsx`, the button-and-list dropdown that matches `TimeRangeSelect`; `TimeRangeSelect` takes an optional `options` list so the card can leave out the 5-minute range) |
| `components/device-inventory/` | Host/device table; the host detail drawer (all detail drawers, here and in Plugin Manager, NCPA deployment and Remediation, are built on `components/shared/DrawerShell.tsx`: sticky header, sections separated by divider lines, 15px text, 13px captions, 17px section headings); `DevicePortsSection` (a device's ports in groups with the reason each is or is not monitored, and the Monitor / Acknowledge / Ignore / Stop / Leave suggested / Resume / Set service / Remove pin actions with confirmations), `SetServiceDialog`, `CheckOptionsDialog` with `checkOptionsForm.ts` (the "Check options" action on a monitored HTTP, HTTPS, POP3, IMAP, POP3S or IMAPS port: expected text, status codes, virtual host and request method, or the expected greeting, saved per device and service through `lib/devicePluginVariablesApi.ts`; checked before sending, the server's 400 and 422 messages shown, Reset to defaults, read-only without `system.hosts.edit`), and `devicePortsLogic.ts` (grouping, which actions apply, wording); `DeviceInterfacesSection` (the drawer's Interfaces section for SNMP devices: name, index, speed and status of each interface, a Monitor checkbox per interface, and Refresh to read the list from the device; hidden for a device without SNMP; editing needs `system.hosts.edit`; data from `lib/bandwidthApi.ts`, types in `types/bandwidth.ts`); `DeviceSnmpSection` (the drawer's SNMP section for a device with an SNMP port: version Default / 1 / 2c / 3, the community, and for v3 the security level, user, authentication and privacy protocols and passwords; a saved password is only shown as "Saved", is kept when its box is blank and can be removed; required fields per level are checked before sending; Save, Test and Reset to defaults; viewing needs `system.hosts`, changing and Test need `system.hosts.edit`; rules in `snmpForm.ts`, data from `lib/devicePluginVariablesApi.ts`, types in `types/devicePluginVariables.ts`); `DeviceMonitoringSection` (the monitoring label, its reason and Pause / Resume with confirmation) and `monitoringState.ts` (labels, reasons, styles, filter options). Data comes from `lib/devicePortsApi.ts`, `lib/deviceMonitoringApi.ts` and `hooks/useDevicePorts.ts` |
| `components/network-health/` | Trend/metric cards, network health summaries, insight panels, and graph modal |
| `components/device-inventory/` | Host/device table; the host detail drawer; `DevicePortsSection` (a device's ports in groups with the reason each is or is not monitored, and the Monitor / Acknowledge / Ignore / Stop / Leave suggested / Resume / Set service / Remove pin actions with confirmations), `SetServiceDialog`, `CheckOptionsDialog` with `checkOptionsForm.ts` (the "Check options" action on a monitored HTTP, HTTPS, POP3, IMAP, POP3S or IMAPS port: expected text, status codes, virtual host and request method, or the expected greeting, saved per device and service through `lib/devicePluginVariablesApi.ts`; checked before sending, the server's 400 and 422 messages shown, Reset to defaults, read-only without `system.hosts.edit`), and `devicePortsLogic.ts` (grouping, which actions apply, wording); `FlapHistorySection` (in the host/service detail drawer, for users with `system.network_health`: how often the item was flagged as flapping in a chosen window of 1, 6, 24 or 168 hours, a warning when Nagios has flap detection off globally, from `GET /api/system/network-health/flapping`); the host and service tables have a "Flapping only" filter that sends `flapping=true`; `DeviceMonitoringSection` (the monitoring label, its reason and Pause / Resume with confirmation) and `monitoringState.ts` (labels, reasons, styles, filter options). Data comes from `lib/devicePortsApi.ts`, `lib/deviceMonitoringApi.ts` and `hooks/useDevicePorts.ts` |
| `components/plugin-manager/` | Plugin inventory table, details drawer (enable preview dialog, "Not service-driven" state, attach notices), `PluginServicesSection` (paginated, searchable monitored services with status chips and Stop/Resume), `PluginCustomChecksSection` and `CustomCheckDialog` (a plugin's custom checks with Add, Change, Pause/Resume and Remove, shown only to `plugin.custom_check`, and only for plugins whose details report `custom_checks.supported`; password fields are masked, write-only and say where the password ends up; the drawer's "Not service-driven" note says why other plugins take none; for a plugin whose `custom_checks.target` is `server` the section is titled "Server checks" and the dialog has no device picker), and the disabled custom-upload modal |
| `components/maintenance/` | Maintenance window form and table |
| `components/system-status/` | `ServiceStatusTable`; with forecast data (`SystemStatusPage` loads it through `useForecasts`) a service row shows an "Estimate: warning level in about 6 days" badge whose tooltip gives the metric and basis, or "Not enough data yet" |
| `components/ncpa-deployment/` | NCPA device table, deploy wizard, run banner, history table, run drawer, outcome badges and the header bell item |
| `components/ncpa-deployment/` | NCPA device table, deploy wizard, `CleanupDialog` for trusted failed devices with ephemeral credentials and per-step results, run banner, history table, run drawer, outcome badges and the header bell item |
| `components/plugins/` | Older installed/available plugin table components; do not assume these drive the current page |
| `components/remediation/` | `StatusPanel` (the health of the consumer, a stalled banner and the kill switch), `ActionsTable` (the actions with their enable switch and a "Paused by the kill switch" note), `ActionFormDialog` (add and edit, including the Run when acknowledged option, per-field server errors, reload prompt on 409), `RunLog` (filters, table, pagination) and `RunDrawer` (one run with its output). Data comes from `lib/remediationApi.ts` and `types/remediation.ts` |
| `components/reports/` | Host availability and network-services tables; `ExtraReports.tsx` supplies Hosts by OS, Device Services, Alerts and Notifications |
| `components/manage-accounts/` | Account management table/UI |
| `components/settings/` | General, security, and system settings controls; the Network Discovery tab edits networks, scan ports and one Port → Service table per protocol (NCPA's port fixed, each entry showing the check it leads to); the Plugins tab (`PluginSettings`) shows one editable table per installed plugin: SNMP OIDs (description, OID) once `check_snmp` is installed and NCPA metrics (description, metric path, optional warning, critical, units, query args) once `check_ncpa` is installed. The NCPA table also offers Add process check: exact process name (24 safe characters) and expected count (0–1000000) produce a reviewable `processes` row with `name=<name>` query args and inclusive count thresholds; invalid names/counts and duplicate descriptions show an error, and the existing Save action persists the row. Help explains swap, editable sda disk-rate defaults, skipped paths and the load-average limitation. Cells edit in place, Add appends an empty row, rows can be removed, Reset restores the `config.py` defaults; each table warns when its plugin is not Enabled/Active and that a new or renamed description starts a new Nagios service; the Email tab (`EmailSettings`) edits the Gmail account notification mail uses: a locked Gmail preset (`smtp.gmail.com`, 587, STARTTLS), the Gmail address, a sender that follows it (warning when changed, because Gmail rewrites From), an "App password" field (`xxxx xxxx xxxx xxxx`, sent exactly as typed, write-only, blank keeps the saved one) with help text and a new-tab link to `https://myaccount.google.com/apppasswords`, and a "Send test email" card that shows a plain-language message for each failure (rejected login, blocked port, unknown host) with a technical explanation and the server's own response under "Details" |
| `components/layout/` | Authenticated application shell and global session/access behavior |
| `components/shared/` | Reusable headers, summary cards, export menu, alerts sidebar, rescan modal, and `Pagination` (Previous, page numbers, Next: every page up to four, otherwise `1 2 3 … last`, sliding to `1 … 4 5 6 … last` and `1 … last-2 last-1 last`; used by every paginated table) |

## Contexts, hooks, types, and utilities

- `CurrentUserContext` loads `/api/user/me` and exposes identity/permissions.
- `SystemSettingsContext` merges the system singleton with per-user preferences,
  handles optimistic version conflicts, and supplies `dashboardRefreshRate` and
  `scanFrequency`.
- `useNetworkRescan` starts and polls network discovery.
- `useNcpaDeploymentStatus` polls the latest NCPA run (2 s running, 15 s idle)
  for the page and the header bell, which shows a dedicated deployment item
  for users with `system.deploy.ncpa`. NCPA wrappers live in
  `src/lib/ncpaDeploymentApi.ts`; `ApiError.data` carries an error envelope's
  `data`.
- `types/` owns TypeScript API records, view models, and conversion functions.
- `formatDateTime.ts` applies display preferences to timestamps. The Time Zone preference is a fixed UTC offset or `Browser` (the viewer's own zone). `parseServerDate` reads API timestamps that carry no offset as UTC. Components get formatters from `hooks/useDisplayTime.ts`; do not call `toLocaleString` for displayed times.
- `exportData.ts` performs client-side exports and records export actions.

## Polling settings

Settings → System offers **Data polling interval** with exactly 30, 60, 120 and
300 seconds, default 60. The tab requires `settings.system`; the backend enforces
field permissions. `SystemSettingsContext` and `types/settings.tsx` carry
`dataPollingInterval` as a shared system field through save, reload and conflicts.
Settings → General explains the saved Nagios Check interval, saved Pinpoint Data
polling interval and selected per-user Dashboard Refresh Rate (including Manual).
Changing any of these schedules leaves the others, retry timing and discovery
cadence alone. Save errors retain the draft and show the API message.

## Frontend rules

- Use TypeScript; source components use `.tsx`, utilities use `.ts`.
- Page components live in `src/pages/`; subcomponents live under the matching
  `src/components/<feature>/` directory.
- Use the shared API client or a focused wrapper built on it.
- Use `/api/system/`, `/api/user/`, or `/api/plugin/` paths exactly as mounted by
  Flask. Do not omit the `/api` prefix in client code.
- Use `SystemSettingsContext` for refresh and display preferences; do not
  hardcode refresh intervals.
- Preserve loading, empty, access-denied, and error states required by the
  relevant page specification.
- Do not introduce new mock data when an API exists. Remove stale mock imports
  when connecting a feature.
- Service names in URL paths must be encoded, and backend routes must retain the
  Flask `path` converter because names may contain `/`.

## Nagios command channel UI

- `components/shared/CheckNowButton.tsx`: **Check now** in the host and service views of
  `StatusDetailDrawer`. Shown only with `system.recheck`; shows Requesting…, a
  success line, the server's error, and a countdown from the 429 `retry_after`
  (default 10 s) during which it is disabled.
- `components/shared/NagiosSyncNotice.tsx` with `types/nagiosSync.ts`: every acknowledge
  and unacknowledge call (Dashboard, Device Inventory, System Status, the drawer)
  reads `nagios_synced` from the response and shows a dismissible notice when it
  is false; nothing is shown when it is true or absent.

## Host email recipient editor

`DeviceRecipientsSection` in `components/device-inventory/` is mounted by
`StatusDetailDrawer` only in the host view, for a discovered device, and only
with `system.hosts.alerts`. It reads and replaces `/api/system/hosts/<id>/recipients`
through the shared API client; `types/hostRecipients.ts` owns the wire contract.
Each user choice shows name, email and eligibility; inactive/opted-out selections
remain visible. Saving sends `{recipient_ids: number[]}`. Empty or entirely
ineligible selections visibly explain the default group of all Active opted-in
users. Loading, load-error Retry, no accounts, apply errors and success are shown;
inputs are disabled during save. Retired/merged devices are read-only. A rejected
save retains the editable choice for retry and displays the server's message.
This editor does not require account-management permission and does not change
any user's global email setting.

Live browser coverage for host recipients is opt-in through `scripts/playwright-lab --project issue-79-live --project issue-79-restricted`. The tests save through the real recipient API/Nagios writer, reopen the drawer to verify persistence, clear the choices to verify default fallback, restore the original assignments, and verify that the restricted reader sees no editor and receives 403 for recipient reads/writes. They require two eligible lab accounts and discovered lab targets.


## Manual parent editor and topology

`DeviceParentSection` is shared by the host-only `StatusDetailDrawer` (when a
stable device ID exists) and the selected-device topology panel. It shows configured
parents to readers, a searchable checkbox multi-select/clear-all/save to
`system.hosts.edit`, an advisory suggested gateway, monitoring warnings for omitted
parents, loading/retry/empty states and server validation/apply errors. A rejected
save retains the draft; a successful save refreshes the graph or Inventory table
without unmounting the editor, so its success message remains visible. Retired and
merged devices are read-only. Parent choices do not require access to the Ports or
Interfaces sections.

`lib/topologyApi.ts` uses the shared API client; `types/topology.ts` owns wire types.
`lib/topologyLayout.ts` places each device once using iterative longest-path layers
so a shared child appears below all its parents. Isolated roots and paused devices
remain visible. React Flow retains pan/zoom/fit and device/edge/background selection;
node dragging, handle connections, edge reconnection and the interactive layout
control are disabled. Solid neutral edges mean an eligible configured parent;
dashed amber edges explain omitted parents. Edge colors do not claim measured link
health. The node labels distinguish missing checks/paused state from DOWN.

Device selection shows available device identity/address/OS, monitoring status,
last check/last seen and the shared parent editor. Connection selection names the
parent/child and explains Nagios eligibility, with a button to select the child.
No interface, power-state, utilization or traffic data is fabricated. Hosts without
a discovery record remain visible but cannot edit parents. Refresh follows the
shared Dashboard Refresh Rate (minutes, zero for Manual), plus an explicit Refresh
button. The Topology route/sidebar/header and access guard remain separate from
System Status. The page uses shared theme and timestamp preferences.

## Email settings

`components/settings/EmailSettings.tsx`, `lib/smtpSettingsApi.ts` and
`types/smtpSettings.ts` own Settings → Email (`settings.email`). Provider choices
are Gmail and Other SMTP relay. Gmail keeps its fixed host/port/security, app
password instructions, sender warning and historical save body. Other SMTP relay
shows editable host and port plus fixed STARTTLS security; host, integer port
1–65535 and STARTTLS are validated before saving. Its username may be a relay
account name; sender must be an email address accepted by the relay. Server 400
messages appear in the save error state. Discard restores the saved provider and
values. Loading, save/success/error and test-email states remain available.

Passwords are masked and write-only, never loaded from the API or stored in
browser storage. Blank preserves the saved credential; successful save clears
the entered value. Gmail and custom provider help text are separate.

The tab reads `lastMailFailure` from the settings GET and refreshes it every
30 seconds while mounted without replacing unsaved edits. A present value shows
the time using display preferences, sanitized reason and a Test email settings
link. Null removes it; polling errors show a refresh error and retain the last
observed indicator. Requests do not overlap. A successful test does not clear a
historical failure; the tab explains this. See the
[Email settings guide](../docs/manuals/Email_Settings.md).
### Escalation settings

`SettingsPage` mounts `components/settings/EscalationSettings.tsx` after the
existing System controls in Settings → System. Both that tab and the card require
`settings.system`; the card makes no request when permission is absent.
`lib/escalationApi.ts` uses the shared JSON client for `/api/system/escalations`
CRUD; `types/escalation.ts` owns the wire contracts. No new tab, route or
permission is added.

The card lists group, all/device scope, first/last counts, interval, activity
explanation and Edit/Delete actions. Its form supports create and edit, validates
finite 1–10000 integer counts and 0–1440 integer minutes before saving, and shows
server error messages including 400 and 422 without losing rejected drafts.
Delete requires explicit confirmation. Loading, retry/reload, empty and success
states are present; mutations disable controls while applying. No eligible group
disables the form and explains Active/email-alert eligibility. Inactive saved
ranges remain visible and removable. Help explains replacement recipients,
notification counts, interval zero and existing quiet-hour/suppression behavior.

The opt-in browser regression is `e2e/escalations.lab.spec.ts`, Playwright project
`issue-116-live`. Set `ISSUE116_LAB_URL` to an exclusively owned test lab and
`LAB_ADMIN_PASSWORD` for its administrator (optional `LAB_ADMIN_EMAIL`), then run
`npx playwright test --project=issue-116-live` from `client/`. With no lab URL the
test skips before any request; normal Vitest verification never runs live tests.
Login screenshots, video and traces remain disabled.


## Appliance storage and Nagios log viewer

`DashboardPage` passes status `storage_usage` through `types/dashboard.ts` to
`components/dashboard/StorageUsageCard.tsx`. It displays database/backup/archive
sizes, per-location free/total disk and a warning below 10% free, with the
threshold in help text, unavailable/partial labels, loading and error states.
The card requires `system.dashboard` and preserves old status payload handling.
Status loads independently so a failing or denied Network Health source does not
hide appliance storage.

`SystemLogsPage` retains its five paginated audit categories and adds **Nagios
log**, a separate `components/system-logs/NagiosLogPanel.tsx` rather than a
paginated audit record. It reads `/api/system/log/nagios?lines=200` through the
shared API client and `NagiosLogResponse` in `types/log.ts`. Refresh disables
while loading; empty, file-unavailable, network failure and 403 states are
explicit, and stale requests are ignored after unmount. Search/date filters,
details and audit export do not apply to the bounded tail. Help states that only
the latest 200 lines within 64 KiB are shown, newest last, that hostnames and
addresses may appear, and that free-form outputs/commands/messages are redacted.
The page/tab require `system.logs` and issue no log requests without it. Existing
audit export retains its format choices and behavior.

Live storage/log role journeys use the opt-in Playwright project `issue-124-live`
(`client/e2e/storage-logs.lab.spec.ts`) with an exclusively owned appliance and
private credential files. See the [acceptance report](../docs/test-runs/2026-10-15-issue-124-storage-logs/REPORT.md).

## Device identity review

`DeviceIdentityReviews` supplies the independent Needs Review table in
`DeviceInventoryPage` and the participating-device notice in `StatusDetailDrawer`.
Both require `system.discover` and open `IdentityReviewDrawer`, which loads
identity evidence and address history on demand (`system.hosts`) and offers
explicit source/target choices, discovered-record search and confirmation only
with `system.hosts.edit` as well. `lib/deviceIdentityApi.ts` uses the shared API
client for the existing review/evidence/merge routes and `/api/system/hosts/lookup`;
`types/deviceIdentity.ts` owns the wire contracts and identity-kind filtering.
See `Device_Inventory_Requirements.md` §14 for the permission, confirmation,
keyboard, refresh and saved-configuration-warning requirements.

## Manual agent registration (#130)

On NCPA Deployment (`system.deploy.ncpa`), every device row whose agent is not
already deployed has **Register agent**. `RegisterAgentDialog` asks for the NCPA
token (32 hexadecimal characters) and an optional port, validates both before
calling `registerManualAgent` (`POST .../<id>/register`), and shows loading,
server error and success (status, disks found, config message) states. The token
field is cleared after every call and the token is never kept in state or shown
again. A collapsible panel explains installing NCPA on Windows. Registration
reloads the device list. The page header also has **Register an agent I installed**,
which opens the same dialog with a device picker loaded from
`GET .../register-candidates` (active scanned devices that are not deployed,
including hosts without SSH such as Windows servers); the deploy list is unchanged.

## Remote service restart controls (#182)

On NCPA Deployment (`system.deploy.ncpa`), trusted device rows expose **Remote
restart**, including already deployed devices. `RemoteRestartDialog` loads and
saves the per-device enabled switch and up to 20 service names through
`ncpaDeploymentApi` and `RemoteRestartSettings`. It shows loading, empty-list,
load/retry, save/error, success and server permission states. Enabling requires a
trusted deployment; the list can be prepared with the switch off. Settings cannot
open during a deployment. Help explains the cleanup/redeploy requirement for old
devices and changed lists. The Clean up dialog warns that remote restarts stop
until redeployment and preserves ephemeral credential clearing.

`ActionFormDialog` renders the typed parameter schema from the action-types API:
local `unit` is a fixed-choice select, remote `unit` is a text field. Create and
edit submit the entered parameters, show field-specific validation errors and
clear old parameters when the action type changes. Existing remediation page
view/manage guards continue to control access. See the
[administrator guide](../docs/manuals/Remote_Service_Restart.md).

The opt-in `issue-182-live` Playwright project covers these controls against an
exclusively owned appliance through the no-network private socket bridge: settings
loading/retry, real validation and persistence, cleanup/deployment wizard, remote
and local unit forms, and real read-only permissions. See
[the acceptance plan](../server/tests/plans/REMOTE_RESTART_ACCEPTANCE.md).


## Reports

`pages/ReportsPage.tsx` exposes six views, all requiring `system.report` in
both the page guard and the server routes in `app/api/system/report.py`.
Pinpoint shows measured uptime; availability targets, breach comparisons and
scheduled or recurring emailed reports are outside the supported scope.

| View | API route (GET) | Displayed data |
|---|---|---|
| Host Availability | `/api/system/report/availability` | Hostname, state, uptime %, Snapshots (legacy label for known-state seconds), last check and last state change; summary cards show total hosts, Up, Down / Unreachable and overall uptime |
| Network Services | `/api/system/report/network-services` | One row per service name: instance count, OK / Warning / Critical / Unknown counts and uptime %; summary cards show service and instance totals, OK, Warning / Critical and overall uptime |
| Hosts by OS | `/api/system/report/hosts-by-os` | Flattened host rows with OS, hostname, state, uptime %, last check and last state change; no summary cards |
| Device Services | `/api/system/report/device-services` | One row per host/service pair: hostname, service, state, uptime %, snapshot count, last check and last state change; no summary cards |
| Alerts | `/api/system/report/alerts` | Time, hostname, service, previous state, new state and output; cards count listed alerts, recoveries, problems and affected hosts |
| Notifications | `/api/system/report/notifications` | Time, hostname, service, state, contact and message; cards count listed notifications, recoveries, problems and distinct nonempty contacts |

Host Availability and Hosts by OS obtain host uptime from Nagios archive
Up / (Up + Down + Unreachable) durations; unknown time is excluded and no known
time yields a null uptime (shown as `—`). Network Services and Device Services
compute service uptime from OK snapshots / all service snapshots in the selected
window. Alerts and Notifications read Nagios archive events; their cards are
computed from the returned rows rather than the separate API `count` object.

### Periods and running reports

Every view sends `period` to its route. The shared selector offers `last_24h`
(default), `today`, `last_7d`, `last_30d`, `last_90d` and `custom`. Rolling periods
end at server now; Today starts at server-local midnight. Custom ranges send
`start` and `end` as `YYYY-MM-DD`, inclusive, and require both dates. The backend
validates periods and dates. Changing a view or period loads its report; after
editing custom dates, **Run Report** loads the chosen range. It also reruns the
current report. Host Availability and Network Services load in `ReportsPage`;
the other four load in `ExtraReports` on view change or a changed run key.
Tables have loading and empty states, and request errors appear above them.

### Filtering and export support

All six tables page ten rows at a time, support search and a sort-direction
control, and export the full filtered, sorted result rather than only the
current page. Host Availability searches hostname and filters state; Network
Services searches service name. Hosts by OS searches hostname/OS, Device
Services searches host/service, Alerts searches host/service/output and
Notifications searches host/service/contact; all four extra views filter state.
Host and service tables sort by their respective names, Hosts by OS and Device
Services by hostname, and event views by time (newest first by default).

Each view uses `ExportMenu` and `utils/exportData.ts`, limited to the formats
allowed by `SystemSettings.exportFormats`: CSV download, XLS download (an HTML
table with an `.xls` extension), or a print view for saving as PDF. Exports use
raw row timestamps; on-screen timestamps use the configured display format and
time zone. No report period metadata or summary cards are included in exports.

| View | Filename stem | Export columns |
|---|---|---|
| Host Availability | `host-availability-report` | Hostname, State, Uptime %, Total Snapshots, Last Check, Last State Change |
| Network Services | `network-services-report` | Service, Total Instances, OK, Warning, Critical, Unknown, Uptime % |
| Hosts by OS | `hosts-by-os-report` | OS, Hostname, State, Uptime %, Last Check, Last State Change |
| Device Services | `device-services-report` | Hostname, Service, State, Uptime %, Snapshots, Last Check, Last State Change |
| Alerts | `alerts-report` | Time, Hostname, Service, Previous State, New State, Output |
| Notifications | `notifications-report` | Time, Hostname, Service, State, Contact, Message |

Host Availability retains `Snapshots` on screen and `Total Snapshots` in exports, but its
API `total_snapshots` value is known-state duration in seconds from Nagios,
not a polling snapshot count. Export logging posts to `/api/system/exportlog`;
a logging failure does not prevent the download.
