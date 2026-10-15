"""
tests/unit/test_remediation_consumer.py — The spool consumer (app/remediation.py).

Covers the design's threats: forged or malformed spool files (T1, T3), flood (T7), secrets in
rows and logs (T8), replay and crash between steps (T9), and the decisions: SOFT ignored,
match, cooldown, hourly cap.
"""
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

from app import remediation
from app import remediation_actions as registry
from app.system_models import (
    RemediationAction, RemediationActionType, RemediationEventState, RemediationEventStateType,
    RemediationOutcome, RemediationRun, RemediationScope,
)

HOSTILE = ["a;b", "a$(id)", "a`id`", "a'b", 'a"b', "a\nb", "a|b", "../../etc/passwd", "ünï", "x" * 101, ""]


@pytest.fixture()
def spool(tmp_path, monkeypatch):
    """A spool folder whose files count as owned by the trusted user."""
    monkeypatch.setattr(remediation, "trusted_uid", lambda: os.stat(tmp_path).st_uid)
    return tmp_path


_counter = {"n": 0}


def put(spool, event, name=None, raw=None):
    """Write one spool file the way the handler would; returns its path."""
    _counter["n"] += 1
    path = spool / (name or f"{1760432100000000000 + _counter['n']}-{_counter['n']}.json")
    path.write_text(raw if raw is not None else json.dumps(event) + "\n")
    return path


def event(**changes):
    base = {"v": 1, "kind": "service", "host": "web-01", "service": "HTTP", "state": "CRITICAL",
            "state_type": "HARD", "attempt": 3, "last_change": 1760432100}
    base.update(changes)
    return base


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


def runs(db_session):
    return db_session.session.query(RemediationRun).order_by(RemediationRun.Id).all()


def left(spool):
    return sorted(p.name for p in spool.iterdir())


# ==========================================================
# DECISIONS
# ==========================================================

def test_hard_failure_for_a_covered_service_makes_exactly_one_run(db_session, spool):
    add_action(db_session)
    put(spool, event())
    remediation.process_spool(str(spool))
    (run,) = runs(db_session)
    assert run.Outcome == RemediationOutcome.SUCCEEDED
    assert (run.Hostname, run.Service, run.Action_Name) == ("web-01", "HTTP", "restart-web")
    assert run.State == RemediationEventState.CRITICAL and run.State_Type == RemediationEventStateType.HARD
    assert run.Output == "recorded"
    assert run.Started_At is not None and run.Finished_At is not None
    assert left(spool) == []


def test_soft_state_makes_no_run_and_the_file_is_removed(db_session, spool):
    add_action(db_session)
    put(spool, event(state_type="SOFT", attempt=1))
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert left(spool) == []


@pytest.mark.parametrize("changes", [
    {"state": "OK"},
    {"kind": "host", "service": None, "state": "UP"},
])
def test_a_recovery_makes_no_run_and_the_file_is_removed(db_session, spool, changes):
    """A HARD recovery (OK or UP) is not a failure: no action may run on it, whatever the cooldown."""
    add_action(db_session, Scope_Kind=RemediationScope.SERVICE if "kind" not in changes else RemediationScope.HOST,
               Host_Pattern="*", Service_Pattern="*" if "kind" not in changes else None)
    put(spool, event(**changes))
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert left(spool) == []


@pytest.mark.parametrize("changes", [{"host": "db-01"}, {"service": "SSH"}, {"kind": "host", "service": None, "state": "DOWN"}])
def test_events_outside_the_scope_make_no_run(db_session, spool, changes):
    add_action(db_session)
    put(spool, event(**changes))
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert left(spool) == []


def test_disabled_action_makes_no_run(db_session, spool):
    add_action(db_session, Enabled=False)
    put(spool, event())
    remediation.process_spool(str(spool))
    assert runs(db_session) == []


def test_host_scope_action_matches_host_events_only(db_session, spool):
    add_action(db_session, Name="host-rule", Scope_Kind=RemediationScope.HOST, Host_Pattern="web-01", Service_Pattern=None)
    put(spool, event(kind="host", service=None, state="DOWN"))
    put(spool, event())
    remediation.process_spool(str(spool))
    (run,) = runs(db_session)
    assert run.Service is None and run.State == RemediationEventState.DOWN


def test_wildcard_matches_by_star_only_not_regex(db_session, spool):
    add_action(db_session, Host_Pattern="web-.*", Service_Pattern="*")
    put(spool, event(host="web-01"))
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    put(spool, event(host="web-.x"))
    remediation.process_spool(str(spool))
    assert len(runs(db_session)) == 1


def test_two_matching_actions_each_get_a_run(db_session, spool):
    add_action(db_session, Name="one")
    add_action(db_session, Name="two")
    put(spool, event())
    remediation.process_spool(str(spool))
    assert sorted(r.Action_Name for r in runs(db_session)) == ["one", "two"]


def test_cooldown_skips_a_repeat_for_the_same_host_and_service_and_says_why(db_session, spool):
    add_action(db_session, Cooldown_Seconds=600)
    put(spool, event(last_change=1760432100))
    put(spool, event(last_change=1760432400))
    remediation.process_spool(str(spool))
    first, second = runs(db_session)
    assert first.Outcome == RemediationOutcome.SUCCEEDED
    assert second.Outcome == RemediationOutcome.SKIPPED_COOLDOWN
    assert "cooldown" in second.Reason.lower()
    assert second.Started_At is None


def test_cooldown_is_per_host_and_service(db_session, spool):
    add_action(db_session, Cooldown_Seconds=600)
    put(spool, event(host="web-01"))
    put(spool, event(host="web-02"))
    remediation.process_spool(str(spool))
    assert [r.Outcome for r in runs(db_session)] == [RemediationOutcome.SUCCEEDED] * 2


def test_a_skipped_run_does_not_extend_the_cooldown(db_session, spool):
    action = add_action(db_session, Cooldown_Seconds=600)
    old = datetime.now(timezone.utc) - timedelta(seconds=700)
    db_session.session.add(RemediationRun(
        Event_Key="old", Action_Id=action.Id, Action_Name="restart-web", Hostname="web-01", Service="HTTP",
        State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
        Received_At=old, Outcome=RemediationOutcome.SUCCEEDED))
    db_session.session.add(RemediationRun(
        Event_Key="skipped", Action_Id=action.Id, Action_Name="restart-web", Hostname="web-01", Service="HTTP",
        State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
        Received_At=datetime.now(timezone.utc) - timedelta(seconds=10), Outcome=RemediationOutcome.SKIPPED_COOLDOWN))
    db_session.session.commit()
    put(spool, event())
    remediation.process_spool(str(spool))
    assert runs(db_session)[-1].Outcome == RemediationOutcome.SUCCEEDED


def test_hourly_cap_skips_and_says_why(db_session, spool):
    action = add_action(db_session, Cooldown_Seconds=60, Max_Runs_Per_Hour=2, Host_Pattern="*")
    for i in range(2):
        db_session.session.add(RemediationRun(
            Event_Key=f"p{i}", Action_Id=action.Id, Action_Name="restart-web", Hostname=f"web-0{i}", Service="HTTP",
            State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
            Received_At=datetime.now(timezone.utc) - timedelta(minutes=30), Outcome=RemediationOutcome.SUCCEEDED))
    db_session.session.commit()
    put(spool, event(host="web-09"))
    remediation.process_spool(str(spool))
    last = runs(db_session)[-1]
    assert last.Outcome == RemediationOutcome.SKIPPED_HOURLY_CAP
    assert "hour" in last.Reason.lower()


def test_runs_older_than_an_hour_do_not_count_toward_the_cap(db_session, spool):
    action = add_action(db_session, Cooldown_Seconds=60, Max_Runs_Per_Hour=1, Host_Pattern="*")
    db_session.session.add(RemediationRun(
        Event_Key="p", Action_Id=action.Id, Action_Name="restart-web", Hostname="web-00", Service="HTTP",
        State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
        Received_At=datetime.now(timezone.utc) - timedelta(minutes=61), Outcome=RemediationOutcome.SUCCEEDED))
    db_session.session.commit()
    put(spool, event(host="web-09"))
    remediation.process_spool(str(spool))
    assert runs(db_session)[-1].Outcome == RemediationOutcome.SUCCEEDED


# ==========================================================
# REPLAY AND CRASHES (T9)
# ==========================================================

def test_the_same_event_twice_runs_the_action_once(db_session, spool, monkeypatch):
    add_action(db_session, Cooldown_Seconds=60)
    calls = []
    real = registry.run_action
    monkeypatch.setattr(remediation, "run_action", lambda *a, **k: calls.append(1) or real(*a, **k))
    put(spool, event())
    remediation.process_spool(str(spool))
    put(spool, event())  # identical event content replayed
    remediation.process_spool(str(spool))
    assert len(runs(db_session)) == 1
    assert len(calls) == 1
    assert left(spool) == []


def test_running_rows_become_interrupted_at_start_and_are_not_run_again(db_session, spool, monkeypatch):
    action = add_action(db_session)
    db_session.session.add(RemediationRun(
        Event_Key="k", Action_Id=action.Id, Action_Name="restart-web", Hostname="web-01", Service="HTTP",
        State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
        Received_At=datetime.now(timezone.utc), Outcome=RemediationOutcome.RUNNING))
    db_session.session.commit()
    assert remediation.mark_interrupted() == 1
    (run,) = runs(db_session)
    assert run.Outcome == RemediationOutcome.INTERRUPTED
    assert run.Reason
    monkeypatch.setattr(remediation, "run_action", lambda *a, **k: pytest.fail("must not run again"))
    remediation.process_spool(str(spool))


def test_a_crash_after_the_row_is_saved_leaves_it_running_and_the_file_gone(db_session, spool, monkeypatch):
    add_action(db_session)

    def crash(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(remediation, "run_action", crash)
    put(spool, event())
    remediation.process_spool(str(spool))  # must not raise
    (run,) = runs(db_session)
    assert run.Outcome == RemediationOutcome.RUNNING
    assert left(spool) == []
    assert remediation.mark_interrupted() == 1


def test_a_failing_action_is_recorded_as_failed(db_session, spool, monkeypatch):
    add_action(db_session)
    monkeypatch.setitem(registry.ACTION_TYPES, "record_only", registry.ActionType(
        key="record_only", label="x", description="x", parameters=[], validate=lambda p: ({}, {}),
        run=lambda params, context: (_ for _ in ()).throw(RuntimeError("nope"))))
    put(spool, event())
    remediation.process_spool(str(spool))
    assert runs(db_session)[0].Outcome == RemediationOutcome.FAILED


# ==========================================================
# FORGED, MALFORMED AND OVERSIZED FILES (T1, T3)
# ==========================================================

BAD_EVENTS = [
    ("not json", None, "this is not json"),
    ("empty", None, ""),
    ("a list", None, "[1, 2]"),
    ("extra key", event(extra="x"), None),
    ("missing key", {k: v for k, v in event().items() if k != "attempt"}, None),
    ("wrong version", event(v=2), None),
    ("bool attempt", event(attempt=True), None),
    ("string attempt", event(attempt="3"), None),
    ("zero attempt", event(attempt=0), None),
    ("huge attempt", event(attempt=10**9), None),
    ("unknown kind", event(kind="other"), None),
    ("service state for host", event(kind="host", service=None, state="CRITICAL"), None),
    ("host state for service", event(state="DOWN"), None),
    ("host with service", event(kind="host", state="DOWN"), None),
    ("service without name", event(service=None), None),
    ("bad state type", event(state_type="FIRM"), None),
    ("string last change", event(last_change="1760432100"), None),
    ("negative last change", event(last_change=-5), None),
    ("huge last change", event(last_change=10**15), None),
]


@pytest.mark.parametrize("label,body,raw", BAD_EVENTS, ids=[b[0] for b in BAD_EVENTS])
def test_malformed_event_is_discarded_without_a_run_or_a_crash(db_session, spool, label, body, raw):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    put(spool, body, raw=raw)
    result = remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert left(spool) == []
    assert result["discarded"] == 1


@pytest.mark.parametrize("bad", HOSTILE)
def test_hostile_host_or_service_names_are_discarded(db_session, spool, bad):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    put(spool, event(host=bad))
    if bad != "x" * 101:  # 101 characters is too long for a host but allowed for a service
        put(spool, event(service=bad))
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert left(spool) == []


def test_oversized_file_is_discarded_unread(db_session, spool):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    big = event(host="web-01")
    path = put(spool, big, raw=json.dumps(big) + " " * 3000)
    remediation.process_spool(str(spool))
    assert runs(db_session) == [] and not path.exists()


def test_a_directory_in_the_spool_is_not_followed_or_run(db_session, spool):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    (spool / "1760432100000000009-1.json").mkdir()
    remediation.process_spool(str(spool))
    assert runs(db_session) == []


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges on Windows")
def test_a_symlink_is_discarded_and_its_target_is_not_read(db_session, spool, tmp_path_factory):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    outside = tmp_path_factory.mktemp("outside") / "secret.json"
    outside.write_text(json.dumps(event()))
    (spool / "1760432100000000009-1.json").symlink_to(outside)
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert not (spool / "1760432100000000009-1.json").exists()
    assert outside.exists()  # the target is never touched


def test_a_file_not_owned_by_the_trusted_user_is_discarded(db_session, spool, monkeypatch):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    monkeypatch.setattr(remediation, "trusted_uid", lambda: os.stat(spool).st_uid + 4242)
    put(spool, event())
    remediation.process_spool(str(spool))
    assert runs(db_session) == []
    assert left(spool) == []


def test_when_the_trusted_user_is_unknown_nothing_is_trusted(db_session, spool, monkeypatch):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    monkeypatch.setattr(remediation, "trusted_uid", lambda: None)
    put(spool, event())
    remediation.process_spool(str(spool))
    assert runs(db_session) == []


def test_files_with_other_names_and_temporary_files_are_left_alone(db_session, spool):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    (spool / ".1760432100000000009-1.tmp").write_text("partial")
    (spool / "notes.txt").write_text("hello")
    remediation.process_spool(str(spool))
    assert left(spool) == [".1760432100000000009-1.tmp", "notes.txt"]


def test_a_missing_spool_folder_is_not_an_error(db_session, tmp_path):
    result = remediation.process_spool(str(tmp_path / "nope"))
    assert result["processed"] == 0


def test_discard_log_lines_never_contain_file_content(db_session, spool, caplog):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*")
    put(spool, None, raw="password=hunter2 $(reboot)")
    put(spool, event(host="a;b hunter2"))
    with caplog.at_level(logging.DEBUG):
        remediation.process_spool(str(spool))
    assert "hunter2" not in caplog.text and "reboot" not in caplog.text
    assert "discard" in caplog.text.lower()


# ==========================================================
# FLOOD (T7)
# ==========================================================

def test_at_most_200_files_are_handled_per_run_oldest_first(db_session, spool):
    add_action(db_session, Host_Pattern="*", Service_Pattern="*", Cooldown_Seconds=60, Max_Runs_Per_Hour=60)
    for i in range(250):
        put(spool, event(host=f"h{i:03d}", last_change=1760432100 + i), name=f"{1760432100000000000 + i}-1.json")
    remediation.process_spool(str(spool))
    remaining = left(spool)
    assert len(remaining) == 50
    assert remaining[0] == f"{1760432100000000200}-1.json"


# ==========================================================
# SECRETS (T8)
# ==========================================================

def test_secret_like_output_is_redacted_before_it_is_stored(db_session, spool, monkeypatch):
    add_action(db_session)
    monkeypatch.setitem(registry.ACTION_TYPES, "record_only", registry.ActionType(
        key="record_only", label="x", description="x", parameters=[], validate=lambda p: ({}, {}),
        run=lambda params, context: "ok password=hunter2 token: abc123 community=public " + "x" * 5000))
    put(spool, event())
    remediation.process_spool(str(spool))
    (run,) = runs(db_session)
    assert "hunter2" not in run.Output and "abc123" not in run.Output and "public" not in run.Output
    assert len(run.Output) <= 1024


def test_the_activity_line_has_no_output_or_parameters(db_session, spool, monkeypatch, caplog):
    add_action(db_session, Parameters={})
    monkeypatch.setitem(registry.ACTION_TYPES, "record_only", registry.ActionType(
        key="record_only", label="x", description="x", parameters=[], validate=lambda p: ({}, {}),
        run=lambda params, context: "secret-output-text"))
    put(spool, event())
    with caplog.at_level(logging.INFO):
        remediation.process_spool(str(spool))
    assert "secret-output-text" not in caplog.text
    assert "restart-web" in caplog.text


# ==========================================================
# NAME RULES AGREE WITH THE HANDLER
# ==========================================================

def test_consumer_and_handler_accept_and_refuse_the_same_names():
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "pinpoint_event_handler.py"
    spec = importlib.util.spec_from_file_location("pinpoint_event_handler", script)
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)

    samples = HOSTILE + ["web-01", "db_01.lan", "Port 5432/tcp: postgres", "a..b", "h" * 100, "s" * 150, "s" * 151]
    for value in samples:
        for kind, limit in (("host", 100), ("service", 150)):
            try:
                handler.check_name(value, kind, limit)
                handler_ok = True
            except handler.InputRejected:
                handler_ok = False
            assert remediation.valid_name(value, limit) == handler_ok, (kind, value)


# ==========================================================
# SCHEDULER WIRING
# ==========================================================

def test_the_scheduler_job_runs_the_consumer(app, monkeypatch):
    import app.scheduler as scheduler

    called = []
    monkeypatch.setattr(remediation, "process_spool", lambda *a, **k: called.append(1) or {"processed": 0})
    scheduler._consume_remediation_spool()
    assert called == [1]
