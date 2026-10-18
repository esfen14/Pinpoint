"""Read-only, bulk current host status for the host reports.

The host availability archive answers how long each host spent in each state. It
does not say what state a host is in now or when it was last checked, so the host
reports join one bulk `hostlist` read to it by the full Nagios host name. This
mirrors the service reports (`service_availability.read_service_report`): at most
one status call, no per-row calls, no snapshots and no writes. A failed status read
leaves the history visible with an explicit notice and no invented state.
"""
import time
from datetime import datetime, timezone

from app.nagios.service_availability import AvailabilityError, checked_data, request_cgi, timestamp

HOST_STATES = {'up': 'Up', 'down': 'Down', 'unreachable': 'Unreachable'}
UNAVAILABLE_NOTICE = (
    'Current status unavailable. Historical availability is still shown; '
    'retry the report to refresh status.'
)


def current_hosts(payload):
    """Normalize one bulk enumerated host list into {host name: current status}.

    A host that has never been checked is Pending with no timestamps. A zero
    native timestamp means "not recorded" and becomes None, never 1970.
    """
    data = checked_data(payload)
    hostlist = data.get('hostlist')
    if not isinstance(hostlist, dict):
        raise AvailabilityError('Invalid Nagios current status response.')
    result = {}
    for name, raw in hostlist.items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise AvailabilityError('Invalid Nagios current status response.')
        state = raw.get('status')
        if state not in (*HOST_STATES, 'pending'):
            raise AvailabilityError('Invalid Nagios current status response.')
        pending = state == 'pending' or raw.get('has_been_checked') is False
        result[name] = {
            'state': 'Pending' if pending else HOST_STATES[state],
            'last_check': None if pending else timestamp(raw.get('last_check', 0)),
            'last_state_change': None if pending else timestamp(raw.get('last_state_change', 0)),
        }
    return result


def read_current_hosts():
    """Return (current status by host name, context) from one bulk status call.

    The context says whether current status is available, when it was observed and,
    when it is not, a fixed sanitized notice. No upstream text reaches the notice.
    """
    try:
        payload = request_cgi('NAGIOS_STATUS_URL',
            {'query': 'hostlist', 'details': 'true', 'formatoptions': 'enumerate'}, time.monotonic() + 10)
        current = current_hosts(payload)
    except AvailabilityError:
        return {}, {'available': False, 'observed_at': None, 'notice': UNAVAILABLE_NOTICE}
    return current, {'available': True, 'observed_at': datetime.now(timezone.utc).isoformat(), 'notice': None}

