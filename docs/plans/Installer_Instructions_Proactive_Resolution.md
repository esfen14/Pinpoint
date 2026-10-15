# Installer instruction: permissions and files for proactive resolution (event handlers)

Written for: the PinPoint Installer maintainer (the installer lives outside this repository,
`lorraine-pangilinan/PinPoint-Installer`).
Tracks: the proactive-resolution work in this repository: GitHub issues #120 (event handler
framework, Part 7.3 Installer), #121 (recovery actions, Part 8.2 sudo rule) and the permission
decision D1 in `docs/plans/Event_Handler_Security_Review.md`.

File and line references below were read in the installer repository on 2026-10-14. If a line
has moved, search for the quoted text.

## 1. The issue

PinPoint is about to let Nagios trigger actions (restart a service when it fails for good).
Before that is safe, two things on an installed appliance must change. Both were measured on a
lab appliance (Ubuntu 22.04.5) on 2026-10-13.

**1a. The `nagios` group gives the web server too much.** The web server user `www-data` is in
group `nagios` (it has to be: Apache runs Nagios's own CGIs, and PinPoint reads alert history
from `archivejson.cgi`). The group also lets `www-data`, and so anyone who breaks into the web
server, do this:

| What | Current owner and mode | What the group can do |
|---|---|---|
| `/usr/local/nagios/var/rw/nagios.cmd` | `nagios:nagios` 660 | Write Nagios commands: acknowledge, disable notifications, schedule downtime |
| `/usr/local/nagios/var/status.dat` and other files in `var/` | group writable | Change what Nagios reports |
| `/etc/msmtprc` | `root:nagios` 640 | Read the Gmail app password |
| `/usr/local/nagios/libexec` | `nagios:nagios` 775 | Replace a plugin that Nagios runs |

**1b. There is nowhere safe for the event handler.** Nagios will call one small program on a
state change. It must not be writable by the web server or by `nagios`, and Nagios must be able
to write its output where only PinPoint reads it. `/usr/local/nagios/libexec` (group-writable by
`nagios`, so by `www-data`) is the wrong place, and `/usr/local/nagios/var/spool` is `root:root`
755 so nobody but root can create anything in it.

## 2. What needs to be fixed

### Fix A. Keep the Gmail password away from the web server (required)

Where: `setup/configure-pinpoint-privileges.sh`

- near line 370: `chown root:"$NAGIOS_GROUP" "$MSMTP_CFG"` followed by `chmod 640`
- near line 397, inside the embedded `pinpoint-apply-smtp` helper: `OWNER_GROUP = "nagios"`

Why: `msmtprc` holds the SMTP password. Only the `nagios` user (which sends the mail) needs to read
it. Today `www-data` can too, through the shared group. The PinPoint app does not read this file:
its "send test email" uses `smtplib` with the settings in its own database
(`server/app/smtp_settings.py`), and the file is written by the root helper.

How:

1. Create a group with one member: `groupadd -r pinpoint-mail`, `usermod -aG pinpoint-mail nagios`
   (idempotent: skip if it exists).
2. Change both places above to that group (`chown root:pinpoint-mail`, keep mode 640, and set
   `OWNER_GROUP = "pinpoint-mail"` in the helper).
3. Upgrade: on a re-run, re-apply the owner to an existing `/etc/msmtprc`.

Check:
- `sudo -u www-data cat /etc/msmtprc` is refused.
- `sudo -u pinpoint cat /etc/msmtprc` is refused.
- `sudo -u nagios cat /etc/msmtprc` works.
- Settings -> Email in PinPoint still saves and the "send test email" still works.
- A Nagios notification still arrives (stop a monitored host and wait for the alert).

### Fix B. Narrow the Nagios command pipe and status files (required)

Where: `setup/install-nagios-core.sh` (after `make install-commandmode`, near line 114) and, for
an existing appliance, `setup/configure-pinpoint-privileges.sh` (the same place that already does
`usermod -aG "$NAGIOS_GROUP" "$APP_USER"`, near line 251).

Why: so that only `nagios` and `pinpoint` can send Nagios commands, and so that the web server
can read Nagios's files but not change them.

How:

1. `chgrp pinpoint /usr/local/nagios/var/rw && chmod 2770 /usr/local/nagios/var/rw`. The command
   pipe `nagios.cmd` then belongs to `nagios` with group `pinpoint`; `www-data` is no longer
   able to reach it. `cmd.cgi` is unusable today (`authorized_for_*_commands` lists only
   `nagiosadmin`, which has no usable password), so nothing is lost.
2. Make the files under `/usr/local/nagios/var/` (not `rw/`) owned by `nagios`, directory 755
   and files 644, so the CGIs can still read them and the group can no longer write them.
   `pinpoint` must not need to write there. Confirm that before changing it.
3. Do NOT remove `www-data` from group `nagios` (`install-nagios-core.sh` line 100). That breaks
   PinPoint's alert history.

Check:
- `sudo -u www-data bash -c 'echo > /usr/local/nagios/var/rw/nagios.cmd'` is refused.
- `sudo -u pinpoint` can still write a command (the "Check Now" and acknowledgement features
  from issue #132 use this pipe).
- After `systemctl restart nagios` the pipe still has the same owner, group and mode (Nagios
  recreates it). If it does not, set it in a `ExecStartPost` drop-in for `nagios.service`.
- The Nagios web pages and PinPoint's notification bell still load.

### Fix C. Create the event spool directory (required for issue #120)

Where: `setup/configure-pinpoint-privileges.sh` (new section, after the existing steps).

Why: Nagios appends one line per state change here; PinPoint reads and deletes them. The owner
and group are chosen so that `www-data` cannot see or forge lines.

How:

- `/usr/local/nagios/var/spool/pinpoint-events`, owner `nagios`, **group `pinpoint`**, mode
  `2770` (not group `nagios`: `www-data` is in it). Create it with `install -d -m 2770 -o nagios
  -g pinpoint`. The parent directory is `root:root` 755, so only the installer can create it.
- Idempotent: run it again without error and without changing files already inside.

Check:
- `sudo -u nagios touch .../pinpoint-events/x` works; `sudo -u pinpoint rm` of it works.
- `sudo -u www-data ls .../pinpoint-events` is refused.

### Fix D. Install the event handler program (required for issue #120)

Where: `setup/configure-pinpoint-privileges.sh`, modelled on how `pinpoint-apply-smtp` is
installed (lines ~383 to 540: written as a heredoc, `chown root:root`, `chmod 755`).

Why: Nagios runs it as the `nagios` user on every state change. It must be root-owned so neither
`nagios`, `pinpoint` nor `www-data` can replace it. It only appends one validated JSON line to the
spool; it never fixes anything itself.

How:

- Path: `/usr/local/sbin/pinpoint-event-handler`, `root:root`, mode 755. Not under `libexec`,
  and not under `/opt/pinpoint` (the `nagios` user may not be able to enter that folder).
- Source: this repository will provide it at `server/scripts/pinpoint_event_handler.py`
  (to be added with issue #120) so it is reviewed and tested here. The installer copies that
  file; it must not carry its own copy of the logic.
- Run it with the same interpreter flags as the email script: `/usr/bin/python3 -I`.
- Upgrade: replace the file on every run, and do not touch anything else.

Check:
- `stat -c '%U:%G %a' /usr/local/sbin/pinpoint-event-handler` shows `root:root 755`.
- None of `nagios`, `pinpoint`, `www-data` can write it.
- Run it as `nagios` with sample arguments and see one line appear in the spool.

### Fix E. Nagios settings for event handlers (check, probably no change)

Where: `setup/configure-nagios.sh`.

Why: event handlers must be enabled, bounded in time and logged. The lab appliance already has
`enable_event_handlers=1`. Confirm these three on a fresh install and set them if missing:
`enable_event_handlers=1`, `event_handler_timeout=30`, `log_event_handlers=1`. Also confirm
`check_external_commands=1` (PinPoint's command channel needs it).

Check: `grep -E '^(enable_event_handlers|event_handler_timeout|log_event_handlers|check_external_commands)=' /usr/local/nagios/etc/nagios.cfg`.

### Fix F. Allow local service restarts through one narrow sudo rule (only when issue #121 ships)

Where: `setup/configure-pinpoint-privileges.sh`, modelled on the existing SMTP rule (variables
`SMTP_SUDOERS_FILE`, `visudo -cf`, `install -m 440`, near lines 550 to 560).

Why: a recovery action restarts a service on the PinPoint server as the `pinpoint` user. It needs
exactly the commands in an allowlist and nothing else.

How:

- A new file `/etc/sudoers.d/pinpoint-service-recovery`, written to a temp file, checked with
  `visudo -cf`, installed `440 root:root`. If the check fails, do not install it and stop with an
  error (same as the SMTP rule).
- One line per allowed unit, written as the full command, with no wildcards. The exact unit list
  comes from issue #121. `pinpoint-gunicorn` is excluded from the first list, because restarting
  the web interface from itself drops the request.
- Do NOT add any rule that lets `pinpoint` restart services on other machines. Remote restart is
  deliberately left out (decision D2): it would need a new privileged helper on every monitored
  device.

Check: `sudo -n -l -U pinpoint` lists only the allowed commands, plus the two rules that already
exist. A command not on the list (for example `sudo -n systemctl restart ssh`) is refused.

### Fix G. Make the health check and tests match (required)

Where: `setup/pinpoint-healthcheck.sh` and the installer's `tests/` folder.

Why: the earlier NCPA problem (`INSTALLER_INSTRUCTIONS_check_ncpa_shebang.md`) was missed because
the installer checked the wrong thing. Check the real behaviour here.

How: add checks that assert the owner and mode of each item above, and that the negative cases
fail:

- spool directory `nagios:pinpoint 2770`; handler `root:root 755`; `msmtprc` group is
  `pinpoint-mail`.
- `www-data` cannot read `msmtprc`, cannot write `nagios.cmd`, cannot list the spool.
- `nagios` can run the handler and append to the spool; `pinpoint` can read and remove a line.

## 3. Order and risk

1. Fix A, then B: they only remove access. Test alerts and the Nagios web pages after each.
2. Fix C and D together, with Fix E checked. Nothing uses them until issue #120 ships.
3. Fix F last, only with issue #121.
4. Every fix must be safe to run twice and must work on an appliance that is already installed
   (upgrade), not only on a fresh one.

If any step makes alert email stop or the Nagios web pages fail, undo that step and report it
before going on. Do not widen a permission to make a check pass.

## 4. Why PinPoint itself does not change these

PinPoint runs as the unprivileged `pinpoint` user and cannot change ownership or sudo rules, by
design. These are root-level, one-time setup changes, so they belong to the installer.
