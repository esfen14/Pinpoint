"""
tests/unit/test_remediation_service_recovery.py — GET/PUT /api/system/remediation/services/<host>/<service>
(Issue #154, plan issue #23: the per-service "Recover automatically" switch).

The switch is one RemediationAction scoped to exactly one host and service. These tests cover
the choice of action and unit (always made by the server), the permission split, 400 for any
input beyond enabled and the restart limit, 409 for a stale version, 422 for a config Nagios
rejects or a device that cannot be acted on, that the Remediation screen and the switch share
the same row, and that disabling takes the handler out of the generated config.
"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app.network_discovery import host_config_templates as templates
from app.system_models import (
    ActivityLog, DeviceState, DiscoveryStatus, NetworkDiscovery, NetworkDiscoveryStatus, Permission,
    RemediationAction, RemediationActionType, RemediationEventState, RemediationEventStateType,
    RemediationOutcome, RemediationRun, RolePermission, SSHCredentials,
)
from tests.support.seed_helpers import _make_service

BASE = "/api/system/remediation"
APPLY = "app.network_discovery.create_host_cfg.regenerate_and_apply_config_status"
HOST = "web-01"
SERVICE = "ssh-22-tcp"
FINGERPRINT = "SHA256:" + "a" * 43


def url(host=HOST, service=SERVICE):
    return f"{BASE}/services/{host}/{service}"


@pytest.fixture(autouse=True)
def nagios_apply():
    """Nagios accepts the config unless a test says otherwise."""
    with patch(APPLY, return_value=("applied", "ok")) as apply:
        yield apply


@pytest.fixture(autouse=True)
def handler_installed(monkeypatch):
    """Pretend the event handler program exists, as it does on the appliance."""
    monkeypatch.setattr(templates, "handler_exists", lambda path: True)


def grant(db_session, role, name):
    permission = db_session.session.query(Permission).filter_by(Name=name).one()
    db_session.session.add(RolePermission(RoleID=role.RoleID, PermissionID=permission.PermissionID))
    db_session.session.commit()


def make_device(db_session, admin_user, nagios_name=HOST, state=DeviceState.ACTIVE, include=True,
                key_installed=True, enabled=True, services=("ssh",)):
    """A device with a deployment key. Returns the device."""
    log = ActivityLog(Action_Type="test", UserID=admin_user.UserID)
    db_session.session.add(log)
    db_session.session.flush()
    status = NetworkDiscoveryStatus(Status=DiscoveryStatus.SUCCESS, Progress=100, Message="Done", LogID=log.LogID)
    db_session.session.add(status)
    db_session.session.flush()
    device = NetworkDiscovery(
        Hostname=nagios_name, IP_Address="10.0.20.11", Network="10.0.20.0/24", Nagios_Host_Name=nagios_name,
        Device_State=state, Include_Device_In_Scanning=include, DiscoveryStatusID=status.DiscoveryStatusID)
    db_session.session.add(device)
    db_session.session.flush()
    db_session.session.add(SSHCredentials(
        SSH_Port=22, Key_Installed=key_installed, Key_Fingerprint=FINGERPRINT if key_installed else None,
        Remote_Restart_Enabled=enabled, Remote_Restart_Services=list(services) if services else None,
        NetworkDiscoveryID=device.NetDiscoveryID))
    db_session.session.commit()
    return device


def add_service(db_session, host=HOST, service=SERVICE):
    _make_service(db_session, hostname=host, service=service)
    db_session.session.commit()


@pytest.fixture()
def ready(db_session, admin_user):
    """A trusted device that may restart ssh, and its monitored ssh service."""
    device = make_device(db_session, admin_user)
    add_service(db_session)
    return device


def actions(db_session):
    return db_session.session.scalars(sa.select(RemediationAction)).all()


def enable(client, **changes):
    return client.put(url(), json={"enabled": True, "maxRestartsPerHour": 2, **changes})


# ==========================================================
# PERMISSIONS
# ==========================================================

def test_both_routes_need_login(client, ready):
    assert client.get(url()).status_code in (401, 302)
    assert client.put(url(), json={"enabled": True, "maxRestartsPerHour": 2}).status_code in (401, 302)


def test_without_the_permissions_the_routes_are_403(limited_client, ready, db_session):
    assert limited_client.get(url()).status_code == 403
    assert limited_client.put(url(), json={"enabled": True, "maxRestartsPerHour": 2}).status_code == 403
    assert actions(db_session) == []


def test_view_alone_can_read_but_not_change(limited_client, ready, db_session, regular_role):
    grant(db_session, regular_role, "remediation.view")
    assert limited_client.get(url()).status_code == 200
    assert limited_client.put(url(), json={"enabled": True, "maxRestartsPerHour": 2}).status_code == 403
    assert actions(db_session) == []


def test_manage_alone_cannot_read(limited_client, ready, db_session, regular_role):
    grant(db_session, regular_role, "remediation.manage")
    assert limited_client.get(url()).status_code == 403


# ==========================================================
# READING THE SETTING
# ==========================================================

def test_an_unconfigured_service_reports_what_would_be_used(logged_in_client, ready):
    body = logged_in_client.get(url()).get_json()["data"]
    assert body["enabled"] is False
    assert body["actionId"] is None and body["version"] is None
    assert body["canEnable"] is True and body["reason"] is None
    assert body["actionType"] == "restart_remote_service" and body["unit"] == "ssh"
    assert body["maxRestartsPerHour"] == 2
    assert body["lastRun"] is None and body["otherActions"] == []


def test_a_unit_alias_on_the_device_list_is_used(logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user, services=("sshd",))
    add_service(db_session)
    body = logged_in_client.get(url()).get_json()["data"]
    assert body["canEnable"] is True and body["unit"] == "sshd"


def test_an_unknown_service_is_a_404(logged_in_client, ready):
    assert logged_in_client.get(url(service="nope-1-tcp")).status_code == 404
    assert logged_in_client.get(url(host="other")).status_code == 404
    assert logged_in_client.put(
        url(service="nope-1-tcp"), json={"enabled": True, "maxRestartsPerHour": 2}).status_code == 404


def test_a_service_name_with_a_slash_works(logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user)
    add_service(db_session, service="ssh/22")
    assert logged_in_client.get(url(service="ssh/22")).status_code == 200


# ==========================================================
# ENABLING
# ==========================================================

def test_enabling_creates_one_action_scoped_to_that_service(logged_in_client, db_session, ready, nagios_apply):
    response = enable(logged_in_client, maxRestartsPerHour=3)
    assert response.status_code == 200
    rows = actions(db_session)
    assert len(rows) == 1
    row = rows[0]
    assert row.Scope_Kind.value == "service"
    assert row.Host_Pattern == HOST and row.Service_Pattern == SERVICE
    assert row.Action_Type is RemediationActionType.RESTART_REMOTE_SERVICE
    assert row.Parameters == {"unit": "ssh"}
    assert row.Enabled is True and row.Max_Runs_Per_Hour == 3
    assert nagios_apply.call_count == 1
    body = response.get_json()["data"]
    assert body["enabled"] is True and body["actionId"] == row.Id and body["version"] == 1
    assert body["maxRestartsPerHour"] == 3


def test_the_handler_is_added_to_that_service_only(logged_in_client, db_session, ready):
    stub = "define service {\n    service_description x\n}\n"
    assert "event_handler" not in templates.add_event_handler_lines(stub, "service", HOST, SERVICE)
    enable(logged_in_client)
    assert "event_handler" in templates.add_event_handler_lines(stub, "service", HOST, SERVICE)
    assert "event_handler" not in templates.add_event_handler_lines(stub, "service", HOST, "http-80-tcp")
    assert "event_handler" not in templates.add_event_handler_lines(stub, "service", "db-01", SERVICE)
    assert "event_handler" not in templates.add_event_handler_lines(stub, "host", HOST, None)


def test_disabling_keeps_the_row_bumps_the_version_and_removes_the_handler(
        logged_in_client, db_session, ready, nagios_apply):
    enable(logged_in_client)
    response = logged_in_client.put(url(), json={"enabled": False, "maxRestartsPerHour": 2, "version": 1})
    assert response.status_code == 200
    rows = actions(db_session)
    assert len(rows) == 1 and rows[0].Enabled is False and rows[0].Version == 2
    assert nagios_apply.call_count == 2
    stub = "define service {\n    service_description x\n}\n"
    assert "event_handler" not in templates.add_event_handler_lines(stub, "service", HOST, SERVICE)
    assert response.get_json()["data"]["enabled"] is False


def test_disabling_a_service_that_was_never_enabled_changes_nothing(
        logged_in_client, db_session, ready, nagios_apply):
    response = logged_in_client.put(url(), json={"enabled": False, "maxRestartsPerHour": 2})
    assert response.status_code == 200
    assert actions(db_session) == [] and nagios_apply.call_count == 0


def test_changing_only_the_limit_updates_the_same_row(logged_in_client, db_session, ready):
    enable(logged_in_client)
    response = logged_in_client.put(url(), json={"enabled": True, "maxRestartsPerHour": 5, "version": 1})
    assert response.status_code == 200
    rows = actions(db_session)
    assert len(rows) == 1 and rows[0].Max_Runs_Per_Hour == 5 and rows[0].Version == 2


def test_changes_are_written_to_the_configuration_log(logged_in_client, db_session, ready):
    from app.system_models import ConfigurationChanges
    enable(logged_in_client, maxRestartsPerHour=3)
    rows = db_session.session.scalars(sa.select(ConfigurationChanges)).all()
    assert {row.Conf_Type for row in rows} == {"remediation_action"}
    assert {"enabled", "maxRunsPerHour"} <= {row.Parameter_Name for row in rows}


# ==========================================================
# THE REMEDIATION SCREEN AND THE SWITCH SHARE ONE ROW
# ==========================================================

def screen_action(client, **changes):
    payload = {
        "name": "ssh-screen", "actionType": "restart_remote_service", "scopeKind": "service", "hostPattern": HOST,
        "servicePattern": SERVICE, "parameters": {"unit": "ssh"}, "enabled": True, "maxRunsPerHour": 4,
        "cooldownSeconds": 900, **changes,
    }
    return client.post(f"{BASE}/actions", json=payload)


def test_an_action_made_on_the_remediation_screen_shows_on_the_switch(logged_in_client, ready):
    created = screen_action(logged_in_client).get_json()["data"]
    body = logged_in_client.get(url()).get_json()["data"]
    assert body["enabled"] is True and body["actionId"] == created["id"]
    assert body["maxRestartsPerHour"] == 4 and body["version"] == created["version"]


def test_the_switch_changes_the_action_the_screen_made(logged_in_client, db_session, ready):
    created = screen_action(logged_in_client).get_json()["data"]
    logged_in_client.put(url(), json={
        "enabled": False, "maxRestartsPerHour": 3, "version": created["version"]})
    rows = actions(db_session)
    assert len(rows) == 1 and rows[0].Name == "ssh-screen"
    assert rows[0].Enabled is False and rows[0].Max_Runs_Per_Hour == 3 and rows[0].Cooldown_Seconds == 900
    listed = logged_in_client.get(f"{BASE}/actions").get_json()["data"]["items"]
    assert listed[0]["enabled"] is False and listed[0]["maxRunsPerHour"] == 3


def test_a_unit_chosen_on_the_screen_is_kept_while_it_is_still_valid(logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user, services=("ssh", "sshd"))
    add_service(db_session)
    created = screen_action(logged_in_client, parameters={"unit": "sshd"}, enabled=False).get_json()["data"]
    logged_in_client.put(url(), json={"enabled": True, "maxRestartsPerHour": 2, "version": created["version"]})
    assert actions(db_session)[0].Parameters == {"unit": "sshd"}


def test_another_enabled_action_that_covers_the_service_is_listed(logged_in_client, ready):
    screen_action(logged_in_client, name="all-ssh", actionType="record_only", parameters={},
                  hostPattern="web-*", servicePattern="ssh-*")
    body = logged_in_client.get(url()).get_json()["data"]
    assert body["enabled"] is False and body["actionId"] is None
    assert [item["name"] for item in body["otherActions"]] == ["all-ssh"]


def test_the_last_run_is_returned(logged_in_client, db_session, ready):
    created = enable(logged_in_client).get_json()["data"]
    older = datetime(2026, 10, 1, tzinfo=timezone.utc)
    newer = datetime(2026, 10, 2, tzinfo=timezone.utc)
    for received, outcome in ((older, RemediationOutcome.FAILED), (newer, RemediationOutcome.SUCCEEDED)):
        db_session.session.add(RemediationRun(
            Event_Key=f"k-{outcome.value}", Action_Id=created["actionId"], Action_Name="x", Hostname=HOST,
            Service=SERVICE, State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD,
            Attempt=3, Received_At=received, Outcome=outcome, Output="secret output"))
    db_session.session.commit()
    last = logged_in_client.get(url()).get_json()["data"]["lastRun"]
    assert last["outcome"] == "succeeded" and "id" in last and "output" not in last


# ==========================================================
# VALIDATION (400), VERSION (409), NAGIOS (422)
# ==========================================================

@pytest.mark.parametrize("extra", [
    {"unit": "nagios"}, {"command": "rm -rf /"}, {"script": "/tmp/x.sh"}, {"path": "/etc/passwd"},
    {"actionType": "restart_local_service"}, {"parameters": {"unit": "ssh"}}, {"hostPattern": "*"},
])
def test_a_unit_command_path_or_any_other_field_is_a_400(logged_in_client, db_session, ready, extra):
    response = enable(logged_in_client, **extra)
    assert response.status_code == 400
    assert list(extra)[0] in response.get_json()["data"]["fields"]
    assert actions(db_session) == []


@pytest.mark.parametrize("limit", [0, 7, -1, 2.5, "2", True, None])
def test_a_limit_outside_the_bounds_is_a_400(logged_in_client, db_session, ready, limit):
    response = enable(logged_in_client, maxRestartsPerHour=limit)
    assert response.status_code == 400
    assert "maxRestartsPerHour" in response.get_json()["data"]["fields"]
    assert actions(db_session) == []


@pytest.mark.parametrize("enabled", ["true", 1, None])
def test_enabled_must_be_true_or_false(logged_in_client, ready, enabled):
    response = enable(logged_in_client, enabled=enabled)
    assert response.status_code == 400 and "enabled" in response.get_json()["data"]["fields"]


@pytest.mark.parametrize("body", [None, [], "x"])
def test_a_body_that_is_not_an_object_is_a_400(logged_in_client, ready, body):
    assert logged_in_client.put(url(), json=body).status_code == 400


@pytest.mark.parametrize("version", [None, 7, "1", True])
def test_a_stale_or_missing_version_is_a_409(logged_in_client, db_session, ready, nagios_apply, version):
    enable(logged_in_client)
    nagios_apply.reset_mock()
    body = {"enabled": False, "maxRestartsPerHour": 2}
    if version is not None:
        body["version"] = version
    assert logged_in_client.put(url(), json=body).status_code == 409
    assert actions(db_session)[0].Enabled is True and nagios_apply.call_count == 0


def test_a_version_for_a_setting_that_does_not_exist_is_a_409(logged_in_client, db_session, ready):
    response = logged_in_client.put(url(), json={"enabled": True, "maxRestartsPerHour": 2, "version": 3})
    assert response.status_code == 409 and actions(db_session) == []


def test_a_config_nagios_rejects_rolls_the_enable_back(logged_in_client, db_session, ready, nagios_apply):
    nagios_apply.return_value = ("failed", "Nagios said no")
    response = enable(logged_in_client)
    assert response.status_code == 422 and "Nagios said no" in response.get_json()["message"]
    assert actions(db_session) == []


def test_a_config_nagios_rejects_rolls_the_disable_back(logged_in_client, db_session, ready, nagios_apply):
    enable(logged_in_client)
    nagios_apply.return_value = ("failed", "Nagios said no")
    response = logged_in_client.put(url(), json={"enabled": False, "maxRestartsPerHour": 2, "version": 1})
    assert response.status_code == 422
    row = actions(db_session)[0]
    assert row.Enabled is True and row.Version == 1


# ==========================================================
# WHEN NO ACTION IS VALID
# ==========================================================

def refused(client, db_session, text):
    """Reading gives the reason, enabling is refused with it, and no action is created."""
    body = client.get(url()).get_json()["data"]
    assert body["canEnable"] is False and text in body["reason"]
    assert body["actionType"] is None and body["unit"] is None
    response = enable(client)
    assert response.status_code == 422 and text in response.get_json()["message"]
    assert actions(db_session) == []


def test_a_paused_device_cannot_be_enabled(logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user, include=False)
    add_service(db_session)
    refused(logged_in_client, db_session, "paused")


@pytest.mark.parametrize("state", [DeviceState.RETIRED, DeviceState.MERGED, DeviceState.MISSING])
def test_a_retired_or_inactive_device_cannot_be_enabled(logged_in_client, db_session, admin_user, state):
    make_device(db_session, admin_user, state=state)
    add_service(db_session)
    refused(logged_in_client, db_session, "not active")


def test_an_untrusted_device_cannot_be_enabled(logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user, key_installed=False)
    add_service(db_session)
    refused(logged_in_client, db_session, "not trusted")


def test_a_device_with_remote_restart_off_cannot_be_enabled(logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user, enabled=False)
    add_service(db_session)
    refused(logged_in_client, db_session, "emote restart is not turned on")


def test_a_service_with_no_matching_unit_on_the_device_list_cannot_be_enabled(
        logged_in_client, db_session, admin_user):
    make_device(db_session, admin_user, services=("apache2",))
    add_service(db_session)
    refused(logged_in_client, db_session, "restart list")


def test_a_host_with_no_device_record_cannot_be_enabled(logged_in_client, db_session):
    add_service(db_session)
    refused(logged_in_client, db_session, "o monitored device")


def test_the_event_handler_not_being_installed_blocks_enabling(
        logged_in_client, db_session, ready, monkeypatch):
    monkeypatch.setattr(templates, "handler_exists", lambda path: False)
    refused(logged_in_client, db_session, "not installed")


def test_an_enabled_setting_on_a_device_that_was_paused_can_still_be_turned_off(
        logged_in_client, db_session, ready):
    enable(logged_in_client)
    ready.Include_Device_In_Scanning = False
    db_session.session.commit()
    body = logged_in_client.get(url()).get_json()["data"]
    assert body["enabled"] is True and body["canEnable"] is False and "paused" in body["reason"]
    response = logged_in_client.put(url(), json={"enabled": False, "maxRestartsPerHour": 2, "version": 1})
    assert response.status_code == 200 and actions(db_session)[0].Enabled is False


# ==========================================================
# THE PINPOINT HOST (LOCAL RESTART)
# ==========================================================

def test_a_service_on_the_pinpoint_host_uses_the_local_restart_and_the_fixed_unit_list(
        logged_in_client, db_session):
    add_service(db_session, host="localhost", service="nagios-process")
    body = logged_in_client.get(url("localhost", "nagios-process")).get_json()["data"]
    assert body["canEnable"] is True
    assert body["actionType"] == "restart_local_service" and body["unit"] == "nagios"
    response = logged_in_client.put(
        url("localhost", "nagios-process"), json={"enabled": True, "maxRestartsPerHour": 1})
    assert response.status_code == 200
    row = actions(db_session)[0]
    assert row.Action_Type is RemediationActionType.RESTART_LOCAL_SERVICE and row.Parameters == {"unit": "nagios"}


def test_a_pinpoint_host_service_with_no_listed_unit_cannot_be_enabled(logged_in_client, db_session):
    add_service(db_session, host="localhost", service="ssh-22-tcp")
    body = logged_in_client.get(url("localhost", "ssh-22-tcp")).get_json()["data"]
    assert body["canEnable"] is False and "nagios" in body["reason"]
    assert logged_in_client.put(
        url("localhost", "ssh-22-tcp"), json={"enabled": True, "maxRestartsPerHour": 1}).status_code == 422
    assert actions(db_session) == []


# ==========================================================
# UNIT CHOICE
# ==========================================================

@pytest.mark.parametrize("service,expected", [
    ("ssh-22-tcp", ["ssh", "sshd"]),
    ("HTTP-80-TCP", ["apache2", "httpd", "nginx", "http"]),
    ("redis-6379-tcp", ["redis"]),
    ("nagios process", ["nagios"]),
])
def test_unit_candidates_come_from_the_check_name(service, expected):
    from app import remediation
    assert remediation.unit_candidates(service) == expected


@pytest.mark.parametrize("service", ["", "-22-tcp", "../etc-1-tcp", "a;b-1-tcp", "$(x)"])
def test_a_check_name_never_yields_an_unsafe_unit(service):
    from app import remediation
    from app.remote_restart import valid_unit
    assert all(valid_unit(unit) for unit in remediation.unit_candidates(service))
