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
        db_session.session.add(SystemSettings(Id=1, Diagnostic_History_Retention_Days=90))
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
        db_session.session.add(SystemSettings(Id=1, Diagnostic_History_Retention_Days=7))
        db_session.session.add(self._run("eight-days", now - timedelta(days=8)))
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
