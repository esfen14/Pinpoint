# Runs as root inside the lab appliance (`scripts/vmlab provision` and `fresh`).
#
# The lab snapshot ages, so Ubuntu's daily upgrade is overdue after every restore, starts
# on its own a few minutes after boot and holds the package lock while the installer needs
# it (#350). Stop new runs, then wait for one that has already started. It is never
# stopped or killed: interrupting dpkg would leave a broken appliance. Lab only.
set -eu

apt_conf_dir="${VMLAB_APT_CONF_DIR:-/etc/apt/apt.conf.d}"
limit="${VMLAB_UPGRADE_WAIT_SECONDS:-3600}"

command -v fuser >/dev/null || { echo "fuser (package psmisc) is missing; cannot check the package locks" >&2; exit 1; }

systemctl disable --now apt-daily.timer apt-daily-upgrade.timer
# Also makes a run that is already queued exit without doing anything.
printf 'APT::Periodic::Enable "0";\n' > "$apt_conf_dir/99-vmlab-no-auto-upgrades"

upgrade_running() {
  if fuser /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock >/dev/null 2>&1; then
    return 0
  fi
  # A oneshot service is "activating" while it runs, also between two lock holders.
  states="$(systemctl is-active apt-daily.service apt-daily-upgrade.service || true)"
  printf '%s\n' "$states" | grep -qE '^(active|activating|reloading|deactivating)$'
}

waited=0
while upgrade_running; do
  if [ "$waited" -ge "$limit" ]; then
    echo "an automatic upgrade is still running after $limit seconds; let it finish, then run the command again" >&2
    exit 1
  fi
  if [ $((waited % 60)) -eq 0 ]; then
    echo "waiting for a running automatic upgrade to finish (${waited}s so far) ..."
  fi
  sleep 10
  waited=$((waited + 10))
done
echo "automatic upgrades are off on this lab appliance and the package locks are free"
