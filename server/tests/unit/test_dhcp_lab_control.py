"""Safety contracts for the opt-in real DHCP lab controller."""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("dhcp_control", ROOT / "lab/dhcp/control.py")
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)


def test_range_rejects_host_docker_or_vm_overlap():
    """Setup must reject any subnet intersecting the test segment."""
    for occupied in (["10.79.0.0/24"], ["10.79.0.8/29"], ["10.79.0.5/32"]):
        with pytest.raises(ValueError, match="overlap"):
            control.validate_range("10.79.0.0/28", occupied)
    control.validate_range("10.79.0.0/28", ["10.77.0.0/28", "10.78.0.0/24", "192.168.130.0/24"])


def test_owned_resource_requires_exact_token_and_role():
    """A name match or generic label cannot authorize Docker mutation."""
    expected = {"org.pinpoint.dhcp.owner": "private-token", "org.pinpoint.dhcp.role": "switch"}
    control.require_owned(expected, "private-token", "switch")
    with pytest.raises(ValueError, match="ownership"):
        control.require_owned({"org.pinpoint.dhcp.owner": "other", "org.pinpoint.dhcp.role": "switch"}, "private-token", "switch")
    with pytest.raises(ValueError, match="ownership"):
        control.require_owned({"org.pinpoint.dhcp.owner": "private-token", "org.pinpoint.dhcp.role": "client"}, "private-token", "switch")


def test_dnsmasq_config_is_segment_only_and_reservation_only():
    """The allocator must bind the switch interface and serve only known MACs."""
    config = control.render_dnsmasq({"client1": "10.79.0.5", "client2": None})
    assert "interface=brdhcp\n" in config
    assert "bind-interfaces\n" in config
    assert "port=0\n" in config
    assert "dhcp-ignore=tag:!known\n" in config
    assert "dhcp-host=02:79:00:00:00:01,10.79.0.5\n" in config
    assert "10.79.0.1" not in config.split("dhcp-range=")[1].splitlines()[0]
    assert "10.79.0.2" not in config.split("dhcp-range=")[1].splitlines()[0]
    with pytest.raises(ValueError, match="duplicate"):
        control.render_dnsmasq({"client1": "10.79.0.5", "client2": "10.79.0.5"})


def test_client_address_requires_only_expected_lease():
    """Moving to B must fail if A remains installed or B is absent."""
    control.require_test_address(["10.79.0.6"], "10.79.0.6")
    with pytest.raises(ValueError, match="test address"):
        control.require_test_address(["10.79.0.5", "10.79.0.6"], "10.79.0.6")
    with pytest.raises(ValueError, match="test address"):
        control.require_test_address([], "10.79.0.6")
