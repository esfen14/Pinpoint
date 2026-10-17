# Backup and restore (cold-standby recovery)

PinPoint keeps a daily copy of its two databases, `system.db` and `history.db`.
This page covers restoring that copy on the same host or on a freshly installed
replacement host. It is **cold standby**: one host runs at a time. There is no
second live node and no automatic failover.

## What is and is not backed up

| Backed up | Not backed up (record or copy it yourself) |
|---|---|
| `system.db` (accounts, roles, settings, devices, plugins, remediation) and `history.db` (check and alert history) | Generated Nagios configuration (it is rebuilt by the restore steps below) |
| | The NCPA deployment key and any SSH host-key fingerprints stored outside the databases |
| | `/etc/pinpoint/pinpoint.env`, including `SECRET_KEY`. Stored passwords are encrypted with it, so a replacement host needs the **same** `SECRET_KEY` |

Whether to back up the Nagios configuration and the NCPA deployment key is a
separate decision and is not covered here.

## Check that backups are happening

The dashboard status data (`GET /api/system/dashboard/status`, Dashboard
permission) includes `backup_health`:

| Field | Meaning |
|---|---|
| `newest_backup_at` | Time of the newest backup (UTC), or `null` if there is none |
| `backup_count` | Backup folders kept (the newest 7) |
| `total_bytes` | Size of the backup files |
| `automatic_backups` | The **Automatic backups** setting |
| `stale` | `true` when automatic backups are on and the newest backup is missing or older than two days. It is never `true` while automatic backups are off |

A scheduled backup that fails writes an activity-log entry, *Scheduled database
backup failed; see the application log*, at most once a day. The reason is in the
service log (`journalctl -u pinpoint-gunicorn`).

## Restore

Run these on the appliance as the `pinpoint` user, from `server/` with the
virtual environment active.

1. List the backups (`DATABASE_BACKUP_DIR`, default `server/database-backups`).
   A backup is a folder named `YYYYMMDD-HHMMSS`.
2. Stop the web service. Restoring under a running service is refused.

   ```bash
   sudo systemctl stop pinpoint-gunicorn.service
   ```

3. Restore. `--yes` confirms that the current databases will be replaced.

   ```bash
   flask restore-backup 20261016-020000 --yes
   ```

   The command refuses, and changes nothing, when the folder name is not in that
   format or is not a folder inside the backup directory, when either database
   file is missing, when either fails SQLite's integrity check, or when the
   service is running. `--force` skips only the running-service check.

   The current databases are kept in `pre-restore-<timestamp>` next to the
   backups. Backup rotation never deletes it; remove it yourself once the
   restore is confirmed good.

4. Run the follow-up steps the command prints:

   ```bash
   flask db upgrade --multidb
   flask sync-permissions
   ```

   Then regenerate the Nagios configuration through the existing writer (save a
   device, or run a discovery scan). It is checked with `nagios -v` before Nagios
   is reloaded.

5. Start the service and sign in.

   ```bash
   sudo systemctl start pinpoint-gunicorn.service
   ```

## Restoring onto a replacement host

1. Install PinPoint with the installer as usual.
2. Put the old host's `/etc/pinpoint/pinpoint.env` values (above all
   `SECRET_KEY`) in place.
3. Copy a backup folder from the old host into the new host's
   `DATABASE_BACKUP_DIR` (keep the folder name).
4. Follow **Restore** above.

## If a restore goes wrong

The command replaces each file with an atomic rename. If the second database
cannot be replaced, the first is put back from the safety copy. To undo a
finished restore, stop the service and copy `system.db` and `history.db` from
`pre-restore-<timestamp>` over the live files.

## Evidence

Unit tests cover the command and the health data (`server/tests/unit/test_backup_restore.py`,
`test_automation.py`, `test_dashboard.py`). A lab run on a fresh appliance
(`scripts/vmlab fresh`) is recorded in `docs/test-runs/` when performed.
