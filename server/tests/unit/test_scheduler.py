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
