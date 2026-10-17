"""
tests/unit/test_ncpa.py — Tests for NCPA deployment endpoints.

Endpoints tested (all under /api/system/deployment/ncpa/):
  GET  /devices
  GET  /<device_id>/fingerprint
  POST /<device_id>/confirm-trust
  POST /start
  POST /stop
  GET  /status
  GET  /devices/trusted
"""
import pytest
from unittest.mock import patch, MagicMock

from app.system_models import (
    NetworkDiscovery,
    NetworkDiscoveryStatus,
    DiscoveryStatus,
    ActivityLog,
    SSHCredentials,
    NCPADeployment,
    AgentStatus,
)


# ─── Seeding helper ───────────────────────────────────────────────────────────

def _make_ncpa_device(db_session, admin_user, trusted=False, ncpa_eligible=True):
    """Create a NetworkDiscovery device with an ActivityLog and SSHCredentials."""
    log = ActivityLog(Action_Type="test", UserID=admin_user.UserID)
    db_session.session.add(log)
    db_session.session.flush()

    ds = NetworkDiscoveryStatus(
        Status=DiscoveryStatus.SUCCESS,
        Progress=100,
        Message="Done",
        LogID=log.LogID,
    )
    db_session.session.add(ds)
    db_session.session.flush()

    device = NetworkDiscovery(
        Hostname="ncpa-host",
        IP_Address="10.99.0.1",
        Network="10.99.0.0",
        NCPA_Eligible=ncpa_eligible,
        DiscoveryStatusID=ds.DiscoveryStatusID,
    )
    db_session.session.add(device)
    db_session.session.flush()

    creds = SSHCredentials(
        SSH_Port=22,
        Key_Installed=False,
        Key_Fingerprint="abc:123" if trusted else None,
        NetworkDiscoveryID=device.NetDiscoveryID,
    )
    db_session.session.add(creds)
    db_session.session.commit()
    return device, creds


def test_deployed_port_resolution_uses_stored_port_and_default(app, db_session, admin_user):
    from app.ncpa_deployment.ncpa_deployment import deployed_ncpa_port

    device, _ = _make_ncpa_device(db_session, admin_user)
    deployment = NCPADeployment(NetworkDiscoveryID=device.NetDiscoveryID)
    db_session.session.add(deployment)
    db_session.session.commit()

    with app.app_context():
        assert deployed_ncpa_port(deployment) == int(app.config["NCPA_PORT"])
        deployment.Port = 5864
        db_session.session.commit()
        assert deployed_ncpa_port(deployment) == 5864


class TestCleanup:
    def test_requires_login_and_permission(self, client, limited_client, db_session):
        path = "/api/system/deployment/ncpa/1/cleanup"
        assert client.post(path, json={}).status_code in (401, 302, 403)
        assert limited_client.post(path, json={}).status_code == 403

    def test_refuses_untrusted_pending_and_running(self, logged_in_client, db_session, admin_user):
        from app.api.system import ncpa_deployment as routes
        device, creds = _make_ncpa_device(db_session, admin_user)
        deployment = NCPADeployment(NetworkDiscoveryID=device.NetDiscoveryID, Agent_Status=AgentStatus.FAILED)
        db_session.session.add(deployment)
        db_session.session.commit()
        path = f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/cleanup"
        body = {"username": "operator", "password": "private", "remove_account": True}
        with patch.object(routes, "get_host_key_fingerprint") as fingerprint, \
             patch.object(routes, "cleanup_ncpa_bootstrap") as cleanup:
            assert logged_in_client.post(path, json=body).status_code == 409
            creds.Key_Fingerprint = "abc:123"
            deployment.Agent_Status = AgentStatus.PENDING_NCPA
            db_session.session.commit()
            assert logged_in_client.post(path, json=body).status_code == 409
            deployment.Agent_Status = AgentStatus.FAILED
            db_session.session.commit()
            with patch.object(routes, "deploy_ncpa_thread") as thread:
                thread.is_alive.return_value = True
                assert logged_in_client.post(path, json=body).status_code == 409
            fingerprint.assert_not_called()
            cleanup.assert_not_called()

    def test_body_cannot_override_url_device_id(self, logged_in_client, db_session, admin_user):
        from app.api.system import ncpa_deployment as routes
        device, _ = _make_ncpa_device(db_session, admin_user, trusted=True)
        deployment = NCPADeployment(NetworkDiscoveryID=device.NetDiscoveryID, Agent_Status=AgentStatus.FAILED)
        db_session.session.add(deployment)
        db_session.session.commit()
        with patch.object(routes, "get_host_key_fingerprint", return_value="abc:123"), \
             patch.object(routes, "cleanup_ncpa_bootstrap", return_value=[{"step": "key", "ok": True}]) as cleanup:
            response = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/cleanup",
                                             json={"device_id": device.NetDiscoveryID + 1,
                                                   "username": "operator", "password": "private"})
        assert response.status_code == 200
        assert response.get_json()["data"]["device_id"] == device.NetDiscoveryID
        cleanup.assert_called_once()

    def test_changed_host_key_stops_before_cleanup(self, logged_in_client, db_session, admin_user):
        from app.api.system import ncpa_deployment as routes
        device, _ = _make_ncpa_device(db_session, admin_user, trusted=True)
        db_session.session.add(NCPADeployment(NetworkDiscoveryID=device.NetDiscoveryID, Agent_Status=AgentStatus.FAILED))
        db_session.session.commit()
        with patch.object(routes, "get_host_key_fingerprint", return_value="different"), \
             patch.object(routes, "cleanup_ncpa_bootstrap") as cleanup:
            response = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/cleanup",
                                             json={"username": "operator", "password": "private"})
        assert response.status_code == 409
        assert "private" not in response.get_data(as_text=True)
        cleanup.assert_not_called()

    @pytest.mark.parametrize("initial_status", [AgentStatus.FAILED, AgentStatus.DEPLOYED])
    def test_success_reports_steps_and_clears_status_without_exposing_credentials(
        self, logged_in_client, db_session, admin_user, caplog, initial_status
    ):
        from app.api.system import ncpa_deployment as routes
        device, creds = _make_ncpa_device(db_session, admin_user, trusted=True)
        creds.Key_Installed = True
        deployment = NCPADeployment(NetworkDiscoveryID=device.NetDiscoveryID, Agent_Status=initial_status,
                                    Error="Previous failure")
        db_session.session.add(deployment)
        db_session.session.commit()
        steps = [{"step": name, "ok": True} for name in ("key", "sudo_rule", "helper", "account")]
        with patch.object(routes, "get_host_key_fingerprint", return_value="abc:123"), \
             patch.object(routes, "cleanup_ncpa_bootstrap", return_value=steps) as cleanup:
            response = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/cleanup",
                                             json={"username": "operator", "password": "private",
                                                   "remove_account": True})
        assert response.status_code == 200
        assert response.get_json()["data"]["steps"] == steps
        assert response.get_json()["data"]["agent_status"] == AgentStatus.PENDING_NCPA.value
        assert deployment.Agent_Status is AgentStatus.PENDING_NCPA and deployment.Error is None
        assert creds.Key_Installed is False
        assert cleanup.call_args.args[-2:] == ("private", True)
        assert "private" not in response.get_data(as_text=True) + caplog.text
        assert "private" not in str(deployment.Error)

    def test_partial_failure_keeps_failed_status(self, logged_in_client, db_session, admin_user):
        from app.api.system import ncpa_deployment as routes
        device, _ = _make_ncpa_device(db_session, admin_user, trusted=True)
        deployment = NCPADeployment(NetworkDiscoveryID=device.NetDiscoveryID, Agent_Status=AgentStatus.FAILED)
        db_session.session.add(deployment)
        db_session.session.commit()
        steps = [{"step": "key", "ok": False}, {"step": "sudo_rule", "ok": True}]
        with patch.object(routes, "get_host_key_fingerprint", return_value="abc:123"), \
             patch.object(routes, "cleanup_ncpa_bootstrap", return_value=steps):
            response = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/cleanup",
                                             json={"username": "operator", "password": "private"})
        assert response.status_code == 200
        assert response.get_json()["data"]["steps"] == steps
        assert deployment.Agent_Status is AgentStatus.FAILED
        assert "private" not in deployment.Error


# ─── GET /api/system/deployment/ncpa/devices ──────────────────────────────────

class TestNcpaEligibleDevices:
    def test_ncpa_eligible_devices_requires_login(self, client, db_session):
        resp = client.get("/api/system/deployment/ncpa/devices")
        assert resp.status_code in (401, 302)

    def test_ncpa_eligible_devices_empty(self, logged_in_client, db_session, admin_user):
        # No devices seeded — should return an empty list
        resp = logged_in_client.get("/api/system/deployment/ncpa/devices")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["devices"] == []

    def test_ncpa_eligible_devices_returns_eligible(self, logged_in_client, db_session, admin_user):
        eligible, _ = _make_ncpa_device(db_session, admin_user, ncpa_eligible=True)
        non_eligible, _ = _make_ncpa_device(db_session, admin_user, ncpa_eligible=False)

        resp = logged_in_client.get("/api/system/deployment/ncpa/devices")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        device_ids = [d["device_id"] for d in data["devices"]]
        assert eligible.NetDiscoveryID in device_ids
        assert non_eligible.NetDiscoveryID not in device_ids

    def test_ncpa_eligible_devices_requires_permission(self, limited_client, db_session, admin_user):
        resp = limited_client.get("/api/system/deployment/ncpa/devices")
        assert resp.status_code == 403


# ─── GET /api/system/deployment/ncpa/<device_id>/fingerprint ─────────────────

class TestGetFingerprint:
    def test_get_fingerprint_device_not_found(self, logged_in_client, db_session, admin_user):
        resp = logged_in_client.get("/api/system/deployment/ncpa/99999/fingerprint")
        assert resp.status_code == 404

    def test_get_fingerprint_unreachable_device(self, logged_in_client, db_session, admin_user):
        device, _ = _make_ncpa_device(db_session, admin_user)

        with patch("app.api.system.ncpa_deployment.get_host_key_fingerprint") as mock_fp:
            mock_fp.side_effect = Exception("Connection refused")
            resp = logged_in_client.get(
                f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/fingerprint"
            )
        assert resp.status_code == 502


# ─── POST /api/system/deployment/ncpa/<device_id>/confirm-trust ───────────────

class TestConfirmTrust:
    def test_confirm_trust_device_not_found(self, logged_in_client, db_session, admin_user):
        with patch("app.api.system.ncpa_deployment.get_host_key_fingerprint") as mock_fp:
            mock_fp.return_value = "fp:123"
            resp = logged_in_client.post(
                "/api/system/deployment/ncpa/99999/confirm-trust",
                json={"fingerprint": "fp:123"},
            )
        assert resp.status_code == 404

    def test_confirm_trust_no_ssh_creds(self, logged_in_client, db_session, admin_user):
        """Device exists but has no SSHCredentials row — should return 404."""
        log = ActivityLog(Action_Type="test", UserID=admin_user.UserID)
        db_session.session.add(log)
        db_session.session.flush()

        ds = NetworkDiscoveryStatus(
            Status=DiscoveryStatus.SUCCESS,
            Progress=100,
            Message="Done",
            LogID=log.LogID,
        )
        db_session.session.add(ds)
        db_session.session.flush()

        device = NetworkDiscovery(
            Hostname="no-creds-host",
            IP_Address="10.99.0.2",
            Network="10.99.0.0",
            NCPA_Eligible=True,
            DiscoveryStatusID=ds.DiscoveryStatusID,
        )
        db_session.session.add(device)
        db_session.session.commit()

        with patch("app.api.system.ncpa_deployment.get_host_key_fingerprint") as mock_fp:
            mock_fp.return_value = "fp:123"
            resp = logged_in_client.post(
                f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/confirm-trust",
                json={"fingerprint": "fp:123"},
            )
        assert resp.status_code == 404

    def test_confirm_trust_success(self, logged_in_client, db_session, admin_user):
        device, creds = _make_ncpa_device(db_session, admin_user, trusted=False)
        assert creds.Key_Fingerprint is None

        with patch("app.api.system.ncpa_deployment.get_host_key_fingerprint") as mock_fp:
            mock_fp.return_value = "fp:123"
            resp = logged_in_client.post(
                f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/confirm-trust",
                json={"fingerprint": "fp:123"},
            )

        assert resp.status_code == 200
        db_session.session.refresh(creds)
        assert creds.Key_Fingerprint == "fp:123"


# ─── POST /api/system/deployment/ncpa/start ───────────────────────────────────

class TestDeployNcpaStart:
    def test_deploy_ncpa_requires_login(self, client, db_session):
        resp = client.post(
            "/api/system/deployment/ncpa/start",
            json={"devices": []},
        )
        assert resp.status_code in (401, 302)

    def test_deploy_ncpa_no_devices_provided(self, logged_in_client, db_session, admin_user):
        resp = logged_in_client.post(
            "/api/system/deployment/ncpa/start",
            json={"devices": []},
        )
        assert resp.status_code == 400

    def test_deploy_ncpa_already_running(self, logged_in_client, db_session, admin_user):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        with patch("app.api.system.ncpa_deployment.deploy_ncpa_thread", mock_thread):
            resp = logged_in_client.post(
                "/api/system/deployment/ncpa/start",
                json={"devices": [{"device_id": 1, "username": "u", "password": "p"}]},
            )
        assert resp.status_code == 400

    def test_deploy_ncpa_device_not_found_rejected(self, logged_in_client, db_session, admin_user):
        """Device 99999 doesn't exist — it is rejected, and with nothing left to deploy the response is 400."""
        with patch("app.api.system.ncpa_deployment.deploy_ncpa_thread", None), \
             patch("app.api.system.ncpa_deployment.threading.Thread") as mock_thread_cls:
            mock_thread_instance = MagicMock()
            mock_thread_cls.return_value = mock_thread_instance

            resp = logged_in_client.post(
                "/api/system/deployment/ncpa/start",
                json={"devices": [{"device_id": 99999, "username": "u", "password": "p"}]},
            )

        assert resp.status_code == 400
        mock_thread_cls.assert_not_called()
        data = resp.get_json()["data"]
        assert len(data["rejected"]) > 0
        rejected_ids = [r["device_id"] for r in data["rejected"]]
        assert 99999 in rejected_ids

    def test_deploy_ncpa_untrusted_device_rejected(self, logged_in_client, db_session, admin_user):
        """Device exists but has no Key_Fingerprint (not trust-confirmed) — rejected, so nothing starts."""
        device, creds = _make_ncpa_device(db_session, admin_user, trusted=False)
        assert creds.Key_Fingerprint is None

        with patch("app.api.system.ncpa_deployment.deploy_ncpa_thread", None), \
             patch("app.api.system.ncpa_deployment.threading.Thread") as mock_thread_cls:
            mock_thread_instance = MagicMock()
            mock_thread_cls.return_value = mock_thread_instance

            resp = logged_in_client.post(
                "/api/system/deployment/ncpa/start",
                json={"devices": [
                    {"device_id": device.NetDiscoveryID, "username": "u", "password": "p"}
                ]},
            )

        assert resp.status_code == 400
        mock_thread_cls.assert_not_called()
        data = resp.get_json()["data"]
        assert len(data["rejected"]) > 0
        rejected_ids = [r["device_id"] for r in data["rejected"]]
        assert device.NetDiscoveryID in rejected_ids


# ─── POST /api/system/deployment/ncpa/stop ────────────────────────────────────

class TestDeployNcpaStop:
    def test_stop_ncpa_not_running(self, logged_in_client, db_session, admin_user):
        """Stopping when no deployment is running should return 400."""
        with patch("app.api.system.ncpa_deployment.deploy_ncpa_thread", None):
            resp = logged_in_client.post("/api/system/deployment/ncpa/stop")
        assert resp.status_code == 400


# ─── GET /api/system/deployment/ncpa/status ───────────────────────────────────

class TestDeployNcpaStatus:
    def test_ncpa_status_no_records(self, logged_in_client, db_session, admin_user):
        """When no deployment has occurred, should return 200 with a message."""
        resp = logged_in_client.get("/api/system/deployment/ncpa/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "message" in data


# ─── GET /api/system/deployment/ncpa/devices/trusted ─────────────────────────

class TestTrustedDevices:
    def test_trusted_devices_empty(self, logged_in_client, db_session, admin_user):
        """When no devices are trusted (no NCPADeployment rows with PENDING_NCPA), return empty list."""
        resp = logged_in_client.get("/api/system/deployment/ncpa/devices/trusted")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["devices"] == []


# ─── POST /api/system/deployment/ncpa/<device_id>/refresh-disks ───────────────

class TestRefreshDisks:
    def deploy(self, db_session, device):
        db_session.session.add(NCPADeployment(
            NetworkDiscoveryID=device.NetDiscoveryID, Token="t" * 32, Agent_Status=AgentStatus.DEPLOYED))
        db_session.session.commit()

    def test_not_deployed_is_404(self, logged_in_client, db_session, admin_user):
        device, _ = _make_ncpa_device(db_session, admin_user)
        resp = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/refresh-disks")
        assert resp.status_code == 404

    def test_requires_permission(self, limited_client, db_session, admin_user):
        resp = limited_client.post("/api/system/deployment/ncpa/1/refresh-disks")
        assert resp.status_code == 403

    def test_stores_disks_and_regenerates(self, logged_in_client, db_session, admin_user):
        device, _ = _make_ncpa_device(db_session, admin_user)
        self.deploy(db_session, device)
        with patch("app.api.system.ncpa_deployment.refresh_ncpa_partitions", return_value=["|", "|boot|efi"]),              patch("app.api.plugin.reconcile.reconcile_plugin_monitoring", return_value={"success": True, "changed": True, "message": "ok"}):
            resp = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/refresh-disks")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["disks"] == ["|", "|boot|efi"] and data["config_applied"] is True

    def test_no_disks_is_502(self, logged_in_client, db_session, admin_user):
        device, _ = _make_ncpa_device(db_session, admin_user)
        self.deploy(db_session, device)
        with patch("app.api.system.ncpa_deployment.refresh_ncpa_partitions", return_value=[]):
            resp = logged_in_client.post(f"/api/system/deployment/ncpa/{device.NetDiscoveryID}/refresh-disks")
        assert resp.status_code == 502
