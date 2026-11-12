# Pinpoint Backend

## Start for development

From the repository root:

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
flask run
```

The development API runs on
[http://127.0.0.1:5000](http://127.0.0.1:5000). `.flaskenv` points Flask at
`server.py` and enables debug mode.

For an existing environment, the shorter startup is:

```bash
cd server
source .venv/bin/activate
flask run
```

Useful commands:

```bash
pytest                                      # run the backend suite
pytest tests/unit/test_dashboard.py -v        # run one test module
```

See [Command-line commands](#command-line-commands) for the `flask` commands.
Do not use `flask seed --reset` on data you need to keep; it drops and rebuilds
the databases.

After changing models, use the multi-bind migration workflow. If this checkout
does not yet have a `migrations/` directory, initialize it first:

```bash
flask db init --multidb
flask db migrate --multidb -m "description"
flask db upgrade --multidb
```

## Python version

The backend targets **Python 3.14** (developed on 3.14.2). That is the version
the CI `backend` job, the dev container (`.devcontainer/devcontainer.json`), the
installer's appliance build and the Docker lab appliance (installed with `uv`,
because Ubuntu 22.04 ships an older Python) all use, and the pins in
`requirements.txt` are the set tested on it. Using another version is
unsupported: dependencies may resolve to untested versions and the tests may
behave differently. Changing the supported version means changing all four
places together, and the installer.

## Database layout

Two SQLite files, both in `server/` and git-ignored:

| File | Models | Contents | Bind |
|---|---|---|---|
| `system.db` | `app/system_models.py`, `app/plugin_models.py` | Users, roles, permissions, settings, acknowledgements, devices, discovery and deployment state, Plugin Manager records, logs | default (`DATABASE_URL` overrides the location) |
| `history.db` | `app/history_models.py` | Polled Nagios host, service, performance and program snapshots | `history` (fixed path next to `config.py`) |

Each model change ships with a migration in `migrations/versions/` that covers
both databases; see [`migrations/README.md`](migrations/README.md).

Backups: the scheduler writes a dated folder (`YYYYMMDD-HHMMSS`) holding both
files into `DATABASE_BACKUP_DIR` (default `server/database-backups/`) and keeps
the newest 7. Other folders under `server/` are generated, not source:
`running-host-config-backup/` (a copy of Nagios' `hosts.cfg` taken before it is
rewritten) and `host-config-files/` (generated host configuration files). Restore is described below and in
[Backup and restore](../docs/manuals/Backup_and_Restore.md).

## Command-line commands

Run from `server/` with the virtual environment active. Leave
`PINPOINT_SCHEDULER` unset so a command does not start the Nagios poller.

| Command | Use | When |
|---|---|---|
| `flask db upgrade --multidb` | Apply migrations to both databases | Fresh install and every upgrade |
| `flask init-production --admin-email EMAIL --password-stdin` | Seed permissions, roles and settings and create the first administrator; refuses to run if any user exists | Fresh production install, once (the installer runs it) |
| `flask sync-permissions` | Add permissions introduced since the install and grant them to the built-in `Super Admin` role; idempotent | After `flask db upgrade` on an existing install |
| `flask recover-bootstrap-admin` | Prompt twice for a temporary password for the earliest-created account and require a change at next sign-in | An administrator is locked out |
| `flask restore-backup FOLDER --yes` | Replace both databases with backup `FOLDER` (a name from `DATABASE_BACKUP_DIR`, not a path); the current files are kept in a `pre-restore-*` folder; stop `pinpoint-gunicorn.service` first | Disaster recovery. Then run `flask db upgrade --multidb`, `flask sync-permissions`, regenerate the Nagios configuration and start the service |
| `flask seed` | Add test users and sample data; `--reset` drops and rebuilds both databases | Development only, never on a real server |

The commands are defined in `app/api/commands/`.

## What this side does

The backend is the Flask API and integration layer for Pinpoint. It authenticates
users, enforces permissions, reads and aggregates Nagios monitoring data,
manages alerts and notifications, runs network discovery and NCPA deployment,
generates reports and logs, and manages server-side Nagios plugins.

The API is mounted under three prefixes:

- `/api/user/*` — authentication, accounts, roles, and preferences
- `/api/system/*` — dashboard, health, history, reports, logs, settings,
  discovery, and NCPA deployment
- `/api/plugin/*` — Plugin Manager inventory and administration

## Important parts

- `app/__init__.py` creates the Flask app, database, login manager, blueprints,
  CLI command, and scheduler.
- `app/api/` contains route blueprints and shared API helpers.
- `app/system_models.py` owns application data in `system.db`.
- `app/plugin_models.py` owns Plugin Manager data in `system.db`.
- `app/history_models.py` contains only Nagios-sourced snapshots in
  `history.db`.
- `app/nagios/` reads Nagios status, object, and archive JSON CGI endpoints.
- `app/network_discovery/` scans networks and generates validated Nagios host
  and service configuration.
- `app/ncpa_deployment/` performs fingerprint-verified remote NCPA deployment.
- `app/scheduler.py` polls Nagios, purges retained data, and triggers
  settings-driven automation.
- `config.py` contains database, Nagios, scan, plugin, and filesystem settings;
  the environment variables it reads are listed in the root
  [README](../README.md#production-settings).
- Package guides: [`app/api/`](app/api/README.md), [`app/nagios/`](app/nagios/README.md),
  [`app/network_discovery/`](app/network_discovery/README.md),
  [`app/ncpa_deployment/`](app/ncpa_deployment/README.md),
  [`app/logging/`](app/logging/README.md), [`scripts/`](scripts/README.md) and
  [`migrations/`](migrations/README.md).

## Folder structure

```text
server/
|-- app/
|   |-- api/
|   |   |-- user/              authentication, roles, accounts, preferences
|   |   |-- system/            monitoring, history, reports, logs, settings
|   |   |-- plugin/            Plugin Manager routes and services
|   |   |-- helper/            responses, validation, conversion, DB lookups
|   |   `-- commands/          Flask CLI commands such as seed
|   |-- nagios/                Nagios CGI readers and snapshot ingestion
|   |-- network_discovery/     scanning and Nagios config generation
|   |-- ncpa_deployment/       SSH/NCPA installation workflow
|   |-- logging/               audit and subsystem log writers
|   |-- system_models.py       default-bind application models
|   |-- plugin_models.py       default-bind plugin models
|   |-- history_models.py      history-bind Nagios snapshot models
|   |-- scheduler.py           recurring jobs
|   `-- automation.py          settings-driven scheduled tasks
|-- migrations/                Alembic migrations for both databases
|-- scripts/                   Nagios-side helper scripts installed on the appliance
|-- tests/                     unit, integration, e2e, support and plans
|-- config.py                  runtime configuration
|-- conftest.py                shared pytest environment and fixtures
|-- server.py                  Flask entry point and shell context
|-- requirements.txt          runtime dependencies
|-- requirements-test.txt     test dependencies
|-- system.db                 application-generated state
`-- history.db                Nagios monitoring snapshots
```

## Data and integration notes

The two SQLite databases share one SQLAlchemy session but have different
ownership:

- `system.db` stores users, roles, settings, acknowledgements, logs,
  discovery/deployment state, and Plugin Manager records.
- `history.db` stores polled host, service, performance, and Nagios program
  snapshots.

Current monitoring state comes from the latest `history.db` snapshots.
Historical state-change and notification events come from Nagios'
`archivejson.cgi`; these sources are intentionally not interchangeable.

Network discovery, SSH deployment, plugin installation, and Nagios
configuration touch external systems. Development and tests should use mocks or
temporary paths unless a live integration run is intentional.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "SECRET_KEY is not set" at start | Set `SECRET_KEY` in `server/.env`, or start with `FLASK_DEBUG=1` (development only) |
| No monitoring data in development | Set `NAGIOS_HOST`, `NAGIOS_USERNAME` and `NAGIOS_PASSWORD` in `server/.env`, and set `PINPOINT_SCHEDULER=1` with `FLASK_DEBUG=0` so the poller runs (`../dev/start-server.sh` does this) |
| `flask db upgrade` complains about missing tables or revisions | Read [`migrations/README.md`](migrations/README.md) before stamping |
| Tests touch a real Nagios | They should not; run `pytest tests/unit/`. Live tests are opt-in under `tests/integration/` and `tests/e2e/` |

## Testing

Tests use in-memory databases and suppress the background scheduler. See the
[backend test-suite guide](tests/README.md) for fixtures, module coverage, live
Nagios tests, and focused test commands.

## Further documentation

- [Backend Modules and Routes](../spec%20files/Backend_Modules_and_Routes.md)
- [Data Model and Integrations](../spec%20files/Data_Model_and_Integrations.md)
- [Engineering Standards](../spec%20files/Engineering_Standards.md)
