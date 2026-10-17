"""
tests/unit/test_remediation_escalation.py — Operator notification for automatic recovery (#153,
app/remediation_escalation.py).

Covers the outcome-to-notification mapping, the Notify_On filter, the notification comment
(fixed text only, hostile action names), the bounded retry and the failure paths of the command
channel, idempotency, and the repeat-recovery window. The Nagios command functions are replaced,
so no pipe is needed.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app import remediation_escalation as esc
from app.nagios import commands
from app.system_models import (
    RemediationAction, RemediationActionType, RemediationEventState, RemediationEventStateType,
    RemediationNotifyState, RemediationOutcome, RemediationRun, RemediationScope,
)

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
HOSTILE_NAMES = ["a;b", "a$(id)", "a`id`", "a'b", 'a"b', "a\nb", "a|b", "../../x", "ünï", "a\0b", "x" * 60]


def add_action(db_session, **changes):
    fields = dict(
        Name="restart-web", Action_Type=RemediationActionType.RECORD_ONLY, Scope_Kind=RemediationScope.SERVICE,
        Host_Pattern="web-*", Service_Pattern="HTTP", Parameters={}, Enabled=True,
        Max_Runs_Per_Hour=2, Cooldown_Seconds=600, Version=1,
    )
    fields.update(changes)
    action = RemediationAction(**fields)
    db_session.session.add(action)
    db_session.session.commit()
    return action


def add_run(db_session, action, outcome=RemediationOutcome.FAILED, service="HTTP", received=NOW, key=None, **changes):
    fields = dict(
        Event_Key=key or f"key-{RemediationRun.query.count()}", Action_Id=action.Id, Action_Name=action.Name,
        Hostname="web-01", Service=service, State=RemediationEventState.CRITICAL,
        State_Type=RemediationEventStateType.HARD, Attempt=3, Received_At=received, Outcome=outcome,
    )
    fields.update(changes)
    run = RemediationRun(**fields)
    db_session.session.add(run)
    db_session.session.commit()
    return run


@pytest.fixture()
def sent(monkeypatch):
    """Replace the two command functions; each call is recorded and returns ok."""
    calls = []

    def service(host, name, comment, *args, **kwargs):
        calls.append(("service", host, name, comment))
        return commands.CommandResult(True)

    def host(name, comment, *args, **kwargs):
        calls.append(("host", name, None, comment))
        return commands.CommandResult(True)

    monkeypatch.setattr(commands, "send_custom_service_notification", service)
    monkeypatch.setattr(commands, "send_custom_host_notification", host)
    return calls


def failing(monkeypatch, error=commands.UNAVAILABLE, message="The Nagios command pipe was not found."):
    calls = []

    def fail(*args, **kwargs):
        calls.append(args)
        return commands.CommandResult(False, error, message)

    monkeypatch.setattr(commands, "send_custom_service_notification", fail)
    monkeypatch.setattr(commands, "send_custom_host_notification", fail)
    return calls


# ==========================================================
# MAPPING AND FILTER
# ==========================================================

@pytest.mark.parametrize("outcome, kind", [
    (RemediationOutcome.FAILED, "failed"),
    (RemediationOutcome.TIMED_OUT, "failed"),
    (RemediationOutcome.SKIPPED_COOLDOWN, "capped"),
    (RemediationOutcome.SKIPPED_HOURLY_CAP, "capped"),
    (RemediationOutcome.SUCCEEDED, None),
    (RemediationOutcome.RUNNING, None),
    (RemediationOutcome.INTERRUPTED, None),
    (RemediationOutcome.SKIPPED_KILL_SWITCH, None),
    (RemediationOutcome.SKIPPED_MAINTENANCE, None),
    (RemediationOutcome.SKIPPED_DOWNTIME, None),
    (RemediationOutcome.SKIPPED_ACKNOWLEDGED, None),
])
def test_only_failures_and_caps_map_to_a_notification(outcome, kind):
    assert esc.kind_for_outcome(outcome) == kind


def test_a_run_is_marked_pending_when_the_action_asks_for_it(db_session):
    action = add_action(db_session)
    run = add_run(db_session, action)
    assert esc.mark_for_notification(run, "failed", ["failed", "capped", "repeated"]) is True
    assert (run.Notify_Kind, run.Notify_State) == ("failed", RemediationNotifyState.PENDING)


@pytest.mark.parametrize("notify_on", [[], ["capped"], ["repeated"], None])
def test_a_run_is_left_alone_when_the_action_does_not_ask_for_it(db_session, notify_on):
    action = add_action(db_session)
    run = add_run(db_session, action)
    assert esc.mark_for_notification(run, "failed", notify_on) is False
    assert (run.Notify_Kind, run.Notify_State) == (None, None)


# ==========================================================
# COMMENT
# ==========================================================

def test_comment_is_fixed_text_with_action_outcome_and_run_id():
    comment = esc.build_comment("failed", "restart-web", "timed_out", 42)
    assert "restart-web" in comment and "timed_out" in comment and "42" in comment
    assert "failed" in comment.lower() or "did not" in comment.lower()


@pytest.mark.parametrize("name", HOSTILE_NAMES)
def test_comment_never_carries_a_hostile_action_name(name):
    comment = esc.build_comment("failed", name, "failed", 7)
    assert len(comment) <= commands.MAX_COMMENT_CHARS
    assert commands.validate_comment(comment) is None
    for bad in (";", "$", "`", "'", '"', "|", "\n", "\0", ".."):
        assert bad not in comment
    assert comment.isascii()


@pytest.mark.parametrize("kind", ["failed", "capped", "repeated"])
def test_every_kind_has_its_own_wording(kind):
    assert esc.build_comment(kind, "a", "failed", 1)
    assert len({esc.build_comment(k, "a", "failed", 1) for k in ("failed", "capped", "repeated")}) == 3


# ==========================================================
# DELIVERY
# ==========================================================

def pending(db_session, action, **changes):
    run = add_run(db_session, action, **changes)
    esc.mark_for_notification(run, "failed", ["failed"])
    db_session.session.commit()
    return run


def test_a_service_run_sends_one_service_notification(db_session, sent):
    run = pending(db_session, add_action(db_session))
    esc.deliver(run.Id)
    assert [c[:3] for c in sent] == [("service", "web-01", "HTTP")]
    row = db_session.session.get(RemediationRun, run.Id)
    assert row.Notify_State == RemediationNotifyState.SENT
    assert row.Notify_Attempts == 1 and row.Notify_Error is None and row.Notify_At is not None


def test_a_host_run_sends_a_host_notification(db_session, sent):
    run = pending(db_session, add_action(db_session), service=None)
    esc.deliver(run.Id)
    assert [c[:2] for c in sent] == [("host", "web-01")]


def test_delivering_twice_notifies_once(db_session, sent):
    run = pending(db_session, add_action(db_session))
    esc.deliver(run.Id)
    esc.deliver(run.Id)
    assert len(sent) == 1


def test_a_run_with_nothing_due_sends_nothing(db_session, sent):
    run = add_run(db_session, add_action(db_session))
    esc.deliver(run.Id)
    assert sent == []


def test_a_failed_send_is_recorded_and_stays_pending_for_a_retry(db_session, monkeypatch):
    failing(monkeypatch)
    run = pending(db_session, add_action(db_session))
    esc.deliver(run.Id)
    row = db_session.session.get(RemediationRun, run.Id)
    assert row.Notify_State == RemediationNotifyState.PENDING
    assert row.Notify_Attempts == 1
    assert row.Notify_Error == "The Nagios command pipe was not found."


def test_retries_are_bounded_then_abandoned(db_session, monkeypatch):
    calls = failing(monkeypatch)
    run = pending(db_session, add_action(db_session))
    for _ in range(esc.MAX_ATTEMPTS + 5):
        esc.deliver_pending()
    row = db_session.session.get(RemediationRun, run.Id)
    assert len(calls) == esc.MAX_ATTEMPTS == row.Notify_Attempts
    assert row.Notify_State == RemediationNotifyState.FAILED
    assert row.Notify_Error


@pytest.mark.parametrize("error", [commands.UNAVAILABLE, commands.TIMEOUT, commands.INVALID, commands.UNKNOWN_TARGET])
def test_every_command_failure_is_recorded_and_never_raised(db_session, monkeypatch, error):
    failing(monkeypatch, error, "Fixed message.")
    run = pending(db_session, add_action(db_session))
    esc.deliver(run.Id)
    assert db_session.session.get(RemediationRun, run.Id).Notify_Error == "Fixed message."


def test_an_exception_from_the_command_layer_is_recorded_and_never_raised(db_session, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("/usr/local/nagios/var/rw/nagios.cmd: permission denied")

    monkeypatch.setattr(commands, "send_custom_service_notification", boom)
    run = pending(db_session, add_action(db_session))
    esc.deliver(run.Id)
    row = db_session.session.get(RemediationRun, run.Id)
    assert row.Notify_Error == esc.UNEXPECTED_ERROR
    assert "nagios.cmd" not in row.Notify_Error


def test_deliver_pending_picks_up_only_unfinished_rows_with_a_recorded_error(db_session, sent):
    action = add_action(db_session)
    new = pending(db_session, action)
    retry = pending(db_session, action, key="retry")
    retry.Notify_Error, retry.Notify_Attempts = "The Nagios command pipe was not found.", 1
    done = pending(db_session, action, key="done")
    done.Notify_State = RemediationNotifyState.SENT
    db_session.session.commit()
    esc.deliver_pending()
    assert sorted(c[0] for c in sent) == ["service", "service"]
    assert db_session.session.get(RemediationRun, done.Id).Notify_Attempts == 0
    assert db_session.session.get(RemediationRun, new.Id).Notify_State == RemediationNotifyState.SENT


def test_after_a_stop_an_attempt_with_no_result_is_failed_and_never_resent(db_session, sent):
    """A crash between 'attempt started' and 'result saved' leaves attempts > 0 and no error."""
    run = pending(db_session, add_action(db_session))
    run.Notify_Attempts = 1
    db_session.session.commit()
    assert esc.fail_unfinished() == 1
    esc.deliver_pending()
    row = db_session.session.get(RemediationRun, run.Id)
    assert row.Notify_State == RemediationNotifyState.FAILED and row.Notify_Error
    assert sent == []


def test_a_not_yet_attempted_row_survives_a_restart_and_is_sent(db_session, sent):
    run = pending(db_session, add_action(db_session))
    assert esc.fail_unfinished() == 0
    esc.deliver_pending()
    assert len(sent) == 1
    assert db_session.session.get(RemediationRun, run.Id).Notify_State == RemediationNotifyState.SENT


# ==========================================================
# REPEATED RECOVERY
# ==========================================================

def succeeded(db_session, action, minutes_ago, key):
    return add_run(db_session, action, RemediationOutcome.SUCCEEDED, received=NOW - timedelta(minutes=minutes_ago), key=key)


def test_n_successes_in_the_window_mark_one_run_repeated(db_session):
    action = add_action(db_session)
    succeeded(db_session, action, 120, "a")
    succeeded(db_session, action, 60, "b")
    assert esc.check_repeat(succeeded(db_session, action, 0, "c"), action.Notify_On, 3, 24, NOW) is True
    row = RemediationRun.query.filter_by(Event_Key="c").one()
    assert (row.Notify_Kind, row.Notify_State) == ("repeated", RemediationNotifyState.PENDING)


def test_fewer_than_n_successes_do_nothing(db_session):
    action = add_action(db_session)
    succeeded(db_session, action, 60, "a")
    assert esc.check_repeat(succeeded(db_session, action, 0, "b"), action.Notify_On, 3, 24, NOW) is False


def test_successes_outside_the_window_do_not_count(db_session):
    action = add_action(db_session)
    succeeded(db_session, action, 60 * 30, "old1")
    succeeded(db_session, action, 60 * 26, "old2")
    assert esc.check_repeat(succeeded(db_session, action, 0, "new"), action.Notify_On, 3, 24, NOW) is False


def test_only_one_repeat_notification_per_window(db_session):
    action = add_action(db_session)
    for n, minutes in enumerate((180, 120, 60)):
        succeeded(db_session, action, minutes, f"s{n}")
    assert esc.check_repeat(succeeded(db_session, action, 30, "first"), action.Notify_On, 3, 24, NOW) is True
    assert esc.check_repeat(succeeded(db_session, action, 0, "second"), action.Notify_On, 3, 24, NOW) is False


def test_a_new_repeat_notification_is_allowed_once_the_window_has_passed(db_session):
    action = add_action(db_session)
    first = succeeded(db_session, action, 60 * 30, "s0")
    first.Notify_Kind, first.Notify_State = "repeated", RemediationNotifyState.SENT
    db_session.session.commit()
    succeeded(db_session, action, 120, "s1")
    succeeded(db_session, action, 60, "s2")
    assert esc.check_repeat(succeeded(db_session, action, 0, "s3"), action.Notify_On, 3, 24, NOW) is True


def test_repeats_are_counted_per_host_and_service(db_session):
    action = add_action(db_session)
    succeeded(db_session, action, 120, "a")
    other = add_run(db_session, action, RemediationOutcome.SUCCEEDED, service="SSH", key="b",
                    received=NOW - timedelta(minutes=60))
    assert other.Service == "SSH"
    assert esc.check_repeat(succeeded(db_session, action, 0, "c"), action.Notify_On, 3, 24, NOW) is False


def test_repeat_is_off_when_the_action_does_not_ask_for_it(db_session):
    action = add_action(db_session, Notify_On=["failed"])
    succeeded(db_session, action, 120, "a")
    succeeded(db_session, action, 60, "b")
    assert esc.check_repeat(succeeded(db_session, action, 0, "c"), action.Notify_On, 3, 24, NOW) is False


def test_repeat_settings_default_when_the_settings_row_is_missing(db_session):
    assert esc.repeat_settings() == (3, 24)
