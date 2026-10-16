"""Discovered-device picker searches application records independently of Nagios."""
import pytest

from app.system_models import DeviceState
from tests.support.identity_helpers import make_status, run_scan, scan, NET

BASE = "/api/system/hosts/lookup"


def test_lookup_requires_login(client, db_session):
    assert client.get(BASE).status_code in (401, 302)


def test_lookup_requires_hosts_permission(limited_client, db_session):
    assert limited_client.get(BASE).status_code == 403


def test_lookup_searches_nonmonitored_and_legacy_names(logged_in_client, db_session, admin_user):
    status = make_status(db_session, admin_user)
    device = run_scan(db_session, status, scan("10.0.0.5", hostname="Old-Printer"))[(NET, "10.0.0.5")]
    device.Display_Name = "Front Desk"
    device.Include_Device_In_Scanning = False
    device.Device_State = DeviceState.ADDRESS_UNKNOWN
    db_session.session.commit()
    for term in ("front", "old-printer", "10.0.0.5", str(device.NetDiscoveryID)):
        response = logged_in_client.get(BASE, query_string={"search": term})
        assert response.status_code == 200
        item = response.json["data"]["items"][0]
        assert item["id"] == device.NetDiscoveryID
        assert item["monitoring_state"] == "paused"
        assert item["nagios_host_name"]
    assert logged_in_client.get(BASE, query_string={"search": "absent"}).json["data"]["items"] == []


def test_lookup_is_bounded_and_includes_retired_sources(logged_in_client, db_session, admin_user):
    status = make_status(db_session, admin_user)
    for n in range(1, 24):
        device = run_scan(db_session, status, scan(f"10.0.0.{n}"))[(NET, f"10.0.0.{n}")]
        device.Device_State = DeviceState.RETIRED if n == 1 else DeviceState.ACTIVE
    db_session.session.commit()
    response = logged_in_client.get(BASE).json["data"]
    assert len(response["items"]) == 20
    assert response["has_more"] is True
    assert response["items"][0]["state"] == "RETIRED"


def test_lookup_omits_merged_and_treats_wildcards_literally(logged_in_client, db_session, admin_user):
    status = make_status(db_session, admin_user)
    device = run_scan(db_session, status, scan("10.0.0.5"))[(NET, "10.0.0.5")]
    # Prove wildcard escaping against a visible record before testing exclusion.
    assert logged_in_client.get(BASE, query_string={"search": "%"}).json["data"]["items"] == []
    assert logged_in_client.get(BASE, query_string={"search": "_"}).json["data"]["items"] == []
    device.Display_Name = "Printer_100%"
    db_session.session.commit()
    literal = logged_in_client.get(BASE, query_string={"search": "100%"}).json["data"]["items"]
    assert [row["id"] for row in literal] == [device.NetDiscoveryID]
    device.Device_State = DeviceState.MERGED
    db_session.session.commit()
    assert logged_in_client.get(BASE).json["data"]["items"] == []
    assert logged_in_client.get(BASE, query_string={"search": "%"}).json["data"]["items"] == []


@pytest.mark.parametrize("term", ["x" * 101])
def test_lookup_rejects_overlong_search(logged_in_client, db_session, term):
    assert logged_in_client.get(BASE, query_string={"search": term}).status_code == 400
