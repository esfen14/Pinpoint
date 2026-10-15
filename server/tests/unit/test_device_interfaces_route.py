"""
tests/unit/test_device_interfaces_route.py — The Device Inventory interface routes
(app/api/system/device_interfaces.py): list, refresh over SNMP, and the monitor on/off choice.

SNMP and Nagios are never touched: the walk and the config reconciler are replaced.
"""
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db
from app.network_discovery.interface_discovery import InterfaceDiscoveryError
from app.network_discovery.plugin_registry import MAX_MONITORED_INTERFACES
from app.system_models import ActivityLog, DeviceInterface
from tests.unit.test_interface_discovery import snmp_device
from tests.unit.test_create_host_cfg import make_device

BASE = "/api/system"
WALK = "app.network_discovery.interface_discovery.walk_interfaces"
INTERFACES = [
    {"if_index": 1, "name": "lo", "speed_bps": None, "admin_status": "up", "oper_status": "up"},
    {"if_index": 2, "name": "eth0", "speed_bps": 1_000_000_000, "admin_status": "up", "oper_status": "up"},
]


@pytest.fixture(autouse=True)
def reconcile():
    with patch("app.api.system.device_identity.reconcile_plugin_monitoring",
               return_value={"success": True, "changed": True, "message": "applied"}) as mock:
        yield mock


@pytest.fixture
def device(db_session, admin_user):
    return snmp_device(db_session, admin_user)


@pytest.fixture
def listed(logged_in_client, device):
    with patch(WALK, return_value=INTERFACES):
        assert logged_in_client.post(f"{BASE}/hosts/{device.NetDiscoveryID}/interfaces/refresh").status_code == 200
    return device


def url(device, suffix=""):
    return f"{BASE}/hosts/{device.NetDiscoveryID}/interfaces{suffix}"


class TestAccess:

    def test_requires_login(self, client, db_session):
        assert client.get(f"{BASE}/hosts/1/interfaces").status_code in (401, 302)
        assert client.post(f"{BASE}/hosts/1/interfaces/refresh").status_code in (401, 302)
        assert client.put(f"{BASE}/hosts/1/interfaces/1", json={"monitored": True}).status_code in (401, 302)

    def test_requires_permissions(self, limited_client, device):
        assert limited_client.get(url(device)).status_code == 403
        assert limited_client.post(url(device, "/refresh")).status_code == 403
        assert limited_client.put(url(device, "/1"), json={"monitored": True}).status_code == 403

    def test_unknown_device(self, logged_in_client, db_session):
        assert logged_in_client.get(f"{BASE}/hosts/999/interfaces").status_code == 404
        assert logged_in_client.post(f"{BASE}/hosts/999/interfaces/refresh").status_code == 404
        assert logged_in_client.put(f"{BASE}/hosts/999/interfaces/1", json={"monitored": True}).status_code == 404


class TestList:

    def test_empty_before_the_first_refresh(self, logged_in_client, device):
        data = logged_in_client.get(url(device)).get_json()["data"]
        assert data["interfaces"] == [] and data["snmp"] is True
        assert data["max_monitored"] == MAX_MONITORED_INTERFACES
        assert data["device"]["id"] == device.NetDiscoveryID

    def test_a_device_without_snmp_says_so(self, logged_in_client, db_session, admin_user):
        plain = make_device(db_session, admin_user, "plain", "10.0.0.50")
        assert logged_in_client.get(url(plain)).get_json()["data"]["snmp"] is False


class TestRefresh:

    def test_refresh_stores_and_returns_the_list(self, logged_in_client, device):
        with patch(WALK, return_value=INTERFACES):
            resp = logged_in_client.post(url(device, "/refresh"))

        assert resp.status_code == 200
        interfaces = resp.get_json()["data"]["interfaces"]
        assert [(i["if_index"], i["name"], i["monitored"], i["speed_bps"]) for i in interfaces] == [
            (1, "lo", False, None), (2, "eth0", False, 1_000_000_000),
        ]
        assert logged_in_client.get(url(device)).get_json()["data"]["interfaces"] == interfaces

    def test_an_unreachable_device_is_a_502_with_a_reason(self, logged_in_client, device):
        with patch(WALK, side_effect=InterfaceDiscoveryError("The device did not answer in time.")):
            resp = logged_in_client.post(url(device, "/refresh"))
        assert resp.status_code == 502
        assert resp.get_json()["message"] == "The device did not answer in time."

    def test_a_device_without_snmp_is_refused(self, logged_in_client, db_session, admin_user):
        plain = make_device(db_session, admin_user, "plain", "10.0.0.50")
        with patch(WALK) as walk:
            resp = logged_in_client.post(url(plain, "/refresh"))
        assert resp.status_code == 400
        walk.assert_not_called()


class TestMonitor:

    def put(self, client, device, index, body):
        return client.put(url(device, f"/{index}"), json=body)

    def test_start_monitoring_saves_logs_and_applies_the_config(self, logged_in_client, listed, reconcile):
        resp = self.put(logged_in_client, listed, 2, {"monitored": True})

        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert [i["monitored"] for i in data["interfaces"]] == [False, True]
        assert data["config_ok"] is True and data["config_applied"] is True
        reconcile.assert_called_once()
        logs = db.session.scalars(sa.select(ActivityLog.Action_Type)).all()
        assert any("Started monitoring interface eth0" in text for text in logs)

    def test_stop_monitoring(self, logged_in_client, listed):
        self.put(logged_in_client, listed, 2, {"monitored": True})
        resp = self.put(logged_in_client, listed, 2, {"monitored": False})

        assert [i["monitored"] for i in resp.get_json()["data"]["interfaces"]] == [False, False]

    def test_no_change_does_not_touch_nagios(self, logged_in_client, listed, reconcile):
        resp = self.put(logged_in_client, listed, 2, {"monitored": False})

        assert resp.status_code == 200 and resp.get_json()["data"]["config_applied"] is False
        reconcile.assert_not_called()

    def test_a_config_failure_keeps_the_change_and_reports_it(self, logged_in_client, listed, reconcile):
        reconcile.return_value = {"success": False, "changed": False, "message": "Config failed to validate"}
        resp = self.put(logged_in_client, listed, 2, {"monitored": True})

        data = resp.get_json()["data"]
        assert resp.status_code == 200 and data["config_ok"] is False
        assert data["config_message"] == "Config failed to validate"
        assert data["interfaces"][1]["monitored"] is True

    @pytest.mark.parametrize("body", [{}, {"monitored": "yes"}, {"monitored": 1}, {"monitored": None}])
    def test_bad_bodies_are_refused(self, logged_in_client, listed, body):
        assert self.put(logged_in_client, listed, 2, body).status_code == 400

    def test_unknown_interface(self, logged_in_client, listed):
        resp = self.put(logged_in_client, listed, 99, {"monitored": True})
        assert resp.status_code == 404 and "Refresh" in resp.get_json()["message"]

    def test_limit_per_device(self, logged_in_client, device, monkeypatch):
        monkeypatch.setattr("app.api.system.device_interfaces.MAX_MONITORED_INTERFACES", 1)
        with patch(WALK, return_value=INTERFACES):
            logged_in_client.post(url(device, "/refresh"))
        assert self.put(logged_in_client, device, 1, {"monitored": True}).status_code == 200

        resp = self.put(logged_in_client, device, 2, {"monitored": True})
        assert resp.status_code == 400 and "At most 1" in resp.get_json()["message"]

    def test_an_interface_the_device_dropped_cannot_be_started(self, logged_in_client, listed):
        row = db.session.scalar(sa.select(DeviceInterface).where(DeviceInterface.If_Index == 1))
        row.Present = False
        db.session.commit()
        assert self.put(logged_in_client, listed, 1, {"monitored": True}).status_code == 400

    def test_a_failed_commit_rolls_back(self, logged_in_client, listed):
        with patch("app.api.system.device_interfaces.create_user_log"), \
                patch.object(db.session, "commit", side_effect=RuntimeError("disk full")), \
                patch.object(db.session, "rollback", wraps=db.session.rollback) as rollback:
            resp = self.put(logged_in_client, listed, 2, {"monitored": True})
        assert resp.status_code == 500
        rollback.assert_called()
