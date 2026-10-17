"""Read-only, bulk Nagios service history and separately observed current status.

State seconds include native scheduled components exactly once. Missing coverage
includes native indeterminate time and any unaccounted portion of the window.
No database access or snapshot-writing poller is used here.
"""
from datetime import datetime, timezone
import math
import time

import requests
from flask import current_app

STATES = ('ok', 'warning', 'critical', 'unknown')
DURATION_FIELDS = (
    *(f'{state}_seconds' for state in STATES),
    *(f'scheduled_{state}_seconds' for state in STATES),
    'known_seconds', 'no_data_seconds', 'nagios_not_running_seconds',
    'unaccounted_seconds', 'no_recorded_data_seconds', 'window_seconds',
)
ARCHIVE_OPTIONS = {
    'query': 'availability', 'availabilityobjecttype': 'services',
    'statetypes': 'hard', 'assumeinitialstate': 'false',
    'assumestateretention': 'true', 'assumestatesduringnagiosdowntime': 'false',
    'backtrackedarchives': 4,
}


class AvailabilityError(ValueError):
    """A sanitized failure to obtain a valid historical availability report."""


def number(value):
    """Validate a native numeric duration/timestamp without coercing strings."""
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise AvailabilityError('Invalid Nagios service availability response.')
    return value


def checked_data(payload):
    """Validate a CGI success envelope and return its data object."""
    if not isinstance(payload, dict) or not isinstance(payload.get('result'), dict):
        raise AvailabilityError('Invalid Nagios service availability response.')
    code = payload['result'].get('type_code')
    if isinstance(code, bool) or code != 0 or not isinstance(payload.get('data'), dict):
        raise AvailabilityError('Invalid Nagios service availability response.')
    return payload['data']


def summarize(rows):
    """Sum raw seconds first, calculating rounded availability only at output."""
    totals = {key: sum(row[key] for row in rows) for key in DURATION_FIELDS}
    known = totals['known_seconds']
    totals['uptime_pct'] = round(100 * totals['ok_seconds'] / known, 2) if known else None
    return totals


def normalize_services(payload, start, end):
    """Normalize native list/single rows, preserving exact identity and coverage.

    End must precede native query time: Core otherwise synthesizes a current
    pseudo-state for objects without history, even with assumeinitialstate=false.
    Native query_time is milliseconds. A full zero row remains a visible instance.
    """
    data = checked_data(payload)
    query_time = number(payload['result'].get('query_time')) / 1000
    if end <= start or end >= query_time:
        raise AvailabilityError('Invalid Nagios service availability window.')
    if 'services' in data and 'service' not in data and isinstance(data['services'], list):
        raw_rows = data['services']
    elif 'service' in data and 'services' not in data and isinstance(data['service'], dict):
        raw_rows = [data['service']]
    else:
        raise AvailabilityError('Invalid Nagios service availability response.')
    rows, identities = [], set()
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise AvailabilityError('Invalid Nagios service availability response.')
        host, service = raw.get('host_name'), raw.get('description')
        if not isinstance(host, str) or not host or not isinstance(service, str) or not service:
            raise AvailabilityError('Invalid Nagios service availability identity.')
        identity = (host, service)
        if identity in identities:
            raise AvailabilityError('Duplicate Nagios service availability identity.')
        identities.add(identity)
        item = {'hostname': host, 'service': service, 'window_seconds': end - start}
        for state in STATES:
            scheduled = number(raw.get(f'scheduled_time_{state}'))
            item[f'scheduled_{state}_seconds'] = scheduled
            item[f'{state}_seconds'] = number(raw.get(f'time_{state}')) + scheduled
        item['known_seconds'] = sum(item[f'{state}_seconds'] for state in STATES)
        item['no_data_seconds'] = number(raw.get('time_indeterminate_nodata'))
        item['nagios_not_running_seconds'] = number(raw.get('time_indeterminate_notrunning'))
        accounted = item['known_seconds'] + item['no_data_seconds'] + item['nagios_not_running_seconds']
        if accounted > end - start:
            raise AvailabilityError('Contradictory Nagios service availability durations.')
        item['unaccounted_seconds'] = end - start - accounted
        item['no_recorded_data_seconds'] = end - start - item['known_seconds']
        item['uptime_pct'] = round(100 * item['ok_seconds'] / item['known_seconds'], 2) if item['known_seconds'] else None
        rows.append(item)
    return rows


def request_cgi(config_key, params, deadline):
    """Make one configured/authenticated CGI call within the shared timeout budget.

    No upstream exception text, credentials, URL or response content is logged.
    Each call has a maximum ten-second connect/read timeout; the second receives
    only the remaining twenty-second request timeout budget. No retries/redirects.
    """
    timeout = min(10, deadline - time.monotonic())
    if timeout <= 0:
        raise AvailabilityError('Nagios service report request budget exhausted.')
    try:
        response = requests.get(current_app.config[config_key], params=params,
            auth=(current_app.config['NAGIOS_USERNAME'], current_app.config['NAGIOS_PASSWORD']),
            timeout=timeout, allow_redirects=False)
        response.raise_for_status()
        if isinstance(response.status_code, int) and response.status_code != 200:
            raise AvailabilityError('Unable to read service availability from Nagios.')
        return response.json()
    except (requests.RequestException, ValueError, TypeError):
        raise AvailabilityError('Unable to read service availability from Nagios.') from None


def timestamp(value):
    """Convert native milliseconds into an explicit UTC timestamp; zero is absent."""
    value = number(value)
    if not value:
        return None
    try:
        return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        raise AvailabilityError('Invalid Nagios current status timestamp.') from None


def current_services(payload):
    """Normalize one bulk enumerated service list, without fabricating timestamps."""
    data = checked_data(payload)
    hosts = data.get('servicelist')
    if not isinstance(hosts, dict):
        raise AvailabilityError('Invalid Nagios current status response.')
    result = {}
    for host, services in hosts.items():
        if not isinstance(host, str) or not isinstance(services, dict):
            raise AvailabilityError('Invalid Nagios current status response.')
        for service, raw in services.items():
            if not isinstance(service, str) or not isinstance(raw, dict):
                raise AvailabilityError('Invalid Nagios current status response.')
            state = raw.get('status')
            if state not in (*STATES, 'pending'):
                raise AvailabilityError('Invalid Nagios current status response.')
            pending = state == 'pending' or raw.get('has_been_checked') is False
            result[(host, service)] = {
                'state': 'Pending' if pending else {'ok': 'Ok', 'warning': 'Warning', 'critical': 'Critical', 'unknown': 'Unknown'}[state],
                'last_check': None if pending else timestamp(raw.get('last_check', 0)),
                'last_state_change': None if pending else timestamp(raw.get('last_state_change', 0)),
                'plugin_output': None if pending else raw.get('plugin_output') if isinstance(raw.get('plugin_output'), str) else None,
            }
    return result


def read_service_report(start, end):
    """Fetch one archive and at most one status list, joining full identities.

    Archive failure aborts. Current-status failure leaves history with an explicit
    notice and null metadata. No snapshot fallback and no writes are performed.
    """
    deadline = time.monotonic() + 20
    payload = request_cgi('NAGIOS_ARCHIVE_URL', {**ARCHIVE_OPTIONS, 'starttime': start, 'endtime': end}, deadline)
    rows = normalize_services(payload, start, end)
    current, context = {}, {'available': True, 'observed_at': None, 'notice': None}
    if rows:
        try:
            current = current_services(request_cgi('NAGIOS_STATUS_URL',
                {'query': 'servicelist', 'details': 'true', 'formatoptions': 'enumerate'}, deadline))
            context['observed_at'] = datetime.now(timezone.utc).isoformat()
        except AvailabilityError:
            context = {'available': False, 'observed_at': None,
                'notice': 'Current status unavailable. Historical availability is still shown; retry the report to refresh status.'}
    for row in rows:
        row.update(current.get((row['hostname'], row['service']),
            {'state': None, 'last_check': None, 'last_state_change': None, 'plugin_output': None}))
    return rows, context
