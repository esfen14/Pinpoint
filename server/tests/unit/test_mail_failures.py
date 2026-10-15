"""Bounded, privacy-preserving notification failure diagnostics."""
from unittest.mock import patch

import pytest

from app.nagios.mail_failures import MAX_TAIL_BYTES, read_mail_failure


def failure(timestamp=1700000000, detail='send-mail: account default not found'):
    return (f"[{timestamp}] wproc: NOTIFY job 4 from worker Core Worker 123 is a non-check helper but exited with return code 78\n"
            f"[{timestamp}] wproc:   command: /usr/bin/printf 'private body to victim@example.org' | /usr/bin/mail victim@example.org\n"
            f"[{timestamp}] wproc:   host=web01; service=SSH; contact=admin\n"
            f"[{timestamp}] wproc:   early_timeout=0; exited_ok=1; wait_status=19968; error_code=0;\n"
            f"[{timestamp}] wproc:   stderr line 01: {detail}\n")


def test_safe_latest_notification_failure(tmp_path):
    path = tmp_path / 'nagios.log'
    path.write_text(failure() + failure(1700000060, detail='535 authentication failed password=private-secret'))
    result = read_mail_failure(path)
    assert result['time'] == '2023-11-14T22:14:20+00:00'
    assert result['reason'] == 'Notification email login was rejected.'
    assert 'victim' not in str(result) and 'private-secret' not in str(result)


def test_unconfigured_mail_has_actionable_fixed_reason(tmp_path):
    path = tmp_path / 'nagios.log'; path.write_text(failure())
    assert read_mail_failure(path)['reason'] == 'Notification mail transport is not configured.'


@pytest.mark.parametrize('text', ['', '[1700000000] SERVICE NOTIFICATION: admin;web01;SSH;CRITICAL;notify-service-by-email;failed\n',
    '[1700000000] wproc: SERVICE job 1 from worker Core Worker 123 is a non-check helper but exited with return code 2\n',
    '[1700000000] wproc:   stderr line 01: send-mail: account default not found\n'])
def test_no_notification_failure(text, tmp_path):
    path = tmp_path / 'nagios.log'; path.write_text(text)
    assert read_mail_failure(path) is None


def test_no_missing_or_unreadable_file(tmp_path):
    assert read_mail_failure(tmp_path / 'missing') is None
    with patch('app.nagios.mail_failures.os.open', side_effect=PermissionError):
        assert read_mail_failure(tmp_path / 'no-access') is None


def test_bound_large_file_and_partial_first_line(tmp_path):
    path = tmp_path / 'nagios.log'
    path.write_text(failure() + ('x' * (MAX_TAIL_BYTES * 3)) + '\n')
    assert read_mail_failure(path) is None
    with path.open('a') as handle:
        handle.write(failure(1700000060))
    assert read_mail_failure(path)['time'] == '2023-11-14T22:14:20+00:00'


def test_truncated_block_and_interleaved_checks_do_not_leak(tmp_path):
    path = tmp_path / 'nagios.log'
    text = failure().split('[1700000000] wproc:   stderr')[0]
    text += '[1700000000] wproc: SERVICE job 5 from worker Core Worker 124 is a non-check helper but exited with return code 2\n'
    text += '[1700000000] wproc:   stderr line 01: send-mail: account default not found\n'
    path.write_text(text)
    assert read_mail_failure(path)['reason'] == 'Notification command failed (exit code 78).'


def test_api_reads_fresh_tail_on_each_poll(logged_in_client, db_session, app, tmp_path):
    path = tmp_path / 'nagios.log'; path.write_text('')
    app.config['NAGIOS_LOG_FILE'] = path
    url = '/api/system/smtp-settings'
    assert logged_in_client.get(url).get_json()['data']['lastMailFailure'] is None
    path.write_text(failure())
    data = logged_in_client.get(url).get_json()['data']
    assert data['lastMailFailure']['time'] == '2023-11-14T22:13:20+00:00'
    path.write_text('')
    assert logged_in_client.get(url).get_json()['data']['lastMailFailure'] is None


def test_reopens_rotated_log(tmp_path):
    path = tmp_path / 'nagios.log'; path.write_text(failure())
    assert read_mail_failure(path)
    path.rename(tmp_path / 'nagios.log.1')
    path.write_text('x' * (MAX_TAIL_BYTES * 2) + '\n' + failure(1700000060))
    result = read_mail_failure(path)
    assert result['time'] == '2023-11-14T22:14:20+00:00'


def test_timeout_signal_and_nonregular_file(tmp_path):
    import os
    path = tmp_path / 'nagios.log'
    path.write_text('[1700000000] wproc: NOTIFY job 1 from worker Core Worker 42 timed out after 30.00s\n')
    assert 'timed out' in read_mail_failure(path)['reason']
    path.write_text('[1700000000] wproc: NOTIFY job 1 from worker Core Worker 42 died by signal 9 after 1.00 seconds\n')
    assert read_mail_failure(path)
    fifo = tmp_path / 'pipe'; os.mkfifo(fifo)
    assert read_mail_failure(fifo) is None
    assert read_mail_failure(tmp_path) is None


def test_invalid_log_directory_does_not_leak_descriptors(tmp_path):
    import os
    from pathlib import Path
    if not Path('/proc/self/fd').exists():
        pytest.skip('Descriptor accounting needs Linux procfs')
    before = len(os.listdir('/proc/self/fd'))
    for _ in range(5):
        assert read_mail_failure(tmp_path) is None
    assert len(os.listdir('/proc/self/fd')) == before
