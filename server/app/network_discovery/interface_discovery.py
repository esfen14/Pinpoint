"""
Interface discovery: ask a device over SNMP which network interfaces it has.

Mechanism: the net-snmp `snmpwalk` command, run with an argument list (never a shell) and
a hard timeout. check_snmp, which Nagios already uses for every SNMP service, needs the same
net-snmp tools installed, so no new dependency is added to the server. Rejected alternatives:
a Python SNMP library (a new, large dependency for one walk) and check_ifstatus (it reports
the state of the interfaces, not their names, speeds and indexes).

Each IF-MIB column is walked once: ifDescr, ifName, ifSpeed, ifHighSpeed, ifAdminStatus and
ifOperStatus. The interface list is then stored per device (DeviceInterface), keeping the
administrator's Monitored choice across refreshes.

Security: the address comes from the database and is checked as an IP address, the port as
1-65535, and the community is passed as one argv item after -c, so none of them can reach a
shell. The community appears in the process list for the length of the walk, exactly as it does
for check_snmp. Error messages and logs never contain the community or the command line.
"""
import ipaddress
import re
import subprocess
import time
from datetime import datetime, timezone

import sqlalchemy as sa
from flask import current_app

from app import db
from app.network_discovery.plugin_registry import (
    PluginConfigurationError,
    resolve_plugin_variables,
    validate_variable_value,
)
from app.network_discovery.plugin_settings import plugin_config
from app.system_models import DeviceInterface, DeviceState, NetworkDiscovery, Open_UDP_Services, PortState

SNMPWALK = "snmpwalk"

# IF-MIB / IF-MIB::ifXTable columns.
COLUMNS = {
    "descr": "1.3.6.1.2.1.2.2.1.2",
    "speed": "1.3.6.1.2.1.2.2.1.5",
    "admin": "1.3.6.1.2.1.2.2.1.7",
    "oper": "1.3.6.1.2.1.2.2.1.8",
    "name": "1.3.6.1.2.1.31.1.1.1.1",
    "high_speed": "1.3.6.1.2.1.31.1.1.1.15",
}

# Limits that keep one refresh, and one scan, bounded.
WALK_TIMEOUT_SECONDS = 20
SNMP_TIMEOUT_SECONDS = 2
SNMP_RETRIES = 1
MAX_INTERFACES = 512
SCAN_DEVICE_LIMIT = 64
SCAN_TIME_BUDGET_SECONDS = 120

# Ports that are checked with the SNMP plugin; older rows have no frozen plugin name yet.
SNMP_PORT_FILTER = sa.or_(Open_UDP_Services.Plugin_Name == "snmp", Open_UDP_Services.Service_Name == "snmp")

STATUS_NAMES = {1: "up", 2: "down", 3: "testing", 4: "unknown", 5: "dormant", 6: "notPresent", 7: "lowerLayerDown"}

# "<oid> = <TYPE>: <value>" as printed by `snmpwalk -On`.
LINE_PATTERN = re.compile(r"^\.?(\d+(?:\.\d+)*) = (?:([A-Za-z0-9-]+): ?)?(.*)$")
NUMBER_PATTERN = re.compile(r"(\d+)")


class InterfaceDiscoveryError(Exception):
    """The interface list could not be read. The message is safe to show to a user."""


def parse_walk(output, column_oid):
    """
    Return {ifIndex: value} for the lines of `snmpwalk -On` output that belong to column_oid.
    Values are text with surrounding quotes removed; "INTEGER: up(1)" gives "up(1)". Lines of
    other columns, "No Such Instance" lines and anything unreadable are skipped.
    """
    prefix = column_oid + "."
    values = {}
    for line in output.splitlines():
        match = LINE_PATTERN.match(line.strip())
        if not match or not match.group(1).startswith(prefix):
            continue
        index = match.group(1)[len(prefix):]
        if not index.isdigit() or match.group(2) is None:
            continue
        values[int(index)] = match.group(3).strip().strip('"')
    return values


def as_number(text):
    """The first whole number in text ("up(1)" -> 1, "1000000000" -> 1000000000), or None."""
    match = NUMBER_PATTERN.search(text or "")
    return int(match.group(1)) if match else None


def speed_bps(speed, high_speed):
    """
    The interface speed in bit/s, or None when the device does not report one. ifHighSpeed (Mbit/s)
    is preferred because ifSpeed is capped at 4.29 Gbit/s; 0 means unknown.
    """
    mbit = as_number(high_speed)
    if mbit:
        return mbit * 1_000_000
    bits = as_number(speed)
    return bits if bits else None


def status_name(text):
    """The interface status as a word ("up", "down", ...), from "up(1)" or "1"; None when unreadable."""
    number = as_number(text)
    if number is None:
        return None
    return STATUS_NAMES.get(number, str(text)[:20])


def run_walk(address, port, community, column_oid):
    """
    Run snmpwalk for one column and return its output. Raises InterfaceDiscoveryError, without
    the community or command line in the message, when the tool is missing, the walk times out or
    the device does not answer.
    """
    command = [
        SNMPWALK, "-v2c", "-c", community, "-On",
        "-t", str(SNMP_TIMEOUT_SECONDS), "-r", str(SNMP_RETRIES),
        f"udp:{address}:{port}", column_oid,
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=WALK_TIMEOUT_SECONDS, check=False,
        )
    except FileNotFoundError:
        raise InterfaceDiscoveryError("The snmpwalk tool is not installed on the server (install net-snmp-utils / snmp).")
    except subprocess.TimeoutExpired:
        raise InterfaceDiscoveryError("The device did not answer in time.")
    except OSError:
        raise InterfaceDiscoveryError("The SNMP query could not be started.")
    if result.returncode != 0:
        raise InterfaceDiscoveryError("The device did not answer the SNMP query. Check that SNMP is enabled and the community is right.")
    return result.stdout


def walk_interfaces(address, port, community):
    """
    Read a device's interface list over SNMP: [{"if_index", "name", "speed_bps", "admin_status",
    "oper_status"}], sorted by index and capped at MAX_INTERFACES. Raises InterfaceDiscoveryError
    when the device cannot be read or reports no interfaces.
    """
    try:
        ipaddress.ip_address(address)
        validate_variable_value("port", port)
        validate_variable_value("community", community)
    except (ValueError, PluginConfigurationError):
        raise InterfaceDiscoveryError("This device has no usable SNMP address, port or community.")
    if str(community).startswith("-") or not str(community):
        raise InterfaceDiscoveryError("This device has no usable SNMP address, port or community.")

    columns = {key: parse_walk(run_walk(address, int(port), str(community), oid), oid) for key, oid in COLUMNS.items()}

    indexes = sorted(set(columns["descr"]) | set(columns["name"]))[:MAX_INTERFACES]
    if not indexes:
        raise InterfaceDiscoveryError("The device reported no network interfaces.")

    interfaces = []
    for index in indexes:
        name = columns["name"].get(index) or columns["descr"].get(index) or f"Interface {index}"
        interfaces.append({
            "if_index": index,
            "name": name[:100],
            "speed_bps": speed_bps(columns["speed"].get(index), columns["high_speed"].get(index)),
            "admin_status": status_name(columns["admin"].get(index)),
            "oper_status": status_name(columns["oper"].get(index)),
        })
    return interfaces


def device_snmp_settings(device):
    """
    Return (port, community) the device is polled with: the app defaults, the SNMP port found on the
    device and the device's own overrides, resolved like the Nagios checks. Raises
    InterfaceDiscoveryError if the device has no SNMP port to ask.
    """
    udp_ports = db.session.scalars(
        sa.select(Open_UDP_Services).where(
            Open_UDP_Services.NetDiscoveryID == device.NetDiscoveryID,
            SNMP_PORT_FILTER,
            Open_UDP_Services.Port_State.in_((PortState.MONITORED, PortState.MISSING)),
        ).order_by(Open_UDP_Services.Port_Number)
    ).all()
    if not udp_ports:
        raise InterfaceDiscoveryError("SNMP is not monitored on this device.")

    overrides = (device.Plugin_Variables or {}).get("snmp") if isinstance(device.Plugin_Variables, dict) else None
    try:
        variables = resolve_plugin_variables(
            "snmp", plugin_config(), discovered={"port": udp_ports[0].Port_Number}, overrides=overrides,
        )
    except PluginConfigurationError:
        raise InterfaceDiscoveryError("This device has no usable SNMP settings.")
    return variables.get("port"), variables.get("community")


def store_interfaces(device, interfaces, now=None):
    """
    Save a fresh interface list for the device: new interfaces are added, known ones updated (the
    Monitored choice is kept), and ones no longer reported are removed unless they are monitored,
    which are kept and marked not present. Does not commit. Returns the DeviceInterface rows.
    """
    now = now or datetime.now(timezone.utc)
    existing = {
        row.If_Index: row
        for row in db.session.scalars(
            sa.select(DeviceInterface).where(DeviceInterface.NetDiscoveryID == device.NetDiscoveryID)
        ).all()
    }

    seen = set()
    for interface in interfaces:
        seen.add(interface["if_index"])
        row = existing.get(interface["if_index"])
        if row is None:
            row = DeviceInterface(NetDiscoveryID=device.NetDiscoveryID, If_Index=interface["if_index"], Monitored=False)
            db.session.add(row)
        row.Name = interface["name"]
        row.Speed_Bps = interface["speed_bps"]
        row.Admin_Status = interface["admin_status"]
        row.Oper_Status = interface["oper_status"]
        row.Present = True
        row.Last_Seen_At = now

    for index, row in existing.items():
        if index in seen:
            continue
        if row.Monitored:
            row.Present = False
        else:
            db.session.delete(row)
    db.session.flush()

    return db.session.scalars(
        sa.select(DeviceInterface).where(DeviceInterface.NetDiscoveryID == device.NetDiscoveryID)
        .order_by(DeviceInterface.If_Index)
    ).all()


def refresh_device_interfaces(device):
    """
    Read the device's interfaces over SNMP and store them (store_interfaces), committing on
    success and rolling back on failure. Returns the DeviceInterface rows. Raises
    InterfaceDiscoveryError, with a message safe to show, if the device cannot be read.
    """
    port, community = device_snmp_settings(device)
    interfaces = walk_interfaces(device.IP_Address, port, community)
    try:
        rows = store_interfaces(device, interfaces)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not save the interfaces of a device.")
        raise InterfaceDiscoveryError("The interfaces were read but could not be saved.")
    return rows


def refresh_interfaces_after_scan():
    """
    Refresh the interface list of devices that already have one, or that expose SNMP, after a scan.
    Best effort and bounded: at most SCAN_DEVICE_LIMIT devices and SCAN_TIME_BUDGET_SECONDS in total;
    a device that does not answer is logged (without its community) and skipped. Returns the number
    of devices refreshed.
    """
    started = time.monotonic()
    refreshed = 0
    devices = db.session.scalars(
        sa.select(NetworkDiscovery)
        .where(
            NetworkDiscovery.Include_Device_In_Scanning.is_(True),
            NetworkDiscovery.Device_State == DeviceState.ACTIVE,
            NetworkDiscovery.NetDiscoveryID.in_(
                sa.select(Open_UDP_Services.NetDiscoveryID).where(
                    SNMP_PORT_FILTER,
                    Open_UDP_Services.Port_State.in_((PortState.MONITORED, PortState.MISSING)),
                )
            ),
        )
        .order_by(NetworkDiscovery.NetDiscoveryID)
        .limit(SCAN_DEVICE_LIMIT)
    ).all()

    for device in devices:
        if time.monotonic() - started > SCAN_TIME_BUDGET_SECONDS:
            current_app.logger.warning("Interface refresh after the scan stopped early: time budget used.")
            break
        try:
            refresh_device_interfaces(device)
            refreshed += 1
        except InterfaceDiscoveryError as e:
            current_app.logger.info(f"Interfaces of device {device.NetDiscoveryID} not refreshed: {e}")
    return refreshed

