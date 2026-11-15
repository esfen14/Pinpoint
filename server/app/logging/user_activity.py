"""
Writes user activity and audit log entries as ActivityLog rows. create_audit_log only
writes when audit logging is enabled in the system settings.
"""

from app.system_models import ActivityLog
from flask import current_app
import sqlalchemy as sa
from app import db
from datetime import datetime


def create_user_log(user_id, action):
    """
    Add an ActivityLog row for a user action and flush it so the new LogID is
    available. It does not commit; the caller commits. On error it logs the
    exception and re-raises it.
    """
    try:
        user_log = ActivityLog(
            Action_Type = action,
            UserID = user_id
        )

        db.session.add(user_log)
        db.session.flush()

        return user_log
    except Exception as e:
        current_app.logger.exception(f"Cannot create log for user {user_id} error: {e}")
        raise


def create_audit_log(user_id, action):
    """
    Write a user log entry only when audit logging is enabled in the system
    settings. The action text is cut to 255 characters. It returns the new
    ActivityLog row, or None when audit logging is off. It does not commit.
    """
    from app.api.helper.settings_flags import is_audit_logging_enabled
    if not is_audit_logging_enabled():
        return None
    return create_user_log(user_id, action[:255])
