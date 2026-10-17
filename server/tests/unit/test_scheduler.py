"""
tests/unit/test_scheduler.py — Tests for app/scheduler.py.
"""
import app.scheduler as scheduler


class TestInitScheduler:

    def test_not_started_under_testing(self, app):
        assert app.testing
        assert scheduler._scheduler is None

    def test_init_is_noop_under_testing(self, app):
        scheduler.init_scheduler()
        assert scheduler._scheduler is None


class TestMaintenanceJob:

    def test_job_runs_the_dispatcher(self, app):
        from unittest.mock import patch
        with patch("app.maintenance.dispatch_due_windows", return_value=0) as dispatch:
            scheduler._dispatch_maintenance_windows()
        dispatch.assert_called_once_with()

    def test_job_never_raises(self, app):
        from unittest.mock import patch
        with patch("app.maintenance.dispatch_due_windows", side_effect=RuntimeError("boom")):
            scheduler._dispatch_maintenance_windows()
class TestForecastJob:

    def test_job_runs_the_forecast(self, app):
        from unittest.mock import patch
        with patch("app.forecast.compute_forecasts", return_value=0) as compute:
            scheduler._compute_forecasts()
        compute.assert_called_once_with()

    def test_job_never_raises(self, app):
        from unittest.mock import patch
        with patch("app.forecast.compute_forecasts", side_effect=RuntimeError("boom")):
            scheduler._compute_forecasts()

    def test_job_is_registered_once_at_a_bounded_interval(self, app):
        from unittest.mock import MagicMock, patch
        fake = MagicMock()
        was_debug = app.debug
        app.testing = False
        app.debug = False
        try:
            with patch.object(scheduler, "BackgroundScheduler", return_value=fake),                  patch.object(scheduler, "_mark_interrupted_remediation_runs"),                  patch.object(scheduler, "persisted_poll_interval", return_value=60),                  patch.object(scheduler.atexit, "register"):
                scheduler.init_scheduler()
        finally:
            app.testing = True
            app.debug = was_debug
            scheduler._scheduler = None
        jobs = [c for c in fake.add_job.call_args_list if c.kwargs.get("id") == "resource_forecast"]
        assert len(jobs) == 1
        assert jobs[0].args[0] is scheduler._compute_forecasts
        assert jobs[0].kwargs["max_instances"] == 1 and jobs[0].kwargs["coalesce"] is True
        assert jobs[0].kwargs["minutes"] == scheduler.FORECAST_MINUTES


class TestPurgeRemediationRuns:
    """_purge_old_data also bounds the remediation run log (an audit trail, not statistics)."""

    @staticmethod
    def _run(Event_Key, received_at):
        from app.system_models import RemediationEventState, RemediationEventStateType, RemediationOutcome, RemediationRun
        return RemediationRun(
            Event_Key=Event_Key, Action_Id=1, Action_Name="a", Hostname="web-01", Service="HTTP",
            State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
            Received_At=received_at, Outcome=RemediationOutcome.SUCCEEDED,
        )

    def test_old_runs_are_removed_and_recent_ones_kept(self, db_session):
        from datetime import datetime, timedelta, timezone
        from app.system_models import RemediationRun, SystemSettings

        now = datetime.now(timezone.utc)
        db_session.session.add(SystemSettings(Id=1, Remediation_Retention_Days=90))
        db_session.session.add(self._run("old", now - timedelta(days=91)))
        db_session.session.add(self._run("recent", now - timedelta(days=89)))
        db_session.session.commit()

        scheduler._purge_old_data()

        keys = [r.Event_Key for r in db_session.session.query(RemediationRun).all()]
        assert keys == ["recent"]

    def test_retention_setting_is_respected(self, db_session):
        from datetime import datetime, timedelta, timezone
        from app.system_models import RemediationRun, SystemSettings

        now = datetime.now(timezone.utc)
        db_session.session.add(SystemSettings(Id=1, Remediation_Retention_Days=7))
        db_session.session.add(self._run("eight-days", now - timedelta(days=8)))
        db_session.session.commit()

        scheduler._purge_old_data()

        assert db_session.session.query(RemediationRun).count() == 0


    def test_the_diagnostic_history_setting_no_longer_decides_run_retention(self, db_session):
        from datetime import datetime, timedelta, timezone
        from app.system_models import RemediationRun, SystemSettings

        now = datetime.now(timezone.utc)
        db_session.session.add(SystemSettings(
            Id=1, Diagnostic_History_Retention_Days=7, Remediation_Retention_Days=30))
        db_session.session.add(self._run("twenty-days", now - timedelta(days=20)))
        db_session.session.commit()

        scheduler._purge_old_data()

        assert db_session.session.query(RemediationRun).count() == 1

    def test_the_default_retention_is_still_ninety_days(self, db_session):
        from app.system_models import SystemSettings

        db_session.session.add(SystemSettings(Id=1))
        db_session.session.commit()
        assert db_session.session.get(SystemSettings, 1).Remediation_Retention_Days == 90


class TestPurgeSpoolFiles:
    """_purge_old_data removes spool files nobody handled for a long time (never newer or foreign ones)."""

    @staticmethod
    def _file(folder, name, age_days):
        import os
        import time
        path = folder / name
        path.write_text("{}")
        stamp = time.time() - age_days * 86400
        os.utime(path, (stamp, stamp))
        return path

    def test_old_event_files_are_removed_and_newer_or_other_files_are_kept(self, db_session, app, tmp_path):
        from app.system_models import SystemSettings

        app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
        db_session.session.add(SystemSettings(Id=1))
        db_session.session.commit()
        self._file(tmp_path, "1760432100000000000-1.json", 8)
        self._file(tmp_path, "1760432100000000000-2.json", 1)
        self._file(tmp_path, "notes.txt", 30)

        scheduler._purge_old_data()

        assert sorted(p.name for p in tmp_path.iterdir()) == ["1760432100000000000-2.json", "notes.txt"]

    def test_a_missing_spool_folder_does_not_stop_the_purge(self, db_session, app, tmp_path):
        from datetime import datetime, timedelta, timezone
        from app.system_models import RemediationRun, SystemSettings

        app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path / "missing")
        db_session.session.add(SystemSettings(Id=1, Remediation_Retention_Days=7))
        db_session.session.add(TestPurgeRemediationRuns._run("old", datetime.now(timezone.utc) - timedelta(days=9)))
        db_session.session.commit()

        scheduler._purge_old_data()

        assert db_session.session.query(RemediationRun).count() == 0


class TestPersistedPollInterval:

    def test_defaults_when_the_database_has_no_tables_yet(self, app):
        from unittest.mock import patch
        import sqlalchemy as sa
        error = sa.exc.OperationalError("SELECT", {}, Exception("no such table: SYSTEM_SETTINGS"))
        with patch("app.scheduler.db.session.get", side_effect=error):
            assert scheduler.persisted_poll_interval() == scheduler.DEFAULT_POLL_INTERVAL_SECONDS
