"""Per-device alert selection, generated Nagios objects and atomic recipient saves."""
import re
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db
from app.system_models import ActivityLog, DeviceState, HostAlertRecipient, UserStatus
from app.network_discovery.create_host_cfg import _create_host_cfg_file, _load_monitored_hosts
from tests.support.identity_helpers import NET, MAC_1, MAC_2, make_status, run_scan, scan
from tests.unit.test_management import _make_user

BASE = '/api/system/hosts'
pytestmark = pytest.mark.usefixtures('monitoring_plugins')


@pytest.fixture
def devices(db_session, admin_user):
    status = make_status(db_session, admin_user)
    first = run_scan(db_session, status, scan('10.0.0.5', mac=MAC_1, hostname='web-01', tcp={22: 'ssh'}))[(NET, '10.0.0.5')]
    second = run_scan(db_session, status, scan('10.0.0.6', mac=MAC_2, hostname='web-02', tcp={22: 'ssh'}))[(NET, '10.0.0.6')]
    return first, second, status


def assign(device, *users):
    """Persist recipient choices in the test database."""
    for user in users:
        db.session.add(HostAlertRecipient(NetDiscoveryID=device.NetDiscoveryID, UserID=user.UserID))
    db.session.commit()


def selected(device):
    return sorted(db.session.scalars(sa.select(HostAlertRecipient.UserID).where(
        HostAlertRecipient.NetDiscoveryID == device.NetDiscoveryID)).all())


def objects(text, kind):
    return re.findall(r'define\s+' + kind + r'\s*\{(.*?)\}', text, re.S)


def generate(app, monkeypatch, tmp_path):
    monkeypatch.setitem(app.config, 'HOST_CONFIG_DIR', tmp_path)
    return _create_host_cfg_file(_load_monitored_hosts()).read_text()


def test_groups_filter_eligibility_and_bind_every_service(app, db_session, admin_user, admin_role, devices, monkeypatch, tmp_path):
    first, second, _ = devices
    opted_out = _make_user(db_session, admin_role, 'out@example.com')
    opted_out.Receive_Email_Alerts = False
    inactive = _make_user(db_session, admin_role, 'idle@example.com', status=UserStatus.INACTIVE)
    suspended = _make_user(db_session, admin_role, 'suspended@example.com', status=UserStatus.SUSPENDED)
    other = _make_user(db_session, admin_role, 'other@example.com')
    assign(first, admin_user, opted_out, inactive, suspended)
    text = generate(app, monkeypatch, tmp_path)
    groups = objects(text, 'contactgroup')
    private = [g for g in groups if f'pinpoint_host_{first.NetDiscoveryID}' in g]
    assert len(private) == 1
    assert re.search(r'members\s+' + re.escape(admin_user.Email) + r'\s*$', private[0], re.M)
    for group in groups:
        assert opted_out.Email not in group and inactive.Email not in group and suspended.Email not in group
    assert other.Email in next(g for g in groups if 'system_users' in g)
    for kind in ('host', 'service'):
        for obj in objects(text, kind):
            if re.search(r'host_name\s+' + re.escape(first.Nagios_Host_Name) + r'\s*$', obj, re.M):
                assert f'pinpoint_host_{first.NetDiscoveryID}' in obj
            if re.search(r'host_name\s+' + re.escape(second.Nagios_Host_Name) + r'\s*$', obj, re.M):
                assert 'system_users' in obj
    assert objects(text, 'service')


@pytest.mark.parametrize('ineligible', [False, True])
def test_default_fallback_has_no_empty_group(app, db_session, admin_user, devices, monkeypatch, tmp_path, ineligible):
    first, _, _ = devices
    if ineligible:
        assign(first, admin_user)
        admin_user.Receive_Email_Alerts = False
        # Keep one eligible contact for the global fallback.
        _make_user(db_session, admin_user.Role, 'fallback@example.com')
    text = generate(app, monkeypatch, tmp_path)
    assert f'pinpoint_host_{first.NetDiscoveryID}' not in text
    for obj in objects(text, 'host') + objects(text, 'service'):
        assert 'system_users' in obj
    assert all(re.search(r'members\s+\S+', g) for g in objects(text, 'contactgroup'))


def test_no_eligible_users_never_writes_empty_groups(app, db_session, admin_user, devices, monkeypatch, tmp_path):
    assign(devices[0], admin_user)
    from app.system_models import User
    for user in db.session.scalars(sa.select(User)):
        user.Receive_Email_Alerts = False
    db.session.commit()
    text = generate(app, monkeypatch, tmp_path)
    assert not objects(text, 'contactgroup')
    assert 'contact_groups' not in text


@pytest.mark.parametrize('method', ['get', 'put'])
def test_requires_login(client, db_session, method):
    assert getattr(client, method)(f'{BASE}/1/recipients', json={'recipient_ids': []}).status_code in (401, 302)


@pytest.mark.parametrize('method', ['get', 'put'])
def test_requires_separate_permission(limited_client, db_session, method):
    assert getattr(limited_client, method)(f'{BASE}/1/recipients', json={'recipient_ids': []}).status_code == 403


@pytest.fixture
def writer():
    with patch('app.network_discovery.create_host_cfg.regenerate_and_apply_config_status', return_value=('applied', 'Applied.')) as fake:
        yield fake


def test_save_read_clear_and_audit(logged_in_client, db_session, admin_user, regular_user, devices, writer):
    first = devices[0]
    path = f'{BASE}/{first.NetDiscoveryID}/recipients'
    def inspect_pending():
        assert selected(first) == [regular_user.UserID]
        return 'applied', 'Applied.'
    writer.side_effect = inspect_pending
    response = logged_in_client.put(path, json={'recipient_ids': [regular_user.UserID]})
    assert response.status_code == 200
    assert response.get_json()['data']['recipient_ids'] == [regular_user.UserID]
    writer.assert_called_once_with()
    body = logged_in_client.get(path).get_json()['data']
    assert body['recipient_ids'] == [regular_user.UserID]
    assert any(u['id'] == admin_user.UserID and u['eligible'] for u in body['users'])
    assert any('alert recipients' in action for action in db.session.scalars(sa.select(ActivityLog.Action_Type)))
    writer.side_effect = None
    cleared = logged_in_client.put(path, json={'recipient_ids': []})
    assert cleared.status_code == 200 and selected(first) == []
    assert cleared.get_json()['data']['using_default'] is True


@pytest.mark.parametrize('result', [('failed', 'Config failed to validate: bad config'), ('failed', 'Nagios reload failed')])
def test_failure_restores_selection_and_reports_error(logged_in_client, db_session, admin_user, regular_user, devices, writer, result):
    first = devices[0]
    assign(first, admin_user)
    count = db.session.scalar(sa.select(sa.func.count()).select_from(ActivityLog))
    writer.return_value = result
    response = logged_in_client.put(f'{BASE}/{first.NetDiscoveryID}/recipients', json={'recipient_ids': [regular_user.UserID]})
    assert response.status_code == 422
    assert result[1] in response.get_json()['message']
    assert selected(first) == [admin_user.UserID]
    assert db.session.scalar(sa.select(sa.func.count()).select_from(ActivityLog)) == count


def test_writer_exception_rolls_back(logged_in_client, db_session, admin_user, regular_user, devices, writer):
    first = devices[0]
    assign(first, admin_user)
    writer.side_effect = RuntimeError('writer unavailable')
    assert logged_in_client.put(f'{BASE}/{first.NetDiscoveryID}/recipients', json={'recipient_ids': [regular_user.UserID]}).status_code == 500
    assert selected(first) == [admin_user.UserID]


@pytest.mark.parametrize('body', [None, [], {}, {'recipient_ids': '1'}, {'recipient_ids': [True]}, {'recipient_ids': ['1']}, {'recipient_ids': [-1]}, {'recipient_ids': [1, 1]}, {'recipient_ids': [99999]}, {'recipient_ids': [1], 'unexpected': True}])
def test_invalid_payload_has_no_side_effect(logged_in_client, db_session, devices, writer, body):
    response = logged_in_client.put(f'{BASE}/{devices[0].NetDiscoveryID}/recipients', json=body)
    assert response.status_code in (400, 415)
    writer.assert_not_called()
    assert selected(devices[0]) == []


@pytest.mark.parametrize('method', ['get', 'put'])
def test_unknown_device(logged_in_client, db_session, writer, method):
    response = getattr(logged_in_client, method)(f'{BASE}/99999/recipients', json={'recipient_ids': []})
    assert response.status_code == 404
    writer.assert_not_called()


@pytest.mark.parametrize('state', [DeviceState.RETIRED, DeviceState.MERGED])
def test_terminal_device_cannot_edit(logged_in_client, db_session, devices, writer, state):
    devices[0].Device_State = state
    db.session.commit()
    assert logged_in_client.put(f'{BASE}/{devices[0].NetDiscoveryID}/recipients', json={'recipient_ids': []}).status_code == 409
    writer.assert_not_called()


def test_rescan_address_change_preserves_recipients(db_session, admin_user, devices):
    first, _, status = devices
    assign(first, admin_user)
    moved = run_scan(db_session, status, scan('10.0.0.8', mac=MAC_1, hostname='renamed', tcp={22: 'ssh'}))[(NET, '10.0.0.8')]
    assert moved.NetDiscoveryID == first.NetDiscoveryID
    assert selected(moved) == [admin_user.UserID]


def test_merge_unions_and_deduplicates_then_retire_cleans_up(logged_in_client, db_session, admin_user, regular_user, devices):
    first, second, _ = devices
    assign(first, admin_user, regular_user)
    assign(second, admin_user)
    with patch('app.api.system.device_identity.reconcile_plugin_monitoring', return_value={'success': True, 'changed': True, 'message': 'applied'}):
        assert logged_in_client.post(f'{BASE}/{first.NetDiscoveryID}/merge', json={'target_id': second.NetDiscoveryID}).status_code == 200
        assert selected(first) == []
        assert selected(second) == sorted([admin_user.UserID, regular_user.UserID])
        assert logged_in_client.post(f'{BASE}/{second.NetDiscoveryID}/retire').status_code == 200
    assert selected(second) == []


def test_permission_seeded():
    from app.api.commands.seed import PERMISSIONS
    assert 'system.hosts.alerts' in PERMISSIONS


def test_custom_services_use_device_group(app, db_session, admin_user, devices, monkeypatch, tmp_path):
    first = devices[0]
    assign(first, admin_user)
    with patch('app.network_discovery.create_host_cfg.load_custom_checks', return_value={first.NetDiscoveryID: [('custom-ping-health', 'pinpoint_custom_check_ping!100,20%!500,60%', 'check_ping')]}):
        text = generate(app, monkeypatch, tmp_path)
    custom = next(obj for obj in objects(text, 'service') if 'custom-ping-health' in obj)
    assert f'pinpoint_host_{first.NetDiscoveryID}' in custom


def test_other_permissions_do_not_allow_recipient_edits(limited_client, db_session, regular_user, seeded_permissions):
    from app.system_models import RolePermission
    for name in ('account.alerts', 'system.hosts', 'system.hosts.edit'):
        db.session.add(RolePermission(RoleID=regular_user.RoleID, PermissionID=seeded_permissions[name].PermissionID))
    db.session.commit()
    for method in ('get', 'put'):
        assert getattr(limited_client, method)(f'{BASE}/1/recipients', json={'recipient_ids': []}).status_code == 403


def test_ineligible_selections_are_preserved_but_report_default(logged_in_client, db_session, admin_user, devices, writer):
    admin_user.Receive_Email_Alerts = False
    db.session.commit()
    path = f'{BASE}/{devices[0].NetDiscoveryID}/recipients'
    response = logged_in_client.put(path, json={'recipient_ids': [admin_user.UserID]})
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['recipient_ids'] == [admin_user.UserID]
    assert data['using_default'] is True
    assert not next(user for user in data['users'] if user['id'] == admin_user.UserID)['eligible']


@pytest.mark.parametrize('failure', ['validation', 'reload'])
def test_real_shared_writer_failure_preserves_database_and_file(logged_in_client, app, db_session, admin_user, regular_user, devices, monkeypatch, tmp_path, failure):
    import app.network_discovery.create_host_cfg as cfg
    first = devices[0]
    assign(first, admin_user)
    text = generate(app, monkeypatch, tmp_path)
    running = tmp_path / 'running.cfg'
    running.write_text(text)
    monkeypatch.setitem(app.config, 'NAGIOS_HOST_CFG', running)
    monkeypatch.setitem(app.config, 'BACKUP_DIR', tmp_path / 'backup')
    with patch.object(cfg, '_validate_config', return_value=(failure != 'validation', 'validation rejected')) as validation, patch.object(cfg.subprocess, 'run', side_effect=RuntimeError('reload rejected')):
        response = logged_in_client.put(f'{BASE}/{first.NetDiscoveryID}/recipients', json={'recipient_ids': [regular_user.UserID]})
    assert response.status_code == 422
    assert selected(first) == [admin_user.UserID]
    assert running.read_text() == text
    validation.assert_called_once()


def test_upgrade_permission_sync_grants_administrator(db_session, admin_role, seeded_permissions):
    from app.system_models import Permission, RolePermission
    from app.api.commands.seed import sync_permissions
    permission = seeded_permissions['system.hosts.alerts']
    db.session.execute(sa.delete(RolePermission).where(RolePermission.PermissionID == permission.PermissionID))
    db.session.execute(sa.delete(Permission).where(Permission.PermissionID == permission.PermissionID))
    db.session.commit()
    admin_role.Name = 'Administrator'
    db.session.commit()
    sync_permissions()
    granted = db.session.scalar(sa.select(Permission).where(Permission.Name == 'system.hosts.alerts'))
    assert granted is not None
    assert db.session.scalar(sa.select(RolePermission).where(RolePermission.PermissionID == granted.PermissionID, RolePermission.RoleID == admin_role.RoleID)) is not None


def test_migration_round_trip():
    import json
    import subprocess
    import sys
    from pathlib import Path
    result = subprocess.run([sys.executable, 'tests/support/host_recipients_migration_runner.py'], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, (result.stdout + result.stderr)[-3000:]
    report = json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert report['version'] == [['a79e14c0b621']]
    assert report['empty'] == report['reupgrade_empty'] == 0
    assert report['legacy'] == report['devices'] == [['legacy']]
    assert report['users'] == [['existing@example.com']]
    assert report['rejected'] == [[1, 1], [999, 1], [1, 999]]
    assert report['rows'] == [[1, 1]]
    assert report['history_unchanged'] and report['removed']


@pytest.mark.parametrize('ineligible', [False, True])
def test_fallback_validates_through_shared_writer(app, db_session, admin_user, admin_role, devices, monkeypatch, tmp_path, ineligible):
    """Fake Nagios at its process boundary, checking contact references in its candidate."""
    from pathlib import Path
    import app.network_discovery.create_host_cfg as cfg
    first = devices[0]
    if ineligible:
        assign(first, admin_user)
        admin_user.Receive_Email_Alerts = False
        _make_user(db_session, admin_role, 'fallback@example.com')
    monkeypatch.setitem(app.config, 'HOST_CONFIG_DIR', tmp_path)
    live = tmp_path / 'running.cfg'
    live.write_text('# previous config\n')
    main = tmp_path / 'nagios.cfg'
    main.write_text(f'cfg_file={live}\n')
    monkeypatch.setitem(app.config, 'NAGIOS_HOST_CFG', live)
    monkeypatch.setitem(app.config, 'NAGIOS_MAIN_CFG', main)
    def verify(main_path):
        candidate_path = Path(main_path.read_text().strip().split('=', 1)[1])
        text = candidate_path.read_text()
        contact_names = {re.search(r'contact_name\s+(\S+)', obj)[1] for obj in objects(text, 'contact')}
        groups = {}
        for obj in objects(text, 'contactgroup'):
            name = re.search(r'contactgroup_name\s+(\S+)', obj)[1]
            members = re.search(r'members\s+(\S+)', obj)[1].split(',')
            assert members and set(members) <= contact_names
            groups[name] = members
        assert set(groups) == {'system_users'}
        for obj in objects(text, 'host') + objects(text, 'service'):
            assert re.search(r'contact_groups\s+(\S+)', obj)[1] in groups
        return True, 'No errors found (fake Nagios).'
    with patch.object(cfg, '_run_nagios_verify', side_effect=verify) as validator, patch.object(cfg, '_apply_new_host_cfg', return_value=(True, 'Applied.')):
        assert cfg.regenerate_and_apply_config_status() == ('applied', 'Applied.')
    validator.assert_called_once()
