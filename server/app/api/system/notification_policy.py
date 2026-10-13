"""System-wide Nagios notification timing and state options.

Routes
------
GET  /system/notification-policy
    Read the singleton policy in Nagios server local time.
PUT  /system/notification-policy
    Validate, apply and save a versioned policy.
"""
import re

from flask import current_app, request
from flask_login import current_user, login_required

from app import db
from app.api.helper import error, success
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.logging.configuration_changes import create_configuration_log
from app.system_models import NotificationPolicy, SystemSettings

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
HOST_OPTIONS = ("d", "u", "r", "f", "s")
SERVICE_OPTIONS = ("w", "u", "c", "r", "f", "s")
TIME = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")


def policy_row():
    """Return the singleton, creating defaults only for a fresh test database."""
    row = db.session.get(NotificationPolicy, 1)
    if row is None:
        row = NotificationPolicy(Id=1)
        db.session.add(row)
        db.session.flush()
    return row


def serialize_policy(row):
    """Convert stored option strings to the public list contract."""
    return {"quietHours": row.Quiet_Hours, "hostOptions": row.Host_Options.split(","),
            "serviceOptions": row.Service_Options.split(","),
            "renotifyInterval": row.Renotify_Interval, "version": row.Version,
            "timeZone": "Nagios server local time"}


def validate_policy(data):
    """Return a field-specific message or None; accept only fixed Nagios literals."""
    if not isinstance(data, dict):
        return "Policy must be a JSON object."
    windows = data.get("quietHours")
    if not isinstance(windows, list) or len(windows) > 100:
        return "quietHours must be a list of at most 100 windows."
    by_day = {day: [] for day in WEEKDAYS}
    for index, window in enumerate(windows):
        if not isinstance(window, dict) or window.get("weekday") not in WEEKDAYS:
            return f"quietHours[{index}].weekday must be a weekday name."
        for key in ("start", "end"):
            if not isinstance(window.get(key), str) or not TIME.fullmatch(window[key]):
                return f"quietHours[{index}].{key} must be HH:MM (24-hour time)."
        if window["start"] >= window["end"]:
            return f"quietHours[{index}].start must be before end (split midnight crossings)."
        by_day[window["weekday"]].append((window["start"], window["end"]))
    for periods in by_day.values():
        periods.sort()
        if any(periods[i][0] < periods[i - 1][1] for i in range(1, len(periods))):
            return "quietHours windows must not overlap on a weekday."
    for field, allowed in (("hostOptions", HOST_OPTIONS), ("serviceOptions", SERVICE_OPTIONS)):
        options = data.get(field)
        if (not isinstance(options, list) or not options or len(options) > len(allowed)
                or any(not isinstance(item, str) or item not in allowed for item in options)
                or len(set(options)) != len(options)):
            return f"{field} must contain distinct allowed option letters."
    interval = data.get("renotifyInterval")
    if type(interval) is not int or not 0 <= interval <= 1440:
        return "renotifyInterval must be an integer from 0 to 1440 minutes."
    return None


# ==========================================================
# POLICY ROUTES
# ==========================================================
@system_bp.get('/notification-policy')
@login_required
@require_permission('settings.system')
def get_notification_policy():
    """Return notification settings; quiet hours use the Nagios server's local time."""
    try:
        row = policy_row()
        db.session.commit()
        return success(serialize_policy(row))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not read notification policy.")
        return error("An unexpected error occurred.", 500)


@system_bp.put('/notification-policy')
@login_required
@require_permission('settings.system')
def update_notification_policy():
    """Save a policy after Nagios accepts it.

    JSON: {"version": 1, "quietHours": [{"weekday": "monday", "start": "09:00",
    "end": "10:00"}], "hostOptions": ["d", "u", "r", "f", "s"],
    "serviceOptions": ["w", "u", "c", "r", "f", "s"], "renotifyInterval": 30}.
    """
    data = request.get_json(silent=True)
    problem = validate_policy(data)
    if problem:
        return error(problem, 400)
    try:
        row = policy_row()
        if data.get("version") != row.Version:
            db.session.rollback()
            return error("Notification policy was updated by someone else. Reload and try again.", 409)
        before = serialize_policy(row)
        row.Quiet_Hours = [{key: window[key] for key in ("weekday", "start", "end")}
                           for window in data["quietHours"]]
        row.Host_Options = ",".join(item for item in HOST_OPTIONS if item in data["hostOptions"])
        row.Service_Options = ",".join(item for item in SERVICE_OPTIONS if item in data["serviceOptions"])
        row.Renotify_Interval = data["renotifyInterval"]
        db.session.flush()
        from app.network_discovery.create_host_cfg import regenerate_and_apply_config_status
        status, message = regenerate_and_apply_config_status()
        if status == "failed":
            db.session.rollback()
            return error(f"Notification policy could not be applied: {message}", 422)
        row.Version += 1
        row.Updated_By = current_user.UserID
        settings = db.session.get(SystemSettings, 1)
        if settings is None or settings.Audit_Logging:
            after = serialize_policy(row)
            for field in ("quietHours", "hostOptions", "serviceOptions", "renotifyInterval"):
                if before[field] != after[field]:
                    create_configuration_log(current_user.UserID, "notification_policy", field,
                                             str(before[field])[:100], str(after[field])[:100])
        db.session.commit()
        return success(serialize_policy(row), message="Notification policy updated.")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update notification policy.")
        return error("An unexpected error occurred.", 500)
