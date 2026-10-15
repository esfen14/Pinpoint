"""
tests/unit/test_maintenance_routes.py — Maintenance window routes (app/api/system/maintenance.py).

  GET  /api/system/maintenance/windows
  POST /api/system/maintenance/windows
  PUT  /api/system/maintenance/windows/<id>
  POST /api/system/maintenance/windows/<id>/cancel

The Nagios pipe is replaced by _write_line; nothing reaches a real Nagios.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db, maintenance as mw
from app.history_models import HostStateType, ServiceStateType
from app.nagios import commands as cmd
from app.system_models import ActivityLog, MaintenanceOccurrence, MaintenanceWindow
from tests.support.seed_helpers import _make_host, _make_service
from tests.unit.test_create_host_cfg import make_device

URL = "/api/system/maintenance/windows"


def body(**over):
    now = mw.utcnow()
    data = {"startAt": mw.iso(now + timedelta(hours=2)), "endAt": mw.iso(now + timedelta(hours=3)),
            "comment": "patching", "deviceId": None, "recurrence": "none", "timeZone": "UTC"}
    data.update(over)
    return data


@pytest.fixture
def hosts(db_session):
    _make_host(db_session, "web-01", HostStateType.UP)
    _make_service(db_session, "web-01", "http", ServiceStateType.OK)
    db_session.session.commit()


@pytest.fixture
def sent():
    lines = []
    with patch.object(cmd, "_write_line", side_effect=lambda line: lines.append(line.split("] ", 1)[1]) or cmd.CommandResult(True)):
        yield lines


def audit():
    return db.session.scalars(sa.select(ActivityLog.Action_Type)).all()


class TestAccess:

    def test_requires_login(self, client, db_session):
        assert client.get(URL).status_code in (401, 302)
        assert client.post(URL, json=body()).status_code in (401, 302)
        assert client.put(f"{URL}/1", json=body()).status_code in (401, 302)
        assert client.post(f"{URL}/1/cancel").status_code in (401, 302)

    def test_requires_the_permission(self, limited_client):
        assert limited_client.get(URL).status_code == 403
        assert limited_client.post(URL, json=body()).status_code == 403
        assert limited_client.put(f"{URL}/1", json=body()).status_code == 403
        assert limited_client.post(f"{URL}/1/cancel").status_code == 403
        assert db.session.scalars(sa.select(MaintenanceWindow)).all() == []


class TestCreate:

    def test_creates_and_audits(self, logged_in_client, db_session):
        resp = logged_in_client.post(URL, json=body(comment="  kernel update "))
        data = resp.get_json()["data"]
        assert resp.status_code == 201
        assert data["status"] == "active" and data["comment"] == "kernel update"
        assert data["scope"] == {"type": "all", "deviceId": None, "deviceName": None}
        assert data["nextOccurrence"]["startAt"] == data["startAt"]
        assert data["createdBy"] == "Admin User"
        assert any(f"Created maintenance window {data['id']}" in action for action in audit())

    def test_times_are_stored_as_utc(self, logged_in_client, db_session):
        resp = logged_in_client.post(URL, json=body(startAt="2099-10-21T04:00:00+02:00", endAt="2099-10-21T06:00:00+02:00"))
        assert resp.status_code == 201
        row = db.session.scalars(sa.select(MaintenanceWindow)).one()
        assert row.Start_At.hour == 2 and row.End_At.hour == 4
        assert resp.get_json()["data"]["startAt"] == "2099-10-21T02:00:00Z"

    def test_device_scope(self, logged_in_client, db_session, admin_user):
        device = make_device(db_session, admin_user, "web-01", "10.0.0.1")
        db_session.session.commit()
        data = logged_in_client.post(URL, json=body(deviceId=device.NetDiscoveryID)).get_json()["data"]
        assert data["scope"]["type"] == "device" and data["scope"]["deviceName"] == "web-01"

    @pytest.mark.parametrize("over", [
        {"endAt": "2000-01-01T00:00:00Z", "startAt": "1999-01-01T00:00:00Z"},
        {"recurrence": "yearly"},
        {"comment": ""},
        {"deviceId": 424242},
        {"timeZone": "Nowhere/Land"},
        {"startAt": "tomorrow"},
    ])
    def test_invalid_is_400_and_saves_nothing(self, logged_in_client, db_session, over):
        resp = logged_in_client.post(URL, json=body(**over))
        assert resp.status_code == 400 and resp.get_json()["success"] is False
        assert db.session.scalars(sa.select(MaintenanceWindow)).all() == []

    def test_non_object_body_is_400(self, logged_in_client):
        assert logged_in_client.post(URL, json=[1]).status_code == 400
        assert logged_in_client.post(URL, data="nope", content_type="text/plain").status_code == 400


class TestList:

    def test_lists_newest_first_with_failures(self, logged_in_client, db_session, admin_user):
        first = logged_in_client.post(URL, json=body()).get_json()["data"]["id"]
        second = logged_in_client.post(URL, json=body()).get_json()["data"]["id"]
        row = db.session.get(MaintenanceWindow, first)
        db_session.session.add(MaintenanceOccurrence(
            WindowID=first, Start_At=row.Start_At, End_At=row.End_At, Status="failed", Attempts=3,
            Last_Error="web-01: Nagios is not reading its command pipe."))
        db_session.session.commit()

        windows = logged_in_client.get(URL).get_json()["data"]["windows"]

        assert [w["id"] for w in windows] == [second, first]
        assert windows[1]["occurrences"] == [{
            "startAt": mw.iso(row.Start_At), "endAt": mw.iso(row.End_At), "status": "failed",
            "attempts": 3, "error": "web-01: Nagios is not reading its command pipe."}]

    def test_empty(self, logged_in_client, db_session):
        data = logged_in_client.get(URL).get_json()["data"]
        assert data["windows"] == [] and data["devices"] == []

    def test_offers_only_monitored_devices(self, logged_in_client, db_session, admin_user):
        make_device(db_session, admin_user, "b-web", "10.0.0.2")
        make_device(db_session, admin_user, "a-db", "10.0.0.1")
        paused = make_device(db_session, admin_user, "paused-box", "10.0.0.3")
        paused.Include_Device_In_Scanning = False
        db_session.session.commit()
        names = [device["name"] for device in logged_in_client.get(URL).get_json()["data"]["devices"]]
        assert names == ["a-db", "b-web"]


class TestUpdate:

    def test_edits_an_active_window(self, logged_in_client, db_session):
        window_id = logged_in_client.post(URL, json=body()).get_json()["data"]["id"]
        resp = logged_in_client.put(f"{URL}/{window_id}", json=body(comment="moved", recurrence="daily"))
        data = resp.get_json()["data"]
        assert resp.status_code == 200
        assert data["comment"] == "moved" and data["recurrence"] == "daily"
        assert data["nagios_synced"] is True
        assert any(f"Updated maintenance window {window_id}" in action for action in audit())

    def test_edit_deletes_downtime_already_sent(self, logged_in_client, db_session, hosts, sent):
        window_id = logged_in_client.post(URL, json=body(
            startAt=mw.iso(mw.utcnow() + timedelta(minutes=5)), endAt=mw.iso(mw.utcnow() + timedelta(hours=1)))).get_json()["data"]["id"]
        mw.dispatch_due_windows()
        sent.clear()

        resp = logged_in_client.put(f"{URL}/{window_id}", json=body())

        assert resp.status_code == 200
        assert sent and all(line.startswith("DEL_DOWNTIME_BY_HOST_NAME;web-01;;;PinPoint maintenance window") for line in sent)
        assert db.session.scalars(sa.select(MaintenanceOccurrence)).all() == []

    def test_invalid_edit_changes_nothing(self, logged_in_client, db_session):
        window_id = logged_in_client.post(URL, json=body()).get_json()["data"]["id"]
        assert logged_in_client.put(f"{URL}/{window_id}", json=body(comment="")).status_code == 400
        assert db.session.get(MaintenanceWindow, window_id).Comment == "patching"

    def test_unknown_window_is_404(self, logged_in_client, db_session):
        assert logged_in_client.put(f"{URL}/999", json=body()).status_code == 404

    def test_cancelled_window_cannot_be_edited(self, logged_in_client, db_session):
        window_id = logged_in_client.post(URL, json=body()).get_json()["data"]["id"]
        logged_in_client.post(f"{URL}/{window_id}/cancel")
        assert logged_in_client.put(f"{URL}/{window_id}", json=body()).status_code == 400


class TestCancel:

    def test_cancel_removes_downtime_and_audits(self, logged_in_client, db_session, hosts, sent):
        window_id = logged_in_client.post(URL, json=body(
            startAt=mw.iso(mw.utcnow() + timedelta(minutes=5)), endAt=mw.iso(mw.utcnow() + timedelta(hours=1)))).get_json()["data"]["id"]
        mw.dispatch_due_windows()
        sent.clear()

        resp = logged_in_client.post(f"{URL}/{window_id}/cancel")

        data = resp.get_json()["data"]
        assert resp.status_code == 200 and data["status"] == "cancelled" and data["nagios_synced"] is True
        assert data["nextOccurrence"] is None
        assert len(sent) == 1 and sent[0].startswith("DEL_DOWNTIME_BY_HOST_NAME;web-01;;;")
        assert any(f"Cancelled maintenance window {window_id}" in action for action in audit())

    def test_cancelled_window_is_not_dispatched(self, logged_in_client, db_session, hosts, sent):
        window_id = logged_in_client.post(URL, json=body(
            startAt=mw.iso(mw.utcnow() + timedelta(minutes=5)), endAt=mw.iso(mw.utcnow() + timedelta(hours=1)))).get_json()["data"]["id"]
        logged_in_client.post(f"{URL}/{window_id}/cancel")
        assert mw.dispatch_due_windows() == 0 and sent == []

    def test_nagios_failure_is_reported_but_the_window_is_cancelled(self, logged_in_client, db_session, hosts, sent):
        window_id = logged_in_client.post(URL, json=body(
            startAt=mw.iso(mw.utcnow() + timedelta(minutes=5)), endAt=mw.iso(mw.utcnow() + timedelta(hours=1)))).get_json()["data"]["id"]
        mw.dispatch_due_windows()
        down = cmd.CommandResult(False, cmd.UNAVAILABLE, "Nagios is not reading its command pipe.")
        with patch.object(cmd, "_write_line", return_value=down):
            data = logged_in_client.post(f"{URL}/{window_id}/cancel").get_json()["data"]
        assert data["status"] == "cancelled" and data["nagios_synced"] is False
        assert "Nagios was not updated" in data["nagios_message"]

    def test_twice_is_400(self, logged_in_client, db_session):
        window_id = logged_in_client.post(URL, json=body()).get_json()["data"]["id"]
        assert logged_in_client.post(f"{URL}/{window_id}/cancel").status_code == 200
        assert logged_in_client.post(f"{URL}/{window_id}/cancel").status_code == 400

    def test_unknown_window_is_404(self, logged_in_client, db_session):
        assert logged_in_client.post(f"{URL}/999/cancel").status_code == 404
