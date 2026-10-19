# Implementation Status and Scope

**Snapshot date:** 2026-10-17

This file reports what is present in the repository. It is not a substitute for
the normative behavior in the requirement specifications.

## Isolated DHCP acceptance lab (#187)

The opt-in Docker lab in `lab/dhcp/` supplies real IPv4 DHCP on an isolated
`10.79.0.0/28` test bridge and a separate loopback management path. Its owned
controller (`scripts/dhcp-lab`) provisions a static appliance/server and two
persistent, distinct DHCP clients, checks route and resource collisions, moves
client-1 from A to B and tears down only resources bearing its saved owner
token. `scripts/dhcp-accept` runs bounded real discovery, Nagios, Inventory and
History checks plus a second clean cycle; see the [acceptance plan](../server/tests/plans/DHCP_LAB_ACCEPTANCE.md).
The ordinary static Docker and VM labs remain separate. This lab does not
cover installer behavior, physical networks, routed discovery without a MAC,
cloned identities, IPv6, DHCP failover or NCPA deployment. The live outcome is
recorded in the issue #187 test-run report rather than inferred from the
runner's presence.

## Navigation order (#231)

The sidebar places Device Inventory → Network Status → Topology consecutively.
The `/system-status` page content heading is Network Service Overview (#232);
its service behavior, route and permissions are unchanged.
Existing labels, destinations and `system.network_health` filtering are preserved;
rendered-sidebar regression checks cover order, links and denied visibility.
Live appliance/browser verification is pending.

## Manual topology (#117)

Manual multiple-parent relationships, graph validation and eligibility-aware Nagios
rendering are implemented on the issue branch, with a reversible multi-bind
migration. The existing React Flow prototype is wired to real inventory/status data,
with a shared Inventory/Topology parent editor and automatic non-editable layout.
Local full verification and real routed Nagios default-three-attempt reachability,
notification dispatch, pause, merge and retire checks pass. A continued real
browser/Flask/Nagios run verifies both editors, reload/cross-page persistence, cycle
errors, read-only controls and direct 403; it also fixed an Inventory save-confirmation
unmount regression. See [the live browser report](../docs/test-runs/2026-10-15-issue-117-live-browser/REPORT.md)
and [the routed report](../docs/test-runs/2026-10-15-issue-117-manual-topology/REPORT.md).
The current-main integration preserves escalation/remediation rendering and joins
the published migration histories without rewriting them; populated upgrades from
both old heads and a real browser/Nagios retest pass. See [the main-sync report](../docs/test-runs/2026-10-15-issue-117-main-sync/REPORT.md).
CI and human review are tracked on the implementation PR. For
[issue #173](https://github.com/esfen14/Pinpoint/issues/173), the user accepted
Option A on 2026-10-17: temporary child DOWN notifications are allowed before
Nagios confirms parent reachability. One-attempt monitoring remains supported;
no cache, retry or notification configuration change is approved. The contract is
in Device Inventory §13 and the data integration specification, with
[operator guidance](../docs/manuals/Notification_Policy.md#parent-outages-and-temporary-child-down-alerts).
The [#173 routed acceptance report](../docs/test-runs/2026-10-17-issue-173-parent-notifications/REPORT.md)
records exact settings and observed single/redundant-parent HARD DOWN notifications
followed by UNREACHABLE, no-parent DOWN controls, recovery and cleanup. The opt-in
Core driver covers the accepted contract; no application runtime change is needed.
Review readiness and CI are tracked on PR #192. Parent links do not implement
routing failover or guarantee immediate suppression under every Nagios cache/retry
configuration.

## Account creation (#191)

The Add User dialog now uses the displayed default role for validation and
submission even when roles load after the dialog opens. The previously stale
zero role ID could keep Save disabled despite a visibly selected role. Isolated
interaction tests cover the timing regression, sequential creation and list
refresh, explicit role/status, no-role guidance and rejection/retry. A backend
regression verifies two additional persisted accounts and a total of three.
A [local Chromium/real Flask run](../docs/test-runs/2026-10-17-issue-191-accounts/REPORT.md)
also confirms delayed-role creation, a second account and reload persistence
with temporary SQLite and a stubbed Nagios writer. The API has no one-account cap. The exact trigger in the original report is
unconfirmed; password policy and mismatch checks intentionally still block Save.
See [the investigation](../docs/plans/Issue_191_Account_Creation_Investigation.md).

## NCPA resource trend selection (#242)

Historical CPU, disk and memory samples now use the existing command-first plugin
classifier, including generated `ncpa-*` descriptions and command-identified
checks. The requested time window excludes old and future samples, and non-NCPA
checks are excluded even when their names or metrics resemble NCPA. A shared classifier also maps real short `percent`/`used_percent` labels in trends
and current summaries, keeping swap, disk I/O and ambiguous identities out.
Existing full-path history remains supported without rewriting stored labels.
Forecast selection now shares the canonical chart/summary classifier for
virtual-memory and disk full/short labels (#259), preserving forecast safety rules. Numeric API/summary regressions and both real-agent Docker browser resource
journeys pass; see the [live chart report](../docs/test-runs/2026-10-19-issue-242-resource-charts/REPORT.md).
The user's appliance, installer deployment and scale remain unverified.

[Separate #259 real-history verification](../docs/test-runs/2026-10-19-issue-259-ncpa-forecast-labels/REPORT.md) confirms short-label selection and preserved insufficient state on an isolated history copy; numeric crossings use controlled regressions, not a long real fill.

## Implemented backend areas

- Session login/logout and current-user identity. Existing-session login is
  explicitly rejected with 409 and requires sign-out before another login (#222).
  The login route checks the server session and redirects authenticated users to
  an authorized page. Isolated regressions cover both Admin/Viewer directions,
  retained identity after rejection and the new account's permissions after logout.
  Original manual role/evidence details and new appliance manual acceptance remain
  pending; these tests do not establish a live manual pass.
- Account, role, permission-option, and per-user preference APIs, including the
  bootstrap administrator's first-run setup (`POST /api/user/complete-setup`)
  and server-access recovery (`flask recover-bootstrap-admin`). Recovery privately
  prompts for a policy-compliant temporary password, identifies only the unique
  earliest-created account, preserves setup/status/role/data, forces a password
  change and records a password-free audit event; current sessions continue to
  expire on their configured timeout. The first account (bootstrap administrator)
  is protected from suspension, inactivation, assignment to a role without the
  seven account/role administration permissions, and removal of those permissions
  from its assigned role. Both routes reject before changing persisted data. The
  account and role responses mark the protected choices so their edit forms explain
  the restriction and disable unsafe status, role, and permission controls.
  The built-in `Super Admin` role additionally has an immutable permission set
  for every account assigned to it: direct API edits reject changed grants before
  saving metadata, while reordered unchanged grants permit description edits.
  Its name is fixed to preserve the role's built-in identity, and role management
  displays all its permission controls read-only with an explanation. The role
  was renamed from the legacy `Administrator` name; `flask sync-permissions`
  renames an existing `Administrator` role to `Super Admin` (keeping its RoleID,
  users and permissions) and, if a `Super Admin` role already exists, leaves the
  legacy role under the distinct name `Administrator (Legacy)` rather than
  merging roles or reassigning users. Fresh installs and repeated initialization
  seed and look up the role by the new name without creating a duplicate.
- Singleton system settings with personal/system separation and optimistic
  version conflict handling. The system Check interval (1/2/5/10/15 minutes),
  Retry interval (1 to 10 minutes) and Maximum check attempts (1 to 10)
  generate host and service check timing through the shared Nagios writer;
  Flap detection (on/off and optional low/high thresholds) is also written
  through it, with a Flapping-only filter on the host and service tables and a
  flap history (from polling snapshots, 60 seconds by default, so fast flaps can be missed) in the
  detail drawer;
  unchanged Nagios `Last_Check` results are not stored again. Plugin status text,
  stale fallback and the per-user browser-refresh hint use the setting. Fresh
  appliance cadence, backup and validation/reload rollback were verified in
  `docs/test-runs/2026-10-10-issue-60/REPORT.md`; controlled full-hour
  before/after rows-per-host measurement is deferred to #82 under the #62 QA
  plan. The short VM comparison is not that measurement.
- Dashboard status, summary, active alerts, acknowledgement, and latest
  notifications.
- Network Health summary, metric trends, plugin grouping, host table/details,
  service table/details, and acknowledgements.
- Alerts and Notifications History list/detail routes backed by Nagios archive
  events and Pinpoint acknowledgement history.
- Header notification feed with per-user unread cursor.
- Nagios command channel (`app/nagios/commands.py`, `NAGIOS_COMMAND_FILE`): acknowledgements and unacknowledgements are sent to Nagios (`nagios_synced` in the response, notice in the UI), and **Check now** (`system.recheck`, 10 s per-target limit) forces a host or service check. Covered by unit and API tests against a temporary FIFO; **not yet verified on a live Nagios appliance** (no lab report in `docs/test-runs/`; run `flask sync-permissions` after deploying to add `system.recheck`).
- Maintenance windows (#122): `MaintenanceWindow`/`MaintenanceOccurrence`, the `maintenance_windows` scheduler job, the four `/api/system/maintenance/windows` routes (`maintenance.manage`; run `flask sync-permissions` after upgrading) and the Maintenance page. Unit, API, migration, scheduler and frontend tests pass. Docker-lab run (`docs/test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md`): schedule and cancel by comment on Nagios 4.5.11. See the report for what the lab did not cover (suppressed notification mail, installer-built appliance, browser UI).
- Per-user email alert setting (`User.Receive_Email_Alerts`, permission `account.alerts`): only Active opted-in users become Nagios contacts, and account changes that affect a contact rebuild the Nagios config (#80). Verified on the VM lab: contacts follow account changes without a scan, and host and service notifications reach only opted-in users (#80).
- Interface bandwidth: SNMP interface discovery (`snmpwalk`, on demand and after a scan), per-device
  `DeviceInterface` rows, in/out octet Nagios services per monitored interface, the rate calculator
  (`app/bandwidth.py`: 32/64-bit wrap, restart, gap, insufficient data), the bandwidth routes, the
  Network Health Interface Bandwidth card and the drawer's Interfaces section. Unit, API, migration
  and frontend tests pass. Docker-lab run (`docs/test-runs/2026-10-14-issue-13-bandwidth-docker-lab/`):
  discovery, monitoring, Nagios validation and a rate within 5% of `ping` traffic observed; **`iperf3`,
  a fast link, counter wrap on a live device and the browser UI are not yet verified**. Interface discovery needs `snmpwalk`
  on the server (net-snmp-utils / snmp), which `check_snmp` already needs.
- Alert email is formatted HTML with a plain-text part (dark layout, state colour and wording, parsed packet-loss figure, UTC detection time), built by `server/scripts/pinpoint_notify_email.py` through generated `pinpoint_notify_*_html` commands; contacts fall back to the stock plain-text commands when the script is unavailable. Verified on a lab appliance by sending a Nagios custom notification (2026-10-13). Gaps: recovery, acknowledgement and warning layouts are covered by unit tests and a browser render but not yet seen in a mail client; the script runs from the application directory (owned by `pinpoint`), not a root-owned path.
- Network discovery start/stop/status and Nagios host/service config generation. The reconciliation engine is designed to isolate potential identity conflicts for operator review (creating `DeviceReviewItem` records) rather than silently merging them. This prevents unintended record modification during subnet changes or cloned-identity events (see `device_identity.py`). Ambiguous records remain available for review. Device Inventory now exposes an identity-only Needs Review table, comparison with confidence/identifiers and on-demand address history, discovered-record search and an explicitly directed merge confirmation (#164). Retire remains API-only; the review UI never automatically merges records.
- NCPA eligibility, SSH fingerprint trust (approved key only), login checks,
  deployment with per-device outcomes, cancellation, status, run history and
  review, and trusted-device routes.
- NCPA bootstrap probes log expected missing-account/key exits at INFO while
  preserving creation behavior; unexpected command failures remain ERROR (#47).
- Activity, configuration, discovery, NCPA, and export logs. Issue #124 adds a
  read-only fixed-path Nagios log tail and a System Logs tab (200 lines by
  default, caps 500 lines / 64 KiB, command/output redaction, permission and
  unavailable states). Dashboard status now includes bounded database, backup
  and archive storage measurements with per-location free disk and a below-10%
  warning. No model/migration/permission changes. Paired installer changes live
  on `issue-124-log-retention` in the separate installer repository: 100 MiB / 7-day
  host journal defaults, administrator-policy preservation and weekly installer
  log rotation. Automated tests cover helpers/APIs/UI and installer fixtures;
  [exclusive VM acceptance](../docs/test-runs/2026-10-15-issue-124-storage-logs/REPORT.md)
  verifies fresh deployment (60/0 health), bounded journal usage after volume,
  actual rotation, administrator-policy preservation through upgrade, live APIs
  and four browser role journeys. The post-setup installer healthcheck expects
  hosts.cfg 664 while the existing writer uses 640 (installer #9); other 59
  checks pass. Paired human review and interactive ISO boot remain unverified.
- Availability, OS, network-service, device-service, alert, and notification
  report APIs. Host availability and hosts-by-OS reports use Nagios
  `archivejson.cgi` durations, matching Network Health; Nagios failure returns
  502 without snapshot fallback (#92).
- Plugin Manager scanning, inventory, running checks, summaries, details,
  dependencies, enable/disable, validation, custom upload, command overrides,
  updates/rollback, history, and target configuration.
- Configurable Pinpoint Data polling interval (`dataPollingInterval`): 30/60/120/300
  seconds, default 60, system permission, persisted with upgrade default migration.
  Saves reschedule one existing job and restore its trigger/next run on failure;
  disabled scheduling stays disabled and startup uses the saved interval. General
  displays the actual saved check/poll and personal browser refresh schedules.
- Database restore and backup health (#125): `flask restore-backup`, `backup_health` on the dashboard status route and a failed-backup activity-log entry; unit tests pass. Recovery runbook `docs/manuals/Backup_and_Restore.md`. No frontend display of `backup_health`. **Not yet verified on a fresh lab appliance** (`scripts/vmlab fresh`; no report in `docs/test-runs/`). Cold standby only; Nagios config and NCPA key are not backed up.
- Scheduled Nagios polling, retention purges, backups, network scans, plugin
  update scans, and security validation.
- Event handler framework (#120): admin-defined remediation actions (`record_only`, plus `restart_local_service` from #121 and `restart_remote_service` from #8 Part 8.3), the
  `/api/system/remediation` routes with `remediation.view` and `remediation.manage`, the handler
  script, the spool consumer with cooldown, hourly cap, replay protection and crash recovery, and
  Nagios config rendering that is byte-identical when no action is enabled.
- Remediation safety controls (#155): a kill switch and a run-retention setting changed through
  `/api/system/remediation/settings`, skip reasons for the kill switch, Maintenance Mode (every action
  type), scheduled downtime and acknowledged problems (`Run_When_Acknowledged` opts an action out),
  purge of old runs and spool files with a 1000 file spool cap, a consumer heartbeat and
  `/api/system/remediation/health` with a `stalled` flag, and the status panel on the Remediation page.
- Failure escalation for automatic recovery (#153): a failed or timed-out run, a run stopped by the
  cooldown or hourly cap, and a service recovered repeatedly each send one Nagios custom
  notification (never forced, fixed-text comment) when the action's `Notify_On` asks for it; state,
  bounded retry and restart safety are on the run; `/api/system/remediation/last-runs`; the Operator
  column, drawer details, `Notify_On` checkboxes, Repeat recovery limits and a last-recovery badge on
  service rows. Verified with the command layer mocked and a lab run; the browser pass and an automatic-run mail check are open
  (see Incomplete or mismatched work).
- Per-service "Recover automatically" (#154): `GET`/`PUT /api/system/remediation/services/<host>/<service>` and a switch with a restarts-per-hour limit in the Device Inventory service view, backed by one service-scoped `RemediationAction` shared with the Remediation page, plus a read-only mark on Network Status rows.

## Implemented frontend areas

- Login and authenticated application layout.
- Permission-aware sidebar and direct-route guard.
- Dashboard API integration and acknowledgement flow.
- Network Health summary/trend integration.
- Device Inventory backed by latest host-status APIs.
  - Account and role management. Edit Account rejects reuse of the edited user's
    current password before saving any changes (#219), with a server warning
    displayed in the dialog and a retry using a different password. Isolated
    backend and UI regressions cover rejection, unchanged data and retry; the
    original TC-ACC-06 manual FAIL remains unchanged pending a separate manual
    retest on an identified build.
- System Settings and per-user preferences. The separate Notification Policy singleton drives generated Nagios timeperiods, contact options and host/service notification settings; Settings → System exposes quiet hours and state/interval controls (`settings.system`). Defaults preserve pre-change `hosts.cfg`. Docker-lab Nagios validation and forced host/service notification dispatch inside/outside quiet hours are documented in `docs/test-runs/2026-10-13-issue-113-notification-policy/REPORT.md`; browser save/reload was exercised via the Docker lab; installer-built VM and inbox delivery are not verified there.
- Notification escalations (#116): Settings → System and `settings.system` CRUD use the existing #79 groups, finite notification-count ranges and all/device scope. The shared writer emits host/service escalation blocks, suppresses empty groups and absent scoped hosts, and rolls back failed apply. Automated API, renderer, migration and interaction checks cover these paths. The [isolated Docker report](../docs/test-runs/2026-10-15-issue-116-escalations/REPORT.md) verifies real Nagios host/service validation, notification 1 reaching the normal recipient and notification 2 the escalation recipient on an unacknowledged HARD CRITICAL, opt-out/deactivation suppression, rejected-config rollback and browser CRUD. Local MIME capture proves notifier routing; external SMTP/inbox delivery and installer/VM deployment were not tested.
- NCPA notification dependencies (#118): default-on `PINPOINT_NCPA_NOTIFICATION_DEPENDENCIES` generates a visible TCP listener service and notification-only `c,u` dependencies for each generated NCPA metric when `check_tcp` is enabled; off retains the old service list. There is no host-to-service dependency object because Nagios does not support one. [Docker lab evidence](../docs/test-runs/2026-10-17-issue-118/REPORT.md) verifies Nagios accepts three generated dependency objects, and a real host outage with three monitored services produces one host notification event, no service notification events, and critical states in Dashboard and Network Health APIs. A real NCPA agent/port-failure notification trial remains unverified.
- Settings -> Plugins tab (`settings.plugins`): the SNMP OID table and the NCPA metric table, each editable once its plugin (`check_snmp`, `check_ncpa`) is installed; saving rebuilds the Nagios config. A metric's `fallback_path` (used when no partitions were recorded) is supported by the planner but not editable from the tab.
- Settings -> Email tab (`settings.email`): Gmail preset plus Other SMTP relay over STARTTLS, applied through the existing installer helper. Custom host/port validation, password preservation and generic relay test-email errors are covered by isolated tests; Gmail tests remain unchanged. The tab polls a bounded, sanitized Nagios notification-failure indicator every 30 seconds. No migration or new permission is needed. The [#115 Docker acceptance run](../docs/test-runs/2026-10-15-issue-115-starttls-docker/REPORT.md) verifies the unchanged root helper through real sudo, protected file metadata, five authenticated STARTTLS sink deliveries (API, Nagios host/service and browser), actual worker failure detection within 0.33 seconds, service-user log access and browser notice polling without losing edits. The [external receipt run](../docs/test-runs/2026-10-15-issue-115-inbox-confirmed/REPORT.md) records owner-reported successful test email, owner-confirmed receipt of the uniquely labeled real Nagios notification, a final guarded browser repeat and removal of the owned fixture. No installer ISO/upgrade result is claimed. Implicit TLS/installer changes are deferred by the user; plaintext SMTP and Microsoft 365/OAuth remain excluded. The helper exists only on installed appliances, so saving elsewhere returns "The mail helper is not installed on this server."
- System Logs with five backend categories.
- Reports UI with six connected views: Host Availability, Network Services, Hosts by OS, Device Services, Alerts and Notifications. Each supports shared report periods and filtered exports; see [Reports](Frontend_Modules_and_Routes.md#reports) for endpoints, displayed fields and formats.
- Plugin Manager inventory/running tabs, details, scan, custom plugin, and
  administrative actions.
- Remediation page (`remediation.view`): actions with an enable switch, an add/edit form, and a run log with filters and a detail drawer (#120).
- NCPA Deployment page: device list, deploy wizard with host-key verification
  and per-device login checks, live progress, header bell item, and Deployment
  History with run review.
- Header notification feed/unread behavior, session timeout, maintenance banner,
  shared export UI, and network rescan workflow.

## Incomplete or mismatched work

| Area | Current state | Required direction |
|---|---|---|
| Set service uppercase validation (TC-DI-07) | `SetServiceDialog` lowercases trimmed input before applying the lowercase-only regex and before saving, while the black-box case expects uppercase `SSH` to be invalid. The regex unit test rejects uppercase in isolation, but this does not verify dialog normalization. No live result is claimed. | Resolve the intended uppercase behavior and align the dialog or approved case/spec before accepting E2; the current adapter asserts the catalog expectation and keeps the live case result evidence-dependent |
| History frontend audit | `/history` is routed and permission-guarded; its source audit against `Alerts_Notifications_History_Requirements.md` is in `docs/test-runs/2026-10-14-issue-133-history-audit/AUDIT.md`. It supports sorting for API-supported columns and cross-tab target navigation. Episode-specific acknowledgement now bounds list/filter/detail annotations by Nagios problem/recovery transitions and ACK_HISTORY actions (#141). The list API now supports validated offset-aware custom date/time bounds and all-column sorting with timestamp-desc ties (#142); the page still needs to wire its picker and remaining columns to those options. Exact event linking now uses deterministic archive event locators in list/detail responses and cross-tab row expansion outside the default range (#143; indistinguishable duplicate archive records still require upstream identity). Prior-state and recovery duration derive from the archive timeline, including transitions before the selected list range (#144); when no earlier archive record exists, onset cannot be inferred. No live appliance walk has been recorded | Wire the history UI to #142, complete #144 and verify manually on a lab appliance |
| Auto-resolved acknowledgements | A completed Nagios status poll clears active acknowledgements for fresh UP/OK checks and appends actorless AUTO_RESOLVED history in one transaction; missing/stale/failed checks retain them. Isolated tests pass; live lab recovery not yet verified | Verify acknowledge → recover → history on a lab appliance |
| Per-host alert recipients | `HostAlertRecipient` selects users per stable device; permission `system.hosts.alerts` gates the host editor and read/write routes. Generated host and service groups filter Active opted-in users, fall back to the default, and roll back failed saves; rescan/merge/retire ownership covered by isolated tests | #79: [Docker repeat](../docs/test-runs/2026-10-14-issue-79-docker-repeat/REPORT.md) verifies real Nagios groups, selected/default host and service MIME routing, fallback, rescan and rollback (14 passes across the initial and follow-up reports). [VM/browser run](../docs/test-runs/2026-10-15-issue-79-vm-browser/REPORT.md) also verifies save/config validation, normal host/service captured mail routing, rescan and ineligible fallback. [Rebuilt VM run](../docs/test-runs/2026-10-15-issue-79-rebuilt-inbox/REPORT.md) on integrated commit `4ed80435` passes browser E2E (4 checks), selected/default groups, real DOWN/HARD CRITICAL dispatch, actual Gmail SMTP acceptance (12 problem/recovery messages), bounded rescan and ineligible fallback; original baseline restored with unchanged database/static hashes. [Owner inbox confirmation](../docs/test-runs/2026-10-15-issue-79-inbox-confirmed/REPORT.md) completes acceptance: selected mailbox received eight host/service problem/recovery messages for both hosts, while the default-only mailbox received four for the default host and none for the selected host, including Spam. [#162](https://github.com/esfen14/Pinpoint/issues/162) is resolved by merged PR #165 and the rebuilt lab passes ownership preflight. Recipient/interface migration histories now join at e79b7d3c2641; interface counter services retain recipient groups with global NCPA enabled. The initial immediate post-reload capture timed out; a later transition after worker registration passed, and the timing cause remains undiagnosed |
| Discovery stop permission | Stop route checks `network.discovery`; seed data defines `system.discover` | Standardize the route on the seeded permission or deliberately introduce/seed the alternate permission |
| Password recovery | Email settings and installer transport now support notification email, including the STARTTLS custom relay evidence above. The login page’s “Forgot Password?” button has no handler and the server has no recovery route (the only reset is an administrator resetting a password). First-login placeholder email replacement remains tracked separately under #61 | Design password recovery on top of the existing SMTP settings and transport |
| Reports frontend breadth | All six API-backed views are implemented: Host Availability, Network Services, Hosts by OS, Device Services, Alerts and Notifications. Each route, period and export mapping is documented in [Reports](Frontend_Modules_and_Routes.md#reports) | Documentation reconciled in #134. Product decision: measured uptime only; availability targets and breach indicators are excluded |
| Network Health plugin section | Backend endpoint exists; current page does not call `/network-health/plugins` | Connect it when implementing the corresponding `Display_Requirements.md` section |
| Device discovery inventory | Historical docs described `/system/hosts` and port endpoints, but those routes do not exist; current Device Inventory uses latest Nagios host status | Treat the current host-status API as implemented behavior unless a separate discovery inventory contract is approved |
| Plugin lifecycle and discovery | Generation and promotion follow Plugin Manager; the reconciler attaches and detaches services on enable, disable, scan, port edit, merge/retire and NCPA events; the Plugin Manager page shows an enable preview, a Monitoring column, each plugin's monitored services with live status and stop/resume per device. The manual apply routes, `plugin-services.cfg` writing and the `plugin.configure` permission are removed | Not yet run against a live Nagios or checked in a browser: `server/tests/plans/PLUGIN_DRIVEN_MONITORING_LAB_TEST_PLAN.md` is the checklist. Held ports are shown and released from the device drawer's Ports section |
| Plugin-driven monitoring acceptance run | The 2026-10-06 live run found defects D-1 to D-8; code and plan fixes are on `fix/plugin-monitoring-acceptance-defects` but not re-run on the lab. Live status chips, browser UI, NCPA and two journeys were not run | Follow `docs/plans/Plugin_Driven_Monitoring_Remediation.md` |
| Custom plugins | `POST /api/plugin/custom` and its client call remain commented out; the Add Custom Plugin control is outside #252's scope. Plugin Manager shows only Installed Plugins, Active Capabilities and Validation Issues, in a responsive three-card row. The unused Custom Plugins and Updates Available cards and client summary fields are removed; the backend retains those counts for compatibility | Custom plugin uploads and plugin updates remain outside the release; upload-control changes are a separate decision |
| Plugins with no port | Enabling a plugin no longer applies it to every host: services are attached per discovered port, so a plugin that checks no port (`check_ping`, `check_load`, ...) attaches to nothing and cannot be enabled. Accepted: every host keeps the `check-host-alive` host check, and the response time and packet loss on the Dashboard come from it | None; confirm `check-host-alive` in the lab (plan G13) |
| Custom checks | Plugins that probe a device but need arguments (`check_by_ssh`, `check_ups`, ...) take per-device custom checks from the plugin drawer (`plugin.custom_check`); seven more port-driven plugins (`check_pgsql`, `check_ldap`, `check_ldaps`, `check_rpc`, `check_ircd`, `check_time`, `check_ntp_peer`) are in the registry and enable like `check_ssh`. Not run against a live Nagios or opened in a browser | Lab run (`docs/plans/Custom_Checks_Plan.md` phase C4). Server-local plugins (`check_apt`, `check_uptime`, `check_file_age`, ... ) take **server checks** on the Nagios server's own host; the five stock local plugins stay with Nagios Core. Passwords for `check_radius`, `check_mysql_query`, `check_nt` and `check_disk_smb` are stored encrypted (generated through protected resource slots and secure NCPA/native adapters under #129; password-bearing SMB generation is explicitly refused because its child lacks secure credential input); `check_dbi` and `check_oracle` are not available; see the plan's section 2.4. The ping family (`check_ping`, `check_icmp`, `check_fping`, `check_dig`) takes custom checks like the rest |
| Device Inventory beyond ports | The Ports section of the device drawer exists (state, reason, monitor, ignore, stop, leave suggested, resume, acknowledge, set service, remove pin). The host table shows a monitoring label (Monitored, Missing, Address unknown, Paused, Retired, Merged) with a filter that opens on Monitored, and the drawer pauses and resumes a device (`Include_Device_In_Scanning` now has a writer). A paused, retired or merged device is left out of the dashboard and Network Health counts and alerts. Identity review and merging now have an independent Needs Review table and linked device notice, comparison evidence, address history on demand, discovered-record lookup and confirmation (#164). Isolated interaction/backend regressions and [Docker real-Nagios/browser acceptance](../docs/test-runs/2026-10-15-issue-164-final-refresh/REPORT.md) pass, including the linked notice, both themes, keyboard focus, source outside Monitored and a saved merge with a configuration warning. Still API-only: `SERVICE_CHANGED` review resolution, retire and static/DHCP marking; standalone device confidence badges are not implemented | Follow-ups in `docs/plans/Device_Ports_UI_Plan.md` §10 and `docs/plans/DHCP_Device_Identity_Plan.md` §11 |
| Acknowledgement filter on host and service tables | The Dashboard Active Alerts feed and History → Alerts have an acknowledgement filter. The Device Inventory host table and the Network Status service table do not show one in the UI, although `GET` host and service list routes accept `ack_filter` and `Display_Requirements.md` §2 asks for it (found while working #239; not yet filed as separate issues) | Add the control to both tables or amend the requirement; retest TC-ACK-06 on each page |
| NCPA port per device | Installed `NCPADeployment.Port` is recorded and used by checks, probes, relocation and port protection, with a global fallback. The reversible migration backfills existing deployed rows. Isolated tests pass; actual main Nagios monitoring, authenticated probes and certificate relocation on port 5703 pass in [the finish-journeys report](../docs/test-runs/2026-10-15-issue-129-finish-journeys/REPORT.md). | No re-port UI; change deployed agents through the documented deployment workflow. |
| Manual NCPA registration (#130) | `POST .../ncpa/<id>/register` and the **Register agent** dialog with Windows install help are implemented with isolated backend and frontend tests. | Not done: probing a lab Windows host for valid disk/process node names (the issue's open scope decision), Windows-specific metric defaults the lab report in `docs/test-runs/`, and checking the help wording on the lab host |
| NCPA deployment cleanup | The permission-protected failed-only cleanup endpoint and dialog remove bootstrap artifacts, optionally the account, recheck the SSH fingerprint and report each step. Isolated backend/frontend tests pass. | Verify deliberately failed install and cleanup on a lab target. |
| SERVICE_CHANGED auto-clear | A `SERVICE_CHANGED` review item stays open after the mismatch disappears (seen when a port rule was removed); only an operator resolves it | Resolve the item automatically when the port again matches its frozen plugin |
| Per-device plugin variables and SNMP v3 (#127) | `GET/PUT/DELETE /api/system/hosts/<id>/plugin-variables/<plugin>` and a Test route; SNMP version 1/2c/3 and v3 credentials in a drawer SNMP section; v3 passphrases encrypted, written to resource slots and given to `check_snmp` on stdin. Backend and frontend tests pass (mocked Nagios and `check_snmp`). | **Not run against a live Nagios or a real `snmpd` v3 device**, and the Nagios-validated apply, the `--extra-opts` support of the installed `check_snmp`, and a lab report in `docs/test-runs/` are still to do. `check_snmp` hands the passphrases to its `snmpget` helper in argv, so they are briefly visible in the process list during a check (Engineering Standards secret rule not met for this plugin). SNMP interface discovery (`snmpwalk -v2c`) does not support v3 devices. The other plugins' variables can be set through the API; besides SNMP only the web and mail options have a form (#131). Next: a lab run with an `snmpd` v3 authPriv device, and a decision on replacing `check_snmp` for v3 with a client that reads credentials from a protected file |
| Mail and web check options (#131) | `pop3`, `pop3s`, `imap` and `imaps` definitions (`check_tcp -M crit [-S] -e`, ports 110, 995, 143, 993 added to the default Port -> Service table, nmap's TLS-wrapped POP3/IMAP named `pop3s`/`imaps`); `http`/`https` options expected text, expected status codes and request method, and a virtual host through `http_vhost`/`https_vhost`; a **Check options** dialog on monitored web and mail ports (save, reset, validation, read-only without `system.hosts.edit`). Default commands are pinned by tests. Backend and frontend tests pass (mocked Nagios). | **Not run against a live Nagios or the lab**: `nagios -v` of the new commands, a real `check_http -I/-H` and `check_tcp -e` against an OK and a wrong-response target, and the manual page in a browser. Port-level only services (SQL Server, Oracle, MongoDB, JBoss, WebLogic, Citrix) stay generic by decision; the unused `nrpe` defaults were kept (decision in `Data_Model_and_Integrations.md`). Ports monitored before the change keep their frozen `tcp` plugin until re-pinned. Next: a lab run recorded in `docs/test-runs/` |
| Check process secrecy (#129 branch) | Generated NCPA commands use an in-process resource reader for inspected clients 1.2.4/1.2.5. Supported native custom checks use extra-options stdin; tests inspect parent/child argv. Password-bearing SMB generation is refused. The restricted installer helper is wired into writes/rollback and installed on the QA appliance; service-user metadata/outside preservation and rollback pass. Four real NCPA adapter metrics matched stock results with secret-free argv. Installed full generated-config apply/reload, three main-daemon NCPA OK checks, protected hosts readability, CGI snapshots/log secrecy and real validation rollback also pass. | Non-default-port main monitoring/probes/relocation and actual failed-install cleanup also pass in [the finish-journeys report](../docs/test-runs/2026-10-15-issue-129-finish-journeys/REPORT.md). Application acceptance and review are recorded; deployment requires the paired restricted helper from [installer PR #7](https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/7), which remains a separate draft; see [the transport plan](../docs/plans/Issue_129_Check_Secret_Transport.md). |
| CI and automation | CI runs docs links, backend unit tests and frontend test/build on pull requests (`.github/workflows/ci.yml`). Drift checks cover backend routes, browser routes, client API calls, environment variables and QA traceability (`Agent_Workflow_and_CI.md`). CI uploads JUnit test results as artifacts, and sanitized lab reports go in `docs/test-runs/`. The QA journeys, master plan, traceability matrix, resumable `qa-run`/`fix-found` workflows and exact-pinned Playwright role smokes exist. Live Playwright uses a repeatable Staff account and a Docker no-network boundary with a Unix-socket bridge to the lab origin. The administrator and restricted smokes passed on the VM lab on 2026-10-11. Full J2/J3 acceptance remains partial. Not automated: deployment, installer ISO build and headless install test, a permissions drift check, branch protection | Complete the remaining live QA cases; require the CI jobs on `main`; add an installer build/install job when that repository's scope is agreed |
| Frontend lint | `npm run lint` has 0 errors and blocks CI. 25 `react-hooks/set-state-in-effect` warnings remain (the rule is set to `warn` in `client/eslint.config.js`): pages and components that set state inside effects | Refactor each (derive state, key the component, or fetch with an event/subscription), then set the rule back to `error` |
| Local lab | `scripts/lab` and `lab/` give a Dockerized appliance and five targets for QA; build, discovery, Nagios reload and `scripts/lab smoke` verified. Plugin enablement, `break`/`fix` and Nagios host/service notification dispatch were exercised for issue #113 in `docs/test-runs/2026-10-13-issue-113-notification-policy/REPORT.md`; `ui`, `sync`, actual mail delivery and NCPA install (targets have no init system) remain unverified. Not in CI | Finish the unverified commands, add plugin and alert checks to `lab/smoke.py`, then consider a CI job |
| VM control/recovery (#162) | The 2026-10-15 incident exposed two same-user VBoxSVC listening IPC socket inodes at the same pathname; the selected manager reported poweroff while inherited SSH/web listeners remained. Owner-authorized retirement removed the old configured lab VMs/disks and restored a coherent control context. New preflight and mutation gates reject duplicate controllers, VM/controller mismatch or absent runtime NAT forwarding sockets, foreign listeners and inaccessible metadata; isolated regressions pass and live rejection was observed. Owner accepted the lost dashboard/status edits as unrecoverable and authorized removing the old lab disks. Incident snapshots are not verified endpoint backups | Clean replacement appliance/base/five targets rebuilt; real SSH/HTTP marker restored from a powered-off snapshot and all nine discovery smoke checks passed ([report](../docs/test-runs/2026-10-15-issue-162-snapshot-rebuild/REPORT.md)). The setup-admin label/stale-state defect #167 is fixed with isolated command regressions: both email labels parse, and saved logins require authentication at the configured endpoint and explicitly completed setup. Corrected helper not rerun live; this appliance completed setup through the supported API |
| VM lab | `scripts/vmlab` builds a VirtualBox appliance from the stock Ubuntu ISO, snapshots Ubuntu + Nagios below the app, installs a pushed branch with the installer's own steps, and runs the installer healthcheck and a smoke test against the `demo/` targets. First run passed (healthcheck 59/0; five targets monitored; see `docs/test-runs/2026-10-08-vm-lab-first-run/`) and found #43. NCPA run (`docs/test-runs/2026-10-08-ncpa-run/`): deployment to two targets passes, but NCPA services are CRITICAL on installer-built appliances because `check_ncpa.py` needs a `python` command (#45). The installer fix (`e471a1b8`, branch `fix/check-ncpa-python3-shebang`, not merged) was inspected and one NCPA check returned OK on a partial rerun (`docs/test-runs/2026-10-08-ncpa-repeat-run/`, Partial); a later clean run (`docs/test-runs/2026-10-08-ncpa-fresh-run/`) passed the fresh install, all six NCPA services OK and the negative tests, and the installer fix is merged (`2859361d`). The run found a duplicate `Address Unknown` device record for one host (#59); the discovery start race and address-unknown matching are fixed and the fresh VM-lab repeat recorded one ACTIVE record after NCPA deployment (`docs/test-runs/2026-10-10-issue-59/`), though #86 tracks remaining duplicate persistence seen on the inherited lab baseline. Not run: alerts, `demo_lab.py break`/`fix`, `sync --client` | Fix #45 (mainly the installer), rerun the NCPA monitoring cases, then run alerts and `break`/`fix` |
| Local service restart action (#121) | Part 8.1 implemented and unit tested (fixed unit list, no shell, Maintenance Mode, cooldown and cap). Not done: Part 8.2 (sudoers drop-in with `visudo -c`, the installer code is not in this repository), Part 8.3 (remote restart; needs a design note on the on-device helper first), the lab report, and live acceptance remains tracked separately. The Remediation form now renders local and remote `unit` parameters (#182). The consumer now records Maintenance Mode as `skipped_maintenance` before the action runs (#155); the action still refuses on its own as a second guard | Add the sudoers drop-in in the installer repository, run the lab case, complete #182 live acceptance and review |
| Local service restart action (#121) | Part 8.1 implemented and unit tested (fixed unit list, no shell, Maintenance Mode, cooldown and cap). Not done: Part 8.2 (sudoers drop-in with `visudo -c`, the installer code is not in this repository), Part 8.3 (remote restart; needs a design note on the on-device helper first), the lab report, and the Remediation form does not yet render action parameters, so `unit` cannot be set from the page (API only). A Maintenance Mode refusal is recorded as outcome `failed` because a new outcome would need a frontend and migration change | Add the sudoers drop-in in the installer repository, run the lab case, render parameter fields in `ActionFormDialog.tsx`, then Part 8.3 |
| Failure escalation (#153) | Implemented and unit tested with the Nagios command layer mocked: custom notification commands, escalation module (mapping, `Notify_On`, bounded retry, restart safety, repeat window), consumer wiring, API fields, `/last-runs`, run log, form, Repeat recovery limits and the service row badge. The bell, Dashboard and History label a custom notification and show its comment (the archive holds none, so the server rebuilds it from the run that sent it); verified with the archive entry captured on a lab appliance on 2026-10-17, which also showed the service form `SEND_CUSTOM_SVC_NOTIFICATION` is accepted and logged by a live Nagios. **Lab run done** (`docs/test-runs/2026-10-18-issue-153-failure-escalation/`): a failed run, a cap skip, repeat recovery, scheduled-downtime suppression and an unwritable pipe were observed on a dummy host and service. A second lab session confirmed the automatic-run notification reached the mail command and showed the bell and Run log in a browser. **Not done:** the inbox receipt of that mail is unconfirmed, and the History Notifications tab label, run drawer and service-row badge have not been seen in a browser | Do the browser pass and confirm one automatic-run mail, then append to the report. Cap and cooldown skips notify on every blocked event by decision, so a flapping service can send several |
| Event handler framework (#120) | Implemented and unit tested (migration, registry, handler, consumer, config rendering, API, page). Run on a lab appliance on 2026-10-15 (`docs/test-runs/2026-10-15-issue-120-event-handler/REPORT.md`): a covered host's hard DOWN fired the handler through real Nagios and gave a run, repeats were skipped by the cooldown and the hourly cap, `nagios -v` passed, and the run found and fixed one defect (a recovery ran the action). A second run (`docs/test-runs/2026-10-15-issue-120-service-and-spool/REPORT.md`) added a service-scope action, forged, malformed, oversized, symlinked and replayed spool files, all handled safely. Not yet seen live: a SOFT state (needs an active check that really fails) and the page in a browser (checklist in section 8 of `docs/plans/Event_Handler_Design.md`). Two tests (a spool symlink and the file mode of the handler) are skipped on Windows and rely on Linux CI. Needs installer work in the other repository: the spool folder (`nagios:pinpoint`, 2770), the handler at `/usr/local/sbin/pinpoint-event-handler` (`root:root`, 755), and narrower rights for the `nagios` group. `restart_local_service` (#121 Part 8.1) restarts a listed host service (`nagios`) through `sudo -n systemctl restart`; it needs the installer sudoers drop-in, which is not yet written (#121 Part 8.2) | Deploy to a lab appliance after the installer pieces are applied, force a hard failure and recovery on one service, check exactly one run and the cooldown and cap skips, repeat with the installer-built spool folder and handler, a live SOFT state and a browser walk-through; add `restart_local_service` in #121 |
| Resource forecasts (#156) | Display only: `app/forecast.py` (straight-line fit over 72 hours of hourly averages for NCPA disk and memory percent), the `resource_forecast` job every 30 minutes, `RESOURCE_FORECAST` (migration `b7e2a9c4d518`), `GET /api/system/forecast` (`system.dashboard` or `system.services`), the Dashboard "Running out soon" list and a badge on the service table; unit tests cover the fit, the job (canonical NCPA full/short labels and exclusions, numeric crossings, replacement, paused devices, exact-tuple cap, constant mixed-row query count, rotating batches and failed-commit retry), the route, the migration and the UI states. Not done: notifying on a forecast with a horizon and on/off setting and their Settings page controls (decided out of scope on 2026-10-17; needs #132 and #153), native `check_disk` metrics, and the lab comparison of a forecast with a real disk fill (`docs/test-runs/`) | Open a follow-up issue for forecast notifications; run the lab fill test on an appliance |
| Local service restart action (#121) | Part 8.1 implemented and unit tested (fixed unit list, no shell, Maintenance Mode, cooldown and cap). Not done: Part 8.2 (sudoers drop-in with `visudo -c`, the installer code is not in this repository), Part 8.3 (remote restart; needs a design note on the on-device helper first), the lab report, and live acceptance remains tracked separately. The Remediation form now renders local and remote `unit` parameters (#182). A Maintenance Mode refusal is recorded as outcome `failed` because a new outcome would need a frontend and migration change | Add the sudoers drop-in in the installer repository, run the lab case, complete #182 live acceptance and review |
| Event handler framework (#120) | Implemented and unit tested (migration, registry, handler, consumer, config rendering, API, page). Run on a lab appliance on 2026-10-15 (`docs/test-runs/2026-10-15-issue-120-event-handler/REPORT.md`): a covered host's hard DOWN fired the handler through real Nagios and gave a run, repeats were skipped by the cooldown and the hourly cap, `nagios -v` passed, and the run found and fixed one defect (a recovery ran the action). A second run (`docs/test-runs/2026-10-15-issue-120-service-and-spool/REPORT.md`) added a service-scope action, forged, malformed, oversized, symlinked and replayed spool files, all handled safely. Not yet seen live: a SOFT state (needs an active check that really fails) and the page in a browser (checklist in section 8 of `docs/plans/Event_Handler_Design.md`). Two tests (a spool symlink and the file mode of the handler) are skipped on Windows and rely on Linux CI. Needs installer work in the other repository: the spool folder (`nagios:pinpoint`, 2770), the handler at `/usr/local/sbin/pinpoint-event-handler` (`root:root`, 755), and narrower rights for the `nagios` group. `restart_local_service` (#121 Part 8.1) restarts a listed host service (`nagios`) through `sudo -n systemctl restart`; it needs the installer sudoers drop-in, which is now merged in the installer repository (#121 Part 8.2). `restart_remote_service` (#8 Part 8.3) restarts a unit from a per-device list on a trusted, Active, unpaused device through a second root-owned helper installed by the NCPA bootstrap; it is unit tested with SSH mocked, security reviewed in #182 with fingerprint-race and exit-status-timeout regressions; fresh-VM real SSH/systemd restart, changed-key/on-device-list/refusal/deadline cases, helper privileges and audit-ID reuse passed on 2026-10-17 ([report](../docs/test-runs/2026-10-17-issue-182-remote-restart/REPORT.md)); the subsequent [Playwright walkthrough](../docs/test-runs/2026-10-17-issue-182-playwright/REPORT.md) passed settings/persistence/errors, real cleanup/redeployment, action unit fields and real read-only permissions; human review remains pending. Existing devices need cleanup/redeploy to receive the helper, and a changed list reaches a device only through cleanup/redeployment (only root can write it there). The NCPA Deployment settings dialog and remediation `unit` controls are included; trusted deployed devices support cleanup with an explicit redeployment warning. The run action link is a nullable foreign key, preserving audit snapshots while preventing replacement actions from inheriting deleted-action limits | Deploy to a lab appliance after the installer pieces are applied, force a hard failure and recovery on one service, check exactly one run and the cooldown and cap skips, repeat with the installer-built spool folder and handler, a live SOFT state and a browser walk-through; add `restart_local_service` in #121 |
| Per-service Recover automatically (#154) | Implemented and unit tested: the route (400 for any unit, command or path, limit 1 to 6, 409, 422, 403), the server's choice of action and unit by check name against each device's own restart list, the drawer control and the Network Status mark. Service names map to units by their first word and a small fixed alias table, so a check that matches no listed unit shows a disabled switch with the reason. Not run on a lab appliance or in a browser. Remote services depend on the same installer and device pieces as `restart_remote_service` | Walk it through on a lab appliance: switch it on for one service, force a failure, see one run and the cooldown and cap skips, then switch it off and check the handler leaves the config |
| Installer | Developed in another repository | Keep installer work out of this repository unless scope changes |

## Test approach status

The [module black-box catalog](../docs/qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md)
contains 231 TC cases plus eight E2E scenarios. The shared `scripts/qa_catalog.py`
parser validates definitions, run phases, requirement mappings and full procedures.
It preserves original human verdicts and flags 26 conflicting summary/detail
verdicts plus one free-text observation. No human result was reconciled by inference.

`scripts/qa_queue.py` now prepares/checks version-2 module/person queues and Markdown
previews with exact IDs, exclusions, case snapshots and fixed batches. Ordinary
batches have up to five TC IDs; disruptive/fresh/long/E2E cases are isolated and a
session may open at most five batches. `scripts/qa_execute.py` is an offline-only
session/card/result validator: owner/start attestations, immutable scope/adapter
hashes, ordered action slots, evidence completeness and cleanup halt. It performs
no live command dispatch or preflight and cannot constrain an agent with arbitrary
shell/file access. Empty/missing cards remain blocked. Live scan guarding,
recovery/resume orchestration and complete current-case browser adapters remain
unimplemented; no unattended-readiness claim is made.
The [source coverage register](../docs/qa/Automation_Coverage.md) accounts for all
239 definitions: seven source-complete permission adapters, 232 unmapped.
The two new untested adapters are TC-ACC-09 (page denial plus API 403 as
independent E1/E2 items) and TC-NCPA-08 (page denial). Their source-complete
status does not authorize execution. `qa_pilot.py run` now implements a fixed
serial batch for only TC-SS-04, TC-ACC-09 and TC-NCPA-08, with independent private
resources, per-case durable results and stop on non-PASS. `qa_pilot.py handoff`
separately checks complete supervisor-backed PASS/cleanup/evidence/baseline before
archiving the exact old ledger and appending the new queue; no prior attempts,
recoveries or budgets are cleared. Concrete cards, current proof, handoff review
and a new explicit start are required. The new two cases have not run. See the
[next batch review](../docs/qa/Next_Permission_Batch_Review.md).
`qa_coverage.py` validates hashes/review/item coverage and binds cards to exact
selection. `playwright.qa.config.ts` has one worker, zero retries, no setup
dependencies/captures and private unique outputs; offline collection is checked.
The isolated launcher now has a JSON-only `--qa-preview` for the selection/output
contract, validated against one unconsumed opened journal case. Its proposed mounts
keep source/root read-only and expose separate private evidence and only two Staff
credential files, with no credential value reads during preparation. Nine synthetic
transport tests cover stale scope, slot/budget/state, private paths, forbidden
config fallthrough and offline/live distinction. The legacy runner still rejects
the new config; only the narrow pilot entry below adds gated live integration.
Other live cases remain blocked. No new case result
is claimed. See [adapter preparation](../docs/qa/Automation_Readiness.md). Review-only `investigate`
queues now retain human partials for mandatory evidence/issue triage and reject
product case opening. The [partial-pass register](../docs/qa/Partial_Pass_Investigations.md)
links reported confirmation defect #208 and unexplained-result clarification #209;
neither is a fresh runtime reproduction.

`scripts/qa_supervisor.py` now implements the driver-independent lifecycle core:
separate start grant, cooperative lab UUID lock, private atomic/fsynced ledger,
durable pre-dispatch consumption, persistent batch budgets/replay rejection and
halted interruption/cleanup states. Sixteen synthetic-driver regressions include
proof drift, prior-offline-result rejection, failures and no secret exception
persistence. The core has no default driver; the narrow pilot entry is described
below. Actual deployment/controller
proof and full production process/parser/recovery integration remain pending;
elapsed checks cannot interrupt a hanging
Python callback. This does not authorize or demonstrate live case execution.

The runtime components `qa_process.py` and `qa_results.py` now exist with eight
local Python-process and nine synthetic-report regressions. The process helper
bounds time/output, preserves private non-overwriting logs, cancels its owned
POSIX group and halts on uncertain cleanup. The parser validates one reviewed
permission attempt/configuration and copies only fixed item observations; it
requires full PASS and cleanup evidence, otherwise preserves INCONCLUSIVE.
Their narrow pilot wiring is described below; broader running frontend/backend
revision proof, inherited controller/driver wiring, bridge/container-ID lifecycle (daemon work
can outlive its CLI), recovered baseline and live validation remain pending.

`qa_control.py` now coordinates mutating `vmlab` entries and supervisor claims
through one fixed private per-user host flock, including across different ledger
roots. Six local lock/controller fixtures verify exclusion, inherited-descriptor
checks and pre-configuration gating. Direct controllers, other users/namespaces
and legacy browser launchers remain outside the cooperative mechanism. Seven new
preflight contracts cover structured read-only observations and identity drift;
`vmlab preflight --json` explicitly carries no live authorization, target revision,
running application/frontend proof, baseline or restoration claim. No lab was
contacted or acceptance result added by these fixture tests.

`qa_container.py` adds the concrete bounded create/attach/inspect/kill/remove
component with 16 synthetic-command contracts. It binds a pinned image and exact
transport digest to a durable consumed supervisor slot, fsyncs intent before
creation, verifies actual container identity/isolation and proves absence through
a successful daemon query. Uncertain create/cleanup and persisted intent block
retry; child commands use private umask. It has no CLI/default production driver.
Production bridge wiring, running application/frontend identity, Staff
baseline, session recovery and reviewed live cards/start remain pending.

Seven frontend selection/collection/synthetic-worker checks now include a fixed
worker-reload defect that collection-only checks missed. Real Playwright IPC
workers may see their private artifact directory after initial configuration;
environment markers alone cannot allow evidence reuse. No page/browser, appliance
or acceptance adapter executes in the worker fixture. The user prioritized a
TC-SS-04 pilot today, later authorizing appliance setup and read-only inspection;
no acceptance case ran. The narrow pilot entry is described below.

`qa_bridge.py` now implements the owned private relay: consumed transport and
retained host-lock binding, same-user peers, fixed loopback origin, bounded time/
connections/bytes/buffers, durable intent and joined cleanup with socket custody.
Eleven Unix-only fixture tests pass; the container component also verifies bridge
custody and has an integration fixture with no upstream connection or Docker.

Standalone `qa_deployment.py` adds expected Git-object source/build manifests and
stable public artifact/candidate-process observations. Six disposable Git/file/
proc fixtures pass without SSH, real backend processes or an appliance. Observer
runtime/served readiness stays false and verified running revision stays null:
disk matches/start ordering alone cannot attest loaded code or actual served bytes.
The narrow `qa_pilot.py` integration now composes these components for TC-SS-04
only. Twelve isolated driver/proof/gate contracts and read-only actual appliance
inspection pass; 455 source files and 2383 installed runtime files are bound to
the reviewed controlled deployment. Inspection launches no browser/container.
The first explicitly started v4 TC-SS-04 attempt ran once on target `299ab3b`:
browser permission assertions and logout/401 passed, container/bridge removal
completed and independent post-run baseline inspection passed. Overall result is
INCONCLUSIVE because the parser rejected an E1 timestamp 44 ms beyond its computed
attempt end; harness [#211](https://github.com/esfen14/Pinpoint/issues/211) tracks
the offline bounded attach-window fix and pinned-worker timing investigation
([timing rule](../docs/qa/QA_Report_Timing.md)). Import and composed-driver
regressions accept the synthetic 44 ms relationship and halt on stale/foreign or
failed-cleanup evidence. The original v4 result remains INCONCLUSIVE; its halted
attempt, exact private ledger archive, evidence and original budgets are preserved.
See the [original pilot report](../docs/test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md).

After separately approved implementation/use, `qa_pilot.py recover` obtained fresh
cleanup/baseline proof and appended an expiring grant-bound audited disposition,
preserving original attempts/budgets and permitting only the named v2 queue. Paeng
separately explicitly started that one-case recheck. The real TC-SS-04 attempt on
the same target passed through strict fresh import, logout/401, owned container/
bridge/process cleanup and fresh post-case baseline proof. Its E1 was 47 ms beyond
the old invalid duration-derived end, accepted by actual independent attach bounds
without grace. The supervised v2 attempt is complete/PASS/restored; the serialized
source journal retains an active label with no active case/batch and one accepted
result. See the [recheck report](../docs/test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md).
Broader/unattended coverage stays blocked. Controlled launch/build provenance is a
trust boundary, not memory attestation. The standalone observer's negative
readiness fields are unchanged.

The [historical evidence inventory/review](../docs/qa/Historical_Evidence_Review.md)
links 41 post-cutoff-directory-date reports and six partial current-case mappings.
October 15 remains a provisional cutoff. No full-case inherited PASS is accepted.
`scripts/qa_evidence.py` validates reviewer-bound target/report/case hashes and
item-level coverage before full reuse. The requirement validator, derived
[case status view](../docs/qa/QA_Case_Status.md), and docs gate now use the new sources
instead of the removed journey plan, matrix and paper tables.

Issue #214 adds source-reviewed, offline-collection-only adapters for
TC-ACC-08, TC-ROL-04, TC-DI-02, TC-DI-03, TC-DI-07, TC-DI-08, TC-HIS-04 and TC-DASH-07, plus partial TC-ACC-10
coverage for E1/E2. Together with the seven permission adapters, the source coverage
register now has 15 implemented mappings, one partial mapping and 223 unmapped
entries across 239 current cases/scenarios. The supervised live pilot accepts seven
complete read-only module IDs in addition to its three permission IDs; TC-DI-07 is
excluded pending resolution of its uppercase expectation discrepancy and failure-result handling. This
does not add a general live launcher or runtime results. The October 18 supervised reports record
complete PASS/restored outcomes for TC-ACC-09 and TC-SS-04; their original catalog
Result fields remain unchanged under the QA workflow, and both IDs are excluded
from the replacement untested queue.

Backend tests are organized under `server/tests/unit/`, `integration/`, `e2e/`,
`support/`, and `plans/`. Default pytest collection is isolated. The deterministic
browser-to-Nagios approach is recorded in
[`TEST_APPROACH_ADJUSTMENT_PLAN.md`](../server/tests/plans/TEST_APPROACH_ADJUSTMENT_PLAN.md)
as **Proposed — implementation deferred pending fixes**. Missing UI workflows,
complete orchestration and automatic disposable-instance recovery are not yet
implemented; existing harness improvements do not satisfy full acceptance.

## Explicit exclusions

- Automatic topology/parent inference, physical interface mapping and topology
  interface/traffic panels are excluded. Manual multiple-parent topology is in
  scope; graph positions are automatic and cannot be edited.
- Nagios' native UI is not a Pinpoint operator surface.
- Plugin Manager does not install arbitrary agents or plugins on monitored
  devices; it manages plugins on the Pinpoint/Nagios server.

## Status maintenance

When completing an item above, update this file in the same change. When a new
route, page, model, or workflow lands, also update its owning architecture or
catalog specification. Do not preserve stale “not built” notes after the code is
implemented.


## NCPA metric refinements (#128)

The default metric table preserves CPU, memory and per-partition disk and adds
swap percent and sda read/write rates. Agent inventory probes at configuration
time skip unsupported paths individually; unreachable inventories defer the added defaults
with a retry reason and preserve established checks. Settings → Plugins offers a guided exact process-count row
for review before saving. Existing saved tables are unchanged until reset.
NCPA 3.5.0 capability probes found no load-average node, so that default remains
unavailable. Two-target Docker acceptance observed all six defaults and the exact process
check OK, omitted an unsupported path with persisted skipped reasons, and
measured small-lab Nagios load. Installation, independent-host scale and browser
walkthrough remain unverified; see [the service report](../docs/test-runs/2026-10-14-issue-128-ncpa-services/REPORT.md)
and [the capability report](../docs/test-runs/2026-10-14-issue-128-ncpa-probe/REPORT.md).

## Host reports for a period with no data (#229)

Host Availability and Hosts by OS now say "No data in this period" when no listed host has
recorded state time, instead of showing a table of dashes, and Host Availability no longer
shows the success banner in that case. The wording still differs between the six tabs (see
[Reports](Frontend_Modules_and_Routes.md#reports)); the lab re-run of TC-RPT-06 on a deployed
build is pending.

## Host-report current state (#228)

Host Availability and Hosts by OS now show each host's current state, last check and
last state change from one bulk Nagios `hostlist` read joined to the archive durations
(`app/nagios/host_current_status.py`); before, these were always `Unknown` and empty
because the archive row does not carry them. Host Availability lists only hosts of
currently monitored devices. Not covered: a host monitored earlier in the period but
not now is not listed, Hosts by OS keeps its own row set, and the lab re-run of
TC-RPT-01 on a deployed build is pending.

## Host report duration wording (#240)

Host Availability and Hosts by OS rows now expose `known_seconds` (up + down + unreachable
seconds from Nagios) instead of the legacy `total_snapshots`. Host Availability shows and
exports it as `Known Time (seconds)`. The unreachable pre-Nagios snapshot code in the
Hosts by OS route was removed. Isolated backend and frontend regressions cover the field
and label; no live-lab run has been made.

## Service-report availability (#198)

The issue branch replaces Network Services and Device Services snapshot counting
with a shared strict Nagios duration reader, including scheduled components and
separate native/unaccounted missing coverage. Current status is fetched in one
separate bulk read; no status is inferred from availability. Both service-report
contracts, tables and exports remove snapshot counts and expose seconds. Owning
backend/data/frontend specifications and the [operator guide](../docs/manuals/Service_Reports.md)
define exact semantics, completed-second windows, retention and Core assumptions.
No snapshot storage or general polling behavior is removed. The full local gate passes (4040 backend/922 frontend; 14 existing skips), with
51 focused service regressions and two Chromium tests for both views and all
exports. The [final comparison](../docs/test-runs/2026-10-17-issue-198-service-availability/REPORT.md)
records installed Core 4.5.11 real brief-outage/missing-history agreement with
native avail.cgi, small-inventory timings, and a corrected harness socket-isolation
failure/recovery. Large real inventories, installer upgrade and production HTTP
authentication remain untested; CI and human review are tracked on PR #201.
The initial [contract probe](../docs/test-runs/2026-10-17-issue-198-contract-probe/REPORT.md)
is historical partial evidence, not final acceptance.


## Dashboard stopped/stale Nagios indication (#238)

Top-page and Service Overview alerts explain stale data and frozen host/service
states when Nagios is stopped. Stale/missing timestamps show monitoring status
unavailable rather than presenting a recorded PID as live proof. Age is checked
independently of the browser refresh mode; fresh status clears the warning.
Historical TC-DASH-06 FAIL is preserved; the separate issue retest report records
fresh observations without replacing catalog evidence.

[Separate #238 Docker retest](../docs/test-runs/2026-10-19-issue-238-nagios-stale-warning/REPORT.md) records refresh texts, actual stop/restart, both warnings and restoration.
