"""
tests/unit/test_network_health_bandwidth.py — The Network Health bandwidth routes in
app/api/system/network_health_activity.py:

  GET /api/system/network-health/bandwidth/interfaces
  GET /api/system/network-health/bandwidth

Counter samples are seeded as the Nagios services' stored check results, so the whole path from
history.db rows to bit/s is exercised. Window validation, the 404/insufficient-data states and
utilisation are covered here; the arithmetic itself is in test_bandwidth.py.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app import db
from app.network_discovery.device_identity import nagios_host_name
from app.system_models import DeviceInterface
from tests.support.seed_helpers import _make_service, _make_service_perf
from tests.unit.test_interface_discovery import snmp_device

BASE = "/api/system/network-health/bandwidth"
IN_SERVICE = "snmp-if2_in_octets-161-udp"
OUT_SERVICE = "snmp-if2_out_octets-161-udp"


def seed_counter(service, hostname, readings, now=None, check_lag=0):
    """
    Store (minutes ago, octets) readings as check results of a service. check_lag is how many
    seconds before the stored time Nagios actually read the counter (Last_Check).
    """
    now = now or datetime.now(timezone.utc)
    for minutes_ago, octets in readings:
        status = _make_service(db, hostname=hostname, service=service, ts=now - timedelta(minutes=minutes_ago))
        status.Last_Check = status.Timestamp - timedelta(seconds=check_lag)
        _make_service_perf(db, status, "if2", octets, "c")
    db.session.commit()


def traffic(hostname="switch", in_rate=1_000_000, out_rate=250_000):
    """One hour of five-minute readings: in_rate / out_rate are bit/s."""
    minutes = [60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5]
    for service, rate in ((IN_SERVICE, in_rate), (OUT_SERVICE, out_rate)):
        seed_counter(service, hostname, [(m, int((60 - m) * 60 * rate / 8)) for m in minutes])


class TestGuards:

    URLS = [f"{BASE}?hostname=switch&interface=2", f"{BASE}/interfaces"]

    @pytest.mark.parametrize("url", URLS)
    def test_requires_login(self, client, db_session, url):
        assert client.get(url).status_code in (401, 302)

    @pytest.mark.parametrize("url", URLS)
    def test_requires_permission(self, limited_client, db_session, url):
        assert limited_client.get(url).status_code == 403


class TestValidation:

    @pytest.mark.parametrize("hours", ["0.0833", "2", "12", "48", "169", "0", "-1", "abc"])
    def test_only_the_allowed_windows(self, logged_in_client, db_session, hours):
        resp = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours={hours}")
        assert resp.status_code == 400

    def test_the_5_minute_window_is_refused(self, logged_in_client, db_session):
        resp = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours={5 / 60}")
        assert resp.status_code == 400 and "hours must be one of" in resp.get_json()["message"]

    @pytest.mark.parametrize("hours", [1, 6, 24, 168])
    def test_allowed_windows_pass_validation(self, logged_in_client, db_session, hours):
        # No such service: a 404, not a 400, proves the window was accepted.
        assert logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours={hours}").status_code == 404

    @pytest.mark.parametrize("query", [
        "interface=2", "hostname=&interface=2", "hostname=switch", "hostname=switch&interface=abc",
        "hostname=switch&interface=0", "hostname=switch&interface=-3",
        "hostname=switch&interface=2&buckets=0", "hostname=switch&interface=2&buckets=169",
    ])
    def test_bad_parameters(self, logged_in_client, db_session, query):
        assert logged_in_client.get(f"{BASE}?{query}").status_code == 400

    def test_an_interface_that_is_not_monitored(self, logged_in_client, db_session):
        resp = logged_in_client.get(f"{BASE}?hostname=switch&interface=2")
        assert resp.status_code == 404 and "not monitored" in resp.get_json()["message"]


class TestRates:

    def test_in_and_out_rates(self, logged_in_client, db_session):
        traffic(in_rate=1_000_000, out_rate=250_000)

        data = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1&buckets=12").get_json()["data"]

        assert data["status"] == "ok" and data["hours"] == 1 and data["hostname"] == "switch"
        assert data["interface"] == {"if_index": 2, "name": None, "speed_bps": None}
        assert len(data["in_points"]) == len(data["out_points"]) == 12
        in_values = [p["bps"] for p in data["in_points"] if p["bps"] is not None]
        out_values = [p["bps"] for p in data["out_points"] if p["bps"] is not None]
        assert in_values and out_values
        assert all(v == pytest.approx(1_000_000, rel=0.01) for v in in_values)
        assert all(v == pytest.approx(250_000, rel=0.01) for v in out_values)
        assert data["latest"]["in_bps"] == pytest.approx(1_000_000, rel=0.01)
        assert data["latest"]["out_bps"] == pytest.approx(250_000, rel=0.01)
        assert data["latest"]["in_utilisation_pct"] is None      # speed unknown

    def test_utilisation_when_the_speed_is_known(self, logged_in_client, db_session, admin_user):
        device = snmp_device(db_session, admin_user, "switch", "10.0.0.9")
        db_session.session.add(DeviceInterface(
            NetDiscoveryID=device.NetDiscoveryID, If_Index=2, Name="eth0", Speed_Bps=10_000_000, Monitored=True,
        ))
        db_session.session.commit()
        traffic(hostname=nagios_host_name(device), in_rate=2_500_000, out_rate=1_000_000)

        data = logged_in_client.get(
            f"{BASE}?hostname={nagios_host_name(device)}&interface=2&hours=1"
        ).get_json()["data"]

        assert data["interface"] == {"if_index": 2, "name": "eth0", "speed_bps": 10_000_000}
        assert data["latest"]["in_utilisation_pct"] == pytest.approx(25, rel=0.01)
        assert data["latest"]["out_utilisation_pct"] == pytest.approx(10, rel=0.01)

    def test_a_counter_reset_is_not_charted_as_traffic(self, logged_in_client, db_session):
        seed_counter(IN_SERVICE, "switch", [(30, 5_000_000_000), (25, 100), (20, 62_600), (15, 125_100)])
        seed_counter(OUT_SERVICE, "switch", [(30, 1000), (25, 2000), (20, 3000), (15, 4000)])

        data = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1&buckets=12").get_json()["data"]

        values = [p["bps"] for p in data["in_points"] if p["bps"] is not None]
        assert values and all(0 <= v < 10_000_000 for v in values)

    def test_the_default_interface_uses_the_lan_services(self, logged_in_client, db_session):
        seed_counter("snmp-lan_in_octets-161-udp", "router", [(10, 0), (5, 375_000)])
        seed_counter("snmp-lan_out_octets-161-udp", "router", [(10, 0), (5, 75_000)])

        data = logged_in_client.get(f"{BASE}?hostname=router&interface=3&hours=1").get_json()["data"]

        assert data["status"] == "ok"
        assert data["latest"]["in_bps"] == pytest.approx(10_000, rel=0.01)
        assert data["latest"]["out_bps"] == pytest.approx(2_000, rel=0.01)

    def test_other_interfaces_do_not_fall_back_to_the_lan_services(self, logged_in_client, db_session):
        seed_counter("snmp-lan_in_octets-161-udp", "router", [(10, 0), (5, 375_000)])
        assert logged_in_client.get(f"{BASE}?hostname=router&interface=4&hours=1").status_code == 404

    def test_samples_outside_the_window_are_ignored(self, logged_in_client, db_session):
        seed_counter(IN_SERVICE, "switch", [(300, 0), (299, 1_000_000)])     # 5 hours ago
        seed_counter(OUT_SERVICE, "switch", [(300, 0), (299, 1_000_000)])

        data = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1").get_json()["data"]

        assert data["status"] == "insufficient_data" and data["latest"] is None


class TestSampleTime:

    def test_rates_use_the_time_nagios_read_the_counter_not_the_time_it_was_stored(self, logged_in_client, db_session):
        # Stored every 60 s, but the counter was read every 50 s (lab: Pinpoint polls Nagios every
        # minute, Nagios checks every 50 s). 5,625,000 octets per 50 s is exactly 900 kbit/s;
        # dividing by the 60 s storage gap would give 750 kbit/s.
        now = datetime.now(timezone.utc)
        for service in (IN_SERVICE, OUT_SERVICE):
            for step in range(5):
                status = _make_service(db, hostname="switch", service=service, ts=now - timedelta(minutes=5 - step))
                status.Last_Check = now - timedelta(seconds=(5 - step) * 50 + 100)
                _make_service_perf(db, status, "if2", step * 5_625_000, "c")
        db.session.commit()

        data = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1").get_json()["data"]

        assert data["latest"]["in_bps"] == pytest.approx(900_000, rel=0.001)
        assert data["latest"]["out_bps"] == pytest.approx(900_000, rel=0.001)


class TestInsufficientData:

    def test_a_single_sample_is_insufficient_not_an_error(self, logged_in_client, db_session):
        seed_counter(IN_SERVICE, "switch", [(5, 1000)])
        seed_counter(OUT_SERVICE, "switch", [(5, 1000)])

        resp = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1")

        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "insufficient_data" and data["latest"] is None
        assert all(p["bps"] is None for p in data["in_points"] + data["out_points"])

    def test_one_direction_with_data_is_still_shown(self, logged_in_client, db_session):
        seed_counter(IN_SERVICE, "switch", [(10, 0), (5, 375_000)])
        seed_counter(OUT_SERVICE, "switch", [(5, 1000)])

        data = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1").get_json()["data"]

        assert data["status"] == "ok"
        assert data["latest"]["in_bps"] == pytest.approx(10_000, rel=0.01)
        assert data["latest"]["out_bps"] is None

    def test_a_service_with_results_but_no_perfdata(self, logged_in_client, db_session):
        _make_service(db, hostname="switch", service=IN_SERVICE)
        _make_service(db, hostname="switch", service=OUT_SERVICE)
        db.session.commit()

        data = logged_in_client.get(f"{BASE}?hostname=switch&interface=2&hours=1").get_json()["data"]
        assert data["status"] == "insufficient_data"


class TestInterfaceChoices:

    def test_no_snmp_device(self, logged_in_client, db_session):
        assert logged_in_client.get(f"{BASE}/interfaces").get_json()["data"] == {"devices": []}

    def test_device_with_and_without_monitored_interfaces(self, logged_in_client, db_session, admin_user):
        busy = snmp_device(db_session, admin_user, "busy", "10.0.0.31")
        idle = snmp_device(db_session, admin_user, "idle", "10.0.0.32")
        for if_index, name, monitored in ((2, "eth0", True), (3, "eth1", False), (4, "eth2", True)):
            db_session.session.add(DeviceInterface(
                NetDiscoveryID=busy.NetDiscoveryID, If_Index=if_index, Name=name, Speed_Bps=1_000_000_000,
                Monitored=monitored,
            ))
        db_session.session.commit()

        devices = logged_in_client.get(f"{BASE}/interfaces").get_json()["data"]["devices"]

        assert devices == [
            {"hostname": nagios_host_name(busy), "interfaces": [
                {"if_index": 2, "name": "eth0", "speed_bps": 1_000_000_000},
                {"if_index": 4, "name": "eth2", "speed_bps": 1_000_000_000},
            ]},
            {"hostname": nagios_host_name(idle), "interfaces": []},
        ]

    def test_the_default_interface_is_offered_when_its_service_exists(self, logged_in_client, db_session, admin_user):
        device = snmp_device(db_session, admin_user, "router", "10.0.0.33")
        seed_counter("snmp-lan_in_octets-161-udp", nagios_host_name(device), [(5, 1)])

        devices = logged_in_client.get(f"{BASE}/interfaces").get_json()["data"]["devices"]

        assert devices[0]["interfaces"] == [{"if_index": 3, "name": "Interface 3 (default check)", "speed_bps": None}]

    def test_a_device_without_snmp_is_not_listed(self, logged_in_client, db_session, admin_user):
        from tests.unit.test_create_host_cfg import make_device
        make_device(db_session, admin_user, "plain", "10.0.0.34")
        assert logged_in_client.get(f"{BASE}/interfaces").get_json()["data"]["devices"] == []
