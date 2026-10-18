"""
Report routes for the Network Diagnosis System.

All routes accept a `period` query parameter:
    last_24h  - previous 24 hours from now
    today     - midnight-to-now of the current calendar day
    last_7d   - previous 7 days
    last_30d  - previous 30 days
    last_90d  - previous 90 days
    custom    - requires `start` and `end` (YYYY-MM-DD, both inclusive)

Host reports read Nagios archive host durations. Network/Device Services read
bulk Nagios service archive durations plus separately observed current status.
Alert/notification reports read Nagios archive events.

Routes
------
GET /report/availability
    Host availability report within the selected period. Computes uptime % per
    host from Nagios archive durations and returns a summary of Up/Down/Unreachable
    counts alongside per-host details.

GET /report/hosts-by-os
    Host availability grouped by OS type. Works like /report/availability but
    adds an OS_Type dimension from NetworkDiscovery, with per-OS aggregate
    counts and per-host breakdowns.

GET /report/network-services
    Recorded service availability grouped by description across hosts; separate
    current Nagios service status.

GET /report/device-services
    Recorded service availability grouped by hostname, with separate current status.

GET /report/alerts
    Alert list and summary count fetched from Nagios archivejson.cgi.
    Optional hostname and service filters. Returns raw Nagios alert data.

GET /report/notifications
    Notification list and summary count fetched from Nagios archivejson.cgi.
    Optional hostname and service filters. Returns raw Nagios notification data.

GET /report/availability-detail
    One exact host or service: native state durations, coverage, scheduled
    subdivisions and a reconciled interval timeline (#199).

GET /report/alert-summary
    Problem-event totals, distinct objects and a deterministic top-producer
    ranking over the complete filtered archive result (#199).

GET /report/alert-histogram
    Recurring alert buckets by month, day of month, weekday or 15-minute
    hour of day, with an explicit reporting time zone (#199).
"""

from collections import Counter
from datetime import datetime, timedelta

import sqlalchemy as sa
from flask import request, current_app
from flask_login import login_required

from app import db
from app.api.system import system_bp
from app.api.helper import get_range_custom, success, error
from app.api.helper.database_access.permissions import require_permission
from app.history_models import HostStatus
from app.nagios import report_events
from app.nagios.service_availability import AvailabilityError, read_service_report, summarize
from app.system_models import NetworkDiscovery
from app.nagios.notifications import (
    request_alerts_range,
    request_alert_count_range,
    request_notifications_range,
    request_notification_count_range,
    request_host_availability_range,
    normalize_alert,
    normalize_notification,
    fill_previous_states,
    REPORT_HARD_STATE_TYPE,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _as_list(raw):
    """archivejson sends lists either as a list or as a dict keyed by index."""
    return list(raw.values()) if isinstance(raw, dict) else list(raw or [])


VALID_PERIODS = {"last_24h", "today", "last_7d", "last_30d", "last_90d", "custom"}


def _resolve_period(period, start, end):
    """
    Translate a period name into (start_ts, end_ts, start_dt, end_dt).

    Raises ValueError with a human-readable message on bad input.
    """
    now = datetime.now()

    if period == "today":
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = now

    elif period == "last_24h":
        end_dt = now
        start_dt = now - timedelta(hours=24)

    elif period == "last_7d":
        end_dt = now
        start_dt = now - timedelta(days=7)

    elif period == "last_30d":
        end_dt = now
        start_dt = now - timedelta(days=30)

    elif period == "last_90d":
        end_dt = now
        start_dt = now - timedelta(days=90)

    elif period == "custom":
        if not start or not end:
            raise ValueError(
                "'start' and 'end' are required when period=custom (format: YYYY-MM-DD)"
            )
        start_ts, end_ts = get_range_custom(start, end)
        start_dt = datetime.fromtimestamp(start_ts)
        end_dt = datetime.fromtimestamp(end_ts)
        return start_ts, end_ts, start_dt, end_dt

    else:
        raise ValueError(
            f"Invalid period '{period}'. "
            f"Valid values: {', '.join(sorted(VALID_PERIODS))}"
        )

    return int(start_dt.timestamp()), int(end_dt.timestamp()), start_dt, end_dt


def _period_params():
    """
    Extract and validate `period`, `start`, `end` from the request's query string.

    Returns:
        (start_ts, end_ts, start_dt, end_dt, None)  on success
        (None, None, None, None, (body, status))     on error
    """
    period = request.args.get("period", "last_24h").strip().lower()
    start = request.args.get("start") or None
    end = request.args.get("end") or None

    if period not in VALID_PERIODS:
        return None, None, None, None, (
            {
                "message": (
                    f"Invalid period. Valid values: "
                    f"{', '.join(sorted(VALID_PERIODS))}"
                )
            },
            400,
        )

    try:
        start_ts, end_ts, start_dt, end_dt = _resolve_period(period, start, end)
    except ValueError as exc:
        return None, None, None, None, ({"message": str(exc)}, 400)

    return start_ts, end_ts, start_dt, end_dt, None


def _period_meta(period, start_dt, end_dt):
    """Metadata block included in every report response."""
    return {
        "period": period,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "time_zone": report_events.reporting_zone(end_dt.timestamp()),
    }


def _availability_rows(start_ts, end_ts, hostname=None):
    """Read host availability from Nagios archivejson or raise a route error."""
    rows = request_host_availability_range(start_ts, end_ts, hostname=hostname)
    if rows is None:
        raise RuntimeError("Unable to read availability from Nagios.")
    return list(rows.values()) if isinstance(rows, dict) else list(rows)


def _availability_host(row):
    """Normalize one Nagios availability row to the existing report shape."""
    hostname = row.get("hostname") or row.get("host_name") or row.get("name") or ""
    up = float(row.get("time_up") or 0)
    down = float(row.get("time_down") or 0)
    unreachable = float(row.get("time_unreachable") or 0)
    known = up + down + unreachable
    state = row.get("state") or row.get("current_state") or row.get("status")
    if isinstance(state, int):
        state = {0: "Up", 1: "Down", 2: "Down", 4: "Unreachable"}.get(state, "Unknown")
    state = str(state or "Unknown").replace("UP", "Up").replace("DOWN", "Down").replace("UNREACHABLE", "Unreachable")
    return {
        "hostname": hostname,
        "state": state,
        "uptime_pct": round(up / known * 100, 2) if known else None,
        "up_seconds": int(up),
        "down_seconds": int(down),
        "unreachable_seconds": int(unreachable),
        "known_seconds": int(known),
        "last_check": row.get("last_check"),
        "last_state_change": row.get("last_state_change"),
        "_up": up,
        "_known": known,
    }


def _clean_availability_host(host):
    """Remove internal duration fields before serializing a report row."""
    return {key: value for key, value in host.items() if not key.startswith("_")}


# ---------------------------------------------------------------------------
# 1. Host Availability
# ---------------------------------------------------------------------------

@system_bp.get('/report/availability')
@login_required
@require_permission("system.report")
def report_host_availability():
    """
    Host availability within the selected period.

    For each host, reads Nagios archive durations and computes UP seconds /
    known host-state seconds. Missing state/check metadata remains unknown/null.
    Durations are explicit seconds; no snapshot-count field exists.

    Response shape:
    {
        "period":  { "period": "...", "start": "...", "end": "..." },
        "summary": {
            "total": n, "up": n, "down": n, "unreachable": n,
            "uptime_pct": 99.5
        },
        "hosts": [
            {
                "hostname":          "...",
                "state":             "Up|Down|Unreachable",
                "uptime_pct":        99.5,
                "up_seconds":          n,
                "down_seconds":        n,
                "unreachable_seconds": n,
                "known_seconds":       n,
                "last_check":        "ISO-8601 | null",
                "last_state_change": "ISO-8601 | null"
            },
            ...
        ]
    }
    """
    try:
        start_ts, end_ts, start_dt, end_dt, err = _period_params()
        if err:
            return err

        period = request.args.get("period", "last_24h").strip().lower()

        hostname = request.args.get("hostname") or None
        raw_hosts = _availability_rows(start_ts, end_ts, hostname=hostname)
        host_rows = [
            _availability_host(row)
            for row in raw_hosts
            if row.get("hostname") or row.get("host_name") or row.get("name")
        ]
        if hostname:
            host_rows = [host for host in host_rows if host["hostname"] == hostname]
        hosts = [_clean_availability_host(host) for host in sorted(host_rows, key=lambda item: item["hostname"])]
        state_counts = Counter(host["state"] for host in hosts)
        total_known = sum(host["_known"] for host in host_rows)
        total_up = sum(host["_up"] for host in host_rows)
        overall_uptime = round(total_up / total_known * 100, 2) if total_known else None

        return success({
            "period": _period_meta(period, start_dt, end_dt),
            "summary": {
                "total":       len(hosts),
                "up":          state_counts.get("Up", 0),
                "down":        state_counts.get("Down", 0),
                "unreachable": state_counts.get("Unreachable", 0),
                "uptime_pct":  overall_uptime,
            },
            "hosts": hosts,
        })

    except RuntimeError as exc:
        return error(str(exc), 502)
    except Exception:
        current_app.logger.exception("Unexpected error in report_host_availability")
        return error("An unexpected error occurred.", 500)


# ---------------------------------------------------------------------------
# 2. Hosts by OS
# ---------------------------------------------------------------------------

@system_bp.get('/report/hosts-by-os')
@login_required
@require_permission("system.report")
def report_hosts_by_os():
    """
    Host availability within the selected period, grouped by OS type.

    Uses the same Nagios-backed availability data as /report/availability and adds
     the OS_Type dimension
    from NetworkDiscovery.  For each OS group the response includes:
      - a per-host breakdown (same as availability)
      - aggregate UP / DOWN / UNREACHABLE counts
      - an uptime percentage for the group

    Uptime % per group = UP seconds / known host-state seconds * 100.
    Only hosts returned by Nagios are included, with OS from NetworkDiscovery
    or "Unknown". No database snapshot fallback is used.

    Response shape:
    {
        "period": { ... },
        "summary": {
            "total_hosts": n,
            "up": n, "down": n, "unreachable": n,
            "uptime_pct": 99.5
        },
        "by_os": [
            {
                "os_type": "Windows",
                "total":        n,
                "up":           n,
                "down":         n,
                "unreachable":  n,
                "uptime_pct":   99.5,
                "hosts": [
                    {
                        "hostname":          "...",
                        "state":             "Up|Down|Unreachable|No Data",
                        "uptime_pct":        99.5,
                        "last_check":        "ISO-8601 | null",
                        "last_state_change": "ISO-8601 | null"
                    },
                    ...
                ]
            },
            ...
        ]
    }
    """
    try:
        start_ts, end_ts, start_dt, end_dt, err = _period_params()
        if err:
            return err

        period = request.args.get("period", "last_24h").strip().lower()
        hostname = request.args.get("hostname") or None
        raw_hosts = _availability_rows(start_ts, end_ts, hostname=hostname)
        host_rows = [
            _availability_host(row)
            for row in raw_hosts
            if row.get("hostname") or row.get("host_name") or row.get("name")
        ]
        if hostname:
            host_rows = [host for host in host_rows if host["hostname"] == hostname]
        nd_rows = db.session.execute(
            sa.select(NetworkDiscovery.Nagios_Host_Name, NetworkDiscovery.Hostname, NetworkDiscovery.OS_Type)
        ).all()
        os_map = {
            (row.Nagios_Host_Name or row.Hostname): (row.OS_Type or "Unknown")
            for row in nd_rows
            if row.Nagios_Host_Name or row.Hostname
        }
        by_os = {}
        for host in host_rows:
            os_type = os_map.get(host["hostname"], "Unknown")
            by_os.setdefault(os_type, []).append(_clean_availability_host(host))
        groups = []
        for os_type, hosts in sorted(by_os.items()):
            counts = Counter(host["state"] for host in hosts)
            known = sum(host["_known"] for host in host_rows if os_map.get(host["hostname"], "Unknown") == os_type)
            up = sum(host["_up"] for host in host_rows if os_map.get(host["hostname"], "Unknown") == os_type)
            groups.append({
                "os_type": os_type,
                "total": len(hosts),
                "up": counts.get("Up", 0),
                "down": counts.get("Down", 0),
                "unreachable": counts.get("Unreachable", 0),
                "uptime_pct": round(up / known * 100, 2) if known else None,
                "hosts": hosts,
            })
        total_known = sum(host["_known"] for host in host_rows)
        total_up = sum(host["_up"] for host in host_rows)
        return success({
            "period": _period_meta(period, start_dt, end_dt),
            "summary": {
                "total_hosts": len(host_rows),
                "up": sum(group["up"] for group in groups),
                "down": sum(group["down"] for group in groups),
                "unreachable": sum(group["unreachable"] for group in groups),
                "uptime_pct": round(total_up / total_known * 100, 2) if total_known else None,
            },
            "by_os": groups,
        })

    except RuntimeError as exc:
        return error(str(exc), 502)
    except Exception:
        current_app.logger.exception("Unexpected error in report_hosts_by_os")
        return error("An unexpected error occurred.", 500)


# ---------------------------------------------------------------------------
# 3. Network Services Overview
# ---------------------------------------------------------------------------

def service_period():
    """Resolve service-report seconds once, using server-local inclusive dates.

    Rolling/today reports end at the last completed Unix second. Custom end
    dates become the next midnight (exclusive), capped at that completed second.
    This avoids Core's no-history current-state synthesis at query time.
    """
    period = request.args.get('period', 'last_24h').strip().lower()
    now = datetime.now().astimezone()
    completed = int(now.timestamp()) - 1
    if period == 'custom':
        try:
            start_day = datetime.strptime(request.args.get('start', ''), '%Y-%m-%d')
            end_day = datetime.strptime(request.args.get('end', ''), '%Y-%m-%d')
        except ValueError:
            raise ValueError('Custom start and end must be valid YYYY-MM-DD dates.') from None
        if end_day < start_day:
            raise ValueError('end_date must be on or after start_date')
        start = int(start_day.astimezone().timestamp())
        end = min(int((end_day + timedelta(days=1)).astimezone().timestamp()), completed)
    elif period == 'today':
        start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end = completed
    elif period in {'last_24h', 'last_7d', 'last_30d', 'last_90d'}:
        end = completed
        days = {'last_24h': 1, 'last_7d': 7, 'last_30d': 30, 'last_90d': 90}[period]
        start = end - days * 86400
    else:
        raise ValueError('Invalid period. Valid values: ' + ', '.join(sorted(VALID_PERIODS)))
    if start >= end:
        raise ValueError('The report requires a nonempty period before the current time.')
    meta = {
        'period': period, 'start': datetime.fromtimestamp(start).astimezone().isoformat(),
        'end': datetime.fromtimestamp(end).astimezone().isoformat(),
        'start_ts': start, 'end_ts': end, 'end_exclusive': True,
        'time_zone': str(now.tzinfo),
    }
    return start, end, meta


def service_counts(rows):
    """Count separately observed current states across archive instances."""
    counts = Counter(row['state'] for row in rows)
    return {key: counts.get(state, 0) for key, state in (
        ('ok', 'Ok'), ('warning', 'Warning'), ('critical', 'Critical'),
        ('unknown', 'Unknown'), ('pending', 'Pending'), ('unavailable', None))}


def service_report_response(group_by):
    """Build either report from one shared archive/status read and bounded passes."""
    try:
        start, end, meta = service_period()
    except (ValueError, OverflowError):
        return error('Invalid report period or custom date range.', 400)
    try:
        rows, current = read_service_report(start, end)
        grouped = {}
        for row in rows:
            grouped.setdefault(row[group_by], []).append(row)
        groups = []
        for name, instances in sorted(grouped.items()):
            group = {group_by: name, **summarize(instances), **service_counts(instances)}
            if group_by == 'service':
                group.update(total_instances=len(instances), instances=instances)
            else:
                group['services'] = sorted(instances, key=lambda row: row['service'])
            groups.append(group)
        summary = {**summarize(rows), **service_counts(rows),
            'total_hosts': len({row['hostname'] for row in rows}),
            'total_services': len(grouped) if group_by == 'service' else len(rows),
            'total_instances': len(rows)}
        result = {'period': meta, 'current_status': current, 'summary': summary}
        if group_by == 'service':
            result['services'] = groups
        else:
            result.update(hosts=groups, total_hosts=summary['total_hosts'], total_services=len(rows))
        return success(result)
    except AvailabilityError:
        return error('Unable to read service availability from Nagios. Please retry the report.', 502)
    except Exception:
        current_app.logger.error('Unexpected service availability report failure.')
        return error('An unexpected error occurred.', 500)


@system_bp.get('/report/network-services')
@login_required
@require_permission('system.report')
def report_network_services():
    """Return measured service durations grouped by exact service description.

    Headline uptime is OK / known seconds, including scheduled states. UNKNOWN
    is known; no-data/engine-down/unaccounted seconds are separate coverage.
    Current state counts are observed now, regardless of the historical period.
    """
    return service_report_response('service')


# ---------------------------------------------------------------------------
# 4. Services per Device
# ---------------------------------------------------------------------------

@system_bp.get('/report/device-services')
@login_required
@require_permission('system.report')
def report_device_services():
    """Return each archive host/service instance and per-device service availability.

    Device uptime_pct describes its combined service durations, not host uptime.
    Uses the identical calculation and current-status join as Network Services.
    """
    return service_report_response('hostname')


def _csv_arg(name):
    return [v.strip().lower() for v in request.args.get(name, "").split(",") if v.strip()]


def _scope_filter(extra):
    """Validate the optional host/service/both object filter."""
    scope = request.args.get("scope", "").strip().lower()
    if scope in ("", "both"):
        return None
    if scope not in ("host", "service"):
        return ({"message": "scope must be host, service or both."}, 400)
    extra["objecttypes"] = scope
    return None


def _recurrence_arg():
    """Optional ``recurrence=<breakdown>:<bucket index>`` filter from a histogram selection."""
    raw = request.args.get("recurrence", "").strip().lower()
    if not raw:
        return None, None
    breakdown, _, index = raw.partition(":")
    if breakdown not in report_events.BREAKDOWNS or not index.isdigit() \
            or int(index) >= len(report_events.bucket_labels(breakdown)):
        return None, ({"message": "Invalid recurrence filter."}, 400)
    return (breakdown, int(index)), None


def _recurrence_filtered(alerts, recurrence):
    if not recurrence:
        return alerts
    breakdown, index = recurrence
    return [a for a in alerts if report_events.bucket_index(a["timestamp"], breakdown) == index]


def _alert_list_filters():
    """Optional native Alerts filters; with none, the list stays unfiltered."""
    extra = {}
    err = _scope_filter(extra)
    if err:
        return None, err
    state_type = request.args.get("state_type", "").strip().lower()
    if state_type:
        if state_type not in ("hard", "soft", "both"):
            return None, ({"message": "state_type must be hard, soft or both."}, 400)
        extra["statetypes"] = "hard soft" if state_type == "both" else state_type
    states = _csv_arg("states")
    valid_host, valid_service = set(report_events.HOST_STATES_ALL), set(report_events.SERVICE_STATES_ALL)
    if any(s not in valid_host | valid_service for s in states):
        return None, ({"message": "Unknown state filter."}, 400)
    if states:
        host = [s for s in states if s in valid_host]
        svc = [s for s in states if s in valid_service]
        # A state of the other object type matches nothing, so name every state we accept.
        extra["hoststates"] = " ".join(host) if host else "up down unreachable"
        extra["servicestates"] = " ".join(svc) if svc else "ok warning critical unknown"
        if not host:
            extra.setdefault("objecttypes", "service")
        if not svc:
            extra.setdefault("objecttypes", "host")
    return extra, None


_HOST_NOTIFICATION_TYPES = {"down", "unreachable", "recovery", "hostcustom", "hostack", "hostflapstart", "hostflapstop"}
_SERVICE_NOTIFICATION_TYPES = {"critical", "warning", "unknown", "recovery", "custom", "serviceack", "serviceflapstart", "serviceflapstop"}


def _notification_list_filters():
    """Optional native Notifications filters: scope, contact and notification type."""
    extra = {}
    err = _scope_filter(extra)
    if err:
        return None, err
    contact = (request.args.get("contact") or "").strip()
    if contact:
        extra["contactname"] = contact
    types = _csv_arg("notification_types")
    if any(t not in _HOST_NOTIFICATION_TYPES | _SERVICE_NOTIFICATION_TYPES for t in types):
        return None, ({"message": "Unknown notification type."}, 400)
    if types:
        host = [t for t in types if t in _HOST_NOTIFICATION_TYPES]
        svc = [t for t in types if t in _SERVICE_NOTIFICATION_TYPES]
        if host:
            extra["hostnotificationtypes"] = " ".join(host)
        if svc:
            extra["servicenotificationtypes"] = " ".join(svc)
    return extra, None


# ---------------------------------------------------------------------------
# 5. Alerts  (Nagios CGI)
# ---------------------------------------------------------------------------

@system_bp.get('/report/alerts')
@login_required
@require_permission("system.report")
def report_alerts():
    """
    Alert list and summary count from Nagios archivejson.cgi.

    Optional filters:
        hostname  - limit to a specific monitored host
        service   - limit to a specific service on that host

    Response shape:
    {
        "period": { ... },
        "count":  { ... },   # raw Nagios alertcount object  (null on Nagios error)
        "alerts": [ ... ]    # normalized alerts: hostname, service_description, state, last_state, timestamp in seconds (null on Nagios error)
    }
    """
    try:
        start_ts, end_ts, start_dt, end_dt, err = _period_params()
        if err:
            return err

        period   = request.args.get("period", "last_24h").strip().lower()
        hostname = request.args.get("hostname") or None
        service  = request.args.get("service")  or None

        extra, filter_err = _alert_list_filters()
        if filter_err:
            return filter_err
        recurrence, recurrence_err = _recurrence_arg()
        if recurrence_err:
            return recurrence_err

        alerts = request_alerts_range(start_ts, end_ts, hostname=hostname, service=service, extra=extra)
        count  = request_alert_count_range(start_ts, end_ts, hostname=hostname, service=service)

        if alerts is None and count is None:
            return error(
                "Failed to retrieve alert data from Nagios. "
                "Check server logs for details.",
                502,
            )

        return success({
            "period": _period_meta(period, start_dt, end_dt),
            "count":  count,
            "alerts": None if alerts is None else _recurrence_filtered(fill_previous_states(
                [normalize_alert(a, REPORT_HARD_STATE_TYPE) for a in _as_list(alerts)]
            ), recurrence),
        })

    except Exception:
        current_app.logger.exception("Unexpected error in report_alerts")
        return error("An unexpected error occurred.", 500)


# ---------------------------------------------------------------------------
# 6. Notifications  (Nagios CGI)
# ---------------------------------------------------------------------------

@system_bp.get('/report/notifications')
@login_required
@require_permission("system.report")
def report_notifications():
    """
    Notification list and summary count from Nagios archivejson.cgi.

    Optional filters:
        hostname  - limit to a specific monitored host
        service   - limit to a specific service on that host

    Response shape:
    {
        "period": { ... },
        "count":         { ... },   # raw Nagios notificationcount object  (null on Nagios error)
        "notifications": [ ... ]    # normalized notifications: hostname, servicedesc, state, contact, output (null on Nagios error)
    }
    """
    try:
        start_ts, end_ts, start_dt, end_dt, err = _period_params()
        if err:
            return err

        period   = request.args.get("period", "last_24h").strip().lower()
        hostname = request.args.get("hostname") or None
        service  = request.args.get("service")  or None

        extra, filter_err = _notification_list_filters()
        if filter_err:
            return filter_err

        notifications = request_notifications_range(
            start_ts, end_ts, hostname=hostname, service=service, extra=extra
        )
        count = request_notification_count_range(
            start_ts, end_ts, hostname=hostname, service=service
        )

        if notifications is None and count is None:
            return error(
                "Failed to retrieve notification data from Nagios. "
                "Check server logs for details.",
                502,
            )

        return success({
            "period": _period_meta(period, start_dt, end_dt),
            "count":         count,
            "notifications": None if notifications is None else [
                normalize_notification(n) for n in _as_list(notifications)
            ],
        })

    except Exception:
        current_app.logger.exception("Unexpected error in report_notifications")
        return error("An unexpected error occurred.", 500)


# ---------------------------------------------------------------------------
# 7. Availability detail, alert summary and alert histogram (#199)
# ---------------------------------------------------------------------------

def _bounded_period():
    """Resolve the period and enforce the 90-day bound and a positive range."""
    start_ts, end_ts, start_dt, end_dt, err = _period_params()
    if err:
        return None, err
    if end_ts <= start_ts:
        return None, ({"message": "The report end must be after its start."}, 400)
    if end_ts - start_ts > report_events.MAX_RANGE_DAYS * 86400:
        return None, ({"message": f"Reports cover at most {report_events.MAX_RANGE_DAYS} days."}, 400)
    return (start_ts, end_ts, start_dt, end_dt), None


def _flag(name):
    return request.args.get(name, "").strip().lower() in ("1", "true", "yes")


def _event_filters():
    """Validate the shared alert filters; return (filters, error body)."""
    scope = request.args.get("scope", "both").strip().lower()
    state_type = request.args.get("state_type", "hard").strip().lower()
    if scope not in ("host", "service", "both"):
        return None, ({"message": "scope must be host, service or both."}, 400)
    if state_type not in ("hard", "soft", "both"):
        return None, ({"message": "state_type must be hard, soft or both."}, 400)
    states = [s.strip().lower() for s in request.args.get("states", "").split(",") if s.strip()]
    valid = set(report_events.HOST_STATES_ALL) | set(report_events.SERVICE_STATES_ALL)
    if any(state not in valid for state in states):
        return None, ({"message": "Unknown state filter."}, 400)
    return {
        "scope": scope,
        "state_type": state_type,
        "include_recoveries": _flag("include_recoveries"),
        "hostname": request.args.get("hostname") or None,
        "service": request.args.get("service") or None,
        "states": states,
    }, None


def _event_meta(filters, include_initial):
    return {
        "scope": filters["scope"],
        "state_type": filters["state_type"],
        "include_recoveries": filters["include_recoveries"],
        "include_initial": include_initial,
        "hostname": filters["hostname"],
        "service": filters["service"],
        "states": filters["states"],
        "policy": ("HARD problem events only; recoveries and initial-state entries excluded"
                   if filters["state_type"] == "hard" and not filters["include_recoveries"] and not include_initial
                   else "Custom filters applied"),
    }


def _report_event_error(exc):
    current_app.logger.warning("Report archive read failed: %s", exc)
    return error("Unable to read events from Nagios.", 502)


@system_bp.get('/report/availability-detail')
@login_required
@require_permission("system.report")
def report_availability_detail():
    """Exact host (or host + service) detail: native totals and reconciled intervals."""
    try:
        bounds, err = _bounded_period()
        if err:
            return err
        start_ts, end_ts, start_dt, end_dt = bounds
        hostname = (request.args.get("hostname") or "").strip()
        service = (request.args.get("service") or "").strip() or None
        if not hostname:
            return error("hostname is required.", 400)
        period = request.args.get("period", "last_24h").strip().lower()
        try:
            detail = report_events.read_availability_detail(hostname, service, start_ts, end_ts)
        except report_events.ReportNotFound as exc:
            return error(str(exc), 404)
        return success({
            "period": _period_meta(period, start_dt, end_dt),
            "source": "Nagios archive",
            "generated_at": datetime.now().astimezone().isoformat(),
            **detail,
        })
    except AvailabilityError as exc:
        return _report_event_error(exc)
    except Exception:
        current_app.logger.exception("Unexpected error in report_availability_detail")
        return error("An unexpected error occurred.", 500)


@system_bp.get('/report/alert-summary')
@login_required
@require_permission("system.report")
def report_alert_summary():
    """Problem-event totals and top producers from the complete filtered archive result."""
    try:
        bounds, err = _bounded_period()
        if err:
            return err
        start_ts, end_ts, start_dt, end_dt = bounds
        filters, err = _event_filters()
        if err:
            return err
        by = request.args.get("by", "service").strip().lower()
        if by not in ("host", "service"):
            return error("by must be host or service.", 400)
        include_initial = _flag("include_initial")
        period = request.args.get("period", "last_24h").strip().lower()
        events, complete = report_events.fetch_alerts(
            start_ts, end_ts, include_initial=include_initial, **filters)
        payload = {
            "period": _period_meta(period, start_dt, end_dt),
            "source": "Nagios archive",
            "generated_at": datetime.now().astimezone().isoformat(),
            "filters": _event_meta(filters, include_initial),
            "by": by,
            "complete": complete,
        }
        if not complete:
            payload.update({"totals": None, "ranking": [], "top": [],
                            "notice": "Too many alert events to total for this period; narrow the period or filters."})
            return success(payload)
        payload.update(report_events.summarize_alerts(events, by=by))
        payload["notice"] = None
        return success(payload)
    except AvailabilityError as exc:
        return _report_event_error(exc)
    except Exception:
        current_app.logger.exception("Unexpected error in report_alert_summary")
        return error("An unexpected error occurred.", 500)


@system_bp.get('/report/alert-histogram')
@login_required
@require_permission("system.report")
def report_alert_histogram():
    """Recurring alert buckets (month, day of month, weekday, 15-minute hour of day)."""
    try:
        bounds, err = _bounded_period()
        if err:
            return err
        start_ts, end_ts, start_dt, end_dt = bounds
        filters, err = _event_filters()
        if err:
            return err
        breakdown = request.args.get("breakdown", "hour").strip().lower()
        if breakdown not in report_events.BREAKDOWNS:
            return error(f"breakdown must be one of {', '.join(report_events.BREAKDOWNS)}.", 400)
        include_initial = _flag("include_initial")
        period = request.args.get("period", "last_24h").strip().lower()
        events, complete = report_events.fetch_alerts(
            start_ts, end_ts, include_initial=include_initial, **filters)
        payload = {
            "period": _period_meta(period, start_dt, end_dt),
            "source": "Nagios archive",
            "generated_at": datetime.now().astimezone().isoformat(),
            "filters": _event_meta(filters, include_initial),
            "complete": complete,
            "recurring": True,
            "bucketing_note": ("Buckets recur by wall-clock time in the reporting time zone. "
                               "A repeated DST hour counts twice in its bucket; a skipped hour is zero."),
        }
        if not complete:
            payload.update({"breakdown": breakdown, "buckets": [], "series": {}, "total": None,
                            "notice": "Too many alert events to bucket for this period; narrow the period or filters."})
            return success(payload)
        payload.update(report_events.histogram(events, breakdown))
        payload["notice"] = None
        return success(payload)
    except AvailabilityError as exc:
        return _report_event_error(exc)
    except Exception:
        current_app.logger.exception("Unexpected error in report_alert_histogram")
        return error("An unexpected error occurred.", 500)
