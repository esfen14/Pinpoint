import atexit
import os
from contextlib import contextmanager
from threading import RLock
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

from app import app, db
from app.automation import run_due_automation
from app.nagios.status import get_status

DEFAULT_POLL_INTERVAL_SECONDS = 60
SUPPORTED_POLL_INTERVALS = (30, 60, 120, 300)
# Maintenance windows are handed to Nagios on a fixed tick, whatever the status polling interval.
MAINTENANCE_DISPATCH_SECONDS = 60
settings_schedule_lock = RLock()
REMEDIATION_POLL_SECONDS = 15
# Forecasts change slowly and are built from hourly averages, so a half hour is plenty.
FORECAST_MINUTES = 30

_scheduler: BackgroundScheduler | None = None


@contextmanager
def polling_schedule_change(seconds):
    """Apply a poll interval until the caller commits; restore the job on error.

    The settings route holds settings_schedule_lock across read, validation and
    commit. Modifying the same job preserves executor instance accounting, so a
    running poll finishes and max_instances continues to prevent overlap.
    A disabled scheduler is never created here.
    """
    job = _scheduler.get_job("nagios_poll") if _scheduler is not None else None
    if _scheduler is not None and job is None:
        raise RuntimeError("Running scheduler has no Nagios polling job")
    previous = {"trigger": job.trigger, "next_run_time": job.next_run_time} if job else None
    try:
        if job is not None and seconds is not None:
            job.reschedule("interval", seconds=seconds)
        yield
    except Exception:
        if job is not None and seconds is not None:
            # Restore both cadence and phase, including partial reschedule errors.
            job.modify(**previous)
        raise


def persisted_poll_interval():
    """Read the system poll interval at startup without creating settings rows."""
    from app.system_models import SystemSettings

    with app.app_context():
        try:
            row = db.session.get(SystemSettings, 1)
        except sa.exc.OperationalError:
            # No tables yet: `flask db upgrade` imports the app on a fresh database.
            db.session.rollback()
            return DEFAULT_POLL_INTERVAL_SECONDS
        return row.Data_Polling_Interval if row is not None else DEFAULT_POLL_INTERVAL_SECONDS


def _poll_nagios_status():
    with app.app_context():
        get_status()


def _mark_interrupted_remediation_runs():
    """
    At startup, mark remediation runs left running by a stop as interrupted (never re-run), and
    fail operator notifications whose send never saved a result (never re-sent).
    """
    from app import remediation, remediation_escalation as escalation

    with app.app_context():
        try:
            remediation.mark_interrupted()
            escalation.fail_unfinished()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Could not mark interrupted remediation runs")


def _consume_remediation_spool():
    """Hand the event handler spool to the remediation consumer. It never raises."""
    from app import remediation

    with app.app_context():
        try:
            remediation.process_spool()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error while consuming the remediation spool")


def _compute_forecasts():
    """Recompute disk and memory forecasts from stored performance data. It never raises."""
    from app import forecast

    with app.app_context():
        try:
            forecast.compute_forecasts()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error while computing forecasts")


def _relocate_ncpa_devices():
    """Look for NCPA devices that changed IP since the last full scan."""
    from app.network_discovery.ncpa_relocation import relocate_ncpa_devices

    with app.app_context():
        try:
            relocate_ncpa_devices()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error during NCPA relocation")


def _dispatch_maintenance_windows():
    """Hand maintenance windows that are about to start to Nagios as scheduled downtime."""
    from app.maintenance import dispatch_due_windows

    with app.app_context():
        try:
            dispatch_due_windows()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error dispatching maintenance windows")


def _purge_old_data():
    with app.app_context():
        try:
            from app.system_models import (
                SystemSettings,
                ActivityLog,
                ConfigurationChanges,
                NetworkDiscoveryStatus,
                NCPADeploymentStatus,
                ExportLog,
                RemediationRun,
            )
            from app.history_models import (
                HostStatus,
                HostPerfData,
                ServiceStatus,
                ServicePerfData,
                ProgramStatus,
            )

            settings = db.session.get(SystemSettings, 1)
            if settings is None:
                return

            now = datetime.now(timezone.utc)

            # --- Activity / audit log retention ---------------------------
            log_cutoff = now - timedelta(days=settings.Log_Retention_Days)
            old_log_ids = db.session.scalars(
                sa.select(ActivityLog.LogID).where(ActivityLog.Performed_At < log_cutoff)
            ).all()
            if old_log_ids:
                # Children first — they FK onto ActivityLog.LogID.
                db.session.execute(sa.delete(ConfigurationChanges).where(ConfigurationChanges.LogID.in_(old_log_ids)))
                db.session.execute(sa.delete(NetworkDiscoveryStatus).where(NetworkDiscoveryStatus.LogID.in_(old_log_ids)))
                db.session.execute(sa.delete(NCPADeploymentStatus).where(NCPADeploymentStatus.LogID.in_(old_log_ids)))
                db.session.execute(sa.delete(ExportLog).where(ExportLog.LogID.in_(old_log_ids)))
                db.session.execute(sa.delete(ActivityLog).where(ActivityLog.LogID.in_(old_log_ids)))

            # --- Remediation run log (audit trail of automatic actions) ---
            run_cutoff = now - timedelta(days=settings.Remediation_Retention_Days)
            db.session.execute(sa.delete(RemediationRun).where(RemediationRun.Received_At < run_cutoff))
            from app import remediation
            remediation.purge_old_spool_files()

            # --- Diagnostic history retention (Nagios snapshots) ----------
            diag_cutoff = now - timedelta(days=settings.Diagnostic_History_Retention_Days)

            old_host_ids = db.session.scalars(
                sa.select(HostStatus.HostStatusID).where(HostStatus.Timestamp < diag_cutoff)
            ).all()
            if old_host_ids:
                db.session.execute(sa.delete(HostPerfData).where(HostPerfData.HostStatusID.in_(old_host_ids)))
                db.session.execute(sa.delete(HostStatus).where(HostStatus.HostStatusID.in_(old_host_ids)))

            old_service_ids = db.session.scalars(
                sa.select(ServiceStatus.ServiceStatusID).where(ServiceStatus.Timestamp < diag_cutoff)
            ).all()
            if old_service_ids:
                db.session.execute(sa.delete(ServicePerfData).where(ServicePerfData.ServiceStatusID.in_(old_service_ids)))
                db.session.execute(sa.delete(ServiceStatus).where(ServiceStatus.ServiceStatusID.in_(old_service_ids)))

            db.session.execute(sa.delete(ProgramStatus).where(ProgramStatus.Timestamp < diag_cutoff))

            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error while purging old data")


def init_scheduler():
    """Start the background scheduler, once, in the actual serving process.

    Flask's debug reloader imports this module twice: once in the reloader's
    monitor process (no WERKZEUG_RUN_MAIN) and once in the real worker
    process (WERKZEUG_RUN_MAIN=true). Starting in both would double every
    poll/purge, so skip the monitor process when debug+reloader are active.

    The scheduler is also suppressed entirely under ``app.testing`` so that
    background jobs never race against test-created in-memory databases.
    """
    global _scheduler
    if _scheduler is not None:
        return

    if app.testing:
        return

    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    _mark_interrupted_remediation_runs()
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _poll_nagios_status,
        "interval",
        seconds=persisted_poll_interval(),
        id="nagios_poll",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.add_job(
        _dispatch_maintenance_windows,
        "interval",
        seconds=MAINTENANCE_DISPATCH_SECONDS,
        id="maintenance_windows",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _purge_old_data,
        "interval",
        days=1,
        id="retention_purge",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.add_job(
        run_due_automation,
        "interval",
        minutes=app.config["AUTOMATION_CHECK_MINUTES"],
        id="settings_automation",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _relocate_ncpa_devices,
        "interval",
        minutes=app.config["NCPA_RELOCATE_MINUTES"],
        id="ncpa_relocation",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _consume_remediation_spool,
        "interval",
        seconds=REMEDIATION_POLL_SECONDS,
        id="remediation_spool",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _compute_forecasts,
        "interval",
        minutes=FORECAST_MINUTES,
        id="resource_forecast",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
