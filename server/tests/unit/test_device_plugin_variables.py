"""
tests/unit/test_device_plugin_variables.py — per-device plugin variable routes (issue #127, 14.1/14.2):

  GET    /api/system/hosts/<id>/plugin-variables/<plugin>
  PUT    /api/system/hosts/<id>/plugin-variables/<plugin>
  DELETE /api/system/hosts/<id>/plugin-variables/<plugin>
  POST   /api/system/hosts/<id>/plugin-variables/snmp/test

Regenerating the Nagios config and running check_snmp are mocked: no Nagios, no network.
"""
import json
import logging
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db
from app.system_models import ActivityLog, DeviceState, NetworkDiscovery
from tests.support.identity_helpers import make_status, run_scan, scan, NET

BASE = "/api/system"
APPLY = "app.network_discovery.create_host_cfg.regenerate_and_apply_config_status"
PASSWORD = "synthetic-auth-secret"
PRIVACY = "synthetic-priv-secret"
V3 = {"protocol": "3", "security_level": "authPriv", "v3_user": "monitor", "auth_protocol": "SHA",
      "auth_password": PASSWORD, "priv_protocol": "AES", "priv_password": PRIVACY}


@pytest.fixture(autouse=True)
def applied():
    """The shared config writer reports success unless a test says otherwise."""
    with patch(APPLY, return_value=("applied", "Applied.")) as mock:
        yield mock


@pytest.fixture
def device(db_session, admin_user):
    status = make_status(db_session, admin_user)
    return run_scan(db_session, status, scan("10.0.0.5"))[(NET, "10.0.0.5")]


def url(device, plugin="snmp", suffix=""):
    return f"{BASE}/hosts/{device.NetDiscoveryID}/plugin-variables/{plugin}{suffix}"


def stored(device):
    db.session.refresh(device)
    return device.Plugin_Variables


def put(client, device, variables, **extra):
    return client.put(url(device), json={"variables": variables, **extra})


# ==========================================================
# AUTH
# ==========================================================

class TestAuth:

    @pytest.mark.parametrize("method", ["get", "put", "delete"])
    def test_requires_login(self, client, db_session, method):
        assert getattr(client, method)(f"{BASE}/hosts/1/plugin-variables/snmp", json={}).status_code in (401, 302)

    def test_test_route_requires_login(self, client, db_session):
        assert client.post(f"{BASE}/hosts/1/plugin-variables/snmp/test", json={}).status_code in (401, 302)

    @pytest.mark.parametrize("method", ["get", "put", "delete"])
    def test_requires_permission(self, limited_client, db_session, method):
        resp = getattr(limited_client, method)(f"{BASE}/hosts/1/plugin-variables/snmp", json={"variables": {}})
        assert resp.status_code == 403

    def test_test_route_requires_permission(self, limited_client, db_session):
        assert limited_client.post(f"{BASE}/hosts/1/plugin-variables/snmp/test", json={}).status_code == 403

    def test_read_permission_alone_cannot_write(self, client, db_session, device, seeded_permissions):
        from app.system_models import Role, RolePermission, User, UserStatus
        role = Role(Name="Reader", Is_Active=True, Description="r")
        db_session.session.add(role)
        db_session.session.flush()
        db_session.session.add(RolePermission(
            RoleID=role.RoleID, PermissionID=seeded_permissions["system.hosts"].PermissionID))
        user = User(First_Name="R", Last_Name="R", Email="reader@example.com", Status=UserStatus.ACTIVE,
                    RoleID=role.RoleID)
        user.set_password("ReaderPass1!")
        db_session.session.add(user)
        db_session.session.commit()
        client.post("/api/user/login", json={"email": "reader@example.com", "password": "ReaderPass1!"})

        assert client.get(url(device)).status_code == 200
        assert client.put(url(device), json={"variables": {"community": "x"}}).status_code == 403
        assert client.delete(url(device)).status_code == 403
        assert client.post(url(device, suffix="/test"), json={}).status_code == 403


# ==========================================================
# READ, SAVE, RESET
# ==========================================================

class TestSaveReadReset:

    def test_no_override_reads_as_empty(self, logged_in_client, device):
        body = logged_in_client.get(url(device)).get_json()["data"]
        assert body["variables"] == {} and body["secrets_set"] == {"auth_password": False, "priv_password": False}
        assert "community" in body["editable"] and "oid" not in body["editable"]

    def test_in_use_follows_the_devices_snmp_port(self, logged_in_client, device):
        from app.system_models import Open_UDP_Services, PortState
        assert logged_in_client.get(url(device)).get_json()["data"]["in_use"] is False
        assert logged_in_client.get(url(device, "http")).get_json()["data"]["in_use"] is None
        db.session.add(Open_UDP_Services(Port_Number=161, Service_Name="snmp", Plugin_Name="snmp",
                                         Port_State=PortState.MONITORED, NetDiscoveryID=device.NetDiscoveryID))
        db.session.commit()
        assert logged_in_client.get(url(device)).get_json()["data"]["in_use"] is True

    def test_save_and_reset_keep_reporting_in_use(self, logged_in_client, device):
        from app.system_models import Open_UDP_Services, PortState
        db.session.add(Open_UDP_Services(Port_Number=161, Service_Name="snmp", Plugin_Name="snmp",
                                         Port_State=PortState.MONITORED, NetDiscoveryID=device.NetDiscoveryID))
        db.session.commit()
        assert put(logged_in_client, device, {"community": "lab"}).get_json()["data"]["in_use"] is True
        assert logged_in_client.delete(url(device)).get_json()["data"]["in_use"] is True

    def test_save_and_reset_report_in_use_false_without_an_snmp_port(self, logged_in_client, device):
        assert put(logged_in_client, device, {"community": "lab"}).get_json()["data"]["in_use"] is False
        assert logged_in_client.delete(url(device)).get_json()["data"]["in_use"] is False

    def test_save_then_read_back(self, logged_in_client, device, applied):
        resp = put(logged_in_client, device, {"protocol": "2c", "community": "lab"})
        assert resp.status_code == 200
        assert stored(device) == {"snmp": {"protocol": "2c", "community": "lab"}}
        assert logged_in_client.get(url(device)).get_json()["data"]["variables"] == {"protocol": "2c", "community": "lab"}
        applied.assert_called_once()

    def test_saving_one_plugin_keeps_the_others(self, logged_in_client, device):
        device.Plugin_Variables = {"http": {"url": "/up"}}
        db.session.commit()
        put(logged_in_client, device, {"community": "lab"})
        assert stored(device) == {"http": {"url": "/up"}, "snmp": {"community": "lab"}}

    def test_put_replaces_the_previous_plain_values(self, logged_in_client, device):
        put(logged_in_client, device, {"community": "lab", "port": 1161})
        put(logged_in_client, device, {"community": "other"})
        assert stored(device) == {"snmp": {"community": "other"}}

    def test_reset_with_delete(self, logged_in_client, device):
        put(logged_in_client, device, {"community": "lab"})
        resp = logged_in_client.delete(url(device))
        assert resp.status_code == 200 and stored(device) is None

    def test_reset_with_empty_body_keeps_other_plugins(self, logged_in_client, device):
        device.Plugin_Variables = {"http": {"url": "/up"}, "snmp": {"community": "lab"}}
        db.session.commit()
        assert logged_in_client.put(url(device), json={}).status_code == 200
        assert stored(device) == {"http": {"url": "/up"}}

    def test_saving_an_empty_override_removes_it(self, logged_in_client, device):
        put(logged_in_client, device, {"community": "lab"})
        put(logged_in_client, device, {})
        assert stored(device) is None

    def test_activity_log_names_variables_not_values(self, logged_in_client, device):
        put(logged_in_client, device, V3)
        rows = [row.Action_Type for row in db.session.scalars(sa.select(ActivityLog)).all()]
        entry = next(row for row in rows if "snmp" in row.lower() and "settings" in row.lower())
        assert "protocol" in entry and "monitor" not in entry
        assert PASSWORD not in " ".join(rows) and PRIVACY not in " ".join(rows)


# ==========================================================
# VALIDATION AND REFUSALS
# ==========================================================

class TestRefusals:

    def test_unknown_plugin_is_404(self, logged_in_client, device):
        assert logged_in_client.get(url(device, "nope")).status_code == 404
        assert logged_in_client.put(url(device, "nope"), json={"variables": {}}).status_code == 404
        assert logged_in_client.delete(url(device, "nope")).status_code == 404

    def test_unknown_device_is_404(self, logged_in_client, db_session):
        assert logged_in_client.get(f"{BASE}/hosts/999/plugin-variables/snmp").status_code == 404

    def test_unknown_key_is_400_naming_the_field(self, logged_in_client, device):
        resp = put(logged_in_client, device, {"colour": "red"})
        assert resp.status_code == 400
        assert resp.get_json()["data"]["field"] == "colour" and "colour" in resp.get_json()["message"]
        assert stored(device) is None

    def test_invalid_value_is_400_naming_the_field(self, logged_in_client, device):
        resp = put(logged_in_client, device, {"port": 99999})
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == "port"
        resp = put(logged_in_client, device, {"community": "a'b"})
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == "community"

    @pytest.mark.parametrize("state", [DeviceState.RETIRED, DeviceState.MERGED])
    def test_retired_or_merged_device_is_refused(self, logged_in_client, device, state):
        device.Device_State = state
        db.session.commit()
        assert put(logged_in_client, device, {"community": "x"}).status_code == 400
        assert logged_in_client.delete(url(device)).status_code == 400

    @pytest.mark.parametrize("body", [None, "text", [1], {"variables": [1]}, {"variables": "x"}])
    def test_malformed_bodies_are_400(self, logged_in_client, device, body):
        resp = logged_in_client.put(url(device), data=json.dumps(body), content_type="application/json")
        assert resp.status_code == 400 if body is not None else resp.status_code in (200, 400)

    def test_oversized_body_is_refused(self, logged_in_client, device):
        resp = put(logged_in_client, device, {"community": "x" * 20000})
        assert resp.status_code in (400, 413)

    def test_extra_top_level_keys_are_refused(self, logged_in_client, device):
        resp = logged_in_client.put(url(device), json={"variables": {}, "extra": 1})
        assert resp.status_code == 400

    def test_rejected_config_rolls_back_with_422(self, logged_in_client, device, applied):
        put(logged_in_client, device, {"community": "lab"})
        applied.return_value = ("failed", "Config failed to validate: nope")
        resp = put(logged_in_client, device, {"community": "other"})
        assert resp.status_code == 422 and "nope" in resp.get_json()["message"]
        assert stored(device) == {"snmp": {"community": "lab"}}
        assert logged_in_client.delete(url(device)).status_code == 422
        assert stored(device) == {"snmp": {"community": "lab"}}

    def test_apply_exception_is_reported_and_rolled_back(self, logged_in_client, device, applied):
        applied.side_effect = RuntimeError("boom")
        assert put(logged_in_client, device, {"community": "x"}).status_code == 500
        assert stored(device) is None


# ==========================================================
# SNMP v3
# ==========================================================

class TestSnmpV3:

    def test_v3_save_encrypts_and_never_returns_passwords(self, logged_in_client, device):
        resp = put(logged_in_client, device, V3)
        assert resp.status_code == 200
        assert PASSWORD not in resp.get_data(as_text=True) and PRIVACY not in resp.get_data(as_text=True)
        blob = json.dumps(stored(device))
        assert PASSWORD not in blob and PRIVACY not in blob
        read = logged_in_client.get(url(device))
        assert PASSWORD not in read.get_data(as_text=True)
        data = read.get_json()["data"]
        assert data["secrets_set"] == {"auth_password": True, "priv_password": True}
        assert data["variables"]["v3_user"] == "monitor"

    @pytest.mark.parametrize("missing", ["security_level", "v3_user", "auth_protocol", "auth_password",
                                         "priv_protocol", "priv_password"])
    def test_missing_field_is_400_naming_it(self, logged_in_client, device, missing):
        resp = put(logged_in_client, device, {k: v for k, v in V3.items() if k != missing})
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == missing
        assert stored(device) is None

    def test_omitted_password_is_kept(self, logged_in_client, device):
        put(logged_in_client, device, V3)
        before = stored(device)["snmp"]["auth_password_enc"]
        without = {k: v for k, v in V3.items() if not k.endswith("_password")}
        assert put(logged_in_client, device, {**without, "v3_user": "other"}).status_code == 200
        assert stored(device)["snmp"]["auth_password_enc"] == before
        assert stored(device)["snmp"]["v3_user"] == "other"

    def test_clearing_a_required_password_is_400(self, logged_in_client, device):
        put(logged_in_client, device, V3)
        without = {k: v for k, v in V3.items() if not k.endswith("_password")}
        resp = put(logged_in_client, device, without, clear_secrets=["priv_password"])
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == "priv_password"

    def test_dropping_to_a_lower_level_removes_the_unused_password(self, logged_in_client, device):
        put(logged_in_client, device, V3)
        resp = put(logged_in_client, device, {"protocol": "3", "security_level": "authNoPriv", "v3_user": "monitor",
                                              "auth_protocol": "SHA"})
        assert resp.status_code == 200
        assert "priv_password_enc" not in stored(device)["snmp"] and "auth_password_enc" in stored(device)["snmp"]

    def test_switching_to_v2c_removes_every_credential(self, logged_in_client, device):
        put(logged_in_client, device, V3)
        assert put(logged_in_client, device, {"protocol": "2c", "community": "lab"}).status_code == 200
        assert stored(device) == {"snmp": {"protocol": "2c", "community": "lab"}}

    def test_weak_password_is_400_without_echo(self, logged_in_client, device):
        resp = put(logged_in_client, device, {**V3, "priv_password": "short"})
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == "priv_password"
        assert "short" not in resp.get_json()["message"]

    def test_no_password_in_logs(self, logged_in_client, device, caplog):
        with caplog.at_level(logging.DEBUG):
            put(logged_in_client, device, V3)
            logged_in_client.get(url(device))
            put(logged_in_client, device, {**V3, "v3_user": "bad user"})
        assert PASSWORD not in caplog.text and PRIVACY not in caplog.text

    def test_server_without_a_fixed_key_refuses_to_store_passwords(self, logged_in_client, device, app):
        with patch("app.network_discovery.device_plugin_variables.secrets_store.encrypt",
                   side_effect=__import__("app.secrets_store", fromlist=["SecretsError"]).SecretsError("no key")):
            resp = put(logged_in_client, device, V3)
        assert resp.status_code == 400 and "no key" in resp.get_json()["message"]
        assert stored(device) is None


# ==========================================================
# TEST ACTION
# ==========================================================

class FakeResult:
    def __init__(self, returncode=0, stdout="SNMP OK - 12345 | uptime=12345", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class TestTestAction:

    def run(self, client, device, body=None, **kwargs):
        with patch("app.network_discovery.snmp_check.subprocess.run", return_value=FakeResult(**kwargs)) as mock:
            resp = client.post(url(device, suffix="/test"), json=body or {})
        return resp, mock

    def test_success_reports_ok(self, logged_in_client, device):
        put(logged_in_client, device, {"protocol": "2c", "community": "lab"})
        resp, mock = self.run(logged_in_client, device)
        data = resp.get_json()["data"]
        assert resp.status_code == 200 and data["ok"] is True and data["state"] == "OK"
        assert mock.call_args.args[0][0].endswith("check_snmp")

    def test_failure_reports_the_reason(self, logged_in_client, device):
        resp, _ = self.run(logged_in_client, device, returncode=2, stdout="External command error: Timeout")
        data = resp.get_json()["data"]
        assert resp.status_code == 200 and data["ok"] is False and data["state"] == "CRITICAL"
        assert "Timeout" in data["message"]

    def test_missing_plugin_is_a_clear_failure(self, logged_in_client, device):
        with patch("app.network_discovery.snmp_check.subprocess.run", side_effect=FileNotFoundError):
            data = logged_in_client.post(url(device, suffix="/test"), json={}).get_json()["data"]
        assert data["ok"] is False and "check_snmp" in data["message"]

    def test_v3_passwords_go_on_stdin_never_in_argv_and_never_in_output(self, logged_in_client, device):
        resp, mock = self.run(logged_in_client, device, {"variables": V3},
                              stdout=f"SNMP CRITICAL - bad {PASSWORD}", returncode=2)
        argv = mock.call_args.args[0]
        assert PASSWORD not in " ".join(argv) and PRIVACY not in " ".join(argv)
        assert mock.call_args.kwargs["input"] == f"[pinpoint]\nauthpasswd={PASSWORD}\nprivpasswd={PRIVACY}\n"
        assert PASSWORD not in resp.get_data(as_text=True)

    def test_test_uses_stored_passwords_when_the_form_leaves_them_blank(self, logged_in_client, device):
        put(logged_in_client, device, V3)
        without = {k: v for k, v in V3.items() if not k.endswith("_password")}
        _, mock = self.run(logged_in_client, device, {"variables": without})
        assert mock.call_args.kwargs["input"].count("passwd=") == 2

    def test_test_does_not_save_anything(self, logged_in_client, device, applied):
        self.run(logged_in_client, device, {"variables": V3})
        assert stored(device) is None
        applied.assert_not_called()

    def test_invalid_input_is_400(self, logged_in_client, device):
        resp = logged_in_client.post(url(device, suffix="/test"), json={"variables": {"colour": "red"}})
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == "colour"

    def test_only_snmp_can_be_tested(self, logged_in_client, device):
        assert logged_in_client.post(url(device, "http", "/test"), json={}).status_code == 400


# ==========================================================
# MAIL AND WEB CHECK OPTIONS (issue #131)
# ==========================================================

class TestWebAndMailOptions:

    WEB = {"expected_text": "Welcome", "expected_status": "200,301", "virtual_host": "www.example.com", "method": "HEAD"}

    @pytest.mark.parametrize("plugin", ["http", "https"])
    def test_web_options_are_saved_and_read_back(self, logged_in_client, device, plugin):
        resp = logged_in_client.put(url(device, plugin), json={"variables": self.WEB})
        assert resp.status_code == 200
        assert stored(device) == {plugin: self.WEB}
        data = logged_in_client.get(url(device, plugin)).get_json()["data"]
        assert data["variables"] == self.WEB
        assert {"expected_text", "expected_status", "virtual_host", "method"} <= set(data["editable"])

    @pytest.mark.parametrize("plugin", ["pop3", "imap", "pop3s", "imaps"])
    def test_mail_greeting_is_saved(self, logged_in_client, device, plugin):
        assert logged_in_client.put(url(device, plugin), json={"variables": {"expected_text": "+OK ready"}}).status_code == 200
        assert stored(device) == {plugin: {"expected_text": "+OK ready"}}

    @pytest.mark.parametrize("plugin,variable,value", [
        ("http", "expected_text", "it's"), ("http", "expected_text", "a;b"), ("http", "expected_text", "x$y"),
        ("http", "expected_status", "700"), ("http", "expected_status", "ok"), ("https", "expected_status", "200;"),
        ("http", "method", "FETCH"), ("https", "method", "get"),
        ("http", "virtual_host", "bad host"), ("https", "virtual_host", "-x"),
        ("pop3", "expected_text", "a`b"),
    ])
    def test_invalid_values_are_400_naming_the_field(self, logged_in_client, device, plugin, variable, value):
        resp = logged_in_client.put(url(device, plugin), json={"variables": {variable: value}})
        assert resp.status_code == 400
        assert resp.get_json()["data"]["field"] == variable and variable in resp.get_json()["message"]
        assert value not in resp.get_json()["message"]
        assert stored(device) is None

    def test_web_only_options_are_unknown_for_mail(self, logged_in_client, device):
        resp = logged_in_client.put(url(device, "imap"), json={"variables": {"virtual_host": "mail.example.com"}})
        assert resp.status_code == 400 and resp.get_json()["data"]["field"] == "virtual_host"

    def test_reset_returns_to_the_defaults(self, logged_in_client, device):
        logged_in_client.put(url(device, "http"), json={"variables": self.WEB})
        assert logged_in_client.delete(url(device, "http")).status_code == 200
        assert stored(device) is None
