"""Read-only Nagios archive readers for report detail, alert summary and histogram.

Probed against Nagios Core 4.5.11 (#199, see docs/plans/Reports_Requirements.md):
archivejson.cgi list queries accept ``start``/``count`` paging, send timestamps
in milliseconds, send state bitmasks (host 1/2/4, service 8/16/32/64) and state
types HARD=1 / SOFT=2. ``statechangelist`` begins with an "Initial ... Pseudo-State"
entry at the range start; availability totals with ``assumeinitialstate=false``
treat the time before the first real transition as no data, so that entry is
never used as a recorded state.

Everything here is bounded (per-call timeout, one shared deadline, page, request
and row limits) and fails closed: when completeness cannot be proven the caller
gets ``complete=False`` and must suppress totals. No database or snapshot data
is read, and nothing is written.
"""
from collections import Counter
from datetime import datetime
import re
import time

from app.nagios.notifications import REPORT_HARD_STATE_TYPE, _alert_state, _timestamp_seconds, normalize_alert
from app.nagios.service_availability import AvailabilityError, checked_data, number, request_cgi

PAGE_SIZE = 500
MAX_EVENTS = 20_000          # rows kept per report; more than this is "incomplete"
MAX_REQUESTS = 45            # archive calls per report (MAX_EVENTS / PAGE_SIZE + slack)
BUDGET_SECONDS = 30          # overall time budget for one report
MAX_RANGE_DAYS = 90          # custom ranges and rolling periods
RECONCILE_TOLERANCE = 2      # seconds between interval sums and native durations

HOST_PROBLEMS = ("down", "unreachable")
SERVICE_PROBLEMS = ("warning", "critical", "unknown")
HOST_STATES_ALL = ("up", "down", "unreachable")
SERVICE_STATES_ALL = ("ok", "warning", "critical", "unknown")
_INITIAL = re.compile(r"^Initial (Host|Service) Pseudo-State", re.I)

BREAKDOWNS = ("month", "day_of_month", "weekday", "hour")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_WEEKDAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


class ReportSourceError(AvailabilityError):
    """A sanitized failure to read an event list from Nagios."""


class ReportNotFound(ReportSourceError):
    """Nagios has no such host or service (it answers success with no object)."""


def is_initial(event):
    """True for Core's synthetic start-of-range state, which is not a recorded event."""
    return bool(_INITIAL.match(str(event.get("plugin_output") or "")))


def fetch_list(query, params, list_key, deadline=None):
    """Read every page of one archive list query.

    Returns ``(rows, complete)``. ``complete`` is False when the row or request
    limit stopped the traversal before the last (short) page, so callers never
    present a truncated list as the full result.
    """
    deadline = deadline or time.monotonic() + BUDGET_SECONDS
    rows, start, requests_made = [], 0, 0
    while True:
        if requests_made >= MAX_REQUESTS or len(rows) >= MAX_EVENTS:
            return rows, False
        payload = request_cgi(
            "NAGIOS_ARCHIVE_URL",
            {**params, "query": query, "start": start, "count": PAGE_SIZE},
            deadline,
        )
        requests_made += 1
        data = checked_data(payload)
        page = data.get(list_key)
        if not isinstance(page, list):
            raise ReportSourceError("Invalid Nagios archive response.")
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows, True
        start += PAGE_SIZE


def _names(values):
    return " ".join(values)


def alert_params(start_ts, end_ts, scope="both", state_type="hard", include_recoveries=False,
                 hostname=None, service=None, states=None):
    """Native alertlist options for the shared problem-event policy.

    ``scope`` is host, service or both; ``state_type`` hard, soft or both. Problem
    states only unless recoveries are requested; ``states`` (lowercase native names)
    narrows further.
    """
    params = {"starttime": start_ts, "endtime": end_ts}
    if scope == "host":
        params["objecttypes"] = "host"
    elif scope == "service":
        params["objecttypes"] = "service"
    else:
        params["objecttypes"] = "host service"
    params["statetypes"] = "hard soft" if state_type == "both" else state_type
    wanted = set(states or ())
    host = [s for s in (HOST_STATES_ALL if include_recoveries else HOST_PROBLEMS)
            if not wanted or s in wanted]
    svc = [s for s in (SERVICE_STATES_ALL if include_recoveries else SERVICE_PROBLEMS)
           if not wanted or s in wanted]
    if host:
        params["hoststates"] = _names(host)
    if svc:
        params["servicestates"] = _names(svc)
    if hostname:
        params["hostname"] = hostname
    if service:
        params["servicedescription"] = service
    return params


def fetch_alerts(start_ts, end_ts, include_initial=False, deadline=None, **filters):
    """Normalized alert events (never the synthetic initial entries by default)."""
    rows, complete = fetch_list("alertlist", alert_params(start_ts, end_ts, **filters), "alertlist", deadline)
    events = [normalize_alert(row, REPORT_HARD_STATE_TYPE) for row in rows if isinstance(row, dict)]
    if not include_initial:
        events = [event for event in events if not is_initial(event)]
    return events, complete


def _healthy(event):
    return event["state"] in ("UP", "OK")


def summarize_alerts(events, by="service", limit=10):
    """Problem-event totals and a deterministic top-producer ranking.

    Ranking: event count descending, then host name, then service name. Recoveries
    (when present in ``events``) are counted separately and never as problems.
    """
    problems = [e for e in events if not _healthy(e)]
    recoveries = len(events) - len(problems)
    groups = {}
    for event in problems:
        host = event["hostname"]
        service = event["service_description"] if by == "service" else None
        entry = groups.setdefault((host, service or ""), {
            "hostname": host, "service": service, "total": 0, "states": Counter(),
            "first": event["timestamp"], "last": event["timestamp"]})
        entry["total"] += 1
        entry["states"][event["state"]] += 1
        entry["first"] = min(entry["first"], event["timestamp"])
        entry["last"] = max(entry["last"], event["timestamp"])
    ranked = sorted(groups.values(), key=lambda g: (-g["total"], g["hostname"], g["service"] or ""))
    for rank, entry in enumerate(ranked, 1):
        entry["rank"] = rank
        entry["states"] = dict(sorted(entry["states"].items()))
    state_counts = Counter(e["state"] for e in problems)
    return {
        "totals": {
            "problem_events": len(problems),
            "recovery_events": recoveries,
            "host_problem_events": sum(1 for e in problems if not e["service_description"]),
            "service_problem_events": sum(1 for e in problems if e["service_description"]),
            "distinct_hosts": len({e["hostname"] for e in problems}),
            "distinct_objects": len({(e["hostname"], e["service_description"] or "") for e in problems}),
            "states": dict(sorted(state_counts.items())),
        },
        "ranking": ranked,
        "top": ranked[:limit],
    }


def _local(ts):
    """Wall-clock time in the server's reporting zone (DST-aware)."""
    return datetime.fromtimestamp(ts).astimezone()


def bucket_labels(breakdown):
    if breakdown == "month":
        return list(_MONTHS)
    if breakdown == "day_of_month":
        return [str(day) for day in range(1, 32)]
    if breakdown == "weekday":
        return list(_WEEKDAYS)
    if breakdown == "hour":
        return [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 15, 30, 45)]
    raise ValueError(f"Invalid breakdown. Valid values: {', '.join(BREAKDOWNS)}")


def bucket_index(ts, breakdown):
    """Recurring-bucket index in wall-clock time.

    DST: a repeated wall-clock hour counts in the same bucket twice; a skipped
    hour has zero events. Weekday 0 is Sunday, as in the Core histogram.
    """
    local = _local(ts)
    if breakdown == "month":
        return local.month - 1
    if breakdown == "day_of_month":
        return local.day - 1
    if breakdown == "weekday":
        return (local.weekday() + 1) % 7
    return local.hour * 4 + local.minute // 15


def histogram(events, breakdown):
    """Stable, zero-filled recurring buckets with per-state series and totals."""
    labels = bucket_labels(breakdown)
    series = {}
    totals = [0] * len(labels)
    for event in events:
        index = bucket_index(event["timestamp"], breakdown)
        state = event["state"] or "UNKNOWN"
        series.setdefault(state, [0] * len(labels))[index] += 1
        totals[index] += 1
    return {
        "breakdown": breakdown,
        "buckets": [{"label": label, "total": totals[i],
                     "states": {state: counts[i] for state, counts in sorted(series.items())}}
                    for i, label in enumerate(labels)],
        "series": dict(sorted(series.items())),
        "total": sum(totals),
    }


def reporting_zone(ts=None):
    """Name and UTC offset of the zone used for period bounds and bucketing."""
    local = _local(ts if ts is not None else time.time())
    offset = local.utcoffset()
    return {"name": local.tzname(), "utc_offset_seconds": int(offset.total_seconds()) if offset else 0}


# ---------------------------------------------------------------------------
# Availability detail: native totals plus intervals from statechangelist
# ---------------------------------------------------------------------------

HOST_DETAIL_STATES = ("up", "down", "unreachable")
SERVICE_DETAIL_STATES = ("ok", "warning", "critical", "unknown")
NO_DATA = "no_data"


def native_totals(raw, states, start, end):
    """Normalize one native availability row for the detail drawer.

    State totals already include their scheduled part exactly once. Percentages are
    of total requested time and of known time; either is None for a zero
    denominator. Scheduled time is reported as a subdivision, never added.
    """
    window = end - start
    row, known, scheduled = {}, 0, {}
    for state in states:
        value = number(raw.get(f"time_{state}")) + number(raw.get(f"scheduled_time_{state}"))
        row[state] = value
        scheduled[state] = number(raw.get(f"scheduled_time_{state}"))
        known += value
    no_data = number(raw.get("time_indeterminate_nodata"))
    not_running = number(raw.get("time_indeterminate_notrunning"))
    if known + no_data + not_running > window + RECONCILE_TOLERANCE:
        raise ReportSourceError("Contradictory Nagios availability durations.")
    unaccounted = max(0, window - known - no_data - not_running)
    return {
        "window_seconds": window,
        "known_seconds": known,
        "no_recorded_data_seconds": window - known,
        "no_data_seconds": no_data,
        "nagios_not_running_seconds": not_running,
        "unaccounted_seconds": unaccounted,
        "states": [{
            "state": state,
            "seconds": row[state],
            "scheduled_seconds": scheduled[state],
            "unscheduled_seconds": row[state] - scheduled[state],
            "pct_of_total": round(100 * row[state] / window, 2) if window else None,
            "pct_of_known": round(100 * row[state] / known, 2) if known else None,
        } for state in states],
    }


def build_intervals(events, start, end, states):
    """State intervals clipped to [start, end] from statechangelist events.

    Events are native normalized entries (``timestamp`` seconds, lowercase
    ``state`` via ``state_key``). The synthetic initial entry is ignored: time
    before the first real transition is ``no_data`` with an unknown onset, an
    absent predecessor is never a recovery, and the last interval is marked
    continuing. Events before ``start`` (a recorded predecessor) clip to it and
    are marked ``clipped_start``. Consecutive identical states merge.
    """
    real = sorted((e for e in events if not is_initial(e) and e["state_key"] in states),
                  key=lambda e: e["timestamp"])
    points = []
    for event in real:
        if event["timestamp"] >= end:
            continue
        if points and points[-1]["state"] == event["state_key"]:
            continue
        points.append({"at": event["timestamp"], "state": event["state_key"],
                       "info": event.get("plugin_output") or ""})
    intervals = []

    def add(at, until, state, info, clipped_start=False, unknown_onset=False):
        at, until = max(at, start), min(until, end)
        if until <= at:
            return
        intervals.append({"start": at, "end": until, "duration_seconds": until - at,
                          "state": state, "information": info,
                          "clipped_start": clipped_start, "unknown_onset": unknown_onset,
                          "continuing": False})

    first = points[0]["at"] if points else end
    if first > start:
        add(start, first, NO_DATA, "No recorded state before the first transition in this period.",
            unknown_onset=True)
    for index, point in enumerate(points):
        until = points[index + 1]["at"] if index + 1 < len(points) else end
        add(point["at"], until, point["state"], point["info"], clipped_start=point["at"] < start)
    if intervals:
        intervals[-1]["continuing"] = True
    return intervals


def reconcile(intervals, totals):
    """Compare interval sums with native state durations (and no-data time)."""
    sums = Counter()
    for interval in intervals:
        sums[interval["state"]] += interval["duration_seconds"]
    differences = {}
    for item in totals["states"]:
        delta = sums[item["state"]] - item["seconds"]
        if abs(delta) > RECONCILE_TOLERANCE:
            differences[item["state"]] = delta
    no_data_delta = sums[NO_DATA] - totals["no_recorded_data_seconds"]
    if abs(no_data_delta) > RECONCILE_TOLERANCE:
        differences[NO_DATA] = no_data_delta
    return {"matches": not differences, "tolerance_seconds": RECONCILE_TOLERANCE,
            "differences": differences}


def state_key(event, is_service):
    """Lowercase native state name for an event (``None`` when not recognised)."""
    name = _alert_state(event.get("state"), is_service)
    return name.lower() if name else None


def read_availability_detail(hostname, service, start, end, deadline=None):
    """Native totals and reconciled intervals for one exact host or service.

    If intervals cannot be reconciled with native totals no intervals are
    returned and the discrepancy is reported instead of inventing a timeline.
    """
    deadline = deadline or time.monotonic() + BUDGET_SECONDS
    is_service = bool(service)
    states = SERVICE_DETAIL_STATES if is_service else HOST_DETAIL_STATES
    base = {"starttime": start, "endtime": end, "hostname": hostname,
            "assumeinitialstate": "false", "assumestateretention": "true",
            "assumestatesduringnagiosdowntime": "false", "backtrackedarchives": 4,
            "statetypes": "hard"}
    availability = {**base, "query": "availability",
                    "availabilityobjecttype": "services" if is_service else "hosts"}
    if is_service:
        availability["servicedescription"] = service
    key = "service" if is_service else "host"
    data = checked_data(request_cgi("NAGIOS_ARCHIVE_URL", availability, deadline))
    raw = data.get(key)
    if raw is None:
        raise ReportNotFound("No such host or service in Nagios.")
    if not isinstance(raw, dict):
        raise ReportSourceError("Invalid Nagios availability response.")
    totals = native_totals(raw, states, start, end)

    # The displayed totals exclude time while Nagios was not running (the same assumption as the
    # report tables). State-change events continue through that time, so the timeline is checked
    # against a second native answer that carries the state through Nagios downtime.
    assumed = {**availability, "assumestatesduringnagiosdowntime": "true"}
    assumed_raw = checked_data(request_cgi("NAGIOS_ARCHIVE_URL", assumed, deadline)).get(key)
    if not isinstance(assumed_raw, dict):
        raise ReportSourceError("Invalid Nagios availability response.")
    assumed_totals = native_totals(assumed_raw, states, start, end)

    change_params = {k: v for k, v in base.items()
                     if k in ("starttime", "endtime", "hostname", "backtrackedarchives", "statetypes")}
    change_params["objecttype"] = "service" if is_service else "host"
    if is_service:
        change_params["servicedescription"] = service
    rows, complete = fetch_list("statechangelist", change_params, "statechangelist", deadline)
    events = []
    for row in rows:
        if not isinstance(row, dict):
            raise ReportSourceError("Invalid Nagios archive response.")
        event = normalize_alert(row, REPORT_HARD_STATE_TYPE)
        event["timestamp"] = _timestamp_seconds(row.get("timestamp"))
        event["state_key"] = state_key(row, is_service)
        events.append(event)
    result = {"object": {"hostname": hostname, "service": service or None}, "totals": totals,
              "complete": complete, "intervals": [], "reconciliation": None,
              "intervals_available": False, "notice": None}
    if not complete:
        result["notice"] = "Too many state changes to list for this period; narrow the period."
        return result
    intervals = build_intervals(events, start, end, states)
    reconciliation = reconcile(intervals, assumed_totals)
    reconciliation["basis"] = "native availability with the state carried through Nagios downtime"
    reconciliation["nagios_not_running_seconds"] = totals["nagios_not_running_seconds"]
    result["reconciliation"] = reconciliation
    if reconciliation["matches"]:
        result["intervals"] = intervals
        result["intervals_available"] = True
    else:
        result["notice"] = ("The interval list does not agree with Nagios's native durations, "
                            "so it is withheld. The totals above are native.")
    if reconciliation["matches"] and totals["nagios_not_running_seconds"]:
        result["notice"] = ("Intervals continue the last recorded state through the "
                            f"{totals['nagios_not_running_seconds']} s Nagios was not running; the totals above exclude that time.")
    return result
