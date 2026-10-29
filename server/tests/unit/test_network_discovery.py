"""
tests/unit/test_network_discovery.py — Tests for the network-discovery endpoints.

Endpoints tested:
  POST /api/system/discover/start
  POST /api/system/network-discovery/stop
  GET  /api/system/discover/status
"""
import pytest
import xml.etree.ElementTree as ET
from threading import Event, Thread
from unittest.mock import patch, MagicMock

from app import db
from app.network_discovery import network_discovery
from app.network_discovery.create_host_cfg import _save_discovered_hosts
from app.system_models import DiscoverySettings, NetworkDiscovery, Open_TCP_Services
from tests.support.identity_helpers import NET, MAC_1, MAC_2, make_status, scan, combine

from app.system_models import (
    NetworkDiscoveryStatus,
    DiscoveryStatus,
    ActivityLog,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_activity_log(db_session, admin_user):
    log = ActivityLog(Action_Type="test", UserID=admin_user.UserID)
    db_session.session.add(log)
    db_session.session.flush()
    return log


def _seed_discovery_status(db_session, admin_user, status=DiscoveryStatus.SUCCESS):
    log = _make_activity_log(db_session, admin_user)
    ds = NetworkDiscoveryStatus(
        Status=status,
        Progress=100,
        Message="Done",
        LogID=log.LogID,
    )
    db_session.session.add(ds)
    db_session.session.commit()
    return ds


# ─── /discover/start ─────────────────────────────────────────────────────────

class TestDiscoverStart:
    def test_discover_start_requires_login(self, client, db_session):
        resp = client.post("/api/system/discover/start")
        assert resp.status_code in (401, 302)

    def test_discover_start_success(self, logged_in_client, db_session, admin_user):
        """
        Mock the thread so no real network scan runs.
        Expects 202 with a "started" message.
        """
        with patch(
            "app.api.system.network_discovery.threading.Thread"
        ) as mock_thread_cls:
            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = False
            mock_thread_cls.return_value = mock_thread

            # Also patch discover_network_create_hosts to be a no-op
            with patch(
                "app.api.system.network_discovery.discover_network_create_hosts"
            ):
                # Reset the module-level discovery_thread to None
                import app.api.system.network_discovery as nd_module
                nd_module.discovery_thread = None

                resp = logged_in_client.post("/api/system/discover/start")

        assert resp.status_code == 202
        data = resp.get_json()
        assert "message" in data

    def test_focused_start_passes_only_normalized_ipv4_to_worker(self, logged_in_client, db_session):
        import app.api.system.network_discovery as nd_module
        nd_module.discovery_thread = None
        with patch.object(nd_module.threading, "Thread") as worker_cls:
            response = logged_in_client.post("/api/system/discover/start", json={"target": " 10.0.0.4 "})
        assert response.status_code == 202
        assert worker_cls.call_args.kwargs["args"][-1] == "10.0.0.4"

    @pytest.mark.parametrize("target", [
        "", "host.local", "10.0.0.0/24", "10.0.0.4/32", "127.0.0.1",
        "224.0.0.1", "0.0.0.0", "240.0.0.1", "::1", "10.0.0.4 -sV",
        ["10.0.0.4"], None,
    ])
    def test_invalid_focused_target_never_starts_worker(self, logged_in_client, db_session, target):
        import app.api.system.network_discovery as nd_module
        nd_module.discovery_thread = None
        with patch.object(nd_module.threading, "Thread") as worker_cls:
            response = logged_in_client.post("/api/system/discover/start", json={"target": target})
        assert response.status_code == 400
        worker_cls.assert_not_called()

    def test_focused_start_requires_permission(self, limited_client, db_session):
        response = limited_client.post("/api/system/discover/start", json={"target": "10.0.0.4"})
        assert response.status_code == 403

    def test_focused_stop_then_retry_uses_same_shared_worker_lock(self, logged_in_client, db_session):
        import app.api.system.network_discovery as nd_module
        nd_module.discovery_thread = None
        nd_module.discovery_thread_stop_event.clear()
        with patch.object(nd_module.threading, "Thread") as worker_cls:
            first_worker = worker_cls.return_value
            first_worker.is_alive.return_value = True
            assert logged_in_client.post("/api/system/discover/start", json={"target": "10.0.0.4"}).status_code == 202
            assert logged_in_client.post("/api/system/discover/start", json={"target": "10.0.0.5"}).status_code == 400
            assert logged_in_client.post("/api/system/network-discovery/stop").status_code == 200
            assert nd_module.discovery_thread_stop_event.is_set()
            first_worker.is_alive.return_value = False
            assert logged_in_client.post("/api/system/discover/start", json={"target": "10.0.0.4"}).status_code == 202
            assert not nd_module.discovery_thread_stop_event.is_set()
            assert worker_cls.call_count == 2
        nd_module.discovery_thread = None

    def test_simultaneous_starts_reserve_one_scan(self, app):
        """Two requests that both see an idle worker must not launch two scans."""
        import app.api.system.network_discovery as nd_module

        entered = Event()
        release = Event()
        results = []
        old_thread = nd_module.discovery_thread
        existing = MagicMock()

        def check_idle():
            entered.set()
            assert release.wait(timeout=5)
            return False

        existing.is_alive.side_effect = check_idle
        nd_module.discovery_thread = existing

        def start():
            with app.app_context():
                results.append(nd_module.start_discovery_thread(1))

        try:
            with patch.object(nd_module.threading, "Thread") as worker_cls:
                worker_cls.return_value.is_alive.return_value = True
                workers = [Thread(target=start) for _ in range(2)]
                workers[0].start()
                assert entered.wait(timeout=5)
                workers[1].start()
                release.set()
                for worker in workers:
                    worker.join(timeout=5)
                assert all(not worker.is_alive() for worker in workers)
                assert sorted(results) == [False, True]
                assert worker_cls.call_count == 1
        finally:
            release.set()
            nd_module.discovery_thread = old_thread

    def test_discover_start_already_running(self, logged_in_client, db_session):
        """When discovery_thread.is_alive() is True, expect 400."""
        import app.api.system.network_discovery as nd_module

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        nd_module.discovery_thread = mock_thread

        try:
            resp = logged_in_client.post("/api/system/discover/start")
            assert resp.status_code == 400
            data = resp.get_json()
            assert "message" in data
        finally:
            # Clean up so other tests start fresh
            nd_module.discovery_thread = None


# ─── /network-discovery/stop ──────────────────────────────────────────────────

class TestDiscoverStop:
    def test_discover_stop_not_running(self, logged_in_client, db_session):
        """When there is no running discovery, stop should return 400."""
        import app.api.system.network_discovery as nd_module
        nd_module.discovery_thread = None  # ensure not running

        resp = logged_in_client.post("/api/system/network-discovery/stop")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "message" in data

    def test_discover_stop_running_sets_event(self, logged_in_client, db_session):
        """A running scan gets its stop event set and the route returns 200."""
        import app.api.system.network_discovery as nd_module
        fake_thread = MagicMock()
        fake_thread.is_alive.return_value = True
        nd_module.discovery_thread = fake_thread
        nd_module.discovery_thread_stop_event.clear()

        try:
            resp = logged_in_client.post("/api/system/network-discovery/stop")
            assert resp.status_code == 200
            assert nd_module.discovery_thread_stop_event.is_set()
        finally:
            nd_module.discovery_thread = None
            nd_module.discovery_thread_stop_event.clear()


# ─── cancelled scans ─────────────────────────────────────────────────────────

class TestDiscoveryCancelled:
    def test_mark_interrupted_keeps_progress(self, db_session, admin_user):
        """A cancelled run leaves "Running" and keeps the progress it reached."""
        from app.network_discovery.create_host_cfg import mark_discovery_interrupted
        ds = _seed_discovery_status(db_session, admin_user, status=DiscoveryStatus.RUNNING)
        ds.Progress = 40
        db_session.session.commit()

        mark_discovery_interrupted(ds.DiscoveryStatusID)

        refreshed = db_session.session.get(NetworkDiscoveryStatus, ds.DiscoveryStatusID)
        assert refreshed.Status == DiscoveryStatus.INTERRUPTED
        assert refreshed.Progress == 40
        assert refreshed.Completed_At is not None

    def test_stop_before_scan_marks_interrupted(self, app, db_session, admin_user):
        """Stopping before nmap runs records the run as Interrupted, not Running."""
        import threading
        from app.network_discovery import create_host_cfg
        stop_event = threading.Event()
        stop_event.set()

        with patch.object(create_host_cfg, "discover_network") as fake_discover:
            create_host_cfg.discover_network_create_hosts(app, admin_user.UserID, stop_event)
            fake_discover.assert_not_called()

        latest = db_session.session.scalars(
            db_session.select(NetworkDiscoveryStatus)
            .order_by(NetworkDiscoveryStatus.DiscoveryStatusID.desc())
        ).first()
        assert latest.Status == DiscoveryStatus.INTERRUPTED


def test_focused_scan_probes_only_requested_host_and_keeps_saved_networks(db_session, admin_user):
    status = make_status(db_session, admin_user)
    db.session.add(DiscoverySettings(Id=1, Networks=[NET], TCP_Ports=[22], UDP_Ports=[161]))
    db.session.commit()
    with patch.object(network_discovery, "_discover_host", return_value={
        "10.0.0.4": {"data": {"hostname": "one"}, "services": {}},
        "10.0.0.5": {"data": {"hostname": "other"}, "services": {}},
    }) as host_scan, patch.object(network_discovery, "_discover_host_tcp_port", return_value=({}, "Linux")) as tcp, \
         patch.object(network_discovery, "_discover_host_udp_port", return_value=({}, {})) as udp:
        found = network_discovery.discover_network(status, 40, Event(), target="10.0.0.4")
    host_scan.assert_called_once_with("10.0.0.4")
    tcp.assert_called_once_with("10.0.0.4")
    udp.assert_called_once_with("10.0.0.4")
    assert list(found[NET]) == ["10.0.0.4"]
    assert db.session.get(DiscoverySettings, 1).Networks == [NET]


def test_focused_save_preserves_other_device_and_ports(db_session, admin_user):
    status = make_status(db_session, admin_user)
    with patch("app.network_discovery.create_host_cfg.get_monitoring_server_ips", return_value=set()):
        _save_discovered_hosts(combine(
            scan("10.0.0.4", mac=MAC_1, tcp={22: "ssh"}),
            scan("10.0.0.5", mac=MAC_2, tcp={80: "http"}),
        ), status, 70)
        other = db.session.query(NetworkDiscovery).filter_by(IP_Address="10.0.0.5").one()
        other_id, other_misses = other.NetDiscoveryID, other.Missed_Scans
        other_port = db.session.query(Open_TCP_Services).filter_by(NetDiscoveryID=other_id).one()
        other_port_misses = other_port.Missed_Scans
        _save_discovered_hosts(scan("10.0.0.4", mac=MAC_1, tcp={443: "https"}), status, 70,
                               target="10.0.0.4")
    assert other.Device_State.name == "ACTIVE"
    assert other.Missed_Scans == other_misses
    assert other_port.Missed_Scans == other_port_misses
    target_device = db.session.query(NetworkDiscovery).filter_by(IP_Address="10.0.0.4").one()
    assert {port.Port_Number for port in db.session.query(Open_TCP_Services).filter_by(NetDiscoveryID=target_device.NetDiscoveryID)} == {22, 443}


def test_focused_unreachable_target_skips_save_and_config(app, db_session, admin_user):
    from app.network_discovery import create_host_cfg
    with patch.object(create_host_cfg, "discover_network", return_value={NET: {}}), \
         patch.object(create_host_cfg, "_save_discovered_hosts") as save, \
         patch.object(create_host_cfg, "_create_host_cfg_file") as config:
        create_host_cfg.discover_network_create_hosts(app, admin_user.UserID, Event(), "10.0.0.4")
    save.assert_not_called()
    config.assert_not_called()
    status = db.session.query(NetworkDiscoveryStatus).order_by(NetworkDiscoveryStatus.DiscoveryStatusID.desc()).first()
    assert status.Status == DiscoveryStatus.FAILED
    assert "10.0.0.4" in status.Message


def test_new_focused_device_outside_saved_network_keeps_later_full_scan_scope(db_session, admin_user):
    status = make_status(db_session, admin_user)
    db.session.add(DiscoverySettings(Id=1, Networks=[NET]))
    db.session.commit()
    host = {"data": {"hostname": "external", "mac_address": MAC_1, "os": "Linux"}, "services": {}}
    with patch.object(network_discovery, "_discover_host", side_effect=lambda address: {"10.2.0.4": host} if address == "10.2.0.4" else {}), \
         patch.object(network_discovery, "_discover_host_tcp_port", return_value=({}, "Linux")), \
         patch.object(network_discovery, "_discover_host_udp_port", return_value=({}, {})), \
         patch("app.network_discovery.create_host_cfg.get_monitoring_server_ips", return_value=set()):
        focused = network_discovery.discover_network(status, 40, Event(), "10.2.0.4")
        assert list(focused) == ["10.2.0.4/32"]
        _save_discovered_hosts(focused, status, 70, target="10.2.0.4")
        device = db.session.query(NetworkDiscovery).filter_by(IP_Address="10.2.0.4").one()
        full = network_discovery.discover_network(status, 40, Event())
        _save_discovered_hosts(full, status, 70)
    assert device.Device_State.name == "ACTIVE"
    assert device.Missed_Scans == 0
    assert db.session.get(DiscoverySettings, 1).Networks == [NET]


# ─── repeat scans with changed port settings ─────────────────────────────────

@pytest.mark.parametrize("extra_ports", ([8080, 2222], ["8000-8099", "2200-2299"]))
def test_known_devices_record_newly_scanned_tcp_ports(app, db_session, admin_user, logged_in_client, extra_ports):
    """A rescan must persist newly requested ports on the original device rows."""
    status = _seed_discovery_status(db_session, admin_user)
    db_session.session.add(DiscoverySettings(Id=1, TCP_Ports=["1-1024"]))
    db_session.session.commit()

    hosts = {
        "10.0.0.4": ("app01", "00:11:22:33:44:04", 8080, "http"),
        "10.0.0.6": ("legacy01", MAC_1, 2222, "ssh"),
    }
    # Simulate nmap's XML, but only return a port when the command requests it.
    # This makes argument construction part of the regression, not just the DB upsert.
    def scan_command(ip, flags, args=None):
        if "-sn" in flags:
            return ET.fromstring("<nmaprun><host><status state='up'/><address addrtype='ipv4' addr='" + ip + "'/></host></nmaprun>")
        if "-sU" in flags:
            return ET.fromstring("<nmaprun/>")
        name, mac, port, service = hosts[ip]
        requested = args.split("-p ", 1)[1].split()
        requested = requested[0].split(",")
        if not any(str(port) == entry or ("-" in entry and int(entry.split("-")[0]) <= port <= int(entry.split("-")[1])) for entry in requested):
            return ET.fromstring("<nmaprun><host><ports/></host></nmaprun>")
        return ET.fromstring(f"<nmaprun><host><ports><port protocol='tcp' portid='{port}'><state state='open'/><service name='{service}' method='probed'/></port></ports></host></nmaprun>")

    def discover_host(network):
        return {ip: {"data": {"hostname": name, "mac_address": mac, "os": "Linux"}, "services": {}}
                for ip, (name, mac, _, _) in hosts.items()}

    with patch.object(network_discovery, "_discover_host", side_effect=discover_host), \
         patch.object(network_discovery.nmap3, "Nmap") as nmap_cls, \
         patch("app.network_discovery.create_host_cfg.get_monitoring_server_ips", return_value=set()), \
         patch("app.network_discovery.create_host_cfg.update_network_discovery_status"):
        nmap_cls.return_value.scan_command.side_effect = scan_command
        first = network_discovery.discover_network(status.DiscoveryStatusID, 40, Event())
        _save_discovered_hosts(first, status.DiscoveryStatusID, 70)
        original = {device.Hostname: device.NetDiscoveryID for device in db.session.query(NetworkDiscovery).all()}
        assert len(original) == 2
        assert db.session.query(Open_TCP_Services).count() == 0

        settings = db.session.get(DiscoverySettings, 1)
        settings.TCP_Ports = ["1-1024", *extra_ports]
        db.session.commit()
        second = network_discovery.discover_network(status.DiscoveryStatusID, 40, Event())
        _save_discovered_hosts(second, status.DiscoveryStatusID, 70)

    assert {device.Hostname: device.NetDiscoveryID for device in db.session.query(NetworkDiscovery).all()} == original
    for name, _, port, service in hosts.values():
        device_id = original[name]
        response = logged_in_client.get(f"/api/system/hosts/{device_id}/ports")
        assert response.status_code == 200
        assert any(item["protocol"] == "tcp" and item["number"] == port
                   and item["service_name"] == service for item in response.get_json()["data"]["ports"])


# ─── /discover/status ────────────────────────────────────────────────────────

class TestDiscoverStatus:
    def test_discover_status_no_records(self, logged_in_client, db_session):
        """When no discovery has run yet, return 200 with an informational message."""
        resp = logged_in_client.get("/api/system/discover/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "message" in data
