"""Nagios-backed availability report regression tests for issue #92."""

from unittest.mock import patch

import pytest

from tests.support.seed_helpers import _make_host
from app.history_models import HostStateType
from app.system_models import (
    ActivityLog, DeviceState, DiscoveryStatus, NetworkDiscovery, NetworkDiscoveryStatus,
)


AVAILABILITY = "/api/system/report/availability"
HOSTS_BY_OS = "/api/system/report/hosts-by-os"
REQUEST = "app.api.system.report.request_host_availability_range"
NETWORK_REQUEST = "app.api.system.network_health_activity.request_host_availability_range"
CURRENT = "app.api.system.report.read_current_hosts"

AVAILABLE = {"available": True, "observed_at": "2026-10-18T16:00:00+00:00", "notice": None}
UNAVAILABLE = {
    "available": False, "observed_at": None,
    "notice": "Current status unavailable. Historical availability is still shown; retry the report to refresh status.",
}
CURRENT_STATUS = {
    "web-01": {"state": "Up", "last_check": "2026-10-18T15:59:00+00:00", "last_state_change": "2026-10-17T09:00:00+00:00"},
    "db-01": {"state": "Down", "last_check": "2026-10-18T15:58:00+00:00", "last_state_change": "2026-10-18T14:00:00+00:00"},
}


def make_device(db_session, admin_user, name, state=DeviceState.ACTIVE, include=True, os_type=None):
    """One device with the given Nagios host name; returns it."""
    log = ActivityLog(Action_Type="test", UserID=admin_user.UserID)
    db_session.session.add(log)
    db_session.session.flush()
    status = NetworkDiscoveryStatus(Status=DiscoveryStatus.SUCCESS, Progress=100, Message="Done", LogID=log.LogID)
    db_session.session.add(status)
    db_session.session.flush()
    device = NetworkDiscovery(
        Hostname=name, IP_Address="10.0.20.11", Network="10.0.20.0/24", Nagios_Host_Name=name,
        Device_State=state, Include_Device_In_Scanning=include, OS_Type=os_type,
        DiscoveryStatusID=status.DiscoveryStatusID)
    db_session.session.add(device)
    db_session.session.commit()
    return device


@pytest.fixture(autouse=True)
def fleet(db_session, admin_user):
    """web-01 and db-01 are monitored devices, and Nagios reports their current status."""
    make_device(db_session, admin_user, "web-01", os_type="Linux")
    make_device(db_session, admin_user, "db-01", os_type="Linux")
    with patch(CURRENT, return_value=(CURRENT_STATUS, AVAILABLE)) as read_current:
        yield read_current


def _rows():
    return [
        {
            "hostname": "web-01",
            "time_up": 80,
            "time_down": 20,
            "time_unreachable": 0,
            "state": "UP",
        },
        {
            "hostname": "db-01",
            "time_up": 0,
            "time_down": 100,
            "time_unreachable": 0,
            "state": "DOWN",
        },
    ]


class TestReportAvailabilityNagiosSource:
    def test_uses_nagios_window_and_preserves_compatible_shape(
        self, logged_in_client, db_session, seeded_permissions
    ):
        with patch(REQUEST, return_value=_rows()) as request_availability:
            response = logged_in_client.get(
                f"{AVAILABILITY}?period=custom&start=2024-01-01&end=2024-01-02"
            )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["summary"]["uptime_pct"] == 40.0
        assert {host["hostname"] for host in data["hosts"]} == {"web-01", "db-01"}
        host = next(h for h in data["hosts"] if h["hostname"] == "web-01")
        assert "total_snapshots" not in host
        assert host["up_seconds"] == 80
        assert host["down_seconds"] == 20
        assert host["unreachable_seconds"] == 0
        assert host["known_seconds"] == 100
        start, end = request_availability.call_args.args
        assert start < end

    def test_host_scope_is_forwarded_to_nagios(
        self, logged_in_client, db_session, seeded_permissions
    ):
        with patch(REQUEST, return_value=_rows()) as request_availability:
            response = logged_in_client.get(f"{AVAILABILITY}?hostname=web-01")

        assert response.status_code == 200
        assert request_availability.call_args.kwargs == {"hostname": "web-01"}

    def test_does_not_fall_back_to_snapshots_on_empty_nagios_data(
        self, logged_in_client, db_session, seeded_permissions
    ):
        _make_host(db_session, "snapshot-only", state=HostStateType.UP)
        db_session.session.commit()

        with patch(REQUEST, return_value=[]):
            response = logged_in_client.get(AVAILABILITY)

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["hosts"] == []
        assert data["summary"]["total"] == 0
        assert data["summary"]["uptime_pct"] is None

    def test_nagios_failure_is_explicit(self, logged_in_client, db_session, seeded_permissions):
        with patch(REQUEST, return_value=None):
            response = logged_in_client.get(AVAILABILITY)

        assert response.status_code == 502
        assert "Nagios" in response.get_json()["message"]

    def test_hosts_by_os_uses_the_same_nagios_rows(
        self, logged_in_client, db_session, seeded_permissions
    ):
        with patch(REQUEST, return_value=_rows()) as request_availability:
            response = logged_in_client.get(f"{HOSTS_BY_OS}?period=last_7d&hostname=web-01")

        assert response.status_code == 200
        groups = response.get_json()["data"]["by_os"]
        assert [host["hostname"] for host in groups[0]["hosts"]] == ["web-01"]
        assert groups[0]["hosts"][0]["uptime_pct"] == 80.0
        assert "total_snapshots" not in groups[0]["hosts"][0]
        assert groups[0]["hosts"][0]["known_seconds"] == 100
        assert request_availability.call_args.kwargs == {"hostname": "web-01"}

    def test_hosts_by_os_reports_nagios_failure(
        self, logged_in_client, db_session, seeded_permissions
    ):
        with patch(REQUEST, return_value=None):
            response = logged_in_client.get(HOSTS_BY_OS)

        assert response.status_code == 502

    def test_network_health_and_report_use_equivalent_availability_semantics(
        self, logged_in_client, db_session, seeded_permissions
    ):
        """Equivalent Nagios durations produce the same percentage in both routes."""
        rows = [{
            "hostname": "web-01",
            "time_up": 80,
            "time_down": 15,
            "time_unreachable": 5,
            "time_indeterminate": 100,
        }]
        with (
            patch(REQUEST, return_value=rows),
            patch(NETWORK_REQUEST, return_value=rows),
        ):
            report_response = logged_in_client.get(AVAILABILITY)
            health_response = logged_in_client.get(
                "/api/system/network-health/availability?days=1"
            )

        assert report_response.status_code == 200
        assert health_response.status_code == 200
        assert report_response.get_json()["data"]["summary"]["uptime_pct"] == 80.0
        assert health_response.get_json()["data"]["availability_pct"] == 80.0


class TestReportAvailabilityCurrentStatus:
    """State, last check and last state change come from one bulk current-status read (#228)."""

    def test_rows_carry_current_state_and_check_times(self, logged_in_client, fleet):
        with patch(REQUEST, return_value=_rows()):
            response = logged_in_client.get(AVAILABILITY)

        data = response.get_json()["data"]
        by_name = {host["hostname"]: host for host in data["hosts"]}
        assert by_name["web-01"]["state"] == "Up"
        assert by_name["web-01"]["last_check"] == "2026-10-18T15:59:00+00:00"
        assert by_name["web-01"]["last_state_change"] == "2026-10-17T09:00:00+00:00"
        assert by_name["db-01"]["state"] == "Down"
        assert by_name["db-01"]["last_check"] == "2026-10-18T15:58:00+00:00"
        assert data["current_status"] == AVAILABLE
        assert fleet.call_count == 1

    def test_summary_cards_count_the_real_states(self, logged_in_client, db_session, admin_user, fleet):
        make_device(db_session, admin_user, "edge-01")
        status = {**CURRENT_STATUS, "edge-01": {"state": "Unreachable", "last_check": None, "last_state_change": None}}
        fleet.return_value = (status, AVAILABLE)
        rows = _rows() + [{"hostname": "edge-01", "time_up": 0, "time_down": 0, "time_unreachable": 50}]

        with patch(REQUEST, return_value=rows):
            response = logged_in_client.get(AVAILABILITY)

        summary = response.get_json()["data"]["summary"]
        assert (summary["total"], summary["up"], summary["down"], summary["unreachable"]) == (3, 1, 1, 1)

    def test_every_uptime_is_between_0_and_100(self, logged_in_client):
        with patch(REQUEST, return_value=_rows()):
            hosts = logged_in_client.get(AVAILABILITY).get_json()["data"]["hosts"]

        assert hosts
        assert all(0 <= host["uptime_pct"] <= 100 for host in hosts)

    def test_unavailable_status_keeps_history_with_a_notice_and_no_invented_state(self, logged_in_client, fleet):
        fleet.return_value = ({}, UNAVAILABLE)

        with patch(REQUEST, return_value=_rows()):
            response = logged_in_client.get(AVAILABILITY)

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["current_status"] == UNAVAILABLE
        assert {host["hostname"] for host in data["hosts"]} == {"web-01", "db-01"}
        assert all(host["state"] is None for host in data["hosts"])
        assert all(host["last_check"] is None and host["last_state_change"] is None for host in data["hosts"])
        assert data["hosts"][0]["uptime_pct"] is not None
        assert (data["summary"]["up"], data["summary"]["down"], data["summary"]["unreachable"]) == (0, 0, 0)

    def test_a_host_with_history_but_no_status_row_has_no_state(self, logged_in_client, fleet):
        fleet.return_value = ({"web-01": CURRENT_STATUS["web-01"]}, AVAILABLE)

        with patch(REQUEST, return_value=_rows()):
            hosts = logged_in_client.get(AVAILABILITY).get_json()["data"]["hosts"]

        by_name = {host["hostname"]: host for host in hosts}
        assert by_name["web-01"]["state"] == "Up"
        assert by_name["db-01"]["state"] is None

    def test_the_status_read_does_not_replace_a_failed_archive_read(self, logged_in_client):
        with patch(REQUEST, return_value=None):
            response = logged_in_client.get(AVAILABILITY)

        assert response.status_code == 502


class TestReportAvailabilityMonitoredHosts:
    """Only hosts of currently monitored devices are listed (#228)."""

    def test_missing_paused_retired_and_deviceless_hosts_are_not_listed(
        self, logged_in_client, db_session, admin_user
    ):
        make_device(db_session, admin_user, "lost-01", state=DeviceState.MISSING)
        make_device(db_session, admin_user, "paused-01", include=False)
        make_device(db_session, admin_user, "gone-01", state=DeviceState.RETIRED)
        rows = _rows() + [
            {"hostname": name, "time_up": 10, "time_down": 0, "time_unreachable": 0}
            for name in ("lost-01", "paused-01", "gone-01", "localhost")
        ]

        with patch(REQUEST, return_value=rows):
            data = logged_in_client.get(AVAILABILITY).get_json()["data"]

        assert [host["hostname"] for host in data["hosts"]] == ["db-01", "web-01"]
        assert data["summary"]["total"] == 2

    def test_a_monitored_device_without_history_is_not_invented(self, logged_in_client, db_session, admin_user):
        make_device(db_session, admin_user, "quiet-01")

        with patch(REQUEST, return_value=_rows()):
            data = logged_in_client.get(AVAILABILITY).get_json()["data"]

        assert "quiet-01" not in {host["hostname"] for host in data["hosts"]}

    def test_overall_uptime_only_counts_the_listed_hosts(self, logged_in_client):
        rows = _rows() + [{"hostname": "localhost", "time_up": 0, "time_down": 1000, "time_unreachable": 0}]

        with patch(REQUEST, return_value=rows):
            data = logged_in_client.get(AVAILABILITY).get_json()["data"]

        assert data["summary"]["uptime_pct"] == 40.0


class TestHostsByOsCurrentStatus:
    def test_hosts_by_os_rows_carry_current_state_and_check_times(self, logged_in_client):
        with patch(REQUEST, return_value=_rows()):
            data = logged_in_client.get(HOSTS_BY_OS).get_json()["data"]

        hosts = {host["hostname"]: host for group in data["by_os"] for host in group["hosts"]}
        assert hosts["web-01"]["state"] == "Up"
        assert hosts["web-01"]["last_check"] == "2026-10-18T15:59:00+00:00"
        assert hosts["db-01"]["state"] == "Down"
        assert data["current_status"] == AVAILABLE
