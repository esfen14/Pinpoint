"""
tests/unit/test_forecast.py — The straight-line forecast (app/forecast.py, fit_forecast).

A forecast is an estimate of when a metric reaches its warning or critical threshold. It must
return nothing rather than an alarming number when the series is flat, falling, noisy, short,
reset, or already past the threshold.
"""
import random
from datetime import datetime, timedelta, timezone

from app.forecast import fit_forecast

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def series(start, per_hour, hours=72, step_minutes=15, noise=0.0, seed=1):
    """Samples ending at NOW, rising per_hour percentage points an hour from start."""
    rng = random.Random(seed)
    out = []
    count = int(hours * 60 / step_minutes) + 1
    for i in range(count):
        at = NOW - timedelta(hours=hours) + timedelta(minutes=i * step_minutes)
        value = start + per_hour * (i * step_minutes / 60) + rng.uniform(-noise, noise)
        out.append((at, value))
    return out


class TestRisingSeries:

    def test_crossing_matches_true_value_within_tolerance(self):
        # 50% -> 71% over 72 h at 0.2917 %/h; ends at 71%, warning 80 is 9 points = ~30.9 h away.
        samples = series(50, 21 / 72)
        result = fit_forecast(samples, warning=80, critical=95, now=NOW, window_hours=72)
        assert result is not None
        assert result["kind"] == "warning"
        true_hours = (80 - 71) / (21 / 72)
        actual = (result["crossing_at"] - NOW).total_seconds() / 3600
        assert abs(actual - true_hours) < 0.5
        assert result["sample_count"] == len(samples)
        assert result["window_hours"] == 72
        assert abs(result["slope_per_hour"] - 21 / 72) < 1e-6

    def test_past_warning_forecasts_critical(self):
        samples = series(80, 0.1)  # ends at 87.2
        result = fit_forecast(samples, warning=85, critical=95, now=NOW, window_hours=72)
        assert result["kind"] == "critical"
        assert abs((result["crossing_at"] - NOW).total_seconds() / 3600 - (95 - 87.2) / 0.1) < 0.5

    def test_missing_warning_threshold_uses_critical(self):
        result = fit_forecast(series(50, 0.2), warning=None, critical=90, now=NOW, window_hours=72)
        assert result["kind"] == "critical"

    def test_small_noise_still_forecasts(self):
        result = fit_forecast(series(40, 0.3, noise=0.4), warning=90, critical=95, now=NOW, window_hours=72)
        assert result is not None and result["kind"] == "warning"

    def test_tz_naive_samples_are_read_as_utc(self):
        naive = [(at.replace(tzinfo=None), v) for at, v in series(50, 0.2)]
        assert fit_forecast(naive, warning=90, critical=95, now=NOW, window_hours=72) is not None


class TestNoForecast:

    def test_flat(self):
        assert fit_forecast(series(60, 0.0), warning=80, critical=95, now=NOW, window_hours=72) is None

    def test_falling(self):
        assert fit_forecast(series(70, -0.1), warning=80, critical=95, now=NOW, window_hours=72) is None

    def test_noisy_poor_fit(self):
        assert fit_forecast(series(50, 0.01, noise=8), warning=80, critical=95, now=NOW, window_hours=72) is None

    def test_too_few_samples(self):
        assert fit_forecast(series(50, 0.5, hours=2, step_minutes=60), warning=80, critical=95, now=NOW, window_hours=72) is None

    def test_samples_cover_too_little_of_the_window(self):
        # Plenty of samples but only 3 hours of a 72 hour window: a trend over hours is not a trend.
        assert fit_forecast(series(50, 2.0, hours=3, step_minutes=1), warning=80, critical=95, now=NOW, window_hours=72) is None

    def test_already_past_every_threshold(self):
        assert fit_forecast(series(90, 0.1), warning=80, critical=95 - 10, now=NOW, window_hours=72) is None

    def test_counter_reset_or_cleanup(self):
        # Climbs to 85, a cleanup drops it to 20, then it climbs again: the fit would mislead.
        samples = series(40, 0.5, hours=72)
        half = len(samples) // 2
        reset = samples[:half] + [(at, v - 45) for at, v in samples[half:]]
        assert fit_forecast(reset, warning=90, critical=95, now=NOW, window_hours=72) is None

    def test_crossing_too_far_away(self):
        # About 5 years out: not useful and not trustworthy.
        assert fit_forecast(series(10, 0.003), warning=90, critical=95, now=NOW, window_hours=72) is None

    def test_no_thresholds(self):
        assert fit_forecast(series(50, 0.5), warning=None, critical=None, now=NOW, window_hours=72) is None

    def test_empty(self):
        assert fit_forecast([], warning=80, critical=95, now=NOW, window_hours=72) is None
