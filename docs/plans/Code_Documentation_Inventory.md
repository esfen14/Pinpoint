# Code documentation inventory

**Status:** draft inventory for issue #292; feeds the Technical Manual module reference (#181 §3.7), which does not exist yet.
**Counted:** 2026-11-14 on branch `sys-missing-docu-inventory`.

This records which Python modules and public names under `server/app` and `server/scripts` have no docstring. It is documentation only: no code was changed. Adding the docstrings themselves is a separate follow-up that needs owner approval (see [Follow-up](#follow-up)).

## How it was counted

Every `.py` file under `server/app` and `server/scripts` was parsed with Python's `ast` module. A file counts as **undocumented** when it has no module docstring (empty package markers are included). A **public name** is a top-level function or class whose name does not start with an underscore; it counts as undocumented when it has no docstring. Methods and nested functions are not counted. Decorated route handlers count as ordinary functions.

## Totals

| Measure | Count |
|---|---|
| Python files scanned | 116 |
| Files with no module docstring | 37 (35 with code, 2 empty package markers) |
| Public top-level functions and classes | 1,106 |
| Of those, with no docstring | 217 |

The issue's scan reported about 225 of 1,092; the difference is the counting rules above and code added since.

| Area | Files | Files without module docstring | Public names | Without docstring |
|---|---|---|---|---|
| `server/app` (top level) | 18 | 4 | 228 | 69 |
| `server/app/api` | 58 | 16 | 481 | 83 |
| `server/app/logging` | 7 | 7 | 22 | 15 |
| `server/app/nagios` | 8 | 4 | 52 | 18 |
| `server/app/ncpa_deployment` | 1 | 1 | 29 | 7 |
| `server/app/network_discovery` | 19 | 5 | 260 | 16 |
| `server/scripts` | 5 | 0 | 34 | 9 |

## Frontend

In `client/src/lib/*Api.ts` and `client/src/hooks/`, 15 of the 26 files have no leading comment explaining their purpose. They are described in the tables of [`Frontend_Modules_and_Routes.md`](../../spec%20files/Frontend_Modules_and_Routes.md) only. Frontend comments are out of scope for the follow-up unless the owner adds them.

## Module reference

What each undocumented module is for. This is the text intended for the Technical Manual's module reference; it was written from reading each file's top-level names and the owning specification, so confirm any line before it is published (**TBC** where a module has behavior this summary does not cover). Columns: lines, public names, public names without a docstring.

| File | Lines | Public | No docstring | Purpose |
|---|---|---|---|---|
| `server/app/__init__.py` | 80 | 0 | 0 | Application factory module: builds the Flask app, database, migrations, login manager and CORS, registers the `/api` blueprint and the command-line commands. |
| `server/app/api/__init__.py` | 18 | 0 | 0 | Defines the `/api` blueprint and attaches the user, system, plugin and other sub-blueprints. |
| `server/app/api/commands/restore.py` | 69 | 1 | 0 | `flask restore-backup` command: restores a backup folder and prints the follow-up steps. See the backup and restore guide. |
| `server/app/api/commands/seed.py` | 544 | 16 | 7 | Seed and bootstrap commands: permissions, built-in roles, development users, `sync-permissions`, `recover-bootstrap-admin`, `init-production` and default system settings. |
| `server/app/api/helper/converter.py` | 254 | 14 | 6 | Conversions between Nagios values and Pinpoint enums, time conversion, email normalising, and performance-data parsing. |
| `server/app/api/helper/database_access/__init__.py` | 10 | 0 | 0 | Re-exports the user, role and permission lookup helpers. |
| `server/app/api/helper/database_access/permissions.py` | 99 | 4 | 3 | Permission checks: `require_permission` decorator and `user_has_permission`. |
| `server/app/api/helper/database_access/role_access.py` | 48 | 5 | 5 | Role lookups by id or name and name-uniqueness checks. |
| `server/app/api/helper/database_access/user_access.py` | 61 | 8 | 7 | User lookups by id or email, the Super Admin lookup and email-uniqueness checks. |
| `server/app/api/helper/responses.py` | 43 | 2 | 0 | `success` and `error` helpers that build the standard JSON response. |
| `server/app/api/helper/validation.py` | 198 | 14 | 13 | Request validation: password policy, JSON fields, user/role existence, status values and email checks. |
| `server/app/api/plugin/__init__.py` | 5 | 0 | 0 | Defines the `/plugin` blueprint and loads the Plugin Manager routes. |
| `server/app/api/system/__init__.py` | 31 | 0 | 0 | Defines the `/system` blueprint and loads each system route module. |
| `server/app/api/system/network_profile.py` | 213 | 3 | 2 | Network profile routes: saved network details plus values derived from scanned networks, devices, gateway and DNS. |
| `server/app/api/user/__init__.py` | 8 | 0 | 0 | Defines the `/user` blueprint and loads the login, management, password-request and preference routes. |
| `server/app/api/user/management.py` | 1023 | 16 | 10 | Account and role administration routes: roles, accounts, password change, first-run setup, and the bootstrap-administrator protections. |
| `server/app/api/user/preferences.py` | 41 | 2 | 2 | Per-user display preferences routes. |
| `server/app/history_models.py` | 167 | 10 | 10 | Models and enums for `history.db`: host and service status, performance data and program status. |
| `server/app/logging/__init__.py` | 4 | 0 | 0 | Re-exports the audit-log writers. |
| `server/app/logging/configuration_changes.py` | 25 | 1 | 1 | Writes configuration-change log entries. |
| `server/app/logging/deployment_history.py` | 205 | 10 | 4 | NCPA deployment run records: create, update, per-device results and progress. |
| `server/app/logging/export_logs.py` | 27 | 1 | 1 | Writes an export log entry when a report is exported. |
| `server/app/logging/network_discovery_status.py` | 95 | 5 | 4 | Network discovery run records: create, update, skipped services and progress. |
| `server/app/logging/plugin_scan_status.py` | 69 | 3 | 3 | Plugin scan run records: create, update and read the latest. |
| `server/app/logging/user_activity.py` | 28 | 2 | 2 | Writes user activity and audit log entries. |
| `server/app/nagios/notifications.py` | 310 | 10 | 1 | Reads alert and notification archives from Nagios and normalises, fills previous states and collapses repeats for the History page. |
| `server/app/nagios/pinpoint_events.py` | 61 | 2 | 2 | Turns discovery-run records into events shown on the History page. |
| `server/app/nagios/status.py` | 346 | 5 | 4 | Polls Nagios status and stores host, service and program status; resolves acknowledgements that recovered. |
| `server/app/nagios/version.py` | 22 | 1 | 1 | Checks the latest published Nagios version. |
| `server/app/ncpa_deployment/ncpa_deployment.py` | 1329 | 29 | 7 | NCPA deployment over SSH: host-key checks, deployment user and key, install, verification, disk discovery and per-device results. |
| `server/app/network_discovery/__init__.py` | 0 | 0 | 0 | Empty package marker. |
| `server/app/network_discovery/create_host_cfg.py` | 2343 | 34 | 2 | Builds and applies Nagios host and service configuration from discovery results: plugin planning, secrets substitution, validation, backup and apply. |
| `server/app/network_discovery/host_config_templates.py` | 369 | 25 | 7 | Renders Nagios object definitions (hosts, services, contacts, notification and event-handler commands, escalations, flap settings). |
| `server/app/network_discovery/network_discovery.py` | 317 | 3 | 1 | Runs nmap scans (TCP and UDP) over networks or one device and maps results to services. |
| `server/app/network_discovery/templates/__init__.py` | 0 | 0 | 0 | Empty package marker for the template files. |
| `server/app/scheduler.py` | 286 | 3 | 0 | Background scheduler: Nagios polling, remediation spool, forecasts, NCPA relocation, maintenance windows and data purge. |
| `server/app/system_models.py` | 1436 | 66 | 42 | Models and enums for `system.db`: accounts and roles, logs, discovery and devices, ports, maintenance, NCPA deployment, settings and acknowledgements. |

Owning specifications: routes and helpers in [`Backend_Modules_and_Routes.md`](../../spec%20files/Backend_Modules_and_Routes.md); models, Nagios data, scheduler, discovery and NCPA in [`Data_Model_and_Integrations.md`](../../spec%20files/Data_Model_and_Integrations.md).

## Public names without a docstring

| File | Count | Names |
|---|---|---|
| `server/app/api/commands/seed.py` | 7 of 16 | `get_role`, `get_permission`, `seed_permissions`, `seed_roles`, `seed_users`, `remove_seed_data`, `seed_command` |
| `server/app/api/helper/converter.py` | 6 of 14 | `convert_user_status`, `convert_host_state_type_enum`, `convert_to_UTC`, `convert_to_UNIX`, `normalize_email`, `get_range_day` |
| `server/app/api/helper/database_access/permissions.py` | 3 of 4 | `require_permission`, `exists_permission_by_id`, `exists_permission_by_name` |
| `server/app/api/helper/database_access/role_access.py` | 5 of 5 | `get_role_by_id`, `get_role_by_name`, `exists_role_by_id`, `exists_role_by_name`, `has_name` |
| `server/app/api/helper/database_access/user_access.py` | 7 of 8 | `get_user_by_id`, `is_super_admin`, `get_user_by_email`, `get_all_users`, `exists_user_by_id`, `exists_user_by_email`, `has_email` |
| `server/app/api/helper/settings_flags.py` | 2 of 4 | `is_failed_login_monitoring_enabled`, `is_strong_password_policy_enabled` |
| `server/app/api/helper/validation.py` | 13 of 14 | `validate_password`, `validate_password_is_same`, `validate_user_exists`, `validate_user_not_exists`, `validate_role_exists`, `validate_role_not_exists`, `validate_role_name_available`, `validate_permission_exists`, `validate_json_data`, `validate_userstatus`, `validate_user_email`, `validate_deliverable_email_domain`, `validate_email_available` |
| `server/app/api/plugin/custom_plugin.py` | 3 of 7 | `UploadTooLargeError`, `InvalidFilenameError`, `NameCollisionError` |
| `server/app/api/plugin/plugin_update.py` | 10 of 17 | `InvalidUrlError`, `DownloadError`, `ArchiveTooLargeError`, `UnsupportedArchiveError`, `UnsafeArchiveError`, `PluginNotInArchiveError`, `NoBackupAvailableError`, `get_backup_path`, `has_backup`, `cleanup_staging` |
| `server/app/api/plugin/reconcile.py` | 1 of 6 | `utcnow` |
| `server/app/api/plugin/scanner.py` | 1 of 7 | `ScannedPlugin` |
| `server/app/api/plugin/service.py` | 5 of 50 | `serialize_command`, `get_active_override`, `PluginNameTakenError`, `NoExecutableError`, `configured_check_interval_minutes` |
| `server/app/api/system/maintenance.py` | 2 of 7 | `get_window_or_404`, `apply_fields` |
| `server/app/api/system/network_profile.py` | 2 of 3 | `get_network_profile`, `update_network_profile` |
| `server/app/api/system/settings.py` | 1 of 3 | `get_settings` |
| `server/app/api/user/login.py` | 1 of 4 | `enforce_password_change` |
| `server/app/api/user/management.py` | 10 of 16 | `permission_list`, `roles`, `list_roles`, `role_info`, `roles_status`, `available_accounts`, `account_info`, `change_password`, `complete_setup`, `user_permission` |
| `server/app/api/user/password_requests.py` | 2 of 4 | `forgot_password`, `dismiss_password_request` |
| `server/app/api/user/preferences.py` | 2 of 2 | `get_preferences`, `update_preferences` |
| `server/app/history_models.py` | 10 of 10 | `ConnectionStateType`, `HostStateType`, `ServiceStateType`, `PluginStatusType`, `AcknowledgementType`, `HostStatus`, `HostPerfData`, `ServiceStatus`, `ServicePerfData`, `ProgramStatus` |
| `server/app/logging/configuration_changes.py` | 1 of 1 | `create_configuration_log` |
| `server/app/logging/deployment_history.py` | 4 of 10 | `create_ncpa_deployment_status`, `update_ncpa_deployment_status`, `get_deployment_ncpa_status`, `calculate_progress` |
| `server/app/logging/export_logs.py` | 1 of 1 | `create_export_log` |
| `server/app/logging/network_discovery_status.py` | 4 of 5 | `create_network_discovery_status`, `update_network_discovery_status`, `get_network_discovery_status`, `calculate_progress` |
| `server/app/logging/plugin_scan_status.py` | 3 of 3 | `create_plugin_scan_status`, `update_plugin_scan_status`, `get_plugin_scan_status` |
| `server/app/logging/user_activity.py` | 2 of 2 | `create_user_log`, `create_audit_log` |
| `server/app/maintenance.py` | 1 of 11 | `epoch` |
| `server/app/nagios/commands.py` | 10 of 22 | `CommandResult`, `acknowledge_host_problem`, `acknowledge_service_problem`, `remove_host_acknowledgement`, `remove_service_acknowledgement`, `schedule_forced_host_check`, `schedule_forced_service_check`, `schedule_host_downtime`, `schedule_service_downtime`, `release_recheck` |
| `server/app/nagios/notifications.py` | 1 of 10 | `request_notifications_last` |
| `server/app/nagios/pinpoint_events.py` | 2 of 2 | `get_scan_events`, `get_scan_event` |
| `server/app/nagios/status.py` | 4 of 5 | `insert_programstatus_data`, `insert_host_status_data`, `insert_service_status_data`, `get_status` |
| `server/app/nagios/version.py` | 1 of 1 | `check_latest_version` |
| `server/app/ncpa_deployment/ncpa_deployment.py` | 7 of 29 | `mark_device_incompatible`, `update_ncpa_deployment_info`, `connect_with_fingerprint_check`, `ensure_deployment_user`, `install_deployment_key`, `install_restricted_sudo`, `install_deployment_helper` |
| `server/app/network_discovery/create_host_cfg.py` | 2 of 34 | `discover_network_create_hosts`, `add_ncpa_port` |
| `server/app/network_discovery/custom_checks.py` | 1 of 16 | `field` |
| `server/app/network_discovery/device_identity.py` | 2 of 43 | `utcnow`, `host_name_in_use` |
| `server/app/network_discovery/host_config_templates.py` | 7 of 25 | `check_interval`, `create_service`, `create_contact`, `create_contact_template`, `create_hostgroup`, `create_contactgroup`, `create_multi_host_service` |
| `server/app/network_discovery/network_discovery.py` | 1 of 3 | `discover_network` |
| `server/app/network_discovery/plugin_registry.py` | 1 of 32 | `Transport` |
| `server/app/network_discovery/port_lifecycle.py` | 2 of 30 | `utcnow`, `transport_for` |
| `server/app/plugin_models.py` | 14 of 18 | `PluginType`, `PluginSource`, `PluginStatus`, `Plugin`, `PluginVersion`, `PluginCommand`, `PluginCommandOverride`, `DependencyType`, `DependencyStatus`, `PluginDependency`, `PluginHistoryAction`, `PluginActionResult`, `PluginHistory`, `PluginScanStatusValue` |
| `server/app/remediation_actions.py` | 1 of 15 | `ActionType` |
| `server/app/smtp_settings.py` | 1 of 11 | `get_smtp_row` |
| `server/app/system_models.py` | 42 of 66 | `Permission`, `Role`, `RolePermission`, `UserStatus`, `User`, `load_user`, `ActivityLog`, `ConfigurationChanges`, `ExportFormat`, `ExportLog`, `DiscoveryStatus`, `NetworkDiscoveryStatus`, `ServiceProtocol`, `SkippedService`, `AddressingMode`, `IdentityConfidence`, `DeviceState`, `IdentifierKind`, `AddressSource`, `ReviewKind`, `PortState`, `PortSource`, `NetworkDiscovery`, `Open_TCP_Services`, `Open_UDP_Services`, `SSHCredentials`, `DeploymentStatus`, `NCPADeploymentStatus`, `AgentStatus`, `DeploymentMethod`, `NCPADeployment`, `SystemSettings`, `DiscoverySettings`, `PluginSettings`, `NetworkProfile`, `UserPreferences`, `AckAction`, `RemediationActionType`, `RemediationScope`, `RemediationEventState`, `RemediationEventStateType`, `RemediationOutcome` |
| `server/scripts/build_plugin_descriptions.py` | 1 of 5 | `main` |
| `server/scripts/pinpoint_notify_email.py` | 8 of 14 | `parse`, `target_of`, `subject_for`, `device_rows`, `render_text`, `render_html`, `build_message`, `main` |

## Follow-up

A follow-up issue should propose adding a one-paragraph module docstring to the 37 files above, then docstrings to the 217 public names, starting with the larger modules (`system_models.py`, `api/user/management.py`, `ncpa_deployment.py`, `create_host_cfg.py`). It changes code files (comments only) and needs owner approval before it is opened; it has not been opened.
