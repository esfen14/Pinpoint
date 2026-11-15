"""Per-user display preferences routes: read and update the logged-in user's theme, time zone, fonts and dashboard settings."""

from flask import jsonify, request
from flask_login import login_required, current_user

from app import db
from app.api.user import user_bp
from app.system_models import UserPreferences  # adjust import path to actual location


def _get_or_create_preferences():
    row = db.session.scalar(
        db.select(UserPreferences).where(UserPreferences.UserID == current_user.UserID)
    )
    if row is None:
        row = UserPreferences(UserID=current_user.UserID)
        db.session.add(row)
        db.session.commit()
    return row


@user_bp.route("/preferences", methods=["GET"])
@login_required
def get_preferences():
    """Return the logged-in user's display preferences as JSON.

    Creates and commits a default preferences row first if the user has none.
    """
    row = _get_or_create_preferences()
    return jsonify(row.to_dict())


@user_bp.route("/preferences", methods=["PUT"])
@login_required
def update_preferences():
    """Update the logged-in user's display preferences and return the saved values.

    Expected JSON body (every key optional; missing keys keep their value):
    {"theme": str, "timeZone": str, "dateTimeFormat": str, "systemFont": str,
     "systemFontSize": int, "dashboardLayout": str, "dashboardRefreshRate": int}

    Commits the change.
    """
    row = _get_or_create_preferences()
    payload = request.get_json(force=True)

    row.Theme = payload.get("theme", row.Theme)
    row.Time_Zone = payload.get("timeZone", row.Time_Zone)
    row.Date_Time_Format = payload.get("dateTimeFormat", row.Date_Time_Format)
    row.System_Font = payload.get("systemFont", row.System_Font)
    row.System_Font_Size = payload.get("systemFontSize", row.System_Font_Size)
    row.Dashboard_Layout = payload.get("dashboardLayout", row.Dashboard_Layout)
    row.Dashboard_Refresh_Rate = payload.get("dashboardRefreshRate", row.Dashboard_Refresh_Rate)

    db.session.commit()
    return jsonify(row.to_dict())