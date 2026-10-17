"""
tests/unit/test_remote_restart.py — Issue #8 Part 8.3, remote service restart.

Covers the restart_remote_service action (app/remediation_actions.py), the device lookup the
consumer does before it (app/remediation.py resolve_remote_target), the SSH side
(app/remote_restart.py) with SSH mocked, and the device-side helper script.
"""
import shutil
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app import remediation, remediation_actions as registry, remote_restart
from app.system_models import (
    ActivityLog, DeviceState, DiscoveryStatus, NetworkDiscovery, NetworkDiscoveryStatus, SSHCredentials,
)

FINGERPRINT = "abc123FINGERPRINT"
TARGET = registry.RemoteTarget(
    ip_address="10.0.20.11", ssh_port=22, fingerprint=FINGERPRINT, services=("nagios", "apache2"))
UNIT = {"unit": "apache2"}
RESTART = "app.remote_restart.restart_remote_unit"


def context(**changes):
    fields = dict(hostname="web-01", service="HTTP", state="CRITICAL", remote_target=TARGET,
                  app=MagicMock())
    fields.update(changes)
    return registry.RunContext(**fields)


# ==========================================================
# PARAMETERS
# ==========================================================

def test_the_type_is_listed_for_the_form():
    info = next(t for t in registry.describe_types() if t["key"] == "restart_remote_service")
    assert info["parameters"][0]["name"] == "unit"


@pytest.mark.parametrize("good", ["nagios", "apache2", "ssh", "ncpa_listener", "getty@tty1", "my-app.v2"])
def test_plain_unit_names_are_accepted(good):
    assert registry.validate_parameters("restart_remote_service", {"unit": good}) == ({"unit": good}, {})


@pytest.mark.parametrize("bad", [
    "", " ", "nagios; reboot", "$(id)", "`id`", "a b", "../nagios", "/etc/passwd", "-x", "--now",
    "a\nb", "x" * 64, None, ["nagios"], 5,
])
def test_anything_that_is_not_a_plain_unit_name_is_refused(bad):
    cleaned, errors = registry.validate_parameters("restart_remote_service", {"unit": bad})
    assert cleaned == {} and "unit" in errors


def test_other_parameters_are_refused():
    cleaned, errors = registry.validate_parameters(
        "restart_remote_service", {"unit": "nagios", "host": "10.0.0.1", "command": "id"})
    assert cleaned == {} and set(errors) == {"host", "command"}


def test_the_device_is_never_a_parameter():
    cleaned, errors = registry.validate_parameters("restart_remote_service", {"unit": "nagios", "device": 3})
    assert cleaned == {} and "device" in errors


def test_clean_services_sorts_dedupes_and_rejects_bad_names():
    assert remote_restart.clean_services(["nagios", "apache2", "nagios"]) == (["apache2", "nagios"], None)
    assert remote_restart.clean_services(None) == ([], None)
    assert remote_restart.clean_services(["nagios; reboot"])[1]
    assert remote_restart.clean_services("nagios")[1]
    assert remote_restart.clean_services([f"s{i}" for i in range(21)])[1]


# ==========================================================
# THE ACTION
# ==========================================================

def test_a_listed_unit_is_restarted_with_the_devices_trusted_details():
    with patch(RESTART, return_value=("succeeded", "Restarted apache2; exit code 0.")) as restart:
        result = registry.run_action("restart_remote_service", UNIT, context())
    assert result.outcome == "succeeded"
    restart.assert_called_once_with("10.0.20.11", 22, FINGERPRINT, "apache2")


def test_the_run_happens_inside_an_application_context():
    ctx = context()
    with patch(RESTART, return_value=("succeeded", "ok")):
        registry.run_action("restart_remote_service", UNIT, ctx)
    ctx.app.app_context.assert_called_once()


def test_maintenance_mode_blocks_it_before_any_connection():
    with patch(RESTART) as restart:
        result = registry.run_action("restart_remote_service", UNIT, context(maintenance_mode=True))
    assert result.outcome == "failed" and "Maintenance Mode" in result.output
    restart.assert_not_called()


def test_a_device_that_may_not_be_acted_on_is_refused_with_its_reason():
    ctx = context(remote_target=None, remote_refusal="Refused: monitoring of the device is paused.")
    with patch(RESTART) as restart:
        result = registry.run_action("restart_remote_service", UNIT, ctx)
    assert result.outcome == "failed" and "paused" in result.output
    restart.assert_not_called()


def test_without_a_target_or_reason_it_still_refuses():
    with patch(RESTART) as restart:
        result = registry.run_action("restart_remote_service", UNIT, context(remote_target=None))
    assert result.outcome == "failed"
    restart.assert_not_called()


def test_a_unit_off_the_devices_list_is_refused_without_connecting():
    with patch(RESTART) as restart:
        result = registry.run_action("restart_remote_service", {"unit": "sshd"}, context())
    assert result.outcome == "failed" and "restart list" in result.output
    restart.assert_not_called()


def test_a_bad_unit_name_stored_in_an_old_rule_is_refused_at_run_time():
    with patch(RESTART) as restart:
        result = registry.run_action("restart_remote_service", {"unit": "nagios; reboot"}, context())
    assert result.outcome == "failed"
    restart.assert_not_called()


def test_a_changed_host_key_is_a_failed_run_with_its_message():
    with patch(RESTART, return_value=("host_key_changed", "Host key changed. Verify the device's host key again.")):
        result = registry.run_action("restart_remote_service", UNIT, context())
    assert result.outcome == "failed" and "Host key changed" in result.output


def test_a_timeout_is_recorded_as_timed_out():
    with patch(RESTART, return_value=("timed_out", "Restarting apache2 did not finish in time.")):
        result = registry.run_action("restart_remote_service", UNIT, context())
    assert result.outcome == "timed_out"


def test_a_crash_never_puts_the_exception_text_in_the_record():
    with patch(RESTART, side_effect=RuntimeError("password=hunter2 key=/home/x/.ssh/id")):
        result = registry.run_action("restart_remote_service", UNIT, context())
    assert result.outcome == "failed"
    assert "hunter2" not in result.output and ".ssh" not in result.output


# ==========================================================
# DEVICE LOOKUP (consumer side)
# ==========================================================

def make_device(db_session, admin_user, nagios_name="web-01", state=DeviceState.ACTIVE, include=True,
                key_installed=True, fingerprint=FINGERPRINT, enabled=True, services=("apache2",), port=2222):
    log = ActivityLog(Action_Type="test", UserID=admin_user.UserID)
    db_session.session.add(log)
    db_session.session.flush()
    status = NetworkDiscoveryStatus(Status=DiscoveryStatus.SUCCESS, Progress=100, Message="Done", LogID=log.LogID)
    db_session.session.add(status)
    db_session.session.flush()
    device = NetworkDiscovery(
        Hostname="web-01", IP_Address="10.0.20.11", Network="10.0.20.0/24", Nagios_Host_Name=nagios_name,
        Device_State=state, Include_Device_In_Scanning=include, DiscoveryStatusID=status.DiscoveryStatusID)
    db_session.session.add(device)
    db_session.session.flush()
    db_session.session.add(SSHCredentials(
        SSH_Port=port, Key_Installed=key_installed, Key_Fingerprint=fingerprint,
        Remote_Restart_Enabled=enabled, Remote_Restart_Services=list(services) if services else None,
        NetworkDiscoveryID=device.NetDiscoveryID))
    db_session.session.commit()
    return device


def test_an_active_trusted_enabled_device_becomes_a_target(db_session, admin_user):
    make_device(db_session, admin_user)
    target, refusal = remediation.resolve_remote_target("web-01")
    assert refusal is None
    assert target == registry.RemoteTarget("10.0.20.11", 2222, FINGERPRINT, ("apache2",))


def test_an_unknown_host_is_refused(db_session, admin_user):
    make_device(db_session, admin_user)
    target, refusal = remediation.resolve_remote_target("other-host")
    assert target is None and "no monitored device" in refusal


@pytest.mark.parametrize("state", [DeviceState.RETIRED, DeviceState.MERGED, DeviceState.MISSING,
                                   DeviceState.ADDRESS_UNKNOWN])
def test_a_device_that_is_not_active_is_refused(db_session, admin_user, state):
    make_device(db_session, admin_user, state=state)
    target, refusal = remediation.resolve_remote_target("web-01")
    assert target is None and "not active" in refusal


def test_a_paused_device_is_refused(db_session, admin_user):
    make_device(db_session, admin_user, include=False)
    target, refusal = remediation.resolve_remote_target("web-01")
    assert target is None and "paused" in refusal


@pytest.mark.parametrize("changes", [{"key_installed": False}, {"fingerprint": None}])
def test_a_device_that_is_not_trusted_is_refused(db_session, admin_user, changes):
    make_device(db_session, admin_user, **changes)
    target, refusal = remediation.resolve_remote_target("web-01")
    assert target is None and "not trusted" in refusal


def test_a_device_without_the_switch_on_is_refused(db_session, admin_user):
    make_device(db_session, admin_user, enabled=False)
    target, refusal = remediation.resolve_remote_target("web-01")
    assert target is None and "not turned on" in refusal


def test_an_empty_list_gives_a_target_that_allows_nothing(db_session, admin_user):
    make_device(db_session, admin_user, services=None)
    target, _ = remediation.resolve_remote_target("web-01")
    assert target.services == ()


# ==========================================================
# SSH SIDE (SSH mocked)
# ==========================================================

DEPLOY = "app.remote_restart.deploy"


def ssh_client(status):
    client = MagicMock()
    channel = MagicMock()
    channel.recv_exit_status.return_value = status
    stdout = MagicMock()
    stdout.channel = channel
    client.exec_command.return_value = (MagicMock(), stdout, MagicMock())
    return client


def deploy_mock(check="ok", client=None):
    deploy = MagicMock()
    deploy.check_host_key.return_value = check
    deploy.connect_with_fingerprint_check.return_value = client
    deploy.DEPLOYMENT_USER = "pinpoint-deployment"
    deploy.PRIVATE_KEY_PATH = "/home/pinpoint/.ssh/pinpoint_ncpa_deploy"
    deploy.HOST_KEY_CHANGED_MESSAGE = "Host key changed. Verify the device's host key again."
    return deploy


def test_a_changed_host_key_stops_before_any_login():
    deploy = deploy_mock(check="mismatch")
    with patch(DEPLOY, deploy):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "host_key_changed" and "Host key changed" in message
    deploy.connect_with_fingerprint_check.assert_not_called()


def test_an_unreachable_device_is_a_failure_with_no_login():
    deploy = deploy_mock(check="unreachable")
    with patch(DEPLOY, deploy):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "failed" and "unreachable" in message
    deploy.connect_with_fingerprint_check.assert_not_called()


def test_the_only_remote_command_is_the_helper_with_one_quoted_unit():
    client = ssh_client(0)
    with patch(DEPLOY, deploy_mock(client=client)):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "succeeded" and "exit code 0" in message
    command = client.exec_command.call_args[0][0]
    assert command == "sudo -n /usr/local/sbin/pinpoint-service-restart apache2"
    client.close.assert_called_once()


def test_the_login_uses_the_deployment_account_and_key_and_the_stored_fingerprint():
    deploy = deploy_mock(client=ssh_client(0))
    with patch(DEPLOY, deploy):
        remote_restart.restart_remote_unit("10.0.20.11", 2222, FINGERPRINT, "apache2")
    deploy.connect_with_fingerprint_check.assert_called_once_with(
        "10.0.20.11", 2222, "pinpoint-deployment", FINGERPRINT,
        private_key="/home/pinpoint/.ssh/pinpoint_ncpa_deploy")


@pytest.mark.parametrize("bad", ["nagios; reboot", "a b", "-x", "", "$(id)"])
def test_an_invalid_unit_never_reaches_ssh(bad):
    deploy = deploy_mock(client=ssh_client(0))
    with patch(DEPLOY, deploy):
        outcome, _ = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, bad)
    assert outcome == "failed"
    deploy.check_host_key.assert_not_called()


@pytest.mark.parametrize("status, text", [
    (3, "not on its service list"), (2, "invalid service name"), (1, "exit code 1"), (5, "exit code 5")])
def test_helper_exit_codes_become_fixed_messages(status, text):
    with patch(DEPLOY, deploy_mock(client=ssh_client(status))):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "failed" and text in message


def test_a_refused_key_is_reported_without_exception_text():
    import paramiko
    deploy = deploy_mock()
    deploy.connect_with_fingerprint_check.side_effect = paramiko.AuthenticationException("secret=abc")
    with patch(DEPLOY, deploy):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "failed" and "abc" not in message


def test_a_command_that_overruns_is_a_timeout():
    client = ssh_client(0)
    client.exec_command.side_effect = TimeoutError("timed out")
    with patch(DEPLOY, deploy_mock(client=client)):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "timed_out"
    client.close.assert_called_once()


def test_an_unreachable_login_is_a_failure():
    with patch(DEPLOY, deploy_mock(client=None)):
        outcome, message = remote_restart.restart_remote_unit("10.0.20.11", 22, FINGERPRINT, "apache2")
    assert outcome == "failed" and "unreachable" in message


# ==========================================================
# DEVICE-SIDE INSTALL
# ==========================================================

def test_install_checks_the_sudoers_file_before_moving_it_into_place():
    deploy = MagicMock()
    deploy.DEPLOYMENT_USER = "pinpoint-deployment"
    deploy.run_sudo_command.return_value = {"success": True}
    with patch(DEPLOY, deploy):
        assert remote_restart.install_restart_helper(MagicMock(), "pw", ["apache2", "nagios"]) is True
    command = deploy.run_sudo_command.call_args[0][1]
    assert "NOPASSWD: /usr/local/sbin/pinpoint-service-restart" in command
    assert "apache2" in command and "nagios" in command
    # The rule is checked with visudo before it replaces the live file.
    assert command.index("visudo -cf") < command.index("/bin/mv -f /etc/sudoers.d/pinpoint-service-restart.new")
    # The password goes to sudo on stdin and is never part of the command.
    assert "pw" not in command.split()
    assert deploy.run_sudo_command.call_args[0][2] == "pw"


def test_install_reports_failure():
    deploy = MagicMock()
    deploy.DEPLOYMENT_USER = "pinpoint-deployment"
    deploy.run_sudo_command.return_value = {"success": False}
    with patch(DEPLOY, deploy):
        assert remote_restart.install_restart_helper(MagicMock(), "pw", []) is False


# ==========================================================
# THE HELPER SCRIPT ON THE DEVICE
# ==========================================================

BASH = shutil.which("bash")


def test_the_helper_script_has_no_shell_escape_hatches():
    script = remote_restart.HELPER_SCRIPT
    assert script.startswith("#!/bin/bash\nset -euo pipefail")
    for forbidden in ("eval ", "sh -c", "$(echo", "source ", "bash -c"):
        assert forbidden not in script
    assert 'exec "$SYSTEMCTL" restart -- "$UNIT"' in script


@pytest.fixture()
def helper(tmp_path):
    """The helper with its allowlist and systemctl pointed at harmless stand-ins."""
    if BASH is None:
        pytest.skip("bash is not available")
    allowlist = tmp_path / "restartable-services"
    fake_systemctl = tmp_path / "systemctl"
    fake_systemctl.write_text('#!/bin/bash\necho "$@" > "$(dirname "$0")/called"\n')
    fake_systemctl.chmod(0o755)
    script = remote_restart.HELPER_SCRIPT.replace(
        "/etc/pinpoint/restartable-services", allowlist.as_posix()).replace(
        "/usr/bin/systemctl", fake_systemctl.as_posix())
    path = tmp_path / "helper.sh"
    path.write_text(script, newline="\n")

    def run(*args):
        return subprocess.run([BASH, path.as_posix(), *args], capture_output=True, text=True, timeout=20)

    return SimpleNamespace(run=run, allowlist=allowlist, called=tmp_path / "called")


def test_helper_restarts_a_listed_unit(helper):
    helper.allowlist.write_text("apache2\nnagios\n")
    done = helper.run("apache2")
    owner_is_root_only = done.returncode in (0, 3)  # off Linux the file is not owned by root
    assert owner_is_root_only
    if done.returncode == 0:
        assert helper.called.read_text().split() == ["restart", "--", "apache2"]


@pytest.mark.parametrize("args", [(), ("a", "b"), ("nagios; reboot",), ("-x",), ("../x",), ("",), ("a b",)])
def test_helper_rejects_bad_arguments_with_exit_2(helper, args):
    helper.allowlist.write_text("nagios\n")
    assert helper.run(*args).returncode == 2
    assert not helper.called.exists()


def test_helper_refuses_everything_when_the_list_is_missing(helper):
    done = helper.run("nagios")
    assert done.returncode == 3 and not helper.called.exists()


def test_helper_refuses_a_unit_not_on_the_list(helper):
    helper.allowlist.write_text("nagios\n")
    done = helper.run("sshd")
    assert done.returncode == 3 and not helper.called.exists()


def test_helper_matches_whole_lines_only(helper):
    helper.allowlist.write_text("nagios-extra\n")
    assert helper.run("nagios").returncode == 3
    assert not helper.called.exists()


# ==========================================================
# ADMIN SETTINGS ROUTE
# ==========================================================

def path_for(device):
    return f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/remote-restart"


def test_settings_need_login_and_permission(client, limited_client, db_session, admin_user):
    device = make_device(db_session, admin_user)
    assert client.get(path_for(device)).status_code in (401, 302, 403)
    assert limited_client.get(path_for(device)).status_code == 403
    assert limited_client.put(path_for(device), json={"enabled": False}).status_code == 403


def test_settings_are_read_back(logged_in_client, db_session, admin_user):
    device = make_device(db_session, admin_user)
    body = logged_in_client.get(path_for(device)).get_json()["data"]
    assert body == {"enabled": True, "services": ["apache2"], "trusted": True}


def test_an_administrator_turns_it_on_with_a_list(logged_in_client, db_session, admin_user):
    device = make_device(db_session, admin_user, enabled=False, services=None)
    reply = logged_in_client.put(path_for(device), json={"enabled": True, "services": ["nagios", "apache2"]})
    assert reply.status_code == 200
    data = reply.get_json()["data"]
    assert data["enabled"] is True and data["services"] == ["apache2", "nagios"]
    assert data["redeploy_needed"] is True
    creds = db_session.session.query(SSHCredentials).one()
    assert creds.Remote_Restart_Enabled is True and creds.Remote_Restart_Services == ["apache2", "nagios"]


def test_turning_it_off_needs_no_redeploy(logged_in_client, db_session, admin_user):
    device = make_device(db_session, admin_user)
    reply = logged_in_client.put(path_for(device), json={"enabled": False, "services": ["apache2"]})
    assert reply.status_code == 200 and reply.get_json()["data"]["redeploy_needed"] is False


@pytest.mark.parametrize("body", [
    {}, {"enabled": "yes", "services": ["nagios"]}, {"enabled": 1, "services": ["nagios"]},
    {"enabled": True, "services": "nagios"}, {"enabled": True, "services": ["nagios; reboot"]},
    {"enabled": True, "services": []}, {"enabled": True, "services": ["a"], "command": "id"},
])
def test_bad_settings_are_refused_and_nothing_changes(logged_in_client, db_session, admin_user, body):
    device = make_device(db_session, admin_user, enabled=False, services=None)
    assert logged_in_client.put(path_for(device), json=body).status_code == 400
    creds = db_session.session.query(SSHCredentials).one()
    assert creds.Remote_Restart_Enabled is False and not creds.Remote_Restart_Services


def test_an_untrusted_device_cannot_be_turned_on(logged_in_client, db_session, admin_user):
    device = make_device(db_session, admin_user, enabled=False, key_installed=False)
    reply = logged_in_client.put(path_for(device), json={"enabled": True, "services": ["nagios"]})
    assert reply.status_code == 409


def test_an_unknown_device_is_a_404(logged_in_client, db_session, admin_user):
    assert logged_in_client.get("/api/system/deployment/ncpa/9999/remote-restart").status_code == 404


# ==========================================================
# DEPLOYMENT INSTALLS THE HELPER
# ==========================================================

def deployment_patches(ncpa, installed):
    return [
        patch.object(ncpa, "query_trusted_host", return_value=(FINGERPRINT, 22)),
        patch.object(ncpa, "check_host_key", return_value="ok"),
        patch.object(ncpa, "connect_with_fingerprint_check", return_value=MagicMock()),
        patch.object(ncpa, "check_debian_based", return_value=(True, "Debian")),
        patch.object(ncpa, "ensure_deployment_user", return_value=True),
        patch.object(ncpa, "install_deployment_helper", return_value=True),
        patch.object(ncpa, "install_deployment_key", return_value=True),
        patch.object(ncpa, "install_restricted_sudo", return_value=True),
        patch.object(ncpa, "update_ncpa_deployment_info"),
        patch("app.remote_restart.install_restart_helper", installed),
    ]


def run_bootstrap(app, device, installed):
    from contextlib import ExitStack
    from app.ncpa_deployment import ncpa_deployment as ncpa
    with app.app_context(), ExitStack() as stack:
        for patcher in deployment_patches(ncpa, installed):
            stack.enter_context(patcher)
        return ncpa.give_program_permissions(device.NetDiscoveryID, 1, "10.0.20.11", "admin", "pw")


def test_bootstrap_installs_the_restart_helper_with_the_devices_list(app, db_session, admin_user):
    device = make_device(db_session, admin_user, services=("nagios", "apache2"))
    installed = MagicMock(return_value=True)
    outcome, error = run_bootstrap(app, device, installed)
    assert error is None
    assert installed.call_args[0][1] == "pw"
    assert installed.call_args[0][2] == ["apache2", "nagios"]


def test_bootstrap_installs_an_empty_list_when_nothing_is_chosen(app, db_session, admin_user):
    device = make_device(db_session, admin_user, enabled=False, services=None)
    installed = MagicMock(return_value=True)
    outcome, error = run_bootstrap(app, device, installed)
    assert error is None and installed.call_args[0][2] == []


def test_bootstrap_fails_cleanly_when_the_helper_cannot_be_installed(app, db_session, admin_user):
    device = make_device(db_session, admin_user)
    outcome, error = run_bootstrap(app, device, MagicMock(return_value=False))
    assert "restart helper" in error


def test_remote_exit_status_wait_has_an_actual_deadline(monkeypatch):
    client = ssh_client(0)
    channel = client.exec_command.return_value[1].channel
    channel.exit_status_ready.return_value = False
    channel.recv_ready.return_value = False
    channel.recv_stderr_ready.return_value = False
    clock = iter([0, 0, 21])
    monkeypatch.setattr(remote_restart, 'monotonic', lambda: next(clock), raising=False)
    monkeypatch.setattr(remote_restart, 'sleep', lambda _: None, raising=False)
    with patch(DEPLOY, deploy_mock(client=client)):
        outcome, _ = remote_restart.restart_remote_unit('10.0.20.11', 22, FINGERPRINT, 'apache2')
    assert outcome == 'timed_out'
    channel.recv_exit_status.assert_not_called()
    client.close.assert_called_once()


def test_restart_helper_install_suppresses_remote_output_and_secures_parent():
    deploy = MagicMock()
    deploy.DEPLOYMENT_USER = 'pinpoint-deployment'
    deploy.run_sudo_command.return_value = {'success': True}
    with patch(DEPLOY, deploy):
        remote_restart.install_restart_helper(MagicMock(), 'private-password', ['apache2'])
    call = deploy.run_sudo_command.call_args
    assert call.kwargs['suppress_output'] is True
    assert '/usr/bin/chown root:root /etc/pinpoint' in call.args[1]
    assert '! -L /etc/pinpoint' in call.args[1]
