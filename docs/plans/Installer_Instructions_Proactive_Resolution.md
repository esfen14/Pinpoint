# Installer instructions: proactive resolution

Instructions for the installer repository (not built here). This file holds only the #121 section;
the #120 items (Fix A to D) are described in `Event_Handler_Design.md` section 8.

## #121 Part 8.2: sudoers rule for local service restarts

PinPoint's `restart_local_service` action runs, as the `pinpoint` user:

```
sudo -n /usr/bin/systemctl restart <unit>
```

Add a drop-in `/etc/sudoers.d/pinpoint-restart` (owner `root:root`, mode `0440`) with one full
command line per unit, no wildcards, no shell:

```
pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl restart nagios
```

Rules:
- The unit list must be identical to `RESTARTABLE_UNITS` in `server/app/remediation_actions.py`
  (today only `nagios`). Change both together. Do not add `pinpoint-gunicorn`: restarting it
  would kill the process that runs the restart.
- Write the file to a temporary name, run `visudo -c -f <temp>`, and move it into place only if
  that passes. If validation fails, keep the previous drop-in and stop the install with an error.
- On upgrade, replace the drop-in the same way. Leave the existing rules unchanged
  (`/usr/local/sbin/pinpoint-apply-smtp` and `systemctl reload nagios`).
- Release notes: say that PinPoint can now restart `nagios` automatically.

Checks on a VM lab, as `pinpoint`, recorded under `docs/test-runs/`:
- `sudo -n /usr/bin/systemctl restart nagios` works.
- `sudo -n /usr/bin/systemctl restart sshd` and `sudo -n /usr/bin/systemctl restart nagios extra` are refused.
- `sudo -n -l` shows no wildcard or shell.
