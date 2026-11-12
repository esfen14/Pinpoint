# `app/logging/` — activity, audit and job-status records

Small writer functions that save rows to `system.db` (models in
`app/system_models.py`). The package name shadows nothing in practice: it is
imported as `app.logging`, not the standard library `logging`.

| Module | Records |
|---|---|
| `user_activity.py` | User activity and audit log entries |
| `configuration_changes.py` | Settings changes, with old and new value |
| `export_logs.py` | Report and log exports |
| `network_discovery_status.py` | Progress and result of a discovery run, and services skipped |
| `plugin_scan_status.py` | Progress and result of a plugin scan |
| `deployment_history.py` | Progress and per-device results of an NCPA deployment |

Who runs it: the route and background-job code, never users directly. The Logs
page reads these rows through `app/api/system/log.py`.
