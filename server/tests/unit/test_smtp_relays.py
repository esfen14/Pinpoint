"""Custom STARTTLS relay validation, API/helper round trip and secret handling."""
import json
import smtplib
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.smtp_settings import SmtpSettingsError, validate_smtp_settings
from app.system_models import SmtpSettings

URL = '/api/system/smtp-settings'
SECRET = 'relay test password'
CUSTOM = dict(provider='custom', host='mail.example.org', port=2525, tls='starttls',
              username='monitoring', sender='alerts@example.org', password=SECRET)


@pytest.mark.parametrize('host', ['mail.example.org', '192.0.2.1', 'localhost', 'a' * 253])
def test_custom_hosts_and_non_email_username(host):
    values = validate_smtp_settings({**CUSTOM, 'host': host}, False)
    assert values == {**CUSTOM, 'host': host}


@pytest.mark.parametrize(('field', 'value'), [
    ('host', ''), ('host', 'a' * 254), ('host', 'bad host'), ('host', '-bad'),
    ('host', 'mail\nexample.org'), ('host', '::1'), ('host', None),
    ('host', 'mail;id'), ('host', 'café.org'),
    ('port', 0), ('port', 65536), ('port', True), ('port', 587.0), ('port', '587'),
    ('tls', 'tls'), ('tls', 'none'), ('tls', 'ssl'), ('tls', None),
    ('username', ''), ('username', 'é'), ('username', 'x' * 255), ('username', 'bad\nuser'),
    ('sender', 'bad'), ('sender', 'a!b@example.org'), ('sender', 'a@example.123'),
])
def test_custom_rejects_helper_incompatible_fields(field, value):
    with pytest.raises(SmtpSettingsError, match=field):
        validate_smtp_settings({**CUSTOM, field: value}, False)


@pytest.mark.parametrize('provider', [[], {}, None, 7])
def test_bad_provider_types_are_validation_errors(provider):
    with pytest.raises(SmtpSettingsError):
        validate_smtp_settings({**CUSTOM, 'provider': provider}, False)


def test_custom_username_needs_explicit_sender_when_not_an_email():
    with pytest.raises(SmtpSettingsError, match='sender'):
        validate_smtp_settings({**CUSTOM, 'sender': ''}, False)


def test_custom_save_reload_keep_password_and_send(logged_in_client, db_session, app):
    app.config.update(SECRET_KEY='test-secret', SECRET_KEY_IS_TEMPORARY=False)
    helper_result = subprocess.CompletedProcess([], 0, '', '')
    with patch('app.smtp_settings.subprocess.run', return_value=helper_result) as helper:
        response = logged_in_client.put(URL, json={**CUSTOM, 'version': 0})
        assert response.status_code == 200
        assert json.loads(helper.call_args.kwargs['input']) == {k: v for k, v in CUSTOM.items() if k != 'provider'}
        response = logged_in_client.put(URL, json={**CUSTOM, 'version': 1, 'password': ''})
        assert response.status_code == 200
        assert json.loads(helper.call_args.kwargs['input'])['password'] == SECRET
    settings = logged_in_client.get(URL).get_json()['data']['settings']
    assert settings['provider'] == 'custom' and settings['host'] == CUSTOM['host']
    assert settings['passwordSet'] and SECRET not in json.dumps(settings)
    assert SECRET not in db_session.session.get(SmtpSettings, 1).Password_Encrypted
    with patch('app.smtp_settings.smtplib.SMTP') as smtp:
        result = logged_in_client.post(URL + '/test').get_json()['data']
    assert result['ok']
    smtp.assert_called_once_with(CUSTOM['host'], CUSTOM['port'], timeout=15)
    connection = smtp.return_value.__enter__.return_value
    connection.starttls.assert_called_once()
    connection.login.assert_called_once_with('monitoring', SECRET)


@pytest.mark.parametrize(('field', 'value'), [('host', 'bad;id'), ('port', True), ('tls', 'tls')])
def test_invalid_custom_never_reaches_helper(logged_in_client, db_session, field, value):
    with patch('app.smtp_settings.subprocess.run') as helper:
        response = logged_in_client.put(URL, json={**CUSTOM, field: value, 'version': 0})
    assert response.status_code == 400
    assert field in response.get_json()['message'].lower()
    helper.assert_not_called()


def test_password_echo_is_redacted_from_helper_and_smtp_errors(logged_in_client, db_session, app, caplog):
    app.config.update(SECRET_KEY='test-secret', SECRET_KEY_IS_TEMPORARY=False)
    with patch('app.smtp_settings.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'rejected ' + SECRET)):
        response = logged_in_client.put(URL, json={**CUSTOM, 'version': 0})
    assert response.status_code == 400 and SECRET not in response.get_data(as_text=True)
    with patch('app.smtp_settings.subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')):
        assert logged_in_client.put(URL, json={**CUSTOM, 'version': 0}).status_code == 200
    with patch('app.smtp_settings.smtplib.SMTP') as smtp:
        smtp.return_value.__enter__.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, SECRET.encode())
        response = logged_in_client.post(URL + '/test')
    data = response.get_json()['data']
    assert data['code'] == 'auth_failed' and 'Gmail' not in data['message']
    assert SECRET not in response.get_data(as_text=True) and SECRET not in caplog.text
