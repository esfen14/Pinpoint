"""Both service report APIs use the same measured seconds, never snapshots."""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.nagios.service_availability import AvailabilityError, normalize_services
from tests.support.seed_helpers import _make_host, _make_service
from app.history_models import ServiceStateType
from tests.unit.test_service_availability import row, envelope, reply

ROUTES = ['/api/system/report/network-services', '/api/system/report/device-services']


def durations():
    rows = normalize_services(envelope([
        row(time_ok=1, time_critical=2),
        row(host_name='host-b', time_ok=991),
        row(description='zero'),
    ]), 0, 1000)
    for r in rows:
        r.update(state='Critical', last_check=None, last_state_change=None, plugin_output=None)
    return rows


def assert_no_counts(value):
    if isinstance(value, dict):
        assert not any('snapshot' in k.lower() for k in value)
        for v in value.values(): assert_no_counts(v)
    elif isinstance(value, list):
        for v in value: assert_no_counts(v)


def test_same_instances_weighted_totals_and_database_independence(logged_in_client, db_session):
    host = _make_host(db_session, 'snapshot-only')
    _make_service(db_session, host.Hostname, 'db-only', state=ServiceStateType.OK)
    db_session.session.commit()
    with patch('app.api.system.report.read_service_report', return_value=(durations(), {
            'available': False, 'observed_at': None, 'notice': 'Current status unavailable.'})) as reader:
        network = logged_in_client.get(ROUTES[0]).get_json()['data']
        device = logged_in_client.get(ROUTES[1]).get_json()['data']
    assert reader.call_count == 2
    assert network['summary']['uptime_pct'] == 99.8
    assert network['summary']['known_seconds'] == 994
    assert network['summary']['total_instances'] == 3
    assert device['summary']['uptime_pct'] == 99.8
    assert device['total_hosts'] == 2
    a = {(i['hostname'], g['service']): i for g in network['services'] for i in g['instances']}
    b = {(h['hostname'], i['service']): i for h in device['hosts'] for i in h['services']}
    assert a.keys() == b.keys()
    for key in a:
        for field in ('ok_seconds', 'known_seconds', 'unaccounted_seconds', 'uptime_pct'):
            assert a[key][field] == b[key][field]
    assert_no_counts(network); assert_no_counts(device)
    assert network['current_status']['available'] is False
    assert next(h for h in device['hosts'] if h['hostname']=='host-a')['uptime_pct'] == 33.33


@pytest.mark.parametrize('route', ROUTES)
def test_empty_and_failed_archive_are_distinct(logged_in_client, db_session, route):
    with patch('app.api.system.report.read_service_report', return_value=([], {'available': True, 'observed_at': None, 'notice': None})):
        response = logged_in_client.get(route)
    assert response.status_code == 200
    assert response.get_json()['data']['summary']['uptime_pct'] is None
    with patch('app.api.system.report.read_service_report', side_effect=AvailabilityError('Invalid Nagios service availability response.')):
        response = logged_in_client.get(route)
    assert response.status_code == 502
    assert response.get_json()['success'] is False


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('query', ['period=bad', 'period=custom',
    'period=custom&start=2024-02-30&end=2024-03-01',
    'period=custom&start=2024-03-02&end=2024-03-01',
    'period=custom&start=2999-01-01&end=2999-01-02'])
def test_bad_period_precedes_upstream(logged_in_client, db_session, route, query):
    with patch('app.api.system.report.read_service_report') as reader:
        assert logged_in_client.get(f'{route}?{query}').status_code == 400
    reader.assert_not_called()


@pytest.mark.parametrize('route', ROUTES)
def test_login(client, db_session, route):
    assert client.get(route).status_code in (302, 401)


@pytest.mark.parametrize('route', ROUTES)
def test_permission(limited_client, db_session, route):
    assert limited_client.get(route).status_code == 403


@pytest.mark.parametrize('route', ROUTES)
def test_custom_inclusive_dates_and_completed_seconds(logged_in_client, db_session, route):
    with patch('app.api.system.report.read_service_report', return_value=([], {})) as reader:
        response = logged_in_client.get(route+'?period=custom&start=2024-01-01&end=2024-01-02')
    assert response.status_code == 200
    start, end = reader.call_args.args
    assert end-start == 172800
    meta = response.get_json()['data']['period']
    assert meta['start_ts'] == start and meta['end_ts'] == end
    assert meta['start'].endswith('+00:00') or datetime.fromisoformat(meta['start']).utcoffset() is not None
    with patch('app.api.system.report.read_service_report', return_value=([], {})) as reader:
        response = logged_in_client.get(route)
    assert reader.call_args.args[1] < datetime.now(timezone.utc).timestamp()


@pytest.mark.parametrize('route', ROUTES)
def test_one_bulk_archive_and_status_independent_of_hosts(logged_in_client, db_session, route):
    raw = [row(host_name=f'h-{i}', time_ok=5) for i in range(300)]
    payload = envelope(raw); payload['result']['query_time'] = int(datetime.now(timezone.utc).timestamp()*1000)+1000
    status = {'result': {'type_code': 0}, 'data': {'servicelist': {}}}
    with patch('app.nagios.service_availability.requests.get', side_effect=[reply(payload),reply(status)]) as get:
        response = logged_in_client.get(route)
    assert response.status_code == 200
    assert get.call_count == 2


@pytest.mark.parametrize('zone,date,expected', [
    ('UTC', '2024-03-10', 86400),
    ('Asia/Kathmandu', '2024-03-10', 86400),
    ('America/New_York', '2024-03-10', 82800),
    ('America/New_York', '2024-11-03', 90000),
])
def test_custom_dates_use_server_calendar_including_dst(app, monkeypatch, zone, date, expected):
    import os
    import time
    from app.api.system.report import service_period
    original = os.environ.get('TZ')
    try:
        monkeypatch.setenv('TZ', zone)
        time.tzset()
        with app.test_request_context('/?period=custom&start='+date+'&end='+date):
            start, end, meta = service_period()
        assert end-start == expected
        assert datetime.fromisoformat(meta['start']).utcoffset() is not None
    finally:
        if original is None:
            os.environ.pop('TZ', None)
        else:
            os.environ['TZ'] = original
        time.tzset()
