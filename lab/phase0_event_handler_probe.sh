#!/usr/bin/env bash
# Phase 0 lab checks for the proactive-resolution work (Issues #7, #8, #22).
# See docs/plans/Proactive_Resolution_Implementation_Plan.md, sections 3.2 and 5.1.
#
# Runs ON the appliance, normally through:  scripts/vmlab phase0 [--with-notification]
# It changes nothing that outlives it: the trial directories are removed on exit.
#
#   --with-notification   also write ONE SEND_CUSTOM_SVC_NOTIFICATION line to the Nagios
#                         command file. This can send a real email if contacts are set up,
#                         so it is off by default.
#
# Needs the "lab" user to have passwordless sudo. Exit status is 1 if any check FAILs.
set -uo pipefail

NAGIOS=/usr/local/nagios
CFG=$NAGIOS/etc/nagios.cfg
APP_ROOT=/opt/pinpoint
APP_DIR=$APP_ROOT/Network-Diagnosis-System
SPOOL_PARENT=$NAGIOS/var/spool
TRIAL=$SPOOL_PARENT/.pinpoint-phase0-$$
with_notification=0
password_stdin=0
for arg in "$@"; do
  case "$arg" in
    --with-notification) with_notification=1 ;;
    --sudo-password-stdin) password_stdin=1 ;;
  esac
done

pass=0; fail=0; info=0
say()  { printf '%s\n' "$*"; }
head_() { printf '\n== %s\n' "$*"; }
PASS() { pass=$((pass + 1)); printf 'PASS  %s\n' "$*"; }
FAIL() { fail=$((fail + 1)); printf 'FAIL  %s\n' "$*"; }
INFO() { info=$((info + 1)); printf 'INFO  %s\n' "$*"; }

cleanup() { sudo rm -rf "$TRIAL" "$TRIAL-open" 2>/dev/null; }
trap cleanup EXIT

# --sudo-password-stdin: the first line of stdin is the sudo password, for hosts without
# passwordless sudo. It is held in a shell variable only and is never printed or written to disk.
if [ "$password_stdin" = 1 ]; then
  IFS= read -r PROBE_SUDO_PW
  sudo() { if [ "${1:-}" = "-n" ]; then shift; fi; command sudo -S -p '' "$@" <<<"$PROBE_SUDO_PW"; }
  sudo true 2>/dev/null || { say "The sudo password was not accepted."; exit 2; }
else
  sudo -n true 2>/dev/null || { say "This probe needs passwordless sudo, or --sudo-password-stdin."; exit 2; }
fi

head_ "Context"
say "date:     $(date -u +%FT%TZ)"
say "host:     $(hostname)"
say "os:       $(. /etc/os-release && echo "$PRETTY_NAME")"
say "commit:   $(sudo -u pinpoint git -C "$APP_DIR" rev-parse --short HEAD 2>/dev/null || echo 'app not installed')"
say "stamp:    $(cat /etc/pinpoint-vmlab-stamp 2>/dev/null || echo none)"

# ---------------------------------------------------------------- users and groups
head_ "1. Users and groups (plan 5.1 #1)"
for u in nagios pinpoint www-data; do say "id $u: $(id "$u" 2>&1)"; done
getent group pinpoint >/dev/null && PASS "group 'pinpoint' exists" || FAIL "group 'pinpoint' does not exist (spool group design needs it)"
id -nG pinpoint 2>/dev/null | tr ' ' '\n' | grep -qx nagios \
  && PASS "pinpoint is in group nagios" || FAIL "pinpoint is not in group nagios"
id -nG www-data 2>/dev/null | tr ' ' '\n' | grep -qx nagios \
  && INFO "www-data IS in group nagios (confirms the installer finding: a nagios-group spool is web-writable)" \
  || INFO "www-data is not in group nagios"

# ---------------------------------------------------------------- ownership and modes
head_ "2. Owners and modes (plan 3.2 #1, 5.1 #5)"
for p in $NAGIOS $NAGIOS/etc $NAGIOS/libexec $NAGIOS/var $NAGIOS/var/rw $NAGIOS/var/spool \
         $NAGIOS/var/rw/nagios.cmd /usr/local/sbin /usr/local/sbin/pinpoint-apply-smtp \
         $APP_ROOT $APP_DIR $APP_DIR/.venv; do
  if [ -e "$p" ]; then say "$(stat -c '%U:%G %a  %n' "$p")"; else say "missing   $p"; fi
done
[ -p $NAGIOS/var/rw/nagios.cmd ] && PASS "command file is a pipe" || FAIL "command file is not a pipe"
[ "$(stat -c %a /usr/local/sbin/pinpoint-apply-smtp 2>/dev/null)" = 755 ] \
  && [ "$(stat -c %U:%G /usr/local/sbin/pinpoint-apply-smtp 2>/dev/null)" = root:root ] \
  && PASS "SMTP helper is root:root 755 (pattern for the handler)" || INFO "SMTP helper not root:root 755 (is the app installed?)"

# ---------------------------------------------------------------- reachability
head_ "3. Can nagios run a root-owned file, and reach the app? (plan 3.2 #2)"
sudo -u nagios test -x /usr/local/sbin/pinpoint-apply-smtp \
  && PASS "nagios can execute a root-owned 755 file in /usr/local/sbin" \
  || FAIL "nagios cannot execute a root-owned 755 file in /usr/local/sbin"
if sudo -u nagios test -x "$APP_DIR"; then
  INFO "nagios CAN traverse $APP_DIR (the handler still must not depend on it)"
else
  INFO "nagios cannot traverse $APP_DIR (matches the original concern; handler must not depend on it)"
fi

# ---------------------------------------------------------------- nagios.cfg
head_ "4. nagios.cfg settings (plan 3.2 #3, 5.1 #7)"
for k in enable_event_handlers log_event_handlers event_handler_timeout check_external_commands command_file \
         enable_notifications interval_length; do
  v="$(sudo grep -E "^[[:space:]]*$k[[:space:]]*=" "$CFG" | tail -n1)"
  if [ -n "$v" ]; then say "$v"; else say "# $k: not set (Nagios default applies)"; fi
done
sudo grep -E "^[[:space:]]*enable_event_handlers[[:space:]]*=[[:space:]]*1" "$CFG" >/dev/null \
  && PASS "enable_event_handlers=1" || INFO "enable_event_handlers is not explicitly 1 (installer must set it; Issue #7 Part 7.3)"
sudo grep -E "^[[:space:]]*check_external_commands[[:space:]]*=[[:space:]]*1" "$CFG" >/dev/null \
  && PASS "check_external_commands=1" || FAIL "check_external_commands is not 1 (Issues #19 and #22 need it)"
say "nagios.cfg sha256: $(sudo sha256sum "$CFG" | cut -d' ' -f1)   (compare before and after re-running the installer, plan 5.1 #4)"
sudo "$NAGIOS/bin/nagios" -v "$CFG" >/dev/null 2>&1 && PASS "nagios -v accepts the current config" || FAIL "nagios -v rejects the current config"

# ---------------------------------------------------------------- spool trial
head_ "5. Spool directory trial (plan 3.2 #1, 5.1 #1)"
if [ -d "$SPOOL_PARENT" ] && getent group pinpoint >/dev/null; then
  # Proposed design: owner nagios, group pinpoint, 2770.
  sudo install -d -o nagios -g pinpoint -m 2770 "$TRIAL"
  say "proposed:    $(stat -c '%U:%G %a' "$TRIAL")"
  sudo -u nagios sh -c "printf '{\"probe\":1}\n' > '$TRIAL/event-1.json'" 2>/dev/null \
    && PASS "nagios can write a spool file" || FAIL "nagios cannot write a spool file"
  [ "$(sudo stat -c %G "$TRIAL/event-1.json" 2>/dev/null)" = pinpoint ] \
    && PASS "new files inherit group pinpoint (setgid works)" || FAIL "new files do not inherit group pinpoint"
  sudo -u pinpoint cat "$TRIAL/event-1.json" >/dev/null 2>&1 \
    && PASS "pinpoint can read a spool file" || FAIL "pinpoint cannot read a spool file"
  sudo -u pinpoint rm -f "$TRIAL/event-1.json" 2>/dev/null; [ ! -e "$TRIAL/event-1.json" ] \
    && PASS "pinpoint can delete a spool file" || FAIL "pinpoint cannot delete a spool file"
  sudo -u www-data ls "$TRIAL" >/dev/null 2>&1 \
    && FAIL "www-data can list the proposed spool" || PASS "www-data cannot list the proposed spool"
  sudo -u www-data sh -c "printf x > '$TRIAL/web.json'" 2>/dev/null \
    && FAIL "www-data can write to the proposed spool" || PASS "www-data cannot write to the proposed spool"

  # Rejected design: group nagios. Shows whether the web user could write to it.
  sudo install -d -o nagios -g nagios -m 2770 "$TRIAL-open"
  if sudo -u www-data sh -c "printf x > '$TRIAL-open/web.json'" 2>/dev/null; then
    INFO "with group nagios, www-data CAN write to the spool (confirms why group pinpoint is required)"
  else
    INFO "with group nagios, www-data could not write (www-data not in nagios here)"
  fi
else
  FAIL "spool parent missing or group pinpoint missing; trial not run"
fi

# ---------------------------------------------------------------- gunicorn unit and sudo
head_ "6. pinpoint-gunicorn unit (plan 5.1 #6)"
sudo systemctl show pinpoint-gunicorn -p User -p Group -p NoNewPrivileges -p ProtectSystem -p ProtectHome -p ReadWritePaths -p PrivateTmp 2>&1
sudo systemctl show pinpoint-gunicorn -p NoNewPrivileges 2>/dev/null | grep -q '=no' \
  && PASS "NoNewPrivileges is off, so sudo can work from the service" || INFO "NoNewPrivileges is on or the unit is missing"

head_ "7. sudo rules for pinpoint (plan 5.1 #2)"
ls -l /etc/sudoers.d 2>&1
sudo -n -l -U pinpoint 2>&1
sudo -u pinpoint sudo -n systemctl restart nagios >/dev/null 2>&1 \
  && FAIL "pinpoint can restart nagios today (step 9 expects this to be refused)" \
  || PASS "pinpoint cannot restart nagios today (matches installer step 9; Issue #8 Part 8.2 will change this on purpose)"

# ---------------------------------------------------------------- AppArmor
head_ "8. AppArmor (plan 5.1 #8)"
if command -v aa-status >/dev/null; then sudo aa-status 2>&1 | head -n 12; else INFO "aa-status not installed"; fi
sudo aa-status 2>/dev/null | grep -Ei 'nagios|pinpoint|gunicorn' && INFO "a profile mentions nagios/pinpoint/gunicorn (review it)" || INFO "no profile mentions nagios, pinpoint or gunicorn"

# ---------------------------------------------------------------- custom notification
head_ "9. Custom notification through the command pipe (plan 3.2 #4, Issue #22)"
if [ "$with_notification" = 1 ]; then
  status=$NAGIOS/var/status.dat
  pair="$(sudo awk '/^servicestatus \{/{h="";s=""} /host_name=/{sub(/^[ \t]*host_name=/,"");h=$0} /service_description=/{sub(/^[ \t]*service_description=/,"");s=$0; if(h!="" && s!=""){print h "|" s; exit}}' "$status" 2>/dev/null)"
  if [ -z "$pair" ]; then
    FAIL "could not find a service in status.dat to use"
  else
    h="${pair%%|*}"; s="${pair#*|}"; ts="$(date +%s)"; marker="phase0-probe-$ts"
    say "target: $h / $s   marker: $marker"
    if sudo -u pinpoint sh -c "printf '[%s] SEND_CUSTOM_SVC_NOTIFICATION;%s;%s;0;pinpoint-lab;%s\n' '$ts' '$h' '$s' '$marker' > $NAGIOS/var/rw/nagios.cmd"; then
      PASS "pinpoint wrote the command to the pipe"
      sleep 6
      if sudo grep -q "$marker" $NAGIOS/var/nagios.log $NAGIOS/var/archives/*.log 2>/dev/null; then
        PASS "Nagios logged the custom notification (marker found in the log)"
        sudo grep "$marker" $NAGIOS/var/nagios.log 2>/dev/null | tail -n 2
      else
        INFO "marker not in the log. With options=0 Nagios suppresses it when notifications are disabled, in downtime or outside the timeperiod; that is the intended behavior, so check those first"
      fi
    else
      FAIL "pinpoint could not write to the command pipe"
    fi
  fi
else
  INFO "skipped (re-run with --with-notification to send ONE custom notification)"
fi

# ---------------------------------------------------------------- manual
head_ "Not scripted (do by hand, record the result)"
say "- Event handler timeout kills a slow handler (needs a temporary handler and config change)."
say "- Re-run the installer (scripts/vmlab fresh) and confirm the nagios.cfg sha256 and section 4 values are unchanged."

head_ "Summary"
printf 'PASS %d   FAIL %d   INFO %d\n' "$pass" "$fail" "$info"
[ "$fail" -eq 0 ]
