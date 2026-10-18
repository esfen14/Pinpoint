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
- Email settings: `SmtpSettings` (`SMTP_SETTINGS`), the singleton (`Id` 1) behind Settings -> Email: `Provider`, `Host`, `Port`, `Tls`, `Username`, `Sender` and `Password_Encrypted` (Fernet via `app/secrets_store.py`; never returned by the API), with `Version`/`Updated_By`. Saving also applies the settings to `/etc/msmtprc` through the installer's root helper `/usr/local/sbin/pinpoint-apply-smtp` (`sudo -n`, JSON on stdin: `host`, `port`, `tls`, `username`, `password`, `sender`). No row means no mail transport is configured. `Provider` is `gmail` (fixed smtp.gmail.com:587 STARTTLS) or `custom` (helper-valid host and port 1–65535, STARTTLS only). The existing columns support both; no migration or permission change is required. The helper JSON field set remains unchanged.

  `app/nagios/mail_failures.py` reads at most 64 KiB from the current regular `NAGIOS_LOG_FILE` (default `/usr/local/nagios/var/nagios.log`) per settings GET, opening nonblocking and ignoring partial boundary lines. It recognizes Nagios 4.5.11 NOTIFY worker failures and adjacent stderr categories; stdout, command text, addresses and credentials never leave the reader. The last failure is returned as UTC time plus fixed reason, or null for missing/unreadable/nonregular/no-match logs. It is a historical failure in the current tail, not a delivery receipt or current health status; a successful test does not erase it. Rotation/tail eviction can remove the indicator. This diagnostic is not written to either database and does not alter archive-based notification history.
- Plugin settings: `PluginSettings` (`PLUGIN_SETTINGS`), one row per plugin definition (`Plugin_Name`, e.g. `snmp`) holding the variables saved from Settings -> Plugins in `Variables` (JSON), with `Version`/`Updated_By`. No row means the `config.py` defaults apply.
- Device interfaces: `DeviceInterface` (`DEVICE_INTERFACE`, migration `b7d3f1a9c264`), one row per interface SNMP reports for a device (unique per `NetDiscoveryID` + `If_Index`): `Name`, `Speed_Bps` (null when unreported; `ifHighSpeed` is preferred over `ifSpeed`), `Admin_Status`, `Oper_Status`, `Monitored` (the administrator's choice, default false), `Present` (false once a refresh no longer finds a monitored interface) and `Last_Seen_At`. No rows means no change to the generated Nagios config.
- Maintenance windows: `MaintenanceWindow` (`MAINTENANCE_WINDOW`, migration `a4c8e1b7d933`): `NetDiscoveryID` (a device, or null for every monitored device), `Start_At`/`End_At` (first occurrence, naive UTC), `Recurrence` (`none`, `daily`, `weekly`), `Recurrence_Until`, `Time_Zone` (IANA name the recurrence repeats in), `Comment`, `Status` (`active`, `cancelled`, `completed`), `Last_Occurrence_Sent`, `Created_By`/`Created_At`; and `MaintenanceOccurrence` (`MAINTENANCE_OCCURRENCE`), one row per occurrence handed to Nagios, unique per (`WindowID`, `Start_At`), with `Status` (`pending` while retrying, `sent`, `failed`, `cancelled`), `Attempts`, `Last_Error` and `Sent_At`. No rows means nothing changes. The downgrade drops both tables; run `flask sync-permissions` after upgrading to add `maintenance.manage` (Super Admin only).
- Resource forecasts: `ResourceForecast` (`RESOURCE_FORECAST`, migration `b7e2a9c4d518`), the latest forecast per host, service and metric (unique), replaced on every run with no history: `Kind` (`warning`/`critical` with `Threshold`, `Crossing_At` UTC, `Slope_Per_Hour`, `R_Squared`, `Current_Value`, or `insufficient` for a series too new to forecast, where those are null), `Sample_Count`, `Window_Hours`, `Unit`, `Computed_At`.
- Network profile: singleton `NetworkProfile` (`Id=1`) holding the editable name, reference and detail rows of the Network Health info card.
- Audit/logging: `ActivityLog`, `ConfigurationChanges`, `ExportLog`.
- Discovery: `NetworkDiscoveryStatus`, `SkippedService`, `NetworkDiscovery`,
  `Open_TCP_Services`, `Open_UDP_Services`, `DeviceParent` (manual reachability links).
- NCPA deployment: `SSHCredentials` (also `Remote_Restart_Enabled`, default false, and `Remote_Restart_Services`, a JSON list of unit names, both added by `c7a1f4d92e60` for #8 Part 8.3), `NCPADeploymentStatus` (one row per run,
  with `Reviewed_At`/`Reviewed_By`), `NCPADeploymentResult` (one row per device
  per run), `NCPADeployment` (each device's latest agent state and nullable installed `Port`; `Deployement_Method` is Automatic for SSH installs and Manual for an agent registered by the administrator, #130, which needs no migration because the enum already had `Manual`),
  `NCPADevicePartition`.
- Remediation: `RemediationAction` (`REMEDIATION_ACTION`): the admin-defined rule with `Name` (unique), `Action_Type` (`record_only`, `restart_local_service` added by migration `b8e3d5f2a417`, or `restart_remote_service` added by `c7a1f4d92e60`), `Scope_Kind` (service or host), `Host_Pattern`, `Service_Pattern`, `Parameters` (JSON, validated per type), `Enabled`, `Max_Runs_Per_Hour`, `Cooldown_Seconds`, `Version` and `Updated_By`/`Updated_At`; and `RemediationRun` (`REMEDIATION_RUN`): one row per decision with `Event_Key` (sha256 of kind, host, service, state and last state change; unique together with `Action_Id`), `Action_Id` (nullable foreign key to `REMEDIATION_ACTION.Id`, `ON DELETE SET NULL`, migration `a182f6c9d301`; deleting an action keeps its runs and snapshots but detaches its cooldown/hourly history; upgrade clears existing orphan links without removing audit rows), `Action_Name` (a copy), host, service, state, `State_Type`, `Attempt`, `Received_At`, `Started_At`, `Finished_At`, `Outcome`, `Reason` and `Output` (at most 1 KB, redacted). Both live in `system.db` because PinPoint writes them; `history.db` stays Nagios snapshots only. Migration `e4a7c1d9b305` creates both tables and the `remediation.view` and `remediation.manage` permissions, granted to the Super Admin role. Migration `f155a3c7d2b1` (safety controls, #155) adds `SystemSettings.Remediation_Enabled` (the kill switch, default on) and `Remediation_Retention_Days` (default 90), `RemediationAction.Run_When_Acknowledged` (default off), the outcomes `skipped_kill_switch`, `skipped_maintenance`, `skipped_downtime` and `skipped_acknowledged`, and the one-row `RemediationConsumerState` table (`REMEDIATION_CONSUMER_STATE`, Id 1: `Last_Tick_At`, `Last_Error`, `Dropped_Count`, `Dropped_At`; written on every consumer tick, which is why it is not on the settings row). Existing rows keep today's behavior; the downgrade deletes runs with a new outcome and drops the added columns and table.
- Settings: singleton `SystemSettings`, singleton `NotificationPolicy` (`NOTIFICATION_POLICY`, Id 1, migration `143c48cd6663`), one-per-user `UserPreferences`. `NotificationPolicy` stores weekday/HH:MM quiet windows as JSON, host/service option strings, a 0–1440-minute renotify interval, `Version`, and `Updated_By`; the migration seeds the historical 24x7/default-options/30-minute policy and removes the table on downgrade.
- Notification escalations: `Escalation` (`ESCALATION`, migration `cd74e5f8a2d5`) stores `First_Notification` and `Last_Notification` (1–10000, first no greater than last), `Interval_Minutes` (0–1440), `Contact_Group` (an existing generated recipient group) and nullable `HostID` (stable `NetworkDiscovery` foreign key; null scopes to all Nagios hosts and services). Database checks enforce numeric ranges. An empty table preserves generated config byte-for-byte. Upgrade creates only this default-bind table; downgrade drops it without changing recipient/device/history records. Deploy with the existing multi-bind `flask db upgrade`; no new permission or `sync-permissions` change is needed.
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
| System operations | `dataPollingInterval` (Pinpoint reads of Nagios, seconds), `checkInterval` (Nagios-generated host and service checks, minutes), `retryInterval` and `maxCheckAttempts` (how soon a failing check is re-run and how many failures confirm a problem), `flapDetectionEnabled`, `flapLowThreshold` and `flapHighThreshold` (Nagios flap detection for generated hosts and services), update frequency, maintenance mode, automatic backups, log retention, diagnostic-history retention |
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
  `SECRET_KEY`), never returned by the API, and decrypted only during config generation. It is stored
  in the protected resource file and referenced by a bare USER slot identifier in `hosts.cfg`.
  `server/scripts/pinpoint_check_native.py` supplies passwords to `check_nt`, `check_radius` and
  `check_mysql_query` using extra-options stdin after verifying installed help support. Password-bearing
  SMB generation is refused because its child process lacks secure credential transport. Merging a device moves its custom
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
service), schedule downtime (host, service) and cancel downtime by host name and
comment (`DEL_DOWNTIME_BY_HOST_NAME;host;;;comment`, which removes the host's and its
services' downtime with that exact comment; the comment is required, since a blank one
would delete all of the host's downtime). Each line is `[epoch] COMMAND;args`, built only after validation: host,
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

Per-service recovery (#154): `/api/system/remediation/services/...` stores nothing new. The switch is one `RemediationAction` with `Scope_Kind` service whose `Host_Pattern` and `Service_Pattern` are the exact Nagios host and service names, so the Remediation page and the config renderer see the same row. The server maps a check name to a unit by its first word (`ssh-22-tcp` gives `ssh`, plus the fixed `SERVICE_UNIT_ALIASES` in `app/remediation.py`, for example `ssh` and `sshd`) and uses a unit only when it is on that device's own restart list (`SSH_CREDENTIALS.Remote_Restart_Services`) or, for host `localhost`, in `RESTARTABLE_UNITS`. No model, migration or permission was added.

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

### Operator notification for automatic recovery (#153)

Migration `e153c4a8b2d7` (after `f155a3c7d2b1`) adds `RemediationAction.Notify_On` (JSON list of
`failed`, `capped` and `repeated`, default all three, may be empty), `RemediationRun.Notify_Kind`
(`failed`, `capped` or `repeated`; null when no notification was due), `Notify_State`
(`pending`, `sent`, `failed`; null when none was due), `Notify_Attempts` (default 0), `Notify_Error`
(a fixed sentence, at most 200 characters) and `Notify_At`, and `SystemSettings.Remediation_Repeat_Count`
(default 3, range 2 to 20) and `Remediation_Repeat_Window_Hours` (default 24, range 1 to 168).
Existing rows keep today's behavior (nothing due, defaults as stated); the downgrade drops the
added columns and keeps every run.

`app/remediation_escalation.py` owns the rest. A run is marked for a notification when its outcome
is `failed` or `timed_out` (kind `failed`), `skipped_cooldown` or `skipped_hourly_cap` (kind
`capped`), or when it succeeds and the same action has now succeeded `Remediation_Repeat_Count`
times for the same host and service inside the window with no `repeated` notification in the
window (kind `repeated`), and only when the action's `Notify_On` lists that kind. The deliberate
skips (kill switch, Maintenance Mode, downtime, acknowledged) never notify. The consumer marks the
run in the same commit that records its outcome. Every consumer tick then calls `deliver_pending`:
each attempt is counted and committed before it is sent, so a stop in the middle is never sent
again (`fail_unfinished` runs at startup and fails such a run); a failed send keeps the run
`pending` with a fixed error until `MAX_ATTEMPTS` (3) is reached, then `failed`. Nothing here raises,
so a missing or unwritable command file is recorded on the run and the consumer carries on.

The notification is a Nagios custom notification written through `app/nagios/commands.py`
(`SEND_CUSTOM_SVC_NOTIFICATION` for a service, `SEND_CUSTOM_HOST_NOTIFICATION` for a host) with
option `0`: the force option is never set, so Nagios still applies notification-enabled flags,
scheduled downtime, timeperiods and escalations, and Nagios alone chooses the recipients. The
comment is fixed text plus the action name (reduced to letters, digits and `. _ : / -`), the
outcome code and the run id; plugin output and command output never reach it. Because the message
is written to the Nagios archive, it appears in the notification feed without a PinPoint-owned
notification table.

`Config.NAGIOS_HOST` is the CGI network host. In contrast,
`api/system/statistics.py` uses `NAGIOS_HOST = "localhost"` to identify the
Nagios server within status data. Changing either requires understanding its
different purpose.

## Service report history and coverage (#198)

Network Services and Device Services read `archivejson.cgi` availability through
`app/nagios/service_availability.py`, not `ServiceStatus` snapshot counts.
Snapshots and the general poller remain available for their existing consumers.
The exact `(host_name, description)` identifies a native instance; service
names are preserved verbatim. Only configured objects in the archive response
are counted; historical removed objects are not guaranteed.

Explicit options: `availabilityobjecttype=services`, `statetypes=hard`,
`assumeinitialstate=false`, `assumestateretention=true`,
`assumestatesduringnagiosdowntime=false`, `backtrackedarchives=4`.
There is no report-timeperiod restriction. Four preceding archives are searched
for initial state; actual coverage depends on Nagios's rotation, retained logs,
recorded checks and engine events, not Pinpoint snapshot retention. Missing logs
cannot be recovered by these reports. Unlike existing host-report defaults, these
service reports explicitly avoid assuming an initial state or state during engine
downtime; this intentional difference is explained in the UI and operator guide.

Native `time_STATE` and `scheduled_time_STATE` are separate accumulators in Core
4.5.11. Add the matching scheduled component to each normalized state exactly
once, preserving maintenance in headline availability. UNKNOWN is observed and
belongs in known time. Native no-data and engine-down time are excluded. Native
all-zero responses can leave the requested range unexplained, so expose
`unaccounted_seconds = window - known - native_no_data - native_engine_down`.
Total missing coverage is native no-data + engine downtime + unaccounted seconds.
An unaccounted duration asserts no state or cause. Reject negative/nonfinite
values, wrong shapes, duplicate identities, and totals exceeding the window.

Core can synthesize current state for no-history objects when a range includes
its query time, even with `assumeinitialstate=false`. Service reports request
completed seconds, ending strictly before query time; the normalizer checks this
against the millisecond native `result.query_time`. A clock disagreement fails
closed. This avoids that pseudo-state path; it does not reconstruct unobserved
outages or turn missing history into healthy time. Raw seconds are aggregated
before percentages: Network Services by exact service description; Device Services
by hostname. A device aggregate measures its services, not host uptime. A null
percentage means no known time; zero-known instances still contribute coverage
and instance counts.

Current state/timestamps/output are fetched in one read-only bulk
`statusjson.cgi?query=servicelist&details=true&formatoptions=enumerate` request.
The reader never calls the snapshot-writing status poller. It joins full identity,
retains pending/missing metadata as absent, and records a separate observation time.
Historical archive failure aborts; current-status failure is a visible partial
result. No new dependency, database model, migration, permission, credential,
monitoring-config change or scheduler job is introduced.

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
| Data polling interval (`dataPollingInterval`) | System-wide `SystemSettings.Data_Polling_Interval`: exactly 30, 60 (default), 120 or 300 seconds, in Settings → System with `settings.system`. Migration `f6d2c8a1b390` gives existing installations the same 60-second default as new ones. Pinpoint reads Nagios CGI status independently of discovery, check/retry timing and browser refresh. Unchanged `Last_Check` does not add another host/service or performance row. |
| Dashboard Refresh Rate | Per-user browser fetch, Manual/1/5/15 minutes, independent of the other schedules; its hint shows the saved Check interval, Data polling interval and the selected personal refresh rate (including Manual). |

A new Nagios result can take up to one poll cycle to appear in Pinpoint, then
up to one browser refresh cycle to appear in the dashboard. Discovery scans
are not part of that latency or the check freshness threshold.

## Appliance storage and Nagios log access

`app/storage_usage.py` measures the SQLite files returned by
`automation.database_file_paths()` (in-memory databases omitted),
`DATABASE_BACKUP_DIR` and `NAGIOS_LOG_ARCHIVE_DIR`. File lengths use `os.stat`;
folders sum regular-file lengths, skipping symlinks, with budgets of 10,000
entries and 0.1 seconds per directory tree. `complete=false` marks a partial
folder total, which the UI labels “At least”. Missing/unreadable paths have
`bytes=null`, never a fabricated zero. `shutil.disk_usage` reports free/total
bytes separately for every location, including split mounts. A missing path
uses its nearest existing parent for disk space. No internal directory paths
are returned. This is a current measurement on each dashboard-status request,
independent of host count or monitoring plugin configuration; it creates no
model or migration.

`app/nagios_log.py` reads only the trusted `NAGIOS_LOG_PATH`, default
`/usr/local/nagios/var/nagios.log`. It opens read-only, nonblocking, without
following a final symlink, checks for a regular file and seeks to the last
64 KiB. A clipped first record is discarded. It returns at most 500 lines
(default 200) in file order, newest last, with optional exclusive `after` Unix
seconds. Unterminated final lines are supported. Unknown/unparseable timestamps
are omitted when `after` is positive. Missing, unreadable, symlinked and special
files give an empty unavailable result. It never loads the whole log or accepts
a path from HTTP. Host/service alert and current/initial state records keep
validated host/service names, state/type/attempt fields; plugin output and all
other messages, including commands and debug content, are replaced with
redaction markers. Hostnames and addresses can remain visible. This
conservative policy avoids guessing which free-form arguments are secrets.
Nagios continues to own log rotation; Pinpoint does not modify its logs.

## Scheduler and retention

`scheduler.py` runs:

- Nagios status polling at the persisted Data polling interval, with an immediate first run.
- Daily purging based on `Log_Retention_Days` and
  `Diagnostic_History_Retention_Days`.
- Settings-driven automation checks every `AUTOMATION_CHECK_MINUTES`.
- Maintenance window dispatch every 60 seconds (`maintenance_windows`, `app/maintenance.py`).
- Resource forecasts every 30 minutes (`resource_forecast`, `app/forecast.py`, `max_instances=1`, `coalesce=True`): see "Resource forecasts" below.
- The remediation spool consumer every 15 seconds (`max_instances=1`); at startup, runs left
  `running` by a stop become `interrupted` and are never run again.

The daily purge also deletes `RemediationRun` rows older than
`Remediation_Retention_Days` and event files in the remediation spool older than 7 days
(only files with the handler's names; other files are left alone). A spool of more than 1000
files is cut back on every consumer tick, oldest first, and the number dropped is stored in
`RemediationConsumerState` and logged.

Saving a changed polling interval reschedules the existing `nagios_poll` job in
place; the next run is one new interval after the save. Unchanged saves preserve
the next run. `max_instances=1` and `coalesce=True` stay enabled: a running poll
finishes normally, overlapping due runs are skipped, and accumulated due runs
coalesce. Settings saves are serialized within the serving process (the supported
deployment has one worker). The old trigger and next run time are restored on a
reschedule, audit or persistence exception, and the database transaction rolls
back; the API returns an error. A disabled scheduler stays disabled on save and
reads the persisted interval when next started. No other job cadence changes.

`automation.py` can schedule database backups, network discovery, plugin update
scans, and plugin security validation. Scheduled network discovery runs only if
at least one scan has already been recorded; a fresh installation waits for an
administrator to trigger the first scan manually. Maintenance mode permits backups but
stops the other automated operations.

Backups are folders `YYYYMMDD-HHMMSS` under `DATABASE_BACKUP_DIR`, one SQLite
online-backup copy of each database, newest 7 kept. They are restored with
`flask restore-backup` (`backup_restore.py`), which keeps the replaced files in
`pre-restore-<timestamp>` in the same directory (not rotated). No model,
migration or setting is added. Cold-standby recovery only: active/passive
failover, Nagios configuration backup and the NCPA deployment key are not
covered (`docs/manuals/Backup_and_Restore.md` lists what is not backed up,
including `SECRET_KEY`). Jobs are attributed to an active user for
audit purposes.

## Maintenance windows and Nagios downtime

### Resource forecasts

`app/forecast.py` estimates when a disk or memory metric reaches its warning or critical
threshold. It reads `ServicePerfData` joined to `ServiceStatus` in `history.db` for the NCPA
metrics `disk/<partition>/used_percent` and `memory/virtual/percent` over the last 72 hours,
averaged per hour in SQL (so a series is at most 72 points), and fits a least-squares line.
The nearest threshold the latest value has not reached gets a crossing time. No forecast is
made when there are fewer than 12 hourly points, they span less than half the window, the
slope is flat or falling, R squared is under 0.8, one fall exceeds half the series range (a
cleanup or reset), no threshold is left, or the crossing is more than 90 days away. A series
with too little history is stored as `insufficient`. A run makes at most five SQL statements
however many services exist (one for the series list, capped at `MAX_SERIES_PER_RUN` = 500,
one for the hourly averages of exactly the selected host/service/metric tuples, one device
lookup, one delete and one bulk insert). Mixed forecast/insufficient rows use identical
insert columns, including explicit nulls, so insertion remains one batch. Runs rotate in
host/service/metric order, wrapping within the capped query, so eligible series beyond the
cap receive a later turn. The process-local cursor advances only after commit, including
when the batch produces no forecast; a scheduler restart begins traversal again. Each run
replaces the previous batch's stored set (at most 500 rows), rather than retaining earlier
batches. Paused, retired and merged devices are skipped. A forecast only reads `history.db` and writes
`RESOURCE_FORECAST`; it never changes a Nagios state, config or notification. Delivering a
forecast as a notification, with a horizon and on/off setting, is not implemented.

`app/maintenance.py` turns a `MaintenanceWindow` into Nagios scheduled downtime through
the command channel. The dispatcher runs every 60 seconds with the server's clock (the
Nagios server's clock on an appliance). For each active window it finds the occurrence
running now or next; when that starts within 10 minutes it claims a
`MaintenanceOccurrence` row (committed before anything is sent, unique per window and
start, so a restart or an overlapping run never schedules it twice) and sends
`SCHEDULE_HOST_DOWNTIME` for each host in scope and `SCHEDULE_SVC_DOWNTIME` for each of
its services in the latest snapshot, with a fixed start and end so Nagios ends the
downtime itself. Host downtime alone does not raise a service's `Scheduled_Downtime_Depth`,
hence the per-service commands. Every downtime carries the comment
`PinPoint maintenance window <id> starting <epoch>`; cancelling or editing deletes by that
comment, so only downtime PinPoint created for that occurrence is touched. A failed send
(pipe unavailable, scope device paused or absent from Nagios) leaves the occurrence
`pending` and is retried on the next runs, each retry first deleting what the earlier
attempt left; after 3 attempts it is `failed` with the reason in `Last_Error`, shown on the
Maintenance page and written to the activity log. A window with no occurrence left is
marked `completed`. Daily and weekly windows repeat at the same local time in their
`Time_Zone`, with the same length. `DEL_DOWNTIME_BY_HOST_NAME` was checked on the Docker
lab's Nagios 4.5.11 (`docs/test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md`).
This path is injection-sensitive: it only calls the closed functions in `commands.py`.

## Network discovery and Nagios configuration

`app/network_discovery/network_discovery.py` performs host/TCP/UDP discovery.
`create_host_cfg.py` stores results, plans plugin-backed services, writes a
candidate Nagios host configuration, validates it with the Nagios binary,
backs up the running configuration, and applies only a valid candidate.

By default, a device with generated NCPA metrics also gets a visible
`pinpoint-ncpa-port-<port>-tcp` listener service when `check_tcp` is enabled.
Each metric has a `servicedependency` on that exact service with
`notification_failure_criteria c,u` and `execution_failure_criteria n`:
failed/unknown port checks suppress metric notifications, while metric checks
and their status snapshots continue. If the port service is absent, no rule is
written. `PINPOINT_NCPA_NOTIFICATION_DEPENDENCIES=off` omits both the listener
and these dependency objects, preserving the previous generated service list.
The setting defaults on, is read at application startup, and takes effect on
the next `regenerate_and_apply_config_status()` after restart. The shared
writer still validates with Nagios and rolls back a rejected candidate. Nagios
itself suppresses same-host service notifications while their host is DOWN;
there is no cross-type host-to-service dependency object.

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

### SNMP version and v3 credentials (per device)

`Plugin_Variables["snmp"]` may hold `protocol` (the `check_snmp -P` value: `1`, `2c`, `3`),
`community`, and for version 3 `security_level` (`noAuthNoPriv`, `authNoPriv`, `authPriv`),
`v3_user`, `auth_protocol` (`MD5`, `SHA`) and `priv_protocol` (`DES`, `AES`), written only through
`device_plugin_variables.py`. The two passphrases are stored encrypted (`secrets_store`, Fernet) as
`auth_password_enc` and `priv_password_enc`; no API returns them. No migration: the column and
its JSON shape already existed, and a device without an override renders exactly as before.

- **Version 1, 2c or none** use the `snmp` definition and `pinpoint_nd_snmp` unchanged.
- **Version 3** selects `SNMP_V3_DEFINITION` (`plugin_registry.py`, command `pinpoint_nd_snmp_v3`,
  outside `PLUGIN_DEFINITIONS` so no port resolves to it). It has no community argument, fixes `-P 3`
  and renders `-L -U -a -x` from the variables. `validate_snmp_v3()` checks the fields the level needs;
  a device missing one (or whose stored password can no longer be decrypted) has its SNMP port
  skipped with a reason, never rendered without credentials.
- **Passwords.** `load_host_plugin_facts()` decrypts them into memory; `collect_snmp_secrets()` keys
  them `snmp_v3:<device>:<name>` for the resource-slot allocator, and `apply_secret_substitutions()`
  replaces each `--auth-slot` / `--priv-slot` value with a bare `USERn` identifier. The command
  definition runs `check_snmp` under `scripts/pinpoint_check_native.py`, which reads the slots from
  the protected resource file and gives `check_snmp` the passphrases on stdin as `--extra-opts`.
  `hosts.cfg` therefore holds no passphrase and neither does `check_snmp`'s own argument list.
  **Limit:** `check_snmp` passes the passphrases to its `snmpget` helper in that helper's arguments
  for the moment a check runs, so a local user could see them in the process list then. This is not
  claimed to meet the "no secret in child processes" rule of Engineering Standards; closing it needs
  a different SNMP client (see Implementation_Status).
- **Slot limit.** v3 passphrases share the 255 resource slots with NCPA tokens and custom-check
  passwords; exhaustion refuses generation with the existing safe message (422 from the API).
- **Interface discovery** uses `snmpwalk -v2c`, so a v3 device reports "supports SNMP v1 and v2c only".

### Mail and web service checks (per device)

Mail and web checks have options that an administrator sets per device and service, stored in
`Plugin_Variables[<plugin>]` and written only through `device_plugin_variables.py` (no migration:
the column and its JSON shape already existed). A device without an override renders exactly as
before; `tests/unit/test_plugin_registry.py` (`TestUnchangedDefaults`) pins the command of every
existing definition.

| Service | Check | Variables (all optional, default in brackets) |
|---|---|---|
| `pop3` (110), `pop3s` (995, TLS) | `check_tcp -M crit [-S] -e` | `expected_text` (`+OK`), `warning`, `critical` |
| `imap` (143), `imaps` (993, TLS) | `check_tcp -M crit [-S] -e` | `expected_text` (`* OK`), `warning`, `critical` |
| `http`, `https` | `check_http` | `expected_text` (`-s`), `expected_status` (`-e`), `method` (`-j`), `virtual_host` (`-H`), plus the existing `url`, `warning`, `critical` (and `certificate_days` for https) |

- **Mail.** `check_pop` and `check_imap` are not in the bundled catalog, so the four definitions
  use `check_tcp`, which compares the greeting the server sends on connect with the expected text.
  `-M crit` makes a wrong greeting CRITICAL (`check_tcp` reports it as WARNING by default). The TLS
  variants add `-S`. They are reached by the service name `pop3`, `imap`, `pop3s` or `imaps`
  (discovery names TLS-wrapped POP3 and IMAP that way). A port that was already monitored keeps the
  plugin frozen when monitoring started (`generic tcp`); use **Set service** on it to switch.
- **Web.** The new options render after the existing ones, so a default command is unchanged.
  `virtual_host` cannot be an option of the standard command: `check_http -H` is the address there.
  Once it is set, `command_definition_name()` selects `http_vhost` / `https_vhost`
  (`WEB_VHOST_DEFINITIONS`, command `pinpoint_nd_http_vhost`, outside `PLUGIN_DEFINITIONS` like
  `snmp_v3`), which passes the device address as `-I` and the virtual host as `-H`. Each device
  setting applies to every port of that service on the device.
- **Validation.** `validate_variable_value()` rejects, naming the variable and never its value:
  the forbidden characters (single and double quotes, the backtick, `!`, `$`, `;` and the backslash, line breaks, NUL), an `expected_status` that is not
  one to ten HTTP status codes from 100 to 599 separated by commas, a `method` outside
  GET, HEAD, POST, PUT, DELETE, OPTIONS and PATCH (upper case), and a `virtual_host` that is not a
  host name (letters, digits, `.`, `-`; up to 253 characters; it cannot start with `-`). Values are
  single-quoted in the generated command line. The API answers 400 with `data.field`.
- **Authentication headers and passwords for web checks are out of scope** (they need the secret
  handling of Issue #16 first). Nothing else about the command, the secret slots or the Nagios
  pre-apply validation changes.
- **Decision on `nrpe`.** The `5666 -> nrpe` entries of `TCP_PORT_SERVICES` and `UDP_PORT_SERVICES`
  are kept: no check depends on them, `test_discovery_settings.py` resolves them, and removing a
  default would change what an upgraded installation proposes for the port. Remove them in a change
  that owns that migration if the team wants them gone.

#### Services checked at port level only

The registry contains only plugins in the bundled catalog (`spec files/Plugins_List.md`); custom and
community plugins are out of scope by team decision. A service without a bundled plugin is therefore
checked by the generic `tcp` plugin, which proves that the port accepts a connection and nothing more:

- **Database engines:** Microsoft SQL Server, Oracle and MongoDB (only MySQL and PostgreSQL have a
  bundled plugin; `check_dbi` and `check_oracle` need credentials and are unavailable).
- **Application servers:** JBoss, WebLogic and Citrix.
- **Anything else** nmap names but the registry does not (for example `smtps`, `submission`,
  `ldap` on a non-default setup without a base DN, `redis`): port level.

These services still appear in Device Inventory and still alert when the port stops answering;
what they lack is a check of the service's own reply. Web and API services are covered by `http`
and `https` for the status code and the response text, not for authentication. The user guide is
[Application checks](../docs/manuals/Application_Checks.md).

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
`PORT_HINT`; HTTP, POP3 and IMAP inside `tunnel="ssl"` are reported as `https`,
`pop3s` and `imaps` (`TLS_SERVICE_NAMES` in `network_discovery.py`), so they get a TLS check. Discovery then
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
   The defaults are 22 `ssh`, 80 `http`, 443 `https`, 110 `pop3`, 143 `imap`, 993 `imaps`
   and 995 `pop3s` (the four mail names were added by issue #131). Only a table that was
   never saved from Settings picks up new defaults; a saved table is the administrator's
   and is not changed.
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

Migration `e4a129c7b630` joins the deployed-port revision `7db78f308ee5`
and device-interface revision `b7d3f1a9c264` into one head. Run the normal
multi-bind `flask db upgrade`: installations at either prior head apply the
missing branch, then the schema-free join. Prior revision identifiers and
ancestry remain unchanged, preserving already-upgraded installations.
Migration `f129a79e6301` then joins that head with the independently published
interface/recipient merge `e79b7d3c2641`. It adds no schema/data changes and
restores one head for both binds after the recipient feature is integrated.
Upgrades from either merge preserve installed port, interface and recipient data.
Migration `a129f6d23901` joins `f129a79e6301` with the independently published
data-polling revision `f6d2c8a1b390`. The join changes no schema or data, keeps
applied ancestry intact and restores one upgrade head on both database binds.
Existing custom polling intervals remain unchanged.

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
inventory request per agent on its stored deployed port (falling back to `NCPA_PORT`) confirms metric paths. Successful inventories are
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
nothing removes them automatically. A user with `system.deploy.ncpa` can run the
explicit failed-deployment cleanup route, using request-only SSH credentials. It
rechecks the pinned fingerprint before any remote command, removes the bootstrap
key, sudo rule and helper, and optionally removes the account after those steps
succeed. It reports each step without remote command output, logs the outcome,
and returns the device to Pending NCPA only when every requested step succeeds.
Untrusted, non-failed or currently deploying devices are refused.

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
`[listener]` port to `Config.NCPA_PORT` and records that installed port in
`NCPADeployment.Port`. Checks, disk/reachability/certificate probes, relocation
and protected port handling use the recorded port, falling back to `NCPA_PORT`
when absent. Migration `7db78f308ee5` backfills deployed rows with the configured
port and downgrades by dropping the column; failed/pending rows remain NULL.
The column tracks deployment state; it is not a user-editable re-port setting. The helper replaces any
active or commented `port` line in `[listener]` with exactly one, and fails with
"Could not set the NCPA listener port." otherwise. `NCPA_PORT` is a
deployment-time setting (not editable in the UI): changing it after agents are
deployed does not relocate existing listeners or change their stored ports. A
listener change requires a separate supported deployment workflow; this release
has no re-port control. An invalid value is reported as "NCPA_PORT
must be an integer between 1 and 65535." (HTTP 500 from the start route). Discovery's identity probes read
the SSH host key on `SSH_PORT` and on every port nmap identified as `ssh`.

Credentials, tokens, passwords, and secret-bearing command arguments must never
appear in logs, API responses, or persisted Nagios snapshot check commands.

## Check-secret resources

`network_discovery/resource_macros.py` owns only the exact `# BEGIN PINPOINT` /
`# END PINPOINT` block in `Config.NAGIOS_RESOURCE_CFG` (environment
`NAGIOS_RESOURCE_CFG`, default `/usr/local/nagios/etc/resource.cfg`). USER1 stays
reserved for plugins; USER2 through USER256 are allocated deterministically to
secret keys, excluding slots defined outside the block. Key/slot metadata in
comments retains assignments across regenerations; removed keys free slots and
removing the last secret clears the owned entries. Exhaustion refuses generation
with a safe count/limit message. Malformed blocks or slot collisions are rejected.

Resource replacement uses a unique private temporary file, retaining the existing
owner, group and mode. Other-user permissions are refused. Production ownership
must remain `nagios:nagios` with mode 0660. When the application is not the owner,
updates and rollback use `/usr/bin/sudo -n /usr/local/sbin/pinpoint-apply-resources`
with no command arguments. Only the validated owned block (or null to remove it),
an assertion of the fixed resource path and a digest of the external regions go
on stdin; external replacement content never goes to the helper. The helper
independently retains external bytes and metadata. Missing, rejected or timed-out
helper calls fail safely without exposing stdout/stderr; successful calls require
byte and metadata verification. This helper supports only the default resource
path; a foreign-owned custom resource path is refused. A process-owned custom
path still uses the direct atomic writer. A missing or unwritable required resource file prevents
candidate publication. Generated and successfully applied live `hosts.cfg` use
0640; the live owner/group are preserved. Secret substitution changes only the
known password/token fields, not matching text in public arguments.

Discovery, post-deployment generation and the shared regeneration path snapshot
resource bytes in memory before generation under `config_write_lock`. Generation,
validation, apply failure or cancellation restores the original bytes; failed
application restores both files before reloading the old configuration. Resource
changes require validation/reload even when normalized hosts.cfg is unchanged.
No secret backup file is left on disk. Generated NCPA commands run
`server/scripts/pinpoint_check_ncpa.py` under `/usr/bin/python3 -I`, passing a bare
USERn identifier instead of an expanded macro. The adapter reads the private owned
slot and supplies the token to the inspected NCPA 1.2.4/1.2.5 client's options in
memory, executing it in the same process. Unsupported versions, malformed resources,
credential/diagnostic flags and credential-bearing output fail with safe UNKNOWN
results. Public metric/options, plugin output, performance data and return codes
are retained. Native custom checks use verified extra-options stdin; passwords
with surrounding whitespace are refused rather than altered by the INI parser.
No adapter is privileged or imports Flask. Automated parent/child process tests
pass. Installed service-user writes, resource validation and exact rollback have
also passed; four real NCPA adapter metrics matched the stock client as `nagios`.
Applying/reloading the complete generated configuration and final live Nagios
acceptance remain incomplete; see
[the issue #129 transport plan](../docs/plans/Issue_129_Check_Secret_Transport.md).

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
flask db migrate -m "short description"
flask db upgrade
flask sync-permissions   # after any upgrade: adds new seed permissions, grants them to the built-in role (Super Admin)
```

`flask sync-permissions` is idempotent and never changes users, other roles or
existing grants. It also renames the built-in role from its legacy name
`Administrator` to `Super Admin` on installs seeded under the old name (a
pre-existing `Super Admin` role is left untouched and the legacy role is moved
to `Administrator (Legacy)`, never merged). The serving process logs an error
at startup if the installed database lacks any permission in the seed list.

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
adds `system.hosts.alerts` and grants it to Super Admin.

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


## Manual parent relationships

`DeviceParent` (`DEVICE_PARENT`, default bind) stores manual reachability edges with
composite primary key `(Child_ID, Parent_ID)`, foreign keys to stable device IDs,
a parent index and a self-link check. New/upgraded devices have no parent links by
default. Iterative graph validation rejects cycles through any parent path; a
parent-set replacement is atomic and rejects duplicates, missing IDs and retired/
merged parents. Discovery never infers parents. Merge rewrites both ends,
deduplicates and refuses self-links/cycles; explicit and automatic retirement clear
relationships in the retirement transaction. Pause preserves manual choices.

Configuration loads parent pairs once and includes only names present in the candidate
whose parent remains actively checked (including Missing, excluding paused, retired,
merged and address-unknown). Parent host names must match `[A-Za-z0-9_.-]+`; no
request strings enter a directive or shell command. Multiple parents become Nagios's
comma-separated `parents` list. No eligible parents leaves the original host output
unchanged. API summaries and topology edges explain omitted parents. Parent changes
use the existing shared pre-apply validation, config lock and resource/host rollback.

The topology read model uses existing inventory records and latest stored Nagios
snapshots with a fixed number of database queries; it does not compute reachability,
probe devices or collect interface/traffic telemetry. React computes graph positions.

Migration `b117d9a2c041` follows `a129f6d23901`. It was generated with the
repository's multi-bind Alembic environment and reviewed: only `DEVICE_PARENT`
and its index/constraints are added on the default bind; history has no schema
change. Run `flask db upgrade` for both binds. No permission is added. Downgrade
removes parent relationships while retaining devices and monitoring history.
The populated migration regression verifies default-empty parents, multiple-parent
storage, foreign keys/uniqueness/self-link constraints and downgrade/re-upgrade.
Parent transactions ask the shared writer to defer its history commit until the
route commits the graph and audit entry; lifecycle edits also synchronize the
existing Plugin Manager derived rows before committing.


Nagios still owns state classification and notifications. Declaring multiple
parents does not create alternate network routes. The accepted contract for #173
is Option A: a transient child DOWN notification is allowed before Nagios confirms
parent reachability. One-attempt monitoring remains supported. A recent cached UP
parent result can cause a failing child to be classified DOWN; with
`max_check_attempts=1`, that failure can immediately become HARD and notify under
the configured notification policy. Later checks classify a still-failing child
UNREACHABLE when all rendered parents are DOWN or UNREACHABLE. A parent still UP
means a failing child is DOWN; a responding child is UP. This depends on subsequent
checks and updated reachability information, not a fixed timeout.

See [the observed trial and follow-up](../docs/test-runs/2026-10-15-issue-117-manual-topology/REPORT.md).
The default-three-attempt routed trial passed; it does not prove immediate
child-DOWN suppression for every timing/cache configuration. The check interval
controls scheduled check frequency, while maximum attempts controls failure
confirmation; discovery scans and Pinpoint data polling are independent.
No cache, retry or notification setting is changed by this decision or by selecting
parents, and hosts without eligible parents retain their existing behavior.
See the [operator guidance](../docs/manuals/Notification_Policy.md#parent-outages-and-temporary-child-down-alerts).

### Escalation rendering and recipient ownership

`network_discovery/recipient_groups.py` is the shared Active/opted-in eligibility
calculation for the config writer and escalation options. It returns the existing
`system_users` and per-device `pinpoint_host_<numeric ID>` groups; it introduces
no new recipient model. Empty known groups remain available with zero members
for explanations, but no empty group or dependent escalation is written.

`host_config_templates.create_escalations()` renders host and service escalation
templates into the same candidate file as contacts and hosts. Global scope uses
fixed Nagios wildcards; device scope uses the current generated stable host name,
rejecting config metacharacters. Scoped absent/paused/retired/merged hosts are
omitted; a scoped host with no generated service receives only a host escalation.
Groups referenced by escalations are emitted once even if their source device
currently has no generated host. Account opt-out/deactivation triggers the
existing shared config rebuild, which omits now-empty escalation groups and
ranges without deleting their saved choices. They resume when members return.

Nagios owns notification counting and suppression. During a matching range the
escalation group replaces the normal recipients; overlapping ranges combine
eligible escalation contacts and use Nagios's shortest interval. Normal contacts
resume outside the range. Interval zero sends once during that range. The
existing notification policy, quiet hours, acknowledgements and downtime still
apply. Counts are finite in this interface (no special last-notification zero).
All mutations go through `regenerate_and_apply_config_status()` with the shared
config lock held through commit and rollback on validation or reload failure.

### Escalation migration convergence

Schema-free merge revision `99f584ed8151` joins the published escalation
revision `cd74e5f8a2d5` and remediation revision `e4a7c1d9b305`. Existing revisions
and their ancestry are unchanged. Normal multi-bind `flask db upgrade` applies
whichever branch is missing and reaches one head on each bind. Downgrading only
this join preserves both parents' schemas and existing escalation choices,
remediation actions/runs, recipient selections, deployed NCPA ports, interfaces,
polling preferences and history data.


### Topology migration convergence

Because main later added `a4c8e1b7d933` (maintenance windows) and
`b8e3d5f2a417` (remediation restart), schema-free revision `d117f3b8a053` joins
`c117e6a9d042` with `b8e3d5f2a417` so the tree again has a single head. Remediation safety
controls `f155a3c7d2b1` follows `b7e2a9c4d518` (resource forecast, which follows the run-to-action link `a182f6c9d301`, which follows the remote
restart revision `c7a1f4d92e60`), so the tree still has one head.

Schema-free merge revision `c117e6a9d042` joins the published manual-parent
revision `b117d9a2c041` and escalation/remediation head `99f584ed8151` without
rewriting either ancestry. Normal multi-bind `flask db upgrade` applies the
missing branch and reaches a single head on both binds. Populated upgrades from
both prior heads preserve manual parent sets, escalation choices, remediation
actions/runs and device/history data. Downgrading only the join retains both
schemas and their rows.

## Remote restart policy and history integrity (#182)

The NCPA bootstrap installs a root-owned second helper and sudoers rule for
`restart_remote_service`, with a root-owned per-device allowlist. A saved list
reaches the device through cleanup and redeployment. Trusted deployed devices,
as well as failed deployments, support this workflow. Cleanup clears
`SSHCredentials.Key_Installed` even when only some steps succeed, so remote
restart remains blocked until deployment succeeds. The restart preference and
service list are retained for redeployment.

The run/action foreign key preserves `Action_Name` and all audit fields after
an action is removed; its nullable link is cleared in the same transaction as
action deletion, including when SQLite FK enforcement is off. Rejected Nagios
configuration rolls back both deletion and detachment. Existing links to missing
actions are cleared during upgrade; historical misattribution from IDs already
reused before this migration cannot be reconstructed automatically.
