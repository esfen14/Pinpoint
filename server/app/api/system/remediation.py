"""
Remediation: allowlisted actions that run when a service or host reaches a HARD failure, and the
log of what the consumer decided (app/remediation.py).

Routes
------
GET    /system/remediation/action-types
    The action types an admin can pick, with their parameter schema (remediation.view).
GET    /system/remediation/targets
    Nagios host names with their service names, to suggest in the form (remediation.view).
GET    /system/remediation/actions
    All actions (remediation.view).
POST   /system/remediation/actions
    Create an action; validation errors come back per field (remediation.manage).
PUT    /system/remediation/actions/<id>
    Replace an action; needs the current version, 409 when stale (remediation.manage).
DELETE /system/remediation/actions/<id>
    Delete an action; its runs stay in the log (remediation.manage).
GET    /system/remediation/services/<hostname>/<service_name>
    The "Recover automatically" setting of one service (remediation.view).
PUT    /system/remediation/services/<hostname>/<service_name>
    Turn it on or off and set the restart limit; the server picks the action and unit
    (remediation.manage).
GET    /system/remediation/settings
    The kill switch, the run retention and the repeat-recovery count and window (remediation.view).
PUT    /system/remediation/settings
    Change them; each change is audited (remediation.manage).
GET    /system/remediation/health
    The consumer's heartbeat, backlog and 24 hour counts, with a stalled flag (remediation.view).
GET    /system/remediation/runs
    The run log, newest first, with filters and pagination (remediation.view).
GET    /system/remediation/runs/<id>
    One run, including its (redacted) output (remediation.view).
GET    /system/remediation/last-runs
    The newest run for each host and service in the last 7 days, for the badge on a service row
    (remediation.view).

Creating, changing or deleting an action regenerates the Nagios config; a config Nagios
rejects rolls the change back and returns 422.
"""
import hashlib
import re
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from flask import current_app, request
from flask_login import current_user, login_required

from app import db
from app import remediation_actions as registry
from app.api.helper import error, success
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.history_models import ServiceStatus
from app.logging.configuration_changes import create_configuration_log
from app import remediation
from app.remediation import valid_name
from app.history_models import ServiceStatus
from app.network_discovery.device_identity import nagios_host_name
from app.system_models import (
    DeviceState, NetworkDiscovery, RemediationAction, RemediationActionType, RemediationOutcome,
    RemediationRun, RemediationScope, SystemSettings,
)

NAME_RE = re.compile(r"[A-Za-z0-9 ._-]{3,60}", re.ASCII)
HOST_PATTERN_RE = re.compile(r"[A-Za-z0-9._*-]{1,100}", re.ASCII)
SERVICE_PATTERN_RE = re.compile(r"[A-Za-z0-9 ._:/*-]{1,150}", re.ASCII)
ACTION_FIELDS = {
    "name", "actionType", "scopeKind", "hostPattern", "servicePattern", "parameters", "enabled",
    "maxRunsPerHour", "cooldownSeconds", "runWhenAcknowledged", "notifyOn",
}
LOGGED_FIELDS = (
    "name", "actionType", "scopeKind", "hostPattern", "servicePattern", "parameters", "enabled",
    "maxRunsPerHour", "cooldownSeconds", "runWhenAcknowledged", "notifyOn",
)
NOTIFY_KINDS = ("failed", "capped", "repeated")
SETTINGS_FIELDS = ("enabled", "retentionDays", "repeatCount", "repeatWindowHours")
LAST_RUNS_DAYS = 7
TARGET_SERVICE_DAYS = 7
MAX_LAST_RUNS = 500
MIN_REPEAT_COUNT = 2
MAX_REPEAT_COUNT = 20
MIN_REPEAT_WINDOW_HOURS = 1
MAX_REPEAT_WINDOW_HOURS = 168
MIN_RETENTION_DAYS = 7
MAX_RETENTION_DAYS = 3650
MIN_RESTARTS_PER_HOUR = 1
MAX_RESTARTS_PER_HOUR = 6
DEFAULT_RESTARTS_PER_HOUR = 2
SERVICE_RECOVERY_FIELDS = {"enabled", "maxRestartsPerHour", "version"}
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100


# ==========================================================
# HELPERS
# ==========================================================

def serialize_action(row):
    """Public shape of one action."""
    return {
        "id": row.Id,
        "name": row.Name,
        "actionType": row.Action_Type.value,
        "scopeKind": row.Scope_Kind.value,
        "hostPattern": row.Host_Pattern,
        "servicePattern": row.Service_Pattern,
        "parameters": row.Parameters or {},
        "enabled": row.Enabled,
        "maxRunsPerHour": row.Max_Runs_Per_Hour,
        "cooldownSeconds": row.Cooldown_Seconds,
        "runWhenAcknowledged": row.Run_When_Acknowledged,
        "notifyOn": list(row.Notify_On or []),
        "version": row.Version,
        "updatedAt": row.Updated_At.isoformat() if row.Updated_At else None,
        "updatedBy": row.Updated_By,
    }


def serialize_run(row, with_output=False):
    """Public shape of one run; the output is only included for the detail view."""
    item = {
        "id": row.Id,
        "actionId": row.Action_Id,
        "actionName": row.Action_Name,
        "hostname": row.Hostname,
        "service": row.Service,
        "state": row.State.value,
        "stateType": row.State_Type.value,
        "attempt": row.Attempt,
        "receivedAt": row.Received_At.isoformat(),
        "startedAt": row.Started_At.isoformat() if row.Started_At else None,
        "finishedAt": row.Finished_At.isoformat() if row.Finished_At else None,
        "outcome": row.Outcome.value,
        "reason": row.Reason,
        "notifyKind": row.Notify_Kind,
        "notifyState": row.Notify_State.value if row.Notify_State else None,
        "notifyAttempts": row.Notify_Attempts or 0,
        "notifyError": row.Notify_Error,
        "notifyAt": row.Notify_At.isoformat() if row.Notify_At else None,
    }
    if with_output:
        item["output"] = row.Output
    return item


def bad_fields(fields, message="Some fields are not valid."):
    """A 400 response that names each bad field so the form can show it in place."""
    return error(message, 400, {"fields": fields})


def is_int(value):
    """True for a real integer (a JSON true or false is not one)."""
    return isinstance(value, int) and not isinstance(value, bool)


def validate_action(data, current_id=None):
    """
    Validate a create or update body. Returns (cleaned, errors): cleaned holds the values to
    store, errors maps a field name to one message. Unknown fields are errors, not ignored.
    """
    if not isinstance(data, dict):
        return None, {"body": "Request body must be a JSON object."}
    errors = {}
    for key in data:
        if key not in ACTION_FIELDS and key != "version":
            errors[key] = "Unknown field."

    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or name != name.strip():
        errors["name"] = "Name must be 3 to 60 letters, numbers, spaces, dots, dashes or underscores."
    else:
        taken = db.session.scalar(sa.select(RemediationAction.Id).where(RemediationAction.Name == name))
        if taken is not None and taken != current_id:
            errors["name"] = "An action with this name already exists."

    action_type = data.get("actionType")
    if not isinstance(action_type, str) or action_type not in registry.ACTION_TYPES:
        errors["actionType"] = "Choose one of the available action types."

    scope = data.get("scopeKind")
    if scope not in ("service", "host"):
        errors["scopeKind"] = "Scope must be service or host."

    host_pattern = data.get("hostPattern")
    if not isinstance(host_pattern, str) or not HOST_PATTERN_RE.fullmatch(host_pattern):
        errors["hostPattern"] = "Host pattern must be 1 to 100 letters, numbers, dots, dashes, underscores or *."

    service_pattern = data.get("servicePattern")
    if scope == "service":
        if not isinstance(service_pattern, str) or not SERVICE_PATTERN_RE.fullmatch(service_pattern):
            errors["servicePattern"] = "Service pattern must be 1 to 150 letters, numbers, spaces, . _ : / - or *."
    elif scope == "host" and service_pattern not in (None, ""):
        errors["servicePattern"] = "A host action takes no service pattern."
        service_pattern = None
    else:
        service_pattern = None

    parameters = {}
    if "actionType" not in errors:
        parameters, parameter_errors = registry.validate_parameters(action_type, data.get("parameters"))
        for key, message in parameter_errors.items():
            errors[key if key == "parameters" else f"parameters.{key}"] = message

    enabled = data.get("enabled", False)
    if type(enabled) is not bool:
        errors["enabled"] = "Enabled must be true or false."

    max_runs = data.get("maxRunsPerHour", 2)
    if not is_int(max_runs) or not 1 <= max_runs <= 60:
        errors["maxRunsPerHour"] = "Runs per hour must be a whole number from 1 to 60."

    cooldown = data.get("cooldownSeconds", 600)
    if not is_int(cooldown) or not 60 <= cooldown <= 86400:
        errors["cooldownSeconds"] = "Cooldown must be a whole number of seconds from 60 to 86400."

    run_when_acknowledged = data.get("runWhenAcknowledged", False)
    if type(run_when_acknowledged) is not bool:
        errors["runWhenAcknowledged"] = "Run when acknowledged must be true or false."

    notify_on = data.get("notifyOn", list(NOTIFY_KINDS))
    if not isinstance(notify_on, list) or any(kind not in NOTIFY_KINDS for kind in notify_on):
        errors["notifyOn"] = "Notify on must be a list of failed, capped or repeated."
    else:
        notify_on = [kind for kind in NOTIFY_KINDS if kind in notify_on]

    if errors:
        return None, errors
    return {
        "Name": name, "Action_Type": RemediationActionType(action_type), "Scope_Kind": RemediationScope(scope),
        "Host_Pattern": host_pattern, "Service_Pattern": service_pattern, "Parameters": parameters,
        "Enabled": enabled, "Max_Runs_Per_Hour": max_runs, "Cooldown_Seconds": cooldown,
        "Run_When_Acknowledged": run_when_acknowledged, "Notify_On": notify_on,
    }, {}


def log_changes(before, after):
    """Write one configuration-log line per changed field, when audit logging is on."""
    settings = db.session.get(SystemSettings, 1)
    if settings is not None and not settings.Audit_Logging:
        return
    for field in LOGGED_FIELDS:
        old = before.get(field) if before else ""
        new = after.get(field) if after else ""
        if old != new:
            create_configuration_log(current_user.UserID, "remediation_action", field, str(old)[:100], str(new)[:100])


def apply_config():
    """Regenerate and apply the Nagios config. Returns (ok, message)."""
    from app.network_discovery.create_host_cfg import regenerate_and_apply_config_status
    status, message = regenerate_and_apply_config_status()
    return status != "failed", message


def parse_page():
    """(page, per_page) from the query string, or raises ValueError with the problem."""
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", str(DEFAULT_PER_PAGE)))
    except ValueError:
        raise ValueError("page and per_page must be whole numbers.")
    if page < 1:
        raise ValueError("page must be 1 or more.")
    if not 1 <= per_page <= MAX_PER_PAGE:
        raise ValueError(f"per_page must be from 1 to {MAX_PER_PAGE}.")
    return page, per_page


def parse_day(text, name):
    """A YYYY-MM-DD date, or raises ValueError naming the parameter."""
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{name} must be a date like 2026-10-14.")


# ==========================================================
# ACTION TYPES AND ACTIONS
# ==========================================================

@system_bp.get('/remediation/action-types')
@login_required
@require_permission('remediation.view')
def list_remediation_action_types():
    """Return the action types with their parameter schema, for the form."""
    return success({"items": registry.describe_types()})


@system_bp.get('/remediation/targets')
@login_required
@require_permission('remediation.view')
def list_remediation_targets():
    """
    Return the Nagios host names and, for each, the service names seen in the last
    TARGET_SERVICE_DAYS days, so the form can suggest names instead of asking the admin to type them.
    """
    try:
        since = datetime.now(timezone.utc) - timedelta(days=TARGET_SERVICE_DAYS)
        services = {}
        pairs = db.session.execute(
            sa.select(ServiceStatus.Hostname, ServiceStatus.Service)
            .where(ServiceStatus.Timestamp >= since).distinct()
        ).all()
        for hostname, service in pairs:
            services.setdefault(hostname, set()).add(service)
        names = set(services)
        devices = db.session.scalars(
            sa.select(NetworkDiscovery).where(NetworkDiscovery.Device_State != DeviceState.MERGED)
        ).all()
        names.update(nagios_host_name(device) for device in devices)
        items = [{"hostname": name, "services": sorted(services.get(name, ()))} for name in sorted(names)]
        return success({"items": items})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not list remediation targets.")
        return error("An unexpected error occurred.", 500)


@system_bp.get('/remediation/actions')
@login_required
@require_permission('remediation.view')
def list_remediation_actions():
    """Return every action, ordered by name."""
    try:
        rows = db.session.scalars(sa.select(RemediationAction).order_by(RemediationAction.Name)).all()
        items = []
        for row in rows:
            items.append(serialize_action(row))
        return success({"items": items})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not list remediation actions.")
        return error("An unexpected error occurred.", 500)


@system_bp.post('/remediation/actions')
@login_required
@require_permission('remediation.manage')
def create_remediation_action():
    """
    Create an action after Nagios accepts the resulting config.

    JSON: {"name": "restart-web", "actionType": "record_only", "scopeKind": "service",
    "hostPattern": "web-*", "servicePattern": "HTTP", "parameters": {}, "enabled": true,
    "maxRunsPerHour": 2, "cooldownSeconds": 600, "runWhenAcknowledged": false,
    "notifyOn": ["failed", "capped", "repeated"]}. notifyOn lists which problems notify the
    operator through Nagios; it defaults to all three and may be empty. Errors: 400 with
    data.fields, 422 when Nagios rejects the config.
    """
    data = request.get_json(silent=True)
    cleaned, errors = validate_action(data)
    if errors:
        return bad_fields(errors)
    try:
        row = RemediationAction(**cleaned, Version=1, Updated_By=current_user.UserID)
        db.session.add(row)
        db.session.flush()
        ok, message = apply_config()
        if not ok:
            db.session.rollback()
            return error(f"The action could not be applied: {message}", 422)
        log_changes(None, serialize_action(row))
        db.session.commit()
        return success(serialize_action(row), message="Action created.", status=201)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not create remediation action.")
        return error("An unexpected error occurred.", 500)


@system_bp.put('/remediation/actions/<int:action_id>')
@login_required
@require_permission('remediation.manage')
def update_remediation_action(action_id):
    """
    Replace an action's fields after Nagios accepts the resulting config.

    JSON: the same fields as create, plus "version" (the current version). Errors: 400 with
    data.fields, 404, 409 when the version is stale, 422 when Nagios rejects the config.
    """
    data = request.get_json(silent=True)
    try:
        row = db.session.get(RemediationAction, action_id)
        if row is None:
            return error("Action not found.", 404)
        cleaned, errors = validate_action(data, current_id=action_id)
        if errors:
            return bad_fields(errors)
        if not is_int(data.get("version")) or data["version"] != row.Version:
            return error("This action was changed by someone else. Reload and try again.", 409)
        before = serialize_action(row)
        for field, value in cleaned.items():
            setattr(row, field, value)
        db.session.flush()
        ok, message = apply_config()
        if not ok:
            db.session.rollback()
            return error(f"The action could not be applied: {message}", 422)
        row.Version += 1
        row.Updated_By = current_user.UserID
        log_changes(before, serialize_action(row))
        db.session.commit()
        return success(serialize_action(row), message="Action updated.")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update remediation action.")
        return error("An unexpected error occurred.", 500)


@system_bp.delete('/remediation/actions/<int:action_id>')
@login_required
@require_permission('remediation.manage')
def delete_remediation_action(action_id):
    """Delete an action after Nagios accepts the resulting config. Its runs stay in the log."""
    try:
        row = db.session.get(RemediationAction, action_id)
        if row is None:
            return error("Action not found.", 404)
        before = serialize_action(row)
        # Keep audit snapshots and detach history even on SQLite connections that do
        # not enable foreign-key enforcement. Rollback restores links if apply fails.
        db.session.execute(sa.update(RemediationRun).where(
            RemediationRun.Action_Id == action_id
        ).values(Action_Id=None))
        db.session.delete(row)
        db.session.flush()
        ok, message = apply_config()
        if not ok:
            db.session.rollback()
            return error(f"The action could not be removed: {message}", 422)
        log_changes(before, None)
        db.session.commit()
        return success(message="Action deleted.")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not delete remediation action.")
        return error("An unexpected error occurred.", 500)


# ==========================================================
# PER-SERVICE "RECOVER AUTOMATICALLY"
# ==========================================================

def service_action_name(hostname, service_name):
    """A readable, unique, valid action name for the action a service's switch creates."""
    digest = hashlib.sha256(f"{hostname}|{service_name}".encode("utf-8")).hexdigest()[:8]
    label = re.sub(r"[^A-Za-z0-9 ._-]", "-", f"Auto recover {hostname} {service_name}")[:48].rstrip()
    return f"{label} {digest}"


def find_service_action(hostname, service_name):
    """The restart action scoped to exactly this host and service (made here or on the Remediation page), or None."""
    return db.session.scalar(
        sa.select(RemediationAction).where(
            RemediationAction.Scope_Kind == RemediationScope.SERVICE,
            RemediationAction.Host_Pattern == hostname,
            RemediationAction.Service_Pattern == service_name,
            RemediationAction.Action_Type.in_((
                RemediationActionType.RESTART_LOCAL_SERVICE, RemediationActionType.RESTART_REMOTE_SERVICE)),
        ).order_by(RemediationAction.Id).limit(1))


def is_known_service(hostname, service_name):
    """True when Nagios has reported this exact host and service."""
    if not valid_name(hostname, 100) or not valid_name(service_name, 150):
        return False
    return db.session.scalar(
        sa.select(ServiceStatus.ServiceStatusID).where(
            ServiceStatus.Hostname == hostname, ServiceStatus.Service == service_name).limit(1)) is not None


def service_recovery_problem(hostname, service_name):
    """
    Why a new rule cannot be switched on for this service, as (action_type, units, reason). The
    reason is None when it can. Checked in order: the names fit a rule, the server can pick a valid
    restart action and unit, and the event handler program is installed.
    """
    from app.network_discovery.host_config_templates import event_handler_path
    if "*" in hostname or "*" in service_name or not HOST_PATTERN_RE.fullmatch(hostname) \
            or not SERVICE_PATTERN_RE.fullmatch(service_name):
        return None, [], "This host or service name cannot be used in an automatic recovery rule."
    action_type, units, reason = remediation.choose_service_recovery(hostname, service_name)
    if reason is None and event_handler_path() is None:
        return None, [], "The event handler is not installed on this server, so automatic recovery cannot run."
    return action_type, units, reason


def serialize_service_recovery(hostname, service_name):
    """
    The public shape of one service's setting: whether it is on, its limit and version, the action
    and unit that apply, whether it can be switched on (canEnable) and why not (reason), other
    enabled actions that also cover the service, and the newest run.
    """
    action = find_service_action(hostname, service_name)
    action_type, units, reason = service_recovery_problem(hostname, service_name)
    unit = None
    if action is not None:
        action_type = action.Action_Type.value
        unit = (action.Parameters or {}).get("unit")
    elif units:
        unit = units[0]
    event = {"kind": "service", "host": hostname, "service": service_name}
    others = []
    for other in db.session.scalars(
            sa.select(RemediationAction).where(RemediationAction.Enabled.is_(True)).order_by(RemediationAction.Name)):
        if (action is None or other.Id != action.Id) and remediation.covers(other, event):
            others.append({"id": other.Id, "name": other.Name})
    last = db.session.scalar(
        sa.select(RemediationRun).where(RemediationRun.Hostname == hostname, RemediationRun.Service == service_name)
        .order_by(RemediationRun.Received_At.desc(), RemediationRun.Id.desc()).limit(1))
    return {
        "hostname": hostname,
        "service": service_name,
        "enabled": bool(action and action.Enabled),
        "maxRestartsPerHour": action.Max_Runs_Per_Hour if action else DEFAULT_RESTARTS_PER_HOUR,
        "version": action.Version if action else None,
        "actionId": action.Id if action else None,
        "actionType": action_type,
        "unit": unit,
        "canEnable": reason is None,
        "reason": reason,
        "otherActions": others,
        "lastRun": serialize_run(last) if last else None,
    }


@system_bp.get('/remediation/services/<hostname>/<path:service_name>')
@login_required
@require_permission('remediation.view')
def get_service_recovery(hostname, service_name):
    """
    Return one service's "Recover automatically" setting: enabled, maxRestartsPerHour, version
    (null until it exists), actionId, actionType and unit (the server's choice), canEnable with a
    plain reason when false, otherActions (other enabled actions that cover the service) and
    lastRun. 404 when Nagios has not reported the service.
    """
    try:
        if not is_known_service(hostname, service_name):
            return error("Service not found.", 404)
        return success(serialize_service_recovery(hostname, service_name))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not read the service recovery setting.")
        return error("An unexpected error occurred.", 500)


@system_bp.put('/remediation/services/<hostname>/<path:service_name>')
@login_required
@require_permission('remediation.manage')
def update_service_recovery(hostname, service_name):
    """
    Turn "Recover automatically" on or off for one service and set its restart limit.

    JSON: {"enabled": true, "maxRestartsPerHour": 2, "version": 1}. "version" is the current
    version once the setting exists, and is left out until then. Nothing else is accepted: the
    server picks the action type and unit, so a unit, command or path is a 400. This creates,
    updates or disables exactly one action scoped to this host and service, the same row the
    Remediation page shows. Errors: 400 with data.fields, 404, 409 when the version is stale,
    422 when it cannot be switched on (data.reason) or Nagios rejects the config.
    """
    try:
        if not is_known_service(hostname, service_name):
            return error("Service not found.", 404)
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return bad_fields({"body": "Request body must be a JSON object."})
        errors = {key: "Unknown field." for key in data if key not in SERVICE_RECOVERY_FIELDS}
        if type(data.get("enabled")) is not bool:
            errors["enabled"] = "Enabled must be true or false."
        limit = data.get("maxRestartsPerHour")
        if not is_int(limit) or not MIN_RESTARTS_PER_HOUR <= limit <= MAX_RESTARTS_PER_HOUR:
            errors["maxRestartsPerHour"] = (
                f"Restarts per hour must be a whole number from {MIN_RESTARTS_PER_HOUR} to {MAX_RESTARTS_PER_HOUR}.")
        if errors:
            return bad_fields(errors)

        row = find_service_action(hostname, service_name)
        version = data.get("version")
        if (row is None and version is not None) or (row is not None and (not is_int(version) or version != row.Version)):
            return error("This setting was changed by someone else. Reload and try again.", 409)
        if row is None and not data["enabled"]:
            return success(serialize_service_recovery(hostname, service_name), message="Recovery is off.")

        before = serialize_action(row) if row is not None else None
        if data["enabled"]:
            action_type, units, reason = service_recovery_problem(hostname, service_name)
            if reason is not None:
                return error(reason, 422, {"reason": reason})
            if row is None:
                row = RemediationAction(
                    Name=service_action_name(hostname, service_name), Scope_Kind=RemediationScope.SERVICE,
                    Host_Pattern=hostname, Service_Pattern=service_name, Parameters={}, Version=1,
                    Cooldown_Seconds=600, Run_When_Acknowledged=False)
                db.session.add(row)
            # Keep an action or unit an administrator chose on the Remediation page while it is still valid.
            if row.Action_Type is None or row.Action_Type.value != action_type \
                    or (row.Parameters or {}).get("unit") not in units:
                row.Action_Type = RemediationActionType(action_type)
                row.Parameters = {"unit": units[0]}
        row.Enabled = data["enabled"]
        row.Max_Runs_Per_Hour = limit
        row.Updated_By = current_user.UserID
        db.session.flush()
        ok, message = apply_config()
        if not ok:
            db.session.rollback()
            return error(f"The setting could not be applied: {message}", 422)
        if before is not None:
            row.Version += 1
        log_changes(before, serialize_action(row))
        db.session.commit()
        return success(serialize_service_recovery(hostname, service_name), message="Setting saved.")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update the service recovery setting.")
        return error("An unexpected error occurred.", 500)


# ==========================================================
# KILL SWITCH AND RETENTION
# ==========================================================

def serialize_settings(settings):
    """Public shape of the remediation settings."""
    return {
        "enabled": settings.Remediation_Enabled,
        "retentionDays": settings.Remediation_Retention_Days,
        "repeatCount": settings.Remediation_Repeat_Count,
        "repeatWindowHours": settings.Remediation_Repeat_Window_Hours,
    }


def settings_row():
    """The SystemSettings singleton, created with its defaults when missing. The caller commits."""
    settings = db.session.get(SystemSettings, 1)
    if settings is None:
        settings = SystemSettings(Id=1)
        db.session.add(settings)
        db.session.flush()
    return settings


@system_bp.get('/remediation/settings')
@login_required
@require_permission('remediation.view')
def get_remediation_settings():
    """
    Return {"enabled": bool, "retentionDays": int, "repeatCount": int, "repeatWindowHours": int}:
    the kill switch, how long runs are kept, and how many automatic recoveries of the same
    service inside the window send a "repeated" notification.
    """
    try:
        settings = settings_row()
        data = serialize_settings(settings)
        db.session.commit()
        return success(data)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not read the remediation settings.")
        return error("An unexpected error occurred.", 500)


@system_bp.put('/remediation/settings')
@login_required
@require_permission('remediation.manage')
def update_remediation_settings():
    """
    Change the kill switch, the run retention and/or the repeat-recovery limits.

    JSON: {"enabled": false, "retentionDays": 90, "repeatCount": 3, "repeatWindowHours": 24};
    send any of them. "enabled" is true or false; "retentionDays" is a whole number from 7 to
    3650; "repeatCount" from 2 to 20; "repeatWindowHours" from 1 to 168. Unknown fields are errors. The
    switch applies on the consumer's next tick. Each changed value is written to the
    configuration log when audit logging is on. Errors: 400 with data.fields.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return bad_fields({"body": "Request body must be a JSON object."})
    errors = {key: "Unknown field." for key in data if key not in SETTINGS_FIELDS}
    if "enabled" in data and type(data["enabled"]) is not bool:
        errors["enabled"] = "Enabled must be true or false."
    if "retentionDays" in data and (
        not is_int(data["retentionDays"]) or not MIN_RETENTION_DAYS <= data["retentionDays"] <= MAX_RETENTION_DAYS
    ):
        errors["retentionDays"] = (
            f"Retention must be a whole number of days from {MIN_RETENTION_DAYS} to {MAX_RETENTION_DAYS}.")
    if "repeatCount" in data and (
        not is_int(data["repeatCount"]) or not MIN_REPEAT_COUNT <= data["repeatCount"] <= MAX_REPEAT_COUNT
    ):
        errors["repeatCount"] = (
            f"Repeat count must be a whole number from {MIN_REPEAT_COUNT} to {MAX_REPEAT_COUNT}.")
    if "repeatWindowHours" in data and (
        not is_int(data["repeatWindowHours"])
        or not MIN_REPEAT_WINDOW_HOURS <= data["repeatWindowHours"] <= MAX_REPEAT_WINDOW_HOURS
    ):
        errors["repeatWindowHours"] = (
            f"Repeat window must be a whole number of hours from {MIN_REPEAT_WINDOW_HOURS} "
            f"to {MAX_REPEAT_WINDOW_HOURS}.")
    if not errors and not data:
        errors["body"] = "Send at least one setting."
    if errors:
        return bad_fields(errors)
    try:
        settings = settings_row()
        audit = bool(settings.Audit_Logging)
        changes = []
        if "enabled" in data and data["enabled"] != settings.Remediation_Enabled:
            changes.append(("enabled", settings.Remediation_Enabled, data["enabled"]))
            settings.Remediation_Enabled = data["enabled"]
        if "retentionDays" in data and data["retentionDays"] != settings.Remediation_Retention_Days:
            changes.append(("retentionDays", settings.Remediation_Retention_Days, data["retentionDays"]))
            settings.Remediation_Retention_Days = data["retentionDays"]
        if "repeatCount" in data and data["repeatCount"] != settings.Remediation_Repeat_Count:
            changes.append(("repeatCount", settings.Remediation_Repeat_Count, data["repeatCount"]))
            settings.Remediation_Repeat_Count = data["repeatCount"]
        if "repeatWindowHours" in data and data["repeatWindowHours"] != settings.Remediation_Repeat_Window_Hours:
            changes.append(
                ("repeatWindowHours", settings.Remediation_Repeat_Window_Hours, data["repeatWindowHours"]))
            settings.Remediation_Repeat_Window_Hours = data["repeatWindowHours"]
        if audit:
            for name, old, new in changes:
                create_configuration_log(current_user.UserID, "remediation_setting", name, str(old), str(new))
        result = serialize_settings(settings)
        db.session.commit()
        return success(result, message="Settings updated.")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update the remediation settings.")
        return error("An unexpected error occurred.", 500)


# ==========================================================
# CONSUMER HEALTH
# ==========================================================

@system_bp.get('/remediation/health')
@login_required
@require_permission('remediation.view')
def get_remediation_health():
    """
    Return whether automatic recovery is working: lastTickAt, lastError (a fixed sentence),
    stalled (no heartbeat for three poll intervals), backlog and oldestSpoolAgeSeconds (event
    files waiting), runsLast24h, capsHitLast24h, skippedLast24h, droppedTotal and droppedAt.
    Cheap by design: one state row, one folder listing and three counts.
    """
    try:
        from app.scheduler import REMEDIATION_POLL_SECONDS
        return success(remediation.health_snapshot(
            current_app.config["REMEDIATION_SPOOL_DIR"], REMEDIATION_POLL_SECONDS))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not read the remediation health.")
        return error("An unexpected error occurred.", 500)


# ==========================================================
# RUN LOG
# ==========================================================

@system_bp.get('/remediation/runs')
@login_required
@require_permission('remediation.view')
def list_remediation_runs():
    """
    Return the run log, newest first.

    Query: page, per_page (1 to 100), action (action id), host (exact name), outcome (one of the
    outcome values), from and to (YYYY-MM-DD, inclusive). Response: items, page, per_page,
    pages, total.
    """
    try:
        page, per_page = parse_page()
        query = sa.select(RemediationRun)
        action = request.args.get("action")
        if action is not None:
            if not action.isdigit() or int(action) < 1:
                raise ValueError("action must be an action id.")
            query = query.where(RemediationRun.Action_Id == int(action))
        host = request.args.get("host")
        if host is not None:
            if not valid_name(host, 100):
                raise ValueError("host is not a valid host name.")
            query = query.where(RemediationRun.Hostname == host)
        outcome = request.args.get("outcome")
        if outcome is not None:
            try:
                query = query.where(RemediationRun.Outcome == RemediationOutcome(outcome))
            except ValueError:
                raise ValueError("outcome is not a known outcome.")
        start = request.args.get("from")
        if start is not None:
            query = query.where(RemediationRun.Received_At >= parse_day(start, "from"))
        end = request.args.get("to")
        if end is not None:
            query = query.where(RemediationRun.Received_At < parse_day(end, "to") + timedelta(days=1))
    except ValueError as problem:
        return error(str(problem), 400)
    try:
        total = db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))
        rows = db.session.scalars(
            query.order_by(RemediationRun.Received_At.desc(), RemediationRun.Id.desc())
            .limit(per_page).offset((page - 1) * per_page)
        ).all()
        items = []
        for row in rows:
            items.append(serialize_run(row))
        return success({
            "items": items, "page": page, "per_page": per_page,
            "pages": max(1, -(-total // per_page)), "total": total,
        })
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not list remediation runs.")
        return error("An unexpected error occurred.", 500)


@system_bp.get('/remediation/last-runs')
@login_required
@require_permission('remediation.view')
def list_last_remediation_runs():
    """
    Return the newest run for each host and service seen in the last 7 days (at most 500, newest
    first), so a service row can show whether automatic recovery acted on it. Each item has
    runId, hostname, service (null for a host), outcome, notifyState and receivedAt; never output.
    """
    try:
        since = datetime.now(timezone.utc) - timedelta(days=LAST_RUNS_DAYS)
        newest = sa.select(sa.func.max(RemediationRun.Id)).where(
            RemediationRun.Received_At >= since,
        ).group_by(RemediationRun.Hostname, RemediationRun.Service)
        rows = db.session.scalars(
            sa.select(RemediationRun).where(RemediationRun.Id.in_(newest))
            .order_by(RemediationRun.Id.desc()).limit(MAX_LAST_RUNS)
        ).all()
        items = []
        for row in rows:
            items.append({
                "runId": row.Id,
                "hostname": row.Hostname,
                "service": row.Service,
                "outcome": row.Outcome.value,
                "notifyState": row.Notify_State.value if row.Notify_State else None,
                "receivedAt": row.Received_At.isoformat(),
            })
        return success({"items": items})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not list the last remediation runs.")
        return error("An unexpected error occurred.", 500)


@system_bp.get('/remediation/runs/<int:run_id>')
@login_required
@require_permission('remediation.view')
def get_remediation_run(run_id):
    """Return one run including its redacted output."""
    try:
        row = db.session.get(RemediationRun, run_id)
        if row is None:
            return error("Run not found.", 404)
        return success(serialize_run(row, with_output=True))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not read remediation run.")
        return error("An unexpected error occurred.", 500)
