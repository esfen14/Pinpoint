"""
tests/unit/test_nagios_commands.py — The Nagios command channel (app/nagios/commands.py).

A real FIFO stands in for nagios.cmd. Covers the line each allowed command writes,
injection attempts (newline, NUL, semicolon, very long input), refusal of names not in
the snapshot, and a missing, stopped (no reader) or non-pipe command file.
"""
import os

import pytest

from app.nagios import commands as cmd

HOSTS = {"web-01"}
SERVICES = {("web-01", "cpu/percent")}
TARGETS = (HOSTS, SERVICES)


@pytest.fixture
def pipe(app, db_session, tmp_path):
    """A FIFO with a reader, wired in as NAGIOS_COMMAND_FILE; yields a function returning written lines."""
    path = tmp_path / "nagios.cmd"
    os.mkfifo(path)
    reader = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    old = app.config["NAGIOS_COMMAND_FILE"]
    app.config["NAGIOS_COMMAND_FILE"] = path

    def lines():
        try:
            return os.read(reader, 65536).decode().splitlines()
        except BlockingIOError:
            return []

    yield lines
    app.config["NAGIOS_COMMAND_FILE"] = old
    os.close(reader)


def body(line):
    """Drop the [epoch] prefix."""
    assert line.startswith("[") and "] " in line
    return line.split("] ", 1)[1]


class TestCommandLines:

    def test_acknowledge_host(self, pipe):
        assert cmd.acknowledge_host_problem("web-01", "on it", "Jane Doe", TARGETS).ok
        assert body(pipe()[0]) == "ACKNOWLEDGE_HOST_PROBLEM;web-01;1;0;1;Jane Doe;on it"

    def test_acknowledge_service(self, pipe):
        assert cmd.acknowledge_service_problem("web-01", "cpu/percent", "on it", "Jane", TARGETS).ok
        assert body(pipe()[0]) == "ACKNOWLEDGE_SVC_PROBLEM;web-01;cpu/percent;1;0;1;Jane;on it"

    def test_remove_acknowledgements(self, pipe):
        assert cmd.remove_host_acknowledgement("web-01", TARGETS).ok
        assert cmd.remove_service_acknowledgement("web-01", "cpu/percent", TARGETS).ok
        sent = [body(line) for line in pipe()]
        assert sent == ["REMOVE_HOST_ACKNOWLEDGEMENT;web-01",
                        "REMOVE_SVC_ACKNOWLEDGEMENT;web-01;cpu/percent"]

    def test_forced_checks(self, pipe):
        assert cmd.schedule_forced_host_check("web-01", TARGETS).ok
        assert cmd.schedule_forced_service_check("web-01", "cpu/percent", TARGETS).ok
        host, service = [body(line) for line in pipe()]
        assert host.startswith("SCHEDULE_FORCED_HOST_CHECK;web-01;")
        assert service.startswith("SCHEDULE_FORCED_SVC_CHECK;web-01;cpu/percent;")

    def test_downtime(self, pipe):
        assert cmd.schedule_host_downtime("web-01", 100, 200, "patching", "Jane", TARGETS).ok
        assert cmd.schedule_service_downtime("web-01", "cpu/percent", 100, 200, "patching", "Jane", TARGETS).ok
        host, service = [body(line) for line in pipe()]
        assert host == "SCHEDULE_HOST_DOWNTIME;web-01;100;200;1;0;0;Jane;patching"
        assert service == "SCHEDULE_SVC_DOWNTIME;web-01;cpu/percent;100;200;1;0;0;Jane;patching"

    @pytest.mark.parametrize("start, end", [(0, 10), (200, 100), (100, 100), ("1", 5), (True, 5)])
    def test_bad_downtime_window_is_refused(self, pipe, start, end):
        result = cmd.schedule_host_downtime("web-01", start, end, "x", "Jane", TARGETS)
        assert not result.ok and result.error == cmd.INVALID
        assert pipe() == []


class TestCancelDowntime:

    def test_cancel_by_host_and_comment(self, pipe):
        assert cmd.cancel_downtime_by_host_name("web-01", "PinPoint maintenance window 3 1000", TARGETS).ok
        assert body(pipe()[0]) == "DEL_DOWNTIME_BY_HOST_NAME;web-01;;;PinPoint maintenance window 3 1000"

    @pytest.mark.parametrize("comment", ["", "  ", "a\nSHUTDOWN", "a\0b"])
    def test_cancel_needs_a_safe_comment(self, pipe, comment):
        # An empty comment would delete every downtime of the host.
        result = cmd.cancel_downtime_by_host_name("web-01", comment, TARGETS)
        assert not result.ok and result.error == cmd.INVALID
        assert pipe() == []

    def test_cancel_unknown_host_is_refused(self, pipe):
        result = cmd.cancel_downtime_by_host_name("nope", "tag", TARGETS)
        assert not result.ok and result.error == cmd.UNKNOWN_TARGET
        assert pipe() == []


class TestInjection:

    @pytest.mark.parametrize("bad", ["a\nb", "a\rb", "a\0b"])
    def test_comment_control_characters_are_refused(self, pipe, bad):
        result = cmd.acknowledge_host_problem("web-01", bad, "Jane", TARGETS)
        assert not result.ok and result.error == cmd.INVALID
        assert pipe() == []

    @pytest.mark.parametrize("bad", ["web-01\nSHUTDOWN", "web-01;x", "web\0", ""])
    def test_host_names_are_refused(self, pipe, bad):
        result = cmd.remove_host_acknowledgement(bad, ({bad}, set()))
        assert not result.ok and result.error == cmd.INVALID
        assert pipe() == []

    def test_service_name_with_separator_is_refused(self, pipe):
        name = "a;b"
        result = cmd.remove_service_acknowledgement("web-01", name, (HOSTS, {("web-01", name)}))
        assert not result.ok and pipe() == []

    def test_semicolon_in_comment_cannot_add_fields(self, pipe):
        cmd.acknowledge_host_problem("web-01", "a;b;c", "Jane", TARGETS)
        assert body(pipe()[0]).endswith(";Jane;a,b,c")

    def test_author_cannot_break_the_line(self, pipe):
        cmd.acknowledge_host_problem("web-01", "x", "Jane\nSHUTDOWN_PROGRAM;x", TARGETS)
        sent = pipe()
        assert len(sent) == 1 and "\n" not in sent[0]

    def test_long_comment_is_capped(self, pipe):
        assert cmd.acknowledge_host_problem("web-01", "x" * 100000, "Jane", TARGETS).ok
        sent = pipe()
        assert len(sent) == 1 and len(sent[0]) < cmd.MAX_LINE_BYTES
        assert sent[0].endswith("x" * cmd.MAX_COMMENT_CHARS)

    def test_very_long_name_is_refused(self, pipe):
        name = "h" * 5000
        result = cmd.remove_host_acknowledgement(name, ({name}, set()))
        assert not result.ok and pipe() == []


class TestTargetsMustBeKnown:

    def test_unknown_host_is_refused(self, pipe):
        result = cmd.schedule_forced_host_check("nope", TARGETS)
        assert not result.ok and result.error == cmd.UNKNOWN_TARGET
        assert pipe() == []

    def test_unknown_service_is_refused(self, pipe):
        result = cmd.schedule_forced_service_check("web-01", "nope", TARGETS)
        assert result.error == cmd.UNKNOWN_TARGET and pipe() == []

    def test_snapshot_is_read_from_history_when_not_given(self, pipe, db_session):
        from tests.support.seed_helpers import _make_host
        _make_host(db_session, "real-host")
        db_session.session.commit()
        assert cmd.schedule_forced_host_check("real-host").ok
        assert cmd.schedule_forced_host_check("web-01").error == cmd.UNKNOWN_TARGET


class TestPipeProblems:

    def test_missing_pipe(self, app, db_session, tmp_path):
        app.config["NAGIOS_COMMAND_FILE"] = tmp_path / "missing"
        result = cmd.schedule_forced_host_check("web-01", TARGETS)
        assert not result.ok and result.error == cmd.UNAVAILABLE

    def test_regular_file_is_not_a_pipe(self, app, db_session, tmp_path):
        path = tmp_path / "plain"
        path.write_text("")
        app.config["NAGIOS_COMMAND_FILE"] = path
        result = cmd.schedule_forced_host_check("web-01", TARGETS)
        assert result.error == cmd.UNAVAILABLE
        assert path.read_text() == ""

    def test_no_reader_returns_at_once(self, app, db_session, tmp_path):
        path = tmp_path / "nagios.cmd"
        os.mkfifo(path)
        app.config["NAGIOS_COMMAND_FILE"] = path
        result = cmd.schedule_forced_host_check("web-01", TARGETS)
        assert not result.ok and result.error == cmd.UNAVAILABLE

    def test_full_pipe_times_out(self, pipe, monkeypatch):
        monkeypatch.setattr(cmd, "WRITE_TIMEOUT_SECONDS", 0.2)
        sent = 0
        while cmd.schedule_forced_host_check("web-01", TARGETS).ok and sent < 5000:
            sent += 1  # nobody reads, so the 64 KiB pipe fills
        assert cmd.schedule_forced_host_check("web-01", TARGETS).error == cmd.TIMEOUT


class TestSyncFields:

    def test_success(self, app, db_session):
        assert cmd.sync_fields(1, [cmd.CommandResult(True)], "x") == {
            "nagios_synced": True, "nagios_message": None}

    def test_failure_names_the_consequence(self, app, db_session, admin_user):
        fields = cmd.sync_fields(
            admin_user.UserID, [cmd.CommandResult(False, cmd.UNAVAILABLE, "Nagios is down.")], "x")
        assert fields["nagios_synced"] is False
        assert "Notifications may continue" in fields["nagios_message"]


class TestCustomNotifications:
    """SEND_CUSTOM_*_NOTIFICATION lines (#153). The pipe write is replaced, so no FIFO is needed."""

    @pytest.fixture
    def sent(self, app, monkeypatch):
        lines = []
        monkeypatch.setattr(cmd, "_write_line", lambda line: lines.append(line) or cmd._ok())
        return lines

    def test_service_notification_is_not_forced(self, app, sent):
        assert cmd.send_custom_service_notification("web-01", "cpu/percent", "Automatic recovery failed", TARGETS).ok
        assert body(sent[0]) == "SEND_CUSTOM_SVC_NOTIFICATION;web-01;cpu/percent;0;PinPoint;Automatic recovery failed"

    def test_host_notification_is_not_forced(self, app, sent):
        assert cmd.send_custom_host_notification("web-01", "Automatic recovery failed", TARGETS).ok
        assert body(sent[0]) == "SEND_CUSTOM_HOST_NOTIFICATION;web-01;0;PinPoint;Automatic recovery failed"

    def test_semicolon_in_comment_cannot_add_a_field(self, app, sent):
        assert cmd.send_custom_service_notification("web-01", "cpu/percent", "a;b", TARGETS).ok
        assert body(sent[0]).endswith(";PinPoint;a,b")

    @pytest.mark.parametrize("comment", ["", "  ", "line\nbreak", "nul\0byte", None])
    def test_bad_comment_is_refused(self, app, sent, comment):
        result = cmd.send_custom_service_notification("web-01", "cpu/percent", comment, TARGETS)
        assert not result.ok and result.error == cmd.INVALID
        assert sent == []

    def test_unknown_service_is_refused(self, app, sent):
        result = cmd.send_custom_service_notification("web-01", "nope", "x", TARGETS)
        assert not result.ok and result.error == cmd.UNKNOWN_TARGET
        assert sent == []

    def test_unknown_host_is_refused(self, app, sent):
        result = cmd.send_custom_host_notification("db-01", "x", TARGETS)
        assert not result.ok and result.error == cmd.UNKNOWN_TARGET
        assert sent == []
