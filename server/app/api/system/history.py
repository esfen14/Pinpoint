"""
history.py — Alerts and Notifications History page routes.

Serves the two-tab history browsing interface defined in
Alerts_Notifications_History_Requirements.md.

Alerts come from Nagios archivejson.cgi (state-change events).
Notifications come from the same CGI (contact events sent by Nagios).
Acknowledgement records come from ACK_HISTORY in system_models.py (main DB).

Both endpoints are read-only. Filtering, sorting, and pagination follow
the same pattern as the other paginated routes in this project.

Routes
------
GET /system/history/alerts
    Paginated list of Nagios alert state-change events with filters for
    time range, type, host, service, new state, state type, and
    acknowledgement status.

GET /system/history/alerts/detail
    Full detail for a single alert event — untruncated plugin output,
    acknowledgement record if any, and linked notifications.

GET /system/history/notifications
    Paginated list of Nagios notification events with filters for
    time range, type, host, service, state, and contact.

GET /system/history/notifications/detail
    Full detail for a single notification event — full message,
    all contacts, and a link back to the related alert if it exists.
"""

from datetime import datetime, timezone, timedelta
import re
import hashlib
import json

import sqlalchemy as sa
from flask import request, current_app
from flask_login import login_required

from app import db
from app.api.system import system_bp
from app.api.helper import success, error
from app.api.helper.database_access.permissions import require_permission
from app.api.helper.converter import get_range_day, get_range_custom
from app.system_models import AckHistory, AckAction, User
from app.nagios.notifications import (
    request_alerts_range,
    request_notifications_range,
    normalize_notification,
    normalize_alert,
    fill_previous_states,
)
from app.nagios.pinpoint_events import (
    SOURCE_NAGIOS,
    SOURCE_PINPOINT,
    get_scan_event,
    get_scan_events,
)

# Valid per-page values from the spec (§3.5).
_VALID_PER_PAGE = {25, 50, 100}

# Time range presets in days. 1 hour and 6 hours are handled separately
# since get_range_day works in whole days.
_PRESET_HOURS = {
    "1h":   1,
    "6h":   6,
    "24h":  24,
    "7d":   168,
    "30d":  720,
}


# ==========================================================
# HELPERS
# ==========================================================

def resolve_time_range(preset, start_date, end_date):
    """
    Return (start_ts, end_ts) as UNIX integers for the requested time range.

    If preset is given it takes priority over start_date/end_date.
    Preset values: "1h", "6h", "24h", "7d", "30d".
    Custom bounds are either two YYYY-MM-DD dates (server-local full days,
    for backward compatibility) or two ISO 8601 date-times with explicit UTC
    offsets (Z or ±HH:MM). Date-time bounds are inclusive to the second.
    Returns (None, None) if the inputs are invalid.
    """
    now = int(datetime.now(timezone.utc).timestamp())

    if preset:
        hours = _PRESET_HOURS.get(preset)
        if hours is None:
            return None, None
        start_ts = now - hours * 3600
        return start_ts, now

    if start_date or end_date:
        if not (start_date and end_date):
            return None, None
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_date) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", end_date):
            try:
                return get_range_custom(start_date, end_date)
            except ValueError:
                return None, None
        pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})"
        if not (re.fullmatch(pattern, start_date) and re.fullmatch(pattern, end_date)):
            return None, None
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if start > end:
                return None, None
            return int(start.timestamp()), int(end.timestamp())
        except (ValueError, OverflowError):
            return None, None

    # Default: last 24 hours
    return now - 86400, now


def normalize_nagios_list(raw):
    """
    Normalize the Nagios archivejson response to a plain list.

    Nagios returns alert/notification lists as a dict keyed by stringified
    index e.g. {"0": {...}, "1": {...}} rather than a proper list.
    """
    if isinstance(raw, dict):
        return list(raw.values())
    return list(raw) if raw else []


def event_id(event, kind):
    """Build a deterministic locator from canonical Nagios archive fields."""
    fields = (["hostname", "service_description", "timestamp", "state", "state_type", "plugin_output"]
              if kind == "alert" else
              ["hostname", "servicedesc", "timestamp", "state", "contact", "notificationmethod", "output"])
    payload = json.dumps([event.get(f) for f in fields], separators=(",", ":"), ensure_ascii=False)
    return f"{event['timestamp']}:{hashlib.sha256((kind + payload).encode()).hexdigest()}"


def locator_range(value):
    """Validate an event ID and return single-second archive query bounds."""
    match = re.fullmatch(r"([1-9]\d{0,11}):[0-9a-f]{64}", value)
    return (int(match.group(1)), int(match.group(1))) if match else None


def related_alert(notification, alerts):
    """Find the latest preceding same-target, same-state alert in five minutes."""
    matches = [a for a in alerts if a['hostname'] == notification['hostname']
               and a.get('service_description') == notification.get('servicedesc')
               and a['state'] == notification['state']
               and 0 <= notification['timestamp'] - a['timestamp'] <= 300]
    return max(matches, key=lambda a: a['timestamp'], default=None)


def ack_actions(hostname=None, service_name=None):
    """Return chronological acknowledgement actions, optionally for one target."""
    query = sa.select(AckHistory)
    if hostname is not None:
        query = query.where(AckHistory.Hostname == hostname,
                            AckHistory.Service_Name == service_name)
    return db.session.scalars(query.order_by(AckHistory.Actioned_At, AckHistory.AckHistoryID)).all()


def build_ack_map(alerts, actions):
    """Map problem events to the latest acknowledgement in their active episode.

    A recovery closes an episode, as does an AUTO_RESOLVED action if the
    recovery event is absent from the archive window. A manual unacknowledge
    ends the active acknowledgement but preserves the historical badge.
    """
    from collections import defaultdict

    events_by_target = defaultdict(list)
    actions_by_target = defaultdict(list)
    for alert in alerts:
        events_by_target[(alert.get("hostname"), alert.get("service_description") or None)].append(alert)
    for action in actions:
        actions_by_target[(action.Hostname, action.Service_Name)].append(action)

    result = {}
    for target, events in events_by_target.items():
        events.sort(key=lambda event: event.get("timestamp") or 0)
        actions = actions_by_target[target]
        episodes = []
        current = []
        auto_resolutions = [int(action.Actioned_At.replace(tzinfo=timezone.utc).timestamp())
                            for action in actions if action.Action == AckAction.AUTO_RESOLVED]
        for event in events:
            timestamp = event.get("timestamp") or 0
            if current:
                closed = next((boundary for boundary in auto_resolutions
                               if current[0]["timestamp"] <= boundary <= timestamp), None)
                if closed is not None:
                    episodes.append((current, closed))
                    current = []
            if (event.get("state") or "").upper() in ("OK", "UP"):
                if current:
                    episodes.append((current, timestamp))
                    current = []
            else:
                current.append(event)
        if current:
            end = next((boundary for boundary in auto_resolutions
                        if boundary >= current[0]["timestamp"]), None)
            episodes.append((current, end))

        for episode, end in episodes:
            start = episode[0]["timestamp"]
            acknowledgements = [action for action in actions
                                if action.Action == AckAction.ACKNOWLEDGED
                                and start <= int(action.Actioned_At.replace(tzinfo=timezone.utc).timestamp())
                                and (end is None or int(action.Actioned_At.replace(tzinfo=timezone.utc).timestamp()) < end)]
            if acknowledgements:
                for event in episode:
                    result[(target, event["timestamp"], event.get("state"))] = acknowledgements[-1]
    return result


def serialize_ack(ack_row):
    """
    Serialize an AckHistory row into a frontend-ready dict, or return None.

    Joins to User to resolve the actor's full name.
    """
    if ack_row is None:
        return None

    actor = db.session.get(User, ack_row.ActorUserID) if ack_row.ActorUserID else None
    full_name = f"{actor.First_Name} {actor.Last_Name}" if actor else None

    return {
        "acknowledged_by": full_name,
        "acknowledged_at": ack_row.Actioned_At.isoformat(),
        "comment":         ack_row.Comment,
    }


def sort_history_items(items, sort_by, order, columns, aliases=None):
    """Sort list rows by a column, breaking equal values by newest timestamp."""
    field = (aliases or {}).get(sort_by, sort_by)
    if field not in columns:
        field = "timestamp"
    if field != "timestamp":
        items.sort(key=lambda item: item["timestamp"], reverse=True)
    items.sort(key=lambda item: (item[field] or "").casefold() if field not in
               ("timestamp", "duration_seconds", "acknowledged") else item[field],
               reverse=order == "desc")


def paginate_list(items, page, per_page):
    """
    Slice a list into a page and return it with pagination metadata.

    Returns a dict with keys: items, page, per_page, total, pages,
    has_next, has_prev.
    """
    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items":    items[start:end],
        "page":     page,
        "per_page": per_page,
        "total":    total,
        "pages":    pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


# ==========================================================
# ALERTS HISTORY
# ==========================================================

@system_bp.get('/history/alerts')
@login_required
@require_permission("system.history")
def alerts_history():
    """
    Return a paginated list of Nagios alert state-change events.

    Filters, sorts, and paginates in-memory after fetching from Nagios
    because archivejson.cgi does not support server-side pagination.

    Query params:
        preset      — time range shortcut: 1h | 6h | 24h | 7d | 30d
        start_date  — YYYY-MM-DD or offset-aware ISO 8601 date-time
        end_date    — same format as start_date (used without preset)
        type        — host | service (omit for all)
        hostname    — filter to one host
        service     — filter to one service
        new_state   — filter by resulting state string (e.g. CRITICAL, DOWN, OK)
        state_type  — hard | soft (omit for all)
        ack_filter  — all | acknowledged | unacknowledged (default all)
        sort_by     — timestamp (default) | hostname | new_state | duration
        order       — desc (default) | asc
        page        — default 1
        per_page    — 25 (default) | 50 | 100
    """
    try:
        preset     = request.args.get("preset", default="", type=str).lower()
        start_date = request.args.get("start_date", default="", type=str)
        end_date   = request.args.get("end_date", default="", type=str)
        type_f     = request.args.get("type", default="", type=str).lower()
        hostname_f = request.args.get("hostname", default="", type=str)
        service_f  = request.args.get("service", default="", type=str)
        new_state_f= request.args.get("new_state", default="", type=str).upper()
        state_type_f= request.args.get("state_type", default="", type=str).lower()
        ack_filter = request.args.get("ack_filter", default="all", type=str).lower()
        sort_by    = request.args.get("sort_by", default="timestamp", type=str).lower()
        order      = request.args.get("order", default="desc", type=str).lower()
        page       = request.args.get("page", default=1, type=int)
        per_page   = request.args.get("per_page", default=25, type=int)
        locator    = request.args.get("event_id", default="", type=str)
        if locator and locator_range(locator) is None:
            return error("Invalid event_id.", 400)

        if page < 1:
            return error("page must be greater than 0.", 400)
        if per_page not in _VALID_PER_PAGE:
            return error(f"per_page must be one of: {sorted(_VALID_PER_PAGE)}.", 400)
        if order not in ("asc", "desc"):
            return error("order must be 'asc' or 'desc'.", 400)
        if ack_filter not in ("all", "acknowledged", "unacknowledged"):
            return error("ack_filter must be 'all', 'acknowledged', or 'unacknowledged'.", 400)

        start_ts, end_ts = (locator_range(locator) if locator else resolve_time_range(
            preset or None, start_date or None, end_date or None
        ))
        if start_ts is None:
            return error(
                "Invalid time range. Use a preset (1h, 6h, 24h, 7d, 30d) "
                "or provide start_date and end_date as YYYY-MM-DD.", 400
            )

        raw = request_alerts_range(
            start_ts, end_ts,
            hostname=hostname_f or None,
            service=service_f or None,
        )

        if raw is None:
            return error("Failed to retrieve alert history from Nagios.", 502)

        alerts = fill_previous_states([normalize_alert(a) for a in normalize_nagios_list(raw)])
        if locator:
            alerts = [a for a in alerts if event_id(a, 'alert') == locator]

        # Include earlier transitions so an episode beginning before the selected
        # window is not confused with an acknowledgement from a prior episode.
        episode_raw = request_alerts_range(0, end_ts)
        if episode_raw is None:
            return error("Failed to retrieve alert history from Nagios.", 502)
        episode_alerts = [normalize_alert(a) for a in normalize_nagios_list(episode_raw)]
        ack_map = build_ack_map(episode_alerts, ack_actions())

        items = []
        for alert in alerts:
            hostname    = alert.get("hostname", "")
            service     = alert.get("service_description") or None
            alert_type  = "service" if service else "host"
            new_state   = (alert.get("state") or "").upper()
            prev_state  = (alert.get("last_state") or "").upper()
            state_type  = (alert.get("state_type") or "").lower()
            timestamp   = alert.get("timestamp", 0)
            duration    = alert.get("duration_seconds") or 0
            output      = alert.get("plugin_output") or ""

            # Apply filters
            if type_f and alert_type != type_f:
                continue
            if new_state_f and new_state != new_state_f:
                continue
            if state_type_f and state_type != state_type_f:
                continue

            is_acked = ((hostname, service), timestamp, new_state) in ack_map
            if ack_filter == "acknowledged" and not is_acked:
                continue
            if ack_filter == "unacknowledged" and is_acked:
                continue

            items.append({
                "event_id":     event_id(alert, "alert"),
                "timestamp":    timestamp,
                "type":         alert_type,
                "hostname":     hostname,
                "service_name": service,
                "previous_state": prev_state,
                "new_state":    new_state,
                "state_type":   state_type,
                "duration_seconds": duration,
                "plugin_output": output[:200],
                "acknowledged": is_acked,
            })

        sort_history_items(items, sort_by, order, {
            "timestamp", "type", "hostname", "service_name", "previous_state",
            "new_state", "state_type", "duration_seconds", "plugin_output", "acknowledged",
        }, {"duration": "duration_seconds"})

        result = paginate_list(items, page, per_page)
        return success(result)

    except Exception:
        current_app.logger.exception(
            "Unexpected error in GET /system/history/alerts"
        )
        return error("An unexpected error occurred.", 500)


@system_bp.get('/history/alerts/detail')
@login_required
@require_permission("system.history")
def alerts_history_detail():
    """
    Return full detail for a single alert event.

    Includes untruncated plugin output, acknowledgement record if any,
    recovery duration if the new state is OK or UP, and any Nagios
    notification events linked to this alert within a 5-minute window.

    Query params (all required):
        hostname    — host the alert belongs to
        timestamp   — UNIX timestamp of the alert event (integer)
        new_state   — the resulting state string (e.g. CRITICAL, DOWN)
        service     — service name (omit for host-level alerts)
    """
    try:
        hostname  = request.args.get("hostname", default="", type=str)
        timestamp = request.args.get("timestamp", default=0, type=int)
        new_state = request.args.get("new_state", default="", type=str).upper()
        service   = request.args.get("service", default="", type=str) or None

        if not hostname:
            return error("hostname is required.", 400)
        if not timestamp:
            return error("timestamp is required.", 400)

        # Fetch a narrow window around the event to find this specific row.
        window_start = timestamp - 5
        window_end   = timestamp + 5
        raw = request_alerts_range(
            window_start, window_end,
            hostname=hostname,
            service=service,
        )

        if raw is None:
            return error("Failed to retrieve alert detail from Nagios.", 502)

        alerts = [normalize_alert(a) for a in normalize_nagios_list(raw)]
        alerts = [a for a in alerts if a['hostname'] == hostname and a['service_description'] == service]

        # Find the specific event — match on timestamp and new_state.
        alert = next(
            (a for a in alerts
             if a.get("timestamp") == timestamp
             and (a.get("state") or "").upper() == new_state),
            None
        )

        if alert is None:
            return error("Alert event not found.", 404)

        full_output  = alert.get("plugin_output") or ""
        prev_state   = (alert.get("last_state") or "").upper()
        state_type   = (alert.get("state_type") or "").lower()
        duration     = alert.get("duration_seconds") or 0

        # Load preceding transitions to identify the event's problem episode.
        episode_raw = request_alerts_range(0, int(datetime.now(timezone.utc).timestamp()),
                                           hostname=hostname, service=service)
        if episode_raw is None:
            return error("Failed to retrieve alert detail from Nagios.", 502)
        episode_alerts = [normalize_alert(a) for a in normalize_nagios_list(episode_raw)]
        ack_map = build_ack_map(episode_alerts, ack_actions(hostname, service))
        ack = serialize_ack(ack_map.get(((hostname, service), timestamp, new_state)))

        # Recovery duration — meaningful when new state is OK or UP
        recovery_duration = None
        if new_state in ("OK", "UP"):
            recovery_duration = duration

        # Linked notifications — look for notifications in a ±5 minute window
        # around this alert's timestamp for the same host/service.
        notif_raw = request_notifications_range(
            timestamp - 300, timestamp + 300,
            hostname=hostname,
            service=service,
        )
        linked_notifications = []
        if notif_raw:
            nearby = [normalize_notification(n) for n in normalize_nagios_list(notif_raw)]
            alert_raw = request_alerts_range(timestamp - 300, timestamp + 300,
                                             hostname=hostname, service=service)
            nearby_alerts = ([normalize_alert(a) for a in normalize_nagios_list(alert_raw)]
                             if alert_raw else [])
            for notif in nearby:
                if related_alert(notif, nearby_alerts) != alert:
                    continue
                linked_notifications.append({
                    "event_id": event_id(notif, 'notification'),
                    "timestamp": notif['timestamp'],
                    "contact": notif['contact'],
                    "state": notif['state'],
                    "message": notif['output'][:200],
                })

        return success({
            "event_id":           event_id(alert, "alert"),
            "hostname":           hostname,
            "service_name":       service,
            "timestamp":          timestamp,
            "type":               "service" if service else "host",
            "previous_state":     prev_state,
            "new_state":          new_state,
            "state_type":         state_type,
            "duration_seconds":   duration,
            "plugin_output":      full_output,
            "acknowledged":       ack is not None,
            "ack":                ack,
            "recovery_duration":  recovery_duration,
            "linked_notifications": linked_notifications,
        })

    except Exception:
        current_app.logger.exception(
            "Unexpected error in GET /system/history/alerts/detail"
        )
        return error("An unexpected error occurred.", 500)


# ==========================================================
# NOTIFICATIONS HISTORY
# ==========================================================

@system_bp.get('/history/notifications')
@login_required
@require_permission("system.history")
def notifications_history():
    """
    Return a paginated list of Nagios notification events.

    Filters, sorts, and paginates in-memory after fetching from Nagios.

    Query params:
        preset      — time range shortcut: 1h | 6h | 24h | 7d | 30d
        start_date  — YYYY-MM-DD or offset-aware ISO 8601 date-time
        end_date    — same format as start_date (used without preset)
        type        — host | service (omit for all)
        hostname    — filter to one host
        service     — filter to one service
        state       — filter by state at notification time (e.g. CRITICAL)
        contact     — filter by contact name (partial match)
        sort_by     — timestamp (default) | hostname | state
        order       — desc (default) | asc
        page        — default 1
        per_page    — 25 (default) | 50 | 100
    """
    try:
        preset     = request.args.get("preset", default="", type=str).lower()
        start_date = request.args.get("start_date", default="", type=str)
        end_date   = request.args.get("end_date", default="", type=str)
        type_f     = request.args.get("type", default="", type=str).lower()
        hostname_f = request.args.get("hostname", default="", type=str)
        service_f  = request.args.get("service", default="", type=str)
        state_f    = request.args.get("state", default="", type=str).upper()
        contact_f  = request.args.get("contact", default="", type=str).lower()
        source_f   = request.args.get("source", default="", type=str).lower()
        sort_by    = request.args.get("sort_by", default="timestamp", type=str).lower()
        order      = request.args.get("order", default="desc", type=str).lower()
        page       = request.args.get("page", default=1, type=int)
        per_page   = request.args.get("per_page", default=25, type=int)
        locator    = request.args.get("event_id", default="", type=str)
        if locator and locator_range(locator) is None:
            return error("Invalid event_id.", 400)

        if page < 1:
            return error("page must be greater than 0.", 400)
        if per_page not in _VALID_PER_PAGE:
            return error(f"per_page must be one of: {sorted(_VALID_PER_PAGE)}.", 400)
        if order not in ("asc", "desc"):
            return error("order must be 'asc' or 'desc'.", 400)
        if locator and source_f == SOURCE_PINPOINT:
            return error("event_id locates Nagios notifications only.", 400)
        if source_f not in ("", SOURCE_NAGIOS, SOURCE_PINPOINT):
            return error("source must be 'nagios' or 'pinpoint'.", 400)

        start_ts, end_ts = (locator_range(locator) if locator else resolve_time_range(
            preset or None, start_date or None, end_date or None
        ))
        if start_ts is None:
            return error(
                "Invalid time range. Use a preset (1h, 6h, 24h, 7d, 30d) "
                "or provide start_date and end_date as YYYY-MM-DD.", 400
            )

        notifications = []
        nagios_unavailable = False
        if source_f != SOURCE_PINPOINT:
            raw = request_notifications_range(
                start_ts, end_ts,
                hostname=hostname_f or None,
                service=service_f or None,
            )

            if raw is None:
                nagios_unavailable = True
            else:
                notifications = normalize_nagios_list(raw)

        items = []
        for notif in notifications:
            notif     = normalize_notification(notif)
            if locator and event_id(notif, 'notification') != locator:
                continue
            hostname  = notif["hostname"]
            service   = notif["servicedesc"]
            notif_type= "service" if service else "host"
            state     = notif["state"]
            contact   = notif["contact"]
            timestamp = notif.get("timestamp", 0)
            message   = notif["output"]
            method    = notif["notificationmethod"]

            if type_f and notif_type != type_f:
                continue
            if state_f and state != state_f:
                continue
            if contact_f and contact_f not in contact.lower():
                continue

            items.append({
                "source":       SOURCE_NAGIOS,
                "event_id":     event_id(notif, "notification"),
                "timestamp":    timestamp,
                "type":         notif_type,
                "hostname":     hostname,
                "service_name": service,
                "state":        state,
                "contact":      contact,
                "method":       method,
                "message":      message[:200],
            })

        if not locator and source_f != SOURCE_NAGIOS and not (type_f or hostname_f or service_f or contact_f):
            for event in get_scan_events(start_ts, end_ts):
                if state_f and event["state"] != state_f:
                    continue
                items.append({
                    "source":       SOURCE_PINPOINT,
                    "id":           event["id"],
                    "timestamp":    event["timestamp"],
                    "type":         "scan",
                    "hostname":     "Pinpoint",
                    "service_name": event["title"],
                    "state":        event["state"],
                    "contact":      "",
                    "method":       "",
                    "message":      event["message"][:200],
                })

        sort_history_items(items, sort_by, order, {
            "timestamp", "type", "hostname", "service_name", "state", "contact",
            "method", "message",
        })

        if nagios_unavailable and not items:
            return error("Failed to retrieve notification history from Nagios.", 502)

        result = paginate_list(items, page, per_page)
        result["nagios_unavailable"] = nagios_unavailable
        return success(result)

    except Exception:
        current_app.logger.exception(
            "Unexpected error in GET /system/history/notifications"
        )
        return error("An unexpected error occurred.", 500)


@system_bp.get('/history/notifications/detail')
@login_required
@require_permission("system.history")
def notifications_history_detail():
    """
    Return full detail for a single notification event.

    Includes the full untruncated message, all contacts notified, and
    a link to the related alert event if one exists in the same ±5 minute
    window for the same host and service.

    Query params (all required):
        hostname    — host the notification belongs to
        timestamp   — UNIX timestamp of the notification event (integer)
        service     — service name (omit for host-level notifications)
    """
    try:
        hostname  = request.args.get("hostname", default="", type=str)
        timestamp = request.args.get("timestamp", default=0, type=int)
        service   = request.args.get("service", default="", type=str) or None

        if request.args.get("source", default="", type=str).lower() == SOURCE_PINPOINT:
            event = get_scan_event(request.args.get("id", default=0, type=int))
            if event is None:
                return error("Notification event not found.", 404)
            return success({
                "source":       SOURCE_PINPOINT,
                "id":           event["id"],
                "hostname":     "Pinpoint",
                "service_name": event["title"],
                "timestamp":    event["timestamp"],
                "type":         "scan",
                "state":        event["state"],
                "contacts":     [],
                "method":       "",
                "message":      event["message"],
                "linked_alert": None,
            })

        if not hostname:
            return error("hostname is required.", 400)
        if not timestamp:
            return error("timestamp is required.", 400)

        # Narrow fetch to find this specific notification.
        raw = request_notifications_range(
            timestamp - 5, timestamp + 5,
            hostname=hostname,
            service=service,
        )

        if raw is None:
            return error("Failed to retrieve notification detail from Nagios.", 502)

        notifications = [normalize_notification(n) for n in normalize_nagios_list(raw)]
        notifications = [n for n in notifications if n['hostname'] == hostname and n['servicedesc'] == service]

        # Find the specific notification by timestamp (normalized to seconds,
        # the same value the list sent).
        notif = next(
            (n for n in notifications if n.get("timestamp") == timestamp),
            None
        )

        if notif is None:
            return error("Notification event not found.", 404)

        state   = notif["state"]
        contact = notif["contact"]
        message = notif["output"]
        method  = notif["notificationmethod"]

        # All contacts — Nagios may list multiple separated by commas.
        contacts = [c.strip() for c in contact.split(",") if c.strip()]

        # Linked alert — look for an alert in a ±5 minute window.
        alert_raw = request_alerts_range(
            timestamp - 300, timestamp + 300,
            hostname=hostname,
            service=service,
        )
        linked_alert = None
        if alert_raw:
            alerts = [normalize_alert(a) for a in normalize_nagios_list(alert_raw)]
            a = related_alert(notif, alerts)
            if a:
                linked_alert = {
                    "event_id": event_id(a, 'alert'),
                    "timestamp": a['timestamp'],
                    "new_state": a['state'],
                    "prev_state": a['last_state'],
                }

        return success({
            "source":       SOURCE_NAGIOS,
            "event_id":     event_id(notif, "notification"),
            "hostname":     hostname,
            "service_name": service,
            "timestamp":    timestamp,
            "type":         "service" if service else "host",
            "state":        state,
            "contacts":     contacts,
            "method":       method,
            "message":      message,
            "linked_alert": linked_alert,
        })

    except Exception:
        current_app.logger.exception(
            "Unexpected error in GET /system/history/notifications/detail"
        )
        return error("An unexpected error occurred.", 500)

