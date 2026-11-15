"""
Writes configuration-change log entries: one ActivityLog row plus one
ConfigurationChanges row that records the old and new value of a changed setting.
"""

from app.system_models import ConfigurationChanges
from flask import current_app
import sqlalchemy as sa
from app import db
from datetime import datetime
from app.logging.user_activity import create_user_log


def create_configuration_log(user_id, config_type, parameter_name, old_value, new_value):
    """
    Add an activity log entry and a ConfigurationChanges row for one changed
    setting. It takes the acting user ID, the configuration type, the parameter name
    and its old and new values. It adds both rows to the session but does not
    commit; the caller commits. It returns the (activity log, configuration log)
    pair, or logs the error and returns None when something fails.
    """
    try:
        action = f"{config_type} {parameter_name} from {old_value} {new_value}"
        user_log = create_user_log(user_id, action)

        config_log = ConfigurationChanges(
            Conf_Type = config_type,
            Parameter_Name = parameter_name,
            Old_Value = old_value,
            New_Value = new_value,
            Changed_At = datetime.now(),
            LogID = user_log.LogID
        )
        db.session.add(config_log)

        return user_log, config_log
    except Exception as e:
        current_app.logger.exception(f"Cannot create export log for user {user_id} error: {e}")