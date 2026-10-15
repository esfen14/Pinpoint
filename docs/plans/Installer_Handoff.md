# Installer handoff: everything the installer must do

One list of installer work taken from the open and recently closed issues (checked 2026-10-15). The
installer lives in a separate repository (`lorraine-pangilinan/PinPoint-Installer`); none of it is built
from this repository. Update this file when an item is done or a new issue adds one.

Rules that apply to every item: idempotent on upgrade, never overwrite an administrator's own settings,
`visudo -c` before any sudoers file is installed (keep the previous file if it fails), one full command
line per sudoers entry with no wildcards, no secrets in logs.

## Summary

| # | Item | Issue | Status | Needed for |
|---|---|---|---|---|
| 1 | Event spool folder | #120 | Done by hand on the lab appliance, not in the installer | Automatic recovery (#120, #121) |
| 2 | Event handler executable | #120 | Done by hand, not in the installer | Same |
| 3 | Narrower `nagios` group rights | #120 | Not started | Security review of #120 |
| 4 | Restart sudoers rule | #121 Part 8.2 | Not started | `restart_local_service` |
| 5 | Resource-file helper and sudo grant | #129 | Built, draft installer PR #7, not approved | NCPA/SMB secret transport on a real appliance |
| 6 | Journald size limit and installer log rotation | #124 Part 11.1 | Not started | Disk safety |
| 7 | Implicit TLS in the SMTP helper | #115 Part 2.1 | Conditional, only if the team wants it | Non-Gmail relays on port 465 |
| 8 | Wrapper for `recover-bootstrap-admin` | #95 follow-up | Not started, optional | Convenience |
| 9 | Wrapper for `restore-backup` | #125 | Not started, only if the issue is accepted | Convenience |

Items 1 to 4 belong together: #121 does nothing on an appliance without items 1 and 2 (the framework
that decides to restart) and item 4 (the permission to restart).

## 1 and 2. Event spool folder and handler (#120)

- Create `/usr/local/nagios/var/spool/pinpoint-events`: owner `nagios`, group `pinpoint`, mode `2770`.
  Its parent is root-owned. (The #120 issue text said `nagios:nagios`; the design and the lab use
  `nagios:pinpoint`, follow the design.)
- Add the `pinpoint` service user to group `pinpoint`.
- Install `server/scripts/pinpoint_event_handler.py` from the application as
  `/usr/local/sbin/pinpoint-event-handler`: `root:root`, mode `755`, not writable by the web user, no
  import of mutable application code. Set the mode explicitly (`install -m 755 -o root -g root`); the
  source file is stored in Git as `100644`, so do not rely on the copied file's mode.
- Keep `enable_event_handlers=1` in `nagios.cfg` and leave `illegal_macro_output_chars` at its default.
- Upgrade: create the folder and file on existing appliances without touching other Nagios settings or
  the SMTP helper.
- Checks (VM lab, record in `docs/test-runs/`): `nagios` can run the handler and write to the spool;
  `pinpoint` can read and delete entries; the web user cannot modify the handler; fresh install and
  upgrade both give the stated owners and modes.
- Source: `Event_Handler_Design.md` section 8 and issue #120.

## 3. Narrower `nagios` group rights (#120, decision D1)

The design records that the `nagios` group currently has wider rights than the handler needs (threats
T10 and T11) and calls the fixes "Fix A and B". The text of those fixes is not in this repository, so
the exact rights to remove must be taken from the installer review. Goal: the `nagios` group keeps only
what Nagios needs plus the spool folder above. Needs a person to confirm the list before changes.

## 4. Restart sudoers rule (#121 Part 8.2)

The `restart_local_service` action runs, as `pinpoint`: `sudo -n /usr/bin/systemctl restart <unit>`.

- Add the drop-in `/etc/sudoers.d/pinpoint-restart` (`root:root`, `0440`), one full command line per
  unit:
  `pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl restart nagios`
  The existing reload rule lists both `/usr/bin` and `/bin`; confirm which path the appliance resolves
  and add the second path as its own line if needed.
- The unit list must equal `RESTARTABLE_UNITS` in `server/app/remediation_actions.py` (today only
  `nagios`). Change both together. Do not add `pinpoint-gunicorn`: restarting it kills the process that
  runs the restart.
- Write to a temporary name, run `visudo -c -f`, move into place only if it passes. On upgrade replace
  the same way. Leave `/usr/local/sbin/pinpoint-apply-smtp` and `systemctl reload nagios` rules as they
  are.
- Checks as `pinpoint`: `sudo -n /usr/bin/systemctl restart nagios` works; `restart sshd` and
  `restart nagios extra` are refused; `sudo -n -l` shows no wildcard or shell.
- Release note: PinPoint can restart `nagios` automatically.
- Part 8.3 (remote restart) is not an installer item. It needs a design note first.

## 5. Resource-file helper (#129)

Already written on installer branch `issue-129-resource-helper`, published as draft
[installer PR #7](https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/7), with seven isolated
tests. It is a root-owned helper (`pinpoint-apply-resources`) that updates only the managed block of the
Nagios resource file through stdin, keeps `nagios:nagios` and `0660`, supports restoring previous bytes,
and has an exact no-argument sudoers grant for `pinpoint`. Remaining: reviewer approval and merge, and
installing it on every appliance before the application that uses it (an application upgrade without the
helper cannot write the resource file). Source: `Issue_129_Check_Secret_Transport.md`,
`docs/manuals/NCPA_Deployment.md`.

## 6. Journald limit and installer logs (#124 Part 11.1)

- Install `/etc/systemd/journald.conf.d/pinpoint.conf` setting `SystemMaxUse` and `MaxRetentionSec` to
  documented values, then restart journald. The values are not chosen yet; the lab appliance holds about
  40 MB with no overrides.
- Rotate `/var/log/pinpoint-*.log` with a logrotate rule, or document why they are exempt.
- Upgrade: idempotent, and keep any journald settings the administrator edited.
- Checks: fresh install has the drop-in and `journalctl --disk-usage` stays within the limit after log
  volume; upgrade with a pre-existing custom `journald.conf.d` file keeps it.

## 7. Implicit TLS in the SMTP helper (#115 Part 2.1, conditional)

Only if the team supports relays that need port 465. Extend `TLS_MODES` in the helper to add an
implicit-TLS value (for example `tls`, writing `tls on` and `tls_starttls off`). Keep `starttls` as the
default, keep rejecting any mode that sends the password unencrypted, keep the exact-fields,
atomic-write, ownership and mode behaviour, keep `/etc/msmtprc` as `root:nagios` `0640`, and do not
rewrite an existing STARTTLS configuration on upgrade. Checks: each valid and invalid `tls` value, a
VM-lab send through a TLS sink, and an upgrade test.

## 8. Wrapper for `recover-bootstrap-admin` (follow-up of #95, optional)

`Backend_Modules_and_Routes.md` says an installer-owned wrapper for
`sudo pinpoint recover-bootstrap-admin` is a separate follow-up. The backend command does not depend on it.

## 9. Wrapper for `restore-backup` (#125, only if accepted)

Issue #125 adds `flask restore-backup <folder>`. A convenience wrapper in the installer is optional and
not required by the issue.

## Not installer work, but related

- #167: `scripts/vmlab setup-admin` in this repository looks for `Username (email):`, but installer
  commit `697869e` prints `Username (temporary placeholder email):`. The fix is in the vmlab script here.
  The installer's labels should not change again without telling the lab script.
- #130, #131, #127, #122, #117, #118, #153 to #156, #164 and #173 need no installer change.
