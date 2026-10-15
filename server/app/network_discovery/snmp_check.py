"""
One-off SNMP query for the Device Inventory "Test" button: asks a device for its uptime with
check_snmp, using the version and credentials an administrator is editing, and reports whether
it answered. Nothing is saved and Nagios is not touched.

SNMP v3 passphrases are handed to check_snmp on stdin as extra-options (the same transport the
monitored checks use), so they are not in this process's argument list; check_snmp does pass them
on to its snmpget helper while the query runs. Output is scrubbed of every secret before it is
returned. Messages are short and never contain a credential.
"""
import ipaddress
import subprocess
from pathlib import Path

from flask import current_app

UPTIME_OID = "1.3.6.1.2.1.1.3.0"
TEST_TIMEOUT_SECONDS = 15
CHECK_TIMEOUT_SECONDS = 5
MAX_MESSAGE_LENGTH = 200
STATES = {0: "OK", 1: "WARNING", 2: "CRITICAL"}
SECRET_KEYS = (("auth_password", "authpasswd"), ("priv_password", "privpasswd"))


def build_command(plugin, address, variables):
    """check_snmp's argument list for the uptime query. v3 passphrases are not part of it."""
    command = [str(plugin), "-H", address, "-p", str(variables.get("port") or 161), "-o", UPTIME_OID,
               "-t", str(CHECK_TIMEOUT_SECONDS)]
    protocol = str(variables.get("protocol") or "")
    if protocol:
        command += ["-P", protocol]
    if protocol == "3":
        command += ["-L", variables["security_level"], "-U", variables["v3_user"]]
        if variables.get("auth_protocol") and variables["security_level"] != "noAuthNoPriv":
            command += ["-a", variables["auth_protocol"]]
        if variables.get("priv_protocol") and variables["security_level"] == "authPriv":
            command += ["-x", variables["priv_protocol"]]
    else:
        command += ["-C", str(variables.get("community") or "public")]
    return command


def extra_options(variables, secrets):
    """The stdin text carrying the v3 passphrases the security level needs, or None."""
    if str(variables.get("protocol") or "") != "3":
        return None
    level = variables.get("security_level")
    wanted = {"noAuthNoPriv": (), "authNoPriv": ("auth_password",), "authPriv": ("auth_password", "priv_password")}[level]
    lines = [f"{key}={secrets[name]}\n" for name, key in SECRET_KEYS if name in wanted and secrets.get(name)]
    return "[pinpoint]\n" + "".join(lines) if lines else None


def scrub(text, hidden):
    """text with every non-empty value in hidden replaced by '***'."""
    for value in sorted((v for v in hidden if v), key=len, reverse=True):
        text = text.replace(str(value), "***")
    return text


def run_snmp_test(address, variables, secrets):
    """
    Query the device and return {"ok": bool, "state": "OK"|"WARNING"|"CRITICAL"|"UNKNOWN",
    "message": str}. variables are the resolved SNMP settings (port, protocol, community or the
    v3 fields); secrets the plaintext v3 passphrases. Never raises for an unreachable device or a
    missing plugin: those are failed results.
    """
    try:
        ipaddress.ip_address(address)
    except ValueError:
        return {"ok": False, "state": "UNKNOWN", "message": "This device has no usable address."}
    plugin = Path(current_app.config.get("NAGIOS_PLUGIN_DIR") or "/usr/local/nagios/libexec/") / "check_snmp"
    command = build_command(plugin, address, variables)
    stdin_text = extra_options(variables, secrets)
    kwargs = {"input": stdin_text} if stdin_text else {"stdin": subprocess.DEVNULL}
    if stdin_text:
        command.append("--extra-opts=pinpoint@-")
    hidden = [*secrets.values(), variables.get("community")]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TEST_TIMEOUT_SECONDS,
                                check=False, **kwargs)
    except FileNotFoundError:
        return {"ok": False, "state": "UNKNOWN", "message": "check_snmp is not installed on the server."}
    except subprocess.TimeoutExpired:
        return {"ok": False, "state": "CRITICAL", "message": "The device did not answer in time."}
    except OSError:
        return {"ok": False, "state": "UNKNOWN", "message": "The SNMP query could not be started."}
    state = STATES.get(result.returncode, "UNKNOWN")
    lines = (result.stdout or result.stderr or "").strip().splitlines()
    message = scrub(lines[0] if lines else "No answer from check_snmp.", hidden)[:MAX_MESSAGE_LENGTH]
    return {"ok": state == "OK", "state": state, "message": message}
