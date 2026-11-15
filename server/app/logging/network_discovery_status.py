"""
Network discovery run records: create the run status row, update its progress, record
the ports that were skipped, read the latest run, and compute a progress percentage.
"""

from app.system_models import NetworkDiscoveryStatus, DiscoveryStatus, SkippedService, ServiceProtocol
from flask import current_app
import sqlalchemy as sa 
from app import db
from datetime import datetime, timezone
from app.logging.user_activity import create_user_log

def create_network_discovery_status(user_id):
    """
    Start a new network discovery run for a user. It writes the activity log entry
    and a NetworkDiscoveryStatus row in the Running state at 0 percent, then
    commits. It returns the new status row, or rolls back, logs the error and
    returns None.
    """
    try:
        user_log = create_user_log(user_id, "Discovering Network Hosts") 

        network_discovery_status = NetworkDiscoveryStatus(
            Status = DiscoveryStatus.RUNNING,
            Progress = 0, 
            Message = "Network Discovery process starting.",
            LogID = user_log.LogID
        )

        db.session.add(network_discovery_status)
        db.session.commit()

        return network_discovery_status
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Cannot create network dicovery status {e}")
        return None

def update_network_discovery_status(network_discovery_status_id, status, progress, message, completed_at=None, error=None):
    """
    Set the status, progress, message, completion time and error of one discovery
    run, then commit. A missing run is treated as an error: it rolls back, logs it
    and returns None. On success it returns the NetworkDiscoveryStatus class rather
    than the updated row, so callers should not rely on the return value.
    """
    try:

        network_discovery_status = db.session.scalar(
            sa.Select(NetworkDiscoveryStatus).where(
                NetworkDiscoveryStatus.DiscoveryStatusID == network_discovery_status_id
            )
        )

        if network_discovery_status is None:
            raise ValueError(
                f"Discovery status {network_discovery_status_id} does not exist"
            )

        network_discovery_status.Status = status
        network_discovery_status.Progress = progress
        network_discovery_status.Message = message
        network_discovery_status.Completed_At = completed_at
        network_discovery_status.Error = error

        db.session.commit()

        return NetworkDiscoveryStatus
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Cannot create network dicovery status {e}")
        return None

def create_skipped_service_logs(network_discovery_status_id, skipped):
    """
    Record every discovered port that was not turned into a Nagios service
    during one discovery run, so administrators can see it in the discovery
    log. Expects skipped entries as produced by _create_host_cfg_file()
    (hostname, ip_address, port, protocol, service_name, reason). Commits.
    Failure is logged and swallowed — it must never fail the discovery run.
    """
    try:
        for entry in skipped:
            db.session.add(SkippedService(
                DiscoveryStatusID = network_discovery_status_id,
                Hostname = entry["hostname"],
                IP_Address = entry.get("ip_address"),
                Port_Number = int(entry["port"]),
                Protocol = ServiceProtocol(entry["protocol"]),
                Service_Name = str(entry["service_name"])[:100],
                Reason = str(entry["reason"])[:255],
            ))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Cannot record skipped services {e}")

def get_network_discovery_status():
    """
    Return the most recently started network discovery run, or None when there is
    none or the query fails. It does not change the database.
    """
    try:
        return db.session.scalar(
            sa.select(NetworkDiscoveryStatus)
            .order_by(NetworkDiscoveryStatus.Start_At.desc()
                      ).limit(1)
        )
    except Exception as e:
        current_app.logger.exception(f"An Error Occured")
        return None

def calculate_progress(current, total, start, end):
    """
    Map the current step of a total onto a progress percentage between start and end
    and return it as an integer. When total is zero or less it returns end. It is a
    pure function and is also reused by the plugin scan helpers.
    """
    if total <= 0:
        return end

    return int(start + (current / total) * (end - start))