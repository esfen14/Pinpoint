"""Native service-duration normalization and read-only CGI contract regressions."""
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from app.nagios.service_availability import (
    AvailabilityError, normalize_services, read_service_report, summarize,
)

FIXTURES = Path(__file__).parents[1] / 'fixtures/nagios_service_availability'


def row(**changes):
    raw = json.loads((FIXTURES / 'scoped.json').read_text())['data']['service']
    return {**raw, **changes}


def envelope(rows):
    return {'result': {'type_code': 0, 'query_time': 1001000}, 'data': {'services': rows}}


def reply(payload):
    return Mock(json=Mock(return_value=payload), raise_for_status=Mock())


def test_native_missing_history_is_visible_as_unaccounted_time():
    native = json.loads((FIXTURES / 'missing-history.json').read_text())
    rows = normalize_services(native, 978307200, 978393600)
    assert len(rows) == 8
    assert rows[0]['known_seconds'] == 0
    assert rows[0]['uptime_pct'] is None
    assert rows[0]['unaccounted_seconds'] == 86400
    assert rows[0]['no_recorded_data_seconds'] == 86400


def test_scheduled_states_are_included_once_and_unknown_is_known():
    rows = normalize_services(envelope([row(time_ok=20, scheduled_time_ok=10,
        time_warning=5, time_critical=10, scheduled_time_critical=5, time_unknown=10,
        time_indeterminate_nodata=10, time_indeterminate_notrunning=20)]), 0, 100)
    assert rows[0]['ok_seconds'] == 30
    assert rows[0]['critical_seconds'] == 15
    assert rows[0]['known_seconds'] == 60
    assert rows[0]['no_recorded_data_seconds'] == 40
    assert rows[0]['unaccounted_seconds'] == 10
    assert rows[0]['uptime_pct'] == 50


def test_aggregate_raw_seconds_without_percentage_reconstruction():
    rows = normalize_services(envelope([
        row(time_ok=1, time_critical=2),
        row(description='other', time_ok=991),
        row(description='zero'),
    ]), 0, 1000)
    total = summarize(rows)
    assert total['ok_seconds'] == 992
    assert total['known_seconds'] == 994
    assert total['uptime_pct'] == 99.8
    assert total['unaccounted_seconds'] == 2006


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf'), True, '12', None])
def test_invalid_duration_rejected(value):
    with pytest.raises(AvailabilityError):
        normalize_services(envelope([row(time_ok=value)]), 0, 100)


@pytest.mark.parametrize('payload', [
    {}, {'result': {'type_code': 1}, 'data': {'services': []}},
    envelope([row(time_ok=101)]), envelope([row(host_name='')]),
    envelope([row(), row()]), envelope([None]),
    {'result': {'type_code': 0, 'query_time': 100000}, 'data': {'services': []}},
    {'result': {'type_code': 0, 'query_time': 1001000}, 'data': {'services': {}}},
])
def test_malformed_duplicate_excess_or_current_window_rejected(payload):
    with pytest.raises(AvailabilityError):
        normalize_services(payload, 0, 100)


def test_single_documented_shape_and_empty():
    payload = envelope([])
    assert normalize_services(payload, 0, 100) == []
    payload['data'] = {'service': row(time_ok=100)}
    assert normalize_services(payload, 0, 100)[0]['uptime_pct'] == 100


def test_bulk_status_identity_pending_missing_and_request_limits(app):
    archive = envelope([row(time_ok=100), row(description='pending'), row(description='missing')])
    status = {'result': {'type_code': 0}, 'data': {'servicelist': {'host-a': {
        'service-1': {'status': 'critical', 'last_check': 99000, 'last_state_change': 80000,
                      'plugin_output': 'critical now'},
        'pending': {'status': 'pending', 'last_check': 0},
    }}}}
    with app.app_context(), patch('app.nagios.service_availability.requests.get',
            side_effect=[reply(archive), reply(status)]) as get:
        rows, context = read_service_report(0, 100)
    assert get.call_count == 2
    assert get.call_args_list[0].kwargs['params']['assumeinitialstate'] == 'false'
    assert get.call_args_list[1].kwargs['params'] == {
        'query': 'servicelist', 'details': 'true', 'formatoptions': 'enumerate'}
    assert all(0 < call.kwargs['timeout'] <= 10 for call in get.call_args_list)
    assert rows[0]['state'] == 'Critical'
    assert rows[0]['last_check'] == '1970-01-01T00:01:39+00:00'
    assert rows[1]['state'] == 'Pending' and rows[1]['last_check'] is None
    assert rows[2]['state'] is None and rows[2]['plugin_output'] is None
    assert context['available'] is True and context['observed_at']


@pytest.mark.parametrize('failure', [requests.Timeout('secret'), requests.HTTPError('secret'), ValueError('secret')])
def test_archive_failure_is_sanitized_and_never_requests_status(app, caplog, failure):
    with app.app_context(), patch('app.nagios.service_availability.requests.get', side_effect=failure) as get:
        with pytest.raises(AvailabilityError, match='Unable to read service availability from Nagios'):
            read_service_report(0, 100)
    assert get.call_count == 1
    assert 'secret' not in caplog.text


def test_status_failure_retains_archive_with_null_metadata(app):
    with app.app_context(), patch('app.nagios.service_availability.requests.get',
            side_effect=[reply(envelope([row(time_ok=100)])), requests.Timeout('secret')]):
        rows, context = read_service_report(0, 100)
    assert rows[0]['uptime_pct'] == 100
    assert rows[0]['state'] is None and rows[0]['last_check'] is None
    assert context['available'] is False and context['notice']


def test_native_recorded_transitions_before_and_at_bounds_brief_outage_and_downtime():
    native = json.loads((FIXTURES / 'recorded-transitions.json').read_text())
    start = native['data']['selectors']['starttime'] // 1000
    end = native['data']['selectors']['endtime'] // 1000
    measured = normalize_services(native, start, end)[0]
    # Real Core parsed an initial OK before the range, a 30-second critical
    # outage, 100 seconds scheduled maintenance (50 OK/50 critical), UNKNOWN,
    # 100 seconds stopped engine, and a WARNING transition exactly at end.
    assert measured['ok_seconds'] == 720
    assert measured['critical_seconds'] == 130
    assert measured['unknown_seconds'] == 50
    assert measured['warning_seconds'] == 0
    assert measured['known_seconds'] == 900
    assert measured['nagios_not_running_seconds'] == 100
    assert measured['unaccounted_seconds'] == 0
    assert measured['uptime_pct'] == 80


def test_status_call_receives_only_remaining_request_budget(app):
    with app.app_context(), patch('app.nagios.service_availability.time.monotonic', side_effect=[0, 0, 15]), patch(
        'app.nagios.service_availability.requests.get', side_effect=[reply(envelope([row(time_ok=100)])),
        reply({'result': {'type_code': 0}, 'data': {'servicelist': {}}})]
    ) as get:
        rows, context = read_service_report(0, 100)
    assert get.call_args_list[0].kwargs['timeout'] == 10
    assert get.call_args_list[1].kwargs['timeout'] == 5
    assert rows[0]['state'] is None and context['available'] is True


def test_exhausted_status_budget_and_empty_archive_never_make_extra_calls(app):
    with app.app_context(), patch('app.nagios.service_availability.time.monotonic', side_effect=[0, 0, 21]), patch(
        'app.nagios.service_availability.requests.get', return_value=reply(envelope([row(time_ok=100)]))
    ) as get:
        rows, context = read_service_report(0, 100)
    assert get.call_count == 1 and context['available'] is False
    assert rows[0]['uptime_pct'] == 100
    with app.app_context(), patch('app.nagios.service_availability.requests.get', return_value=reply(envelope([]))) as get:
        rows, context = read_service_report(0, 100)
    assert rows == [] and get.call_count == 1
