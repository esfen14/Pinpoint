"""
tests/unit/test_interface_discovery.py — Interface discovery over SNMP
(app/network_discovery/interface_discovery.py).

snmpwalk is never run: subprocess.run is replaced with canned `snmpwalk -On` output. Covers the
output parser, speed/status decoding, the safe command line, errors that do not leak the
community, and storing the list (monitoring choice kept across refreshes).
"""
import subprocess
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db
from app.network_discovery import interface_discovery as discovery
from app.network_discovery.interface_discovery import (
    COLUMNS,
    InterfaceDiscoveryError,
    as_number,
    device_snmp_settings,
    parse_walk,
    refresh_device_interfaces,
    refresh_interfaces_after_scan,
    speed_bps,
    status_name,
    store_interfaces,
    walk_interfaces,
)
from app.system_models import DeviceInterface, Open_UDP_Services, PortState
from tests.unit.test_create_host_cfg import make_device

WALKS = {
    COLUMNS["descr"]: [
        ".1.3.6.1.2.1.2.2.1.2.1 = STRING: lo",
        ".1.3.6.1.2.1.2.2.1.2.2 = STRING: eth0",
        ".1.3.6.1.2.1.2.2.1.2.3 = STRING: eth1",
    ],
    COLUMNS["name"]: [
        ".1.3.6.1.2.1.31.1.1.1.1.2 = STRING: eth0",
        ".1.3.6.1.2.1.31.1.1.1.1.3 = STRING: \"uplink\"",
    ],
    COLUMNS["speed"]: [
        ".1.3.6.1.2.1.2.2.1.5.1 = Gauge32: 10000000",
        ".1.3.6.1.2.1.2.2.1.5.2 = Gauge32: 1000000000",
        ".1.3.6.1.2.1.2.2.1.5.3 = Gauge32: 4294967295",
    ],
    COLUMNS["high_speed"]: [
        ".1.3.6.1.2.1.31.1.1.1.15.2 = Gauge32: 1000",
        ".1.3.6.1.2.1.31.1.1.1.15.3 = Gauge32: 10000",
    ],
    COLUMNS["admin"]: [
        ".1.3.6.1.2.1.2.2.1.7.1 = INTEGER: up(1)",
        ".1.3.6.1.2.1.2.2.1.7.2 = INTEGER: up(1)",
        ".1.3.6.1.2.1.2.2.1.7.3 = INTEGER: down(2)",
    ],
    COLUMNS["oper"]: [
        ".1.3.6.1.2.1.2.2.1.8.1 = INTEGER: up(1)",
        ".1.3.6.1.2.1.2.2.1.8.2 = INTEGER: up(1)",
        ".1.3.6.1.2.1.2.2.1.8.3 = INTEGER: 2",
    ],
}


def fake_run(walks=WALKS, calls=None, returncode=0):
    def run(command, **kwargs):
        if calls is not None:
            calls.append((command, kwargs))
        oid = command[-1]
        return subprocess.CompletedProcess(command, returncode, "\n".join(walks.get(oid, [])), "")
    return run


class TestParsing:

    def test_values_are_keyed_by_interface_index(self):
        assert parse_walk("\n".join(WALKS[COLUMNS["descr"]]), COLUMNS["descr"]) == {1: "lo", 2: "eth0", 3: "eth1"}

    def test_quotes_are_removed(self):
        assert parse_walk("\n".join(WALKS[COLUMNS["name"]]), COLUMNS["name"])[3] == "uplink"

    def test_other_columns_and_noise_are_skipped(self):
        output = "\n".join([
            ".1.3.6.1.2.1.2.2.1.2.1 = STRING: lo",
            ".1.3.6.1.2.1.2.2.1.20.1 = STRING: not this column",
            ".1.3.6.1.2.1.2.2.1.2.2 = No Such Instance currently exists at this OID",
            "Timeout: No Response from 10.0.0.1",
            "garbage",
        ])
        assert parse_walk(output, COLUMNS["descr"]) == {1: "lo"}

    @pytest.mark.parametrize("text, number", [("up(1)", 1), ("1000000000", 1000000000), ("", None), (None, None)])
    def test_as_number(self, text, number):
        assert as_number(text) == number

    def test_high_speed_is_preferred_and_zero_means_unknown(self):
        assert speed_bps("4294967295", "10000") == 10_000_000_000
        assert speed_bps("100000000", None) == 100_000_000
        assert speed_bps("0", "0") is None
        assert speed_bps(None, None) is None

    def test_status_words(self):
        assert status_name("up(1)") == "up"
        assert status_name("2") == "down"
        assert status_name("nonsense") is None


class TestWalk:

    def test_interfaces_are_assembled(self):
        with patch.object(discovery.subprocess, "run", fake_run()):
            interfaces = walk_interfaces("10.0.0.9", 161, "public")

        assert interfaces == [
            {"if_index": 1, "name": "lo", "speed_bps": 10_000_000, "admin_status": "up", "oper_status": "up"},
            {"if_index": 2, "name": "eth0", "speed_bps": 1_000_000_000, "admin_status": "up", "oper_status": "up"},
            {"if_index": 3, "name": "uplink", "speed_bps": 10_000_000_000, "admin_status": "down", "oper_status": "down"},
        ]

    def test_command_is_an_argument_list_with_a_timeout(self):
        calls = []
        with patch.object(discovery.subprocess, "run", fake_run(calls=calls)):
            walk_interfaces("10.0.0.9", 1161, "s3cret")

        assert len(calls) == len(COLUMNS)
        command, kwargs = calls[0]
        assert command[:5] == ["snmpwalk", "-v2c", "-c", "s3cret", "-On"]
        assert "udp:10.0.0.9:1161" in command
        assert kwargs["timeout"] == discovery.WALK_TIMEOUT_SECONDS
        assert "shell" not in kwargs or kwargs["shell"] is False

    @pytest.mark.parametrize("address, port, community", [
        ("10.0.0.9; reboot", 161, "public"),
        ("not-an-ip", 161, "public"),
        ("10.0.0.9", 0, "public"),
        ("10.0.0.9", "16 1", "public"),
        ("10.0.0.9", 161, "pub'lic"),
        ("10.0.0.9", 161, "pub;lic"),
        ("10.0.0.9", 161, "-v3"),
        ("10.0.0.9", 161, ""),
    ])
    def test_unsafe_inputs_never_reach_snmpwalk(self, address, port, community):
        with patch.object(discovery.subprocess, "run") as run:
            with pytest.raises(InterfaceDiscoveryError):
                walk_interfaces(address, port, community)
        run.assert_not_called()

    def test_a_device_with_no_interfaces(self):
        with patch.object(discovery.subprocess, "run", fake_run(walks={})):
            with pytest.raises(InterfaceDiscoveryError, match="no network interfaces"):
                walk_interfaces("10.0.0.9", 161, "public")

    @pytest.mark.parametrize("failure, text", [
        (FileNotFoundError(), "not installed"),
        (subprocess.TimeoutExpired("snmpwalk", 20), "did not answer in time"),
        (PermissionError(), "could not be started"),
    ])
    def test_tool_failures_are_explained_without_the_community(self, failure, text):
        with patch.object(discovery.subprocess, "run", side_effect=failure):
            with pytest.raises(InterfaceDiscoveryError, match=text) as caught:
                walk_interfaces("10.0.0.9", 161, "s3cret-community")
        assert "s3cret-community" not in str(caught.value)

    def test_a_failing_walk_does_not_leak_the_community(self):
        with patch.object(discovery.subprocess, "run", fake_run(returncode=1)):
            with pytest.raises(InterfaceDiscoveryError) as caught:
                walk_interfaces("10.0.0.9", 161, "s3cret-community")
        assert "s3cret-community" not in str(caught.value)


def snmp_device(db_session, admin_user, name="switch", ip="10.0.0.9", plugin_variables=None, state=PortState.MONITORED):
    device = make_device(db_session, admin_user, name, ip, plugin_variables=plugin_variables)
    db_session.session.add(Open_UDP_Services(
        Port_Number=161, Service_Name="snmp", Plugin_Name="snmp", Port_State=state, NetDiscoveryID=device.NetDiscoveryID,
    ))
    db_session.session.commit()
    return device


def stored(device):
    return {
        row.If_Index: row for row in db.session.scalars(
            sa.select(DeviceInterface).where(DeviceInterface.NetDiscoveryID == device.NetDiscoveryID)
        ).all()
    }


class TestSettings:

    def test_port_and_community_follow_the_snmp_plugin_rules(self, db_session, admin_user):
        device = snmp_device(db_session, admin_user, plugin_variables={"snmp": {"community": "private"}})
        assert device_snmp_settings(device) == (161, "private")

    def test_defaults_come_from_config(self, db_session, admin_user, app):
        device = snmp_device(db_session, admin_user)
        assert device_snmp_settings(device) == (161, app.config["SNMP_COMMUNITY_STRING"])

    def test_a_device_without_snmp_is_refused(self, db_session, admin_user):
        device = make_device(db_session, admin_user, "plain", "10.0.0.8")
        with pytest.raises(InterfaceDiscoveryError, match="SNMP is not monitored"):
            device_snmp_settings(device)


class TestStore:

    def test_refresh_stores_every_interface_unmonitored(self, db_session, admin_user):
        device = snmp_device(db_session, admin_user)
        with patch.object(discovery.subprocess, "run", fake_run()):
            rows = refresh_device_interfaces(device)

        assert [(r.If_Index, r.Name, r.Monitored, r.Present) for r in rows] == [
            (1, "lo", False, True), (2, "eth0", False, True), (3, "uplink", False, True),
        ]
        assert stored(device)[2].Speed_Bps == 1_000_000_000

    def test_monitoring_choice_survives_a_refresh(self, db_session, admin_user):
        device = snmp_device(db_session, admin_user)
        with patch.object(discovery.subprocess, "run", fake_run()):
            refresh_device_interfaces(device)
            stored(device)[2].Monitored = True
            db_session.session.commit()
            refresh_device_interfaces(device)

        assert stored(device)[2].Monitored is True
        assert stored(device)[1].Monitored is False

    def test_vanished_interfaces_are_removed_unless_monitored(self, db_session, admin_user):
        device = snmp_device(db_session, admin_user)
        with patch.object(discovery.subprocess, "run", fake_run()):
            refresh_device_interfaces(device)
        stored(device)[3].Monitored = True
        db_session.session.commit()

        smaller = {key: [line for line in lines if not line.endswith(("lo",)) and ".1.3.6.1.2.1.2.2.1.2.1 " not in line]
                   for key, lines in WALKS.items()}
        smaller[COLUMNS["descr"]] = [".1.3.6.1.2.1.2.2.1.2.2 = STRING: eth0"]
        smaller[COLUMNS["name"]] = [".1.3.6.1.2.1.31.1.1.1.1.2 = STRING: eth0"]
        with patch.object(discovery.subprocess, "run", fake_run(walks=smaller)):
            refresh_device_interfaces(device)

        rows = stored(device)
        assert sorted(rows) == [2, 3]                       # lo (1) removed
        assert rows[3].Monitored is True and rows[3].Present is False

    def test_a_failed_save_rolls_back(self, db_session, admin_user):
        device = snmp_device(db_session, admin_user)
        with patch.object(discovery.subprocess, "run", fake_run()), \
                patch.object(discovery, "store_interfaces", side_effect=RuntimeError("boom")):
            with pytest.raises(InterfaceDiscoveryError, match="could not be saved"):
                refresh_device_interfaces(device)
        assert stored(device) == {}

    def test_store_updates_changed_values(self, db_session, admin_user):
        device = snmp_device(db_session, admin_user)
        first = [{"if_index": 7, "name": "old", "speed_bps": 100, "admin_status": "up", "oper_status": "up"}]
        store_interfaces(device, first)
        store_interfaces(device, [{**first[0], "name": "new", "speed_bps": None, "oper_status": "down"}])
        db_session.session.commit()

        row = stored(device)[7]
        assert (row.Name, row.Speed_Bps, row.Oper_Status) == ("new", None, "down")


class TestScanRefresh:

    def test_refreshes_snmp_devices_and_skips_failures(self, db_session, admin_user):
        good = snmp_device(db_session, admin_user, "good", "10.0.0.20")
        bad = snmp_device(db_session, admin_user, "bad", "10.0.0.21")
        make_device(db_session, admin_user, "plain", "10.0.0.22")

        def run(command, **kwargs):
            if "udp:10.0.0.21:161" in command:
                raise subprocess.TimeoutExpired("snmpwalk", 20)
            return fake_run()(command, **kwargs)

        with patch.object(discovery.subprocess, "run", run):
            assert refresh_interfaces_after_scan() == 1

        assert len(stored(good)) == 3
        assert stored(bad) == {}

    def test_is_bounded_by_the_device_limit(self, db_session, admin_user, monkeypatch):
        monkeypatch.setattr(discovery, "SCAN_DEVICE_LIMIT", 2)
        for number in range(4):
            snmp_device(db_session, admin_user, f"dev{number}", f"10.0.1.{number + 1}")
        with patch.object(discovery.subprocess, "run", fake_run()):
            assert refresh_interfaces_after_scan() == 2

    def test_stops_when_the_time_budget_is_used(self, db_session, admin_user, monkeypatch):
        monkeypatch.setattr(discovery, "SCAN_TIME_BUDGET_SECONDS", -1)
        snmp_device(db_session, admin_user)
        calls = []
        with patch.object(discovery.subprocess, "run", fake_run(calls=calls)):
            assert refresh_interfaces_after_scan() == 0
        assert calls == []
