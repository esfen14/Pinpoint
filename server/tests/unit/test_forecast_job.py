"""
tests/unit/test_forecast_job.py — The forecast job (app/forecast.py, compute_forecasts).

It reads hourly-averaged disk and memory percent history, keeps only the latest forecast per
host, service and metric, skips paused devices, caps the services per run, and keeps a fixed
number of queries however many services exist. It never touches Nagios.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import sqlalchemy as sa
import pytest

from app import db, forecast
from app.history_models import ServicePerfData, ServiceStatus
from app.nagios import commands as nagios_commands
from app.system_models import ResourceForecast
from tests.support.seed_helpers import _make_service, _make_service_perf
from tests.unit.test_create_host_cfg import make_device

DISK = "disk/logical/|/used_percent"
MEMORY = "memory/virtual/percent"


@pytest.fixture(autouse=True)
def reset_forecast_cursor(monkeypatch):
    """Each test starts a new scheduler's traversal of eligible series."""
    monkeypatch.setattr(forecast, "last_series", None, raising=False)


def seed_series(db_session, host, service, metric, start, per_hour, hours=72, warn=80.0, crit=95.0):
    """Hourly samples ending an hour ago, rising per_hour points an hour."""
    now = datetime.now(timezone.utc)
    for i in range(hours):
        at = now - timedelta(hours=hours - i)
        row = _make_service(db_session, host, service, ts=at, check_command="pinpoint_nd_ncpa")
        _make_service_perf(db_session, row, metric, start + per_hour * i, "%", warn=warn, crit=crit)
    db_session.session.commit()


def rows():
    return db.session.scalars(sa.select(ResourceForecast).order_by(ResourceForecast.Hostname)).all()


class TestStoring:

    def test_rising_disk_is_stored_with_its_basis(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.3)  # ends 61.0

        assert forecast.compute_forecasts() == 1

        row, = rows()
        assert (row.Hostname, row.Service, row.Metric, row.Kind) == ("web-01", "ncpa-disk-5693", DISK, "warning")
        assert row.Threshold == 80.0 and row.Unit == "%"
        assert 70 <= row.Sample_Count <= 72 and row.Window_Hours == forecast.WINDOW_HOURS
        assert abs(row.Slope_Per_Hour - 0.3) < 0.01
        hours = (row.Crossing_At.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 3600
        assert abs(hours - (80 - 61.7) / 0.3) < 3

    def test_memory_is_forecast_and_other_metrics_are_ignored(self, db_session):
        seed_series(db_session, "web-01", "ncpa-memory-5693", MEMORY, 30.0, 0.4)
        seed_series(db_session, "web-01", "ncpa-cpu-5693", "cpu/percent", 10.0, 0.5)

        forecast.compute_forecasts()

        assert [r.Metric for r in rows()] == [MEMORY]

    def test_flat_series_stores_nothing(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 50.0, 0.0)
        assert forecast.compute_forecasts() == 0
        assert rows() == []

    def test_samples_older_than_the_window_are_ignored(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.1, hours=200)
        # Only the last 72 hours count, so the sample count is the window, not 200.
        forecast.compute_forecasts()
        assert rows()[0].Sample_Count <= forecast.WINDOW_HOURS


class TestNotEnoughData:

    def test_a_new_series_is_recorded_as_waiting_not_forecast(self, db_session):
        seed_series(db_session, "new-01", "ncpa-disk-5693", DISK, 40.0, 0.3, hours=5)

        assert forecast.compute_forecasts() == 0

        row, = rows()
        assert (row.Hostname, row.Kind, row.Sample_Count) == ("new-01", "insufficient", 5)
        assert row.Crossing_At is None and row.Slope_Per_Hour is None

    def test_a_flat_series_with_enough_data_is_not_recorded(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 50.0, 0.0)
        forecast.compute_forecasts()
        assert rows() == []

    def test_waiting_becomes_a_forecast_once_data_builds_up(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.3, hours=5)
        forecast.compute_forecasts()
        assert [r.Kind for r in rows()] == ["insufficient"]

        db_session.session.execute(sa.delete(ServicePerfData))
        db_session.session.execute(sa.delete(ServiceStatus))
        db_session.session.commit()
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.3)
        forecast.compute_forecasts()

        assert [r.Kind for r in rows()] == ["warning"]


class TestReplacement:

    def test_a_second_run_keeps_one_row_per_series(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.3)
        forecast.compute_forecasts()
        first = rows()[0].Computed_At
        forecast.compute_forecasts()

        assert len(rows()) == 1
        assert rows()[0].Computed_At >= first

    def test_a_forecast_that_no_longer_holds_is_removed(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.3)
        forecast.compute_forecasts()
        assert len(rows()) == 1

        db_session.session.execute(sa.delete(ServicePerfData))
        db_session.session.execute(sa.delete(ServiceStatus))
        db_session.session.commit()
        forecast.compute_forecasts()

        assert rows() == []


class TestScope:

    def test_paused_device_has_no_forecast(self, db_session, admin_user):
        paused = make_device(db_session, admin_user, "old-nas", "192.168.130.20")
        paused.Include_Device_In_Scanning = False
        make_device(db_session, admin_user, "live-nas", "192.168.130.21")
        db_session.session.commit()
        for host in ("old-nas", "live-nas"):
            seed_series(db_session, host, "ncpa-disk-5693", DISK, 40.0, 0.3)

        forecast.compute_forecasts()

        assert [r.Hostname for r in rows()] == ["live-nas"]

    def test_service_cap_bounds_a_run(self, db_session):
        for n in range(5):
            seed_series(db_session, f"host-{n}", "ncpa-disk-5693", DISK, 40.0, 0.3, hours=24 * 3)
        with patch.object(forecast, "MAX_SERIES_PER_RUN", 2):
            assert forecast.compute_forecasts() == 2
        assert len(rows()) == 2

    def test_never_touches_nagios_or_history(self, db_session):
        seed_series(db_session, "web-01", "ncpa-disk-5693", DISK, 40.0, 0.3)
        before = db.session.scalar(sa.select(sa.func.count()).select_from(ServiceStatus))
        with patch.object(nagios_commands, "_write_line") as pipe,              patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status") as regenerate:
            forecast.compute_forecasts()
        pipe.assert_not_called()
        regenerate.assert_not_called()
        assert db.session.scalar(sa.select(sa.func.count()).select_from(ServiceStatus)) == before


class TestCost:

    @staticmethod
    def count_queries(app):
        statements = []

        def record(conn, cursor, statement, *args):
            statements.append(statement)

        engines = [db.engines[None], db.engines["history"]]
        for engine in engines:
            sa.event.listen(engine, "before_cursor_execute", record)
        try:
            forecast.compute_forecasts()
        finally:
            for engine in engines:
                sa.event.remove(engine, "before_cursor_execute", record)
        return len(statements)

    def test_query_count_does_not_grow_with_services(self, app, db_session):
        for n in range(3):
            seed_series(db_session, f"host-{n}", "ncpa-disk-5693", DISK, 40.0, 0.3)
        small = self.count_queries(app)

        for n in range(3, 25):
            seed_series(db_session, f"host-{n}", "ncpa-disk-5693", DISK, 40.0, 0.3)
        large = self.count_queries(app)

        assert large == small

    def test_mixed_row_shapes_keep_a_constant_statement_count(self, app, db_session):
        now = datetime.now(timezone.utc)

        def seed_mixed(first, stop):
            for n in range(first, stop):
                for hour in (range(71) if n % 2 == 0 else (0, 70)):
                    row = _make_service(
                        db_session, "same-host", f"disk-{n:03}",
                        ts=now - timedelta(hours=71 - hour), check_command="pinpoint_nd_ncpa",
                    )
                    _make_service_perf(db_session, row, DISK, 40 + .3 * hour, "%", warn=80, crit=95)
            db_session.session.commit()

        seed_mixed(0, 6)
        small = self.count_queries(app)
        seed_mixed(6, 20)
        large = self.count_queries(app)

        assert small == large == 5
        assert len(rows()) == 20
        assert sum(row.Kind == "insufficient" for row in rows()) == 10
        assert all(row.Crossing_At is None for row in rows() if row.Kind == "insufficient")

    def test_hourly_query_fetches_only_selected_service_and_metric_tuples(self, db_session, monkeypatch):
        for service, metric in (("disk-a", DISK), ("disk-a", MEMORY), ("disk-b", DISK)):
            seed_series(db_session, "same-host", service, metric, 40, .3)
        monkeypatch.setattr(forecast, "MAX_SERIES_PER_RUN", 1)
        execute = db.session.execute
        fetched = []

        def record(statement, *args, **kwargs):
            result = execute(statement, *args, **kwargs)
            if isinstance(statement, sa.sql.Select) and "avg(" in str(statement).lower():
                data = result.all()
                fetched.extend(data)
                result = type("Rows", (), {"all": lambda self: data})()
            return result

        with patch.object(db.session, "execute", side_effect=record):
            forecast.compute_forecasts()

        assert fetched
        assert {(row.Hostname, row.Service, row.Metric) for row in fetched} == {
            ("same-host", "disk-a", DISK),
        }
        assert len(fetched) <= 73


class TestRotation:

    def test_runs_cover_excess_series_and_wrap(self, db_session, monkeypatch):
        for n in range(5):
            seed_series(db_session, "same-host", f"disk-{n}", DISK, 40, .3)
        monkeypatch.setattr(forecast, "MAX_SERIES_PER_RUN", 2)

        batches = []
        for _ in range(3):
            assert forecast.compute_forecasts() == 2
            batches.append({row.Service for row in rows()})

        assert batches == [{"disk-0", "disk-1"}, {"disk-2", "disk-3"}, {"disk-4", "disk-0"}]

    def test_non_forecast_series_also_advance_the_cursor(self, db_session, monkeypatch):
        seed_series(db_session, "same-host", "a-flat", DISK, 40, 0)
        seed_series(db_session, "same-host", "b-rising", DISK, 40, .3)
        monkeypatch.setattr(forecast, "MAX_SERIES_PER_RUN", 1)

        assert forecast.compute_forecasts() == 0
        assert rows() == []
        assert forecast.compute_forecasts() == 1
        assert rows()[0].Service == "b-rising"

    def test_commit_failure_preserves_rows_and_retries_the_same_batch(self, db_session, monkeypatch):
        for n in range(3):
            seed_series(db_session, "same-host", f"disk-{n}", DISK, 40, .3)
        monkeypatch.setattr(forecast, "MAX_SERIES_PER_RUN", 1)
        forecast.compute_forecasts()
        cursor = forecast.last_series
        before = [(row.Service, row.Computed_At) for row in rows()]

        with patch.object(db.session, "commit", side_effect=RuntimeError("commit failed")):
            with pytest.raises(RuntimeError, match="commit failed"):
                forecast.compute_forecasts()

        assert forecast.last_series == cursor
        assert [(row.Service, row.Computed_At) for row in rows()] == before
        assert forecast.compute_forecasts() == 1
        assert rows()[0].Service == "disk-1"


class TestNcpaResourceIdentity:

    @pytest.fixture(autouse=True)
    def stable_window(self, monkeypatch):
        """Keep the first seeded hour inside the window instead of racing its boundary."""
        now = datetime.now(timezone.utc)
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now if tz else now.replace(tzinfo=None)
        monkeypatch.setattr(forecast, 'datetime', Clock)

    @pytest.mark.parametrize('service,command,metric', [
        ('ncpa-memory-5693-tcp', 'pinpoint_nd_ncpa', 'percent'),
        ('ncpa-memory-5693-tcp', 'pinpoint_nd_ncpa', "'percent'"),
        ('ncpa-disk_root-5693-tcp', 'pinpoint_nd_ncpa', 'used_percent'),
        ('ncpa-disk_root-5693-tcp', 'pinpoint_nd_ncpa', '"used_percent"'),
        ('ncpa-memory-5693-tcp', None, 'percent'),
        ('ncpa-disk_root-5693-tcp', None, 'used_percent'),
        ('custom-memory', 'check_ncpa!memory/virtual/percent', 'percent'),
        ('custom-disk', 'check_ncpa!disk/logical/|/used_percent', 'used_percent'),
        ('custom-memory', 'pinpoint_nd_ncpa', MEMORY),
        ('custom-disk', 'pinpoint_nd_ncpa', DISK),
    ])
    def test_numeric_forecast_for_canonical_history(self, db_session, service, command, metric):
        seed_series(db_session, 'real-label', service, metric, 40, .3)
        db_session.session.execute(sa.update(ServiceStatus).values(Check_Command=command))
        db_session.session.commit()
        assert forecast.compute_forecasts() == 1
        row, = rows()
        assert (row.Service, row.Metric, row.Kind, row.Threshold) == (service, metric, 'warning', 80)
        assert row.Sample_Count == 72
        assert row.Current_Value == pytest.approx(61.3)
        assert row.Slope_Per_Hour == pytest.approx(.3)
        assert row.R_Squared == pytest.approx(1)
        hours = (row.Crossing_At.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds()/3600
        assert hours == pytest.approx((80-61.6)/.3, abs=.02)

    @pytest.mark.parametrize('service,command,metric', [
        ('ncpa-memory-5693-tcp', 'check_http', MEMORY),
        ('ncpa-disk_root-5693-tcp', 'check_snmp', DISK),
        ('ncpa-swap-5693-tcp', 'pinpoint_nd_ncpa', 'percent'),
        ('ncpa-disk_read-5693-tcp', 'pinpoint_nd_ncpa', 'used_percent'),
        ('ncpa-disk_io-5693-tcp', 'pinpoint_nd_ncpa', 'used_percent'),
        ('unknown', 'pinpoint_nd_ncpa', 'percent'),
        ('unknown', 'pinpoint_nd_ncpa', 'used_percent'),
        ('custom', 'check_ncpa!memory/swap/percent', 'percent'),
        ('custom', 'check_ncpa!disk/physical/read_percent', 'used_percent'),
        ('custom', 'check_ncpa!memory/virtual/percent!disk/logical/|/used_percent', 'percent'),
        ('ncpa-cpu-5693-tcp', 'pinpoint_nd_ncpa', 'percent'),
    ])
    def test_excluded_identity_stores_nothing(self, db_session, service, command, metric):
        seed_series(db_session, 'excluded', service, metric, 40, .3)
        db_session.session.execute(sa.update(ServiceStatus).values(Check_Command=command))
        db_session.session.commit()
        assert forecast.compute_forecasts() == 0
        assert rows() == []

    def test_invalid_series_do_not_consume_the_cap(self, db_session, monkeypatch):
        seed_series(db_session, 'a-invalid', 'ncpa-disk-5693-tcp', DISK, 40, .3)
        db_session.session.execute(sa.update(ServiceStatus).values(Check_Command='check_http'))
        seed_series(db_session, 'z-valid', 'ncpa-memory-5693-tcp', 'percent', 40, .3)
        monkeypatch.setattr(forecast, 'MAX_SERIES_PER_RUN', 1)
        assert forecast.compute_forecasts() == 1
        assert [r.Hostname for r in rows()] == ['z-valid']

    def test_hourly_samples_exclude_other_plugin_snapshots_of_the_same_series(self, db_session):
        service = 'ncpa-memory-5693-tcp'
        seed_series(db_session, 'mixed', service, 'percent', 40, .3)
        now = datetime.now(timezone.utc)
        for i in range(72):
            row = _make_service(db_session, 'mixed', service, ts=now-timedelta(hours=72-i), check_command='check_http')
            _make_service_perf(db_session, row, 'percent', 999, '%', warn=1000, crit=2000)
        db_session.session.commit()
        assert forecast.compute_forecasts() == 1
        row, = rows()
        assert row.Sample_Count == 72
        assert row.Current_Value == pytest.approx(61.3)
        assert row.Threshold == 80

    def test_short_new_history_is_insufficient_and_keeps_raw_metric_identity(self, db_session):
        seed_series(db_session, 'new', 'ncpa-memory-5693-tcp', "'percent'", 40, .3, hours=5)
        assert forecast.compute_forecasts() == 0
        row, = rows()
        assert (row.Kind, row.Metric, row.Sample_Count) == ('insufficient', "'percent'", 5)
        assert row.Threshold is None and row.Crossing_At is None
