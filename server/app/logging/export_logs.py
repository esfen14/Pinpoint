"""
Writes an export log entry when a report is exported: an ActivityLog row plus an
ExportLog row with the report type, format and date range.
"""

from app.system_models import ExportLog
from flask import current_app
import sqlalchemy as sa
from app import db
from datetime import datetime, timezone
from app.logging.user_activity import create_user_log


def create_export_log(user_id, report_type, report_format, start_date, end_date):
    """
    Add an activity log entry and an ExportLog row for one report export. It takes
    the acting user ID, the report type and format, and the start and end dates of
    the report. It adds both rows to the session but does not commit; the caller
    commits. It returns the (activity log, export log) pair, or logs the error and
    returns None when something fails.
    """
    try:
        action = f"Export {report_type}"
        user_log = create_user_log(user_id, action)

        export_log = ExportLog(
            Report_Type = report_type,
            Export_Format = report_format,
            Start_Date= start_date,
            End_Date= end_date,
            LogID = user_log.LogID
        )

        db.session.add(export_log)

        return user_log, export_log
    except Exception as e:
        current_app.logger.exception(f"Cannot create export log for user {user_id} error: {e}")

