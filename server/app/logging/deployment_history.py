"""
NCPA deployment run records: create the run status row, update its progress, read the
latest run, and keep one result row per device in each run (add, move to a new outcome,
close open rows, read and count them).
"""

from app.system_models import (
    NCPADeploymentStatus, DeploymentStatus, NCPADeploymentResult, DeploymentOutcome,
)
from flask import current_app
import sqlalchemy as sa
from app import db
from datetime import datetime, timezone
from app.logging.user_activity import create_user_log


def create_ncpa_deployment_status(user_id):
    """
    Start a new NCPA deployment run for a user. It writes the activity log entry and
    a NCPADeploymentStatus row in the Running state at 0 percent, then commits. It
    returns the new status row, or rolls back, logs the error and returns None.
    """
    try:
        action = "NCPA Deployed"
        user_log = create_user_log(user_id, action)

        ncpa_deploymenet_staus = NCPADeploymentStatus(
            Status= DeploymentStatus.RUNNING,
            Progress= 0,
            Message= "NCPA deployment starting.",
            LogID = user_log.LogID
        )

        db.session.add(ncpa_deploymenet_staus)
        db.session.commit()

        return ncpa_deploymenet_staus
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Cannot create NCPA Deployment log for user {user_id} error: {e}")
        return None

def update_ncpa_deployment_status(ncpa_deployment_status_id, status, progress, message, competed_at=None,error=None):
    """
    Set the status, progress, message, completion time and error of one NCPA
    deployment run, then commit. If the run does not exist it logs an error and
    returns without changing anything. Other errors are logged and swallowed; it
    returns None either way.
    """
    try:
        ncpa_deployment_status = db.session.scalar(
            sa.Select(NCPADeploymentStatus)
            .where(
                NCPADeploymentStatus.NCPADeployStatusID == ncpa_deployment_status_id
            )
        )

        if ncpa_deployment_status is None:
            current_app.logger.error(
                f"NCPA Deployment status {ncpa_deployment_status_id} does not exist"
            )
            return

        ncpa_deployment_status.Status = status
        ncpa_deployment_status.Progress = progress
        ncpa_deployment_status.Message = message
        ncpa_deployment_status.Completed_At = competed_at
        ncpa_deployment_status.Error = error

        db.session.commit()

    except Exception as e:
        current_app.logger.exception(f"Cannot update NCPA Deployement log {ncpa_deployment_status_id}")

def get_deployment_ncpa_status():
    """
    Return the most recently started NCPA deployment run, or None when there is none
    or the query fails. It does not change the database.
    """
    try:
        return db.session.scalar(
            sa.select(NCPADeploymentStatus)
            .order_by(NCPADeploymentStatus.Start_At.desc()
                      ).limit(1)
        )

    except Exception as e:
        current_app.logger.exception(f"An unexpected error Occured.")
        return None
    
def calculate_progress(current, total, start, end):
    """
    Map the current step of a total onto a progress percentage between start and end
    and return it as an integer. When total is zero or less it returns end. It is a
    pure function.
    """
    if total <= 0:
        return end

    return int(start + (current / total) * (end - start))

# Outcomes a device can still move out of while its run is going.
OPEN_OUTCOMES = (DeploymentOutcome.PENDING, DeploymentOutcome.RUNNING)


def add_deployment_result(ncpa_deployment_status_id, device, outcome, error=None):
    """
    Add one device's row to a run. The hostname and IP are copied from the
    device so the row stays readable after it is renamed or moves. Flushes
    but does not commit; the caller commits.
    """
    result = NCPADeploymentResult(
        NCPADeploymentStatusID=ncpa_deployment_status_id,
        NetworkDiscoveryID=device.NetDiscoveryID,
        Hostname=device.Hostname,
        IP_Address=device.IP_Address,
        Outcome=outcome,
        Error=error,
    )
    if outcome not in OPEN_OUTCOMES:
        result.Completed_At = datetime.now(timezone.utc)
    db.session.add(result)
    db.session.flush()
    return result


def set_deployment_result(ncpa_deployment_status_id, device_id, outcome, error=None):
    """
    Move one device's row in a run to a new outcome, stamping Started_At when
    it starts and Completed_At when it finishes. Commits. Logs and returns
    None if the row does not exist.
    """
    try:
        result = db.session.scalar(
            sa.select(NCPADeploymentResult).where(
                NCPADeploymentResult.NCPADeploymentStatusID == ncpa_deployment_status_id,
                NCPADeploymentResult.NetworkDiscoveryID == device_id,
            )
        )
        if result is None:
            current_app.logger.error(
                f"No deployment result for device {device_id} in run {ncpa_deployment_status_id}."
            )
            return None

        now = datetime.now(timezone.utc)
        result.Outcome = outcome
        result.Error = error
        if outcome is DeploymentOutcome.RUNNING:
            result.Started_At = now
        elif outcome not in OPEN_OUTCOMES:
            result.Completed_At = now

        db.session.commit()
        return result

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Cannot update deployment result for device {device_id} in run {ncpa_deployment_status_id}."
        )
        return None


def close_open_results(ncpa_deployment_status_id, outcome, error):
    """
    Give every device in a run that is still Pending or Running a final
    outcome (Skipped when the run is stopped, Failed when it crashes).
    Commits.
    """
    try:
        now = datetime.now(timezone.utc)
        results = db.session.scalars(
            sa.select(NCPADeploymentResult).where(
                NCPADeploymentResult.NCPADeploymentStatusID == ncpa_deployment_status_id,
                NCPADeploymentResult.Outcome.in_(OPEN_OUTCOMES),
            )
        ).all()
        for result in results:
            result.Outcome = outcome
            result.Error = error
            result.Completed_At = now
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Cannot close open deployment results for run {ncpa_deployment_status_id}."
        )


def get_deployment_results(ncpa_deployment_status_id):
    """Every device row of one run, in the order they were added."""
    return db.session.scalars(
        sa.select(NCPADeploymentResult)
        .where(NCPADeploymentResult.NCPADeploymentStatusID == ncpa_deployment_status_id)
        .order_by(NCPADeploymentResult.NCPADeployResultID.asc())
    ).all()


def count_deployment_results(ncpa_deployment_status_ids):
    """
    Count device outcomes for several runs in one query. Returns
    {run_id: {"success": n, "failed": n, "down": n, ...}} with every key
    present, so callers never need to check for missing outcomes.
    """
    keys = {outcome: outcome.value.lower() for outcome in DeploymentOutcome}
    counts = {run_id: {key: 0 for key in keys.values()} for run_id in ncpa_deployment_status_ids}
    if not counts:
        return counts

    rows = db.session.execute(
        sa.select(
            NCPADeploymentResult.NCPADeploymentStatusID,
            NCPADeploymentResult.Outcome,
            sa.func.count(),
        )
        .where(NCPADeploymentResult.NCPADeploymentStatusID.in_(list(counts)))
        .group_by(NCPADeploymentResult.NCPADeploymentStatusID, NCPADeploymentResult.Outcome)
    ).all()
    for run_id, outcome, total in rows:
        counts[run_id][keys[outcome]] = total
    return counts


def get_deployment_ncpa_status_by_id(ncpa_deployment_status_id):
    """
    One run by ID, re-read from the database so a status written from
    another session (add_ncpa_port runs in its own app context) is seen.
    """
    return db.session.get(NCPADeploymentStatus, ncpa_deployment_status_id, populate_existing=True)
