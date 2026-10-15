"""Manage Nagios notification escalation ranges and existing recipient choices.

Routes
------
GET /system/escalations
    List saved ranges with eligibility, groups and host scope choices.
POST /system/escalations
    Create a range after shared Nagios validation and apply.
PUT /system/escalations/<id>
    Replace a range after shared Nagios validation and apply.
DELETE /system/escalations/<id>
    Delete a range after shared Nagios validation and apply.
"""
import sqlalchemy as sa
from flask import current_app, request
from flask_login import current_user, login_required

from app import db
from app.api.helper import error, success
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.logging.configuration_changes import create_configuration_log
from app.network_discovery.create_host_cfg import config_write_lock
from app.network_discovery.device_identity import nagios_host_name
from app.network_discovery.recipient_groups import recipient_groups
from app.system_models import DeviceState, Escalation, NetworkDiscovery, SystemSettings


def escalation_hosts():
    """Return currently generated device choices without touching the transaction."""
    return {row.NetDiscoveryID: nagios_host_name(row) for row in db.session.scalars(
        sa.select(NetworkDiscovery).where(
            NetworkDiscovery.Include_Device_In_Scanning.is_(True),
            NetworkDiscovery.Device_State.in_((DeviceState.ACTIVE, DeviceState.MISSING, DeviceState.ADDRESS_UNKNOWN))
        ).order_by(NetworkDiscovery.NetDiscoveryID))}


def serialize_escalation(row, groups, hosts):
    """Include a plain-language reason for a saved but inactive escalation."""
    reason = ''
    if not groups.get(row.Contact_Group):
        reason = 'The contact_group has no eligible members. Active users must have email alerts enabled.'
    elif row.HostID is not None and row.HostID not in hosts:
        reason = 'The scoped host is no longer monitored. Choose another host to activate this escalation.'
    return dict(id=row.EscalationID, first_notification=row.First_Notification,
                last_notification=row.Last_Notification, interval_minutes=row.Interval_Minutes,
                contact_group=row.Contact_Group, host_id=row.HostID,
                active=not reason, reason=reason)


def validate_escalation(data, groups, hosts):
    """Validate exact JSON fields, integer ranges and existing eligible group/scope."""
    fields = {'first_notification', 'last_notification', 'interval_minutes', 'contact_group', 'host_id'}
    if not isinstance(data, dict) or set(data) != fields:
        return 'Provide first_notification, last_notification, interval_minutes, contact_group and host_id only.'
    first, last = data['first_notification'], data['last_notification']
    if type(first) is not int or not 1 <= first <= 10000:
        return 'first_notification must be an integer from 1 to 10000.'
    if type(last) is not int or not first <= last <= 10000:
        return 'last_notification must be an integer from first_notification to 10000; first_notification cannot exceed it.'
    interval = data['interval_minutes']
    if type(interval) is not int or not 0 <= interval <= 1440:
        return 'interval_minutes must be an integer from 0 to 1440 minutes.'
    group = data['contact_group']
    if not isinstance(group, str) or group not in groups:
        return 'contact_group does not exist. Reload the available groups.'
    if not groups[group]:
        return 'contact_group has no eligible members. Active users must have email alerts enabled.'
    host = data['host_id']
    if host is not None and (type(host) is not int or host not in hosts):
        return 'host_id must identify a currently monitored device, or be null for all hosts and services.'
    return None


def apply_escalation_change(id=None, deleting=False):
    """Validate and mutate under the shared writer lock; apply before commit.

    Failure restores database choices, while the shared writer restores files on
    validation/reload failure. A commit failure also regenerates the old config.
    """
    data = None if deleting else request.get_json()
    with config_write_lock:
        applied = False
        try:
            _, groups = recipient_groups()
            hosts = escalation_hosts()
            row = db.session.get(Escalation, id) if id is not None else None
            if id is not None and row is None:
                return error('Escalation not found.', 404)
            if not deleting:
                problem = validate_escalation(data, groups, hosts)
                if problem:
                    return error(problem, 400)
            before = serialize_escalation(row, groups, hosts) if row else None
            if deleting:
                db.session.delete(row)
            else:
                if row is None:
                    row = Escalation()
                    db.session.add(row)
                row.First_Notification = data['first_notification']
                row.Last_Notification = data['last_notification']
                row.Interval_Minutes = data['interval_minutes']
                row.Contact_Group = data['contact_group']
                row.HostID = data['host_id']
            db.session.flush()
            from app.network_discovery.create_host_cfg import regenerate_and_apply_config_status
            status, message = regenerate_and_apply_config_status()
            if status == 'failed':
                db.session.rollback()
                return error(f'Escalation could not be applied: {message}', 422)
            applied = status == 'applied'
            result = None if deleting else serialize_escalation(row, groups, hosts)
            settings = db.session.get(SystemSettings, 1)
            if settings is None or settings.Audit_Logging:
                create_configuration_log(current_user.UserID, 'escalation', str(row.EscalationID),
                                         str(before)[:100], str(result)[:100])
            db.session.commit()
            return success(result, message='Escalation deleted.' if deleting else 'Escalation saved.')
        except Exception:
            db.session.rollback()
            current_app.logger.error('Unable to save escalation.')
            if applied:
                try:
                    from app.network_discovery.create_host_cfg import regenerate_and_apply_config_status
                    status, _ = regenerate_and_apply_config_status()
                    if status == 'failed':
                        current_app.logger.error('Could not restore escalation configuration after a database failure.')
                except Exception:
                    db.session.rollback()
                    current_app.logger.error('Could not restore escalation configuration after a database failure.')
            return error('Unable to save escalation.', 500)


# ==========================================================
# ESCALATION ROUTES
# ==========================================================
@system_bp.get('/escalations')
@login_required
@require_permission('settings.system')
def get_escalations():
    """Return ranges, existing recipient groups with eligible counts, and host choices."""
    _, groups = recipient_groups()
    hosts = escalation_hosts()
    return success({
        'items': [serialize_escalation(row, groups, hosts) for row in db.session.scalars(
            sa.select(Escalation).order_by(Escalation.EscalationID))],
        'groups': [{'name': name, 'member_count': len(members)} for name, members in groups.items()],
        'hosts': [{'id': id, 'name': name} for id, name in hosts.items()],
    })


@system_bp.post('/escalations')
@login_required
@require_permission('settings.system')
def create_escalation():
    """Create a range: JSON {first_notification: 2, last_notification: 5,
    interval_minutes: 10, contact_group: "system_users", host_id: null}.
    """
    return apply_escalation_change()


@system_bp.put('/escalations/<int:id>')
@login_required
@require_permission('settings.system')
def update_escalation(id):
    """Replace a range: JSON {first_notification: 2, last_notification: 5,
    interval_minutes: 10, contact_group: "system_users", host_id: 1}.
    """
    return apply_escalation_change(id)


@system_bp.delete('/escalations/<int:id>')
@login_required
@require_permission('settings.system')
def delete_escalation(id):
    """Remove a saved range, validating and applying config before committing."""
    return apply_escalation_change(id, deleting=True)
