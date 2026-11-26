## 6. Database design and management

### 6.1 Architecture

Two SQLite files through one Flask-SQLAlchemy `db.session`; the model's bind
selects the file.

| Database | Bind | Model files | Holds |
|---|---|---|---|
| `server/system.db` (`DATABASE_URL`) | default | `system_models.py`, `plugin_models.py` | Everything PinPoint produces: users, roles, settings, devices, acknowledgements, logs, plugins, remediation |
| `server/history.db` (fixed path next to `config.py`) | `history` | `history_models.py` | Nagios-sourced status and performance snapshots only |

Rule: a record's producer decides its database, not its topic.

### 6.2 Schema overview (main tables)

| Group | Tables |
|---|---|
| Identity and access | `PERMISSION`, `ROLE`, `ROLE_PERMISSION`, `USER`, `USER_PREFERENCES`, `PASSWORD_RESET_REQUEST` |
| Audit | `ACTIVITY_LOG`, `CONFIGURATION_CHANGES`, `EXPORT_LOG` |
| Discovery and devices | `NETWORK_DISCOVERY_STATUS`, `NETWORK_DISCOVERY`, `SKIPPED_SERVICE`, `OPEN_TCP_Services`, `OPEN_UDP_Services`, `DEVICE_PARENT`, `DEVICE_IDENTIFIER`, `DEVICE_ADDRESS_HISTORY`, `DEVICE_REVIEW_ITEM`, `DEVICE_INTERFACE` |
| Alerting | `ALERT_ACKNOWLEDGEMENT`, `ACK_HISTORY`, `NOTIFICATION_CURSOR`, `HOST_ALERT_RECIPIENT`, `ESCALATION`, `NOTIFICATION_POLICY` |
| Operations | `MAINTENANCE_WINDOW`, `MAINTENANCE_OCCURRENCE`, `RESOURCE_FORECAST`, `REMEDIATION_ACTION`, `REMEDIATION_RUN`, `REMEDIATION_CONSUMER_STATE` |
| NCPA | `SSH_CREDENTIALS`, `NCPA_DEPLOYMENT_STATUS`, `NCPA_DEPLOYMENT_RESULT`, `NCPA_DEPLOYMENT`, `NCPA_DEVICE_PARTITION` |
| Settings (singletons) | `SYSTEM_SETTINGS`, `DISCOVERY_SETTINGS`, `PLUGIN_SETTINGS`, `SMTP_SETTINGS`, `NETWORK_PROFILE` |
| Plugin Manager | `PLUGIN`, `PLUGIN_VERSION`, `PLUGIN_COMMAND`, `PLUGIN_COMMAND_OVERRIDE`, `PLUGIN_DEPENDENCY`, `PLUGIN_CONFIGURATION`, `PLUGIN_HISTORY`, plugin scan status |
| History bind | `HOST_STATUS`, `HOST_PERF_DATA`, `SERVICE_STATUS`, `SERVICE_PERF_DATA`, `PROGRAM_STATUS` |

Field-level detail: [`Data_Model_and_Integrations.md`](../../spec%20files/Data_Model_and_Integrations.md),
"Model inventory", and the model files themselves.

### 6.3 Entity relationship diagram

The full entity relationship diagram is generated from the models, so it is
always current: [`docs/reference/ERD.md`](../reference/ERD.md). It has an
overview of every table and relationship for skimming, then one diagram per
domain (accounts, settings, audit log, discovery and devices, NCPA deployment,
alerts, plugins, remediation, Nagios history) with every column, type and key.
A backend unit test fails when that file differs from the models. After a model
change, refresh it from `server/` with the virtual environment active:

```bash
python scripts/generate_erd.py
```

The diagram is built from the database schema (the model files), not from the
capstone paper's ERD (Chapter 3, Figure 4), which was a snapshot taken during the
project and is superseded by the generated file.

### 6.4 Keys, validation and integrity

- Every table has an integer surrogate primary key, except `DEVICE_PARENT`
  and `HOST_ALERT_RECIPIENT` (composite keys) and `NOTIFICATION_CURSOR`
  (keyed by user).
- Users are never deleted (`UserStatus`: Active, Inactive, Suspended); do not
  add delete cascades to user foreign keys. `NOTIFICATION_CURSOR` and
  `PASSWORD_RESET_REQUEST` carry legacy cascades.
- Strong device identifiers are unique on (`Kind`, `Value`).
- Fixed-value fields are Python `Enum` columns.
- Settings rows carry `Version` for optimistic concurrency (409 on conflict).
- `REMEDIATION_RUN.Event_Key` is unique per action (replay protection).
- Input is validated in route guard clauses before reaching the database,
  network, SSH or Nagios config.

### 6.5 Migrations

Multi-bind Flask-Migrate/Alembic in `server/migrations/`; every model change
ships a migration. From `server/` with the venv active:

```bash
flask db upgrade            # multi-database environment
flask sync-permissions      # add new permissions, grant to Super Admin
```

### 6.6 Backup and recovery

Automatic backups, once a day (`BACKUP_INTERVAL` in `automation.py`), (setting **Automatic Backups**) to
`DATABASE_BACKUP_DIR/YYYYMMDD-HHMMSS/`, newest 7 kept, using SQLite's online
backup. Restore with `flask restore-backup <folder> --yes` with the service
stopped. Not backed up: generated Nagios config, NCPA deployment key,
`/etc/pinpoint/pinpoint.env` (including `SECRET_KEY`). Runbook:
[Backup and restore](guides/Backup_and_Restore.md).

### 6.7 Access control

The database files are owned by the `pinpoint` service account and accessed
only by the application. Application-level access is RBAC (section 9).
Passwords are stored as hashes made by Werkzeug's `generate_password_hash`
(`User.set_password` in `system_models.py`). Stored secrets (SMTP password, custom-check
passwords, SNMPv3 passphrases) are Fernet-encrypted with a key from
`PINPOINT_SECRETS_KEY` or `SECRET_KEY`.
