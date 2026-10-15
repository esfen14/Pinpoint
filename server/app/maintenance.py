"""
maintenance.py — Maintenance windows that become Nagios scheduled downtime.

A MaintenanceWindow (system_models.py) is turned, shortly before each occurrence, into
host and service downtime through the Nagios command channel (nagios/commands.py), with a
fixed start and end so Nagios ends the downtime itself. This is separate from PinPoint's own
Maintenance Mode (automation.py), which only pauses PinPoint's background jobs.

All stored times are naive UTC. Recurrence repeats at the same local wall-clock time in the
window's own time zone, so a daily 02:00 window stays at 02:00 across a daylight-saving change;
the occurrence's length stays fixed. Scheduling uses the server's clock, which is the Nagios
server's clock on an appliance.

Each occurrence handed to Nagios is a MaintenanceOccurrence row, unique per (window, start). It
is claimed (committed) before anything is sent, so a restart or an overlapping run never
schedules it twice. A failed send is retried on later runs up to MAX_ATTEMPTS, then marked
failed with the reason. A retry first deletes any downtime the earlier attempt left, so it
cannot duplicate.

Every downtime carries the comment from occurrence_comment(); cancelling deletes by that
comment (DEL_DOWNTIME_BY_HOST_NAME, checked on Nagios 4.5.11), so it only touches downtime
PinPoint created for that occurrence.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import sqlalchemy as sa
from flask import current_app

from app import db
from app.logging.user_activity import create_user_log
from app.nagios import commands
from app.network_discovery.device_identity import monitoring_state, nagios_host_name
from app.system_models import MaintenanceOccurrence, MaintenanceWindow, NetworkDiscovery

# Downtime is scheduled this long before an occurrence starts.
LEAD_TIME = timedelta(minutes=10)
# Sends tried per occurrence (one per dispatcher run) before it is marked failed.
MAX_ATTEMPTS = 3

RECURRENCES = ("none", "daily", "weekly")
PERIODS = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}
MAX_ONE_OFF_DURATION = timedelta(days=30)
MAX_RECURRENCE_SPAN = timedelta(days=366)
MAX_COMMENT_CHARS = 200

ACTIVE, CANCELLED, COMPLETED = "active", "cancelled", "completed"
PENDING, SENT, FAILED, OCC_CANCELLED = "pending", "sent", "failed", "cancelled"


def zone(name: str):
    """
    The tzinfo for an IANA name. UTC needs no tz database, so it works on an image without
    one; any other name needs the `tzdata` package (requirements.txt) or the system database.
    """
    if name == "UTC":
        return timezone.utc
    return ZoneInfo(name)


def utcnow() -> datetime:
    """Now as a naive UTC datetime, the way times are stored."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(value: datetime | None) -> str | None:
    """A stored naive-UTC time as ISO 8601 with a trailing Z."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def epoch(value: datetime) -> int:
    return int(value.replace(tzinfo=timezone.utc).timestamp())


def occurrence_comment(window_id: int, start: datetime) -> str:
    """The exact Nagios downtime comment of one occurrence; also what cancel matches."""
    return f"PinPoint maintenance window {window_id} starting {epoch(start)}"


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------

def occurrence_bounds(window: MaintenanceWindow, index: int) -> tuple[datetime, datetime]:
    """Start and end (naive UTC) of occurrence `index`, counting from 0."""
    duration = window.End_At - window.Start_At
    period = PERIODS.get(window.Recurrence)
    if index == 0 or period is None:
        return window.Start_At, window.End_At
    tz = zone(window.Time_Zone)
    local = window.Start_At.replace(tzinfo=timezone.utc).astimezone(tz).replace(tzinfo=None)
    start = (local + period * index).replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
    return start, start + duration


def next_occurrence(window: MaintenanceWindow, now: datetime) -> tuple[datetime, datetime] | None:
    """The occurrence running now or the next one to start, or None when there is none left."""
    period = PERIODS.get(window.Recurrence)
    if period is None:
        return (window.Start_At, window.End_At) if window.End_At > now else None

    # Start one period early so a daylight-saving shift cannot skip an occurrence.
    first = max(0, int((now - window.Start_At) / period) - 1)
    for index in range(first, first + 4):
        start, end = occurrence_bounds(window, index)
        if window.Recurrence_Until is not None and start > window.Recurrence_Until:
            return None
        if end > now:
            return start, end
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _parse_time(value, label: str) -> tuple[datetime | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, f"{label} is required."
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None, f"{label} must be an ISO 8601 date and time."
    if parsed.tzinfo is None:
        return None, f"{label} must include a UTC offset (for example 2026-10-20T02:00:00Z)."
    return parsed.astimezone(timezone.utc).replace(tzinfo=None), None


def validate_window(data, now: datetime) -> tuple[dict | None, str | None]:
    """
    Check a create or update body. Returns (fields, None) with the values ready to store, or
    (None, message). Guard clauses, first problem wins.
    """
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    start, message = _parse_time(data.get("startAt"), "startAt")
    if message:
        return None, message
    end, message = _parse_time(data.get("endAt"), "endAt")
    if message:
        return None, message
    if end <= start:
        return None, "endAt must be after startAt."
    if end <= now:
        return None, "The window must end in the future."

    recurrence = data.get("recurrence", "none")
    if recurrence not in RECURRENCES:
        return None, "recurrence must be none, daily or weekly."
    duration = end - start
    period = PERIODS.get(recurrence)
    if period is None and duration > MAX_ONE_OFF_DURATION:
        return None, "A window can last at most 30 days."
    if period is not None and duration > period:
        return None, f"A {recurrence} window cannot last longer than one {'day' if recurrence == 'daily' else 'week'}."

    until = None
    if data.get("recurrenceUntil") not in (None, ""):
        if period is None:
            return None, "recurrenceUntil only applies to a recurring window."
        until, message = _parse_time(data.get("recurrenceUntil"), "recurrenceUntil")
        if message:
            return None, message
        if until < start:
            return None, "recurrenceUntil must not be before startAt."
        if until - start > MAX_RECURRENCE_SPAN:
            return None, "A recurring window can be scheduled at most 366 days ahead."

    time_zone = data.get("timeZone", "UTC")
    if not isinstance(time_zone, str) or not time_zone.strip():
        return None, "timeZone must be an IANA time zone name."
    try:
        zone(time_zone)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return None, "timeZone is not a known time zone."

    comment = data.get("comment")
    if not isinstance(comment, str) or not comment.strip():
        return None, "comment is required."
    comment = comment.strip()
    if len(comment) > MAX_COMMENT_CHARS:
        return None, f"comment must be at most {MAX_COMMENT_CHARS} characters."
    if commands.has_forbidden_chars(comment):
        return None, "comment must not contain line breaks."

    device_id = data.get("deviceId")
    if device_id is not None:
        if isinstance(device_id, bool) or not isinstance(device_id, int):
            return None, "deviceId must be a device id, or null for all devices."
        device = db.session.get(NetworkDiscovery, device_id)
        if device is None:
            return None, "Device not found."
        if monitoring_state(device) != "monitored":
            return None, f"Device is {monitoring_state(device)}, so it has no Nagios downtime to schedule."

    return {
        "NetDiscoveryID": device_id, "Start_At": start, "End_At": end, "Recurrence": recurrence,
        "Recurrence_Until": until, "Time_Zone": time_zone, "Comment": comment,
    }, None


# ---------------------------------------------------------------------------
# Talking to Nagios
# ---------------------------------------------------------------------------

def _scope_hosts(window: MaintenanceWindow, targets) -> tuple[list[str], str | None]:
    """The Nagios host names a window covers, or (_, reason) when the scope cannot be resolved."""
    hosts, _services = targets
    if window.NetDiscoveryID is None:
        return sorted(hosts), None
    device = db.session.get(NetworkDiscovery, window.NetDiscoveryID)
    if device is None:
        return [], "The device no longer exists."
    if monitoring_state(device) != "monitored":
        return [], f"The device is {monitoring_state(device)}."
    name = nagios_host_name(device)
    if name not in hosts:
        return [], f"{name} is not in the latest Nagios status."
    return [name], None


def _send_occurrence(window: MaintenanceWindow, occurrence: MaintenanceOccurrence, targets, retry: bool) -> str | None:
    """Schedule the downtime of one occurrence. Returns None on success, else the reason."""
    host_names, reason = _scope_hosts(window, targets)
    if reason:
        return reason
    if not host_names:
        return "There is no monitored device to put into downtime."

    _hosts, services = targets
    by_host: dict[str, list[str]] = {}
    for host, service in services:
        by_host.setdefault(host, []).append(service)

    comment = occurrence_comment(window.WindowID, occurrence.Start_At)
    start, end = epoch(occurrence.Start_At), epoch(occurrence.End_At)
    for host in host_names:
        if retry:
            # A failed earlier attempt may have scheduled some of these already.
            commands.cancel_downtime_by_host_name(host, comment, targets)
        results = [commands.schedule_host_downtime(host, start, end, comment, "PinPoint", targets)]
        if results[0].ok:
            for service in sorted(by_host.get(host, [])):
                results.append(commands.schedule_service_downtime(host, service, start, end, comment, "PinPoint", targets))
                if not results[-1].ok:
                    break
        failed = next((result for result in results if not result.ok), None)
        if failed:
            return f"{host}: {failed.message}"[:255]
    return None


def cancel_occurrence_downtime(window: MaintenanceWindow, occurrence: MaintenanceOccurrence, targets) -> list[commands.CommandResult]:
    """
    Delete the Nagios downtime of one occurrence (pending or running). A host that is gone from
    Nagios has nothing to delete, so an unknown target is not a failure.
    """
    host_names, _reason = _scope_hosts(window, targets)
    comment = occurrence_comment(window.WindowID, occurrence.Start_At)
    results = []
    for host in host_names:
        result = commands.cancel_downtime_by_host_name(host, comment, targets)
        if not result.ok and result.error == commands.UNKNOWN_TARGET:
            continue
        results.append(result)
    return results


def cancel_live_occurrences(window: MaintenanceWindow, now: datetime, delete_rows: bool) -> list[commands.CommandResult]:
    """
    Remove the Nagios downtime of every occurrence of `window` that has not finished, and mark
    those rows cancelled (or delete them, so an edited window can schedule again). Past
    occurrences are history and stay.
    """
    targets = commands.known_targets()
    results: list[commands.CommandResult] = []
    for occurrence in list(window.Occurrences):
        if occurrence.End_At <= now:
            continue
        if occurrence.Status in (SENT, PENDING, FAILED):
            results.extend(cancel_occurrence_downtime(window, occurrence, targets))
        if delete_rows:
            window.Occurrences.remove(occurrence)
        else:
            occurrence.Status = OCC_CANCELLED
    return results


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def dispatch_due_windows(now: datetime | None = None) -> int:
    """
    Hand every occurrence that starts within LEAD_TIME to Nagios, once. Run every minute by the
    scheduler. Returns how many occurrences were attempted. Never raises: a failure is recorded
    on the occurrence.
    """
    now = now or utcnow()
    attempted = 0
    windows = db.session.scalars(
        sa.select(MaintenanceWindow).where(MaintenanceWindow.Status == ACTIVE)
    ).all()
    targets = None
    for window in windows:
        try:
            upcoming = next_occurrence(window, now)
            if upcoming is None:
                window.Status = COMPLETED
                db.session.commit()
                continue
            start, end = upcoming
            if start - now > LEAD_TIME:
                continue

            occurrence = db.session.scalar(sa.select(MaintenanceOccurrence).where(
                MaintenanceOccurrence.WindowID == window.WindowID,
                MaintenanceOccurrence.Start_At == start,
            ))
            if occurrence is None:
                occurrence = MaintenanceOccurrence(Window=window, Start_At=start, End_At=end, Status=PENDING, Attempts=0)
                db.session.add(occurrence)
            elif occurrence.Status != PENDING:
                continue

            # Claim before sending: the attempt count survives a crash during the send.
            occurrence.Attempts += 1
            db.session.commit()

            if targets is None:
                targets = commands.known_targets()
            reason = _send_occurrence(window, occurrence, targets, retry=occurrence.Attempts > 1)
            attempted += 1
            if reason is None:
                occurrence.Status = SENT
                occurrence.Last_Error = None
                occurrence.Sent_At = now
                window.Last_Occurrence_Sent = start
                create_user_log(window.Created_By, f"Maintenance window {window.WindowID} downtime sent to Nagios for {iso(start)}")
            else:
                occurrence.Last_Error = reason
                if occurrence.Attempts >= MAX_ATTEMPTS:
                    occurrence.Status = FAILED
                    create_user_log(window.Created_By, f"Maintenance window {window.WindowID} failed for {iso(start)}: {reason}"[:255])
                    current_app.logger.warning("Maintenance window %s failed: %s", window.WindowID, reason)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error dispatching maintenance window %s", window.WindowID)
    return attempted
