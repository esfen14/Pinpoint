"""Maintenance windows: planned work that PinPoint turns into Nagios scheduled downtime.

Not PinPoint's own Maintenance Mode (a System setting that only pauses PinPoint's background
jobs). A window silences alerts and notifications for a device, or for every device, while the
work is done. app/maintenance.py sends the downtime to Nagios shortly before each occurrence.
All routes require "maintenance.manage" and every change is written to the activity log.

Routes
------
GET  /system/maintenance/windows
    List windows (newest first) with next occurrence and recent occurrences, including
    failures and their reason, and the monitored devices a window can be scoped to.
POST /system/maintenance/windows
    Create a window. Body: deviceId (null = all devices), startAt, endAt (ISO 8601 with
    offset), recurrence (none|daily|weekly), recurrenceUntil, timeZone (IANA), comment.
PUT  /system/maintenance/windows/<id>
    Replace an active window. Downtime already handed to Nagios for it is deleted first.
POST /system/maintenance/windows/<id>/cancel
    Cancel a window and delete its pending and running Nagios downtime.
"""
import sqlalchemy as sa
from flask import request
from flask_login import current_user, login_required

from app import db, maintenance
from app.api.helper import error, success
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.logging.user_activity import create_user_log
from app.nagios.commands import sync_fields
from app.network_discovery.device_identity import monitoring_state, nagios_host_name
from app.system_models import MaintenanceWindow, NetworkDiscovery, User

PERMISSION = "maintenance.manage"
MAX_LISTED = 200
RECENT_OCCURRENCES = 5


def serialize_window(window, now):
    """The public shape of one window, with its next and recent occurrences."""
    device = db.session.get(NetworkDiscovery, window.NetDiscoveryID) if window.NetDiscoveryID else None
    creator = db.session.get(User, window.Created_By)
    upcoming = maintenance.next_occurrence(window, now) if window.Status == maintenance.ACTIVE else None
    recent = sorted(window.Occurrences, key=lambda row: row.Start_At, reverse=True)[:RECENT_OCCURRENCES]
    return {
        "id": window.WindowID,
        "scope": {
            "type": "device" if window.NetDiscoveryID else "all",
            "deviceId": window.NetDiscoveryID,
            "deviceName": nagios_host_name(device) if device else None,
        },
        "startAt": maintenance.iso(window.Start_At),
        "endAt": maintenance.iso(window.End_At),
        "recurrence": window.Recurrence,
        "recurrenceUntil": maintenance.iso(window.Recurrence_Until),
        "timeZone": window.Time_Zone,
        "comment": window.Comment,
        "status": window.Status,
        "nextOccurrence": {"startAt": maintenance.iso(upcoming[0]), "endAt": maintenance.iso(upcoming[1])} if upcoming else None,
        "lastOccurrenceSent": maintenance.iso(window.Last_Occurrence_Sent),
        "createdBy": f"{creator.First_Name} {creator.Last_Name}" if creator else None,
        "createdAt": maintenance.iso(window.Created_At),
        "occurrences": [
            {"startAt": maintenance.iso(row.Start_At), "endAt": maintenance.iso(row.End_At),
             "status": row.Status, "attempts": row.Attempts, "error": row.Last_Error}
            for row in recent
        ],
    }


def get_window_or_404(id):
    window = db.session.get(MaintenanceWindow, id)
    if window is None:
        return None, error("Maintenance window not found.", 404)
    return window, None


def apply_fields(window, fields):
    for name, value in fields.items():
        setattr(window, name, value)


@system_bp.get('/maintenance/windows')
@login_required
@require_permission(PERMISSION)
def list_maintenance_windows():
    """List maintenance windows, newest first, and the monitored devices to scope one to."""
    now = maintenance.utcnow()
    windows = db.session.scalars(
        sa.select(MaintenanceWindow).order_by(MaintenanceWindow.WindowID.desc()).limit(MAX_LISTED)
    ).all()
    devices = sorted(
        ({"id": device.NetDiscoveryID, "name": nagios_host_name(device)}
         for device in db.session.scalars(sa.select(NetworkDiscovery)) if monitoring_state(device) == "monitored"),
        key=lambda device: device["name"].lower(),
    )
    return success({"windows": [serialize_window(window, now) for window in windows], "devices": devices})


@system_bp.post('/maintenance/windows')
@login_required
@require_permission(PERMISSION)
def create_maintenance_window():
    """Create a maintenance window. The downtime is sent to Nagios shortly before it starts."""
    fields, message = maintenance.validate_window(request.get_json(silent=True), maintenance.utcnow())
    if message:
        return error(message, 400)

    window = MaintenanceWindow(**fields, Created_By=current_user.UserID)
    db.session.add(window)
    try:
        db.session.flush()
        create_user_log(current_user.UserID, f"Created maintenance window {window.WindowID}: {window.Comment}"[:255])
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("The maintenance window could not be saved.", 500)

    return success(serialize_window(window, maintenance.utcnow()), message="Maintenance window created.", status=201)


@system_bp.put('/maintenance/windows/<int:id>')
@login_required
@require_permission(PERMISSION)
def update_maintenance_window(id):
    """
    Replace an active window. Downtime already handed to Nagios for its unfinished occurrences
    is deleted, then the dispatcher schedules the new times. nagios_synced is false when Nagios
    could not be told to delete it.
    """
    window, err = get_window_or_404(id)
    if err is not None:
        return err
    if window.Status != maintenance.ACTIVE:
        return error(f"A {window.Status} window cannot be edited.", 400)

    now = maintenance.utcnow()
    fields, message = maintenance.validate_window(request.get_json(silent=True), now)
    if message:
        return error(message, 400)

    results = maintenance.cancel_live_occurrences(window, now, delete_rows=True)
    apply_fields(window, fields)
    try:
        create_user_log(current_user.UserID, f"Updated maintenance window {window.WindowID}: {window.Comment}"[:255])
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("The maintenance window could not be saved.", 500)

    sync = sync_fields(current_user.UserID, results, f"update maintenance window {window.WindowID}")
    return success({**serialize_window(window, now), **sync}, message="Maintenance window updated.")


@system_bp.post('/maintenance/windows/<int:id>/cancel')
@login_required
@require_permission(PERMISSION)
def cancel_maintenance_window(id):
    """Cancel a window and delete its pending and running Nagios downtime. No body."""
    window, err = get_window_or_404(id)
    if err is not None:
        return err
    if window.Status == maintenance.CANCELLED:
        return error("The window is already cancelled.", 400)

    now = maintenance.utcnow()
    results = maintenance.cancel_live_occurrences(window, now, delete_rows=False)
    window.Status = maintenance.CANCELLED
    try:
        create_user_log(current_user.UserID, f"Cancelled maintenance window {window.WindowID}: {window.Comment}"[:255])
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("The maintenance window could not be cancelled.", 500)

    sync = sync_fields(current_user.UserID, results, f"cancel maintenance window {window.WindowID}")
    return success({**serialize_window(window, now), **sync}, message="Maintenance window cancelled.")
