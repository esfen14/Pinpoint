"""Turns completed network-discovery runs (NetworkDiscoveryStatus rows) into events
shaped like the Nagios entries shown on the History page, tagged with source
"pinpoint".
"""
from datetime import timezone

import sqlalchemy as sa

from app import db
from app.system_models import DiscoveryStatus, NetworkDiscoveryStatus

SOURCE_NAGIOS = "nagios"
SOURCE_PINPOINT = "pinpoint"

SCAN_TITLES = {
    DiscoveryStatus.SUCCESS: ("SUCCESS", "Network scan completed successfully"),
    DiscoveryStatus.FAILED: ("FAILED", "Network scan failed"),
    DiscoveryStatus.INTERRUPTED: ("CANCELLED", "Network scan was cancelled"),
}


def _epoch(moment):
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int(moment.timestamp())


def _to_event(row):
    state, title = SCAN_TITLES[row.Status]
    detail = row.Message or ""
    if row.Error:
        detail = f"{detail}\n{row.Error}" if detail else row.Error
    return {
        "source": SOURCE_PINPOINT,
        "id": row.DiscoveryStatusID,
        "timestamp": _epoch(row.Completed_At),
        "category": "network_scan",
        "state": state,
        "title": title,
        "message": detail,
    }


def get_scan_events(start_ts, end_ts):
    """Return History events for network scans that finished successfully, failed or
    were cancelled between the UNIX timestamps `start_ts` and `end_ts` (inclusive of
    the end second), newest first. Reads the database only.
    """
    from datetime import datetime
    start = datetime.fromtimestamp(start_ts, tz=timezone.utc).replace(tzinfo=None)
    end = datetime.fromtimestamp(end_ts + 1, tz=timezone.utc).replace(tzinfo=None)
    rows = db.session.scalars(
        sa.select(NetworkDiscoveryStatus)
        .where(
            NetworkDiscoveryStatus.Status.in_(list(SCAN_TITLES)),
            NetworkDiscoveryStatus.Completed_At.is_not(None),
            NetworkDiscoveryStatus.Completed_At >= start,
            NetworkDiscoveryStatus.Completed_At < end,
        )
        .order_by(NetworkDiscoveryStatus.Completed_At.desc())
    ).all()
    return [_to_event(row) for row in rows]


def get_scan_event(discovery_status_id):
    """Return the History event for one finished network scan, or None if the record
    does not exist, is still running or has no completion time. Reads the database
    only.
    """
    row = db.session.get(NetworkDiscoveryStatus, discovery_status_id)
    if row is None or row.Status not in SCAN_TITLES or row.Completed_At is None:
        return None
    return _to_event(row)
