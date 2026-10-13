# Nagios Core Feature-Gap Plan for Pinpoint

**Audit date:** 2026-10-13 · **Revised after `git pull` and a read-only inspection of a live appliance VM (`pinpoint-2`, `main` at `d4df736`)** (branch `issue-62-qa-journeys-test-plan` at `c9414d41`, which includes `main` as of 2026-10-10) · **Method:** code and specification reading, plus read-only commands on one live appliance (marked "VM-verified"). No application code was changed and **no test suite was executed.** "Fully Implemented" therefore means "present and complete in the code read", not "proven by a test run".

---

## 1. Executive Summary

Pinpoint is deliberately **not** a Nagios replacement. `spec files/System_Overview_and_Architecture.md` says Nagios Core stays the monitoring engine, and Pinpoint discovers devices, generates Nagios configuration, polls Nagios's JSON CGIs, and presents the results. So parity with Nagios Core means two things:

1. Pinpoint **generates** the Nagios configuration that switches a Nagios capability on.
2. Pinpoint **exposes** that capability to operators, who are told not to use Nagios's own UI.

Most gaps below are the *generated config being thinner than Nagios's capability*. The generator writes fixed templates with no parents, escalations, event handlers, dependencies or user-defined notification periods.

### Feature totals (55 rows on the official page)

The official page has 55 bullets in 8 categories. "Performance Data" appears under two categories, so there are 54 unique names and 55 rows.

| Status | Count |
|---|---|
| Fully Implemented | 16 |
| Implemented but Needs Refinement | 9 |
| Partially Implemented | 12 |
| Not Implemented | 9 |
| Unverified | 0 |
| Not Applicable | 9 |
| **Total** | **55** |

These totals match the Section 2 table row by row. **21 issues** are raised (Section 3).

### Development issues

Each issue below is expanded into engineering-ready tickets in [`docs/issues/`](issues/README.md), split into independently deliverable sub-issues (for example `Issue #19.1`). Writing them corrected three statements in this plan, which are fixed in place: `check_pop` and `check_imap` are not in the bundled catalog, the per-device `Plugin_Variables` override has no writer, and PinPoint stores no SSH password.

### Scope decisions applied (team, 2026-10-13)

- **No custom applications or plugins.** They need security controls Pinpoint does not have. Simple Plugin Design, Community Plugins and Any Language are therefore Not Applicable, and Custom Application counts only the custom checks that run bundled plugins.
- **No NRPE.** Pinpoint uses NCPA. Remote Execution counts NCPA and SSH only, and the Windows gap is about NCPA onboarding.
- **No third-party integrations.** Third-Party Tools is Not Applicable. I extended this to API Integration, the Performance Data export row (Grafana, InfluxDB, Prometheus), and SMS or chat notification gateways. I also treated Custom Alert Scripts as out of scope for the same security reason. **These extensions are my assumption, so please confirm them.**
- **Issue #21 awaits clarification** (see its entry). It is left in place and flagged.

### Major architectural gaps

- **No control path from Pinpoint to Nagios at runtime.** No code writes to the Nagios command pipe or `cmd.cgi`. Pinpoint's alert acknowledgement is stored only in `system.db`, so Nagios keeps notifying. Scheduled downtime can be displayed but not created. (Issue #19)
- **Generated config omits whole Nagios object features:** `parents`, `hostescalation`/`serviceescalation`, `hostdependency`/`servicedependency`, `event_handler`, and timeperiods other than `24x7`. (Issues #1, #3, #4, #5, #7)
- **Email delivery is narrow.** Email and the in-app feed are the alert channels. Delivery exists through Settings → Email (Gmail only, via the appliance's root helper), but there is no other provider, and the helper exists only on installed appliances. (Issue #2)
- **Single-host design:** in-process APScheduler, SQLite, one Nagios. No redundancy. (Issue #12)

### High-priority opportunities that improve what already exists

- Issue #19 (Nagios command channel). It unblocks acknowledgement propagation, downtime and "check now".
- Issue #1 (notification policy and the misleading Notifications setting).
- Issue #2 (broaden mail delivery beyond Gmail and verify the helper path).
- Issues #6, #15, #20 (surfacing and configuring things the backend already collects). Issue #21 is provisional.

### Changes found when the repository was updated

The pull (about 47 application files) changed four findings, and the report below reflects them:

- **Mail delivery now exists (Gmail only).** `server/app/smtp_settings.py`, `api/system/smtp_settings.py` and Settings → Email (`EmailSettings.tsx`) configure `msmtp` through a root helper and send a test email. `Implementation_Status.md` records the VM-lab check. Issue #2 is narrowed accordingly.
- **Alert recipients are now per user.** `User.Receive_Email_Alerts` (permission `account.alerts`) decides who becomes a Nagios contact. Per-host recipients are the open issue #79 and are covered by Issue #3.
- **Check interval is now a setting** (`SystemSettings.Check_Interval`, 1/2/5/10/15 minutes, applied through `regenerate_and_apply_config_status()`). Retry interval and `max_check_attempts` are still fixed, so Issue #10 is narrowed, not closed.
- **Unchanged:** no event handlers, parents, escalations, dependencies, command channel, downtime creation, log rotation or metrics export were added. All Not Implemented rows stand, and the totals are unchanged.

### Live-appliance verification (read-only, 2026-10-13)

I connected to one installer-built appliance (`pinpoint-2`, Nagios Core 4.5.11, Pinpoint `main` at `d4df736`, six discovered hosts, no plugin services enabled) and only read files and logs. What it showed:

- **Flap detection is on for generated objects.** `nagios.cfg` has `enable_flap_detection=1` with thresholds 5.0 (low) and 20.0 (high) for hosts and services. The resolved `objects.cache` entry for the generated host `gateway` has `flap_detection_enabled 1` and `flap_detection_options a`. Pinpoint only displays this. It cannot tune it.
- **Nagios event handlers are enabled globally** (`enable_event_handlers=1`), but no generated object has an `event_handler`. Nothing is hooked up.
- **The command pipe is reachable by Pinpoint.** `/usr/local/nagios/var/rw/nagios.cmd` is `prw-rw---- nagios:nagios`, `check_external_commands=1`, and the `pinpoint` service user is in group `nagios`. Writing commands directly needs no extra privilege.
- **The CGI route to commands is not.** `cgi.cfg` authorizes commands (`authorized_for_all_service_commands`, `..._host_commands`, `..._system_commands`) only for `nagiosadmin`. `htpasswd.users` contains only `pinpoint-api`, which has read access only.
- **Nagios rotates its own log daily** (`log_rotation_method=d`, archives in `/usr/local/nagios/var/archives`). Pinpoint's Gunicorn writes to stdout, so its logs go to journald with no overrides in `journald.conf` (40 MB in use). Installer logs in `/var/log/pinpoint-*.log` are small and are not in `logrotate.d`.
- **Mail was not configured on this VM.** `/etc/msmtprc` is empty, and `nagios.log` shows the notification for `gateway` failing (`account default not found in /etc/msmtprc`, exit code 78). Nagios logs this failure; I found nothing in Pinpoint that surfaces it.
- **Sudo scope is narrow:** `pinpoint` may run only the SMTP helper and `systemctl reload nagios`.

### Correction to the preliminary document

`Backup Documents from Nagios.pdf` says "Event Handler Attempt Fix: this is mostly in the system/PinPoint along with the Proactive Resolution". **The repository does not support this.** No `event_handler` appears in any template or generator, and no remediation code exists. Event handlers are classified Not Implemented (Issues #7, #8). The PDF's other claims were checked: parallel checks are a Nagios capability (confirmed), scheduled operations are partly present (Issue #9), and Pinpoint has no log-file rotation of its own (Issue #11), although journald bounds the service's logs by default.

---

## 2. Nagios Core vs. PinPoint Feature Comparison

Paths are relative to the repository root. `tpl` = `server/app/network_discovery/templates/`.

### Network Monitoring

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Network Services | `server/app/network_discovery/plugin_registry.py` → `PLUGIN_DEFINITIONS` maps discovered ports to `check_http`, `check_ssh`, `check_smtp`, `check_ftp`, `check_dns`, `check_snmp`, `check_ldap` and others. Created by `create_host_cfg.py` → `build_host_services()`. Enable per plugin in the Plugin Manager page (`/plugins`). | Fully Implemented — No issue required. |
| Network Protocols | TCP: `check_tcp` (also the generic fallback). UDP: `check_udp`. ICMP: the host check `check-host-alive` in `tpl/host.cfg.tpl`. `check_ping`, `check_icmp` and `check_fping` are available as custom checks (`custom_checks.py` → `CUSTOM_CHECK_FIELDS`). | Fully Implemented — No issue required. |
| Bandwidth Monitoring | `server/config.py` → `SNMP_OIDS` defaults include `lan_in_octets` and `lan_out_octets`, hardcoded to interface index `.3`, editable in Settings → Plugins. Values are stored as `ServicePerfData`. No rate is computed. | Issue #13 — Raw counters on one fixed interface. No bits/s calculation, interface selection or utilisation view. |
| Device Availability | Host check `check-host-alive` per device. Host status goes to `history.db` (`HostStatus`). Shown on the Dashboard and in Device Inventory (`/device-inventory`, `HostTable.tsx`). | Fully Implemented — No issue required. |
| Network Host Hierarchy | Not found in the inspected repository. `tpl/host.cfg.tpl` has no `parents`, and no model stores a parent link. Because of that, Nagios can never report UNREACHABLE for a Pinpoint-generated host. The UNREACHABLE state is only counted (`api/system/statistics.py` → `host_counts()`). The spec explicitly excludes topology (`Implementation_Status.md` "Explicit exclusions"). | Issue #4 — Parent host relationships absent. Needs a scope decision, because parents are not the excluded topology view. |
| SNMP Monitoring | `plugin_registry.py` → `snmp` definition (`check_snmp`, `-C community`, `-o oid`, `-P` protocol option). `config.py` → `SNMP_COMMUNITY_STRING` defaults to `"public"`. OID table editable via `PUT /api/system/plugin-settings/snmp`. No v3 arguments (user, auth or privacy) are defined. Whether `-P` can be set from the UI is unverified. | Issue #14 — v1/v2c only in practice. v3 not supported. Community is a global default. |
| Network Discovery | `server/app/network_discovery/network_discovery.py` (nmap host, TCP and UDP scans). Identity tracking in `device_identity.py`. Scheduled via `automation.py` (`Scan_Frequency`). Start from the Dashboard rescan button (`RescanButton.tsx`) or Settings. | Fully Implemented — No issue required. |

### Server & Host Monitoring

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Processor Load | Remote: NCPA metric `cpu` (`cpu/percent`, `aggregate=avg`) in `config.py` → `NCPA_METRICS`. Server only: stock `localhost.cfg` services. No load average on remote hosts by default. | Issue #15 — Percent only. No load average default. |
| Disk Usage | NCPA metric `disk` (`disk/logical/{partition}/used_percent`), one service per recorded partition (`NCPADevicePartition`). Mount points are covered. | Issue #15 — Disk I/O not monitored by default. |
| Memory Monitoring | NCPA metric `memory` (`memory/virtual/percent`). | Issue #15 — No swap metric. No leak or growth trend. |
| Process Monitoring | Server-side `check_procs` results are read by `api/system/network_health_activity.py` (System Activity card). Remote process checks are possible only by hand-adding an NCPA path in Settings → Plugins. There is no default and no guided "this process must run" form. | Issue #15 — Partial. No operator-friendly process check. |
| Linux/Unix Servers | NCPA installed over SSH (`server/app/ncpa_deployment/ncpa_deployment.py`, NCPA Deployment page `/ncpa-deployment`). The remote helper uses systemd, so Linux is supported. Other Unix is unverified. | Issue #16 — Known gaps in `Implementation_Status.md`: one global NCPA port, no cleanup action, and the token is visible in process listings. |
| Windows Servers | `check_nt` (NSClient++) exists as a **custom check** only (`custom_checks.py`). Pinpoint's chosen agent is NCPA, which is cross-platform, but its deployment workflow is SSH/Linux only (`server/app/ncpa_deployment/ncpa_deployment.py`), and no Windows NCPA onboarding was found. NRPE is not used and is out of scope (team decision). | Issue #17 — Partial. No Windows onboarding for NCPA. |
| Resource Utilization | Dashboard `ResourceUtilizationSection.tsx` and Network Health `ResourceUsageCard.tsx`, `CpuUtilizationChart.tsx`. APIs `/network-health/cpu`, `/network-health/plugin-trends`, `/dashboard/status`. | Fully Implemented — No issue required. |

### Application & Service Monitoring

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Database Servers | Port-driven: `check_mysql`, `check_pgsql` (`plugin_registry.py`). Custom: `check_mysql_query`. Not available: `check_dbi` and `check_oracle` (`custom_checks.py` marks them "credentials"). Not found: SQL Server and MongoDB checks. | Issue #18 — Partial. |
| Web Servers | `check_http` for http and https ports, with a `url` option. HTTP availability covers Apache, Nginx, IIS and Tomcat as Nagios does. | Fully Implemented — No issue required. |
| Mail Servers | SMTP: `check_smtp`. POP3 and IMAP get no protocol-aware check, only the generic `check_tcp` fallback. | Issue #18 — Partial. |
| Directory Services | `check_ldap` and `check_ldaps` are port-driven. Nothing is specific to Active Directory. | Issue #18 — Partial. |
| Application Servers | Only generic `check_tcp` or `check_http` on discovered ports. No JBoss, WebLogic or Citrix specifics. | Issue #18 — Partial. |
| Custom Application | Custom checks over the bundled plugin catalog: `server/app/api/plugin/custom_checks.py`, `network_discovery/custom_checks.py`, `plugin_manager/CustomCheckDialog.tsx`, `docs/manuals/Custom_Checks_Manual.md`. Custom application plugins are out of scope (team decision: they need security controls), so the upload route stays disabled (`POST /api/plugin/custom` is commented out in `manager.py`, and the UI button is greyed out). | Fully Implemented — No issue required. Within scope: custom checks over bundled plugins. |
| API Monitoring | `check_http` accepts a `url`. No JSON or body validation, authentication headers or API-specific form. | Issue #18 — Partial. |

### Alerting & Notifications

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Contact Notifications | `create_host_cfg.py` writes a contact for each Active user with `Receive_Email_Alerts` on, in a single group `system_users` (no group is written if nobody qualifies). `tpl/contact_template.cfg.tpl` notifies on warning, unknown, critical, recovery, flapping and downtime, so recovery notifications are included. Mail is sent through the appliance's `msmtp` helper configured in Settings → Email (`smtp_settings.py`, Gmail over STARTTLS only). VM-verified: until that is configured, Nagios's notification fails (`/etc/msmtprc` empty) and only `nagios.log` records it. The Pinpoint acknowledgement (`api/system/dashboard.py` → `acknowledge_alert()`) writes only `AlertAcknowledgement`/`AckHistory`. No call to Nagios was found. | Issue #2 — Gmail-only mail delivery. Issue #1 — notification periods and options are not user-controlled. Issue #19 — acknowledgement does not stop Nagios notifications. |
| Multiple Methods | Email through the contact template commands (`notify-service-by-email`, `notify-host-by-email`), sent through Gmail (Settings → Email), plus Pinpoint's in-app notification feed (`api/system/notifications.py`, header bell in `Header.tsx`). Pager, SMS and user-defined commands are not provided. SMS and chat gateways are third-party integrations, which are out of scope (team decision). | Fully Implemented — No issue required. Within scope: email and in-app. |
| Escalation Paths | Not found in the inspected repository. Every host and service uses the one `system_users` contact group; per-host recipients are the open issue #79. No `hostescalation` or `serviceescalation` is generated. | Issue #3 — Not implemented. |
| Time-Based Alerting | `24x7` is hardcoded in `tpl/host.cfg.tpl`, `service.cfg.tpl` and `contact_template.cfg.tpl`. No timeperiod model or UI. | Issue #1 — Not implemented. |
| Notification Dependencies | Not found. No `hostdependency` or `servicedependency` is generated. | Issue #5 — Not implemented. |
| Flap Detection | Read-only. Nagios state is stored (`history_models.py` → `Is_Flapping`, `ProgramStatus.Enable_Flap_Detection`). It is shown on the Dashboard (`ServiceOverview.tsx`), in Device Inventory (`HostTable.tsx`, `StatusDetailDrawer.tsx`) and System Status. The Insights card also mentions flapping (`network_health_activity.py`). Templates set no flap options, and VM-verified: the generated host resolves to `flap_detection_enabled 1` under the global 5%/20% thresholds. | Issue #6, Issue #10 — Displayed but not configurable, with no flap history. |
| Custom Alert Scripts | Not found. No notification command other than the two email commands. Arbitrary notification scripts are a security-sensitive extension of the same kind as custom plugins, which are out of scope (team decision). | Not Applicable — Out of agreed scope (assumption, confirm). No issue required. |

### Event Handlers & Automation

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Event Handlers | Not found in the inspected repository. No `event_handler` in any template, `create_host_cfg.py`, or the plugin registry. (Contradicts the preliminary PDF.) | Issue #7 — Not implemented. |
| Proactive Resolution | Not found. Pinpoint only observes. The failure-attempt data it stores (`Current_Attempt`, `Max_Attempts`, `Last_State_Change`) is displayed and never acted on. | Issue #7 — Not implemented. |
| Service Recovery | Not found. No restart or remediation action, and no remediation log. | Issue #8 — Not implemented. |
| Parallelized Checks | Provided by Nagios Core, which schedules and forks checks. Pinpoint generates one service per port or metric and does not execute checks. Pinpoint's own poll is a single job (`scheduler.py`, `max_instances=1`, every 60 s). | Fully Implemented — No issue required. |
| Scheduled Operations | Pinpoint operations are scheduled (`server/app/automation.py`, `scheduler.py`): scans, plugin update checks, security validation, daily DB backups (7 kept), retention purge. A "Maintenance Mode" switch pauses Pinpoint's own jobs (`SystemSettings.Maintenance_Mode`, `MaintenanceBanner.tsx`). It does **not** create Nagios downtime. Downtime is only displayed (`Scheduled_Downtime_Depth`). | Issue #9 — Partial. No maintenance windows, and no recurring schedule beyond fixed frequencies. |
| Automatic Log Rotation | **Nagios's** log rotation is Nagios's own `log_rotation_method` setting (not inspected here). Pinpoint reads the archive via `archivejson.cgi` (`nagios/notifications.py`). **Pinpoint's** DB retention exists (`scheduler.py` → `_purge_old_data()`, driven by `Log_Retention_Days` and `Diagnostic_History_Retention_Days`). No file-log rotation is configured in `app/__init__.py` or `server.py` (only `app.logger` is used). VM-verified: Nagios rotates daily (`log_rotation_method=d`), and `pinpoint-gunicorn.service` logs to stdout, which journald stores with its default size limits (no overrides). | Issue #11 — Implemented but Needs Refinement — rotation works through journald defaults, but its cap is not set deliberately and storage use is not monitored or shown. |
| Redundant Monitoring | Not found. One Nagios, one in-process scheduler (`PINPOINT_SCHEDULER=1`), SQLite files. The only resilience feature is the daily DB backup (`automation.py` → `backup_databases()`). | Issue #12 — Not implemented. |

### Plugins & Extensibility

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Simple Plugin Design | Plugin Manager scans `NAGIOS_PLUGIN_DIR` (`api/plugin/scanner.py`), validates (`plugin_validator.py`) and manages the bundled plugins. Adding your own plugin is out of scope (team decision: it needs security controls). | Not Applicable — Out of agreed scope. No issue required. |
| Standard Plugins | 58 bundled plugins catalogued (`api/plugin/plugin_catalog_data.py`, `plugin_descriptions.py`). Scan, enable, disable and validate via `/api/plugin/*`. | Fully Implemented — No issue required. |
| Community Plugins | Not supported by decision: community plugins need security controls Pinpoint does not have. The disabled upload route and the `PluginSource` enum remain in the code. A safe archive update path for bundled plugins exists (`plugin_update.py`: tar/zip-slip checks, SSRF check, 50 MB cap, backup and rollback). | Not Applicable — Out of agreed scope. No issue required. |
| Any Language | The scanner lists any executable in the plugin directory (`scanner.py`, `os.X_OK`), but writing or installing your own plugin in another language is not a supported workflow (custom plugins are out of scope). | Not Applicable — Out of agreed scope. No issue required. |
| Check Commands | Command definitions are rendered by `plugin_registry.py` → `render_command_definition()`. Overrides and restore-default go through `command_validator.py`. Forbidden shell characters are rejected. | Fully Implemented — No issue required. |
| Remote Execution | NCPA (deployed over SSH, `ncpa_deployment.py`) and `check_by_ssh` as a custom check (`custom_checks.py`). NRPE is not used (team decision), so that Nagios method is out of scope. | Fully Implemented — No issue required. Within scope: NCPA and SSH. |

### Reporting & Web Interface

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Web Interface | The React client (`client/src/App.tsx`, pages under `client/src/pages/`). | Fully Implemented — No issue required. |
| Notification History | `api/system/history.py` → `/history/notifications`, `HistoryPage.tsx`. Backed by `archivejson.cgi`. `Implementation_Status.md` says the page "has not been audited" against its requirements. | Issue #20 — Needs the audit. |
| Problem History | `/history/alerts` and `/history/alerts/detail`, `AckHistory`. Same audit status. | Issue #20 — Needs the audit. |
| Log File Access | System Logs page (`SystemLogsPage.tsx`, `api/system/log.py`) shows five Pinpoint audit categories. Nagios event history is reachable through History. The raw Nagios log file is not exposed. | Issue #11 — Partial. |
| Availability Reports | `api/system/report.py` has six endpoints. `ReportsPage.tsx` and `reports/ExtraReports.tsx` show availability, network services and several more (Hosts by OS and others). `Implementation_Status.md` says only two views exist, so that file is stale. No SLA target or compliance. No scheduled or recurring reports. | Issue #21 — Refine. |
| Performance Data | `ServicePerfData` and `HostPerfData` collected by `nagios/status.py`. Trends via `/network-health/trends` and `/plugin-trends`, rendered with Recharts. Fixed windows of 1, 6, 24 and 168 hours. | Fully Implemented — No issue required. |
| Status CGI | Nagios's native UI is intentionally not an operator surface (`System_Overview_and_Architecture.md`, `Implementation_Status.md` "Explicit exclusions"). | Not Applicable — Explicitly out of scope. No issue required. |

### Integration & Data Access

| Nagios Core Feature | PinPoint (Location / Implementation) | Gap / Issue |
|---|---|---|
| Status Files | Pinpoint consumes status through `statusjson.cgi` and `objectjson.cgi` (`nagios/status.py`), not `status.dat`. Snapshots go to `history.db` every 60 s. | Fully Implemented — No issue required. |
| External Commands | Not found in the inspected repository. No write to the command pipe or `cmd.cgi`. Acknowledgement, downtime, "check now" and notification toggles cannot reach Nagios. VM-verified: the pipe is writable by the `pinpoint` user, so the capability is available but unused. | Issue #19 — Not implemented. |
| Performance Data | (Integration row.) Collected internally and charted only. Export to Grafana, InfluxDB or Prometheus is a third-party integration, which is out of scope (team decision, assumption extended to this row; confirm). | Not Applicable — Out of agreed scope. No issue required. |
| Event Broker | Nagios-internal module interface. Pinpoint integrates through CGIs by design, and the spec keeps Nagios as the engine. | Not Applicable — Architecture does not use broker modules. No issue required. |
| NDOUtils | The purpose (a database of Nagios data for reporting) is served by `history.db` (`history_models.py`). The spec documents that snapshots can miss transitions between polls, and the archive CGI covers events. | Fully Implemented — No issue required. |
| API Integration | The REST API (`/api/*`) is session-cookie only (Flask-Login) and serves the bundled client. Connectors to ticketing, CMDB or automation tools are third-party integrations, which are out of scope (team decision, assumption extended to this row; confirm). | Not Applicable — Out of agreed scope. No issue required. |
| Third-Party Tools | Not found: PagerDuty, Slack or ServiceNow integrations. Out of scope by team decision. | Not Applicable — Out of agreed scope. No issue required. |

---

## 3. Detailed Issue Breakdown

Conventions: "Existing" paths were verified in the repository. "(new)" marks proposed files. Dependencies list issue numbers. Priority reflects operator impact and risk.

### Issue #1 — Make notification policy configurable (periods, options, intervals)

**Related Nagios Core Feature:** Time-Based Alerting; Contact Notifications

**Current PinPoint Implementation:** `tpl/contact_template.cfg.tpl`, `host.cfg.tpl` and `service.cfg.tpl` hardcode `24x7`, the `w,u,c,r,f,s` options and `notification_interval 30`. `SystemSettings.Notifications` (`system_models.py`) is read by `Header.tsx` to show or hide the bell, and no server code applies it to Nagios. Per-user opt-in (`Receive_Email_Alerts`) now decides who is a contact, but not when or for which states.

**Identified Gap:** Operators cannot set quiet hours, severity options or renotify intervals. The "Notifications" setting suggests it controls alerting but only affects the UI.

**Classification:** Not Implemented (time-based); Implemented but Needs Refinement (setting semantics)

**Recommended Solution:** Add a small notification-policy model (timeperiod plus options plus interval) and render it into the existing templates. Rename or relabel the Notifications setting so it is clear it controls only the header bell, or make it control the Nagios `enable_notifications` flag through Issue #19.

**Backend Changes:** New policy model and migration. Extend `host_config_templates.py` and `create_host_cfg.py` to emit `define timeperiod` and policy fields. Validate names against `ILLEGAL_NAME_CHARACTERS`-style rules. New route under `/api/system`.

**Frontend Changes:** Settings card for the policy. Relabel the Notifications toggle.

**Network / Infrastructure Considerations:** Config applies through the existing validated write path (`create_host_cfg.py` validates with the Nagios binary before applying).

**Files or Modules Affected:** `server/app/network_discovery/templates/*.tpl`, `host_config_templates.py`, `create_host_cfg.py`, `server/app/system_models.py`, `client/src/components/settings/GeneralSettings.tsx`; (new) `server/app/api/system/notification_policy.py`.

**Priority:** High · **Estimated Complexity:** Medium

**Dependencies:** None (relabel); #19 for runtime enable/disable.

**Acceptance Criteria:** A saved quiet-hours policy appears as a timeperiod in generated config. An invalid policy is rejected with 400. The Nagios binary validates the config. The setting's label matches its behavior.

**Verification Plan:** Unit tests on template output. Integration test that a bad timeperiod leaves the live config untouched. Manual: set quiet hours, force a state change, confirm no notification inside the window.

### Issue #2 — Broaden and verify notification email delivery

**Related Nagios Core Feature:** Contact Notifications

**Current PinPoint Implementation:** Settings → Email (`client/src/components/settings/EmailSettings.tsx`, `server/app/api/system/smtp_settings.py`, `server/app/smtp_settings.py`) stores a Gmail app password encrypted (`secrets_store.py`) and applies it through `/usr/local/sbin/pinpoint-apply-smtp` via `sudo -n`. A test email reports a rejected login, a blocked port and an unknown host separately. Contacts are limited to opted-in users. `Implementation_Status.md` records VM-lab verification (#80).

**Identified Gap:** Only Gmail over STARTTLS on port 587 is supported (Microsoft 365, OAuth and other TLS modes are declared out of scope). The helper exists only on installed appliances, so saving elsewhere fails. Delivery depends on one external account. No feedback from Nagios's mail command into the UI was found in the repository.

**Classification:** Partially Implemented

**Recommended Solution:** Decide whether a generic SMTP relay (host, port, TLS mode, user) is required beyond Gmail. If so, extend the `PRESETS` pattern in `smtp_settings.py`. Add a visible "last notification mail failed" indicator. Do not redesign what already works.

**Backend Changes:** Additional presets or a custom-relay preset, and a failure indicator.

**Frontend Changes:** Provider choice in `EmailSettings.tsx` and a failure banner.

**Network / Infrastructure Considerations:** Outbound SMTP. Passwords stay encrypted and are never returned. The root helper is installer-owned and outside this repository.

**Files or Modules Affected:** `server/app/smtp_settings.py`, `server/app/api/system/smtp_settings.py`, `client/src/components/settings/EmailSettings.tsx`; installer repository for the helper.

**Priority:** Medium · **Estimated Complexity:** Low

**Dependencies:** Installer helper changes for any new TLS mode.

**Acceptance Criteria:** A non-Gmail relay can be saved and a test email delivered. A CRITICAL and its recovery each produce one email per opted-in contact. A failed send is visible to an administrator, and no password appears in any response or log.

**Verification Plan:** Existing `server/tests/unit/test_smtp_settings.py` and `test_email_alerts.py` (not executed in this audit), plus a VM-lab run with a local SMTP sink.

### Issue #3 — Contact groups and escalation paths

**Related Nagios Core Feature:** Escalation Paths

**Current PinPoint Implementation:** One group `system_users` for every host and service (`create_host_cfg.py`), now limited to users with `Receive_Email_Alerts`. Per-host recipients are the open issue #79 in `Implementation_Status.md`.

**Identified Gap:** No per-severity or per-time escalation to different people, and no routing by host group.

**Classification:** Not Implemented

**Recommended Solution:** Let a role or user subset form a contact group. Add an escalation record (first notification, last notification, interval, contact group) and render `define serviceescalation`/`hostescalation`.

**Backend Changes:** Escalation model, migration, routes, and config rendering.

**Frontend Changes:** An escalation editor, likely under Settings or Manage Roles.

**Network / Infrastructure Considerations:** None beyond a valid config.

**Files or Modules Affected:** `create_host_cfg.py`, `host_config_templates.py`, `server/app/system_models.py`, (new) escalation templates and route.

**Priority:** Medium · **Estimated Complexity:** Medium

**Dependencies:** #1; coordinate with the existing issue #79 (per-host recipients), which is the first step.

**Acceptance Criteria:** An unacknowledged problem past the configured count notifies the escalation group. Removing an escalation removes it from the config.

**Verification Plan:** Template unit tests. Lab run with two contacts.

### Issue #4 — Parent hosts and reachability

**Related Nagios Core Feature:** Network Host Hierarchy

**Current PinPoint Implementation:** No `parents` is generated. UNREACHABLE is counted but cannot arise from Pinpoint's config. Topology is an explicit exclusion.

**Identified Gap:** A router failure marks every host behind it DOWN instead of UNREACHABLE, which creates an alert storm and hides the root cause.

**Classification:** Not Implemented

**Recommended Solution:** First obtain a scope decision. Parent links (data and config only, no visualisation) are not the excluded topology view. Then add a `Parent_Device_ID` on `NetworkDiscovery`, a field in the device drawer, and a `parents` line in `host.cfg.tpl`. Suggest the parent from the gateway device (`/api/system/network-profile` already derives a gateway).

**Backend Changes:** Column and migration, validation (no cycles, no self, not retired or merged), config rendering, and handling in merge and retire.

**Frontend Changes:** Parent selector in Device Inventory.

**Network / Infrastructure Considerations:** Wrong parents hide real outages. Show a warning when a parent is unmonitored.

**Files or Modules Affected:** `server/app/system_models.py`, `server/app/network_discovery/templates/host.cfg.tpl`, `create_host_cfg.py`, `device_identity.py`, `api/system/device_identity.py`, `client/src/components/device-inventory/`.

**Priority:** Medium · **Estimated Complexity:** Medium

**Dependencies:** Scope decision.

**Acceptance Criteria:** With a parent set and powered off, children show UNREACHABLE, and only the parent raises an alert. Cycles are rejected.

**Verification Plan:** Unit tests (cycle, merge, retire). Lab: power down the parent.

### Issue #5 — Notification dependencies

**Related Nagios Core Feature:** Notification Dependencies

**Current PinPoint Implementation:** None generated.

**Identified Gap:** Services on a failed host, or dependent services, still notify.

**Classification:** Not Implemented

**Recommended Solution:** After #4, generate service dependencies from simple rules (all services depend on the host's availability, and optionally NCPA services depend on the NCPA port).

**Backend Changes:** Dependency rendering and, optionally, a rule table.

**Frontend Changes:** None initially.

**Network / Infrastructure Considerations:** Misconfigured dependencies suppress valid alerts, so log and display them.

**Files or Modules Affected:** `create_host_cfg.py`, `host_config_templates.py`, new template.

**Priority:** Low · **Estimated Complexity:** Medium

**Dependencies:** #4.

**Acceptance Criteria:** A host DOWN suppresses notifications of its dependent services.

**Verification Plan:** Template tests, lab run.

### Issue #6 — Flap detection: show history and allow tuning

**Related Nagios Core Feature:** Flap Detection

**Current PinPoint Implementation:** Flag stored and displayed in several pages (see Section 2). No thresholds in templates, so Nagios defaults apply.

**Identified Gap:** No flap thresholds, no per-service enable and no flap history. VM-verified: flap detection is enabled for generated hosts under the global 5%/20% thresholds, so the engine behavior is in place. The gap is control and history only.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Add `flap_detection_enabled` and low and high thresholds to the generator, with defaults in Settings. Show how long and how often a host or service has flapped, from `Is_Flapping` over snapshots.

**Backend Changes:** Template fields and a settings model, and a flap-history query.

**Frontend Changes:** Settings card, plus a flapping filter and history on the System Status page.

**Network / Infrastructure Considerations:** None.

**Files or Modules Affected:** `tpl/host.cfg.tpl`, `tpl/service.cfg.tpl`, `history_models.py`, `ServiceOverview.tsx`, `ServiceStatusTable.tsx`.

**Priority:** Medium · **Estimated Complexity:** Low

**Dependencies:** #10.

**Acceptance Criteria:** The resolved object (`objects.cache`) shows the saved flap settings, a forced flap is flagged, and the history lists it.

**Verification Plan:** Template tests, lab script toggling a service.

### Issue #7 — Event-handler framework

**Related Nagios Core Feature:** Event Handlers; Proactive Resolution

**Current PinPoint Implementation:** None. Attempt counters are stored (`Current_Attempt`, `Max_Attempts`) but unused.

**Identified Gap:** No way to run an action when a state change becomes HARD.

**Classification:** Not Implemented

**Recommended Solution:** Provide one Pinpoint-owned handler executable that Nagios calls with the state, state type, attempt and a handler id. The handler looks up an **allowlisted, admin-defined action** (not arbitrary shell) and records every run in a new audit log. Gate it with a new permission and a per-action enable flag. Run it on the Nagios host only. Do not accept commands from request bodies at execution time.

**Backend Changes:** Action model, audit table, handler script (new), `event_handler` and `event_handler_enabled` rendering, and a retry policy limit.

**Frontend Changes:** Remediation list in Plugin Manager or Settings, and a log view in System Logs.

**Network / Infrastructure Considerations:** Runs as the `nagios` user, so keep the action set small, validate arguments, add timeouts and a rate limit to prevent restart loops, and log without secrets.

**Files or Modules Affected:** `create_host_cfg.py`, `host_config_templates.py`, `server/app/api/commands/seed.py` (new permission), `server/app/logging/` (new log), `system_models.py`; (new) handler script.

**Priority:** Medium · **Estimated Complexity:** High

**Dependencies:** #8 uses it. Security review is mandatory.

**Acceptance Criteria:** On a HARD CRITICAL, exactly one configured action runs and is logged. A disabled action does not run. Arguments with shell metacharacters are refused.

**Verification Plan:** Unit tests on the handler's decision logic. Lab test with a harmless action. Security review.

### Issue #8 — Service recovery actions

**Related Nagios Core Feature:** Service Recovery

**Current PinPoint Implementation:** None.

**Identified Gap:** No automatic restart of failed services.

**Classification:** Not Implemented

**Recommended Solution:** Built on #7. Provide a fixed action type "restart service X on host Y" executed through the NCPA deployment key and fingerprint-pinned SSH (see `ncpa_deployment.py`; what the on-device rule permits must be investigated first) or a local `systemctl restart` for server services, limited to a per-device allowlist and a maximum restarts per hour.

**Backend Changes:** Action type, SSH execution reuse, restart counters.

**Frontend Changes:** Per-service "recover automatically" toggle with the restart limit.

**Network / Infrastructure Considerations:** Needs privileged access on the target. PinPoint stores no SSH password (only the pinned port, fingerprint and `Key_Installed`), and uses the deployment key `~/.ssh/pinpoint_ncpa_deploy`.

**Files or Modules Affected:** `server/app/ncpa_deployment/`, `server/app/network_discovery/custom_checks.py`; (new) recovery module.

**Priority:** Low · **Estimated Complexity:** High

**Dependencies:** #7. Remote execution reuses the existing SSH trust model and NCPA, so nothing else is needed.

**Acceptance Criteria:** A stopped service is restarted at most N times per hour, every attempt is logged, and a failed restart escalates as a normal alert.

**Verification Plan:** Lab VM service stop test. Check the loop guard.

### Issue #9 — Nagios scheduled downtime and maintenance windows

**Related Nagios Core Feature:** Scheduled Operations

**Current PinPoint Implementation:** Maintenance Mode pauses only Pinpoint jobs (`automation.py`). Downtime state is displayed. Device pause (`/hosts/<id>/pause`) removes a host from the Nagios config, which is a different thing.

**Identified Gap:** No scheduled, recurring or one-off downtime that suppresses notifications while checks continue.

**Classification:** Partially Implemented

**Recommended Solution:** Add a maintenance-window model and apply it to Nagios through the command channel (#19) with `SCHEDULE_HOST_DOWNTIME` and `SCHEDULE_SVC_DOWNTIME`. Recurrence is Pinpoint's job (APScheduler already exists).

**Backend Changes:** Window model, routes, a scheduler job to create and cancel downtime, and audit entries.

**Frontend Changes:** Maintenance calendar or list, plus an "in downtime" indicator that already exists.

**Network / Infrastructure Considerations:** Windows must be time-zone aware, and a failed Nagios call must be visible.

**Files or Modules Affected:** `server/app/automation.py`, `scheduler.py`, `system_models.py`; (new) maintenance module and page.

**Priority:** High · **Estimated Complexity:** Medium

**Dependencies:** #19.

**Acceptance Criteria:** A window creates Nagios downtime at its start. `Scheduled_Downtime_Depth` becomes non-zero, notifications are suppressed, and it ends on schedule.

**Verification Plan:** Unit tests for recurrence. Lab check of downtime state and notification suppression.

### Issue #10 — Check timing and state-tuning settings

**Related Nagios Core Feature:** Flap Detection (tuning); Event Handler attempts (preliminary document)

**Current PinPoint Implementation:** The check interval is now a system setting (`SystemSettings.Check_Interval`: 1, 2, 5, 10 or 15 minutes, `api/system/settings.py`), written into `host.cfg.tpl` and `service.cfg.tpl` by `host_config_templates.py` → `check_interval()`. `retry_interval 1` and `max_check_attempts 3` remain fixed in the templates.

**Identified Gap:** Retry interval and attempt count cannot be tuned, and the interval has no per-device override.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Extend the existing Check interval setting with bounded retry interval and attempt count, and optionally a per-device override following the `Plugin_Variables` pattern. Reuse the apply-and-rollback path already in `settings.py`.

**Backend Changes:** Settings model and template parameters.

**Frontend Changes:** Settings card, and device drawer overrides.

**Network / Infrastructure Considerations:** Short intervals raise Nagios load. Warn about the check count.

**Files or Modules Affected:** `tpl/service.cfg.tpl`, `tpl/host.cfg.tpl`, `host_config_templates.py`, `system_models.py`, `api/system/settings.py`.

**Priority:** Low · **Estimated Complexity:** Low

**Dependencies:** None.

**Acceptance Criteria:** A saved retry interval and attempt count appear in the generated config, out-of-range values are rejected, and a rejected Nagios config rolls the setting back as the interval does today.

**Verification Plan:** Template unit tests.

### Issue #11 — Log management: set a deliberate cap, show storage use and give read access to Nagios logs

**Related Nagios Core Feature:** Automatic Log Rotation; Log File Access

**Current PinPoint Implementation:** VM-verified: Nagios rotates its own log daily (`log_rotation_method=d`) into `/usr/local/nagios/var/archives`. Pinpoint's Gunicorn logs to stdout (`pinpoint-gunicorn.service`), so journald stores them under its default limits (`journald.conf` has no overrides; 40 MB in use). Database retention is handled by `scheduler.py` → `_purge_old_data()`. Installer logs `/var/log/pinpoint-*.log` are not in `logrotate.d` but are small and written at install time.

**Identified Gap:** Rotation exists, but the cap is journald's default rather than a decision, no screen shows log or database storage use, and the raw Nagios log is not viewable in Pinpoint (System Logs shows only Pinpoint's audit categories). This repo does not rotate its own file logs, because it writes none.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Do not add file rotation or replicate Nagios's `log_rotation_method`. Have the installer set `SystemMaxUse` for journald, show log and database storage on the Dashboard status card (`/dashboard/status` already reports server disk), and optionally add a read-only, size-limited Nagios log tail to System Logs.

**Backend Changes:** Storage-use fields for the status route and an optional read route.

**Frontend Changes:** Storage indicator and an optional log tab.

**Network / Infrastructure Considerations:** Disk exhaustion on a single-host appliance. Redact secrets in any displayed log.

**Files or Modules Affected:** `server/app/api/system/dashboard.py`, `server/app/api/system/log.py`, `client/src/pages/SystemLogsPage.tsx`; installer repository for `journald.conf`.

**Priority:** Low · **Estimated Complexity:** Low

**Dependencies:** Installer change for the journald cap.

**Acceptance Criteria:** The journald cap is set explicitly on a fresh install, and log and database usage are visible to an administrator.

**Verification Plan:** Check `journald.conf` on a fresh VM-lab install (`scripts/vmlab`). Unit test for any new status fields.

### Issue #12 — Redundant monitoring

**Related Nagios Core Feature:** Redundant Monitoring

**Current PinPoint Implementation:** None. Daily DB backups only.

**Identified Gap:** A host failure ends monitoring and the dashboard together.

**Classification:** Not Implemented

**Recommended Solution:** Architectural decision first. Options: documented cold standby from the backups (cheap, realistic), or a second Nagios with Pinpoint replication (large). SQLite and the in-process scheduler make an active pair costly. Start with a restore runbook and a backup-restore command.

**Backend Changes:** For cold standby, a restore CLI command and a backup health indicator. For active/passive, leader election and database replacement. Out of scope until decided.

**Frontend Changes:** Backup status indicator.

**Network / Infrastructure Considerations:** Duplicate-check prevention and split-brain are the main risks for any active design.

**Files or Modules Affected:** `server/app/automation.py` (`backup_databases`), `server/app/api/commands/`; installer repository.

**Priority:** Low · **Estimated Complexity:** High

**Dependencies:** Architecture decision.

**Acceptance Criteria:** Documented, tested recovery of a fresh host from a backup within a stated time.

**Verification Plan:** VM lab restore drill.

### Issue #13 — Bandwidth monitoring

**Related Nagios Core Feature:** Bandwidth Monitoring

**Current PinPoint Implementation:** Raw octet counters for interface index 3 only (`config.py` → `SNMP_OIDS`).

**Identified Gap:** No rate, interface choice or utilisation.

**Classification:** Partially Implemented

**Recommended Solution:** Compute bits per second from consecutive `ServicePerfData` counter samples (handle wrap and reset), and let the device choose interfaces from a discovered interface list. Chart in Network Health.

**Backend Changes:** Rate calculation endpoint and interface discovery (SNMP walk or `check_ifstatus`).

**Frontend Changes:** Interface selector and a bandwidth chart.

**Network / Infrastructure Considerations:** Extra SNMP queries, and 32 versus 64-bit counters.

**Files or Modules Affected:** `config.py`, `api/system/network_health.py`, `plugin_registry.py`, `client/src/components/network-health/`.

**Priority:** Medium · **Estimated Complexity:** Medium

**Dependencies:** #14 for v3 devices.

**Acceptance Criteria:** A bandwidth graph matches a known traffic generator within a stated tolerance, and counter wrap is handled.

**Verification Plan:** Unit tests with synthetic counters. Lab with iperf.

### Issue #14 — SNMP v1, v2c and v3

**Related Nagios Core Feature:** SNMP Monitoring

**Current PinPoint Implementation:** Community-based. `-P` is declared in the definition options. A v3 definition (security level, user, auth and privacy) is not present.

**Identified Gap:** v3 unsupported, and the community is global (a per-device override, `NetworkDiscovery.Plugin_Variables`, is read when config is generated, but no API or UI writes it, so a per-device API is a prerequisite).

**Classification:** Partially Implemented

**Recommended Solution:** Add the v3 arguments to the `snmp` definition and store credentials with `secrets_store.py`. Expose the version and credentials per device. Notice the current limitation that command arguments, including secrets, are visible in `hosts.cfg` (see `Implementation_Status.md` on the NCPA token). Prefer Nagios resource-file macros for secrets.

**Backend Changes:** Definition and validation, secret storage, and resource-file support.

**Frontend Changes:** Per-device SNMP form.

**Network / Infrastructure Considerations:** Credentials exposure in command lines.

**Files or Modules Affected:** `plugin_registry.py`, `plugin_settings.py`, `custom_checks.py`, `secrets_store.py`, `PluginSettings.tsx`.

**Priority:** Medium · **Estimated Complexity:** Medium

**Dependencies:** None.

**Acceptance Criteria:** A v3 device is monitored with authPriv, and the secret is not returned by any API or logged.

**Verification Plan:** Lab with `snmpd` v3. Secret-leak tests.

### Issue #15 — Default host metrics: load, swap, disk I/O and process checks

**Related Nagios Core Feature:** Processor Load; Disk Usage; Memory Monitoring; Process Monitoring

**Current PinPoint Implementation:** `NCPA_METRICS` defaults to cpu, memory and disk usage. The table is editable in Settings → Plugins.

**Identified Gap:** Missing defaults for load average, swap and disk I/O, and no guided process check.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Add defaults for the missing NCPA paths (verify their paths against the NCPA version deployed, 3.5.0). Add a "process must run" helper that fills the NCPA path and `queryargs`. Document memory-leak trending through existing trends.

**Backend Changes:** Defaults in `config.py`, and optional helper validation.

**Frontend Changes:** Helper in `PluginSettings.tsx`.

**Network / Infrastructure Considerations:** More services per host increases Nagios load.

**Files or Modules Affected:** `config.py`, `plugin_settings.py`, `client/src/components/settings/PluginSettings.tsx`.

**Priority:** Medium · **Estimated Complexity:** Low

**Dependencies:** None.

**Acceptance Criteria:** After a deploy, services for each new metric report OK on a lab host. The process helper alerts when the process stops.

**Verification Plan:** NCPA lab run (`docs/test-runs/` format).

### Issue #16 — NCPA deployment hardening

**Related Nagios Core Feature:** Linux/Unix Servers

**Current PinPoint Implementation:** `ncpa_deployment.py`. Gaps are already listed in `Implementation_Status.md`: one global `NCPA_PORT`, no cleanup after failure, and the token is a positional argument in the Nagios command.

**Identified Gap:** As listed. Other Unix systems are unverified.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Close the three listed items and document supported operating systems.

**Backend Changes:** Per-device port column, cleanup route, secrets through Nagios resource macros (256-macro limit) and `hosts.cfg` mode 0640.

**Frontend Changes:** Cleanup action in Deployment History.

**Network / Infrastructure Considerations:** Token exposure, leftover privileged account on failed installs.

**Files or Modules Affected:** `server/app/ncpa_deployment/ncpa_deployment.py`, `plugin_registry.py`, `client/src/components/ncpa-deployment/`.

**Priority:** Medium · **Estimated Complexity:** Medium

**Dependencies:** None.

**Acceptance Criteria:** A failed install can be cleaned from the UI, the token is absent from process listings, and a device on a non-default port is tracked.

**Verification Plan:** VM lab (existing `scripts/vmlab`).

### Issue #17 — Windows monitoring through NCPA

**Related Nagios Core Feature:** Windows Servers

**Current PinPoint Implementation:** NCPA is the chosen agent. Its deployment (`server/app/ncpa_deployment/ncpa_deployment.py`) installs over SSH on Linux with systemd, and the metric defaults (`config.py` → `NCPA_METRICS`) assume Linux paths such as `disk/logical/{partition}/used_percent`. `check_nt` (NSClient++) exists only as a custom check (`custom_checks.py`). NRPE is not used.

**Identified Gap:** No documented or supported way to put NCPA on a Windows host and have Pinpoint monitor it. Windows disk and process node names differ from the Linux ones, and the SSH deployment does not apply.

**Classification:** Partially Implemented

**Recommended Solution:** Decide whether Windows hosts are in scope at all. If they are, document the manual NCPA install for Windows, let a device be marked as "agent installed manually" (reusing `NCPADeployment` state and `NCPADevicePartition`), and verify the metric paths against NCPA on Windows. Decide whether to keep the `check_nt` custom check, which relies on NSClient++ and not NCPA.

**Backend Changes:** Manual-agent registration route, partition and metric handling for Windows names, and no SSH deployment.

**Frontend Changes:** An "I installed NCPA myself" action and Windows instructions in the NCPA Deployment page.

**Network / Infrastructure Considerations:** NCPA port and token handling. Token exposure in the Nagios command is the known gap in Issue #16.

**Files or Modules Affected:** `server/app/ncpa_deployment/ncpa_deployment.py`, `server/app/network_discovery/plugin_registry.py`, `server/config.py`, `client/src/pages/NcpaDeploymentPage.tsx`.

**Priority:** Low · **Estimated Complexity:** Medium

**Dependencies:** Scope decision on Windows. Issue #16.

**Acceptance Criteria:** A Windows lab host with NCPA installed by hand reports CPU, memory and disk services as OK in Pinpoint.

**Verification Plan:** Windows lab VM, recorded in `docs/test-runs/`.

### Issue #18 — Application and API check coverage

**Related Nagios Core Feature:** Database Servers; Mail Servers; Directory Services; Application Servers; API Monitoring

**Current PinPoint Implementation:** See Section 2 rows.

**Identified Gap:** POP3 and IMAP protocol checks, SQL Server, Oracle and MongoDB, Active Directory specifics, and API checks (expected status, body match, headers) are missing.

**Classification:** Partially Implemented

**Recommended Solution:** Add registry definitions for bundled plugins that already ship in the catalog (none of `check_pop` or `check_imap` is in the catalog, so use the bundled `check_tcp` with an expected response string for POP3 and IMAP), expose `check_http` options (expected string, status) through a per-device form. Anything that needs a plugin outside the bundled catalog is out of scope.

**Backend Changes:** `PLUGIN_DEFINITIONS` entries and `CUSTOM_CHECK_FIELDS`.

**Frontend Changes:** Field forms follow the existing custom check dialog.

**Network / Infrastructure Considerations:** Credentials rules as in #14.

**Files or Modules Affected:** `plugin_registry.py`, `custom_checks.py`, `CustomCheckDialog.tsx`.

**Priority:** Medium · **Estimated Complexity:** Medium

**Dependencies:** None. Only bundled plugins are in scope.

**Acceptance Criteria:** An IMAP and a REST-API check each go OK and CRITICAL against lab targets.

**Verification Plan:** Lab targets (`lab/`).

### Issue #19 — Nagios external command channel (acknowledge, downtime, re-check, notifications toggle)

**Related Nagios Core Feature:** External Commands; Contact Notifications (acknowledgement)

**Current PinPoint Implementation:** Acknowledgement is Pinpoint-local (`dashboard.py` → `acknowledge_alert()`, `AlertAcknowledgement`, `AckHistory`). No code writes to Nagios. The `Notifications` setting does not either.

**Identified Gap:** A Pinpoint-acknowledged problem keeps notifying through Nagios and keeps its Nagios acknowledgement flag unset. Operators cannot trigger a check now.

**Classification:** Not Implemented

**Recommended Solution:** Add one narrow module that issues a short allowlist of Nagios commands (`ACKNOWLEDGE_*_PROBLEM`, `SCHEDULE_*_DOWNTIME`, `SCHEDULE_FORCED_*_CHECK`, `ENABLE/DISABLE_NOTIFICATIONS`). Prefer the command pipe: VM-verified, `nagios.cmd` is group-writable and the `pinpoint` service user is in group `nagios`, with `check_external_commands=1`. The `cmd.cgi` route would need `pinpoint-api` added to the `authorized_for_*_commands` lines of `cgi.cfg`, which today list only `nagiosadmin` (and that account has no htpasswd entry), so avoid it. Call it from the acknowledge route in addition to the local record. Validate hostnames and service names against known snapshot rows.

**Backend Changes:** New client module, route changes, audit log entries, error handling when Nagios is unreachable.

**Frontend Changes:** "Check now" action and an indication of whether the ack reached Nagios.

**Network / Infrastructure Considerations:** Writing to the pipe gives the web service control of Nagios, so keep the allowlist small. Command injection (newlines in comments) must be handled, so sanitise comments. No installer change is needed for the pipe route.

**Files or Modules Affected:** `server/app/api/system/dashboard.py`, `network_hosts.py`, `network_services.py`; (new) `server/app/nagios/commands.py`; `config.py`.

**Priority:** High · **Estimated Complexity:** Medium

**Dependencies:** None. Unblocks #9.

**Acceptance Criteria:** Acknowledging in Pinpoint stops repeat notifications and sets the Nagios acknowledgement flag. A comment with a newline cannot inject a second command. A Nagios outage returns a clear error and keeps the local record consistent.

**Verification Plan:** Unit tests on command formatting and injection. Lab check of `acknowledgement_type` in the next poll.

### Issue #20 — Audit the History page for problem and notification history

**Related Nagios Core Feature:** Notification History; Problem History

**Current PinPoint Implementation:** `HistoryPage.tsx` and `api/system/history.py`. `Implementation_Status.md`: not audited against `Alerts_Notifications_History_Requirements.md`.

**Identified Gap:** Unaudited. Also, auto-resolved acknowledgements are not cleaned up on UP/OK (known gap), which affects history accuracy.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Perform the audit already requested, and wire the AUTO_RESOLVED cleanup.

**Backend Changes:** Poll-time cleanup of acknowledgements on recovery.

**Frontend Changes:** Fixes found by the audit.

**Network / Infrastructure Considerations:** None.

**Files or Modules Affected:** `server/app/nagios/status.py`, `api/system/history.py`, `client/src/pages/HistoryPage.tsx`.

**Priority:** Medium · **Estimated Complexity:** Low

**Dependencies:** None.

**Acceptance Criteria:** Each requirement in the History spec has a pass or fail record, and a recovered alert's acknowledgement is closed with an AUTO_RESOLVED row.

**Verification Plan:** Existing unit tests plus new cases. QA journey run per `docs/qa/`.

### Issue #21 — Availability reports: SLA targets and recurring reports

> **Status: awaiting clarification.** The scope is unclear, so this issue is provisional. It bundles three separate things: (a) an SLA target with a breach marker in the availability report, (b) scheduled or recurring reports delivered by email, and (c) correcting `Implementation_Status.md`, which understates the Reports UI. Nagios Core itself only shows availability percentages and has no SLA targets, so (a) goes beyond Core. Please say which of (a), (b) and (c) are wanted. (c) is the only part that is certain.

**Related Nagios Core Feature:** Availability Reports

**Current PinPoint Implementation:** Six report endpoints and several views. `Implementation_Status.md` understates the UI.

**Identified Gap:** No SLA target or breach marking, no scheduled report, and the status file is stale.

**Classification:** Implemented but Needs Refinement

**Recommended Solution:** Add an SLA percentage setting with a pass or fail column, and update `Implementation_Status.md`. Scheduled email reports depend on #2.

**Backend Changes:** SLA setting and report fields.

**Frontend Changes:** SLA control and indicator.

**Network / Infrastructure Considerations:** None.

**Files or Modules Affected:** `api/system/report.py`, `ReportsPage.tsx`, `spec files/Implementation_Status.md`.

**Priority:** Low · **Estimated Complexity:** Low

**Dependencies:** #2 (scheduled delivery).

**Acceptance Criteria:** Reports show the target and a breach flag, and the status document matches the UI.

**Verification Plan:** Unit tests, manual check.


---

## 4. Prioritized Implementation Roadmap

### Phase 1 — Refine existing functionality
Issues: **#20, #11, #15, #10, #6, #16, #21**

- Order: #20 first (it is an audit), then #10 and #6 (shared template work), #15 (config defaults), then #11, #16 and #21.
- Dependencies: #6 follows #10.
- Expected outcome: History is audited. Hardcoded check tuning becomes settings. Flapping becomes tunable, and the host metric defaults are broader.

### Phase 2 — Complete partially implemented features
Issues: **#19, #1, #2, #13, #14, #18**

- Order: #19 first because it fixes a correctness gap (acknowledgement does not reach Nagios), then #1, then #2 (small now that Gmail delivery exists). #13, #14 and #18 are independent.
- Dependencies: #2 needs installer-helper changes for any new TLS mode.
- Expected outcome: Acknowledgements behave as operators expect, notification policy is editable, and mail delivery is not tied to one provider.

### Phase 3 — Implement missing core capabilities
Issues: **#9, #3, #4, #5, #7, #8, #17**

- Order: #9 (needs #19), then #4, then #5. #3 after #1 and #2. #7, then #8. #17 is independent and depends on a scope decision.
- Dependencies: #4 needs the scope decision. #7 and #8 need security review first.
- Expected outcome: Maintenance windows, root-cause-aware alerts, escalation and controlled remediation.

### Phase 4 — Reliability, security and scalability
Issues: **#12**, plus a security review of #7, #8 and #19 before release

- Dependencies: #12 needs an architecture decision.
- Expected outcome: A recovery strategy, and reviewed security for the automation features (the plugin-installation path stays out of scope).

---

## 5. Architectural Recommendations

1. **Extend the single config writer.** All generated objects go through `create_host_cfg.py` and `host_config_templates.py`, which validate with the Nagios binary and keep a backup before applying. New object types (timeperiod, escalation, dependency, handler) should use this path (verified existing behavior).
2. **Add one Nagios command module (#19)** rather than scattered calls. It should be the only code that talks to `cmd.cgi` or the pipe (proposed).
3. **Reuse the secret store** (`secrets_store.py`) for SNMP v3 and SMTP secrets. Avoid placing secrets in command lines where Nagios resource files can carry them. Verified on a lab appliance: `resource.cfg` is group-writable by the `pinpoint` user and `hosts.cfg` is world-readable (mode 0664), with a limit of 256 `$USERn$` macros (proposed; the NCPA token issue is also in `Implementation_Status.md`).
4. **Keep Pinpoint from becoming an engine.** Do not execute checks or remediation inside the Flask process. Remediation runs through Nagios event handlers under strict allowlists.
5. **Make hardcoded constants settings.** Check timing, flap thresholds, notification options and NCPA defaults are templates or config constants today (verified). Follow the `DiscoverySettings` and `PluginSettings` pattern, with optimistic versions.
6. **Observability:** log every automated action (remediation, scheduled downtime, notification send) into the existing audit tables, and surface them in System Logs.
7. **Update the specifications with each change,** as `AGENTS.md` requires. `Implementation_Status.md` is already stale on the Reports UI (found in this audit).
8. **Scaling:** SQLite plus an in-process scheduler fits the single-appliance target. Treat redundancy as a documented restore procedure first (proposed).

---

## 6. Reference Documentation

Sources consulted:

- Nagios Core features page (fetched 2026-10-13): https://www.nagios.org/projects/nagios-core/features/ — the 55-row inventory comes from this fetch. The fetch tool summarised the page, so the feature names were copied from that summary.
- Event handlers: https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/eventhandlers.html
- Flap detection: https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/flapping.html
- Tuning: https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/tuning.html
- Network reachability: https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/networkreachability.html
- `Backup Documents from Nagios.pdf` (supplied attachment, treated as context and verified against the repository).
- Repository state: `git pull` on 2026-10-13, then re-inspection of the changed files (`create_host_cfg.py`, `host_config_templates.py`, the templates, `smtp_settings.py`, `api/system/settings.py`, `Implementation_Status.md`).

**Not accessed or not verified:**

- The supplementary pages, the CGI configuration page, the Nagios Core vs. XI comparison PDF and the Monitoring Architecture PDF were **not retrieved**. No claim above relies on their contents. Nagios behavior described here that the VM did not show (downtime commands, escalation and dependency objects) comes from general knowledge of Nagios Core, not from these pages. Verify against the linked pages before implementation.
- One live VM was inspected read-only. It had no plugin services enabled, no mail configured and no running test. Claims about plugin-service config come from the generator code, and Pinpoint's behavior at runtime (UI, acknowledgements) was not exercised.
- The installer repository is outside this audit (log handling and the root mail helper).
- Not verified on the VM: that a command written to the pipe is accepted, downtime and acknowledgement behavior, and NRPE/Windows paths.
