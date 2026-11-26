## 11. Maintenance and troubleshooting

### 11.1 Routine maintenance

| Task | Frequency **[R]** |
|---|---|
| Check Dashboard storage and backup health | Weekly |
| Review System Logs for failed logins and config changes | Weekly |
| Review Device Inventory Needs Review items | Weekly |
| Copy a backup off the server | Weekly |
| Apply OS security updates | Monthly or per policy |

### 11.2 Updates and patching

Upgrades are delivered by the installer. To update the web interface, run
`sudo bash /root/pinpoint/deploy-pinpoint-web.sh` as root; it pulls the latest `main`,
rebuilds the client and restarts the service, backing up databases and configuration first
and restoring them if the update fails (log: `/var/log/pinpoint-web.log`). Nagios Core, the
plugins and `check_ncpa.py` are handled by `sudo pinpoint-update` (read-only in the current
release). After any application upgrade: `flask db upgrade` then `flask sync-permissions`.

### 11.3 Hardware maintenance

Monitor free disk (Dashboard warns below 10%); keep the server on a UPS
**[R]**.

### 11.4 Network monitoring

Use PinPoint itself; also watch the appliance's own `localhost` checks.

### 11.5 Database optimisation

Retention settings purge old logs and diagnostic history daily. **[R]**
Occasionally `VACUUM` `history.db` during a maintenance window, with the
service stopped. The web interface is unavailable meanwhile (Nginx returns
502); Nagios keeps running. Check free disk space first: `VACUUM` needs room for
a temporary copy of the database.

Run as an administrator. Stop at the first failed step and go to **Recovery**.

```bash
cd /opt/pinpoint/Network-Diagnosis-System/server
sudo systemctl stop pinpoint-gunicorn
sudo install -d -m 700 /var/tmp/pinpoint-vacuum
sudo sh -c 'cp -p history.db* /var/tmp/pinpoint-vacuum/'
sudo -u pinpoint /opt/pinpoint/venv/bin/python -c 'import sqlite3; c = sqlite3.connect("history.db"); c.execute("VACUUM"); print(c.execute("PRAGMA integrity_check").fetchone()[0]); c.close()'
sudo systemctl start pinpoint-gunicorn
```

The integrity check must print `ok`. Then confirm that
`systemctl is-active pinpoint-gunicorn` prints `active` and that you can sign
in.

**Recovery** (the `VACUUM` or the check failed, or the service does not work
afterwards): put the copy back, keeping its owner, and start the service.

```bash
cd /opt/pinpoint/Network-Diagnosis-System/server
sudo systemctl stop pinpoint-gunicorn
sudo sh -c 'cp -p /var/tmp/pinpoint-vacuum/history.db* .'
sudo systemctl start pinpoint-gunicorn
```

Anything written to `history.db` after the copy is lost by this restore. Delete
`/var/tmp/pinpoint-vacuum` when PinPoint is confirmed healthy; it holds a copy
of the database.

Tried on an ISO install on 2026-11-25 with a 176 KiB `history.db`: `VACUUM` took
under a second, integrity was `ok` before and after, ownership and mode stayed
`pinpoint:pinpoint` 644, putting the copy back worked, and the service started
with no database errors. A damaged database and a large database were not tested.

### 11.6 Backup and restore

See 6.6 and [Backup and restore](guides/Backup_and_Restore.md). Also keep
a secure copy of `/etc/pinpoint/pinpoint.env`; without the same `SECRET_KEY`
stored passwords cannot be decrypted.

### 11.7 Common technical errors

| Error | Cause | Fix |
|---|---|---|
| Startup: "must be a number greater than zero" / "must be on or off" | Invalid environment value | Fix `/etc/pinpoint/pinpoint.env` |
| Dashboard stale | Scheduler off or Nagios stopped | `PINPOINT_SCHEDULER=1` on Gunicorn only, one worker; check Nagios |
| Nagios calls 401 | Wrong `NAGIOS_USERNAME`/`NAGIOS_PASSWORD` | Correct the env file |
| Stored passwords stopped working | `SECRET_KEY`/`PINPOINT_SECRETS_KEY` changed | Restore the key or re-enter passwords |
| `flask db upgrade` fails on old server | Built with `db.create_all()` | See root README "Database setup" |
| `flask` commands start the poller | `PINPOINT_SCHEDULER` set in shell | Unset it |
| Acknowledgement not in Nagios | Command pipe not writable | Add `pinpoint` to group `nagios`; check pipe path |
| Email fails | Helper missing, relay rejects | Settings → Email failure indicator; Nagios log |

### 11.8 Diagnostic procedure

1. Read Dashboard **Monitoring System** and freshness.
2. `systemctl status pinpoint-gunicorn nginx` and the Nagios service.
3. `journalctl -u pinpoint-gunicorn -n 200`.
4. System Logs → Nagios log tab.
5. Validate Nagios config: `sudo -u pinpoint /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg` **[A]** (path from `NAGIOS_BIN`, `NAGIOS_MAIN_CFG`).

### 11.9 Recovery procedures

- Locked-out administrator: `flask recover-bootstrap-admin`.
- Corrupt database: stop service, `flask restore-backup <folder> --yes`,
  follow printed steps.
- Bad Nagios config: the writer keeps a backup and rolls back rejected
  candidates; regenerate by saving a device or running a scan.
- Replacement host: install, restore env values (same `SECRET_KEY`), copy
  backup, restore.
