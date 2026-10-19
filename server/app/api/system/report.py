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
from app.nagios.host_current_status import read_current_hosts
from app.nagios.service_availability import AvailabilityError, read_service_report, summarize
from app.network_discovery.device_identity import devices_by_host_name, monitoring_state
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
    }


def _availability_rows(start_ts, end_ts, hostname=None):
    """Read host availability from Nagios archivejson or raise a route error."""
    rows = request_host_availability_range(start_ts, end_ts, hostname=hostname)
    if rows is None:
        raise RuntimeError("Unable to read availability from Nagios.")
    return list(rows.values()) if isinstance(rows, dict) else list(rows)


def _availability_host(row):
    """Normalize one Nagios archive availability row to the report row shape.

    The archive row carries durations only. State, last check and last state change
    are joined from one bulk current-status read by _attach_current_status().
    """
    hostname = row.get("hostname") or row.get("host_name") or row.get("name") or ""
    up = float(row.get("time_up") or 0)
    down = float(row.get("time_down") or 0)
    unreachable = float(row.get("time_unreachable") or 0)
    known = up + down + unreachable
    return {
        "hostname": hostname,
        "state": None,
        "uptime_pct": round(up / known * 100, 2) if known else None,
        "known_seconds": int(known),
        "last_check": None,
        "last_state_change": None,
        "_up": up,
        "_known": known,
    }


def _monitored_host_names():
    """Nagios host names of the devices Nagios is checking now (monitoring state "monitored")."""
    return {
        name for name, device in devices_by_host_name().items()
        if monitoring_state(device) == "monitored"
    }


def _attach_current_status(host_rows):
    """Join one bulk current-status read into the rows and return its context.

    A host with no status entry, or any host when the read fails, keeps a null state
    and null times; nothing is guessed. The context says whether status was available.
    """
    current, context = read_current_hosts()
    for host in host_rows:
        status = current.get(host["hostname"])
        host["state"] = status["state"] if status else None
        host["last_check"] = status["last_check"] if status else None
        host["last_state_change"] = status["last_state_change"] if status else None
    return context


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

    For each monitored host, reads Nagios archive durations and computes UP seconds /
    known host-state seconds; known_seconds is that known-state duration. State, last check and last state change come from one bulk current-status
    read joined by Nagios host name; if that read fails, or a host has no entry, they
    stay null and "current_status" says so. Only hosts of devices that are monitored
    now are listed (not Missing, paused, retired or merged devices, and not Nagios's
    own localhost).

    Response shape:
    {
        "period":  { "period": "...", "start": "...", "end": "..." },
        "summary": {
            "total": n, "up": n, "down": n, "unreachable": n,
            "uptime_pct": 99.5
        },
        "current_status": { "available": true, "observed_at": "ISO-8601 | null", "notice": "text | null" },
        "hosts": [
            {
                "hostname":          "...",
                "state":             "Up|Down|Unreachable|Pending|null",
                "uptime_pct":        99.5,
                "known_seconds":     n,
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
        monitored = _monitored_host_names()
        host_rows = [host for host in host_rows if host["hostname"] in monitored]
        current_status = _attach_current_status(host_rows)
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
            "current_status": current_status,
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
    or "Unknown". State, last check and last state change are joined from one bulk
    current-status read (see /report/availability). No database snapshot fallback
    is used.

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
                        "state":             "Up|Down|Unreachable|Pending|null",
                        "uptime_pct":        99.5,
                        "known_seconds":     n,
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
        current_status = _attach_current_status(host_rows)
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
            "current_status": current_status,
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

        alerts = request_alerts_range(start_ts, end_ts, hostname=hostname, service=service)
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
            "alerts": None if alerts is None else fill_previous_states(
                [normalize_alert(a) for a in _as_list(alerts)]
            ),
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

        notifications = request_notifications_range(
            start_ts, end_ts, hostname=hostname, service=service
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
