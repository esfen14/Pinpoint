# Data Model and Integrations

**Last verified against the repository:** 2026-09-27

## Database ownership

Pinpoint uses two SQLite databases through one Flask-SQLAlchemy `db.session`.

| Database | Bind | Model files | Ownership |
|---|---|---|---|
| `server/system.db` | Default/no bind key | `system_models.py`, `plugin_models.py` | Application-generated users, configuration, workflow, audit, acknowledgement, discovery, deployment, and plugin data |
| `server/history.db` | `history` | `history_models.py` | Nagios-sourced status and performance snapshots only |

Never place application-generated data in `history_models.py`. A record's topic
does not decide its database; its producer does. For example, application alert
acknowledgements belong in `system.db` even though they relate to Nagios alerts.

## Model inventory

### Default bind: identity, configuration, operations, and acknowledgement

- Identity/access: `Permission`, `Role`, `RolePermission`, `PasswordResetRequest` (forgot-password requests; Pending until an admin resets or dismisses), `User` (`Must_Change_Password` forces a password change on a new account unless the create form unticks it, after reactivation, after an admin password reset, or after CLI bootstrap recovery; `Needs_Setup` is set only by `flask init-production` on the bootstrap administrator, whose installer email and password are placeholders, and is cleared by `POST /api/user/complete-setup`; migration `d3a9e6b2f741`). The recovery command finds that account by its uniquely earliest `Created_At`, not mutable email, `UserID`, or `Needs_Setup`; ties and no account fail without changes. Each active user is a Nagios contact named and addressed by `User.Email`, so an email change regenerates the config. Alert email is formatted HTML: the generator (`host_config_templates.py`, `create_host_cfg.py`) writes two commands, `pinpoint_notify_host_html` and `pinpoint_notify_service_html`, that run `/usr/bin/python3 -I server/scripts/pinpoint_notify_email.py` (standard library only; arguments are `key=value` Nagios macros; every value is cleaned and HTML-escaped; sends through `/usr/sbin/sendmail`, which is msmtp). Each contact lists them as its host and service notification commands. If the script is missing, or its path holds a character outside `[A-Za-z0-9_./-]`, no commands are written and contacts keep Nagios's stock plain-text `notify-host-by-email` and `notify-service-by-email`.
- Email settings: `SmtpSettings` (`SMTP_SETTINGS`), the singleton (`Id` 1) behind Settings -> Email: `Provider`, `Host`, `Port`, `Tls`, `Username`, `Sender` and `Password_Encrypted` (Fernet via `app/secrets_store.py`; never returned by the API), with `Version`/`Updated_By`. Saving also applies the settings to `/etc/msmtprc` through the installer's root helper `/usr/local/sbin/pinpoint-apply-smtp` (`sudo -n`, JSON on stdin: `host`, `port`, `tls`, `username`, `password`, `sender`). No row means no mail transport is configured.
- Plugin settings: `PluginSettings` (`PLUGIN_SETTINGS`), one row per plugin definition (`Plugin_Name`, e.g. `snmp`) holding the variables saved from Settings -> Plugins in `Variables` (JSON), with `Version`/`Updated_By`. No row means the `config.py` defaults apply.
- Device interfaces: `DeviceInterface` (`DEVICE_INTERFACE`, migration `b7d3f1a9c264`), one row per interface SNMP reports for a device (unique per `NetDiscoveryID` + `If_Index`): `Name`, `Speed_Bps` (null when unreported; `ifHighSpeed` is preferred over `ifSpeed`), `Admin_Status`, `Oper_Status`, `Monitored` (the administrator's choice, default false), `Present` (false once a refresh no longer finds a monitored interface) and `Last_Seen_At`. No rows means no change to the generated Nagios config.
- Network profile: singleton `NetworkProfile` (`Id=1`) holding the editable name, reference and detail rows of the Network Health info card.
- Audit/logging: `ActivityLog`, `ConfigurationChanges`, `ExportLog`.
- Discovery: `NetworkDiscoveryStatus`, `SkippedService`, `NetworkDiscovery`,
  `Open_TCP_Services`, `Open_UDP_Services`.
- NCPA deployment: `SSHCredentials`, `NCPADeploymentStatus` (one row per run,
  with `Reviewed_At`/`Reviewed_By`), `NCPADeploymentResult` (one row per device
  per run), `NCPADeployment` (each device's latest agent state),
  `NCPADevicePartition`.
- Remediation: `RemediationAction` (`REMEDIATION_ACTION`): the admin-defined rule with `Name` (unique), `Action_Type`, `Scope_Kind` (service or host), `Host_Pattern`, `Service_Pattern`, `Parameters` (JSON, validated per type), `Enabled`, `Max_Runs_Per_Hour`, `Cooldown_Seconds`, `Version` and `Updated_By`/`Updated_At`; and `RemediationRun` (`REMEDIATION_RUN`): one row per decision with `Event_Key` (sha256 of kind, host, service, state and last state change; unique together with `Action_Id`), `Action_Id` (a plain number, not a foreign key, so deleting an action keeps its runs), `Action_Name` (a copy), host, service, state, `State_Type`, `Attempt`, `Received_At`, `Started_At`, `Finished_At`, `Outcome`, `Reason` and `Output` (at most 1 KB, redacted). Both live in `system.db` because PinPoint writes them; `history.db` stays Nagios snapshots only. Migration `e4a7c1d9b305` creates both tables and the `remediation.view` and `remediation.manage` permissions, granted to the Administrator role.
- Settings: singleton `SystemSettings`, singleton `NotificationPolicy` (`NOTIFICATION_POLICY`, Id 1, migration `143c48cd6663`), one-per-user `UserPreferences`. `NotificationPolicy` stores weekday/HH:MM quiet windows as JSON, host/service option strings, a 0–1440-minute renotify interval, `Version`, and `Updated_By`; the migration seeds the historical 24x7/default-options/30-minute policy and removes the table on downgrade.
- Notifications/alerts: `NotificationCursor`, `AlertAcknowledgement`,
  append-only `AckHistory`.

Users are never deleted; account lifecycle uses `UserStatus`. Do not add delete
cascades to user foreign keys. `AckHistory.ActorUserID` is nullable only because
`AUTO_RESOLVED` is a system action. The existing `NotificationCursor` cascade is
a legacy inconsistency and must not be copied as a pattern.

### Settings ownership

| Scope | Fields |
|---|---|
| System general | `scanFrequency`, notification enablement, allowed export formats |
| System security | session timeout, strong-password policy, failed-login monitoring, audit logging, security-check frequency |
| System operations | `checkInterval` (Nagios-generated host and service checks, minutes), `retryInterval` and `maxCheckAttempts` (how soon a failing check is re-run and how many failures confirm a problem), `flapDetectionEnabled`, `flapLowThreshold` and `flapHighThreshold` (Nagios flap detection for generated hosts and services), update frequency, maintenance mode, automatic backups, log retention, diagnostic-history retention |
| Per-user display | theme, time zone, date/time format, font, font size, dashboard layout, dashboard refresh rate |

`SystemSettings` is row `Id=1` and carries a version/update audit stamp.
`UserPreferences` has one row per user. Do not move personal display values into
the shared singleton or system controls into user preferences.

### Default bind: Plugin Manager

`plugin_models.py` contains `Plugin`, `PluginVersion`, `PluginCommand`,
`PluginCommandOverride`, `PluginDependency`, `PluginConfiguration`,
`PluginHistory`, and `PluginScanStatus` plus their enums.

Plugin lifecycle and active monitoring are separate:

- `Plugin.Status` describes the executable/plugin lifecycle.
- `PluginConfiguration` describes whether a plugin has been wired to a scanned
  target and successfully applied to Nagios.
- `PluginConfiguration` also records which discovered service a check belongs
  to: `Port_Number`, `Protocol`, `Metric` (SNMP OID / NCPA metric),
  `Nagios_Service_Name` (e.g. `ssh-22-tcp`), `Applied_At` (first time active;
  not reset by a re-apply) and `Origin` (`Auto` for rows the plugin
  reconciler derives, `Manual` for rows created by hand, which the reconciler
  never touches, `Custom` for checks an administrator added for a plugin
  discovery cannot drive). `(PluginID, NetDiscoveryID, Nagios_Service_Name)` is unique;
  rows without a service name are not compared. The reconciler itself is
  planned, see `docs/plans/Plugin_Driven_Monitoring_Plan.md`; today every row is `Manual`.
- Command overrides preserve an immutable snapshot of the original command.
- Plugin Manager targets existing `NetworkDiscovery` devices; free-form targets
  are out of scope.
- **Monitoring state of a device.** `NetworkDiscovery.Device_State` (lifecycle) and
  `Include_Device_In_Scanning` (an administrator's pause) together give one label
  from `monitoring_state()` in `network_discovery/device_identity.py`: merged, retired,
  paused, address_unknown, missing, monitored (first match wins). Only
  `POST /hosts/<id>/pause` and `/resume` write the flag; scans and the lifecycle
  (`apply_match()`, `update_lifecycle()`) never change it. The config builder
  leaves a paused device out of `hosts.cfg`. Its `history.db` rows stop at the
  pause and are kept, but `unchecked_host_names()` (paused, retired, merged) lets
  `get_latest_hosts()` / `get_latest_services()` leave them out of the dashboard and
  Network Health counts and alerts.
- **Plugin Manager gates monitoring.** `plan_host_services()` (the planner
  behind both `hosts.cfg` and the reconciler) skips a port whose plugin
  (`plugin_for_definition()`) is not `Enabled` or `Active`, recording the reason
  ("check_ssh is not enabled in Plugin Manager.") in the skipped services, and
  the generic TCP fallback needs `check_tcp` enabled too. Ports keep their state
  and frozen plugin when a plugin is off, so enabling restores them.
- **Custom checks** (`network_discovery/custom_checks.py`, `api/plugin/custom_checks.py`;
  `docs/plans/Custom_Checks_Plan.md`): a `PluginConfiguration` row with `Origin = Custom`, no port
  (`Port_Number` and `Protocol` stay NULL), `Service_Description` the admin's name,
  `Nagios_Service_Name` `custom-<plugin>-<name>` and `Configuration_Data`
  `{"variables": {...}, "paused": bool}`. `create_host_cfg.load_custom_checks()` reads the
  unpaused rows and writes each as a service on its device in `hosts.cfg`, with one
  `pinpoint_custom_<plugin>` command per plugin used (rendered like a registry command:
  required arguments as `$ARGn$`, optional ones in the final `$ARG$`, every value single-quoted
  and checked against the registry's forbidden characters). Which plugins take one, and
  the arguments of each, are the `CUSTOM_CHECK_FIELDS` table; `PLUGIN_CLASSES` gives every
  other catalog plugin its reason for not taking one. A password field is stored encrypted in
  `Configuration_Data["secrets"]` (`app/secrets_store.py`, Fernet, key from `PINPOINT_SECRETS_KEY` or
  `SECRET_KEY`), never returned by the API, and decrypted only when `hosts.cfg` is generated, where it
  is written in plain text because Nagios needs it in the command (docs/plans/Custom_Checks_Plan.md §8b). Merging a device moves its custom
  checks to the target, dropping one whose name the target already has.
- **Server checks** are custom checks with no device (`NetDiscoveryID` empty) for the plugins in
  `SERVER_CHECK_FIELDS` (`check_apt`, `check_uptime`, `check_sensors`, `check_ide_smart`,
  `check_file_age`, `check_mailq`, `check_nagios`, `check_flexlm`). `load_server_checks()` writes
  them under "Define Server Checks" as services of the host `localhost`, named `server-<plugin>-<name>`,
  with commands that take no `-H`. `localhost.cfg` and the stock `localhost` services are never
  touched; merges and the reconciler ignore them.
- **The reconciler** (`app/api/plugin/reconcile.py`,
  `reconcile_plugin_monitoring`) keeps the `Origin = Auto` rows of
  `PluginConfiguration` equal to the services the planner generates (one per
  metric for SNMP/NCPA), promotes identified ports, calls
  `regenerate_and_apply_config_status()` once, and sets each Enabled/Active
  plugin Active when an applied row backs it. `Manual` rows are never touched
  and are not written to `hosts.cfg`. The manual path that created them
  (`monitoring_config.py`, `plugin-services.cfg`, the `/configurations` routes and
  the `plugin.configure` permission) is removed; upgraded installs keep any
  services it wrote in `plugin-services.cfg`, still loaded by Nagios, until an
  admin deletes that file's entries (see the plan, G18). If
  Nagios rejects the config the database is rolled back and the failure is
  recorded in the plugin history. Merging devices deletes the source's Auto rows
  (the reconciler rebuilds them) because the unique constraint would collide.
- Discovery scans the plugin directory first when Plugin Manager has no
  plugins (`ensure_plugin_inventory`). A fresh install enables nothing. An
  install that was already monitoring ports (it upgraded without ever scanning
  its plugins) has the plugins behind those ports enabled at that moment
  (`enable_plugins_backing_monitored_ports`), because the upgrade migration
  could not enable plugins that did not exist yet.
- Downgrading migration `a8c4e1f6b2d3` deletes the `Origin = Auto` rows: without
  the column they would look hand-made, and older code writes applied rows to
  `plugin-services.cfg` as well as `hosts.cfg`.
- `Plugin.Description` and `Plugin.Category` are filled by each plugin scan
  when empty, and never overwritten. Bundled nagios-plugins come from the
  committed catalog `plugin_catalog_data.py`, generated by
  `server/scripts/build_plugin_descriptions.py` from `Plugins_List.md` and the
  official manual pages (re-run it when either changes; a test fails if the
  committed file is stale). A plugin outside the catalog uses the first
  descriptive paragraph of its own `--help` output. The documentation link is
  derived from the catalog at read time and is not stored. The server never
  fetches documentation from the internet.

### History bind: Nagios snapshots

`history_models.py` contains `HostStatus`, `HostPerfData`, `ServiceStatus`,
`ServicePerfData`, and `ProgramStatus` plus state enums. Every model has
`__bind_key__ = "history"`.

`Acknowledgement_Type` on host/service snapshots is Nagios' acknowledgement
state. It is not Pinpoint's `AlertAcknowledgement` record.

## Current state versus durable event history

These sources are intentionally not interchangeable:

| Question | Correct source | Access path |
|---|---|---|
| What is happening now? | Latest rows in `history.db` | `statistics.py`, dashboard, host, service, and network-health routes |
| What changed between two times? | Nagios `archivejson.cgi` event log | `nagios/notifications.py`, history/report routes |
| What was host availability during a reporting period? | Nagios `archivejson.cgi` availability durations | Network Health and Reports availability routes; no snapshot fallback |
| Who acknowledged something in Pinpoint? | `AlertAcknowledgement` and `AckHistory` in `system.db` | Acknowledgement and history routes |
| Was a notification sent? | Nagios archive notification events | Notification/history/report routes |

Periodic snapshots may miss a state that changes and recovers between polls.
Archive events should therefore never be replaced with snapshot inference.
Conversely, the active-alert count and feed must use the same latest-snapshot
source so they cannot drift from one another.

## Nagios integration

`app/nagios/status.py` reads `statusjson.cgi` and `objectjson.cgi`, normalizes
host/service/program data, strips arguments from stored service check commands
to avoid persisting secrets, and writes snapshots to `history.db`.

A host Nagios lists as pending (no check has run yet) has no state to record, so the
poller skips it without an error and records it once its first check completes; a
pending service is stored as Unknown. A host or service result is recorded only
when its `Last_Check` differs from the latest stored check for that object; the
corresponding performance rows are also skipped on repeated polls. A host status that is not up, down, unreachable
or pending is logged as an error and that host is skipped for that poll; the rest of
the poll continues.

`app/nagios/commands.py` is the only writer of the Nagios external command pipe
(`Config.NAGIOS_COMMAND_FILE`, env `NAGIOS_COMMAND_FILE`, default
`/usr/local/nagios/var/rw/nagios.cmd`; the service user must be in group
`nagios`). The CGI route is not used: `cgi.cfg` authorizes commands only for
`nagiosadmin`, which has no password. The allowlist is closed, one function per
command: acknowledge/remove acknowledgement (host, service), forced check (host,
service) and schedule downtime (host, service; for the maintenance-window
work). Each line is `[epoch] COMMAND;args`, built only after validation: host,
service and author may not contain newline, CR, NUL or `;`; a comment may not
contain newline, CR or NUL (400 at the route) and has `;` replaced by `,`, is cut
to 255 characters and logged at INFO only to 40; a line may not exceed 4096 bytes
(one atomic pipe write); and the host or service must be in the latest snapshot
(paused, retired and merged devices are not). The pipe is checked to be a FIFO and
opened `O_NONBLOCK`, so a stopped Nagios fails at once and a full pipe gives up
after 2 s; every function returns a typed result (`invalid`, `unknown_target`,
`unavailable`, `timeout`) instead of raising. Failures of acknowledgement sync are
written to the audit log. Acknowledgements are sent as normal (not sticky),
matching `AcknowledgementType.NORMACK`. This path is injection-sensitive
(Engineering Standards, Sensitive modules).

`app/nagios/notifications.py` reads `archivejson.cgi` for durable alert and
notification event ranges.

Event handler: when at least one enabled `RemediationAction` exists and the program
`/usr/local/sbin/pinpoint-event-handler` is a file on this machine,
`host_config_templates.py` writes the commands `pinpoint_event_handler_service` and
`pinpoint_event_handler_host` into `hosts.cfg` (every Nagios macro single-quoted; the path must
be a safe Linux path) and adds `event_handler` and `event_handler_enabled 1` to exactly the hosts
and services an enabled action covers, using the same matching as the consumer. With no enabled
action, or without the program, the generated file is byte-for-byte what it was before.
Nagios runs the handler as `nagios` on every state change of a covered object; the handler writes
one file per event to `REMEDIATION_SPOOL_DIR`, and `app/remediation.py` decides and records. The
spool folder, the root-owned handler and narrower rights for the `nagios` group are installer work
(see the installer instructions); the application never runs a command taken from an event.

`Config.NAGIOS_HOST` is the CGI network host. In contrast,
`api/system/statistics.py` uses `NAGIOS_HOST = "localhost"` to identify the
Nagios server within status data. Changing either requires understanding its
different purpose.

## Aggregation rules

- Latest state is selected per host and per `(host, service)` pair.
- An active alert is a host not UP or a service not OK.
- Network-wide averages require at least two reporting hosts; otherwise return
  `null` and display “Insufficient data.”
- Trend windows are exactly 1, 6, 24, and 168 hours.
- Plugin grouping first uses stored check-command mapping, with service-name
  derivation as documented in `Display_Requirements.md`.
- Service descriptions may contain slashes.

## Monitoring and display schedules

| Setting | Owner and purpose |
|---|---|
| Discovery Scan Frequency (`scanFrequency`) | Pinpoint automation scans for devices and ports; it does not execute Nagios checks or determine result freshness. |
| Check interval (`checkInterval`) | System-wide 1, 2, 5 (default), 10 or 15 minutes. Nagios checks generated hosts and services at this cadence (`interval_length=60` seconds must hold on the appliance). The system administrator changes it on Settings → System; the shared config writer validates, backs up and reloads `hosts.cfg`, and a failed apply rolls the settings change back. Stock `localhost.cfg` objects are not rewritten. |
| Retry interval (`retryInterval`) and Maximum check attempts (`maxCheckAttempts`) | System-wide `SystemSettings.Retry_Interval` (1 to 10 minutes, default 1, never longer than the check interval) and `Max_Check_Attempts` (1 to 10, default 3; migration `b7d3f1a9c8e5`). They are written as `retry_interval` and `max_check_attempts` into every generated service and host, and the number of failures before a problem becomes HARD, and so when alerts are sent, follows them. The defaults reproduce the previous generated config exactly; a host gets an explicit `retry_interval` line only when the value is not the default 1. Same Settings → System page, permission and apply-and-rollback flow as the Check interval. There is no per-device override. |
| Flap detection (`flapDetectionEnabled`, `flapLowThreshold`, `flapHighThreshold`) | `SystemSettings.Flap_Detection_Enabled` (default on), `Flap_Low_Threshold` and `Flap_High_Threshold` (percent of state change, 0 to 100, empty by default; migration `c5e2a8f4d716`). Defaults write nothing extra, so default generated config is unchanged and Nagios's global values (5 and 20 on the lab appliance) apply. Custom thresholds are written as `low_flap_threshold` and `high_flap_threshold`; turning detection off writes only `flap_detection_enabled 0`. The change goes through the shared config writer and a rejected config rolls the settings back. The global `enable_flap_detection` and its thresholds in `nagios.cfg` belong to the installer. |
| Notification policy | A separate system-wide singleton controls the generated host/service notification periods, contact periods/options, state options, and renotify interval. Quiet windows use **Nagios server local time**, not each user's display zone; allowed spans are rendered as the complement in a fixed `pinpoint_notify` timeperiod in `hosts.cfg`. No quiet windows emit no new period; historical default output is preserved. Custom contacts inherit a non-registering `pinpoint-contact` template rather than rewriting stock `generic-contact`. Saving validates the candidate with Nagios, rolls back database changes on failed apply, and respects the system audit setting. Stock `localhost.cfg` and check cadence are unchanged. |
| Data polling frequency | Pinpoint reads Nagios CGI status every 60 seconds, fixed and independent of discovery and checks. Unchanged `Last_Check` does not add another host/service or performance row. |
| Dashboard Refresh Rate | Per-user browser fetch, Manual/1/5/15 minutes, independent of the other schedules; its hint shows the Check interval and 60-second poll. |

A new Nagios result can take up to one poll cycle to appear in Pinpoint, then
up to one browser refresh cycle to appear in the dashboard. Discovery scans
are not part of that latency or the check freshness threshold.

## Scheduler and retention

`scheduler.py` runs:

- Nagios status polling every 60 seconds.
- Daily purging based on `Log_Retention_Days` and
  `Diagnostic_History_Retention_Days`.
- Settings-driven automation checks every `AUTOMATION_CHECK_MINUTES`.
- The remediation spool consumer every 15 seconds (`max_instances=1`); at startup, runs left
  `running` by a stop become `interrupted` and are never run again.

The daily purge also deletes `RemediationRun` rows older than
`Diagnostic_History_Retention_Days`.

`automation.py` can schedule database backups, network discovery, plugin update
scans, and plugin security validation. Scheduled network discovery runs only if
at least one scan has already been recorded; a fresh installation waits for an
administrator to trigger the first scan manually. Maintenance mode permits backups but
stops the other automated operations. Jobs are attributed to an active user for
audit purposes.

## Network discovery and Nagios configuration

`app/network_discovery/network_discovery.py` performs host/TCP/UDP discovery.
`create_host_cfg.py` stores results, plans plugin-backed services, writes a
candidate Nagios host configuration, validates it with the Nagios binary,
backs up the running configuration, and applies only a valid candidate.

`plugin_registry.py` is the registry and renderer used to resolve discovered
services to supported plugins and variables. Unmonitorable discovered services
are recorded as `SkippedService` entries rather than silently discarded.

Network targets, ports, service rules, NCPA metrics, SNMP defaults, and
Nagios filesystem paths live in `server/config.py` and may be environment
overridden where defined. Networks, ports and service rules can also be saved
from the Settings page (`DiscoverySettings`), which then takes precedence. The SNMP
OID table (`SNMP_OIDS`) and the NCPA metric table (`NCPA_METRICS`) can be saved from
Settings -> Plugins (`PluginSettings`, one row per plugin: `snmp`, `ncpa`);
`plugin_config()` in `network_discovery/plugin_settings.py` puts the saved values in
place of their `config.py` keys once per config build, for both `hosts.cfg` and the
plugin reconciler. Per-host `Plugin_Variables` overrides still win.

### Interface bandwidth

Bandwidth is computed from stored samples; the Nagios checks are not changed.

- **Services.** Every `DeviceInterface` with `Monitored` true becomes an `interfaces` fact for the
  device's SNMP port (`load_host_plugin_facts()` -> `{"snmp": {"interfaces": [ifIndex, ...]}}`).
  `snmp_checks()` in `plugin_registry.py` then adds, after the OID-table services, one in and one
  out octet service per interface: `snmp-if<N>_in_octets-<port>-udp` (OID `1.3.6.1.2.1.2.2.1.10.<N>`)
  and `snmp-if<N>_out_octets-<port>-udp` (`...16.<N>`). A device with no monitored interface produces
  exactly the services it did before (the fixed interface 3 services `lan_in_octets` / `lan_out_octets`
  stay in the OID table). At most 16 interfaces per device; `interfaces` must be whole numbers
  (`PluginConfigurationError` otherwise). Changes are applied through
  `regenerate_and_apply_config_status()` (via `apply_config_change()`), so the Nagios binary validates
  them and a rejected config is rolled back.
- **Interface discovery** (`network_discovery/interface_discovery.py`). Mechanism: the net-snmp
  `snmpwalk` command (already required by `check_snmp`), run with an argument list and a 20 s limit
  per column, SNMP v2c, over ifDescr, ifName, ifSpeed, ifHighSpeed, ifAdminStatus and ifOperStatus.
  A Python SNMP library was rejected as a large new dependency, and `check_ifstatus` because it
  reports state, not names, speeds and indexes. The port and community follow the SNMP plugin
  rules (config defaults, the port found on the device, `Plugin_Variables["snmp"]`); address, port and
  community are validated before they reach the command, and the community is never returned or logged
  (it is visible in the process list for the length of a walk, as with `check_snmp`). The list is
  refreshed on demand (`POST /hosts/<id>/interfaces/refresh`) and after the scan has saved its results
  (`refresh_interfaces_after_scan()`: best effort, at most 64 devices and 120 s per scan; a device that
  does not answer is skipped).
- **Rate calculation** (`app/bandwidth.py`). `rate = (counter now - counter before) * 8 / seconds`
  between consecutive samples of a service's first perf-data value. A sample's time is the Nagios
  `Last_Check` (when the counter was read), not the stored `Timestamp`: the two differ by up to a
  polling interval, which skewed rates by 17% in the lab. A decrease is a counter wrap when
  the wrapped difference is a believable rate (width detected from the data: above 2**32 means a
  64-bit counter), otherwise a restart, and that interval is left out; a believable rate is at most
  110% of the link speed when known, else 100 Gbit/s. Samples more than 30 minutes apart are not
  compared. Fewer than two valid samples (missing, non-numeric, negative or duplicate readings do not
  count) gives no rate (`null`, shown as insufficient data). Rates are averaged into the requested
  number of buckets; a bucket with no rate is `null`.

### Service identification

A port number is a hint, not proof of the service. The default TCP scan range
is `1-10000` (alternate ports such as 8080, 8443 and 9443 included). TCP scans
use `-sV -O --version-all`. UDP scans run in two steps: `-sU --open` finds the
ports that answer, then `-sU -sV` (with a per-host timeout) probes only those
ports; if the second step fails the port-number names are kept. `service_from_nmap()`
keeps nmap's evidence: `method="probed"` with a real name is a `FINGERPRINT`;
`method="table"` (a lookup by port number) is a `PORT_HINT`; `unknown` and
`tcpwrapped` (the port accepted and closed) are stored as `unknown` with a
`PORT_HINT`; HTTP inside `tunnel="ssl"` is reported as `https`. Discovery then
decides each port's service name, strongest first:

1. `USER`: a service an operator pinned on that device's port through
   `PUT /system/hosts/<id>/ports/<proto>/<port>`. Scans never rename it.
2. `FINGERPRINT`: nmap's probed name, e.g. `ssh` on 2222.
3. `PORT_RULE`: the Port -> Service table (`TCP_Port_Services` /
   `UDP_Port_Services`, defaults `TCP_PORT_SERVICES` / `UDP_PORT_SERVICES` in
   `config.py`), the service an admin *expects* on a port. It names a port nmap
   could not fingerprint, and agrees with a fingerprint of the same service.
   The TCP table always holds `NCPA_PORT -> ncpa`, added when the table is
   read and never stored, so it cannot drift from `NCPA_PORT`; that port always
   takes `ncpa` because deployment configures the agent there and nmap
   fingerprints it as https.
4. `PORT_HINT`: nmap's guess from the port number; never trusted on its own.

**Not used as intended.** When nmap fingerprints a service that contradicts the
table's entry (for example a web server on port 22), the port is not relabelled.
It keeps the service nmap saw, records the table's entry in
`Expected_Service_Name`, and is not monitored until an admin acknowledges it
(`Mismatch_Acknowledged_At`, set through the port-edit route). Acknowledging
accepts the port as the service nmap found. A change in what nmap sees clears
the acknowledgement; pinning the service, or choosing to monitor the port,
settles the flag. A port that is already monitored keeps running while flagged.

The result is stored in `Identified_By` on `Open_TCP_Services` /
`Open_UDP_Services` (NULL for ports recorded before it existed). Plugin Manager
is the switch for monitoring: a `SUGGESTED` port whose service is identified
(pinned, from the table, or fingerprinted) and not flagged starts being
monitored when the plugin that checks it is `Enabled` or `Active`
(`should_auto_monitor`, `promote_identified_ports`). Plugin names come from
`plugin_registry.plugin_for_definition()`. A service with no plugin of its own
is checked by the generic TCP plugin (`check_tcp`), so enabling it picks up every
identified TCP port; UDP is monitored only through a plugin that speaks its
protocol. `AUTO_MONITOR_SERVICES` no longer exists. The plugin reconciler runs
`promote_identified_ports` on plugin enable and disable, after every scan save and
after port edits. A port can be held back from promotion (`Promotion_Held`): it is set
when an admin sets a port to Suggested, and by the upgrade for the Suggested ports the
enabled plugins would otherwise start monitoring. No plugin promotes a held port;
monitoring it by hand or acknowledging a mismatch releases it. A monitored, unpinned port that
fingerprints as a service its frozen plugin does not match keeps its service and
raises a `SERVICE_CHANGED` `DeviceReviewItem`; hints never raise one, and the
NCPA port of a deployed agent is exempt.

Port lifecycle thresholds live in `config.py`: a monitored port unseen for
`PORT_MISSING_AFTER_SCANS` (5) scans becomes `MISSING` and stays monitored; after
`PORT_ARCHIVE_AFTER_DAYS` (30) days as `MISSING` it is archived and its service leaves
Nagios. `PINPOINT_PORT_ARCHIVE_AFTER_DAYS` overrides the 30 days so a test lab can
reach the archived state in minutes (fractions allowed, for example `0.001`); it
must be a number above zero or the application refuses to start, and it is left
unset in production.

The scan leaves the monitoring server out by every non-loopback IPv4 address of
its network interfaces (read with `ip -4 -o addr`) as well as the addresses its
hostname resolves to, so a second network card cannot get the server saved as a
device.

Discovery starts are serialized by an in-process lock around the running-thread
check and worker launch, so simultaneous requests cannot both start a scan. For
a scan observation at an existing address, reconciliation considers ACTIVE,
MISSING, and ADDRESS_UNKNOWN records, preferring an ACTIVE holder when multiple
records share the IP. An ADDRESS_UNKNOWN record is reactivated if the observed
identifiers do not contradict its stored identity; a truly different MAC or
host key remains an IP-reuse review case and is never silently merged. The SSH
identity probe uses the configured SSH port and every port nmap names `ssh`,
including alternate ports such as 2222. A cloned SSH key can be shared by
multiple targets: if a scan observes that key on a known, different device at
its recorded address with its own matching hardware MAC, reconciliation keeps
that device and its newly scanned ports rather than dropping the observation
as a secondary address of the key owner. Similarly, when a network is removed
from discovery settings and a subsequent scan runs on the remaining networks,
a known device in the scanned network is kept by its address rather than being
reassigned to a device from the unscanned network that shares the SSH key. It
records a duplicate-identity review item. A true second NIC of one device still
belongs to its key owner.

## NCPA deployment

The SSH command helpers accept `expected_exit_codes` for probes: the account
existence check (`id`, exit 1) and authorized-key check (`grep`, exits 1 and 2)
log those results at INFO, without command output. Nonzero exits still return
`success: False`, so missing accounts and keys are created as before. Other
nonzero exits, including failing non-probe commands, continue to log at ERROR.

`app/ncpa_deployment/ncpa_deployment.py` installs NCPA over SSH. The workflow
requires explicit SSH host-key fingerprint retrieval/confirmation, uses the
stored fingerprint for subsequent verification, records progress and per-device
results, makes the TLS key readable by the `nagios` user on every deploy, verifies
the listener with an authenticated request, and reads the agent's own logical disk
nodes (`GET /api/disk/logical`, real filesystems whose `used_percent` node
answers) into `NCPADevicePartition.Name` (an NCPA node name such as `|` or
`|data`, not an lsblk partition). Pseudo filesystems (`bpf`, `tmpfs`, ...) and
the `|sys`, `|proc`, `|run`, `|dev` and `|boot|efi` trees are never recorded.
The disk metric path is `disk/logical/{partition}/used_percent`; the path is
stored raw and quoted once by the Nagios command template. During config generation and plugin reconciliation, one authenticated API
inventory request per agent confirms metric paths. Successful inventories are
cached for 60 seconds, failures for 5 seconds, with at most 256 cache entries.
Requests use connect/read timeouts of 1/2 seconds, refuse redirects, limit the
response to 2 MiB and traverse at most 10,000 paths and depth 10. Unsupported
paths are skipped individually through the existing skipped-service mechanism;
failed inventories defer the three added defaults with a retry reason while preserving established checks. No probes run in the
Nagios status poller. Read-only fact loading defaults to no probe.

`NCPA_METRICS` preserves cpu, memory and per-partition disk and adds swap usage
(`memory/swap/percent`, 50/80) and sda read/write rates
(`disk/physical/sda/read_bytes`, `write_bytes`, Mi, `delta=1`, 100/200 MiB/s).
Agents lacking sda skip these two defaults. Saved metric tables retain precedence
and are not extended automatically on upgrade. With sda and P partitions, the
default is 5 + P services instead of 2 + P. No load-average default is added:
NCPA 3.5.0 on the tested agents has no such node. Process checks use path
`processes`, queryargs `name=sshd`, and warning/critical `1:1` for an exact count.
No endpoint, permission or database migration is added.

If a plugin cannot
be planned, the port falls back to the generic TCP check and the fallback is
listed in the run's skipped services.

The deploy helper restarts the agent through systemd, so `ncpa.service` stays
active. Pinpoint's certificate probe ends the TLS session cleanly (NCPA 3.5.0
stops listening if a client drops it), and a deployment fails with "NCPA
stopped listening after the identity check." if the port stops accepting
connections afterwards. A failed install after the bootstrap step reports that
the deployment account, its key, sudo rule and helper remain on the device;
nothing removes them automatically.

Each run records one `NCPADeploymentResult` per device. Its `Outcome`
(`DeploymentOutcome`) moves Pending → Running → Success, Failed, Down
(`UNREACHABLE`: no answer on SSH), or Incompatible; pre-flight rejections are
Rejected and devices not started after a stop are Skipped. A rejected login is
Failed ("SSH authentication failed."), never Down. Hostname and IP are copied
into the row so history survives renames and moves. The run is Success when no
device failed, Failed when none succeeded, otherwise Partial Failure; a stop or
a Nagios config that could not be applied by `add_ncpa_port` keeps that status.

Trust confirmation saves a host key only when the live key equals the
fingerprint the user approved. A device can be deployed to when its agent is
Pending NCPA or Deployment Failed (retry); Deployed and Incompatible devices
are rejected.

SSH is not assumed to be on port 22. `port_lifecycle.device_ssh_port()` picks
the device's SSH port from its recorded TCP ports (a port whose frozen plugin or
service name is `ssh`; hand-added first, then monitored, then `SSH_PORT`, then
lowest; MISSING/ARCHIVED ports are skipped) and falls back to `SSH_PORT`.
Trust confirmation reads the key from that port and stores the port in
`SSHCredentials.SSH_Port` with the approved fingerprint, because a fingerprint
only vouches for the port it was read from; every later connection (the
pre-flight key check at start, the credential check, bootstrap and install)
uses the pinned port, and paramiko host keys
for non-22 ports are registered as `[address]:port`. If SSH moves, the device
must be trust-confirmed again. The remote helper configures the agent's
`[listener]` port to `Config.NCPA_PORT`, and Pinpoint reaches the agent on that
port; deployment has no per-device NCPA port. The helper replaces any
active or commented `port` line in `[listener]` with exactly one, and fails with
"Could not set the NCPA listener port." otherwise. `NCPA_PORT` is a
deployment-time setting (not editable in the UI): changing it after agents are
deployed requires redeploying them. An invalid value is reported as "NCPA_PORT
must be an integer between 1 and 65535." (HTTP 500 from the start route). Discovery's identity probes read
the SSH host key on `SSH_PORT` and on every port nmap identified as `ssh`.

Credentials, tokens, passwords, and secret-bearing command arguments must never
appear in logs, API responses, or persisted Nagios snapshot check commands.

## Alert acknowledgement lifecycle

- One active Pinpoint acknowledgement is allowed per `(hostname, service)`;
  `service = null` identifies a host alert.
- A comment is required when acknowledging.
- Acknowledgement and manual unacknowledgement append `AckHistory` records.
- On a completed nonempty Nagios status poll, a fresh UP/OK check for an acknowledged
  host/service removes its active acknowledgement and appends one actorless
  `AUTO_RESOLVED` history row in a single transaction. Missing or stale checks,
  absent targets, empty/failed polls and still-failing targets retain their records;
  subsequent polls do not duplicate the history event. Freshness uses the configured
  check interval plus 90 seconds for polling/jitter. The poller fetches all service
  lists before reconciling so a later CGI failure cannot partially clear records.

## Migrations

Model changes affect a multi-bind migration environment. From `server/`, with
the virtual environment active:

```bash
flask db migrate --multidb -m "short description"
flask db upgrade --multidb
flask sync-permissions   # after any upgrade: adds new seed permissions, grants them to Administrator
```

`flask sync-permissions` is idempotent and never changes users, other roles or
existing grants. The serving process logs an error at startup if the installed
database lacks any permission in the seed list.

If migrations have never been initialized:

```bash
flask db init --multidb
```

Migrate both databases together. Do not hand-edit generated migrations unless
the generated operations have been reviewed and a manual correction is truly
required.

## Per-device email recipient selections

`HostAlertRecipient` (`HOST_ALERT_RECIPIENT`, default bind, migration
`a79e14c0b621`) links `NetworkDiscovery.NetDiscoveryID` and `User.UserID` as a
composite primary key, with foreign keys to both and a user index. Merge revision
`e79b7d3c2641` joins this migration with interface monitoring (`b7d3f1a9c264`),
allowing normal `flask db upgrade` from either already-applied branch without
rewriting a parent revision or changing data in the merge itself. No assignments
are seeded, so upgraded devices keep their existing default contact group.
There is no user-delete cascade. The standard upgrade `flask sync-permissions`
adds `system.hosts.alerts` and grants it to Administrator.

`create_host_cfg.py` loads assignments once per generation. For each generated
device with eligible selections, it emits `pinpoint_host_<NetDiscoveryID>` with
only Active users whose `Receive_Email_Alerts` is true. That host, discovered
services (including monitored-interface in/out octet checks) and custom device checks reference its group. No selections or no
eligible selections uses `system_users`; if no globally eligible contact exists,
#80's behavior remains: no empty group and no contact_groups directive. Generated
server checks and stock localhost objects retain their existing contact behavior.
Numeric group names do not depend on request strings, addresses or hostnames.

The recipient PUT flushes the candidate assignments, invokes the shared writer
under its re-entrant config lock and commits only after validation and reload
succeed (or the config is unchanged). Failed apply rolls back assignments and
returns the shared writer's error. A successful save writes an activity entry.
Stable device IDs preserve choices across rescans and address/hostname changes.
Device merge unions choices on the target and drops duplicate source choices;
retirement deletes that device's choices. No assignments remain on the merged
source or retired device. Pause preserves choices for resume.

NCPA inventory probing considers only devices with NCPA facts; an SNMP-only device with monitored interfaces does not require an NCPA deployment merely because `check_ncpa` is enabled globally.
