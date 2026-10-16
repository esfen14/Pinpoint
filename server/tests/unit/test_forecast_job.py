"""
tests/unit/test_forecast_job.py — The forecast job (app/forecast.py, compute_forecasts).

It reads hourly-averaged disk and memory percent history, keeps only the latest forecast per
host, service and metric, skips paused devices, caps the services per run, and keeps a fixed
number of queries however many services exist. It never touches Nagios.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import sqlalchemy as sa

from app import db, forecast
from app.history_models import ServicePerfData, ServiceStatus
from app.nagios import commands as nagios_commands
from app.system_models import ResourceForecast
from tests.support.seed_helpers import _make_service, _make_service_perf
from tests.unit.test_create_host_cfg import make_device

DISK = "disk/logical/|/used_percent"
MEMORY = "memory/virtual/percent"


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
        with patch.object(nagios_commands, "_write_line") as pipe:
            forecast.compute_forecasts()
        pipe.assert_not_called()
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
