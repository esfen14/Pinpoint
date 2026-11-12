# `app/api/` — HTTP routes

The Flask blueprints that make up the REST API. `__init__.py` builds `api_bp`
(`/api`) and mounts three sub-blueprints. Nothing here is run directly; the app
factory in `app/__init__.py` registers it.

| Folder | Prefix | Holds |
|---|---|---|
| `user/` | `/api/user` | Sign-in, accounts, roles, password requests, preferences |
| `system/` | `/api/system` | Dashboard, Network Health, Device Inventory, discovery, NCPA deployment, notifications, reports, logs, settings, remediation |
| `plugin/` | `/api/plugin` | Plugin Manager inventory, validation, updates and custom checks |
| `helper/` | none | Shared response, validation, conversion and database-lookup helpers |
| `commands/` | none | The Flask CLI commands: `seed`, `sync-permissions`, `recover-bootstrap-admin`, `init-production`, `restore-backup` (see [`server/README.md`](../../README.md#command-line-commands)) |

Who runs it: the web service, on every request. Developers add or change routes
here.

The complete route catalog, permissions and response contract are in
[Backend Modules and Routes](../../../spec%20files/Backend_Modules_and_Routes.md);
`scripts/check_route_drift.py` fails when that catalog and the registered routes
disagree. Each module starts with a docstring and each route has a prose
docstring (see [Engineering Standards](../../../spec%20files/Engineering_Standards.md)).
