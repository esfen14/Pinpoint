"""
Device interfaces API: the network interfaces an SNMP device reports, and which of them are
monitored for bandwidth (Device Inventory drawer).

Reading needs ``system.hosts``; refreshing the list over SNMP and choosing which interfaces are
monitored need ``system.hosts.edit``. Choosing an interface changes the generated Nagios config
(an in and an out octet service per interface), so the change is saved, written to the activity
log and then applied through the shared config pipeline, which validates it with the Nagios
binary and rolls it back if rejected. The bandwidth shown on Network Health is computed from the
samples those services collect (see app/bandwidth.py).

Routes
------
GET  /system/hosts/<id>/interfaces
    The stored interface list of a device.

POST /system/hosts/<id>/interfaces/refresh
    Read the interface list from the device over SNMP and store it.

PUT  /system/hosts/<id>/interfaces/<if_index>
    Turn bandwidth monitoring of one interface on or off.
"""

import sqlalchemy as sa
from flask import current_app, request
from flask_login import current_user, login_required

from app import db
from app.api.helper import error, success, validate_json_data
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.api.system.device_identity import apply_config_change, get_device_or_404
from app.logging.user_activity import create_user_log
from app.network_discovery.device_identity import nagios_host_name
from app.network_discovery.interface_discovery import (
    InterfaceDiscoveryError,
    SNMP_PORT_FILTER,
    refresh_device_interfaces,
)
from app.network_discovery.plugin_registry import MAX_MONITORED_INTERFACES
from app.system_models import DeviceInterface, Open_UDP_Services, PortState


# ==========================================================
# HELPERS
# ==========================================================

def serialize_interface(row):
    """One DeviceInterface as the drawer shows it."""
    return {
        "if_index": row.If_Index,
        "name": row.Name,
        "speed_bps": row.Speed_Bps,
        "admin_status": row.Admin_Status,
        "oper_status": row.Oper_Status,
        "monitored": bool(row.Monitored),
        "present": bool(row.Present),
        "last_seen_at": row.Last_Seen_At.isoformat() if row.Last_Seen_At else None,
    }


def interface_rows(device_id):
    """A device's stored interfaces, ordered by interface index."""
    return db.session.scalars(
        sa.select(DeviceInterface).where(DeviceInterface.NetDiscoveryID == device_id)
        .order_by(DeviceInterface.If_Index)
    ).all()


def has_snmp(device_id):
    """True if SNMP is a monitored (or missing) port of the device, so its interfaces can be read."""
    return db.session.scalar(
        sa.select(Open_UDP_Services.NetDiscoveryID).where(
            Open_UDP_Services.NetDiscoveryID == device_id,
            SNMP_PORT_FILTER,
            Open_UDP_Services.Port_State.in_((PortState.MONITORED, PortState.MISSING)),
        ).limit(1)
    ) is not None


def interfaces_payload(device, rows):
    """The response body shared by the three routes."""
    return {
        "device": {"id": device.NetDiscoveryID, "nagios_host_name": nagios_host_name(device)},
        "snmp": has_snmp(device.NetDiscoveryID),
        "max_monitored": MAX_MONITORED_INTERFACES,
        "interfaces": [serialize_interface(row) for row in rows],
    }


# ==========================================================
# INTERFACES
# ==========================================================

@system_bp.get('/hosts/<int:id>/interfaces')
@login_required
@require_permission('system.hosts')
def get_device_interfaces(id):
    """
    Return the interfaces stored for a device (see the refresh route to read them from the device).

    Response
    {
        "device": {"id", "nagios_host_name"},
        "snmp": bool,                 // SNMP is monitored on the device, so a refresh can work
        "max_monitored": int,
        "interfaces": [{"if_index", "name", "speed_bps": int | null, "admin_status", "oper_status",
                        "monitored", "present", "last_seen_at"}]
    }
    """
    device, err = get_device_or_404(id)
    if err is not None:
        return err

    try:
        return success(interfaces_payload(device, interface_rows(id)))
    except Exception:
        current_app.logger.exception("An unexpected error occurred while listing a device's interfaces.")
        return error("An unexpected error occurred.", 500)


@system_bp.post('/hosts/<int:id>/interfaces/refresh')
@login_required
@require_permission('system.hosts.edit')
def refresh_interfaces(id):
    """
    Read the device's interface list over SNMP and store it. New interfaces are added (not
    monitored), known ones updated with the monitoring choice kept, and ones the device no longer
    reports are removed unless they are monitored. No body. Responds 502 with a plain-language
    reason when the device cannot be read, and 400 when SNMP is not monitored on the device.
    Same response as the list route.
    """
    device, err = get_device_or_404(id)
    if err is not None:
        return err
    if not has_snmp(id):
        return error("SNMP is not monitored on this device.", 400)

    try:
        rows = refresh_device_interfaces(device)
    except InterfaceDiscoveryError as e:
        return error(str(e), 502)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("An unexpected error occurred while refreshing a device's interfaces.")
        return error("An unexpected error occurred.", 500)

    create_user_log(current_user.UserID, f"Refreshed the interfaces of {nagios_host_name(device)}")
    db.session.commit()
    return success(interfaces_payload(device, rows), message="Interfaces refreshed.")


@system_bp.put('/hosts/<int:id>/interfaces/<int:if_index>')
@login_required
@require_permission('system.hosts.edit')
def edit_device_interface(id, if_index):
    """
    Turn bandwidth monitoring of one interface on or off. Monitoring adds an in and an out octet
    service to the device's SNMP checks; at most max_monitored interfaces per device. The Nagios
    config is regenerated and applied; the change is kept even if Nagios could not be updated, and
    the response says so ("config_ok": false).

    JSON Format
    {
        "monitored": true
    }

    Response: the list route's body plus "config_applied", "config_ok" and "config_message".
    """
    data = request.get_json()
    err = validate_json_data(data)
    if err is not None:
        return err
    monitored = data.get("monitored")
    if not isinstance(monitored, bool):
        return error("monitored must be true or false.", 400)

    device, err = get_device_or_404(id)
    if err is not None:
        return err

    row = db.session.scalar(
        sa.select(DeviceInterface).where(DeviceInterface.NetDiscoveryID == id, DeviceInterface.If_Index == if_index)
    )
    if row is None:
        return error("Device has no such interface. Refresh the interface list first.", 404)
    if monitored and not has_snmp(id):
        return error("SNMP is not monitored on this device.", 400)
    if monitored and not row.Present:
        return error("The device no longer reports this interface.", 400)

    if monitored and not row.Monitored:
        count = len([r for r in interface_rows(id) if r.Monitored])
        if count >= MAX_MONITORED_INTERFACES:
            return error(f"At most {MAX_MONITORED_INTERFACES} interfaces can be monitored on one device.", 400)

    if row.Monitored != monitored:
        row.Monitored = monitored
        verb = "Started" if monitored else "Stopped"
        create_user_log(current_user.UserID, f"{verb} monitoring interface {row.Name} on {nagios_host_name(device)}")
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Could not save an interface monitoring change.")
            return error("The change could not be saved.", 500)
        result = apply_config_change()
    else:
        result = {"config_applied": False, "config_ok": True, "config_message": "Nothing changed."}

    result.update(interfaces_payload(device, interface_rows(id)))
    return success(result, message="Interface updated.")
