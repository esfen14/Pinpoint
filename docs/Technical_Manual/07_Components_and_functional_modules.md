## 7. Components and functional modules

For each module: purpose, key inputs/outputs, dependencies, configuration,
failure points and maintenance notes. Route lists are in
[`Backend_Modules_and_Routes.md`](../../spec%20files/Backend_Modules_and_Routes.md);
per-file purposes in the
[code documentation inventory](../plans/Code_Documentation_Inventory.md).

### 7.1 Authentication and accounts (`api/user/`)

| Aspect | Detail |
|---|---|
| Purpose | Login/logout, current user, accounts, roles, permissions, preferences, first-run setup, forgot-password requests |
| Inputs / outputs | JSON credentials → session cookie; account and role CRUD |
| Dependencies | `USER`, `ROLE`, `PERMISSION`; Nagios config writer (users are Nagios contacts) |
| Configuration | Session timeout, strong password policy (Settings → Security) |
| Failure points | Nagios apply failure after an account save (shown as a warning) |
| Maintenance | `flask sync-permissions` after upgrades; `flask recover-bootstrap-admin` for lockout |

### 7.2 Monitoring views (dashboard, network health, hosts, services)

| Aspect | Detail |
|---|---|
| Purpose | Current state, summaries, trends, acknowledgement, Check now |
| Inputs / outputs | `history.db` latest snapshots → JSON; acknowledgement → `system.db` + Nagios command pipe |
| Dependencies | `nagios/status.py` poller; `api/system/statistics.py` |
| Configuration | Data polling interval (30/60/120/300 s), Check interval |
| Failure points | Stale data if Nagios or the scheduler stops; command pipe unavailable (`nagios_synced: false`) |

### 7.3 History and notifications

Reads `archivejson.cgi` for alert and notification events; joins PinPoint
acknowledgement history; header bell keeps a per-user unread cursor. Failure
point: Nagios archive unavailable → 502.

### 7.4 Network discovery and Nagios configuration (`network_discovery/`)

| Aspect | Detail |
|---|---|
| Purpose | nmap TCP/UDP discovery, identity reconciliation, port lifecycle, SNMP interface discovery, `hosts.cfg` generation |
| Inputs / outputs | Networks, ports, Port → Service tables → device records, `hosts.cfg` |
| Dependencies | `nmap`, `snmpwalk`, Plugin Manager state, `nagios -v`, `sudo systemctl reload nagios` |
| Configuration | `PINPOINT_NETWORKS`, `DiscoverySettings`, `PINPOINT_PORT_ARCHIVE_AFTER_DAYS` |
| Failure points | Nagios rejects candidate config → rolled back, error recorded; scan finds no host → failed status before changes |
| Maintenance | Sensitive module: injection and secret-exposure review on change |

### 7.5 Plugin Manager (`api/plugin/`)

Scans `NAGIOS_PLUGIN_DIR`, tracks status, versions, commands, overrides,
dependencies; enable/disable drives the reconciler, which attaches services
per discovered port and applies config once. Custom checks and server checks
add argument-driven services. Custom plugin upload is disabled in this
release.

### 7.6 NCPA deployment (`ncpa_deployment/`)

SSH host-key fingerprint retrieval and explicit trust, login checks, remote
install, authenticated listener verification, partition discovery,
per-device results, cancellation, failed-only cleanup, manual registration
for Windows. Failure points: SSH auth, fingerprint mismatch, agent
port blocked. Sensitive module.

### 7.7 Alerting configuration

Notification policy (quiet hours, options, renotify), per-host recipients,
escalations, email transport (`SMTP_SETTINGS` + root helper
`/usr/local/sbin/pinpoint-apply-smtp` writing `/etc/msmtprc`), HTML alert email
via `server/scripts/pinpoint_notify_email.py`.

### 7.8 Maintenance windows

`MAINTENANCE_WINDOW` and occurrences; `maintenance_windows` job every 60 s
schedules Nagios downtime through the command pipe with retries.

### 7.9 Remediation (automatic recovery)

Nagios event handler writes one JSON file per event to `REMEDIATION_SPOOL_DIR`;
the consumer (every 15 s) validates, applies safety controls (kill switch,
Maintenance Mode, downtime, acknowledgement, cooldown, hourly cap), records a
`REMEDIATION_RUN` and runs `record_only`, `restart_local_service` (allowlisted
units via sudo) or `restart_remote_service` (root-owned helper on the device
over SSH). Failure escalation sends a Nagios custom notification.

### 7.10 Forecasts, storage and logs

`resource_forecast` every 30 min (linear fit over 72 h for NCPA disk and
memory); storage measurement on dashboard status; five audit-log categories
and a bounded, redacted Nagios log tail.

### 7.11 Scheduler and automation

| Job | Cadence |
|---|---|
| Nagios status poll | Data polling interval (default 60 s) |
| Retention purge | Daily |
| Automation (backups, scheduled discovery, plugin update scan, security validation) | Checked every 5 min (`AUTOMATION_CHECK_MINUTES`); each task's cadence comes from settings |
| Maintenance windows | 60 s |
| Resource forecast | 30 min |
| Remediation consumer | 15 s |
| NCPA relocation | Every 5 min (`NCPA_RELOCATE_MINUTES`) |

Maintenance Mode stops automation except backups. Scheduled discovery runs
only after a first manual scan.

### 7.12 Frontend shell

`AdminLayout`, `Sidebar`, `Header`, `PageAccessGuard`,
`SessionTimeoutWatcher`, `MaintenanceBanner`; `pageAccess.ts` maps routes to
permissions (usability only; the server enforces).
