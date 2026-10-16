"""Storage totals are independent of monitoring checks and tolerate unavailable paths."""
from unittest.mock import patch

from app.storage_usage import storage_usage, directory_usage


def test_totals_and_filesystems(tmp_path):
    database = tmp_path / 'system.db'
    database.write_bytes(b'x' * 31)
    backup = tmp_path / 'backups'
    backup.mkdir()
    (backup / 'one').write_bytes(b'x' * 19)
    (backup / 'nested').mkdir()
    (backup / 'nested' / 'two').write_bytes(b'x' * 7)
    (backup / 'link').symlink_to(database)
    result = storage_usage([str(database)], backup, tmp_path / 'missing')
    assert result['databases'][0]['bytes'] == 31
    assert result['databases'][0]['name'] == 'system.db'
    assert result['backups']['bytes'] == 26
    assert result['backups']['complete'] is True
    assert result['archives']['bytes'] is None
    for item in [*result['databases'], result['backups'], result['archives']]:
        assert item['filesystem']['free_bytes'] > 0
        assert item['filesystem']['total_bytes'] >= item['filesystem']['free_bytes']
    assert str(tmp_path) not in str(result)


def test_budget_and_unreadable(tmp_path):
    for n in range(5):
        (tmp_path / str(n)).write_bytes(b'ab')
    result = directory_usage(tmp_path, max_entries=2)
    assert result['complete'] is False
    assert result['bytes'] <= 4
    with patch('app.storage_usage.os.scandir', side_effect=PermissionError):
        assert directory_usage(tmp_path)['bytes'] is None


def test_status_includes_storage_without_changing_monitoring(logged_in_client, db_session):
    with patch('app.api.system.dashboard.get_storage_usage', return_value={'databases': []}):
        result = logged_in_client.get('/api/system/dashboard/status').get_json()['data']
    assert result['storage_usage'] == {'databases': []}
    assert result['nagios']['running'] is False
    assert result['server_resources']['cpu_load']['configured'] is False
