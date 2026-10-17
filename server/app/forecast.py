"""
forecast.py — Straight-line forecasts of when a metric will reach its threshold.

A forecast is an estimate, not a failure. It is built only from stored performance data
(ServicePerfData joined to ServiceStatus in history.db), never changes a service's Nagios
state, and writes nothing to Nagios configuration. The limit of this module is a linear
least-squares fit over a bounded window: no machine learning and no automatic action.

fit_forecast() is pure (no database) so its arithmetic can be tested directly.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

import sqlalchemy as sa

from app import db
from app.history_models import ServicePerfData, ServiceStatus
from app.network_discovery.device_identity import unchecked_host_names
from app.system_models import ResourceForecast

# A fit needs enough samples spread over most of the window, and must explain the data.
MIN_SAMPLES = 12
MIN_WINDOW_COVERAGE = 0.5
MIN_R_SQUARED = 0.8
# A single fall larger than this share of the series range is a cleanup or counter reset.
MAX_DROP_SHARE = 0.5
# Further out than this is neither useful nor trustworthy.
MAX_HORIZON_DAYS = 90
# Hours of history one fit looks at. Samples are averaged per hour, so a series is at most this many points.
WINDOW_HOURS = 72
# Most host, service and metric series one run forecasts; the rest wait for a later run.
MAX_SERIES_PER_RUN = 500
# Scheduler traversal state; a process restart begins at the first eligible series.
# max_instances=1 prevents concurrent job runs from racing this cursor.
last_series: Optional[tuple[str, str, str]] = None
# Metrics forecast first: NCPA disk used percent and memory percent. Nothing else is read.
METRIC_FILTER = sa.or_(
    ServicePerfData.Metric.like("disk/%/used_percent"),
    ServicePerfData.Metric == "memory/virtual/percent",
)


def as_utc(value: datetime) -> datetime:
    """Return value as an aware UTC datetime; a naive value is read as UTC (history.db stores UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def enough_data(samples: list[tuple[datetime, float]], window_hours: float) -> bool:
    """True when there are enough samples, spread over enough of the window, to attempt a fit."""
    if len(samples) < MIN_SAMPLES:
        return False
    times = [as_utc(at) for at, _ in samples]
    return (max(times) - min(times)).total_seconds() / 3600 >= window_hours * MIN_WINDOW_COVERAGE


def fit_forecast(
    samples: list[tuple[datetime, float]],
    warning: Optional[float],
    critical: Optional[float],
    now: datetime,
    window_hours: float,
) -> Optional[dict]:
    """
    Fit a straight line to (time, value) samples and estimate when it next crosses a threshold.

    Returns None (no forecast) when there are too few samples or they cover too little of the
    window, the trend is flat or falling, the fit is poor, a cleanup or reset is in the data,
    every threshold is already reached, or the crossing is more than MAX_HORIZON_DAYS away.

    Otherwise returns {"kind": "warning"|"critical", "threshold", "crossing_at" (aware UTC),
    "slope_per_hour", "r_squared", "sample_count", "window_hours", "current_value"} for the
    nearest threshold the latest value has not yet reached.
    """
    thresholds = sorted(
        (("warning", warning), ("critical", critical)),
        key=lambda pair: (pair[1] is None, pair[1]),
    )
    thresholds = [(kind, value) for kind, value in thresholds if value is not None]
    if not samples or not thresholds:
        return None

    if not enough_data(samples, window_hours):
        return None
    ordered = sorted(((as_utc(at), float(value)) for at, value in samples), key=lambda pair: pair[0])
    count = len(ordered)
    now = as_utc(now)

    values = [value for _, value in ordered]
    # A cleanup or counter reset shows as one large fall; the line through it would mislead.
    value_range = max(values) - min(values)
    biggest_fall = max((values[i - 1] - values[i] for i in range(1, count)), default=0.0)
    if value_range <= 0 or biggest_fall > MAX_DROP_SHARE * value_range:
        return None

    # Least squares on hours since the first sample keeps the numbers small and exact enough.
    origin = ordered[0][0]
    xs = [(at - origin).total_seconds() / 3600 for at, _ in ordered]
    mean_x = sum(xs) / count
    mean_y = sum(values) / count
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    syy = sum((y - mean_y) ** 2 for y in values)
    if sxx <= 0 or syy <= 0:
        return None
    slope = sxy / sxx
    if slope <= 0:
        return None
    r_squared = (sxy * sxy) / (sxx * syy)
    if r_squared < MIN_R_SQUARED:
        return None

    intercept = mean_y - slope * mean_x
    latest = values[-1]
    now_x = (now - origin).total_seconds() / 3600
    fitted_now = intercept + slope * now_x
    for kind, threshold in thresholds:
        if latest >= threshold:
            continue
        hours_left = (threshold - fitted_now) / slope
        if hours_left <= 0 or hours_left > MAX_HORIZON_DAYS * 24:
            return None
        return {
            "kind": kind,
            "threshold": threshold,
            "crossing_at": now + timedelta(hours=hours_left),
            "slope_per_hour": slope,
            "r_squared": r_squared,
            "sample_count": count,
            "window_hours": window_hours,
            "current_value": latest,
        }
    return None


# ==========================================================
# JOB: forecast every bounded series and store the latest
# ==========================================================

def compute_forecasts() -> int:
    """
    Recompute forecasts for disk and memory percent metrics and replace the stored set; return
    how many forecasts were stored (series too new to forecast are stored too, as "insufficient",
    but not counted). Uses a fixed number of queries however many services exist: one for
    the series list (capped at MAX_SERIES_PER_RUN, paused/retired/merged devices excluded), one
    for hourly averages of exactly those series, then one delete and one batch insert.
    Successive runs rotate through eligible series using a process-local cursor, advanced
    only after a successful commit. Restarting the scheduler restarts traversal. Commits;
    rolls back and re-raises on failure. Reads history.db only; never writes to Nagios.
    """
    global last_series

    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=WINDOW_HOURS)).replace(tzinfo=None)
    skipped = unchecked_host_names()

    series_columns = (ServiceStatus.Hostname, ServiceStatus.Service, ServicePerfData.Metric)
    ordering = list(series_columns)
    if last_series is not None:
        # Put the suffix after the cursor first, then wrap to the beginning in the same query.
        ordering.insert(0, sa.case((sa.tuple_(*series_columns) > last_series, 0), else_=1))
    series_query = (
        sa.select(*series_columns)
        .join(ServiceStatus, ServicePerfData.ServiceStatusID == ServiceStatus.ServiceStatusID)
        .where(ServiceStatus.Timestamp >= start, METRIC_FILTER)
        .group_by(ServiceStatus.Hostname, ServiceStatus.Service, ServicePerfData.Metric)
        .order_by(*ordering)
        .limit(MAX_SERIES_PER_RUN)
    )
    if skipped:
        series_query = series_query.where(ServiceStatus.Hostname.notin_(skipped))
    selected = [tuple(row) for row in db.session.execute(series_query).all()]

    samples = defaultdict(list)
    latest = {}
    if selected:
        hour = sa.func.strftime("%Y-%m-%d %H", ServiceStatus.Timestamp)
        hourly = (
            sa.select(
                ServiceStatus.Hostname, ServiceStatus.Service, ServicePerfData.Metric,
                sa.type_coerce(sa.func.min(ServiceStatus.Timestamp), sa.DateTime()).label("at"),
                sa.func.avg(ServicePerfData.Measured_Value).label("value"),
                sa.func.max(ServicePerfData.Warning_Threshold).label("warning"),
                sa.func.max(ServicePerfData.Critical_Threshold).label("critical"),
                sa.func.max(ServicePerfData.Unit).label("unit"),
            )
            .join(ServiceStatus, ServicePerfData.ServiceStatusID == ServiceStatus.ServiceStatusID)
            .where(
                ServiceStatus.Timestamp >= start, METRIC_FILTER,
                sa.tuple_(*series_columns).in_(selected),
            )
            .group_by(ServiceStatus.Hostname, ServiceStatus.Service, ServicePerfData.Metric, hour)
            .order_by(sa.text("at"))
        )
        for row in db.session.execute(hourly).all():
            key = (row.Hostname, row.Service, row.Metric)
            samples[key].append((row.at, row.value))
            latest[key] = row  # ordered by time, so the last row wins

    stored = []
    for key, points in samples.items():
        last = latest[key]
        result = fit_forecast(points, last.warning, last.critical, now, WINDOW_HOURS)
        if result is None:
            if not enough_data(points, WINDOW_HOURS):
                stored.append({
                    "Hostname": key[0], "Service": key[1], "Metric": key[2], "Kind": "insufficient",
                    "Sample_Count": len(points), "Window_Hours": WINDOW_HOURS, "Unit": last.unit,
                    "Computed_At": now.replace(tzinfo=None),
                })
            continue
        stored.append({
            "Hostname": key[0], "Service": key[1], "Metric": key[2], "Kind": result["kind"],
            "Threshold": result["threshold"], "Crossing_At": result["crossing_at"].replace(tzinfo=None),
            "Slope_Per_Hour": result["slope_per_hour"], "R_Squared": result["r_squared"],
            "Sample_Count": result["sample_count"], "Window_Hours": result["window_hours"],
            "Current_Value": result["current_value"], "Unit": last.unit,
            "Computed_At": now.replace(tzinfo=None),
        })

    try:
        db.session.execute(sa.delete(ResourceForecast))
        if stored:
            # Core executemany with identical columns avoids one ORM insert per alternating
            # forecast/insufficient row. Explicit NULLs keep waiting-series fields empty.
            nullable = dict.fromkeys((
                "Threshold", "Crossing_At", "Slope_Per_Hour", "R_Squared", "Current_Value",
            ))
            db.session.execute(
                sa.insert(ResourceForecast.__table__), [{**nullable, **row} for row in stored],
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    last_series = selected[-1] if selected else None
    return sum(1 for row in stored if row["Kind"] != "insufficient")

