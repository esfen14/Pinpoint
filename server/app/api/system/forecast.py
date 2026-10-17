"""
forecast.py — Read route for resource forecasts (disk and memory "running out soon").

A forecast is an estimate from a straight-line fit of stored performance data (app/forecast.py).
It is for display only and never changes a service's Nagios state.

Routes
------
GET /system/forecast
    The stored forecasts, soonest crossing first, each with the window, sample count and slope
    behind it, plus the series that do not have enough history yet. Query: hostname (optional), limit (1-500, default 100).
"""

import sqlalchemy as sa
from flask_login import login_required
from flask import request

from app import db
from app.api.helper import success, error
from app.api.helper.database_access.permissions import user_has_permission
from app.api.system import system_bp
from app.api.system.network_health import utc_isoformat
from app.system_models import ResourceForecast

DEFAULT_LIMIT = 100
MAX_LIMIT = 500
# Everyone who can see the Dashboard or the service table may see the forecasts shown there.
VIEW_PERMISSIONS = ("system.dashboard", "system.services")


# ==========================================================
# FORECAST LIST
# ==========================================================

@system_bp.route("/forecast", methods=["GET"])
@login_required
def list_forecasts():
    """
    Return the stored forecasts sorted by soonest estimated crossing.

    Response: {"success": true, "data": {"insufficient": [{hostname, service_name, metric,
    sample_count, window_hours}], "forecasts": [{hostname, service_name, metric, kind
    ("warning" or "critical"), threshold, crossing_at, slope_per_hour, r_squared, sample_count,
    window_hours, current_value, unit, computed_at}]}}. Timestamps are ISO-8601 with a UTC offset.
    An empty list means nothing is on course to cross a threshold (or there is not enough data).
    """
    if not any(user_has_permission(name) for name in VIEW_PERMISSIONS):
        return error("User has no permission.", 403)

    raw_limit = request.args.get("limit", str(DEFAULT_LIMIT))
    if not raw_limit.isdigit() or not 1 <= int(raw_limit) <= MAX_LIMIT:
        return error(f"limit must be a whole number from 1 to {MAX_LIMIT}.", 400)

    hostname = request.args.get("hostname", "").strip()
    limit = int(raw_limit)

    def stored(*conditions):
        """Forecast rows matching the conditions (and the optional host filter), soonest first, capped."""
        query = sa.select(ResourceForecast).where(*conditions)
        if hostname:
            query = query.where(ResourceForecast.Hostname == hostname)
        query = query.order_by(ResourceForecast.Crossing_At, ResourceForecast.ForecastID)
        return db.session.scalars(query.limit(limit)).all()

    rows = stored(ResourceForecast.Kind != "insufficient")
    waiting = stored(ResourceForecast.Kind == "insufficient")

    forecasts = []
    for row in rows:
        forecasts.append({
            "hostname": row.Hostname,
            "service_name": row.Service,
            "metric": row.Metric,
            "kind": row.Kind,
            "threshold": row.Threshold,
            "crossing_at": utc_isoformat(row.Crossing_At),
            "slope_per_hour": row.Slope_Per_Hour,
            "r_squared": row.R_Squared,
            "sample_count": row.Sample_Count,
            "window_hours": row.Window_Hours,
            "current_value": row.Current_Value,
            "unit": row.Unit,
            "computed_at": utc_isoformat(row.Computed_At),
        })
    insufficient = []
    for row in waiting:
        insufficient.append({
            "hostname": row.Hostname,
            "service_name": row.Service,
            "metric": row.Metric,
            "sample_count": row.Sample_Count,
            "window_hours": row.Window_Hours,
        })
    return success({"forecasts": forecasts, "insufficient": insufficient})
