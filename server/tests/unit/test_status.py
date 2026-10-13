"""
tests/unit/test_status.py — Tests for the Nagios status parser in
app/nagios/status.py.

Payloads mirror what statusjson.cgi actually returns with
formatoptions=enumerate: lowercase state names, millisecond timestamps,
'max_attempts', and perf data under 'perf_data'. check_command is not in
statusjson.cgi, so it is looked up from objectjson.cgi's servicelist.
Nagios is never contacted — requests.get is patched.
"""
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

import pytest

import requests
import sqlalchemy as sa

from app.nagios.status import (
    get_check_commands,
    get_status,
    insert_host_status_data,
    insert_programstatus_data,
    insert_service_status_data,
)
from app.system_models import AlertAcknowledgement, AckHistory, AckAction
from app.history_models import (
    HostPerfData,
    HostStatus,
    HostStateType,
    ProgramStatus,
    ServicePerfData,
    ServiceStatus,
    ServiceStateType,
)


HOSTNAME = "parser-test-host"


def host_payload(**overrides):
    """Build a hostlist entry in statusjson.cgi's enumerated shape."""
    payload = {
        "name": HOSTNAME,
        "status": "up",
        "state_type": "hard",
        "plugin_output": "PING OK - Packet loss = 0%, RTA = 0.04 ms",
        "perf_data": "rta=0.039000ms;3000.000000;5000.000000;0.000000 pl=0%;80;100;0",
        "last_update": 1_790_418_781_000,
        "last_check": 1_790_418_781_000,
        "next_check": 1_790_419_081_000,
        "current_attempt": 1,
        "max_attempts": 10,
        "acknowledgement_type": "none",
        "is_flapping": False,
        "notifications_enabled": True,
    }
    payload.update(overrides)
    return payload


def service_payload(**overrides):
    """Build a servicelist entry in statusjson.cgi's enumerated shape."""
    payload = {
        "status": "ok",
        "state_type": "hard",
        "plugin_output": "PING OK - Packet loss = 0%, RTA = 0.05 ms",
        "perf_data": "rta=0.051000ms;100.000000;500.000000;0.000000 pl=0%;20;60;0",
        "last_update": 1_790_418_781_000,
        "last_check": 1_790_418_781_000,
        "next_check": 1_790_419_081_000,
        "current_attempt": 1,
        "max_attempts": 4,
        "acknowledgement_type": "none",
        "is_flapping": False,
        "notifications_enabled": True,
    }
    payload.update(overrides)
    return payload


def get_service(db_session, service):
    return db_session.session.scalar(
        sa.select(ServiceStatus).where(
            ServiceStatus.Hostname == HOSTNAME, ServiceStatus.Service == service
        )
    )


# ==========================================================
# SERVICE STATUS
# ==========================================================

class TestServiceStatusParsing:

    def test_lowercase_states_are_mapped(self, db_session):
        cases = {
            "svc-ok": ("ok", ServiceStateType.OK),
            "svc-warning": ("warning", ServiceStateType.WARNING),
            "svc-critical": ("critical", ServiceStateType.CRITICAL),
            "svc-unknown": ("unknown", ServiceStateType.UNKNOWN),
        }
        for service, (status, _expected) in cases.items():
            insert_service_status_data(HOSTNAME, service, service_payload(status=status))

        for service, (_status, expected) in cases.items():
            assert get_service(db_session, service).Current_State == expected

    def test_max_attempts_is_read(self, db_session):
        insert_service_status_data(HOSTNAME, "PING", service_payload(max_attempts=4))

        assert get_service(db_session, "PING").Max_Attempts == 4

    def test_perf_data_is_stored(self, db_session):
        insert_service_status_data(HOSTNAME, "PING", service_payload())

        row = get_service(db_session, "PING")
        perf = {
            p.Metric: p
            for p in db_session.session.scalars(
                sa.select(ServicePerfData).where(ServicePerfData.ServiceStatusID == row.ServiceStatusID)
            )
        }
        assert set(perf) == {"rta", "pl"}
        assert perf["rta"].Measured_Value == 0.051
        assert perf["rta"].Unit == "ms"
        assert perf["rta"].Warning_Threshold == 100.0
        assert perf["rta"].Critical_Threshold == 500.0

    def test_missing_perf_data_stores_no_rows(self, db_session):
        insert_service_status_data(HOSTNAME, "no-perf", service_payload(perf_data=""))

        row = get_service(db_session, "no-perf")
        count = db_session.session.scalar(
            sa.select(sa.func.count()).select_from(ServicePerfData)
            .where(ServicePerfData.ServiceStatusID == row.ServiceStatusID)
        )
        assert count == 0

    def test_same_check_is_not_inserted_twice(self, db_session):
        insert_service_status_data(HOSTNAME, "PING", service_payload())
        insert_service_status_data(HOSTNAME, "PING", service_payload(last_update=1_790_418_841_000))
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(ServiceStatus)) == 1
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(ServicePerfData)) == 2

        insert_service_status_data(HOSTNAME, "PING", service_payload(last_check=1_790_419_081_000))
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(ServiceStatus)) == 2
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(ServicePerfData)) == 4


# ==========================================================
# HOST STATUS
# ==========================================================

class TestProgramStatusParsing:
    # Field names as a live Nagios 4.5 statusjson.cgi programstatus returns them.
    PAYLOAD = {
        "version": "4.5.11",
        "nagios_pid": 175347,
        "daemon_mode": True,
        "program_start": 1790491216000,
        "enable_notifications": False,
        "execute_service_checks": True,
        "accept_passive_service_checks": False,
        "execute_host_checks": True,
        "accept_passive_host_checks": True,
        "enable_flap_detection": True,
    }

    def test_check_switches_use_statusjson_names(self, db_session):
        insert_programstatus_data(self.PAYLOAD)

        row = db_session.session.scalar(sa.select(ProgramStatus))
        assert row.Active_Host_Checks_Enabled is True
        assert row.Active_Service_Checks_Enabled is True
        assert row.Passive_Host_Checks_Enabled is True
        assert row.Passive_Service_Checks_Enabled is False
        assert row.Enable_Notifications is False
        assert row.Enable_Flap_Detection is True


class TestHostStatusParsing:

    def get_host(self, db_session):
        return db_session.session.scalar(sa.select(HostStatus).where(HostStatus.Hostname == HOSTNAME))

    def test_state_and_max_attempts(self, db_session):
        insert_host_status_data(host_payload(status="down", max_attempts=10))

        row = self.get_host(db_session)
        assert row.Current_State == HostStateType.DOWN
        assert row.Max_Attempts == 10

    def test_perf_data_is_stored(self, db_session):
        insert_host_status_data(host_payload())

        row = self.get_host(db_session)
        metrics = set(db_session.session.scalars(
            sa.select(HostPerfData.Metric).where(HostPerfData.HostStatusID == row.HostStatusID)
        ))
        assert metrics == {"rta", "pl"}

    def test_same_check_is_not_inserted_twice(self, db_session):
        insert_host_status_data(host_payload())
        insert_host_status_data(host_payload(last_update=1_790_418_841_000))
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(HostStatus)) == 1
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(HostPerfData)) == 2

        insert_host_status_data(host_payload(last_check=1_790_419_081_000))
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(HostStatus)) == 2
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(HostPerfData)) == 4


# ==========================================================
# CHECK COMMAND LOOKUP (objectjson.cgi)
# ==========================================================

OBJECT_URL = "http://nagios.test/nagios/cgi-bin/objectjson.cgi"


def json_response(payload):
    """Build a mock requests response returning payload from .json()."""
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def object_servicelist(services):
    """Build an objectjson.cgi servicelist payload from {host: {svc: command}}."""
    servicelist = {}
    for hostname, commands in services.items():
        servicelist[hostname] = {}
        for service, command in commands.items():
            servicelist[hostname][service] = {"host_name": hostname, "check_command": command}
    return {"data": {"servicelist": servicelist}}


class TestGetCheckCommands:

    def test_maps_host_and_service_to_command(self, db_session):
        payload = object_servicelist({
            "localhost": {"Current Load": "check_local_load!5.0,4.0,3.0!10.0,6.0,4.0"},
            HOSTNAME: {"PING": "pinpoint_nd_ping!100!500"},
        })
        with patch("app.nagios.status.requests.get", return_value=json_response(payload)) as get:
            result = get_check_commands(OBJECT_URL, ("user", "pass"))

        assert result == {
            ("localhost", "Current Load"): "check_local_load!5.0,4.0,3.0!10.0,6.0,4.0",
            (HOSTNAME, "PING"): "pinpoint_nd_ping!100!500",
        }
        assert get.call_args.kwargs["params"] == {"query": "servicelist", "details": "true"}

    def test_request_failure_returns_empty(self, db_session):
        with patch("app.nagios.status.requests.get", side_effect=requests.ConnectionError("down")):
            assert get_check_commands(OBJECT_URL, ("user", "pass")) == {}

    def test_malformed_payload_returns_empty(self, db_session):
        with patch("app.nagios.status.requests.get", return_value=json_response({"data": {}})):
            assert get_check_commands(OBJECT_URL, ("user", "pass")) == {}


class TestGetStatusCheckCommand:

    def fake_nagios(self, object_payload):
        """Return a requests.get replacement answering statusjson/objectjson queries."""
        def fake_get(url, params=None, **kwargs):
            query = params["query"]
            if url == OBJECT_URL:
                if isinstance(object_payload, Exception):
                    raise object_payload
                return object_payload
            if query == "programstatus":
                return json_response({"data": {"programstatus": {"version": "4.5.0"}}})
            if query == "hostlist":
                return json_response({"data": {"hostlist": {HOSTNAME: host_payload()}}})
            return json_response({"data": {"servicelist": {HOSTNAME: {
                "PING": service_payload(),
                "not-in-objects": service_payload(),
            }}}})
        return fake_get

    def poll(self, app, object_payload):
        with patch.dict(app.config, {"NAGIOS_OBJECT_URL": OBJECT_URL}), \
                patch("app.nagios.status.requests.get", side_effect=self.fake_nagios(object_payload)):
            get_status()

    def test_check_command_name_is_stored(self, app, db_session):
        payload = json_response(object_servicelist({HOSTNAME: {"PING": "pinpoint_nd_ping!100!500"}}))
        self.poll(app, payload)

        # Only the command name is kept — arguments may carry secrets.
        assert get_service(db_session, "PING").Check_Command == "pinpoint_nd_ping"
        assert get_service(db_session, "not-in-objects").Check_Command is None

    def test_object_lookup_failure_still_stores_status(self, app, db_session):
        self.poll(app, requests.ConnectionError("objectjson down"))

        row = get_service(db_session, "PING")
        assert row is not None
        assert row.Check_Command is None


# ==========================================================
# PENDING AND UNKNOWN HOST STATUS
# ==========================================================

class TestPendingHosts:
    """Nagios lists a host as pending until its first check has run: there is no state yet."""

    def host_row(self, db_session, name):
        return db_session.session.scalar(sa.select(HostStatus).where(HostStatus.Hostname == name))

    def test_pending_host_is_skipped_without_an_error(self, db_session, caplog):
        with caplog.at_level("ERROR"):
            insert_host_status_data(host_payload(name="new-host", status="pending"))

        assert self.host_row(db_session, "new-host") is None
        assert "Failed to insert host status" not in caplog.text

    def test_unknown_status_is_logged_and_skipped(self, db_session, caplog):
        # Anything that is not up, down, unreachable or pending is unexpected: say so, keep going.
        with caplog.at_level("ERROR"):
            insert_host_status_data(host_payload(name="odd-host", status="not-a-state"))

        assert self.host_row(db_session, "odd-host") is None
        assert "Failed to insert host status" in caplog.text

    def test_pending_host_does_not_block_the_rest_of_the_poll(self, app, db_session):
        hostlist = {
            "new-host": host_payload(name="new-host", status="pending"),
            "ready-host": host_payload(name="ready-host", status="up"),
        }

        def fake_get(url, params=None, **kwargs):
            query = params["query"]
            if url == OBJECT_URL:
                return json_response(object_servicelist({}))
            if query == "programstatus":
                return json_response({"data": {"programstatus": {"version": "4.5.0"}}})
            if query == "hostlist":
                return json_response({"data": {"hostlist": hostlist}})
            return json_response({"data": {"servicelist": {}}})

        with patch.dict(app.config, {"NAGIOS_OBJECT_URL": OBJECT_URL}), \
                patch("app.nagios.status.requests.get", side_effect=fake_get):
            get_status()

        assert self.host_row(db_session, "new-host") is None
        ready = self.host_row(db_session, "ready-host")
        assert ready is not None
        assert ready.Current_State == HostStateType.UP


class TestPollAckResolution:
    """Only a complete, fresh Nagios poll can retire an active Pinpoint ack."""

    def ack(self, db_session, user_id, hostname=HOSTNAME, service=None):
        row = AlertAcknowledgement(
            Hostname=hostname, Service_Name=service, Comment="Investigating",
            AcknowledgedBy=user_id, Acknowledged_At=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        db_session.session.add(row)
        db_session.session.commit()
        return row

    def poll(self, app, hosts=None, services=None, fail_query=None):
        checked = int(datetime.now(timezone.utc).timestamp() * 1000)
        if hosts is None:
            hosts = {HOSTNAME: host_payload(last_check=checked, last_update=checked)}
        if services is None:
            services = {HOSTNAME: {"PING": service_payload(last_check=checked, last_update=checked)}}

        def fake_get(url, params=None, **kwargs):
            query = params["query"]
            if query == fail_query:
                raise requests.ConnectionError("Nagios unavailable")
            if query == "programstatus":
                return json_response({"data": {"programstatus": {"version": "4.5.0", "program_start": 1_790_418_000_000}}})
            if query == "hostlist":
                return json_response({"data": {"hostlist": hosts}})
            if url == OBJECT_URL:
                return json_response(object_servicelist({}))
            return json_response({"data": {"servicelist": services}})

        with patch.dict(app.config, {"NAGIOS_OBJECT_URL": OBJECT_URL}), \
                patch("app.nagios.status.requests.get", side_effect=fake_get):
            get_status()

    def rows(self, db_session):
        return db_session.session.scalars(sa.select(AckHistory).order_by(AckHistory.AckHistoryID)).all()

    @pytest.mark.parametrize("service", [None, "PING"])
    def test_recovery_clears_one_ack_without_actor_and_repeat_is_idempotent(
        self, app, db_session, admin_user, service
    ):
        self.ack(db_session, admin_user.UserID, service=service)
        self.poll(app)
        assert db_session.session.scalars(sa.select(AlertAcknowledgement)).all() == []
        rows = self.rows(db_session)
        assert len(rows) == 1
        assert (rows[0].Hostname, rows[0].Service_Name, rows[0].Action, rows[0].ActorUserID) == (
            HOSTNAME, service, AckAction.AUTO_RESOLVED, None
        )
        self.poll(app)
        assert len(self.rows(db_session)) == 1

    def test_still_failing_service_and_host_are_kept(self, app, db_session, admin_user):
        self.ack(db_session, admin_user.UserID)
        self.ack(db_session, admin_user.UserID, service="PING")
        checked = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.poll(app, hosts={HOSTNAME: host_payload(status="down", last_check=checked)},
                  services={HOSTNAME: {"PING": service_payload(status="critical", last_check=checked)}})
        assert len(db_session.session.scalars(sa.select(AlertAcknowledgement)).all()) == 2
        assert self.rows(db_session) == []

    @pytest.mark.parametrize("fail_query", ["programstatus", "hostlist", "servicelist"])
    def test_failed_poll_does_not_clear(self, app, db_session, admin_user, fail_query):
        self.ack(db_session, admin_user.UserID, service="PING")
        self.poll(app, fail_query=fail_query)
        assert len(db_session.session.scalars(sa.select(AlertAcknowledgement)).all()) == 1
        assert self.rows(db_session) == []

    def test_empty_poll_and_deleted_target_are_ignored(self, app, db_session, admin_user):
        self.ack(db_session, admin_user.UserID, hostname="deleted", service="PING")
        self.ack(db_session, admin_user.UserID, service="PING")
        self.poll(app, hosts={}, services={})
        self.poll(app)
        remaining = db_session.session.scalars(sa.select(AlertAcknowledgement)).all()
        assert [(row.Hostname, row.Service_Name) for row in remaining] == [("deleted", "PING")]
        assert len(self.rows(db_session)) == 1

    def test_stale_check_cannot_clear_ack(self, app, db_session, admin_user):
        self.ack(db_session, admin_user.UserID, service="PING")
        stale = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp() * 1000)
        self.poll(app, services={HOSTNAME: {"PING": service_payload(last_check=stale, last_update=stale)}})
        assert len(db_session.session.scalars(sa.select(AlertAcknowledgement)).all()) == 1
        assert self.rows(db_session) == []

    def test_unchecked_recovery_never_clears_ack(self, app, db_session, admin_user):
        self.ack(db_session, admin_user.UserID, service="PING")
        self.poll(app, services={HOSTNAME: {"PING": service_payload(last_check=None)}})
        assert len(db_session.session.scalars(sa.select(AlertAcknowledgement)).all()) == 1
        assert self.rows(db_session) == []

    def test_re_failure_after_recovery_can_be_acknowledged_again(self, app, db_session, admin_user):
        self.ack(db_session, admin_user.UserID, service="PING")
        self.poll(app)
        checked = int(datetime.now(timezone.utc).timestamp() * 1000) + 1000
        self.poll(app, services={HOSTNAME: {"PING": service_payload(status="critical", last_check=checked)}})
        self.ack(db_session, admin_user.UserID, service="PING")
        assert len(self.rows(db_session)) == 1
        assert len(db_session.session.scalars(sa.select(AlertAcknowledgement)).all()) == 1

    def test_history_commit_failure_rolls_back_deletion(self, app, db_session, admin_user):
        self.ack(db_session, admin_user.UserID, service="PING")
        real_commit = db_session.session.commit

        def fail_commit():
            raise RuntimeError("commit failed")

        with patch.object(db_session.session, "commit", side_effect=fail_commit):
            self.poll(app)
        assert len(db_session.session.scalars(sa.select(AlertAcknowledgement)).all()) == 1
        assert self.rows(db_session) == []
