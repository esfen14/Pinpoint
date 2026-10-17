"""
Remote service restart (Issue #8 Part 8.3).

Two halves, both described in docs/plans/Issue_8_3_Remote_Restart_Design_Note.md:

* The device side: a root-owned helper, ``pinpoint-service-restart``, one sudoers line that
  lets the deployment account run exactly that helper, and an allowlist file only root can
  change. The helper restarts a unit only if it is on the file. Installed by the same
  bootstrap that installs the NCPA helper, with the administrator's one-time password.
* The PinPoint side: ``restart_remote_unit`` connects with the deployment key after the
  stored host-key fingerprint is checked, runs only the helper with one validated unit name,
  and returns a short fixed message. Command output and exception text are never returned.
"""
import re
import shlex
from time import monotonic, sleep

import paramiko

from app.ncpa_deployment import ncpa_deployment as deploy

REMOTE_RESTART_HELPER = "/usr/local/sbin/pinpoint-service-restart"
REMOTE_RESTART_SUDOERS = "/etc/sudoers.d/pinpoint-service-restart"
REMOTE_RESTART_ALLOWLIST_DIR = "/etc/pinpoint"
REMOTE_RESTART_ALLOWLIST = f"{REMOTE_RESTART_ALLOWLIST_DIR}/restartable-services"

# A systemd unit name without its suffix: letters, digits, and ``_ . @ -``; never a path or option.
UNIT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,62}$")
MAX_SERVICES_PER_DEVICE = 20
RESTART_COMMAND_TIMEOUT_SECONDS = 20

# Exit codes the helper uses on purpose.
EXIT_INVALID_NAME = 2
EXIT_NOT_ALLOWED = 3

HELPER_SCRIPT = r'''#!/bin/bash
set -euo pipefail

ALLOWLIST="/etc/pinpoint/restartable-services"
SYSTEMCTL="/usr/bin/systemctl"

if [ "$#" -ne 1 ]; then
    echo "Exactly one service name is required." >&2
    exit 2
fi

UNIT="$1"

if [[ ! "$UNIT" =~ ^[A-Za-z0-9][A-Za-z0-9_.@-]{0,62}$ ]]; then
    echo "Invalid service name." >&2
    exit 2
fi

# The list must be a regular file owned by root and not writable by anyone else.
if [ -L "$ALLOWLIST" ] || [ ! -f "$ALLOWLIST" ] || \
   [ "$(/usr/bin/stat -c '%U' "$ALLOWLIST")" != "root" ] || \
   [ -n "$(/usr/bin/find "$ALLOWLIST" -perm /022 2>/dev/null)" ]; then
    echo "The service list is missing or not safe." >&2
    exit 3
fi

if ! /usr/bin/grep -Fxq -- "$UNIT" "$ALLOWLIST"; then
    echo "That service is not allowed on this device." >&2
    exit 3
fi

exec "$SYSTEMCTL" restart -- "$UNIT"
'''


def valid_unit(unit):
    """True for a plain unit name that is safe to pass as one command argument."""
    return isinstance(unit, str) and UNIT_PATTERN.fullmatch(unit) is not None


def clean_services(services):
    """Return (sorted unique valid names, error text or None) for an administrator's list."""
    if services is None:
        return [], None
    if not isinstance(services, list):
        return [], "Services must be a list."
    cleaned = []
    for unit in services:
        if not valid_unit(unit):
            return [], "Each service must be a plain unit name such as nagios or apache2."
        if unit not in cleaned:
            cleaned.append(unit)
    if len(cleaned) > MAX_SERVICES_PER_DEVICE:
        return [], f"At most {MAX_SERVICES_PER_DEVICE} services can be listed."
    return sorted(cleaned), None


# ==========================================================
# DEVICE SIDE (bootstrap, runs with the administrator's one-time password)
# ==========================================================

def install_restart_helper(client, password, services):
    """
    Install the restart helper, its sudoers line and the allowlist on a device. Idempotent;
    the sudoers file is written to a temporary name, checked with visudo and only then moved.
    Returns True on success. ``services`` must already be cleaned.
    """
    allowlist_text = "".join(f"{unit}\n" for unit in services)
    sudoers_text = f"{deploy.DEPLOYMENT_USER} ALL=(root) NOPASSWD: {REMOTE_RESTART_HELPER}\n"
    tmp_helper = f"{REMOTE_RESTART_HELPER}.new"
    tmp_sudoers = f"{REMOTE_RESTART_SUDOERS}.new"
    tmp_list = f"{REMOTE_RESTART_ALLOWLIST}.new"

    script = " && ".join([
        f"[ ! -L {shlex.quote(REMOTE_RESTART_ALLOWLIST_DIR)} ]",
        f"/usr/bin/mkdir -p {shlex.quote(REMOTE_RESTART_ALLOWLIST_DIR)}",
        f"/usr/bin/chown root:root {shlex.quote(REMOTE_RESTART_ALLOWLIST_DIR)}",
        f"/usr/bin/chmod 755 {shlex.quote(REMOTE_RESTART_ALLOWLIST_DIR)}",
        f"/usr/bin/rm -f -- {shlex.quote(tmp_list)}",
        f"printf '%s' {shlex.quote(allowlist_text)} > {shlex.quote(tmp_list)}",
        f"/usr/bin/chown root:root {shlex.quote(tmp_list)}",
        f"/usr/bin/chmod 644 {shlex.quote(tmp_list)}",
        f"/bin/mv -f {shlex.quote(tmp_list)} {shlex.quote(REMOTE_RESTART_ALLOWLIST)}",
        f"printf '%s' {shlex.quote(HELPER_SCRIPT)} > {shlex.quote(tmp_helper)}",
        f"/usr/bin/chown root:root {shlex.quote(tmp_helper)}",
        f"/usr/bin/chmod 755 {shlex.quote(tmp_helper)}",
        f"/bin/mv -f {shlex.quote(tmp_helper)} {shlex.quote(REMOTE_RESTART_HELPER)}",
        f"printf '%s' {shlex.quote(sudoers_text)} > {shlex.quote(tmp_sudoers)}",
        f"/usr/bin/chmod 440 {shlex.quote(tmp_sudoers)}",
        f"/usr/sbin/visudo -cf {shlex.quote(tmp_sudoers)}",
        f"/bin/mv -f {shlex.quote(tmp_sudoers)} {shlex.quote(REMOTE_RESTART_SUDOERS)}",
    ])
    result = deploy.run_sudo_command(
        client, f"/bin/sh -c {shlex.quote(script)}", password, log_command="install restart helper", suppress_output=True)
    return result["success"]


# ==========================================================
# PINPOINT SIDE (runs with the deployment key)
# ==========================================================

def restart_remote_unit(ip_address, ssh_port, fingerprint, unit):
    """
    Restart one unit on a trusted device. Returns (outcome, message) where outcome is
    "succeeded", "failed", "timed_out" or "host_key_changed". Must run inside an app context
    (the SSH helpers log through current_app). The message is fixed text, never device output.
    """
    if not valid_unit(unit):
        return "failed", "Refused: that is not a valid service name."
    host_key = deploy.check_host_key(ip_address, ssh_port, fingerprint)
    if host_key == "unreachable":
        return "failed", "Device unreachable."
    if host_key == "mismatch":
        return "host_key_changed", deploy.HOST_KEY_CHANGED_MESSAGE
    client = None
    try:
        client = deploy.connect_with_fingerprint_check(
            ip_address, ssh_port, deploy.DEPLOYMENT_USER, fingerprint,
            private_key=deploy.PRIVATE_KEY_PATH)
        if client is None:
            return "failed", "Device unreachable."
        command = f"sudo -n {REMOTE_RESTART_HELPER} {shlex.quote(unit)}"
        _stdin, stdout, _stderr = client.exec_command(
            command, get_pty=False, timeout=RESTART_COMMAND_TIMEOUT_SECONDS)
        stdout.channel.settimeout(RESTART_COMMAND_TIMEOUT_SECONDS)
        # Paramiko's recv_exit_status waits on an event; channel.settimeout does
        # not bound that wait. Poll against a deadline and discard output so a
        # full SSH window cannot keep the remote process stuck.
        deadline = monotonic() + RESTART_COMMAND_TIMEOUT_SECONDS
        while not stdout.channel.exit_status_ready():
            if monotonic() >= deadline:
                raise TimeoutError()
            if stdout.channel.recv_ready():
                stdout.channel.recv(32768)
            if stdout.channel.recv_stderr_ready():
                stdout.channel.recv_stderr(32768)
            sleep(0.05)
        status = stdout.channel.recv_exit_status()
    except paramiko.BadHostKeyException:
        return "host_key_changed", deploy.HOST_KEY_CHANGED_MESSAGE
    except paramiko.AuthenticationException:
        return "failed", "The device refused the deployment key."
    except (TimeoutError, OSError, paramiko.SSHException) as error:
        if isinstance(error, TimeoutError) or "timed out" in str(error).lower():
            return "timed_out", f"Restarting {unit} did not finish in time."
        return "failed", "Could not run the restart on the device."
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
    if status == 0:
        return "succeeded", f"Restarted {unit}; exit code 0."
    if status == EXIT_NOT_ALLOWED:
        return "failed", f"Refused by the device: {unit} is not on its service list."
    if status == EXIT_INVALID_NAME:
        return "failed", "Refused by the device: invalid service name."
    return "failed", f"Restart of {unit} failed with exit code {status}."
