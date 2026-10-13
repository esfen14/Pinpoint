"""
tests/unit/test_nagios_command_routes.py — Acknowledgement propagation to Nagios and Check Now.

Routes tested:
  POST/DELETE /api/system/dashboard/alerts/acknowledge, POST .../acknowledge-all
  POST/DELETE /api/system/network-health/hosts|services/acknowledge
  POST /api/system/network-health/hosts/<hostname>/recheck
  POST /api/system/network-health/services/<hostname>/<path:service_name>/recheck

Pipe writing is replaced by _write_line so the exact command lines can be asserted; the
pipe itself is covered in test_nagios_commands.py.
"""
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db
from app.history_models import HostStateType, ServiceStateType
from app.nagios import commands as cmd
from app.system_models import ActivityLog, AckHistory, AlertAcknowledgement, DeviceState
from tests.support.seed_helpers import _make_host, _make_service

BASE = "/api/system"
HOSTS = f"{BASE}/network-health/hosts"
SERVICES = f"{BASE}/network-health/services"
DASH = f"{BASE}/dashboard/alerts"


@pytest.fixture
def sent():
    """Capture lines instead of writing a pipe."""
    lines = []
    cmd._recheck_times.clear()

    def fake(line):
        lines.append(line.split("] ", 1)[1])
        return cmd.CommandResult(True)

    with patch.object(cmd, "_write_line", side_effect=fake):
        yield lines
    cmd._recheck_times.clear()


@pytest.fixture
def pipe_down():
    cmd._recheck_times.clear()
    down = cmd.CommandResult(False, cmd.UNAVAILABLE, "Nagios is not reading its command pipe.")
    with patch.object(cmd, "_write_line", return_value=down) as mock:
        yield mock
    cmd._recheck_times.clear()


@pytest.fixture
def problem(db_session):
    _make_host(db_session, "web-01", HostStateType.DOWN)
    _make_service(db_session, "web-01", "cpu/percent", ServiceStateType.CRITICAL)
    db_session.session.commit()


def audit_actions():
    return [r.Action_Type for r in db.session.scalars(sa.select(ActivityLog)).all()]


class TestAcknowledgeSendsToNagios:

    def test_service_ack_writes_command(self, logged_in_client, problem, sent):
        resp = logged_in_client.post(f"{SERVICES}/acknowledge", json={
            "hostname": "web-01", "service_name": "cpu/percent", "comment": "on it"})
        data = resp.get_json()["data"]
        assert resp.status_code == 201
        assert data["nagios_synced"] is True and data["nagios_message"] is None
        assert sent[0].startswith("ACKNOWLEDGE_SVC_PROBLEM;web-01;cpu/percent;1;0;1;")
        assert sent[0].endswith(";on it")

    def test_host_ack_writes_command(self, logged_in_client, problem, sent):
        resp = logged_in_client.post(f"{HOSTS}/acknowledge", json={"hostname": "web-01", "comment": "x"})
        assert resp.status_code == 201 and resp.get_json()["data"]["nagios_synced"] is True
        assert sent[0].startswith("ACKNOWLEDGE_HOST_PROBLEM;web-01;1;0;1;")

    def test_dashboard_ack_and_unack(self, logged_in_client, problem, sent):
        body = {"hostname": "web-01", "service_name": "cpu/percent"}
        assert logged_in_client.post(f"{DASH}/acknowledge", json={**body, "comment": "x"}).status_code == 201
        resp = logged_in_client.delete(f"{DASH}/acknowledge", json=body)
        assert resp.status_code == 200 and resp.get_json()["data"]["nagios_synced"] is True
        assert sent[1] == "REMOVE_SVC_ACKNOWLEDGEMENT;web-01;cpu/percent"

    def test_host_and_service_unack(self, logged_in_client, problem, sent):
        logged_in_client.post(f"{HOSTS}/acknowledge", json={"hostname": "web-01", "comment": "x"})
        logged_in_client.post(f"{SERVICES}/acknowledge", json={
            "hostname": "web-01", "service_name": "cpu/percent", "comment": "x"})
        assert logged_in_client.delete(f"{HOSTS}/acknowledge", json={"hostname": "web-01"}).status_code == 200
        assert logged_in_client.delete(f"{SERVICES}/acknowledge", json={
            "hostname": "web-01", "service_name": "cpu/percent"}).status_code == 200
        assert "REMOVE_HOST_ACKNOWLEDGEMENT;web-01" in sent
        assert "REMOVE_SVC_ACKNOWLEDGEMENT;web-01;cpu/percent" in sent

    def test_acknowledge_all_sends_one_command_each(self, logged_in_client, problem, sent):
        resp = logged_in_client.post(f"{DASH}/acknowledge-all", json={
            "comment": "all", "alerts": [
                {"hostname": "web-01", "service_name": None},
                {"hostname": "web-01", "service_name": "cpu/percent"}]})
        data = resp.get_json()["data"]
        assert data["acknowledged"] == 2 and data["nagios_synced"] is True
        assert len(sent) == 2


class TestLocalAckSurvivesNagiosFailure:

    def test_ack_saved_and_flagged_when_pipe_is_down(self, logged_in_client, problem, pipe_down):
        resp = logged_in_client.post(f"{SERVICES}/acknowledge", json={
            "hostname": "web-01", "service_name": "cpu/percent", "comment": "on it"})
        data = resp.get_json()["data"]
        assert resp.status_code == 201
        assert data["nagios_synced"] is False
        assert "Notifications may continue" in data["nagios_message"]
        assert data["comment"] == "on it"
        assert db.session.scalar(sa.select(sa.func.count()).select_from(AlertAcknowledgement)) == 1
        assert any(a.startswith("Nagios sync failed") for a in audit_actions())

    def test_unack_still_removes_local_record(self, logged_in_client, problem, sent):
        logged_in_client.post(f"{HOSTS}/acknowledge", json={"hostname": "web-01", "comment": "x"})
        with patch.object(cmd, "_write_line",
                          return_value=cmd.CommandResult(False, cmd.TIMEOUT, "full.")):
            resp = logged_in_client.delete(f"{HOSTS}/acknowledge", json={"hostname": "web-01"})
        assert resp.status_code == 200 and resp.get_json()["data"]["nagios_synced"] is False
        assert db.session.scalar(sa.select(sa.func.count()).select_from(AlertAcknowledgement)) == 0

    def test_acknowledge_all_reports_partial_failure(self, logged_in_client, problem, pipe_down):
        resp = logged_in_client.post(f"{DASH}/acknowledge-all", json={
            "comment": "all", "alerts": [{"hostname": "web-01", "service_name": None}]})
        data = resp.get_json()["data"]
        assert resp.status_code == 200 and data["acknowledged"] == 1 and data["nagios_synced"] is False

    def test_unknown_name_is_saved_locally_but_not_sent(self, logged_in_client, db_session, sent):
        """Acknowledge-all does not require an active alert; a name Nagios never reported is not sent."""
        resp = logged_in_client.post(f"{DASH}/acknowledge-all", json={
            "comment": "x", "alerts": [{"hostname": "ghost", "service_name": None}]})
        assert resp.get_json()["data"]["nagios_synced"] is False
        assert sent == []


class TestBadCommentsAreRejected:

    @pytest.mark.parametrize("bad", ["a\nb", "a\rb", "a\0b"])
    def test_every_ack_route_returns_400_and_writes_nothing(self, logged_in_client, problem, sent, bad):
        calls = [
            (f"{SERVICES}/acknowledge", {"hostname": "web-01", "service_name": "cpu/percent", "comment": bad}),
            (f"{HOSTS}/acknowledge", {"hostname": "web-01", "comment": bad}),
            (f"{DASH}/acknowledge", {"hostname": "web-01", "comment": bad}),
            (f"{DASH}/acknowledge-all", {"comment": bad, "alerts": [{"hostname": "web-01"}]}),
        ]
        for url, payload in calls:
            assert logged_in_client.post(url, json=payload).status_code == 400
        assert sent == []
        assert db.session.scalar(sa.select(sa.func.count()).select_from(AlertAcknowledgement)) == 0
        assert db.session.scalar(sa.select(sa.func.count()).select_from(AckHistory)) == 0


@pytest.mark.usefixtures("monitoring_plugins")
class TestCheckNow:

    def test_host_recheck_sends_forced_check(self, logged_in_client, problem, sent):
        resp = logged_in_client.post(f"{HOSTS}/web-01/recheck")
        assert resp.status_code == 200 and resp.get_json()["data"]["retry_after"] == 10
        assert sent[0].startswith("SCHEDULE_FORCED_HOST_CHECK;web-01;")
        assert "Requested check now for web-01" in audit_actions()

    def test_service_recheck_accepts_slash_in_name(self, logged_in_client, problem, sent):
        resp = logged_in_client.post(f"{SERVICES}/web-01/cpu/percent/recheck")
        assert resp.status_code == 200
        assert sent[0].startswith("SCHEDULE_FORCED_SVC_CHECK;web-01;cpu/percent;")

    def test_second_request_inside_the_limit_is_429(self, logged_in_client, problem, sent):
        assert logged_in_client.post(f"{HOSTS}/web-01/recheck").status_code == 200
        resp = logged_in_client.post(f"{HOSTS}/web-01/recheck")
        assert resp.status_code == 429
        assert 1 <= resp.get_json()["data"]["retry_after"] <= 10
        assert len(sent) == 1

    def test_limit_is_per_target(self, logged_in_client, problem, sent):
        assert logged_in_client.post(f"{HOSTS}/web-01/recheck").status_code == 200
        assert logged_in_client.post(f"{SERVICES}/web-01/cpu/percent/recheck").status_code == 200

    def test_failed_send_is_503_and_does_not_start_the_cooldown(self, logged_in_client, problem, pipe_down):
        assert logged_in_client.post(f"{HOSTS}/web-01/recheck").status_code == 503
        assert logged_in_client.post(f"{HOSTS}/web-01/recheck").status_code == 503

    def test_unknown_targets_are_404(self, logged_in_client, problem, sent):
        assert logged_in_client.post(f"{HOSTS}/ghost/recheck").status_code == 404
        assert logged_in_client.post(f"{SERVICES}/web-01/nope/recheck").status_code == 404
        assert sent == []

    @pytest.mark.parametrize("state", [DeviceState.RETIRED, DeviceState.MERGED])
    def test_ended_devices_are_refused(self, logged_in_client, db_session, sent, state):
        _make_host(db_session, "web-01")
        _make_service(db_session, "web-01", "cpu/percent")
        db_session.session.commit()
        self._device(db_session, "web-01").Device_State = state
        db_session.session.commit()
        assert logged_in_client.post(f"{HOSTS}/web-01/recheck").status_code == 409
        assert logged_in_client.post(f"{SERVICES}/web-01/cpu/percent/recheck").status_code == 409
        assert sent == []

    def test_paused_device_is_refused(self, logged_in_client, db_session, sent):
        _make_host(db_session, "web-01")
        db_session.session.commit()
        self._device(db_session, "web-01").Include_Device_In_Scanning = False
        db_session.session.commit()
        assert logged_in_client.post(f"{HOSTS}/web-01/recheck").status_code == 409
        assert sent == []

    @staticmethod
    def _device(db_session, name):
        from tests.support.identity_helpers import NET, make_status, run_scan, scan
        from app.system_models import User
        status = make_status(db_session, db.session.scalar(sa.select(User)))
        device = run_scan(db_session, status, scan("10.0.0.5"))[(NET, "10.0.0.5")]
        device.Nagios_Host_Name = name
        db.session.commit()
        return device

    def test_requires_login(self, client, db_session):
        assert client.post(f"{HOSTS}/web-01/recheck").status_code in (401, 302)
        assert client.post(f"{SERVICES}/web-01/x/recheck").status_code in (401, 302)

    def test_requires_permission(self, limited_client, db_session):
        assert limited_client.post(f"{HOSTS}/web-01/recheck").status_code == 403
        assert limited_client.post(f"{SERVICES}/web-01/x/recheck").status_code == 403
