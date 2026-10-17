# Backend Modules and Route Catalog

**Last verified against the repository:** 2026-10-08

## API composition

`server/app/api/__init__.py` mounts the API blueprint at `/api`. Its child
blueprints are:

| Blueprint | Prefix | Owning package |
|---|---|---|
| `user_bp` | `/api/user` | `app/api/user/` |
| `system_bp` | `/api/system` | `app/api/system/` |
| `plugin_bp` | `/api/plugin` | `app/api/plugin/` |

All protected routes use the Flask-Login session cookie. Permission-protected
routes add `@require_permission(...)` to `@login_required` behavior.

The seed command currently defines these permissions:

```text
role.edit, role.view, role.info, role.list
account.view, account.edit, account.info, account.alerts
system.discover, system.deploy.ncpa, system.hosts, system.hosts.edit, system.hosts.alerts, system.logs
system.report, system.notifications, system.services, system.network_health
system.acknowledge_alerts, system.recheck, system.dashboard, system.history
maintenance.manage
plugin.scan, plugin.view, plugin.enable, plugin.disable
plugin.command_override, plugin.command_restore, plugin.validate
plugin.custom_add, plugin.custom_check, plugin.update, plugin.update_rollback
settings.security, settings.system, settings.discovery, settings.plugins, settings.email
remediation.view, remediation.manage
```

Some seeded permissions are not attached to a current route. That is tracked as
current-state inventory rather than treated as intended permission design.

## Operator CLI commands

`app/api/commands/seed.py` provides `flask recover-bootstrap-admin` for an
operator with local server access when the original bootstrap administrator has
lost its password. It privately prompts for a confirmed temporary password and
applies the current password policy. The command identifies the bootstrap
account as the uniquely earliest-created `User` (the production initializer
refuses an existing user); it never uses email, user ID, or `Needs_Setup` as
identity. Missing or tied earliest accounts fail without a database change.
Recovery changes only the password hash and `Must_Change_Password`, preserves
`Needs_Setup`, status, role, permissions and related records, and writes a
password-free activity event. An installer-owned convenience wrapper for
`sudo pinpoint recover-bootstrap-admin` is a separate follow-up; it does not
affect this backend command's contract. Existing browser sessions retain their
normal configured timeout; immediate invalidation is not part of this command.

## Response and request conventions

- API routes use `success(...)` and `error(...)` from
  `app/api/helper/responses.py`.
- Success envelope: `{ "success": true, "data": ... }`.
- Error envelope: `{ "success": false, "message": "..." }`.
- A required JSON body is read with `request.get_json()`.
- `request.get_json(silent=True) or {}` is reserved for genuinely optional
  bodies.
- Collection routes generally use `page` and `per_page` and return pagination
  metadata; the route docstring and tests own exact query validation.
- Every route returning user or system data must require login and, where a
  defined permission exists, that permission.

## User API

### `app/api/user/login.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `POST /api/user/login` | Public | Validate credentials and establish a session |
| `POST /api/user/logout` | Login | End the current session |

### `app/api/user/management.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/user/permissions/options` | `role.edit` | List permissions available for role editing |
| `POST /api/user/roles` | `role.edit` | Create an active role and assign permissions |
| `GET /api/user/roles` | `role.view` | Paginated role list |
| `GET /api/user/roles/options` | `role.list` | Compact active-role choices for forms. Each item includes `preserves_bootstrap_admin_access`, which is true when the role has all permissions required to manage accounts and roles (`account.view`, `account.edit`, `account.info`, `role.view`, `role.edit`, `role.info`, `role.list`) |
| `GET /api/user/roles/<id>` | `role.info` | Role detail and permission set |
| `PUT /api/user/roles/<id>` | `role.edit` | Replace role metadata and permissions. The built-in role named `Super Admin` cannot be renamed or have its permission set changed (adding, removing, replacing, or clearing); a reordered but otherwise identical set permits description edits. Rejections return 400 before metadata or grants change. The bootstrap administrator's assigned role also cannot be deactivated or lose any permission required to manage accounts and roles, even when it is a different role |
| `PUT /api/user/roles/<id>/status` | `role.edit` | Change role active status |
| `POST /api/user/accounts` | `account.edit` | Create a user account. Optional `require_password_change` (boolean, default true) sets `Must_Change_Password`; unticked, the user is not forced to change the admin-chosen password at first sign-in. Optional `receive_email_alerts` (boolean, default true); sending `false` needs `account.alerts` (403 otherwise). An Active account with alerts on is a Nagios contact, so the config is rebuilt through `regenerate_and_apply_config_status()`; the response carries `config_applied`, `config_ok`, `config_message` (a failed apply does not undo the account) |
| `GET /api/user/accounts` | `account.view` | Paginated account list. Each row carries `is_super_admin` for the first account (lowest `UserID`) so clients can preserve its protected status |
| `GET /api/user/accounts/<id>` | `account.info` | Account detail, including `receive_email_alerts` (the list rows carry it too) |
| `PUT /api/user/accounts/<id>` | `account.edit` | Edit account details/status; users are not deleted. The first account (lowest `UserID`, the bootstrap administrator) must remain Active and may be assigned only an active role that has every permission required to manage accounts and roles (`account.view`, `account.edit`, `account.info`, `role.view`, `role.edit`, `role.info`, `role.list`); either violation returns 400 before account data changes. Other fields remain editable. `password`/`confirm_password` are optional (omit to keep the password, so suspend/deactivate needs none). Setting a password on another account (always, regardless of the create-form option), or returning an account to Active from Suspended/Inactive, sets `Must_Change_Password`. Optional `receive_email_alerts` (boolean): changing it needs `account.alerts` (403 otherwise; resending the current value is allowed) and is written to the activity log. When the account's Nagios contact changes (status, alerts setting, email or name of an Active alert user), the config is rebuilt as on create and the response carries `config_applied`, `config_ok`, `config_message` |
| `GET /api/user/me` | Login | Return the current user, permissions, `must_change_password` and `needs_setup` |
| `POST /api/user/complete-setup` | Login (`Needs_Setup` only) | First-run setup for the bootstrap administrator: `current_password`, `new_email`, `new_password`, `confirm_password`. Checks the current password and the password policy; rejects an invalid or already-used email, the installer's `pinpoint.lan` placeholder domain, and reserved/non-routable domains (`.local`, `.lan`, `.test`, `.example`, `.invalid`, `.localhost`, `.internal`, `home.arpa`). No deliverability check. Saves both, clears `Needs_Setup` and `Must_Change_Password`, writes an audit-log entry, then regenerates the Nagios config through `regenerate_and_apply_config_status()` (Nagios contacts are named and addressed by `User.Email`). Returns `config_applied`, `config_ok`, `config_message`; a failed apply does not undo the account change. 400 for any other account. While `Needs_Setup` is set, every `/api` route except login, logout, `/me` and this one returns 403 (`enforce_password_change`), including `change-password` |
| `POST /api/user/change-password` | Login | Change the caller's own password (`current_password`, `new_password`, `confirm_password`); clears `Must_Change_Password`. While that flag is set every other `/api` route except login, logout and `/me` returns 403 (`enforce_password_change`). A user whose status is no longer Active is signed out on their next request |
| `POST /api/user/forgot-password` | Public | Login-page "Forgot Password?". Body `{email}`. Creates a Pending `PasswordResetRequest` for an Active account (at most one pending per user) and always returns the same generic success, so it cannot reveal which emails exist. No email is sent |
| `GET /api/user/password-requests` | `account.edit` | Pending forgot-password requests, oldest first (`items`, `count`); drives the admin bell alert and the Manage Accounts panel |
| `POST /api/user/password-requests/<id>/resolve` | `account.edit` | Admin sets the new password (`password`, `confirm_password`, same policy as other password routes). Marks the request Completed and sets `Must_Change_Password`; 409 if already handled |
| `POST /api/user/password-requests/<id>/dismiss` | `account.edit` | Admin declines a pending request; 409 if already handled |

### `app/api/user/preferences.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/user/preferences` | Login | Read the caller's display preferences |
| `PUT /api/user/preferences` | Login | Save the caller's display preferences |

## System API

### `app/api/system/settings.py`

The `system_bp` root makes these paths `/api/system`.

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system` | Login | Return singleton system settings |
| `PUT /api/system` | Login, field-level settings permissions | Save the full settings object with optimistic version handling; `checkInterval` accepts 1/2/5/10/15 minutes, `retryInterval` 1 to 10 minutes (never longer than the check interval in effect after the save) and `maxCheckAttempts` 1 to 10, all with `settings.system` (400 for a bad value; the two retry fields are optional in the body and keep their saved value when omitted); `flapDetectionEnabled` (bool), `flapLowThreshold` and `flapHighThreshold` (0 to 100 percent or `null` for Nagios's own value, low below high, 400 otherwise) are optional in the body too and need `settings.system`; any change to one of these regenerates the Nagios config through the shared writer and rolls back on apply failure (422 with message) |

Security and system setting fields are restricted with `settings.security` and
`settings.system`; personal fields are handled by `/api/user/preferences`.

### `app/api/system/notification_policy.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/notification-policy` | `settings.system` | Read the singleton policy; quiet-hour windows use the Nagios server's local time |
| `PUT /api/system/notification-policy` | `settings.system` | Validate quiet-hour windows, host/service options, and renotify interval (0–1440 minutes); 400 on invalid fields, 409 on stale version, 422 with Nagios feedback on failed config apply, rolling back the database; audit changed fields when enabled |

Both routes use the standard success/error envelopes. GET returns `quietHours` (weekday, `start`, `end` in 24-hour `HH:MM`), `hostOptions`, `serviceOptions`, `renotifyInterval`, `version` and `timeZone` (`Nagios server local time`). PUT accepts those editable fields plus the current integer `version`; `timeZone` is informational. Quiet windows cannot cross midnight or overlap on one weekday. The policy belongs to the default-bind singleton, and a successful save regenerates/validates/applies the shared Nagios candidate file before committing.

Notification dependency generation is an application setting in `server/config.py`,
`PINPOINT_NCPA_NOTIFICATION_DEPENDENCIES` (default on), rather than an editable
notification-policy field. It adds a per-device NCPA TCP port check and
notification-only service dependencies for existing NCPA metrics. Setting it
off leaves the previous generated service set; a restart and the next shared
Nagios config regeneration apply the new value. No new HTTP route or permission
is introduced.

### `app/api/system/maintenance.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/maintenance/windows` | `maintenance.manage` | List windows (newest first, at most 200) with `nextOccurrence`, the five most recent occurrences (status, attempts, `error`) and `devices`, the monitored devices a window can be scoped to |
| `POST /api/system/maintenance/windows` | `maintenance.manage` | Create a window (201). 400 when invalid: `startAt`/`endAt` need a UTC offset, end after start and in the future, `recurrence` none/daily/weekly, one-off at most 30 days, a recurring window no longer than its period, `recurrenceUntil` only for a recurring window and at most 366 days after the start, `timeZone` a known IANA name, `comment` 1–200 characters with no line break, `deviceId` null (all devices) or an existing device that is monitored. Audited |
| `PUT /api/system/maintenance/windows/<id>` | `maintenance.manage` | Replace an active window with the same validation (400; 404 unknown; 400 when not active). Downtime already handed to Nagios for its unfinished occurrences is deleted first; the response adds `nagios_synced` / `nagios_message`. Audited |
| `POST /api/system/maintenance/windows/<id>/cancel` | `maintenance.manage` | Cancel a window and delete its pending and running Nagios downtime (`nagios_synced` / `nagios_message` as above; the window is cancelled even when Nagios could not be told). 400 when already cancelled, 404 unknown. Audited |

A window is Nagios scheduled downtime, not PinPoint's own Maintenance Mode (a `SystemSettings` flag that only pauses PinPoint's background jobs and is unchanged). Times are ISO 8601 in and out, stored as UTC; `timeZone` is only the zone a daily or weekly window repeats in, so it keeps its local time across a daylight-saving change. Nothing is sent to Nagios by these routes except the delete on edit and cancel; the scheduler job `maintenance_windows` (`app/maintenance.py`) schedules downtime shortly before each occurrence.
### `app/api/system/forecast.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/forecast` | `system.dashboard` or `system.services` (either) | The stored resource forecasts, soonest estimated crossing first. Query: `hostname` (optional), `limit` (1-500, default 100; 400 otherwise). Returns `forecasts` (`hostname`, `service_name`, `metric`, `kind` `warning`/`critical`, `threshold`, `crossing_at`, `slope_per_hour`, `r_squared`, `sample_count`, `window_hours`, `current_value`, `unit`, `computed_at`; timestamps ISO 8601 with a UTC offset) and `insufficient` (`hostname`, `service_name`, `metric`, `sample_count`, `window_hours`: series not yet watched long enough) |

A forecast is a display-only estimate (`app/forecast.py`); the route reads `RESOURCE_FORECAST` only and nothing here changes a Nagios state or config. No permission was added. Notifications for forecasts are not part of this route.

### `app/api/system/escalations.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/escalations` | `settings.system` | List saved ranges (`items`), existing recipient `groups` with `name`/`member_count`, and monitored device `hosts` with `id`/`name`; each range includes `active` and an inactivity `reason` |
| `POST /api/system/escalations` | `settings.system` | Create and apply a notification escalation; 400 invalid fields/empty group, 422 failed Nagios validation or reload with database rollback |
| `PUT /api/system/escalations/<id>` | `settings.system` | Replace and apply an escalation; same validation/rollback; 404 missing range |
| `DELETE /api/system/escalations/<id>` | `settings.system` | Delete and apply an escalation; 404 missing range, 422 failed apply restores the saved range |

POST/PUT require exactly `first_notification`, `last_notification`,
`interval_minutes`, `contact_group`, `host_id`. Notification counts are integers
from 1 to 10000, first no greater than last; interval is an integer from 0 to
1440 minutes (0 sends once during the range). `contact_group` must be an existing
nonempty group from the shared recipient calculation. `host_id` is a currently
generated device ID, or `null` for all Nagios hosts and services. Responses use
the standard envelope. Mutations hold the shared config lock through validation,
apply and commit, log configuration changes when audit logging is enabled, and
restore the previous database choices on failure. Existing ranges with empty
groups or absent scoped hosts remain visible with an explanation and are omitted
from generated configuration. No new permission is introduced.

### `app/api/system/remediation.py`

Allowlisted actions that run when a covered service or host reaches a HARD failure, and the log of what the consumer decided (`app/remediation.py`).

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/remediation/action-types` | `remediation.view` | The action types an admin can pick, each with `key`, `label`, `description` and its parameter schema |
| `GET /api/system/remediation/targets` | `remediation.view` | Suggestions for the action form: `items` of `hostname` (the Nagios host name of every device that is not merged, plus any host with a service snapshot) and `services` (the service names snapshotted on it in the last 7 days, sorted). Suggestions only; the patterns an action saves are still validated by create and update |
| `GET /api/system/remediation/actions` | `remediation.view` | All actions, ordered by name |
| `POST /api/system/remediation/actions` | `remediation.manage` | Create an action (`notifyOn`: which of `failed`, `capped` and `repeated` notify the operator through Nagios, default all three, may be empty, stored in a fixed order without duplicates, #153); 400 with `data.fields` (field name to message) on invalid input, 422 with Nagios feedback when the regenerated config is rejected (nothing is saved), 201 on success |
| `PUT /api/system/remediation/actions/<id>` | `remediation.manage` | Replace an action; needs the current integer `version`; 400 with `data.fields`, 404, 409 on a stale version, 422 as for create |
| `DELETE /api/system/remediation/actions/<id>` | `remediation.manage` | Delete an action; its runs stay in the log; 404, 422 as for create |
| `GET /api/system/remediation/runs` | `remediation.view` | The run log, newest first: `page`, `per_page` (1 to 100, default 25), filters `action` (action id), `host` (exact name), `outcome`, `from` and `to` (`YYYY-MM-DD`, inclusive); 400 on a bad value; returns `items`, `page`, `per_page`, `pages`, `total` |
| `GET /api/system/remediation/runs/<id>` | `remediation.view` | One run including its redacted `output`; 404 when missing. Every run item also carries `notifyKind` (`failed`, `capped`, `repeated` or null), `notifyState` (`pending`, `sent`, `failed` or null when no notification was due), `notifyAttempts`, `notifyError` (a fixed sentence) and `notifyAt` (#153) |
| `GET /api/system/remediation/last-runs` | `remediation.view` | The newest run for each host and service in the last 7 days (at most 500, newest first), for the badge on a service row: `items` of `runId`, `hostname`, `service` (null for a host), `outcome`, `notifyState`, `receivedAt`; never the output (#153) |
| `GET /api/system/remediation/settings` | `remediation.view` | `{enabled, retentionDays, repeatCount, repeatWindowHours}`: the kill switch (default on), how many days runs are kept (default 90), and the repeat-recovery limits (default 3 successful recoveries of one service in 24 hours send one "repeated" notification, #153) |
| `PUT /api/system/remediation/settings` | `remediation.manage` | Send any of `enabled` (true or false), `retentionDays` (a whole number from 7 to 3650), `repeatCount` (2 to 20) and `repeatWindowHours` (1 to 168); unknown fields and bad values are a 400 with `data.fields` and nothing is saved; each changed value is written to the configuration log as type `remediation_setting` when audit logging is on. These settings are not part of `/api/system` and do not change its `version` |
| `GET /api/system/remediation/health` | `remediation.view` | Whether the consumer is working: `lastTickAt`, `lastError` (a fixed sentence, never a path), `stalled` (no heartbeat for three poll intervals, 45 seconds, or never), `backlog` and `oldestSpoolAgeSeconds` (event files waiting), `runsLast24h` (actions started), `capsHitLast24h`, `skippedLast24h`, `droppedTotal` and `droppedAt` (events discarded because the spool held too many). One state row, one folder listing and three counts; no history scan |

An action body has `name` (3 to 60 letters, numbers, spaces, `.`, `_`, `-`; unique), `actionType` (a key from `action-types`), `scopeKind` (`service` or `host`), `hostPattern` (letters, numbers, `.`, `_`, `-`, `*`), `servicePattern` (required for a service action, null for a host action; also allows spaces, `:` and `/`), `parameters` (validated by the action type; `record_only` takes none and rejects any key; `restart_local_service` takes exactly `unit`, one of the fixed list in `RESTARTABLE_UNITS`, currently `nagios`, and anything else is a 400 on `parameters.unit`), `enabled` (boolean, default false), `maxRunsPerHour` (1 to 60, default 2) and `cooldownSeconds` (60 to 86400, default 600) and `runWhenAcknowledged` (boolean, default false: when false the action is skipped for a problem an operator has already acknowledged). Patterns match an exact name or use `*` for any run of characters; there is no regex. Unknown fields are errors. Every change regenerates, validates and applies the Nagios config through the shared writer before committing, and is written to the configuration log when audit logging is on. Run list items hold `id`, `actionId`, `actionName`, `hostname`, `service`, `state`, `stateType`, `attempt`, `receivedAt`, `startedAt`, `finishedAt`, `outcome` and `reason`; outcomes are `running`, `succeeded`, `failed`, `timed_out`, `skipped_cooldown`, `skipped_hourly_cap`, `interrupted`, `skipped_kill_switch`, `skipped_maintenance`, `skipped_downtime` and `skipped_acknowledged`. Nothing in a response carries credentials or internal paths.

### `app/api/system/dashboard.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/dashboard/status` | `system.dashboard` | Nagios process, monitoring-server resources and appliance storage_usage (per-database, backups, archives, free/total bytes per filesystem) |
| `GET /api/system/dashboard/summary` | `system.dashboard` | Host/service counts, active-alert counts, ping and NCPA summaries |
| `GET /api/system/dashboard/alerts` | `system.dashboard` | Active alerts from the latest snapshot, with acknowledgement filters |
| `POST /api/system/dashboard/alerts/acknowledge` | `system.acknowledge_alerts` | Acknowledge one host or service alert; also sent to Nagios (`nagios_synced`, `nagios_message` in the response). A comment with a line break or NUL returns 400 |
| `POST /api/system/dashboard/alerts/acknowledge-all` | `system.acknowledge_alerts` | Acknowledge a supplied batch of alerts; `nagios_synced` is false if any command failed |
| `DELETE /api/system/dashboard/alerts/acknowledge` | `system.acknowledge_alerts` | Remove one application acknowledgement and the Nagios one (`nagios_synced`) |
| `GET /api/system/dashboard/notifications` | `system.dashboard` | Return the five latest Nagios notifications |

Detailed fields and behavior are normative in `Display_Requirements.md`.

### `app/api/system/network_health.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/network-health/summary` | `system.network_health` | Network Health header totals and last-scan information |
| `GET /api/system/network-health/trends` | `system.network_health` | Bucketed ping and NCPA metric trends |
| `GET /api/system/network-health/plugins` | `system.network_health` | Service health grouped by plugin type |

Valid trend windows are `hours=1`, `6`, `24`, or `168`.

### `app/api/system/network_health_activity.py`

All routes require login and `system.network_health`. Response shapes are in
each route's docstring.

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/network-health/availability` | `system.network_health` | Network-wide host availability per day for the last `days` (1 to 30, default 7), from Nagios `archivejson.cgi` |
| `GET /api/system/network-health/system-activity` | `system.network_health` | Process and logged-in user counts from the latest `check_procs` and `check_users` results; a section is `null` when no device runs that check |
| `GET /api/system/network-health/cpu` | `system.network_health` | CPU utilization trend for one host with an NCPA CPU check (`hostname` optional) |
| `GET /api/system/network-health/connections` | `system.network_health` | TCP connection counts by state on the Nagios/Pinpoint server, read from `/proc/net/tcp`; `available` is false without `/proc` |
| `GET /api/system/network-health/insights` | `system.network_health` | Plain-language observations from the latest snapshot, most severe first |
| `GET /api/system/network-health/flapping` | `system.network_health` | Hosts and services flagged as flapping in the last `hours` (1, 6, 24 default or 168; 400 otherwise): per item the number of flagged snapshots, first and last flagged time, whether it is flapping now and its current state, plus `global_flap_detection_enabled` (`null` until Nagios has reported). Counted from 60-second snapshots, so fast flaps can be missed; paused and retired devices are left out |
| `GET /api/system/network-health/plugin-trends` | `system.network_health` | One entry per plugin enabled in Plugin Manager: state counts, current values and averaged trends for time and percentage metrics |
| `GET /api/system/network-health/bandwidth/interfaces` | `system.network_health` | The devices the bandwidth card can chart: every device with SNMP monitored, each with its monitored interfaces (`if_index`, `name`, `speed_bps`) plus the default interface 3 when the device has the default `lan_in_octets` service |
| `GET /api/system/network-health/bandwidth` | `system.network_health` | In and out bandwidth (bit/s) of one interface: `hostname` and `interface` (ifIndex) required, `hours` 1, 6, 24 (default) or 168 (anything else, including the 5-minute window or an unreadable value, is 400), `buckets` 1 to 168 (default 48). Rates are computed by `app/bandwidth.py` from the stored octet counters of the interface's `snmp-if<N>_in_octets-<port>-udp` and `..._out_octets...` services (interface 3 falls back to the default `snmp-lan_in_octets-...` / `lan_out_octets` services). Returns `status` (`ok`, or `insufficient_data` when neither direction has two valid samples), `in_points` / `out_points` (`bucket_start`, `bps` or `null` for a gap), the `interface` (`if_index`, `name`, `speed_bps`) and `latest` (`in_bps`, `out_bps`, and `*_utilisation_pct` only when the link speed is known). 404 when the host has no bandwidth service for that interface |

### `app/api/system/network_hosts.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/network-health/hosts` | `system.network_health` | Paginated/filterable latest host snapshot; each item carries `device_id` (the discovered device behind the Nagios host name, `null` for a host with no device record such as `localhost`) and `ip_address` (that device's current IP, `null` in the same case), and `monitoring_state` / `monitored` (the device's monitoring label and whether Nagios fully checks it; both `null` in the same case). Optional `flapping=true` lists only flapping hosts (`false`, `all` or empty lists everything, 400 otherwise). Optional `monitoring` filter: `all`, `not_monitored`, `monitored`, `missing`, `address_unknown`, `paused`, `retired` or `merged` (400 otherwise); a host with no device counts as monitored |
| `GET /api/system/network-health/hosts/<hostname>/detail` | `system.network_health` | Host detail panel data, including `device_id`, `monitoring_state` and `monitored` |
| `POST /api/system/network-health/hosts/<hostname>/recheck` | `system.recheck` | Check Now: force a Nagios host check. 429 inside the 10 s per-target limit (`data.retry_after`), 404 not in the latest snapshot, 409 paused/retired/merged, 503 command pipe unavailable. Audited |
| `POST /api/system/network-health/hosts/acknowledge` | `system.acknowledge_alerts` | Acknowledge a host alert. Response data adds `nagios_synced` and `nagios_message` |
| `DELETE /api/system/network-health/hosts/acknowledge` | `system.acknowledge_alerts` | Unacknowledge a host alert |

### `app/api/system/network_services.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/network-health/services` | `system.network_health` | Paginated/filterable latest service snapshot; optional `flapping=true` lists only flapping services (`false`, `all` or empty lists everything, 400 otherwise) |
| `GET /api/system/network-health/services/<hostname>/<path:service_name>/detail` | `system.network_health` | Service detail panel data |
| `POST /api/system/network-health/services/<hostname>/<path:service_name>/recheck` | `system.recheck` | Check Now for a service; same responses as the host route |
| `POST /api/system/network-health/services/acknowledge` | `system.acknowledge_alerts` | Acknowledge a service alert. Response data adds `nagios_synced` and `nagios_message` |
| `DELETE /api/system/network-health/services/acknowledge` | `system.acknowledge_alerts` | Unacknowledge a service alert |

### `app/api/system/history.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/history/alerts` | `system.history` | Paginated Nagios state-change events |
| `GET /api/system/history/alerts/detail` | `system.history` | Full detail for one alert event |
| `GET /api/system/history/notifications` | `system.history` | Paginated notification events from Nagios and Pinpoint; every item has `source` (`nagios` or `pinpoint`), filterable with `source=`. Pinpoint items are finished network scans (`type: scan`, state SUCCESS/FAILED/CANCELLED) read from `NETWORK_DISCOVERY_STATUS`; host/service/contact/type filters exclude them |
| `GET /api/system/history/notifications/detail` | `system.history` | Full detail for one notification event; Pinpoint events use `source=pinpoint&id=<DiscoveryStatusID>` |

Alert list and detail annotate prior state and time in that state from preceding
archive transitions for the same target; recovery detail computes the full
problem episode duration from first problem detection. List annotations include
transitions before the selected window. Without an earlier archive transition,
Nagios-provided metadata is retained rather than inventing an onset.

Both list routes support `preset=1h|6h|24h|7d|30d` (default 24h), or paired
`start_date`/`end_date` as whole server-local `YYYY-MM-DD` days or inclusive
ISO 8601 seconds with explicit timezone (`Z` or `±HH:MM`). Invalid or partial
bounds return 400; a preset takes precedence. `sort_by` accepts every list
column: alerts `timestamp|type|hostname|service_name|previous_state|new_state|state_type|duration_seconds|plugin_output|acknowledged`
(with legacy `duration` alias); notifications `timestamp|type|hostname|service_name|state|contact|method|message`.
`order=asc|desc` selects the primary direction; ties sort by timestamp desc.
Unknown sort keys continue to default to timestamp. List output/message sort
uses the truncated value. Nagios list and detail rows expose `event_id` (UNIX
second plus digest of normalized archive fields); linked notifications/alerts in
detail responses carry the target `event_id`. Both list routes accept `event_id`
for a single-second exact lookup, overriding time range and filters; malformed
IDs return 400, missing IDs yield an empty page. Detail routes also accept
`event_id` to distinguish same-second rows (alongside legacy host/service/time
parameters). Pinpoint scan records retain
`id` instead. Links match host, service and state to the most recent preceding
alert within five minutes. See `Alerts_Notifications_History_Requirements.md`
§§3.3–3.4, 4.3–4.4 and 5.4.

The route implementation exists, but `system.history` is not currently present
in the seed permission list. This is tracked in `Implementation_Status.md`.

### `app/api/system/notifications.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/notifications` | `system.notifications` | Recent notifications from Nagios (`source: nagios`) and Pinpoint itself (`source: pinpoint`, network scan results) annotated with per-user read state. Nagios field names are normalized (`normalize_notification`) and repeats of the same host/service in the same state are collapsed into one entry with `repeat_count` and `first_timestamp` (`collapse_repeats`); the history routes are not collapsed |
| `GET /api/system/notifications/unread-count` | `system.notifications` | Count collapsed entries after the user's cursor (matches the panel list) |
| `POST /api/system/notifications/mark-read` | `system.notifications` | Advance the user's notification cursor |

### `app/api/system/network_discovery.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `POST /api/system/discover/start` | `system.discover` | Start a background discovery/config-generation job |
| `GET /api/system/discover/status` | `system.discover` | Current or most recent discovery job status |
| `POST /api/system/network-discovery/stop` | `network.discovery` in current code | Request cancellation of the running discovery job |

The stop-route permission differs from the seeded `system.discover` permission;
this is a documented implementation mismatch, not a recommended convention.

### `app/api/system/discovery_settings.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/discovery-settings` | `settings.discovery` | Effective discovery settings, their `config.py` defaults, and whether a scan is running |
| `PUT /api/system/discovery-settings` | `settings.discovery` | Save networks, TCP/UDP ports and the Port -> Service tables (`tcpPortServices`, `udpPortServices`: the service expected on each port); every field is required, the version must match. GET also returns `ncpaPort`, the derived NCPA entry in the TCP table (accepted back but never stored; mapping that port to anything but `ncpa` is a 400) and `resolution` (which check each entry leads to) |

### `app/api/system/smtp_settings.py`

Settings -> Email: the shared account notification mail is sent through. Gmail
keeps its fixed preset; Other SMTP relay accepts custom STARTTLS settings. Logic
is in `app/smtp_settings.py`; notification failures come from
`app/nagios/mail_failures.py`.

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/smtp-settings` | `settings.email` | `settings` (`provider`, `host`, `port`, `tls`, `username`, `sender`, `passwordSet`, `configured`, `version`, `updatedAt`) and `presets.gmail` / `presets.custom`, plus `lastMailFailure` (`null` or `{time, reason}`). Time is ISO 8601 UTC; reason is fixed sanitized text. Reads at most 64 KiB from the current `NAGIOS_LOG_FILE` on every GET; missing, unreadable and nonregular logs give `null`. The password is never returned, only whether one is saved |
| `PUT /api/system/smtp-settings` | `settings.email` | Save `{version, provider, host, port, tls, username, sender?, password?}`. Gmail keeps `smtp.gmail.com`, 587 and `starttls`, an email username and its existing validation messages. `custom` accepts the installed helper host rules (1–253 ASCII letters, digits, dots or hyphens, starting and ending with a letter or digit), integer port 1–65535 and only `starttls`; `tls`/`none`/`ssl` are 400. Custom usernames contain 1–254 printable ASCII characters; sender is a valid email matching the helper regex and defaults to username only when that is an email. `password` is printable ASCII, at most 200 characters for Gmail or 256 for custom, used exactly as sent (never trimmed or stripped of spaces) and may be left out or empty once one is saved. The settings go to the root helper (`sudo -n /usr/local/sbin/pinpoint-apply-smtp`, one JSON object on stdin) and are saved only if it exits 0; its credential-redacted stderr is returned as the message (400 when it rejected the input, 500 when it is missing or timed out). 409 on a stale version. Writes Configuration Change entries (`smtp_settings`, the password logged only as `changed`) when audit logging is on |
| `POST /api/system/smtp-settings/test` | `settings.email` | Send a test message to the signed-in user's address over STARTTLS with the saved settings (400 when none are saved). Always 200 with `{ok, recipient}` or `{ok: false, code, message, explanation, details}`; `code` is `auth_failed` (535, `BadCredentials`, "Username and Password not accepted": friendly Gmail app-password message), `connect_failed` (blocked port 587), `host_not_found`, `tls_failed`, `rejected` or `send_failed`; `message` is plain language, `explanation` says technically what happened and what to check, and `details` is credential-redacted Gmail server text, or empty for custom relays (fixed generic messages without Gmail-specific advice) |

### `app/api/system/plugin_settings.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/plugin-settings` | `settings.plugins` | Each editable plugin's section keyed by definition name (`snmp`, `ncpa`): `plugin` (`check_snmp`, `check_ncpa`), `installed` (it has a Plugin Manager row), `status`, `settings` (effective values), `defaults` (`config.py`) and `version` (0 until first saved) |
| `PUT /api/system/plugin-settings/<plugin>` | `settings.plugins` | Save one plugin's table; `<plugin>` is `snmp` or `ncpa` (404 otherwise). SNMP: `{"version", "oids": [{"metric", "oid"}]}`, `oid` numeric and dotted, unique. NCPA: `{"version", "metrics": [{"metric", "path", "warning"?, "critical"?, "units"?, "queryargs"?}]}`; `path` is an NCPA API path (segments of letters, digits, `_ - . |`, or `{partition}`, which expands to one service per partition), thresholds use Nagios range syntax, units up to 8 letters or `%`, query args `name=value` pairs joined by `,`; empty options are dropped. For both, `metric` is the description (lowercase letters, digits, `_`, at most 32, unique) and names the service `<plugin>-<metric>-<port>-<protocol>`; 1 to 50 entries. 400 when the plugin is not installed or an entry is invalid, 409 on a stale version. Writes a Configuration Change entry (`<plugin>_<variable>`, when audit logging is on), then rebuilds the Nagios config; returns the section plus `config_applied`, `config_ok`, `config_message` |

### `app/api/system/device_identity.py`

Device summaries include `parent_device_ids` and `parents` with ID, stable host name,
display name, address, monitoring state, `nagios_eligible` and `omission_reason`.
Parents can be paused or address-unknown at read time; stored choices remain visible
while those references are omitted from Nagios. Merge re-points both relationship ends,
deduplicates and rejects self-links/cycles; retirement clears both ends. Relationship
changes on merge/retire apply before commit and roll back if rejected.


| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/hosts/lookup` | `system.hosts` | Discovered-device picker, independent of Nagios snapshots and monitoring filters. Optional literal case-insensitive `search` (max 100 characters) matches display name, Nagios name, DNS name, IP or exact numeric ID. Returns up to 20 device summaries ordered by ID with `has_more`; merged records excluded, retired sources included |
| `GET /api/system/topology` | `system.network_health` | All discovered devices plus latest Inventory hosts without device records, existing device details, latest stored host state/check time, monitoring state, parent IDs, editable lifecycle flag; configured edges include parent/child IDs and Nagios eligibility/omission reason. Advisory suggested gateway ID; no automatic inference or layout coordinates. Reads never probe target devices |
| `GET /api/system/hosts/<id>/addresses` | `system.hosts` | Address history of a device |
| `GET /api/system/hosts/<id>/identifiers` | `system.hosts` | Identity evidence and confidence |
| `PUT /api/system/hosts/<id>` | `system.hosts.edit` | Change display name, addressing mode and/or `parent_device_ids` (distinct positive integer list). Omitted parents preserve choices; empty clears. 400 for invalid/terminal/self/cyclic parents. Parent changes flush, validate/apply through the shared Nagios writer, then commit; failed apply returns 422 and rolls back the complete edit |
| `POST /api/system/hosts/<id>/merge` | `system.hosts.edit` | Merge the device into another |
| `POST /api/system/hosts/<id>/retire` | `system.hosts.edit` | Retire the device |
| `POST /api/system/hosts/<id>/pause` | `system.hosts.edit` | Pause monitoring: clears `Include_Device_In_Scanning`, so the device leaves the Nagios config while scans still track it. 400 if the device is retired, merged or already paused. Returns `config_applied`, `config_ok`, `config_message` and the `device` summary (which now carries `monitoring_state` and `monitored`) |
| `POST /api/system/hosts/<id>/resume` | `system.hosts.edit` | Resume monitoring of a paused device (400 if it is not paused); same response as pause |
| `GET /api/system/hosts/<id>/ports` | `system.hosts` | Every port of a device, ordered by state (Monitored, Missing, Suggested, Ignored, Archived), protocol and number. Per port: `state`, `source`, `service_name`, `observed_service_name`, `identified_by`, `pinned`, `plugin_name` (frozen), `check_plugin` and `plugin_enabled`, `expected_service_name`, `mismatch_acknowledged`, `promotion_held`, `managed_by_ncpa` (the NCPA port of a deployed agent), first/last seen, `missed_scans`, and `reason` (`code` and `text`: for Suggested and Ignored ports `not_used_as_intended`, `held`, `guessed`, `no_udp_plugin`, `plugin_not_enabled`, `device_excluded`, `pending` or `stopped`, first match wins; `missing` for a Missing port; `monitoring_inactive` for a Monitored port whose check plugin is off; `service_missing` for a Monitored port whose plugin is on but has no Applied service (a configuration problem); null otherwise). Also `device`, `counts` per state and `service_options` (known service names and aliases with the check plugin and protocols they lead to, for the pin dialog) |
| `PUT /api/system/hosts/<id>/ports/<proto>/<port>` | `system.hosts.edit` | Body `{"state"?, "service_name"?, "acknowledge_mismatch"?, "unpin"?}`: change a port's state, pin its service on this device (never renamed by a scan; a monitored port's plugin is re-frozen), acknowledge a port flagged "not used as intended" (accepts the service nmap found; 400 if the port is not flagged), `unpin: true` lets scans decide the service again (a Suggested, Ignored or Archived port returns to the service the last scan saw; a Monitored or Missing port keeps its service and its Nagios service; refused with 400 for a port that is not pinned or for the NCPA port of a deployed agent; never changes state or hold), or add a port by hand (`state` MONITORED plus `service_name`); response includes `identified_by`, `expected_service_name`, `mismatch_acknowledged`, `promotion_held` and `pinned`, plus `config_applied` (a new config went live), `config_ok` (false only when the change was saved but Nagios was not brought up to date) and `config_message`. Setting `state` to SUGGESTED holds the port (no plugin promotes it); MONITORED releases it |
| `GET /api/system/discover/review` | `system.discover` | Unresolved review items, including `SERVICE_CHANGED` |
| `POST /api/system/discover/review/<id>/resolve` | `system.hosts.edit` | Mark a review item as dealt with |

### `app/api/system/device_interfaces.py`

The interfaces an SNMP device reports and which of them are monitored for bandwidth
(Device Inventory drawer). Choosing an interface changes the generated Nagios config, so a
change is saved, written to the activity log and applied through `apply_config_change()` (the
shared writer: validated with the Nagios binary, rolled back if rejected).

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/hosts/<id>/interfaces` | `system.hosts` | The stored interface list: `device`, `snmp` (SNMP is monitored on the device), `max_monitored` (16) and `interfaces` (`if_index`, `name`, `speed_bps`, `admin_status`, `oper_status`, `monitored`, `present`, `last_seen_at`) |
| `POST /api/system/hosts/<id>/interfaces/refresh` | `system.hosts.edit` | Read the list from the device over SNMP (`snmpwalk`, 20 s limit) and store it: new interfaces are added unmonitored, known ones updated with the monitoring choice kept, vanished ones removed unless monitored (kept with `present` false). 400 when SNMP is not monitored on the device, 502 with a plain-language reason when the device cannot be read; the community is never in the message. Same body as the list route |
| `PUT /api/system/hosts/<id>/interfaces/<if_index>` | `system.hosts.edit` | Body `{"monitored": true/false}` (400 for anything else): start or stop monitoring one interface. 404 for an interface not in the list, 400 when SNMP is not monitored, the device no longer reports the interface, or 16 are already monitored. Response is the list body plus `config_applied`, `config_ok` (false only when the change was saved but Nagios was not brought up to date) and `config_message` |

### `app/api/system/device_plugin_variables.py`

Per-device overrides of a registry plugin's variables, stored in
`NetworkDiscovery.Plugin_Variables[<plugin>]` (the Device Inventory SNMP form uses it for the SNMP
version and v3 credentials, and the Ports section's Check options form for the expected text,
status codes, virtual host and method of `http` / `https` and the greeting of `pop3`, `imap`,
`pop3s` and `imaps`; see "Mail and web service checks" in `Data_Model_and_Integrations.md`). A change is validated, written to the activity log (variable names,
never values) and applied through `regenerate_and_apply_config_status()` under `config_write_lock`;
if Nagios rejects it the change is rolled back and the response is 422. Validation reuses the
registry (`validate_variable_value`, `validate_snmp_v3`, `editable_variables`), so it cannot drift
from what the generator renders. Secret variables (SNMP v3 `auth_password`, `priv_password`) are
encrypted with `secrets_store` as `<name>_enc` and never returned.

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/hosts/<id>/plugin-variables/<plugin>` | `system.hosts` | `plugin`, `variables` (plain values), `secrets_set` (`{name: bool}`), `editable` and `in_use` (snmp only: the device has an SNMP port monitored; `null` for other plugins). 404 for an unknown device or a plugin that is not a registry definition |
| `PUT /api/system/hosts/<id>/plugin-variables/<plugin>` | `system.hosts.edit` | Body `{"variables": {...}, "clear_secrets": [...]}`; an empty body resets. The plain variables replace the stored ones; a secret that is not sent keeps its value, `clear_secrets` removes one. Unknown keys, invalid values and a v3 field the security level needs are 400 with `data.field` naming the variable; a retired or merged device is 400; a body over 8 KiB is 400; 422 when Nagios rejects the config (change rolled back). SNMP: `protocol` is 1, 2c or 3; v3 needs `security_level`, `v3_user` and, per level, `auth_protocol`/`auth_password` and `priv_protocol`/`priv_password` (passwords 8 to 64 printable characters); fields a level does not use, and every v3 field of a v1/v2c device, are dropped with their stored passwords |
| `DELETE /api/system/hosts/<id>/plugin-variables/<plugin>` | `system.hosts.edit` | Reset the override: the device returns to the defaults. Same 404, 400 and 422 rules |
| `POST /api/system/hosts/<id>/plugin-variables/<plugin>/test` | `system.hosts.edit` | SNMP only (400 otherwise). Query the device once with `check_snmp` (uptime OID) using the settings in the body (or the saved ones when empty; a blank password uses the stored one). Saves and applies nothing. 200 with `ok`, `state` and `message`; an unreachable device is a failed result. v3 passphrases go to `check_snmp` on stdin as extra-options and are scrubbed from the message |

### `app/api/system/ncpa_deployment.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/deployment/ncpa/devices` | `system.deploy.ncpa` | NCPA-eligible devices (and devices with a deployment record) with IP, trust state, saved fingerprint, agent status, last error, last outcome, last run and `deployable` |
| `GET /api/system/deployment/ncpa/<device_id>/fingerprint` | `system.deploy.ncpa` | Fetch live SSH host-key fingerprint from the device's SSH port (`data.ssh_port`); 502 when the device does not answer |
| `POST /api/system/deployment/ncpa/<device_id>/confirm-trust` | `system.deploy.ncpa` | Body `{"fingerprint"}`: save the key only if the live key on the device's SSH port still equals the one the user approved, pinning that port in `SSH_Port`; 409 with `data.fingerprint` when it changed, 502 when unreachable |
| `POST /api/system/deployment/ncpa/check-credentials` | `system.deploy.ncpa` | Test each device's login and sudo on its pinned SSH port without deploying; per-device result `ok`, `auth_failed`, `no_sudo`, `unreachable`, `host_key_changed`, `not_trusted`, `not_found` or `rate_limited` (one check per device per 3 s) |
| `POST /api/system/deployment/ncpa/<device_id>/refresh-disks` | `system.deploy.ncpa` | Re-read the agent's logical disks, store them, regenerate the Nagios config |
| `GET /api/system/deployment/ncpa/<device_id>/remote-restart`, `PUT /api/system/deployment/ncpa/<device_id>/remote-restart` | `system.deploy.ncpa` | Read or set a device's remote restart switch and service list. PUT body `{"enabled": bool, "services": [unit, ...]}`; units are plain names (letters, digits, `_ . @ -`, at most 63 characters, at most 20 per device); 400 for anything else, 409 for an untrusted device or turning it on with an empty list. `redeploy_needed` is true when the list changed, because the device's own copy is written only by a (re)deployment |
| `POST /api/system/deployment/ncpa/<device_id>/cleanup` | `system.deploy.ncpa` | Body `{"username", "password", "remove_account"?}`: a failed or deployed device with a confirmed SSH fingerprint and no running deployment; recheck SSH key before SSH and remove Pinpoint bootstrap key/rule/helper, optionally account. Response lists each step with `ok`/optional `skipped`, and `agent_status`; cleanup clears `Key_Installed` to block remote actions until redeployment; complete cleanup returns Pending NCPA, incomplete cleanup stays Deployment Failed with a safe error. An activity entry records the outcome; request credentials are cleared. Errors never contain credentials. |
| `POST /api/system/deployment/ncpa/start` | `system.deploy.ncpa` | Validate credentials and devices, create the run with a Rejected or Pending result per device, and start the worker; 400 with `data.rejected` when no device can be deployed |
| `POST /api/system/deployment/ncpa/stop` | `system.deploy.ncpa` | Request deployment cancellation; devices not started become Skipped |
| `GET /api/system/deployment/ncpa/status` | `system.deploy.ncpa` | Latest run with per-device results, outcome counts, starter and review state |
| `GET /api/system/deployment/ncpa/runs` | `system.deploy.ncpa` | Paginated run history (`status`, `needs_review`, `start_date`, `end_date`) plus the count of runs awaiting review |
| `GET /api/system/deployment/ncpa/runs/<run_id>` | `system.deploy.ncpa` | One run with per-device results |
| `POST /api/system/deployment/ncpa/runs/<run_id>/review` | `system.deploy.ncpa` | Mark a finished run reviewed (idempotent; 409 while running); writes an activity-log entry |
| `GET /api/system/deployment/ncpa/devices/trusted` | `system.deploy.ncpa` | List trusted devices whose agent is Pending NCPA or Deployment Failed |

Credentials are accepted only in request bodies, used for one SSH session, and
never stored, logged or returned. `error()` in `app/api/helper/responses.py`
accepts an optional `data` argument for errors the client must act on.

### `app/api/system/log.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/log/nagios` | `system.logs` | Bounded redacted Nagios state-log tail; lines 1–500 (default 200), after Unix seconds, at most 64 KiB; fixed configured path, unreadable returns empty/unavailable |
| `GET /api/system/log` | `system.logs` | User activity logs |
| `GET /api/system/configurationchange` | `system.logs` | Configuration-change logs |
| `GET /api/system/networkdiscovery` | `system.logs` | Discovery-run logs |
| `GET /api/system/ncpadeployment` | `system.logs` | NCPA deployment logs |
| `POST /api/system/exportlog` | Login | Record an export action |
| `GET /api/system/exportlog` | `system.logs` | Export history |

`GET /api/system/log/nagios` accepts only one `lines` (1–500, default 200)
and one `after` (0–2**63-1 Unix seconds, default 0); unknown, duplicate or
invalid parameters return 400. Response data is `{lines: string[], available:
boolean, truncated: boolean, max_lines: 500, max_bytes: 65536}`. `after` is
exclusive and applies within the bounded tail, not a full-history search.
Unreadable logs give 200 with `available=false` and an empty list. Both login
and `system.logs` are enforced. See the data spec for the conservative redaction
policy and fixed path; responses can still contain hostnames and addresses.


### `app/api/system/report.py`

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/report/availability` | `system.report` | Host availability for a period from Nagios `archivejson.cgi` durations; optional `hostname` scope is forwarded |
| `GET /api/system/report/hosts-by-os` | `system.report` | The same Nagios-backed host availability grouped by OS |
| `GET /api/system/report/network-services` | `system.report` | Network-wide service health report |
| `GET /api/system/report/device-services` | `system.report` | Per-device service health report |
| `GET /api/system/report/alerts` | `system.report` | Alert events/count from Nagios archives |
| `GET /api/system/report/notifications` | `system.report` | Notification events/count from Nagios archives |

## Plugin API

All routes are implemented in `app/api/plugin/manager.py`; supporting logic is
split across `scanner.py`, `service.py`, `reconcile.py` (the plugin reconciler), validators,
command defaults, `plugin_descriptions.py` (description/category/documentation
lookups, backed by the generated `plugin_catalog_data.py`), and
update/custom-plugin modules.

| Method and path | Permission | Purpose |
|---|---|---|
| `POST /api/plugin/scan` | `plugin.scan` | Start plugin-directory scan |
| `GET /api/plugin/scan/status` | `plugin.scan` | Read latest scan status |
| `GET /api/plugin` | `plugin.view` | Paginated plugin inventory; optional `group` (Network Services, Device Availability, Network Protocols, Servers, Application, Other) filters to one inventory tab (catalog category, with per-plugin fixes in `PLUGIN_GROUP_OVERRIDES`), 400 otherwise |
| `GET /api/plugin/summary` | `plugin.view` | Plugin-manager summary counts, including `enabled_plugins` (Enabled or Active; zero drives the "no plugins enabled" banner) |
| `GET /api/plugin/history` | `plugin.view` | Plugin audit/history records |
| `GET /api/plugin/<plugin_id>` | `plugin.view` | Plugin detail, including `description`, `category` and `documentation_url` (null for plugins outside the bundled catalog) |
| `GET /api/plugin/<plugin_id>/commands` | `plugin.view` | Commands and active overrides |
| `GET /api/plugin/<plugin_id>/dependencies` | `plugin.view` | Dependency status |
| `GET /api/plugin/<plugin_id>/enable-preview` | `plugin.view` | What enabling would monitor, without changing anything: `matched_services`, `matched_devices`, `held_ports`, `service_driven`, `already_enabled`, `message`. Counts monitored ports plus identified suggestions the plugin would promote; `held_ports` are identified ports held back and not attached |
| `GET /api/plugin/<plugin_id>/services` | `plugin.view` | What the plugin monitors, one row per Nagios service (`page`, `per_page`, `search`): `service`, `device`, `port`, `protocol`, `metric`, `monitored`, `running_since`, and `status` read from the latest `ServiceStatus` in history.db (`kind` is ok, warning, critical, unknown, waiting for the first check, stale after three check intervals, or stopped). Ports an admin stopped are listed with `monitored` false |
| `POST /api/plugin/<plugin_id>/services/stop` | `plugin.disable` | Body `{device_id, protocol, port}`: stop monitoring one port on one device. The port becomes Ignored, the service leaves Nagios, a history row is written; 409 if Nagios rejects it (the port goes back) or the port is protected (NCPA port of a deployed agent) |
| `POST /api/plugin/<plugin_id>/services/resume` | `plugin.enable` | Same body: resume a stopped port; its frozen plugin is kept |
| `GET /api/plugin/custom-check-devices` | `plugin.custom_check` | Up to 20 monitored devices (`id`, `hostname`, `ip_address`) matching `search`, for the custom check form's device picker |
| `GET /api/plugin/<plugin_id>/custom-checks` | `plugin.custom_check` | The plugin's custom checks (`page`, `per_page`, `search`): `id`, `name`, `service`, `device`, `variables`, `paused`, `running_since` and live `status` (`kind` as for services, or `paused`) |
| `POST /api/plugin/<plugin_id>/custom-checks` | `plugin.custom_check` | Body `{device_id, name, variables}`: run a plugin discovery cannot attach to a port against one device, then apply it. Only plugins whose details report `custom_checks.supported` take one. A plugin whose `custom_checks.target` is `server` (`check_apt`, `check_uptime`, ...) runs on the Nagios server itself and takes no `device_id` (400 if one is sent); every other one needs it (400 "Choose a device"). 400 for an unsupported plugin, unknown or retired device, missing or unsafe argument, or a name already used on that device; 409 if Nagios rejects it (nothing is saved, a Failed history row is written) |
| `PUT /api/plugin/<plugin_id>/custom-checks/<check_id>` | `plugin.custom_check` | Body `{name, variables, clear_secrets?}`: rename a check and replace its arguments; the device cannot change. A password left blank keeps the stored one; names in `clear_secrets` remove an optional one. Passwords are stored encrypted (`app/secrets_store.py`) and never returned: each check lists `secrets_set` and `secrets_readable` (false if the server key changed). Same errors, plus 404 for a check of another plugin |
| `POST /api/plugin/<plugin_id>/custom-checks/<check_id>/pause` | `plugin.custom_check` | Pause: the service leaves Nagios, the check stays listed; repeating reports `changed` false |
| `POST /api/plugin/<plugin_id>/custom-checks/<check_id>/resume` | `plugin.custom_check` | Resume a paused check; repeating reports `changed` false |
| `DELETE /api/plugin/<plugin_id>/custom-checks/<check_id>` | `plugin.custom_check` | Remove a check and its service; 409 if Nagios rejects it (the check stays) |
| `POST /api/plugin/<plugin_id>/enable` | `plugin.enable` | Enable a plugin, then run the plugin reconciler (`reconcile_plugin_monitoring`): identified ports whose plugin is now enabled are promoted and attached, hosts.cfg is regenerated once through the shared writer, and the plugin becomes Active if anything is attached. No device is picked by hand. The same reconcile runs after every network discovery, port edit, merge or retire, NCPA deployment and NCPA disk refresh. Plugin names are compared without a script extension (`check_ncpa.py` is `check_ncpa`). Only service-driven plugins (those a registry definition uses: `check_ssh`, `check_http`, `check_snmp`, `check_ncpa`, `check_tcp`, ...) can be enabled; any other returns 409. A failed attach does not undo the enable; the response carries `auto_apply` (`success`, `changed`, `applied`, `removed`, `promoted`, `message`) |
| `POST /api/plugin/<plugin_id>/disable` | `plugin.disable` | Disable a plugin, then reconcile: its services leave Nagios, its ports keep their state and frozen plugin so enabling restores them. If Nagios rejects the change the plugin goes back to its previous state, a failed history row is written and the route returns 409. A plugin enabled before the service-driven rule can still be disabled. The response carries `auto_apply` |
| `POST /api/plugin/<plugin_id>/commands/<command_id>/override` | `plugin.command_override` | Save a command override |
| `POST /api/plugin/<plugin_id>/commands/<command_id>/restore-default` | `plugin.command_restore` | Disable the active override |
| `GET /api/system/network-profile` | `system.network_health` | Network name, reference tag and detail rows for the Network Health card. ISP and Location are saved; IP Range, Subnet Mask, Gateway Device and DNS Server are derived on every read (scan networks, discovered devices, port 53) and flagged `derived: true` |
| `PUT /api/system/network-profile` | `settings.discovery` | Save the name, reference, ISP and Location; derived rows in the body are ignored |
| `POST /api/plugin/<plugin_id>/validate` | `plugin.validate` | Validate executable, permissions, and dependencies |
| ~~`POST /api/plugin/custom`~~ | `plugin.custom_add` | **Disabled** — route commented out in `manager.py` (and the client call in `pluginApi.ts`); not part of the current release |
| `POST /api/plugin/<plugin_id>/update` | `plugin.update` | Update from an archive |
| `POST /api/plugin/<plugin_id>/update/rollback` | `plugin.update_rollback` | Restore the backed-up version |

### Data polling settings contract

`GET /api/system` includes `dataPollingInterval` in seconds. `PUT /api/system`
accepts this optional field: omitting it preserves the saved value. Only integers
30, 60, 120 and 300 are supported (default 60); strings, booleans, null, fractional
numbers and unsupported values return 400 before changing settings or scheduling.
Changing it requires `settings.system` (403 otherwise); unauthenticated writes
return 401. Unchanged restricted values remain allowed on General saves.
Existing version conflicts (409) and the audit policy in effect before the save
apply; audit parameter name is `Data_Polling_Interval`.

Successful changes reschedule the existing `nagios_poll` job without starting a
disabled scheduler. Exceptions during rescheduling or persistence return 500 and
restore both the database transaction and the prior job trigger/next run time.
The job keeps coalescing and its single-instance limit, including while a poll is
running. Check/retry settings, discovery and browser preferences remain independent.

## Non-route backend modules

| Module | Responsibility |
|---|---|
| `api/system/statistics.py` | Shared current-state aggregation for dashboard and network health; never a blueprint |
| `api/helper/responses.py` | Standard response envelopes |
| `api/helper/validation.py` | Shared guard-clause validation and permission decorator |
| `api/helper/settings_flags.py` | Reads security/logging/session settings without importing route modules |
| `api/helper/database_access/` | User, role, and permission lookup helpers |
| `api/commands/seed.py` | Seeds permissions, roles, settings, and development users |
| `nagios/status.py` | Polls status/object CGI data and writes snapshot models |
| `api/plugin/plugin_descriptions.py` | One-line descriptions for the 58 bundled plugins; the scan fills a plugin's empty `Description` from it, and never overwrites an edited one |
| `nagios/notifications.py` | Queries archive CGI alerts and notification events |
| `nagios/pinpoint_events.py` | Pinpoint's own notifications (finished network scans) shaped like notification events |
| `network_discovery/` | Scans networks and builds/applies host/service configuration |
| `ncpa_deployment/` | Fingerprint-pinned SSH workflow and remote NCPA installation |
| `logging/` | Writes activity and subsystem audit records |
| `scheduler.py` | Polling, retention purge, automation scheduling, and the remediation spool consumer (every 15 seconds; at startup it marks runs left `running` as `interrupted`) |
| `remediation.py` | Reads the event handler spool (regular files under 2 KB owned by `REMEDIATION_SPOOL_OWNER`, at most 200 per run, symlinks never followed), parses each strictly, ignores SOFT states and recoveries (a HARD return to OK or UP never runs an action), matches enabled actions, applies the safety controls in order (the kill switch `Remediation_Enabled`, Maintenance Mode for every action type, scheduled downtime, and an acknowledged problem unless the action sets `Run_When_Acknowledged`; downtime and acknowledgement come from the newest Nagios status snapshot) and then the per-host-and-service cooldown and the per-action hourly cap, recording every skip with its reason, writes one `RemediationRun` row per decision, deletes the file, then runs the action; a replayed event runs nothing twice (unique `Event_Key` per action); a spool of more than 1000 files loses its oldest files (counted in the consumer state and logged); every tick, including one that finds the folder unreadable, saves a heartbeat that the health route reads |
| `remediation_actions.py` | The code-defined action types (`record_only`, and `restart_local_service` which runs `sudo -n /usr/bin/systemctl restart <unit>` as an argument list with no shell for a unit in `RESTARTABLE_UNITS`; it is refused for an unlisted unit or in Maintenance Mode, and records only the exit code, never command output): parameter schema and validation, `restart_remote_service` (#8 Part 8.3: restarts one unit on the device the event came from over SSH; see `remote_restart.py`; refused in Maintenance Mode, for a device that is not Active, is paused, is not trusted or has the switch off, and for a unit not on that device's list), and `run_action`, which enforces a timeout and turns a crash into a fixed message so no secret reaches the log. `RESTARTABLE_UNITS` and the installer sudoers drop-in must change together |
| `remote_restart.py` | Remote service restart (#8 Part 8.3). Device side: the root-owned helper `/usr/local/sbin/pinpoint-service-restart`, its one sudoers line (`/etc/sudoers.d/pinpoint-service-restart`, checked with `visudo` before it replaces the live file) and the root-owned list `/etc/pinpoint/restartable-services`, installed by the NCPA bootstrap with the administrator's one-time password. PinPoint side: `restart_remote_unit` checks the stored host-key fingerprint, logs in with the deployment key and runs only `sudo -n <helper> <unit>`; the unit must match a plain-name pattern, and only fixed text is returned. Design: `docs/plans/Issue_8_3_Remote_Restart_Design_Note.md` |
| `scripts/pinpoint_event_handler.py` | The Nagios event handler (standard library only): validates its arguments and writes one JSON file per event to the spool; never opens a shell or the network; installed by the installer at `/usr/local/sbin/pinpoint-event-handler` (`root:root`, 755) |
| `automation.py` | Settings-driven discovery, plugin/security checks, and database backups |

## Shared statistics contract

`statistics.py` exposes `get_latest_hosts()`, `get_latest_services()`,
`host_counts()`, `service_counts()`, `active_alert_count()`,
`avg_ping_metrics()`, `ncpa_averages()`, `nagios_server_resources()`,
`service_health_by_plugin()`, and `perf_trends()`.

The Nagios server host is identified by the statistics module's `NAGIOS_HOST`
constant (`localhost` for status snapshots). Do not confuse it with
`Config.NAGIOS_HOST`, which is the network address used to construct CGI URLs.

## Per-host email recipients (`app/api/system/host_recipients.py`)

| Method and path | Permission | Purpose |
|---|---|---|
| `GET /api/system/hosts/<id>/recipients` | `system.hosts.alerts` | Read selected user IDs, user choices and current eligibility for the stable discovered device |
| `PUT /api/system/hosts/<id>/recipients` | `system.hosts.alerts` | Replace recipients, apply through `regenerate_and_apply_config_status()`, audit and commit; 422 on validation/reload failure, restoring previous recipients |

The permission is separate from `account.alerts` and `system.hosts.edit`. PUT
requires JSON `{ "recipient_ids": [1, 2] }` (distinct positive existing user IDs;
no other fields); empty selections restore the default group. GET and successful
PUT return `recipient_ids`, `users` (`id`, `name`, `email`, `eligible`),
`using_default` and `editable`. Inactive or opted-out users may be selected, but
only Active opted-in users appear in the generated group. When none selected
qualify, the default applies. Retired/merged devices are readable but not editable
(409); a missing device returns 404. Read access intentionally includes the user
choices needed by this editor without requiring account-management permissions.

### Remote restart execution and action deletion (#182)

Remote restart uses the event's monitored device and its pinned SSH port. It
refuses non-Active, paused, untrusted or disabled devices, off-list units,
Maintenance Mode, cooldown and hourly caps. SSH socket, banner and authentication
operations are bounded; a re-fetched key must match the stored fingerprint before
it enters RejectPolicy's known-hosts table. The final connection also checks that
key. Remote restart polls command completion against a 20-second deadline,
discards stdout/stderr, closes SSH on timeout and records fixed outcomes. The
bootstrap suppresses remote output and secures the allowlist directory before
writing the root-owned file; sudoers is validated before replacement.

Deleting a remediation action clears its runs' nullable `Action_Id` foreign key
while preserving `Action_Name` and audit fields. The update and deletion share
the Nagios apply transaction and roll back together on a rejected apply.
