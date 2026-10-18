"""Bulk current host status for the host reports (issue #228)."""

from unittest.mock import patch

import pytest

from app.nagios import host_current_status as hosts
from app.nagios.service_availability import AvailabilityError

REQUEST = "app.nagios.host_current_status.request_cgi"


def payload(hostlist, code=0):
    return {"result": {"type_code": code}, "data": {"hostlist": hostlist}}


class TestCurrentHosts:
    def test_maps_each_native_state_and_converts_milliseconds_to_utc(self):
        current = hosts.current_hosts(payload({
            "web-01": {"status": "up", "last_check": 1_700_000_000_000, "last_state_change": 1_699_990_000_000},
            "db-01": {"status": "down", "last_check": 1_700_000_060_000, "last_state_change": 1_700_000_000_000},
            "edge-01": {"status": "unreachable", "last_check": 1_700_000_120_000, "last_state_change": 1_700_000_100_000},
        }))

        assert current["web-01"] == {
            "state": "Up",
            "last_check": "2023-11-14T22:13:20+00:00",
            "last_state_change": "2023-11-14T19:26:40+00:00",
        }
        assert current["db-01"]["state"] == "Down"
        assert current["edge-01"]["state"] == "Unreachable"

    def test_a_host_never_checked_is_pending_with_no_timestamps(self):
        current = hosts.current_hosts(payload({
            "new-01": {"status": "pending", "has_been_checked": False, "last_check": 0, "last_state_change": 0},
        }))

        assert current["new-01"] == {"state": "Pending", "last_check": None, "last_state_change": None}

    def test_a_zero_timestamp_is_absent_not_1970(self):
        current = hosts.current_hosts(payload({"web-01": {"status": "up", "last_check": 0, "last_state_change": 0}}))

        assert current["web-01"]["last_check"] is None
        assert current["web-01"]["last_state_change"] is None

    @pytest.mark.parametrize("bad", [
        {"result": {"type_code": 1}, "data": {"hostlist": {}}},
        {"result": {"type_code": 0}, "data": {}},
        payload({"web-01": "up"}),
        payload({"web-01": {"status": "sideways"}}),
        payload({"web-01": {"status": "up", "last_check": "yesterday"}}),
        payload({"web-01": {"status": "up", "last_check": -5}}),
        "not json",
    ])
    def test_malformed_status_is_refused_not_guessed(self, bad):
        with pytest.raises(AvailabilityError):
            hosts.current_hosts(bad)


class TestReadCurrentHosts:
    def test_one_bulk_enumerated_call_and_an_available_context(self, app):
        body = payload({"web-01": {"status": "up", "last_check": 1_700_000_000_000, "last_state_change": 0}})
        with app.app_context(), patch(REQUEST, return_value=body) as call:
            current, context = hosts.read_current_hosts()

        assert call.call_count == 1
        assert call.call_args.args[0] == "NAGIOS_STATUS_URL"
        assert call.call_args.args[1] == {"query": "hostlist", "details": "true", "formatoptions": "enumerate"}
        assert current["web-01"]["state"] == "Up"
        assert context["available"] is True
        assert context["notice"] is None
        assert context["observed_at"]

    def test_failure_gives_no_status_and_an_explicit_notice(self, app):
        with app.app_context(), patch(REQUEST, side_effect=AvailabilityError("boom")):
            current, context = hosts.read_current_hosts()

        assert current == {}
        assert context["available"] is False
        assert context["observed_at"] is None
        assert "Current status unavailable" in context["notice"]
        assert "boom" not in context["notice"]
