"""NCPA command logging and bootstrap probes, with SSH entirely mocked."""
import logging
from unittest.mock import MagicMock, patch

import pytest

import app.ncpa_deployment.ncpa_deployment as worker


def test_cleanup_steps_continue_after_failure_without_secret_in_logs(app, caplog, monkeypatch, tmp_path):
    key = tmp_path / "deploy.pub"
    key.write_text("ssh-ed25519 YWJj")
    monkeypatch.setattr(worker, "PUBLIC_KEY_PATH", str(key))
    client = MagicMock()
    with app.app_context(), patch.object(worker, "connect_with_fingerprint_check", return_value=client), \
         patch.object(worker, "run_sudo_command", side_effect=[
             {"success": True}, {"success": False, "error": "private-secret"},
             {"success": True}, {"success": True},
         ]) as run:
        steps = worker.cleanup_ncpa_bootstrap("10.0.0.5", 22, "fp", "admin", "private-secret", True)
    assert steps == [
        {"step": "key", "ok": True}, {"step": "sudo_rule", "ok": False},
        {"step": "helper", "ok": True}, {"step": "account", "ok": False, "skipped": True},
    ]
    assert run.call_count == 3
    assert all(call.kwargs["log_command"].startswith("NCPA cleanup ") for call in run.call_args_list)
    assert "private-secret" not in str(steps) + caplog.text
    client.close.assert_called_once()


def test_cleanup_uses_fixed_paths_and_quotes_key(app, monkeypatch, tmp_path):
    key = tmp_path / "deploy.pub"
    key.write_text("ssh-ed25519 YWJj operator's-key")
    monkeypatch.setattr(worker, "PUBLIC_KEY_PATH", str(key))
    client = MagicMock()
    with app.app_context(), patch.object(worker, "connect_with_fingerprint_check", return_value=client), \
         patch.object(worker, "run_sudo_command", return_value={"success": True}) as run:
        steps = worker.cleanup_ncpa_bootstrap("10.0.0.5", 22, "fp", "admin", "private-secret", True)
    assert all(step["ok"] for step in steps)
    assert [step["step"] for step in steps] == ["key", "sudo_rule", "helper", "account"]
    assert run.call_count == 4
    assert "operator's-key" not in str([call.kwargs for call in run.call_args_list])
    assert "'\"'\"'" in run.call_args_list[0].args[1]
    for call in run.call_args_list:
        assert call.kwargs["suppress_output"] is True
        assert call.args[2] == "private-secret"


def test_cleanup_connection_failure_runs_no_commands(app, monkeypatch, tmp_path):
    key = tmp_path / "deploy.pub"
    key.write_text("ssh-ed25519 YWJj")
    monkeypatch.setattr(worker, "PUBLIC_KEY_PATH", str(key))
    with app.app_context(), patch.object(worker, "connect_with_fingerprint_check", return_value=None), \
         patch.object(worker, "run_sudo_command") as run:
        with pytest.raises(ValueError, match="trusted host key"):
            worker.cleanup_ncpa_bootstrap("10.0.0.5", 22, "fp", "admin", "private-secret")
    run.assert_not_called()


def test_cleanup_suppresses_remote_output_even_on_failure(app, caplog):
    client = MagicMock()
    client.exec_command.return_value = ssh_result(1, b"private-secret")
    with app.app_context():
        result = worker.run_sudo_command(
            client, "/bin/false", "private-secret", log_command="NCPA cleanup key", suppress_output=True
        )
    assert not result["success"]
    assert result["error"] == "" and result["output"] == ""
    assert "private-secret" not in caplog.text


def ssh_result(code, stderr=b""):
    """Build the three SSH streams for a single command without a connection."""
    stdin, stdout, errors = MagicMock(), MagicMock(), MagicMock()
    stdout.read.return_value = b""
    errors.read.return_value = stderr
    stdout.channel.recv_exit_status.return_value = code
    return stdin, stdout, errors


@pytest.mark.parametrize("sudo", [False, True])
@pytest.mark.parametrize("code,expected,level", [
    (1, (1,), logging.INFO), (2, (1, 2), logging.INFO),
    (1, (), logging.ERROR), (3, (1, 2), logging.ERROR),
])
def test_nonzero_exit_preserves_failure(app, caplog, sudo, code, expected, level):
    client = MagicMock()
    client.exec_command.return_value = ssh_result(code)
    helper = worker.run_sudo_command if sudo else worker.run_command
    args = (client, "test-command", "") if sudo else (client, "test-command")
    with app.app_context(), caplog.at_level(logging.INFO):
        result = helper(*args, expected_exit_codes=expected)
    assert result["success"] is False
    assert [record.levelno for record in caplog.records] == [level]


@pytest.mark.parametrize("sudo", [False, True])
def test_success_with_stderr_still_warns(app, caplog, sudo):
    client = MagicMock()
    client.exec_command.return_value = ssh_result(0, b"notice")
    helper = worker.run_sudo_command if sudo else worker.run_command
    args = (client, "test-command", "") if sudo else (client, "test-command")
    with app.app_context(), caplog.at_level(logging.INFO):
        assert helper(*args)["success"] is True
    assert [record.levelno for record in caplog.records] == [logging.WARNING]


@pytest.mark.parametrize("code,count", [(0, 1), (1, 2)])
def test_account_probe_creates_only_missing_account(app, caplog, code, count):
    client = MagicMock()
    client.exec_command.side_effect = [ssh_result(code), ssh_result(0)]
    with app.app_context(), caplog.at_level(logging.INFO):
        assert worker.ensure_deployment_user(client, "") is True
    commands = [call.args[0] for call in client.exec_command.call_args_list]
    assert len(commands) == count
    if code:
        assert "useradd" in commands[1]
        assert any(record.levelno == logging.INFO for record in caplog.records)
    assert not any(record.levelno >= logging.ERROR for record in caplog.records)


@pytest.mark.parametrize("code,count", [(0, 5), (1, 6), (2, 6)])
def test_key_probe_adds_only_missing_key(app, caplog, monkeypatch, tmp_path, code, count):
    public_key = tmp_path / "deployment.pub"
    public_key.write_text("ssh-ed25519 public-test-key")
    monkeypatch.setattr(worker, "PUBLIC_KEY_PATH", str(public_key))
    client = MagicMock()
    client.exec_command.side_effect = [ssh_result(0), ssh_result(code)] + [ssh_result(0) for _ in range(4)]
    with app.app_context(), caplog.at_level(logging.INFO):
        assert worker.install_deployment_key(client, "") is True
    commands = [call.args[0] for call in client.exec_command.call_args_list]
    assert len(commands) == count
    assert any("printf" in command for command in commands) is bool(code)
    assert not any(record.levelno >= logging.ERROR for record in caplog.records)
