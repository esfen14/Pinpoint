"""
forecast.py — Straight-line forecasts of when a metric will reach its threshold.

A forecast is an estimate, not a failure. It is built only from stored performance data
(ServicePerfData joined to ServiceStatus in history.db), never changes a service's Nagios
state, and writes nothing to Nagios configuration. The limit of this module is a linear
least-squares fit over a bounded window: no machine learning and no automatic action.

fit_forecast() is pure (no database) so its arithmetic can be tested directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

# A fit needs enough samples spread over most of the window, and must explain the data.
MIN_SAMPLES = 12
MIN_WINDOW_COVERAGE = 0.5
MIN_R_SQUARED = 0.8
# A single fall larger than this share of the series range is a cleanup or counter reset.
MAX_DROP_SHARE = 0.5
# Further out than this is neither useful nor trustworthy.
MAX_HORIZON_DAYS = 90


def as_utc(value: datetime) -> datetime:
    """Return value as an aware UTC datetime; a naive value is read as UTC (history.db stores UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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

    ordered = sorted(((as_utc(at), float(value)) for at, value in samples), key=lambda pair: pair[0])
    count = len(ordered)
    if count < MIN_SAMPLES:
        return None

    now = as_utc(now)
    span_hours = (ordered[-1][0] - ordered[0][0]).total_seconds() / 3600
    if span_hours < window_hours * MIN_WINDOW_COVERAGE:
        return None

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
