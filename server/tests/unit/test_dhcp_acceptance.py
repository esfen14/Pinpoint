"""Assertions used by the bounded live DHCP acceptance runner."""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("dhcp_acceptance", ROOT / "lab/dhcp/acceptance.py")
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


def test_wait_until_is_bounded_and_reports_last_observation():
    """A nonconverging scan must fail with its last status, never hang."""
    ticks = iter((0.0, 0.1, 0.2, 0.31))
    with pytest.raises(TimeoutError, match="Running"):
        acceptance.wait_until(lambda: {"status": "Running"}, lambda value: False,
                              timeout=0.3, interval=0, clock=lambda: next(ticks),
                              sleep=lambda _: None)


def test_client_continuity_requires_all_persistent_identifiers():
    """A B lease is not enough if the target or one of its keys changed."""
    before = {"container_id": "abc", "boot_id": "boot", "mac": "m1", "client_id": "c1",
              "machine_id": "machine", "host_key": "key", "addresses": ["10.79.0.5"]}
    after = {**before, "addresses": ["10.79.0.6"]}
    acceptance.assert_client_move(before, after)
    for key in ("container_id", "boot_id", "mac", "client_id", "machine_id", "host_key"):
        changed = {**after, key: "changed"}
        with pytest.raises(AssertionError, match=key):
            acceptance.assert_client_move(before, changed)
    with pytest.raises(AssertionError, match="address"):
        acceptance.assert_client_move(before, {**after, "addresses": ["10.79.0.5", "10.79.0.6"]})


def test_product_move_requires_one_id_and_nagios_name():
    """The same host record must actually change its current address."""
    before = {"id": 7, "nagios_host_name": "dev-7", "ip_address": "10.79.0.5"}
    acceptance.assert_device_move(before, {**before, "ip_address": "10.79.0.6"})
    with pytest.raises(AssertionError, match="device id"):
        acceptance.assert_device_move(before, {**before, "id": 8, "ip_address": "10.79.0.6"})
    with pytest.raises(AssertionError, match="Nagios host name"):
        acceptance.assert_device_move(before, {**before, "nagios_host_name": "dev-8", "ip_address": "10.79.0.6"})


def test_reuse_never_attributes_previous_identity():
    """A different MAC/key taking A must have its own Pinpoint/Nagios identity."""
    first = {"id": 7, "nagios_host_name": "dev-7", "ip_address": "10.79.0.6"}
    second = {"id": 8, "nagios_host_name": "dev-8", "ip_address": "10.79.0.5"}
    acceptance.assert_distinct_reuse(first, second)
    with pytest.raises(AssertionError, match="device id"):
        acceptance.assert_distinct_reuse(first, {**second, "id": 7})
    with pytest.raises(AssertionError, match="Nagios host name"):
        acceptance.assert_distinct_reuse(first, {**second, "nagios_host_name": "dev-7"})


def test_wait_up_accepts_real_network_health_state_case():
    """The API serializes the UP enum as title case in live snapshots."""
    class Api:
        def call(self, method, path):
            return {"items": [{"hostname": "dev-7", "ip_address": "10.79.0.5",
                               "state": "Up", "last_check": "2026-10-17T01:00:00"}]}

    assert acceptance.wait_up(Api(), "dev-7", "10.79.0.5")["state"] == "Up"


def test_address_lookup_ignores_displaced_address_unknown_record():
    """A retained address history holder must not count as the current A owner."""
    class Api:
        def call(self, method, path):
            return {"items": [
                {"id": 8, "ip_address": "10.79.0.5", "state": "ADDRESS_UNKNOWN"},
                {"id": 7, "ip_address": "10.79.0.5", "state": "ACTIVE"},
            ]}

    assert acceptance.device_at(Api(), "10.79.0.5")["id"] == 7


def test_pre_move_history_requires_real_down_host_event():
    """A browser history marker must come from the archive-backed API."""
    class Api:
        def call(self, method, path):
            return {"items": [
                {"hostname": "dev-7", "type": "host", "new_state": "DOWN", "timestamp": 42},
                {"hostname": "dev-8", "type": "host", "new_state": "DOWN", "timestamp": 43},
            ]}

    assert acceptance.pre_move_events(Api(), "dev-7")[0]["timestamp"] == 42
