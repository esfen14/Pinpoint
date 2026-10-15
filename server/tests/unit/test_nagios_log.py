"""Bounded fixed-file Nagios log access; untrusted output must never leave the server."""
from unittest.mock import patch

import pytest

from app.nagios_log import read_nagios_log, MAX_BYTES

URL = '/api/system/log/nagios'


def test_tail_order_after_and_unterminated(tmp_path):
    path = tmp_path / 'nagios.log'
    path.write_text(''.join(f'[{n}] HOST ALERT: web01;DOWN;HARD;1;private-output\n' for n in range(1, 10)).rstrip())
    result = read_nagios_log(path, lines=3, after=7)
    assert len(result['lines']) == 2
    assert result['lines'][0].startswith('[8]')
    assert result['lines'][1].startswith('[9]')
    assert 'private-output' not in str(result)
    assert result['available'] is True
    assert result['truncated'] is True


def test_large_file_bounds_and_secrets(tmp_path):
    path = tmp_path / 'nagios.log'
    path.write_text('[1] ' + 'sensitive' * MAX_BYTES + '\n[2] SERVICE ALERT: web01;HTTPS;CRITICAL;HARD;1;password=secret\n'
                    '[3] Warning: check_command=check_ncpa!-t token\n'
                    '[4] EXTERNAL COMMAND: PROCESS_SERVICE_CHECK_RESULT;web01;svc;2;secret\n'
                    '[5] arbitrary token=secret\n')
    result = read_nagios_log(path, lines=500)
    assert len(result['lines']) <= 500
    assert sum(len(line.encode()) for line in result['lines']) <= MAX_BYTES
    assert 'secret' not in str(result) and 'token' not in str(result)
    assert 'web01;HTTPS;CRITICAL;HARD;1' in result['lines'][0]
    assert result['truncated'] is True


def test_file_unavailable_empty_fifo_and_symlink(tmp_path):
    path = tmp_path / 'missing'
    assert read_nagios_log(path)['lines'] == []
    assert read_nagios_log(path)['available'] is False
    path.write_text('')
    assert read_nagios_log(path)['available'] is True
    with patch('app.nagios_log.os.open', side_effect=PermissionError):
        assert read_nagios_log(path)['available'] is False
    link = tmp_path / 'link'
    link.symlink_to(path)
    assert read_nagios_log(link)['available'] is False
    import os
    fifo = tmp_path / 'fifo'
    os.mkfifo(fifo)
    assert read_nagios_log(fifo)['available'] is False


@pytest.mark.parametrize('query', ['lines=0', 'lines=501', 'lines=x', 'lines=1.2', 'after=-1', 'after=abc',
                                  'after=9223372036854775808', 'lines=1&lines=2', 'path=/etc/passwd', 'after='])
def test_invalid_parameters(logged_in_client, db_session, query):
    assert logged_in_client.get(URL + '?' + query).status_code == 400


def test_api_uses_only_configured_path(logged_in_client, db_session, app, tmp_path, monkeypatch):
    path = tmp_path / 'nagios.log'
    path.write_text('[1] HOST ALERT: web01;DOWN;HARD;1;secret\n')
    monkeypatch.setitem(app.config, 'NAGIOS_LOG_PATH', path)
    response = logged_in_client.get(URL + '?lines=1&after=0')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    assert 'secret' not in response.get_data(as_text=True)
    assert len(response.get_json()['data']['lines']) == 1


def test_authorization(client, limited_client, db_session):
    assert client.get(URL).status_code in (401, 302)
    assert limited_client.get(URL).status_code == 403
