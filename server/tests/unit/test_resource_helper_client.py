"""The privileged block helper carries secrets on stdin and restores transactions."""
import hashlib
import json
import stat
import subprocess
from types import SimpleNamespace

import pytest

from app.network_discovery import resource_macros as resources


@pytest.fixture
def helper_resource(tmp_path, monkeypatch):
    path = tmp_path / 'resource.cfg'
    path.write_text('$USER1$=/plugins\n# external bytes\n')
    path.chmod(0o660)
    monkeypatch.setattr(resources, '_HELPER_RESOURCE_PATH', str(path), raising=False)
    # Model a service user different from the file's owner without chown/root.
    monkeypatch.setattr(resources.os, 'geteuid', lambda: path.stat().st_uid + 1)
    calls = []

    def helper(command, **kwargs):
        assert command == ['/usr/bin/sudo', '-n', '/usr/local/sbin/pinpoint-apply-resources']
        assert 'synthetic-helper-token' not in ' '.join(command)
        assert kwargs['timeout'] == 10 and kwargs['capture_output'] is True
        request = json.loads(kwargs['input'])
        assert set(request) == {'resource_path', 'outside_digest', 'block'}
        assert request['resource_path'] == str(path)
        before, _, after = resources._extract_block(resources.read_text(path))
        expected = hashlib.sha256(json.dumps([before, after], separators=(',', ':')).encode()).hexdigest()
        assert request['outside_digest'] == expected
        path.write_text(before + (request['block'] or '') + after)
        calls.append(request)
        return SimpleNamespace(returncode=0, stdout=b'', stderr=b'')

    monkeypatch.setattr(subprocess, 'run', helper)
    return path, calls


def test_foreign_owned_resource_uses_stdin_helper_without_direct_temp(helper_resource, monkeypatch):
    path, calls = helper_resource
    def forbidden_temp(*args, **kwargs):
        raise AssertionError('Foreign owned resource must use the restricted helper.')
    monkeypatch.setattr(resources.tempfile, 'mkstemp', forbidden_temp)
    resources.write_resource_block(path, {'ncpa_token:1': '$USER2$'}, {'ncpa_token:1': 'synthetic-helper-token'})
    assert len(calls) == 1 and '$USER2$=synthetic-helper-token' in calls[0]['block']
    assert path.read_text().startswith('$USER1$=/plugins\n# external bytes\n')
    assert stat.S_IMODE(path.stat().st_mode) == 0o660


@pytest.mark.parametrize('existing', [
    '$USER1$=/plugins\n# external bytes\n',
    '$USER1$=/plugins\n# BEGIN PINPOINT\n$USER2$=old-value\n# END PINPOINT\n# footer\n',
])
def test_helper_transaction_restores_original_block_or_its_absence(helper_resource, existing):
    path, calls = helper_resource
    path.write_text(existing)
    with resources.ResourceTransaction(path):
        resources.write_resource_block(path, {'ncpa_token:1': '$USER2$'}, {'ncpa_token:1': 'synthetic-helper-token'})
    assert path.read_text() == existing
    assert len(calls) == 2
    assert calls[-1]['block'] is None if '# BEGIN PINPOINT' not in existing else '$USER2$=old-value' in calls[-1]['block']


@pytest.mark.parametrize('failure', ['reject', 'timeout', 'missing', 'wrong-bytes', 'wrong-mode'])
def test_helper_failure_does_not_echo_output_or_claim_success(helper_resource, monkeypatch, failure):
    path, _ = helper_resource
    original = path.read_bytes()
    def failed(command, **kwargs):
        if failure == 'timeout': raise subprocess.TimeoutExpired(command, 10, stderr=b'synthetic-helper-token')
        if failure == 'missing': raise FileNotFoundError('synthetic-helper-token')
        if failure == 'wrong-mode': path.chmod(0o664)
        return SimpleNamespace(returncode=1 if failure == 'reject' else 0,
                               stdout=b'synthetic-helper-token', stderr=b'synthetic-helper-token')
    monkeypatch.setattr(subprocess, 'run', failed)
    with pytest.raises(OSError) as error:
        resources.write_resource_block(path, {'ncpa_token:1': '$USER2$'}, {'ncpa_token:1': 'synthetic-helper-token'})
    assert 'synthetic-helper-token' not in str(error.value)
    if failure == 'reject':
        assert 'exact no-argument sudo rule' in str(error.value)
        assert 'nagios:nagios 0660' in str(error.value)
    assert path.read_bytes() == original


def test_helper_cannot_receive_external_replacement_contents(helper_resource):
    path, calls = helper_resource
    with pytest.raises(ValueError, match='outside'):
        resources.atomic_write(path, b'$USER1$=/changed\n', path.stat())
    assert calls == []


def test_custom_resource_path_does_not_invoke_fixed_destination_helper(helper_resource, monkeypatch, tmp_path):
    _, calls = helper_resource
    custom = tmp_path / 'custom.cfg'
    custom.write_text('$USER1$=/custom\n'); custom.chmod(0o660)
    with pytest.raises(PermissionError):
        resources.write_resource_block(custom, {'ncpa_token:1': '$USER2$'}, {'ncpa_token:1': 'synthetic-helper-token'})
    assert calls == []
