"""Escalation CRUD, recipient eligibility, config generation and rollback."""
from unittest.mock import patch
import re

import pytest
import sqlalchemy as sa

from app import db
from app.system_models import UserStatus
from tests.unit.test_host_recipients import devices, assign, generate, objects

pytestmark = pytest.mark.usefixtures('monitoring_plugins')
URL = '/api/system/escalations'


@pytest.fixture
def writer():
    with patch('app.network_discovery.create_host_cfg.regenerate_and_apply_config_status',
               return_value=('applied', 'Applied.')) as fake:
        yield fake


def payload(**changes):
    return dict(first_notification=2, last_notification=5, interval_minutes=10,
                contact_group='system_users', host_id=None, **changes)


def save(client, **changes):
    data = payload()
    data.update(changes)
    response = client.post(URL, json=data)
    assert response.status_code == 200, response.get_json()
    return response.get_json()['data']


@pytest.mark.parametrize('method,path', [('get', ''), ('post', ''), ('put', '/1'), ('delete', '/1')])
def test_permission(limited_client, method, path):
    assert getattr(limited_client, method)(URL + path, json={}).status_code == 403


@pytest.mark.parametrize('method,path', [('get', ''), ('post', ''), ('put', '/1'), ('delete', '/1')])
def test_login(client, db_session, method, path):
    assert getattr(client, method)(URL + path, json={}).status_code in (401, 302)


@pytest.mark.parametrize('change,field', [
    ({'first_notification': 8}, 'first_notification'),
    ({'first_notification': True}, 'first_notification'),
    ({'last_notification': 0}, 'last_notification'),
    ({'interval_minutes': -1}, 'interval_minutes'),
    ({'interval_minutes': 1441}, 'interval_minutes'),
    ({'interval_minutes': 0.5}, 'interval_minutes'),
    ({'contact_group': 'unknown'}, 'contact_group'),
    ({'contact_group': 'system_users\n} define command {'}, 'contact_group'),
    ({'contact_group': []}, 'contact_group'),
    ({'host_id': True}, 'host_id'),
    ({'host_id': 99999}, 'host_id'),
])
def test_invalid(logged_in_client, writer, change, field):
    data = payload()
    data.update(change)
    response = logged_in_client.post(URL, json=data)
    assert response.status_code == 400
    assert field in response.get_json()['message']
    writer.assert_not_called()


def test_create_update_reload_delete(logged_in_client, db_session, writer, devices):
    item = save(logged_in_client, host_id=devices[0].NetDiscoveryID)
    assert item['id'] > 0
    assert item['active']
    data = payload()
    data['interval_minutes'] = 0
    response = logged_in_client.put(f"{URL}/{item['id']}", json=data)
    assert response.status_code == 200
    assert response.get_json()['data']['host_id'] is None
    listing = logged_in_client.get(URL).get_json()['data']
    assert listing['items'][0]['interval_minutes'] == 0
    assert listing['groups'][0]['name'] == 'system_users'
    assert listing['hosts']
    assert logged_in_client.delete(f"{URL}/{item['id']}").status_code == 200
    assert logged_in_client.get(URL).get_json()['data']['items'] == []
    assert writer.call_count == 3


@pytest.mark.parametrize('method', ['put', 'delete'])
def test_missing(logged_in_client, writer, method):
    assert getattr(logged_in_client, method)(URL + '/99999', json=payload()).status_code == 404
    writer.assert_not_called()


@pytest.mark.parametrize('operation', ['create', 'update', 'delete'])
@pytest.mark.parametrize('failure', ['validation', 'reload', 'exception'])
def test_rollback(logged_in_client, db_session, writer, operation, failure):
    from app.system_models import Escalation
    item = save(logged_in_client)
    before = logged_in_client.get(URL).get_json()['data']['items']
    if failure == 'exception':
        writer.side_effect = RuntimeError('writer unavailable')
    else:
        writer.return_value = ('failed', f'{failure} rejected')
    if operation == 'create':
        response = logged_in_client.post(URL, json=payload())
    elif operation == 'update':
        data = payload()
        data['interval_minutes'] = 7
        response = logged_in_client.put(f"{URL}/{item['id']}", json=data)
    else:
        response = logged_in_client.delete(f"{URL}/{item['id']}")
    assert response.status_code == (500 if failure == 'exception' else 422)
    if failure != 'exception':
        assert f'{failure} rejected' in response.get_json()['message']
    db.session.expire_all()
    assert db.session.scalar(sa.select(sa.func.count()).select_from(Escalation)) == 1
    assert logged_in_client.get(URL).get_json()['data']['items'] == before


@pytest.mark.parametrize('ineligible', ['opt-out', 'inactive', 'suspended'])
def test_empty_group_suppressed_and_save_explains(logged_in_client, app, db_session, admin_user,
                                                 devices, writer, monkeypatch, tmp_path, ineligible):
    first = devices[0]
    assign(first, admin_user)
    group = f'pinpoint_host_{first.NetDiscoveryID}'
    item = save(logged_in_client, contact_group=group, host_id=first.NetDiscoveryID)
    text = generate(app, monkeypatch, tmp_path)
    assert len(objects(text, 'hostescalation')) == 1
    assert len(objects(text, 'serviceescalation')) == 1
    if ineligible == 'opt-out':
        admin_user.Receive_Email_Alerts = False
    else:
        admin_user.Status = UserStatus.INACTIVE if ineligible == 'inactive' else UserStatus.SUSPENDED
    db.session.commit()
    text = generate(app, monkeypatch, tmp_path)
    assert not objects(text, 'hostescalation') and not objects(text, 'serviceescalation')
    # Use the still-authenticated test administrator only after restoring account status;
    # alert opt-out still leaves the selected group empty.
    admin_user.Status = UserStatus.ACTIVE
    admin_user.Receive_Email_Alerts = False
    db.session.commit()
    response = logged_in_client.post(URL, json={**payload(), 'contact_group': group})
    assert response.status_code == 400
    assert 'eligible' in response.get_json()['message']
    listing = logged_in_client.get(URL).get_json()['data']['items']
    assert listing[0]['id'] == item['id'] and not listing[0]['active']
    assert 'eligible' in listing[0]['reason']


def test_scoped_blocks_and_delete_default_exact(logged_in_client, app, db_session, admin_user,
                                               devices, writer, monkeypatch, tmp_path):
    first, second, _ = devices
    baseline = generate(app, monkeypatch, tmp_path)
    item = save(logged_in_client, host_id=first.NetDiscoveryID)
    text = generate(app, monkeypatch, tmp_path)
    for kind in ('hostescalation', 'serviceescalation'):
        block, = objects(text, kind)
        assert re.search(r'host_name\s+' + re.escape(first.Nagios_Host_Name) + r'\s*$', block, re.M)
        assert second.Nagios_Host_Name not in block
        assert re.search(r'first_notification\s+2', block)
        assert re.search(r'last_notification\s+5', block)
        assert re.search(r'notification_interval\s+10', block)
        assert re.search(r'contact_groups\s+system_users', block)
    assert logged_in_client.delete(f"{URL}/{item['id']}").status_code == 200
    assert generate(app, monkeypatch, tmp_path) == baseline


def test_global_blocks(logged_in_client, app, db_session, devices, writer, monkeypatch, tmp_path):
    save(logged_in_client)
    text = generate(app, monkeypatch, tmp_path)
    for kind in ('hostescalation', 'serviceescalation'):
        block, = objects(text, kind)
        assert re.search(r'host_name\s+\*\s*$', block, re.M)
    assert re.search(r'service_description\s+\*', objects(text, 'serviceescalation')[0])


def test_database_commit_failure_compensates_config(logged_in_client, db_session, writer):
    """An applied candidate must be rebuilt from rolled-back choices on commit failure."""
    from app.system_models import Escalation
    with patch.object(db.session, 'commit', side_effect=RuntimeError('database unavailable')):
        response = logged_in_client.post(URL, json=payload())
    assert response.status_code == 500
    assert writer.call_count == 2
    assert db.session.scalar(sa.select(sa.func.count()).select_from(Escalation)) == 0


def test_paused_scope_and_host_without_services(logged_in_client, app, db_session, devices,
                                               writer, monkeypatch, tmp_path):
    first = devices[0]
    save(logged_in_client, host_id=first.NetDiscoveryID)
    # A host may have no eligible service plugins; avoid an unmatched wildcard.
    with patch('app.network_discovery.create_host_cfg.build_host_services', return_value=[]):
        text = generate(app, monkeypatch, tmp_path)
    assert len(objects(text, 'hostescalation')) == 1
    assert not objects(text, 'serviceescalation')
    first.Include_Device_In_Scanning = False
    db.session.commit()
    text = generate(app, monkeypatch, tmp_path)
    assert not objects(text, 'hostescalation')
    assert not objects(text, 'serviceescalation')
    item, = logged_in_client.get(URL).get_json()['data']['items']
    assert not item['active'] and 'no longer monitored' in item['reason']


def test_escalation_group_from_paused_source_still_has_members(logged_in_client, app, db_session,
        admin_user, devices, writer, monkeypatch, tmp_path):
    first, second, _ = devices
    assign(second, admin_user)
    group = f'pinpoint_host_{second.NetDiscoveryID}'
    second.Include_Device_In_Scanning = False
    db.session.commit()
    save(logged_in_client, host_id=first.NetDiscoveryID, contact_group=group)
    text = generate(app, monkeypatch, tmp_path)
    assert len([obj for obj in objects(text, 'contactgroup') if group in obj]) == 1
    assert group in objects(text, 'hostescalation')[0]


def test_escalations_coexist_with_enabled_remediation(logged_in_client, app, db_session,
        devices, writer, monkeypatch, tmp_path):
    """The integrated writer retains both the handler and escalation recipients."""
    from app.network_discovery import host_config_templates as templates
    from tests.unit.test_event_handler_config import add_action
    first = devices[0]
    monkeypatch.setattr(templates, 'handler_exists', lambda path: True)
    add_action(db_session, Host_Pattern=first.Nagios_Host_Name, Service_Pattern='*')
    save(logged_in_client, host_id=first.NetDiscoveryID)
    text = generate(app, monkeypatch, tmp_path)
    assert len(objects(text, 'hostescalation')) == 1
    assert len(objects(text, 'serviceescalation')) == 1
    services = [obj for obj in objects(text, 'service') if re.search(
        r'host_name\s+' + re.escape(first.Nagios_Host_Name) + r'\s*$', obj, re.M)]
    assert services
    for service in services:
        assert re.search(r'event_handler\s+pinpoint_event_handler_service', service)
        assert re.search(r'contact_groups\s+system_users', service)
    assert 'define command' in text and 'pinpoint_event_handler_service' in text
