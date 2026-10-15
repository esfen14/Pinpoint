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
| `/system-status` | `SystemStatusPage` | `system.network_health` | The **System Status** page (sidebar label “System Status”): a service-status table with OK / Warning / Unknown / Critical counts, search, state filter, sort, paging and acknowledgement. It is a supported page. The network *topology view* is excluded from the release. |
| `/plugins` | `PluginsPage` | `plugin.view` | Connected to Plugin Manager inventory (category tabs All / Network Services / Device Availability / Network Protocols / Servers / Application / Other, filtered by the `group` query parameter so paging stays per tab; a Monitoring column and a banner while no plugin is enabled), plugin details with an enable confirmation that previews what will be monitored, the plugin's monitored services with live status and per-device stop/resume, scanning, and mutation APIs. There is no Currently Running tab (the tabs are categories only) and devices are never picked by hand |
| `/ncpa-deployment` | `NcpaDeploymentPage` | `system.deploy.ncpa` | Warns, through `useNcpaPluginState`, when `check_ncpa` is not enabled in Plugin Manager (the agent's checks are monitored only while it is). Connected to the NCPA deployment routes: device list, deploy wizard (host-key trust, login checks, start), live run banner, Deployment History tab and run review drawer (`?tab=history&run=<id>`). Trusted failed devices (not deployed/healthy devices) have a Clean up dialog: it accepts ephemeral SSH credentials, optionally removes the deployment account after artifact removal, shows each cleanup step and refreshes the list; fields clear after every request. |
| `/remediation` | `RemediationPage` | `remediation.view` | Connected to `/api/system/remediation/...`; sidebar entry "Remediation". An Actions tab (banner "Actions run automatically when a service reaches a hard failure", an enable switch per action, an add/edit form built from the action types with server messages shown against the right field, delete with confirmation; with only `remediation.view` the list is read-only) and a Run log tab (filters for action, outcome, host and dates, pagination, skipped runs show their reason, a drawer with the redacted output). Changes need `remediation.manage`; 409 offers a reload and 422 shows the Nagios message |
| `/reports` | `ReportsPage` | `system.report` | Connected for host availability and network-services views; backend exposes additional report routes |
| `/system-logs` | `SystemLogsPage` | `system.logs` | Connected to five log categories |
| `/accounts` | `ManageAccountsPage` | `account.view` | Connected to account/role APIs. The table shows each user's Email Alerts (On/Off); the add and edit forms show a "Send this user email alerts" checkbox only with `account.alerts`, and a failed Nagios apply is shown as a notice. The first account is marked by the account API as `is_super_admin`; its edit form keeps Status Active, disables the status selector, explains that the bootstrap administrator must retain account/role administration, and disables role options whose `preserves_bootstrap_admin_access` value is false |
| `/manage-roles` | `ManageRolesPage` | `role.view` | Connected to role and permission APIs. The built-in `Administrator` role shows every permission as read-only with an explanation, and its name cannot be edited. The bootstrap administrator's assigned role is marked as locked; its edit form disables the seven account/role administration permission controls and role deactivation, even when assigned to a different role |
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
| `components/dashboard/` | Dashboard metrics, resource views, alerts, charts, and outage presentation |
| `components/network-health/` | Trend/metric cards, network health summaries, insight panels, and graph modal; `BandwidthCard` / `BandwidthChart` (Interface Bandwidth: device and interface selectors, a time range of 1 hour to 7 days, in and out lines whose unit scales from bit/s to Tbit/s, loading / error / no-device / no-interface / insufficient-data / no-data states and help text; loads its own data from `lib/bandwidthApi.ts`, so a failure never blanks the rest of the page, and reports the reading on screen to the page (`onReading`) for the side Bandwidth widget; the choosers are `components/shared/DropdownSelect.tsx`, the button-and-list dropdown that matches `TimeRangeSelect`; `TimeRangeSelect` takes an optional `options` list so the card can leave out the 5-minute range) |
| `components/device-inventory/` | Host/device table; the host detail drawer; `DevicePortsSection` (a device's ports in groups with the reason each is or is not monitored, and the Monitor / Acknowledge / Ignore / Stop / Leave suggested / Resume / Set service / Remove pin actions with confirmations), `SetServiceDialog`, and `devicePortsLogic.ts` (grouping, which actions apply, wording); `DeviceInterfacesSection` (the drawer's Interfaces section for SNMP devices: name, index, speed and status of each interface, a Monitor checkbox per interface, and Refresh to read the list from the device; hidden for a device without SNMP; editing needs `system.hosts.edit`; data from `lib/bandwidthApi.ts`, types in `types/bandwidth.ts`); `DeviceMonitoringSection` (the monitoring label, its reason and Pause / Resume with confirmation) and `monitoringState.ts` (labels, reasons, styles, filter options). Data comes from `lib/devicePortsApi.ts`, `lib/deviceMonitoringApi.ts` and `hooks/useDevicePorts.ts` |
| `components/network-health/` | Trend/metric cards, network health summaries, insight panels, and graph modal |
| `components/device-inventory/` | Host/device table; the host detail drawer; `DevicePortsSection` (a device's ports in groups with the reason each is or is not monitored, and the Monitor / Acknowledge / Ignore / Stop / Leave suggested / Resume / Set service / Remove pin actions with confirmations), `SetServiceDialog`, and `devicePortsLogic.ts` (grouping, which actions apply, wording); `FlapHistorySection` (in the host/service detail drawer, for users with `system.network_health`: how often the item was flagged as flapping in a chosen window of 1, 6, 24 or 168 hours, a warning when Nagios has flap detection off globally, from `GET /api/system/network-health/flapping`); the host and service tables have a "Flapping only" filter that sends `flapping=true`; `DeviceMonitoringSection` (the monitoring label, its reason and Pause / Resume with confirmation) and `monitoringState.ts` (labels, reasons, styles, filter options). Data comes from `lib/devicePortsApi.ts`, `lib/deviceMonitoringApi.ts` and `hooks/useDevicePorts.ts` |
| `components/plugin-manager/` | Plugin inventory table, details drawer (enable preview dialog, "Not service-driven" state, attach notices), `PluginServicesSection` (paginated, searchable monitored services with status chips and Stop/Resume), `PluginCustomChecksSection` and `CustomCheckDialog` (a plugin's custom checks with Add, Change, Pause/Resume and Remove, shown only to `plugin.custom_check`, and only for plugins whose details report `custom_checks.supported`; password fields are masked, write-only and say where the password ends up; the drawer's "Not service-driven" note says why other plugins take none; for a plugin whose `custom_checks.target` is `server` the section is titled "Server checks" and the dialog has no device picker), and the disabled custom-upload modal |
| `components/ncpa-deployment/` | NCPA device table, deploy wizard, `CleanupDialog` for trusted failed devices with ephemeral credentials and per-step results, run banner, history table, run drawer, outcome badges and the header bell item |
| `components/plugins/` | Older installed/available plugin table components; do not assume these drive the current page |
| `components/remediation/` | `ActionsTable` (the actions with their enable switch), `ActionFormDialog` (add and edit, per-field server errors, reload prompt on 409), `RunLog` (filters, table, pagination) and `RunDrawer` (one run with its output). Data comes from `lib/remediationApi.ts` and `types/remediation.ts` |
| `components/reports/` | Host availability and network-services report tables |
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
