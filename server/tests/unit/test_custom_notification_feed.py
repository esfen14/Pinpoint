"""
tests/unit/test_custom_notification_feed.py — Custom notifications in the feed (#153).

The Nagios archive entry for a custom notification was captured on a lab appliance
(2026-10-17): ``notification_type`` is 1024 and there is no comment or author in it. The comment
text therefore comes from PinPoint's own record: the RemediationRun that sent the notification,
matched by host, service and send time, with the text rebuilt from fixed parts.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app import remediation_escalation as esc
from app.nagios.notifications import normalize_notification
from app.system_models import (
    RemediationEventState, RemediationEventStateType, RemediationNotifyState, RemediationOutcome, RemediationRun,
)

SENT_AT = datetime(2026, 10, 17, 13, 32, 24, tzinfo=timezone.utc)
TS = int(SENT_AT.timestamp())

# The entry exactly as the lab's archivejson returned it (keys and types), milliseconds included.
LAB_ENTRY = {
    "timestamp": TS * 1000, "object_type": 2, "host_name": "web-01", "description": "HTTP",
    "contact": "nagiosadmin", "notification_type": 1024, "method": "notify-service-by-email",
    "message": "HTTP CRITICAL - Connection refused",
}
PROBLEM_ENTRY = {**LAB_ENTRY, "notification_type": 1, "timestamp": (TS - 600) * 1000}


def add_run(db_session, host="web-01", service="HTTP", sent_at=SENT_AT, state=RemediationNotifyState.SENT,
            outcome=RemediationOutcome.FAILED, kind="failed", key="k", action="restart-web"):
    run = RemediationRun(
        Event_Key=key, Action_Id=None, Action_Name=action, Hostname=host, Service=service,
        State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD, Attempt=3,
        Received_At=sent_at - timedelta(seconds=5), Outcome=outcome, Notify_Kind=kind, Notify_State=state,
        Notify_Attempts=1, Notify_At=sent_at)
    db_session.session.add(run)
    db_session.session.commit()
    return run


# ==========================================================
# NORMALIZATION
# ==========================================================

@pytest.mark.parametrize("raw, expected", [(1024, "CUSTOM"), ("1024", "CUSTOM"), ("custom", "CUSTOM"), ("CUSTOM", "CUSTOM")])
def test_a_custom_notification_is_labelled_custom(raw, expected):
    assert normalize_notification({**LAB_ENTRY, "notification_type": raw})["notificationtype"] == expected


@pytest.mark.parametrize("raw, expected", [(1, "1"), (4, "4"), ("PROBLEM", "PROBLEM"), ("RECOVERY", "RECOVERY")])
def test_other_types_are_left_as_they_were(raw, expected):
    assert normalize_notification({**LAB_ENTRY, "notification_type": raw})["notificationtype"] == expected


def test_the_lab_entry_normalizes_to_a_service_notification_with_its_output():
    item = normalize_notification(LAB_ENTRY)
    assert (item["hostname"], item["servicedesc"], item["output"]) == ("web-01", "HTTP", "HTTP CRITICAL - Connection refused")
    assert item["timestamp"] == TS


# ==========================================================
# MATCHING A NOTIFICATION TO THE RUN THAT SENT IT
# ==========================================================

def item(**changes):
    base = {"is_custom": True, "hostname": "web-01", "service": "HTTP", "timestamp": TS}
    base.update(changes)
    return base


def test_the_comment_is_rebuilt_from_the_run_that_sent_it(db_session):
    run = add_run(db_session)
    (result,) = esc.attach_comments([item()], "service")
    assert result["comment"] == esc.build_comment("failed", "restart-web", "failed", run.Id)


def test_a_repeat_notification_gets_its_own_wording(db_session):
    run = add_run(db_session, outcome=RemediationOutcome.SUCCEEDED, kind="repeated")
    (result,) = esc.attach_comments([item()], "service")
    assert result["comment"] == esc.build_comment("repeated", "restart-web", "succeeded", run.Id)
    assert "several times" in result["comment"]


def test_a_host_notification_matches_a_host_run(db_session):
    add_run(db_session, service=None)
    (result,) = esc.attach_comments([item(service=None)], "service")
    assert result["comment"]


@pytest.mark.parametrize("changes", [
    {"hostname": "web-02"}, {"service": "SSH"}, {"service": None}, {"timestamp": TS + 600}, {"timestamp": TS - 600},
])
def test_a_notification_that_no_run_sent_has_no_comment(db_session, changes):
    add_run(db_session)
    (result,) = esc.attach_comments([item(**changes)], "service")
    assert result["comment"] is None


@pytest.mark.parametrize("state", [RemediationNotifyState.PENDING, RemediationNotifyState.FAILED, None])
def test_only_a_notification_that_was_sent_counts(db_session, state):
    add_run(db_session, state=state)
    (result,) = esc.attach_comments([item()], "service")
    assert result["comment"] is None


def test_the_run_closest_in_time_wins(db_session):
    far = add_run(db_session, sent_at=SENT_AT - timedelta(seconds=90), key="far", action="far-run")
    near = add_run(db_session, sent_at=SENT_AT + timedelta(seconds=3), key="near", action="near-run")
    (result,) = esc.attach_comments([item()], "service")
    assert "near-run" in result["comment"] and str(near.Id) in result["comment"]
    assert "far-run" not in result["comment"] and far.Id != near.Id


def test_other_notifications_are_not_touched(db_session):
    add_run(db_session)
    plain = {"is_custom": False, "hostname": "web-01", "service": "HTTP", "timestamp": TS}
    (result,) = esc.attach_comments([plain], "service")
    assert "comment" not in result


def test_a_database_problem_leaves_the_items_unchanged(db_session, monkeypatch):
    add_run(db_session)

    def boom(*args, **kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(esc.db.session, "scalars", boom)
    (result,) = esc.attach_comments([item()], "service")
    assert result["comment"] is None


def test_no_custom_items_means_no_query(db_session, monkeypatch):
    monkeypatch.setattr(esc.db.session, "scalars", lambda *a, **k: pytest.fail("must not query"))
    assert esc.attach_comments([{"is_custom": False, "timestamp": TS}], "service") == [{"is_custom": False, "timestamp": TS}]


# ==========================================================
# THE THREE PLACES THE FEED IS BUILT
# ==========================================================

def test_the_bell_marks_a_custom_notification_and_shows_its_comment(logged_in_client, db_session, seeded_permissions):
    run = add_run(db_session)
    with patch("app.api.system.notifications.request_notifications_range", return_value=[LAB_ENTRY, PROBLEM_ENTRY]):
        data = logged_in_client.get("/api/system/notifications").get_json()["data"]
    by_type = {n["notificationtype"]: n for n in data["notifications"]}
    custom = by_type["CUSTOM"]
    assert custom["is_custom"] is True
    assert custom["comment"] == esc.build_comment("failed", "restart-web", "failed", run.Id)
    assert by_type["1"].get("is_custom") is False and "comment" not in by_type["1"]


def test_the_dashboard_marks_a_custom_notification_and_shows_its_comment(logged_in_client, db_session):
    run = add_run(db_session)
    with patch("app.api.system.dashboard.request_notifications_last", return_value=[LAB_ENTRY, PROBLEM_ENTRY]):
        items = logged_in_client.get("/api/system/dashboard/notifications").get_json()["data"]["notifications"]
    custom = next(n for n in items if n["type"] == "CUSTOM")
    assert custom["is_custom"] is True
    assert custom["comment"] == esc.build_comment("failed", "restart-web", "failed", run.Id)
    problem = next(n for n in items if n["type"] == "1")
    assert problem["is_custom"] is False and "comment" not in problem


def test_history_marks_a_custom_notification_and_shows_its_comment(logged_in_client, db_session):
    run = add_run(db_session)
    with patch("app.api.system.history.request_notifications_range", return_value=[LAB_ENTRY, PROBLEM_ENTRY]):
        response = logged_in_client.get("/api/system/history/notifications", query_string={"preset": "30d"})
    items = response.get_json()["data"]["items"]
    custom = next(n for n in items if n.get("is_custom"))
    assert custom["comment"] == esc.build_comment("failed", "restart-web", "failed", run.Id)
    assert [n for n in items if not n.get("is_custom")] and all("comment" not in n for n in items if not n.get("is_custom"))


def test_a_custom_notification_nobody_here_sent_still_shows_without_a_comment(logged_in_client, db_session, seeded_permissions):
    with patch("app.api.system.notifications.request_notifications_range", return_value=[LAB_ENTRY]):
        (custom,) = logged_in_client.get("/api/system/notifications").get_json()["data"]["notifications"]
    assert custom["is_custom"] is True and custom["comment"] is None


def test_history_detail_of_a_custom_notification_shows_its_comment(logged_in_client, db_session):
    run = add_run(db_session)
    with patch("app.api.system.history.request_notifications_range", return_value=[LAB_ENTRY]), \
            patch("app.api.system.history.request_alerts_range", return_value=[]):
        response = logged_in_client.get("/api/system/history/notifications/detail", query_string={
            "hostname": "web-01", "service": "HTTP", "timestamp": TS})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["is_custom"] is True
    assert data["comment"] == esc.build_comment("failed", "restart-web", "failed", run.Id)


def test_a_problem_is_not_folded_into_the_custom_notification_after_it(logged_in_client, db_session, seeded_permissions):
    """The archive gives both an empty state, so only the type keeps them apart."""
    with patch("app.api.system.notifications.request_notifications_range", return_value=[PROBLEM_ENTRY, LAB_ENTRY]):
        items = logged_in_client.get("/api/system/notifications").get_json()["data"]["notifications"]
    assert sorted(n["notificationtype"] for n in items) == ["1", "CUSTOM"]
    assert all(n["repeat_count"] == 1 for n in items)
