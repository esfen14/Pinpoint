"""
System-wide settings: the singleton SystemSettings row.

The Settings page has three tabs. General settings can be changed by any
logged-in user; the Security and System tabs each need their own
permission, assigned per role in Manage Roles. The whole object is sent
on every save, so the check is on which fields actually changed.

Routes
------
GET  /system
    Return the current settings. Open to any logged-in user, since every
    page reads them (theme, refresh rate, session timeout, maintenance).

PUT  /system
    Save settings, rejecting fields the user isn't allowed to change.
"""
import math
from functools import wraps

from flask import request, current_app
from flask_login import login_required, current_user

from app import db
from app.api.system import system_bp
from app.api.helper import success, error, user_has_permission
from app.system_models import SystemSettings
from app.logging.configuration_changes import create_configuration_log


# Which permission guards each settings field. Fields not listed here
# are General settings, open to every logged-in user.
FIELD_PERMISSIONS = {
    "Session_Timeout": "settings.security",
    "Strong_Password_Policy": "settings.security",
    "Failed_Login_Monitoring": "settings.security",
    "Audit_Logging": "settings.security",
    "Security_Check_Frequency": "settings.security",
    "System_Update_Frequency": "settings.system",
    "Check_Interval": "settings.system",
    "Data_Polling_Interval": "settings.system",
    "Retry_Interval": "settings.system",
    "Max_Check_Attempts": "settings.system",
    "Flap_Detection_Enabled": "settings.system",
    "Flap_Low_Threshold": "settings.system",
    "Flap_High_Threshold": "settings.system",
    "Maintenance_Mode": "settings.system",
    "Automatic_Backups": "settings.system",
    "Log_Retention_Days": "settings.system",
    "Diagnostic_History_Retention_Days": "settings.system",
}

# Settings rendered into the generated Nagios config: changing one rebuilds and applies it.
CHECK_TIMING_FIELDS = (
    "Check_Interval", "Retry_Interval", "Max_Check_Attempts",
    "Flap_Detection_Enabled", "Flap_Low_Threshold", "Flap_High_Threshold",
)

PERMISSION_LABELS = {
    "settings.security": "Security",
    "settings.system": "System",
}


def _get_singleton_row():
    row = db.session.get(SystemSettings, 1)
    if row is None:
        row = SystemSettings(Id=1)
        db.session.add(row)
        db.session.commit()
    return row


@system_bp.route("", methods=["GET"])
@login_required
def get_settings():
    try:
        row = _get_singleton_row()
        return success(row.to_dict())
    except Exception:
        current_app.logger.exception("An unexpected error occurred while fetching settings.")
        return error("An unexpected error occurred.", 500)


def serialize_settings_save(function):
    """Serialize settings reads/saves and scheduler compensation in this worker."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        from app.scheduler import settings_schedule_lock

        with settings_schedule_lock:
            return function(*args, **kwargs)
    return wrapped


@system_bp.route("", methods=["PUT"])
@login_required
@serialize_settings_save
def update_settings():
    """
    Save the settings. The client sends the full settings object with the
    version it loaded; a stale version is rejected with 409. Changing a
    Security or System field without that tab's permission is rejected
    with 403 and nothing is saved. Unchanged restricted fields are fine,
    so users without those permissions can still save General settings.

    Optional dataPollingInterval: integer 30/60/120/300 seconds (default 60).
    It reschedules Pinpoint polling without changing Nagios or browser timing.
    Reschedule or persistence failure restores the saved interval and job.

    Optional System fields (omit to keep the saved value): retryInterval,
    maxCheckAttempts, flapDetectionEnabled (bool), flapLowThreshold and
    flapHighThreshold (0 to 100, low below high, null for "use Nagios's own
    value"). Changing any of them, or checkInterval, rebuilds the Nagios config;
    if Nagios rejects it nothing is saved and the response is 422.

    JSON Format
    {
        "version": 3,
        "scanFrequency": 6,
        "notifications": true,
        "exportFormats": ["CSV", "PDF", "XLS"],
        "sessionTimeout": 30,
        "strongPasswordPolicy": true,
        "failedLoginMonitoring": true,
        "auditLogging": true,
        "securityCheckFrequency": "weekly",
        "systemUpdateFrequency": "monthly",
        "maintenanceMode": false,
        "automaticBackups": true,
        "logRetentionDays": 30,
        "diagnosticHistoryRetentionDays": 90
    }
    """
    try:
        row = _get_singleton_row()
        payload = request.get_json(force=True)

        if payload is None:
            return error("No JSON data provided.", 400)

        incoming_version = payload.get("version")
        if incoming_version != row.Version:
            return error(
                "Settings were updated by someone else. Reload and try again.",
                409,
            )

        # Whether to record this save's diffs in the Configuration Change
        # log — governed by the policy in effect when the save started, not
        # whatever Audit_Logging ends up as after this same request applies.
        audit_logging_enabled = bool(row.Audit_Logging)

        field_map = [
            ("Scan_Frequency", "scanFrequency"),
            ("Check_Interval", "checkInterval"),
            ("Data_Polling_Interval", "dataPollingInterval"),
            ("Retry_Interval", "retryInterval"),
            ("Max_Check_Attempts", "maxCheckAttempts"),
            ("Flap_Detection_Enabled", "flapDetectionEnabled"),
            ("Flap_Low_Threshold", "flapLowThreshold"),
            ("Flap_High_Threshold", "flapHighThreshold"),
            ("Notifications", "notifications"),
            ("Session_Timeout", "sessionTimeout"),
            ("Strong_Password_Policy", "strongPasswordPolicy"),
            ("Failed_Login_Monitoring", "failedLoginMonitoring"),
            ("Audit_Logging", "auditLogging"),
            ("Security_Check_Frequency", "securityCheckFrequency"),
            ("System_Update_Frequency", "systemUpdateFrequency"),
            ("Maintenance_Mode", "maintenanceMode"),
            ("Automatic_Backups", "automaticBackups"),
            ("Log_Retention_Days", "logRetentionDays"),
            ("Diagnostic_History_Retention_Days", "diagnosticHistoryRetentionDays"),
        ]

        from app.scheduler import SUPPORTED_POLL_INTERVALS, polling_schedule_change

        polling_interval = payload.get("dataPollingInterval", row.Data_Polling_Interval)
        if type(polling_interval) is not int or polling_interval not in SUPPORTED_POLL_INTERVALS:
            return error("Data polling interval must be 30, 60, 120 or 300 seconds.", 400)

        interval = payload.get("checkInterval", row.Check_Interval)
        if type(interval) is not int or interval not in (1, 2, 5, 10, 15):
            return error("Check interval must be 1, 2, 5, 10 or 15 minutes.", 400)

        # The retry settings are optional in the body, so a client that predates
        # them keeps the saved values. Every value is checked against the
        # check interval that will be in effect after this save.
        retry_interval = payload.get("retryInterval", row.Retry_Interval)
        if type(retry_interval) is not int or not 1 <= retry_interval <= 10:
            return error("Retry interval must be a whole number of minutes from 1 to 10.", 400)
        if retry_interval > interval:
            return error("Retry interval cannot be longer than the check interval.", 400)
        max_check_attempts = payload.get("maxCheckAttempts", row.Max_Check_Attempts)
        if type(max_check_attempts) is not int or not 1 <= max_check_attempts <= 10:
            return error("Maximum check attempts must be a whole number from 1 to 10.", 400)
        resolved = {"retryInterval": retry_interval, "maxCheckAttempts": max_check_attempts,
                    "dataPollingInterval": polling_interval}

        # Flap detection settings are optional in the body too. A threshold is a
        # percentage of state change (0 to 100) or null for "use Nagios's value".
        flap_enabled = payload.get("flapDetectionEnabled", row.Flap_Detection_Enabled)
        if type(flap_enabled) is not bool:
            return error("Flap detection must be on or off.", 400)
        thresholds = {}
        for key, saved, label in (
            ("flapLowThreshold", row.Flap_Low_Threshold, "Low flap threshold"),
            ("flapHighThreshold", row.Flap_High_Threshold, "High flap threshold"),
        ):
            value = payload.get(key, saved)
            if value is not None:
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
                    return error(f"{label} must be a percentage from 0 to 100.", 400)
            thresholds[key] = value
        low, high = thresholds["flapLowThreshold"], thresholds["flapHighThreshold"]
        if low is not None and high is not None and low >= high:
            return error("Low flap threshold must be lower than the high flap threshold.", 400)
        resolved.update(flapDetectionEnabled=flap_enabled, **thresholds)

        changes = []
        for attr, key in field_map:
            old_value = getattr(row, attr)
            new_value = resolved[key] if key in resolved else payload[key]
            if old_value != new_value:
                changes.append((attr, old_value, new_value))
                setattr(row, attr, new_value)

        new_export_formats = ",".join(payload["exportFormats"])
        if row.Export_Formats != new_export_formats:
            changes.append(("Export_Formats", row.Export_Formats, new_export_formats))
            row.Export_Formats = new_export_formats

        denied = []
        for attr, _, _ in changes:
            permission = FIELD_PERMISSIONS.get(attr)
            if permission is None or permission in denied:
                continue
            if not user_has_permission(permission):
                denied.append(permission)

        if denied:
            db.session.rollback()
            tabs = " and ".join(PERMISSION_LABELS[p] for p in denied)
            return error(f"You don't have permission to change {tabs} settings.", 403)

        if any(attr in CHECK_TIMING_FIELDS for attr, _, _ in changes):
            from app.network_discovery.create_host_cfg import regenerate_and_apply_config_status

            db.session.flush()
            status, message = regenerate_and_apply_config_status()
            if status == "failed":
                db.session.rollback()
                return error(f"Check settings could not be applied: {message}", 422)

        polling_changed = any(attr == "Data_Polling_Interval" for attr, _, _ in changes)
        with polling_schedule_change(polling_interval if polling_changed else None):
            row.Version += 1
            row.Updated_By = current_user.UserID

            if audit_logging_enabled:
                for attr, old_value, new_value in changes:
                    create_configuration_log(
                        current_user.UserID, "system_settings", attr, str(old_value), str(new_value)
                    )

            db.session.flush()
            data = row.to_dict()
            db.session.commit()
        return success(data, message="Settings updated.")

    except KeyError as exc:
        db.session.rollback()
        return error(f"Missing required field: {exc}", 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("An unexpected error occurred while updating settings.")
        return error("An unexpected error occurred.", 500)
