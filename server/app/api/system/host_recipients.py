"""Per-device email alert recipient selection.

Routes
------
GET /system/hosts/<id>/recipients
    Read selections and user choices, with current email eligibility.
PUT /system/hosts/<id>/recipients
    Replace selections and apply the shared Nagios config before committing.
"""
import sqlalchemy as sa
from flask import current_app, request
from flask_login import current_user, login_required

from app import db
from app.api.helper import error, success
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.api.system.device_identity import get_device_or_404
from app.logging.user_activity import create_user_log
from app.network_discovery.device_identity import nagios_host_name
from app.network_discovery.create_host_cfg import config_write_lock
from app.system_models import DeviceState, HostAlertRecipient, User, UserStatus


def serialize_recipients(device):
    """Return selected IDs and user choices; compute eligibility without changing selections."""
    ids = list(db.session.scalars(sa.select(HostAlertRecipient.UserID).where(
        HostAlertRecipient.NetDiscoveryID == device.NetDiscoveryID
    ).order_by(HostAlertRecipient.UserID)))
    users = []
    eligible_ids = set()
    for user in db.session.scalars(sa.select(User).order_by(User.First_Name, User.Last_Name, User.UserID)):
        eligible = user.Status == UserStatus.ACTIVE and bool(user.Receive_Email_Alerts)
        if eligible:
            eligible_ids.add(user.UserID)
        users.append({"id": user.UserID, "name": f"{user.First_Name} {user.Last_Name}",
                      "email": user.Email, "eligible": eligible})
    return {"recipient_ids": ids, "users": users,
            "using_default": not any(user_id in eligible_ids for user_id in ids),
            "editable": device.Device_State not in (DeviceState.RETIRED, DeviceState.MERGED)}


# ==========================================================
# RECIPIENT ROUTES
# ==========================================================
@system_bp.get('/hosts/<int:id>/recipients')
@login_required
@require_permission('system.hosts.alerts')
def get_host_recipients(id):
    """Return the device's selections and eligible/ineligible user choices."""
    device, problem = get_device_or_404(id)
    if problem is not None:
        return problem
    return success(serialize_recipients(device))


@system_bp.put('/hosts/<int:id>/recipients')
@login_required
@require_permission('system.hosts.alerts')
def update_host_recipients(id):
    """Replace recipient choices atomically; empty selections use the default group.

    JSON: {"recipient_ids": [1, 2]}. IDs must be distinct positive user IDs.
    Existing ineligible users may remain selected; only active opted-in users
    are written to Nagios. A failed validation or reload returns 422 and keeps
    the previous choices.
    """
    data = request.get_json()
    if not isinstance(data, dict) or set(data) != {"recipient_ids"}:
        return error("Provide a JSON object containing recipient_ids only.", 400)
    ids = data['recipient_ids']
    if (not isinstance(ids, list) or any(type(value) is not int or value <= 0 for value in ids)
            or len(set(ids)) != len(ids)):
        return error("recipient_ids must be a list of distinct positive integers.", 400)
    device, problem = get_device_or_404(id)
    if problem is not None:
        return problem
    if device.Device_State in (DeviceState.RETIRED, DeviceState.MERGED):
        return error("A retired or merged device cannot have its recipients edited.", 409)
    known_ids = set(db.session.scalars(sa.select(User.UserID).where(User.UserID.in_(ids))))
    if known_ids != set(ids):
        return error("One or more recipients do not exist.", 400)
    try:
        # Serialize generation through commit; the writer uses this re-entrant lock too.
        with config_write_lock:
            before = serialize_recipients(device)['recipient_ids']
            db.session.execute(sa.delete(HostAlertRecipient).where(HostAlertRecipient.NetDiscoveryID == id))
            for user_id in sorted(ids):
                db.session.add(HostAlertRecipient(NetDiscoveryID=id, UserID=user_id))
            db.session.flush()
            from app.network_discovery.create_host_cfg import regenerate_and_apply_config_status
            status, message = regenerate_and_apply_config_status()
            if status == 'failed':
                db.session.rollback()
                return error(f"Alert recipients could not be applied: {message}", 422)
            create_user_log(current_user.UserID,
                            f"Updated alert recipients for {nagios_host_name(device)}: {before} -> {sorted(ids)}")
            db.session.commit()
            return success(serialize_recipients(device), message="Alert recipients saved.")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update host alert recipients.")
        return error("Unable to save alert recipients.", 500)
