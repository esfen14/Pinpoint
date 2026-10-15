"""
tests/unit/test_maintenance.py — Maintenance windows turned into Nagios downtime (app/maintenance.py).

Recurrence expansion (including a daylight-saving change), validation, the dispatcher
(lead time, de-duplication across restarts, bounded retries, failure reason) and cancel. The
Nagios pipe is replaced by _write_line, so the exact command lines are asserted.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from app import db
from app import maintenance as mw
from app.history_models import HostStateType, ServiceStateType
from app.nagios import commands as cmd
from app.system_models import ActivityLog, DeviceState, MaintenanceOccurrence, MaintenanceWindow
from tests.support.seed_helpers import _make_host, _make_service
from tests.unit.test_create_host_cfg import make_device

NOW = datetime(2026, 10, 20, 12, 0, 0)


def window(db_session, user, start, end, recurrence="none", tz="UTC", device=None, until=None):
    row = MaintenanceWindow(
        Start_At=start, End_At=end, Recurrence=recurrence, Time_Zone=tz, Comment="patching",
        Created_By=user.UserID, NetDiscoveryID=device.NetDiscoveryID if device else None,
        Recurrence_Until=until,
    )
    db_session.session.add(row)
    db_session.session.commit()
    return row


@pytest.fixture
def hosts(db_session):
    for name in ("web-01", "web-02"):
        _make_host(db_session, name, HostStateType.UP)
    _make_service(db_session, "web-01", "cpu/percent", ServiceStateType.OK)
    _make_service(db_session, "web-01", "http", ServiceStateType.OK)
    _make_service(db_session, "web-02", "http", ServiceStateType.OK)
    db_session.session.commit()


@pytest.fixture
def sent():
    lines = []

    def fake(line):
        lines.append(line.split("] ", 1)[1])
        return cmd.CommandResult(True)

    with patch.object(cmd, "_write_line", side_effect=fake):
        yield lines


@pytest.fixture
def pipe_down():
    down = cmd.CommandResult(False, cmd.UNAVAILABLE, "Nagios is not reading its command pipe.")
    with patch.object(cmd, "_write_line", return_value=down) as mock:
        yield mock


def only_occurrence():
    return db.session.scalars(sa.select(MaintenanceOccurrence)).one()


class TestRecurrence:

    def test_one_off_has_one_occurrence(self, db_session, admin_user):
        row = window(db_session, admin_user, NOW + timedelta(hours=1), NOW + timedelta(hours=2))
        assert mw.next_occurrence(row, NOW) == (row.Start_At, row.End_At)
        assert mw.next_occurrence(row, row.End_At) is None

    def test_running_window_is_still_next(self, db_session, admin_user):
        row = window(db_session, admin_user, NOW - timedelta(hours=1), NOW + timedelta(hours=1))
        assert mw.next_occurrence(row, NOW) == (row.Start_At, row.End_At)

    def test_daily_moves_to_the_next_day(self, db_session, admin_user):
        row = window(db_session, admin_user, datetime(2026, 10, 10, 2), datetime(2026, 10, 10, 3), "daily")
        assert mw.next_occurrence(row, NOW) == (datetime(2026, 10, 21, 2), datetime(2026, 10, 21, 3))

    def test_weekly_keeps_the_weekday(self, db_session, admin_user):
        row = window(db_session, admin_user, datetime(2026, 10, 7, 2), datetime(2026, 10, 7, 3), "weekly")
        assert mw.next_occurrence(row, NOW) == (datetime(2026, 10, 21, 2), datetime(2026, 10, 21, 3))

    def test_recurrence_until_ends_the_series(self, db_session, admin_user):
        row = window(db_session, admin_user, datetime(2026, 10, 10, 2), datetime(2026, 10, 10, 3), "daily",
                     until=datetime(2026, 10, 15))
        assert mw.next_occurrence(row, NOW) is None

    def test_daily_follows_local_time_across_a_daylight_saving_change(self, db_session, admin_user):
        # 02:00 in New York is 06:00 UTC while on EDT (UTC-4) and 07:00 UTC after the clocks go
        # back on 1 Nov 2026 (02:00 that day is already EST, UTC-5).
        row = window(db_session, admin_user, datetime(2026, 10, 30, 6), datetime(2026, 10, 30, 7),
                     "daily", tz="America/New_York")
        assert mw.occurrence_bounds(row, 1) == (datetime(2026, 10, 31, 6), datetime(2026, 10, 31, 7))
        assert mw.occurrence_bounds(row, 2) == (datetime(2026, 11, 1, 7), datetime(2026, 11, 1, 8))
        assert mw.occurrence_bounds(row, 3) == (datetime(2026, 11, 2, 7), datetime(2026, 11, 2, 8))

    def test_next_occurrence_is_not_skipped_by_the_change(self, db_session, admin_user):
        row = window(db_session, admin_user, datetime(2026, 10, 30, 6), datetime(2026, 10, 30, 7),
                     "daily", tz="America/New_York")
        assert mw.next_occurrence(row, datetime(2026, 11, 1, 8)) == (datetime(2026, 11, 2, 7), datetime(2026, 11, 2, 8))


class TestNoTimeZoneDatabase:
    """The appliance may have no tz database (a minimal image has no /usr/share/zoneinfo)."""

    def test_utc_works_without_one(self, db_session, admin_user):
        row = window(db_session, admin_user, datetime(2026, 10, 10, 2), datetime(2026, 10, 10, 3), "daily")
        with patch.object(mw, "ZoneInfo", side_effect=mw.ZoneInfoNotFoundError("UTC")):
            fields, message = mw.validate_window(
                {"startAt": "2026-10-21T02:00:00Z", "endAt": "2026-10-21T03:00:00Z", "comment": "x", "timeZone": "UTC"}, NOW)
            assert message is None and fields["Time_Zone"] == "UTC"
            assert mw.next_occurrence(row, NOW) == (datetime(2026, 10, 21, 2), datetime(2026, 10, 21, 3))

    def test_other_zones_are_refused_without_one(self, db_session):
        with patch.object(mw, "ZoneInfo", side_effect=mw.ZoneInfoNotFoundError("x")):
            fields, message = mw.validate_window(
                {"startAt": "2026-10-21T02:00:00Z", "endAt": "2026-10-21T03:00:00Z", "comment": "x", "timeZone": "Europe/Paris"}, NOW)
        assert fields is None and "time zone" in message


class TestValidate:

    def body(self, **over):
        data = {"startAt": "2026-10-21T02:00:00Z", "endAt": "2026-10-21T03:00:00Z", "comment": "patching",
                "deviceId": None, "recurrence": "none", "timeZone": "UTC"}
        data.update(over)
        return data

    def test_valid_body_is_converted_to_utc(self, db_session):
        fields, message = mw.validate_window(self.body(startAt="2026-10-21T04:00:00+02:00"), NOW)
        assert message is None
        assert fields["Start_At"] == datetime(2026, 10, 21, 2)

    @pytest.mark.parametrize("over, text", [
        ({"startAt": "2026-10-21T02:00:00"}, "UTC offset"),
        ({"startAt": "later"}, "ISO 8601"),
        ({"endAt": "2026-10-21T01:00:00Z"}, "after startAt"),
        ({"startAt": "2026-10-19T02:00:00Z", "endAt": "2026-10-19T03:00:00Z"}, "future"),
        ({"recurrence": "monthly"}, "recurrence"),
        ({"endAt": "2026-12-21T03:00:00Z"}, "30 days"),
        ({"recurrence": "daily", "endAt": "2026-10-22T03:00:00Z"}, "daily window"),
        ({"recurrenceUntil": "2026-12-01T00:00:00Z"}, "only applies"),
        ({"recurrence": "daily", "recurrenceUntil": "2028-12-01T00:00:00Z"}, "366 days"),
        ({"timeZone": "Mars/Base"}, "time zone"),
        ({"comment": "  "}, "comment"),
        ({"comment": "a\nb"}, "line breaks"),
        ({"comment": "x" * 201}, "at most"),
        ({"deviceId": "7"}, "deviceId"),
        ({"deviceId": 9999}, "not found"),
    ])
    def test_invalid_bodies(self, db_session, over, text):
        fields, message = mw.validate_window(self.body(**over), NOW)
        assert fields is None and text in message

    def test_paused_device_is_refused(self, db_session, admin_user):
        device = make_device(db_session, admin_user, "web-01", "10.0.0.1")
        device.Include_Device_In_Scanning = False
        db_session.session.commit()
        fields, message = mw.validate_window(self.body(deviceId=device.NetDiscoveryID), NOW)
        assert fields is None and "paused" in message

    def test_not_an_object(self, db_session):
        assert mw.validate_window([], NOW)[1] == "Request body must be a JSON object."


class TestDispatch:

    def test_sends_host_and_service_downtime_before_the_start(self, db_session, admin_user, hosts, sent):
        device = make_device(db_session, admin_user, "web-01", "10.0.0.1")
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1), device=device)
        assert mw.dispatch_due_windows(NOW) == 1

        start, end = mw.epoch(row.Start_At), mw.epoch(row.End_At)
        tag = f"PinPoint maintenance window {row.WindowID} starting {start}"
        assert sent == [
            f"SCHEDULE_HOST_DOWNTIME;web-01;{start};{end};1;0;0;PinPoint;{tag}",
            f"SCHEDULE_SVC_DOWNTIME;web-01;cpu/percent;{start};{end};1;0;0;PinPoint;{tag}",
            f"SCHEDULE_SVC_DOWNTIME;web-01;http;{start};{end};1;0;0;PinPoint;{tag}",
        ]
        assert only_occurrence().Status == mw.SENT
        assert row.Last_Occurrence_Sent == row.Start_At

    def test_all_devices_scope_covers_every_host(self, db_session, admin_user, hosts, sent):
        window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        mw.dispatch_due_windows(NOW)
        assert [line.split(";")[1] for line in sent if line.startswith("SCHEDULE_HOST")] == ["web-01", "web-02"]
        assert len(sent) == 5

    def test_waits_until_the_lead_time(self, db_session, admin_user, hosts, sent):
        window(db_session, admin_user, NOW + timedelta(hours=2), NOW + timedelta(hours=3))
        assert mw.dispatch_due_windows(NOW) == 0
        assert sent == [] and db_session.session.scalars(sa.select(MaintenanceOccurrence)).all() == []

    def test_second_run_and_a_restart_do_not_send_again(self, db_session, admin_user, hosts, sent):
        window(db_session, admin_user, datetime(2026, 10, 20, 12, 5), datetime(2026, 10, 20, 13), "daily")
        mw.dispatch_due_windows(NOW)
        first = len(sent)
        mw.dispatch_due_windows(NOW + timedelta(minutes=1))
        db.session.expire_all()  # a new process sees only the database
        mw.dispatch_due_windows(NOW + timedelta(minutes=2))
        assert len(sent) == first
        assert len(db_session.session.scalars(sa.select(MaintenanceOccurrence)).all()) == 1

    def test_recurring_window_sends_the_next_occurrence_once(self, db_session, admin_user, hosts, sent):
        window(db_session, admin_user, datetime(2026, 10, 20, 12, 5), datetime(2026, 10, 20, 13), "daily")
        mw.dispatch_due_windows(NOW)
        sent.clear()
        mw.dispatch_due_windows(datetime(2026, 10, 21, 11, 56))
        mw.dispatch_due_windows(datetime(2026, 10, 21, 11, 57))
        assert len([line for line in sent if line.startswith("SCHEDULE_HOST")]) == 2  # web-01, web-02, once
        assert len(db_session.session.scalars(sa.select(MaintenanceOccurrence)).all()) == 2

    def test_finished_window_is_completed(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW - timedelta(hours=2), NOW - timedelta(hours=1))
        mw.dispatch_due_windows(NOW)
        assert row.Status == mw.COMPLETED and sent == []

    def test_cancelled_window_is_ignored(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        row.Status = mw.CANCELLED
        db_session.session.commit()
        assert mw.dispatch_due_windows(NOW) == 0 and sent == []

    def test_writes_an_audit_entry(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        mw.dispatch_due_windows(NOW)
        actions = db.session.scalars(sa.select(ActivityLog.Action_Type)).all()
        assert any(f"Maintenance window {row.WindowID} downtime sent" in action for action in actions)


class TestFailure:

    def test_retries_then_fails_with_the_reason(self, db_session, admin_user, hosts, pipe_down):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        for minute in range(mw.MAX_ATTEMPTS + 2):
            mw.dispatch_due_windows(NOW + timedelta(minutes=minute))
        occurrence = only_occurrence()
        assert occurrence.Status == mw.FAILED
        assert occurrence.Attempts == mw.MAX_ATTEMPTS
        assert "not reading its command pipe" in occurrence.Last_Error
        assert row.Last_Occurrence_Sent is None
        actions = db.session.scalars(sa.select(ActivityLog.Action_Type)).all()
        assert any("failed" in action for action in actions)

    def test_a_retry_that_succeeds_clears_the_error(self, db_session, admin_user, hosts):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        down = cmd.CommandResult(False, cmd.UNAVAILABLE, "Nagios is not reading its command pipe.")
        with patch.object(cmd, "_write_line", return_value=down):
            mw.dispatch_due_windows(NOW)
        assert only_occurrence().Status == mw.PENDING
        lines = []
        with patch.object(cmd, "_write_line", side_effect=lambda line: lines.append(line) or cmd.CommandResult(True)):
            mw.dispatch_due_windows(NOW + timedelta(minutes=1))
        occurrence = only_occurrence()
        assert occurrence.Status == mw.SENT and occurrence.Last_Error is None
        # The retry first deletes whatever the earlier attempt left.
        assert any("DEL_DOWNTIME_BY_HOST_NAME;web-01;;;" in line for line in lines)
        assert row.Last_Occurrence_Sent == row.Start_At

    def test_a_paused_device_fails_with_a_reason(self, db_session, admin_user, hosts, sent):
        device = make_device(db_session, admin_user, "web-01", "10.0.0.1")
        window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1), device=device)
        device.Include_Device_In_Scanning = False
        db_session.session.commit()
        mw.dispatch_due_windows(NOW)
        assert only_occurrence().Last_Error == "The device is paused."
        assert sent == []

    def test_a_device_missing_from_nagios_fails_with_a_reason(self, db_session, admin_user, sent):
        device = make_device(db_session, admin_user, "ghost", "10.0.0.9")
        window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1), device=device)
        mw.dispatch_due_windows(NOW)
        assert "not in the latest Nagios status" in only_occurrence().Last_Error


class TestCancel:

    def test_cancel_deletes_pending_and_running_downtime(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        mw.dispatch_due_windows(NOW)
        sent.clear()

        results = mw.cancel_live_occurrences(row, NOW, delete_rows=False)

        tag = f"PinPoint maintenance window {row.WindowID} starting {mw.epoch(row.Start_At)}"
        assert sent == [f"DEL_DOWNTIME_BY_HOST_NAME;web-01;;;{tag}", f"DEL_DOWNTIME_BY_HOST_NAME;web-02;;;{tag}"]
        assert all(result.ok for result in results)
        assert only_occurrence().Status == mw.OCC_CANCELLED

    def test_past_occurrences_are_left_alone(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW - timedelta(hours=3), NOW - timedelta(hours=2))
        db_session.session.add(MaintenanceOccurrence(
            WindowID=row.WindowID, Start_At=row.Start_At, End_At=row.End_At, Status=mw.SENT, Attempts=1))
        db_session.session.commit()
        assert mw.cancel_live_occurrences(row, NOW, delete_rows=True) == []
        assert only_occurrence().Status == mw.SENT and sent == []

    def test_delete_rows_lets_an_edited_window_schedule_again(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        mw.dispatch_due_windows(NOW)
        mw.cancel_live_occurrences(row, NOW, delete_rows=True)
        db_session.session.commit()
        assert db_session.session.scalars(sa.select(MaintenanceOccurrence)).all() == []
        sent.clear()
        mw.dispatch_due_windows(NOW + timedelta(minutes=1))
        assert any(line.startswith("SCHEDULE_HOST_DOWNTIME") for line in sent)

    def test_a_pipe_failure_is_reported(self, db_session, admin_user, hosts, sent):
        row = window(db_session, admin_user, NOW + timedelta(minutes=5), NOW + timedelta(hours=1))
        mw.dispatch_due_windows(NOW)
        down = cmd.CommandResult(False, cmd.UNAVAILABLE, "Nagios is not reading its command pipe.")
        with patch.object(cmd, "_write_line", return_value=down):
            results = mw.cancel_live_occurrences(row, NOW, delete_rows=False)
        assert results and not any(result.ok for result in results)
