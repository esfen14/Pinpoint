"""Nagios-backed availability report regression tests for issue #92."""

from unittest.mock import patch

from tests.support.seed_helpers import _make_host
from app.history_models import HostStateType


AVAILABILITY = "/api/system/report/availability"
HOSTS_BY_OS = "/api/system/report/hosts-by-os"
REQUEST = "app.api.system.report.request_host_availability_range"
NETWORK_REQUEST = "app.api.system.network_health_activity.request_host_availability_range"


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
        assert data["hosts"][0]["total_snapshots"] == 100
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
