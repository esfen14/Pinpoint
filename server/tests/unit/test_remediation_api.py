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

READ_URLS = [f"{BASE}/action-types", f"{BASE}/actions", f"{BASE}/runs", f"{BASE}/runs/1"]


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
                         "receivedAt", "startedAt", "finishedAt", "outcome", "reason"}
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
