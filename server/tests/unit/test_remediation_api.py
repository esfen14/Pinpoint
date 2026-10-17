"""
tests/unit/test_remediation_api.py — /api/system/remediation routes.

Permissions (view versus manage), per-field validation (400), optimistic locking (409), the
Nagios apply with rollback (422), run log filters and pagination, and that no response
carries anything secret.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.system_models import (
    Permission, RemediationAction, RemediationEventState, RemediationEventStateType, RemediationOutcome,
    RemediationRun, RolePermission,
)

BASE = "/api/system/remediation"
APPLY = "app.network_discovery.create_host_cfg.regenerate_and_apply_config_status"

PAYLOAD = {
    "name": "restart-web", "actionType": "record_only", "scopeKind": "service", "hostPattern": "web-*",
    "servicePattern": "HTTP", "parameters": {}, "enabled": True, "maxRunsPerHour": 2, "cooldownSeconds": 600,
}


@pytest.fixture(autouse=True)
def nagios_apply():
    """Nagios accepts the config unless a test says otherwise."""
    with patch(APPLY, return_value=("applied", "ok")) as apply:
        yield apply


def grant(db_session, role, name):
    permission = db_session.session.query(Permission).filter_by(Name=name).one()
    db_session.session.add(RolePermission(RoleID=role.RoleID, PermissionID=permission.PermissionID))
    db_session.session.commit()


def create(client, **changes):
    return client.post(f"{BASE}/actions", json={**PAYLOAD, **changes})


def add_run(db_session, action_id=1, name="restart-web", host="web-01", service="HTTP",
            outcome=RemediationOutcome.SUCCEEDED, received=None, key=None, output="recorded"):
    row = RemediationRun(
        Event_Key=key or f"{host}-{service}-{outcome.value}-{received}", Action_Id=action_id, Action_Name=name,
        Hostname=host, Service=service, State=RemediationEventState.CRITICAL, State_Type=RemediationEventStateType.HARD,
        Attempt=3, Received_At=received or datetime.now(timezone.utc), Outcome=outcome, Output=output)
    db_session.session.add(row)
    db_session.session.commit()
    return row


# ==========================================================
# PERMISSIONS
# ==========================================================

READ_URLS = [f"{BASE}/action-types", f"{BASE}/actions", f"{BASE}/runs", f"{BASE}/runs/1", f"{BASE}/health",
             f"{BASE}/last-runs", f"{BASE}/targets"]


def test_every_route_needs_login(client, db_session):
    for url in READ_URLS:
        assert client.get(url).status_code in (401, 302)
    assert client.post(f"{BASE}/actions", json=PAYLOAD).status_code in (401, 302)


@pytest.mark.parametrize("url", READ_URLS)
def test_reading_needs_the_view_permission(limited_client, url):
    assert limited_client.get(url).status_code == 403


def test_changing_needs_the_manage_permission(limited_client, db_session):
    assert limited_client.post(f"{BASE}/actions", json=PAYLOAD).status_code == 403
    assert limited_client.put(f"{BASE}/actions/1", json=PAYLOAD).status_code == 403
    assert limited_client.delete(f"{BASE}/actions/1").status_code == 403


def test_view_alone_can_read_but_not_change(limited_client, db_session, regular_role):
    grant(db_session, regular_role, "remediation.view")
    assert limited_client.get(f"{BASE}/actions").status_code == 200
    assert limited_client.get(f"{BASE}/runs").status_code == 200
    assert limited_client.get(f"{BASE}/action-types").status_code == 200
    assert limited_client.post(f"{BASE}/actions", json=PAYLOAD).status_code == 403
    assert limited_client.delete(f"{BASE}/actions/1").status_code == 403


def test_manage_alone_cannot_read_the_run_log(limited_client, db_session, regular_role):
    grant(db_session, regular_role, "remediation.manage")
    assert limited_client.get(f"{BASE}/runs").status_code == 403


# ==========================================================
# ACTION TYPES
# ==========================================================

def test_action_types_describe_the_form(logged_in_client):
    items = logged_in_client.get(f"{BASE}/action-types").get_json()["data"]["items"]
    assert [item["key"] for item in items] == ["record_only", "restart_local_service", "restart_remote_service"]
    assert set(items[0]) == {"key", "label", "description", "parameters"}
    restart = items[1]
    assert restart["parameters"][0]["choices"] == ["nagios"]


def test_restart_local_service_is_created_with_a_listed_unit(logged_in_client):
    response = create(logged_in_client, actionType="restart_local_service", parameters={"unit": "nagios"})
    assert response.status_code == 201
    assert response.get_json()["data"]["parameters"] == {"unit": "nagios"}


@pytest.mark.parametrize("parameters, field", [
    ({}, "parameters.unit"),
    ({"unit": "sshd"}, "parameters.unit"),
    ({"unit": "nagios; reboot"}, "parameters.unit"),
    ({"unit": "../nagios"}, "parameters.unit"),
    ({"unit": "nagios", "command": "id"}, "parameters.command"),
])
def test_restart_local_service_rejects_a_unit_off_the_list(logged_in_client, parameters, field):
    response = create(logged_in_client, actionType="restart_local_service", parameters=parameters)
    assert response.status_code == 400
    assert field in response.get_json()["data"]["fields"]


# ==========================================================
# CREATE
# ==========================================================

def test_create_returns_the_action_and_applies_the_config(logged_in_client, nagios_apply):
    response = create(logged_in_client)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["name"] == "restart-web" and data["enabled"] is True and data["version"] == 1
    assert data["actionType"] == "record_only" and data["scopeKind"] == "service"
    assert data["hostPattern"] == "web-*" and data["servicePattern"] == "HTTP"
    assert data["maxRunsPerHour"] == 2 and data["cooldownSeconds"] == 600
    nagios_apply.assert_called_once()
    listed = logged_in_client.get(f"{BASE}/actions").get_json()["data"]["items"]
    assert [item["name"] for item in listed] == ["restart-web"]


def test_defaults_apply_when_optional_fields_are_missing(logged_in_client):
    body = {"name": "minimal", "actionType": "record_only", "scopeKind": "host", "hostPattern": "web-01"}
    response = logged_in_client.post(f"{BASE}/actions", json=body)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["enabled"] is False and data["maxRunsPerHour"] == 2 and data["cooldownSeconds"] == 600
    assert data["servicePattern"] is None and data["parameters"] == {}


@pytest.mark.parametrize("changes, field", [
    ({"name": "ab"}, "name"),
    ({"name": "x" * 61}, "name"),
    ({"name": "bad;name"}, "name"),
    ({"name": 5}, "name"),
    ({"actionType": "restart_everything"}, "actionType"),
    ({"actionType": None}, "actionType"),
    ({"scopeKind": "network"}, "scopeKind"),
    ({"hostPattern": ""}, "hostPattern"),
    ({"hostPattern": "web;rm"}, "hostPattern"),
    ({"hostPattern": "web-$(id)"}, "hostPattern"),
    ({"hostPattern": "h" * 101}, "hostPattern"),
    ({"servicePattern": None}, "servicePattern"),
    ({"servicePattern": "a`b`"}, "servicePattern"),
    ({"servicePattern": "s" * 151}, "servicePattern"),
    ({"parameters": {"command": "rm -rf /"}}, "parameters.command"),
    ({"parameters": ["x"]}, "parameters"),
    ({"enabled": "yes"}, "enabled"),
    ({"enabled": 1}, "enabled"),
    ({"maxRunsPerHour": 0}, "maxRunsPerHour"),
    ({"maxRunsPerHour": 61}, "maxRunsPerHour"),
    ({"maxRunsPerHour": True}, "maxRunsPerHour"),
    ({"maxRunsPerHour": "2"}, "maxRunsPerHour"),
    ({"cooldownSeconds": 59}, "cooldownSeconds"),
    ({"cooldownSeconds": 86401}, "cooldownSeconds"),
    ({"surprise": 1}, "surprise"),
])
def test_invalid_input_is_a_400_with_the_field_named(logged_in_client, changes, field):
    response = create(logged_in_client, **changes)
    assert response.status_code == 400
    body = response.get_json()
    assert field in body["data"]["fields"]
    assert body["message"]


def test_a_host_scope_action_takes_no_service_pattern(logged_in_client):
    response = create(logged_in_client, scopeKind="host", servicePattern="HTTP")
    assert response.status_code == 400
    assert "servicePattern" in response.get_json()["data"]["fields"]


def test_a_missing_body_or_non_object_is_a_400(logged_in_client):
    assert logged_in_client.post(f"{BASE}/actions", data="nope", content_type="application/json").status_code == 400
    assert logged_in_client.post(f"{BASE}/actions", json=[1]).status_code == 400


def test_a_second_action_with_the_same_name_is_a_400_on_the_name(logged_in_client):
    assert create(logged_in_client).status_code == 201
    response = create(logged_in_client)
    assert response.status_code == 400
    assert "name" in response.get_json()["data"]["fields"]


def test_a_config_rejected_by_nagios_rolls_the_create_back(logged_in_client, db_session, nagios_apply):
    nagios_apply.return_value = ("failed", "Config failed to validate")
    response = create(logged_in_client)
    assert response.status_code == 422
    assert "Config failed to validate" in response.get_json()["message"]
    assert db_session.session.query(RemediationAction).count() == 0


# ==========================================================
# UPDATE, ENABLE, DISABLE, DELETE
# ==========================================================

def test_update_changes_fields_bumps_the_version_and_applies(logged_in_client, nagios_apply):
    created = create(logged_in_client).get_json()["data"]
    nagios_apply.reset_mock()
    body = {**PAYLOAD, "version": created["version"], "enabled": False, "cooldownSeconds": 900}
    response = logged_in_client.put(f"{BASE}/actions/{created['id']}", json=body)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["enabled"] is False and data["cooldownSeconds"] == 900 and data["version"] == 2
    nagios_apply.assert_called_once()


def test_a_stale_version_is_a_409_and_nothing_is_applied(logged_in_client, nagios_apply):
    created = create(logged_in_client).get_json()["data"]
    nagios_apply.reset_mock()
    body = {**PAYLOAD, "version": created["version"] + 5}
    assert logged_in_client.put(f"{BASE}/actions/{created['id']}", json=body).status_code == 409
    body["version"] = True
    assert logged_in_client.put(f"{BASE}/actions/{created['id']}", json=body).status_code == 409
    nagios_apply.assert_not_called()


def test_renaming_to_another_actions_name_is_a_400(logged_in_client):
    first = create(logged_in_client).get_json()["data"]
    create(logged_in_client, name="second")
    body = {**PAYLOAD, "version": first["version"], "name": "second"}
    response = logged_in_client.put(f"{BASE}/actions/{first['id']}", json=body)
    assert response.status_code == 400
    assert "name" in response.get_json()["data"]["fields"]


def test_keeping_its_own_name_on_update_is_fine(logged_in_client):
    created = create(logged_in_client).get_json()["data"]
    body = {**PAYLOAD, "version": created["version"]}
    assert logged_in_client.put(f"{BASE}/actions/{created['id']}", json=body).status_code == 200


def test_a_rejected_update_rolls_back(logged_in_client, db_session, nagios_apply):
    created = create(logged_in_client).get_json()["data"]
    nagios_apply.return_value = ("failed", "Nagios said no")
    body = {**PAYLOAD, "version": created["version"], "enabled": False}
    assert logged_in_client.put(f"{BASE}/actions/{created['id']}", json=body).status_code == 422
    db_session.session.expire_all()
    row = db_session.session.get(RemediationAction, created["id"])
    assert row.Enabled is True and row.Version == 1


def test_update_and_delete_of_a_missing_action_are_404(logged_in_client):
    assert logged_in_client.put(f"{BASE}/actions/999", json={**PAYLOAD, "version": 1}).status_code == 404
    assert logged_in_client.delete(f"{BASE}/actions/999").status_code == 404


def test_delete_removes_the_action_but_keeps_its_runs(logged_in_client, db_session, nagios_apply):
    created = create(logged_in_client).get_json()["data"]
    add_run(db_session, action_id=created["id"])
    nagios_apply.reset_mock()
    assert logged_in_client.delete(f"{BASE}/actions/{created['id']}").status_code == 200
    nagios_apply.assert_called_once()
    assert db_session.session.query(RemediationAction).count() == 0
    assert db_session.session.query(RemediationRun).count() == 1
    runs = logged_in_client.get(f"{BASE}/runs").get_json()["data"]["items"]
    assert runs[0]["actionName"] == "restart-web"


def test_a_rejected_delete_rolls_back(logged_in_client, db_session, nagios_apply):
    created = create(logged_in_client).get_json()["data"]
    nagios_apply.return_value = ("failed", "Nagios said no")
    assert logged_in_client.delete(f"{BASE}/actions/{created['id']}").status_code == 422
    assert db_session.session.query(RemediationAction).count() == 1


# ==========================================================
# RUN LOG
# ==========================================================

def test_runs_are_newest_first_and_paginated(logged_in_client, db_session):
    now = datetime.now(timezone.utc)
    for i in range(5):
        add_run(db_session, host=f"web-0{i}", received=now - timedelta(minutes=10 - i))
    first = logged_in_client.get(f"{BASE}/runs?per_page=2&page=1").get_json()["data"]
    assert [r["hostname"] for r in first["items"]] == ["web-04", "web-03"]
    assert (first["page"], first["per_page"], first["pages"], first["total"]) == (1, 2, 3, 5)
    last = logged_in_client.get(f"{BASE}/runs?per_page=2&page=3").get_json()["data"]
    assert [r["hostname"] for r in last["items"]] == ["web-00"]


def test_run_list_items_have_the_documented_fields_and_no_output(logged_in_client, db_session):
    add_run(db_session, output="recorded")
    item = logged_in_client.get(f"{BASE}/runs").get_json()["data"]["items"][0]
    assert set(item) == {"id", "actionId", "actionName", "hostname", "service", "state", "stateType", "attempt",
                         "receivedAt", "startedAt", "finishedAt", "outcome", "reason", "notifyKind", "notifyState",
                         "notifyAttempts", "notifyError", "notifyAt"}
    assert item["outcome"] == "succeeded" and item["state"] == "CRITICAL" and item["stateType"] == "HARD"


def test_run_filters(logged_in_client, db_session):
    now = datetime.now(timezone.utc)
    add_run(db_session, action_id=1, host="web-01", outcome=RemediationOutcome.SUCCEEDED, received=now)
    add_run(db_session, action_id=2, name="other", host="db-01", outcome=RemediationOutcome.SKIPPED_COOLDOWN,
            received=now - timedelta(days=5))

    def hosts(query):
        data = logged_in_client.get(f"{BASE}/runs?{query}").get_json()["data"]
        return sorted(r["hostname"] for r in data["items"])

    assert hosts("action=2") == ["db-01"]
    assert hosts("host=web-01") == ["web-01"]
    assert hosts("outcome=skipped_cooldown") == ["db-01"]
    day = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    assert hosts(f"from={day}") == ["web-01"]
    assert hosts(f"to={day}") == ["db-01"]


@pytest.mark.parametrize("query", [
    "page=0", "page=abc", "per_page=0", "per_page=101", "action=abc", "outcome=exploded", "from=yesterday", "to=2026-13-40",
])
def test_bad_run_filters_are_a_400(logged_in_client, query):
    assert logged_in_client.get(f"{BASE}/runs?{query}").status_code == 400


def test_run_detail_includes_the_output(logged_in_client, db_session):
    row = add_run(db_session, output="recorded")
    data = logged_in_client.get(f"{BASE}/runs/{row.Id}").get_json()["data"]
    assert data["output"] == "recorded" and data["actionName"] == "restart-web"
    assert logged_in_client.get(f"{BASE}/runs/999").status_code == 404


def test_skipped_runs_show_their_reason(logged_in_client, db_session):
    row = add_run(db_session, outcome=RemediationOutcome.SKIPPED_HOURLY_CAP)
    row.Reason = "Reached the limit of 2 runs per hour for this action."
    db_session.session.commit()
    item = logged_in_client.get(f"{BASE}/runs").get_json()["data"]["items"][0]
    assert item["outcome"] == "skipped_hourly_cap" and "limit" in item["reason"]


# ==========================================================
# NOTHING SECRET
# ==========================================================

def test_no_response_contains_credentials_or_internal_paths(logged_in_client, db_session):
    created = create(logged_in_client).get_json()["data"]
    add_run(db_session, action_id=created["id"])
    texts = [
        logged_in_client.get(f"{BASE}/actions").get_data(as_text=True),
        logged_in_client.get(f"{BASE}/runs").get_data(as_text=True),
        logged_in_client.get(f"{BASE}/runs/1").get_data(as_text=True),
        logged_in_client.get(f"{BASE}/action-types").get_data(as_text=True),
    ]
    for text in texts:
        for forbidden in ("password", "token", "secret", "/usr/local", "event_key"):
            assert forbidden not in text.lower(), forbidden


# ==========================================================
# AUDIT LOG
# ==========================================================

def test_changes_are_written_to_the_configuration_log(logged_in_client, db_session):
    from app.system_models import ConfigurationChanges
    created = create(logged_in_client).get_json()["data"]
    logged_in_client.put(f"{BASE}/actions/{created['id']}", json={**PAYLOAD, "version": 1, "enabled": False})
    logged_in_client.delete(f"{BASE}/actions/{created['id']}")
    types = {row.Conf_Type for row in db_session.session.query(ConfigurationChanges).all()}
    assert types == {"remediation_action"}
    assert db_session.session.query(ConfigurationChanges).count() >= 3


# ===================================================


# SAFETY CONTROLS (issue #155): run when acknowledged, skip outcomes
# ==========================================================

def test_run_when_acknowledged_defaults_to_false_and_is_returned(logged_in_client):
    body = create(logged_in_client).get_json()["data"]
    assert body["runWhenAcknowledged"] is False


def test_run_when_acknowledged_can_be_set_on_create_and_update(logged_in_client):
    body = create(logged_in_client, runWhenAcknowledged=True).get_json()["data"]
    assert body["runWhenAcknowledged"] is True
    updated = logged_in_client.put(
        f"{BASE}/actions/{body['id']}", json={**PAYLOAD, "version": body["version"], "runWhenAcknowledged": False})
    assert updated.get_json()["data"]["runWhenAcknowledged"] is False


def test_run_when_acknowledged_must_be_true_or_false(logged_in_client):
    response = create(logged_in_client, runWhenAcknowledged="yes")
    assert response.status_code == 400
    assert "runWhenAcknowledged" in response.get_json()["data"]["fields"]


def test_run_when_acknowledged_change_is_written_to_the_configuration_log(logged_in_client, db_session):
    from app.system_models import ConfigurationChanges
    create(logged_in_client, runWhenAcknowledged=True)
    fields = [c.Parameter_Name for c in db_session.session.query(ConfigurationChanges).all()]
    assert "runWhenAcknowledged" in fields


@pytest.mark.parametrize("outcome", [
    RemediationOutcome.SKIPPED_KILL_SWITCH, RemediationOutcome.SKIPPED_MAINTENANCE,
    RemediationOutcome.SKIPPED_DOWNTIME, RemediationOutcome.SKIPPED_ACKNOWLEDGED,
])
def test_the_new_skip_outcomes_can_be_filtered_and_show_their_reason(logged_in_client, db_session, outcome):
    row = add_run(db_session, outcome=outcome)
    row.Reason = "why"
    db_session.session.commit()
    add_run(db_session, outcome=RemediationOutcome.SUCCEEDED, host="web-02")
    items = logged_in_client.get(f"{BASE}/runs?outcome={outcome.value}").get_json()["data"]["items"]
    assert [(i["outcome"], i["reason"]) for i in items] == [(outcome.value, "why")]


# ==========================================================
# CONSUMER HEALTH (issue #155)
# ==========================================================

def set_state(db_session, **fields):
    from app.system_models import RemediationConsumerState
    row = db_session.session.get(RemediationConsumerState, 1) or RemediationConsumerState(Id=1, Dropped_Count=0)
    for name, value in fields.items():
        setattr(row, name, value)
    db_session.session.add(row)
    db_session.session.commit()


def health(client):
    response = client.get(f"{BASE}/health")
    assert response.status_code == 200
    return response.get_json()["data"]


def test_view_alone_can_read_health(limited_client, db_session, regular_role):
    grant(db_session, regular_role, "remediation.view")
    assert limited_client.get(f"{BASE}/health").status_code == 200


def test_a_recent_heartbeat_is_not_stalled(logged_in_client, db_session, tmp_path, app):
    app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
    set_state(db_session, Last_Tick_At=datetime.now(timezone.utc) - timedelta(seconds=10))
    data = health(logged_in_client)
    assert data["stalled"] is False
    assert data["lastError"] is None and data["lastTickAt"]
    assert data["backlog"] == 0 and data["oldestSpoolAgeSeconds"] is None


def test_a_heartbeat_older_than_three_intervals_is_stalled(logged_in_client, db_session, tmp_path, app):
    app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
    set_state(db_session, Last_Tick_At=datetime.now(timezone.utc) - timedelta(seconds=50))  # 3 x 15 = 45
    assert health(logged_in_client)["stalled"] is True


def test_no_heartbeat_at_all_is_stalled(logged_in_client, db_session, tmp_path, app):
    app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
    data = health(logged_in_client)
    assert data["stalled"] is True and data["lastTickAt"] is None


def test_health_counts_the_backlog_and_the_oldest_file(logged_in_client, db_session, tmp_path, app):
    import os
    import time
    app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
    set_state(db_session, Last_Tick_At=datetime.now(timezone.utc))
    for n, age in enumerate((120, 30)):
        path = tmp_path / f"176043210000000000{n}-{n}.json"
        path.write_text("{}")
        os.utime(path, (time.time() - age, time.time() - age))
    (tmp_path / "unrelated.txt").write_text("x")
    data = health(logged_in_client)
    assert data["backlog"] == 2
    assert 110 <= data["oldestSpoolAgeSeconds"] <= 140


def test_health_reports_runs_caps_and_drops_in_the_last_24_hours(logged_in_client, db_session, tmp_path, app):
    app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
    now = datetime.now(timezone.utc)
    set_state(db_session, Last_Tick_At=now, Dropped_Count=4, Dropped_At=now)
    add_run(db_session, outcome=RemediationOutcome.SUCCEEDED, received=now - timedelta(hours=1), key="a")
    add_run(db_session, outcome=RemediationOutcome.FAILED, received=now - timedelta(hours=2), key="b")
    add_run(db_session, outcome=RemediationOutcome.SKIPPED_HOURLY_CAP, received=now - timedelta(hours=3), key="c")
    add_run(db_session, outcome=RemediationOutcome.SKIPPED_KILL_SWITCH, received=now - timedelta(hours=3), key="d")
    add_run(db_session, outcome=RemediationOutcome.SUCCEEDED, received=now - timedelta(hours=30), key="e")
    data = health(logged_in_client)
    assert data["runsLast24h"] == 2          # started actions only
    assert data["capsHitLast24h"] == 1
    assert data["skippedLast24h"] == 2       # every skip, including the cap
    assert data["droppedTotal"] == 4 and data["droppedAt"]


def test_health_shows_the_last_error_without_a_path(logged_in_client, db_session, tmp_path, app):
    app.config["REMEDIATION_SPOOL_DIR"] = str(tmp_path)
    set_state(db_session, Last_Tick_At=datetime.now(timezone.utc), Last_Error="The spool folder could not be read.")
    data = health(logged_in_client)
    assert data["lastError"] == "The spool folder could not be read."
    assert str(tmp_path) not in str(data)


# ==========================================================
# KILL SWITCH AND RETENTION SETTINGS (issue #155)
# ==========================================================

SETTINGS_URL = f"{BASE}/settings"


def saved_settings(db_session):
    from app.system_models import SystemSettings
    db_session.session.expire_all()
    return db_session.session.get(SystemSettings, 1)


def test_settings_default_to_switch_on_and_ninety_days(logged_in_client, db_session):
    response = logged_in_client.get(SETTINGS_URL)
    assert response.status_code == 200
    assert response.get_json()["data"] == {
        "enabled": True, "retentionDays": 90, "repeatCount": 3, "repeatWindowHours": 24}


def test_settings_need_login_and_the_matching_permission(limited_client, db_session, regular_role):
    assert limited_client.get(SETTINGS_URL).status_code == 403
    assert limited_client.put(SETTINGS_URL, json={"enabled": False}).status_code == 403
    grant(db_session, regular_role, "remediation.view")
    assert limited_client.get(SETTINGS_URL).status_code == 200
    assert limited_client.put(SETTINGS_URL, json={"enabled": False}).status_code == 403
    assert saved_settings(db_session) is None or saved_settings(db_session).Remediation_Enabled is True


def test_manage_can_switch_automatic_recovery_off_and_on(logged_in_client, db_session):
    off = logged_in_client.put(SETTINGS_URL, json={"enabled": False})
    assert off.status_code == 200 and off.get_json()["data"]["enabled"] is False
    assert saved_settings(db_session).Remediation_Enabled is False
    assert logged_in_client.get(SETTINGS_URL).get_json()["data"]["enabled"] is False
    on = logged_in_client.put(SETTINGS_URL, json={"enabled": True})
    assert on.get_json()["data"]["enabled"] is True


def test_retention_can_be_changed_and_leaves_the_switch_alone(logged_in_client, db_session):
    logged_in_client.put(SETTINGS_URL, json={"enabled": False})
    response = logged_in_client.put(SETTINGS_URL, json={"retentionDays": 30})
    assert response.get_json()["data"] == {
        "enabled": False, "retentionDays": 30, "repeatCount": 3, "repeatWindowHours": 24}


@pytest.mark.parametrize("body, field", [
    ({"enabled": "no"}, "enabled"),
    ({"enabled": 1}, "enabled"),
    ({"retentionDays": 6}, "retentionDays"),
    ({"retentionDays": 3651}, "retentionDays"),
    ({"retentionDays": "90"}, "retentionDays"),
    ({"retentionDays": True}, "retentionDays"),
    ({"retentionDays": 30.5}, "retentionDays"),
    ({"other": 1}, "other"),
    ({}, "body"),
])
def test_bad_settings_are_a_400_naming_the_field_and_save_nothing(logged_in_client, db_session, body, field):
    response = logged_in_client.put(SETTINGS_URL, json=body)
    assert response.status_code == 400
    assert field in response.get_json()["data"]["fields"]
    settings = saved_settings(db_session)
    assert settings is None or (settings.Remediation_Enabled is True and settings.Remediation_Retention_Days == 90)


def test_a_non_object_body_is_a_400(logged_in_client):
    assert logged_in_client.put(SETTINGS_URL, json=[1]).status_code == 400


def test_each_changed_setting_is_audited_and_unchanged_ones_are_not(logged_in_client, db_session):
    from app.system_models import ConfigurationChanges
    logged_in_client.put(SETTINGS_URL, json={"enabled": False, "retentionDays": 90})
    rows = db_session.session.query(ConfigurationChanges).all()
    assert [(r.Conf_Type, r.Parameter_Name, r.Old_Value, r.New_Value) for r in rows] == [
        ("remediation_setting", "enabled", "True", "False")]


def test_settings_changes_are_not_audited_when_audit_logging_is_off(logged_in_client, db_session):
    from app.system_models import ConfigurationChanges, SystemSettings
    db_session.session.add(SystemSettings(Id=1, Audit_Logging=False))
    db_session.session.commit()
    logged_in_client.put(SETTINGS_URL, json={"enabled": False})
    assert db_session.session.query(ConfigurationChanges).count() == 0
    assert saved_settings(db_session).Remediation_Enabled is False


def test_changing_the_switch_does_not_touch_the_settings_page_version(logged_in_client, db_session):
    from app.system_models import SystemSettings
    db_session.session.add(SystemSettings(Id=1, Version=7))
    db_session.session.commit()
    logged_in_client.put(SETTINGS_URL, json={"enabled": False})
    assert saved_settings(db_session).Version == 7


def test_the_general_settings_response_does_not_carry_the_remediation_fields(logged_in_client, db_session):
    data = logged_in_client.get("/api/system").get_json()["data"]
    assert "remediationEnabled" not in data and "remediationRetentionDays" not in data


def test_deleted_action_history_does_not_limit_a_replacement(logged_in_client, db_session):
    from app.remediation import skip_reason

    created = create(logged_in_client).get_json()["data"]
    old = add_run(db_session, action_id=created["id"])
    old.Started_At = datetime.now(timezone.utc)
    db_session.session.commit()
    assert logged_in_client.delete(f"{BASE}/actions/{created['id']}").status_code == 200
    replacement = create(logged_in_client, name="replacement").get_json()["data"]
    db_session.session.expire_all()
    run = db_session.session.get(RemediationRun, old.Id)
    assert run.Action_Id is None
    assert run.Action_Name == "restart-web"
    action = db_session.session.get(RemediationAction, replacement["id"])
    assert skip_reason(action, {"host": "web-01", "service": "HTTP"}, datetime.now(timezone.utc)) is None


def test_rejected_delete_preserves_run_link(logged_in_client, db_session, nagios_apply):
    created = create(logged_in_client).get_json()["data"]
    run = add_run(db_session, action_id=created["id"])
    nagios_apply.return_value = ("failed", "Nagios said no")
    assert logged_in_client.delete(f"{BASE}/actions/{created['id']}").status_code == 422
    db_session.session.expire_all()
    assert db_session.session.get(RemediationRun, run.Id).Action_Id == created["id"]


def test_run_action_link_is_a_nullable_set_null_foreign_key():
    foreign_keys = list(RemediationRun.__table__.c.Action_Id.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "REMEDIATION_ACTION.Id"
    assert foreign_keys[0].ondelete == "SET NULL"
    assert RemediationRun.__table__.c.Action_Id.nullable


# ==========================================================
# OPERATOR NOTIFICATION (#153)
# ==========================================================

def test_notify_on_defaults_to_all_three_kinds(logged_in_client):
    body = create(logged_in_client).get_json()["data"]
    assert body["notifyOn"] == ["failed", "capped", "repeated"]


def test_notify_on_can_be_set_emptied_and_changed(logged_in_client):
    body = create(logged_in_client, notifyOn=["failed"]).get_json()["data"]
    assert body["notifyOn"] == ["failed"]
    updated = logged_in_client.put(
        f"{BASE}/actions/{body['id']}", json={**PAYLOAD, "version": body["version"], "notifyOn": []})
    assert updated.get_json()["data"]["notifyOn"] == []


def test_notify_on_is_stored_without_duplicates_in_a_fixed_order(logged_in_client):
    body = create(logged_in_client, notifyOn=["repeated", "failed", "failed"]).get_json()["data"]
    assert body["notifyOn"] == ["failed", "repeated"]


@pytest.mark.parametrize("value", ["failed", ["nope"], ["failed", 1], [None], {"failed": True}, 5, True])
def test_a_bad_notify_on_is_a_400_on_that_field(logged_in_client, value):
    response = create(logged_in_client, notifyOn=value)
    assert response.status_code == 400
    assert "notifyOn" in response.get_json()["data"]["fields"]


def test_a_notify_on_change_is_written_to_the_configuration_log(logged_in_client, db_session):
    from app.system_models import ConfigurationChanges
    body = create(logged_in_client).get_json()["data"]
    db_session.session.query(ConfigurationChanges).delete()
    db_session.session.commit()
    logged_in_client.put(
        f"{BASE}/actions/{body['id']}", json={**PAYLOAD, "version": body["version"], "notifyOn": ["failed"]})
    rows = db_session.session.query(ConfigurationChanges).all()
    assert [(r.Parameter_Name, r.New_Value) for r in rows] == [("notifyOn", "['failed']")]


def test_a_run_shows_its_notification_state(logged_in_client, db_session):
    from app.system_models import RemediationNotifyState
    row = add_run(db_session, outcome=RemediationOutcome.FAILED)
    row.Notify_Kind, row.Notify_State, row.Notify_Attempts = "failed", RemediationNotifyState.FAILED, 3
    row.Notify_Error, row.Notify_At = "The Nagios command pipe was not found.", datetime.now(timezone.utc)
    db_session.session.commit()
    for url in (f"{BASE}/runs/{row.Id}", f"{BASE}/runs"):
        data = logged_in_client.get(url).get_json()["data"]
        item = data if "id" in data else data["items"][0]
        assert (item["notifyKind"], item["notifyState"], item["notifyAttempts"]) == ("failed", "failed", 3)
        assert item["notifyError"] == "The Nagios command pipe was not found."
        assert item["notifyAt"]


def test_a_run_with_no_notification_due_has_empty_notify_fields(logged_in_client, db_session):
    row = add_run(db_session)
    item = logged_in_client.get(f"{BASE}/runs/{row.Id}").get_json()["data"]
    assert (item["notifyKind"], item["notifyState"], item["notifyAttempts"], item["notifyError"]) == (
        None, None, 0, None)


def test_repeat_settings_can_be_changed_and_leave_the_rest_alone(logged_in_client, db_session):
    response = logged_in_client.put(SETTINGS_URL, json={"repeatCount": 5, "repeatWindowHours": 48})
    assert response.get_json()["data"] == {
        "enabled": True, "retentionDays": 90, "repeatCount": 5, "repeatWindowHours": 48}
    settings = saved_settings(db_session)
    assert (settings.Remediation_Repeat_Count, settings.Remediation_Repeat_Window_Hours) == (5, 48)


@pytest.mark.parametrize("body, field", [
    ({"repeatCount": 1}, "repeatCount"),
    ({"repeatCount": 21}, "repeatCount"),
    ({"repeatCount": "3"}, "repeatCount"),
    ({"repeatCount": True}, "repeatCount"),
    ({"repeatWindowHours": 0}, "repeatWindowHours"),
    ({"repeatWindowHours": 169}, "repeatWindowHours"),
    ({"repeatWindowHours": 2.5}, "repeatWindowHours"),
])
def test_bad_repeat_settings_are_a_400_and_save_nothing(logged_in_client, db_session, body, field):
    response = logged_in_client.put(SETTINGS_URL, json=body)
    assert response.status_code == 400
    assert field in response.get_json()["data"]["fields"]
    settings = saved_settings(db_session)
    assert settings is None or (settings.Remediation_Repeat_Count, settings.Remediation_Repeat_Window_Hours) == (3, 24)


def test_a_repeat_setting_change_is_audited(logged_in_client, db_session):
    from app.system_models import ConfigurationChanges
    logged_in_client.put(SETTINGS_URL, json={"repeatCount": 4})
    rows = db_session.session.query(ConfigurationChanges).all()
    assert [(r.Conf_Type, r.Parameter_Name, r.Old_Value, r.New_Value) for r in rows] == [
        ("remediation_setting", "repeatCount", "3", "4")]


# ==========================================================
# LAST RUN PER SERVICE (#153, the badge on a service row)
# ==========================================================

LAST_RUNS_URL = f"{BASE}/last-runs"


def test_last_runs_need_the_view_permission(limited_client, db_session, regular_role):
    assert limited_client.get(LAST_RUNS_URL).status_code == 403
    grant(db_session, regular_role, "remediation.view")
    assert limited_client.get(LAST_RUNS_URL).status_code == 200


def test_last_runs_return_the_newest_run_for_each_host_and_service(logged_in_client, db_session):
    now = datetime.now(timezone.utc)
    add_run(db_session, outcome=RemediationOutcome.FAILED, received=now - timedelta(hours=3), key="a")
    newest = add_run(db_session, outcome=RemediationOutcome.SUCCEEDED, received=now - timedelta(hours=1), key="b")
    other = add_run(db_session, host="web-02", service="SSH", outcome=RemediationOutcome.FAILED, received=now, key="c")
    items = logged_in_client.get(LAST_RUNS_URL).get_json()["data"]["items"]
    by_key = {(i["hostname"], i["service"]): i for i in items}
    assert set(by_key) == {("web-01", "HTTP"), ("web-02", "SSH")}
    assert by_key[("web-01", "HTTP")]["runId"] == newest.Id and by_key[("web-01", "HTTP")]["outcome"] == "succeeded"
    assert by_key[("web-02", "SSH")]["runId"] == other.Id


def test_last_runs_carry_the_notification_state_and_no_output(logged_in_client, db_session):
    from app.system_models import RemediationNotifyState
    row = add_run(db_session, outcome=RemediationOutcome.FAILED, output="secret=abc")
    row.Notify_Kind, row.Notify_State = "failed", RemediationNotifyState.SENT
    db_session.session.commit()
    (item,) = logged_in_client.get(LAST_RUNS_URL).get_json()["data"]["items"]
    assert set(item) == {"runId", "hostname", "service", "outcome", "notifyState", "receivedAt"}
    assert item["notifyState"] == "sent"
    assert "secret" not in str(item)


def test_last_runs_ignore_runs_older_than_seven_days(logged_in_client, db_session):
    add_run(db_session, outcome=RemediationOutcome.FAILED, received=datetime.now(timezone.utc) - timedelta(days=8))
    assert logged_in_client.get(LAST_RUNS_URL).get_json()["data"]["items"] == []


def test_a_host_level_run_has_no_service(logged_in_client, db_session):
    add_run(db_session, service=None, outcome=RemediationOutcome.FAILED)
    (item,) = logged_in_client.get(LAST_RUNS_URL).get_json()["data"]["items"]
    assert item["service"] is None


def test_last_runs_are_bounded(logged_in_client, db_session, monkeypatch):
    from app.api.system import remediation as module
    monkeypatch.setattr(module, "MAX_LAST_RUNS", 2)
    for n in range(4):
        add_run(db_session, service=f"svc-{n}", key=f"k{n}")
    assert len(logged_in_client.get(LAST_RUNS_URL).get_json()["data"]["items"]) == 2


# ==========================================================
# TARGETS (device and service suggestions for the form)
# ==========================================================

def test_targets_list_devices_with_the_services_seen_on_them(logged_in_client, db_session, admin_user):
    from app.system_models import DeviceState, NetworkDiscovery
    from tests.support.identity_helpers import NET, make_status
    from tests.support.seed_helpers import _make_service, _ts

    status = make_status(db_session, admin_user)
    db_session.session.add(NetworkDiscovery(
        Hostname="fileserver", Nagios_Host_Name="nas-01", IP_Address="10.0.0.5", Network=NET, DiscoveryStatusID=status))
    db_session.session.add(NetworkDiscovery(
        Hostname=None, IP_Address="10.0.0.8", Network=NET, DiscoveryStatusID=status))
    db_session.session.add(NetworkDiscovery(
        Hostname="gone", Nagios_Host_Name="gone-01", IP_Address="10.0.0.9", Network=NET, DiscoveryStatusID=status,
        Device_State=DeviceState.MERGED))
    _make_service(db_session, hostname="web-01", service="HTTP")
    _make_service(db_session, hostname="web-01", service="HTTP", ts=_ts(-30))
    _make_service(db_session, hostname="web-01", service="SSH")
    _make_service(db_session, hostname="old-01", service="FTP", ts=_ts(-30 * 86400))
    db_session.session.commit()

    items = logged_in_client.get(f"{BASE}/targets").get_json()["data"]["items"]

    assert items == [
        {"hostname": "10.0.0.8", "services": []},
        {"hostname": "nas-01", "services": []},
        {"hostname": "web-01", "services": ["HTTP", "SSH"]},
    ]
