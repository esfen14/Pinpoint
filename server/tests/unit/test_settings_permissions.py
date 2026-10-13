"""
Tests for per-tab settings permissions (PUT /api/system) and for
/api/user/me hiding permissions when the user's role is inactive.

General settings are open to every logged-in user. Security fields need
"settings.security" and System fields need "settings.system".
limited_client's role has neither; logged_in_client's role has all.
"""
from unittest.mock import patch

import pytest

from app.system_models import Permission, RolePermission, SystemSettings


def current_settings(client):
    resp = client.get("/api/system")
    assert resp.status_code == 200
    return resp.get_json()["data"]


def save(client, **changes):
    payload = current_settings(client)
    payload.update(changes)
    return client.put("/api/system", json=payload)


def stored(db_session):
    db_session.session.expire_all()
    return db_session.session.get(SystemSettings, 1)


def grant(db_session, role, permission_name):
    permission = db_session.session.query(Permission).filter_by(Name=permission_name).one()
    db_session.session.add(RolePermission(RoleID=role.RoleID, PermissionID=permission.PermissionID))
    db_session.session.commit()


class TestSettingsPermissions:
    def test_any_user_can_change_general_settings(self, limited_client, db_session):
        resp = save(limited_client, scanFrequency=12, notifications=False)

        assert resp.status_code == 200
        assert stored(db_session).Scan_Frequency == 12
        assert stored(db_session).Notifications is False

    @pytest.mark.parametrize("field, value, tab", [
        ("sessionTimeout", 60, "Security"),
        ("auditLogging", False, "Security"),
        ("maintenanceMode", True, "System"),
        ("logRetentionDays", 7, "System"),
    ])
    def test_restricted_field_needs_permission(self, limited_client, db_session, field, value, tab):
        before = current_settings(limited_client)

        resp = save(limited_client, **{field: value})

        assert resp.status_code == 403
        assert f"{tab} settings" in resp.get_json()["message"]
        assert current_settings(limited_client)[field] == before[field]
        assert current_settings(limited_client)["version"] == before["version"]

    def test_denied_save_changes_nothing_else(self, limited_client, db_session):
        resp = save(limited_client, scanFrequency=12, sessionTimeout=60)

        assert resp.status_code == 403
        assert stored(db_session).Scan_Frequency != 12

    def test_names_both_tabs_when_both_denied(self, limited_client, db_session):
        resp = save(limited_client, sessionTimeout=60, maintenanceMode=True)

        assert resp.status_code == 403
        assert "Security and System settings" in resp.get_json()["message"]

    def test_security_permission_allows_security_only(self, limited_client, db_session, regular_role):
        grant(db_session, regular_role, "settings.security")

        allowed = save(limited_client, sessionTimeout=60)
        denied = save(limited_client, maintenanceMode=True)

        assert allowed.status_code == 200
        assert stored(db_session).Session_Timeout == 60
        assert denied.status_code == 403

    def test_system_permission_allows_system_only(self, limited_client, db_session, regular_role):
        grant(db_session, regular_role, "settings.system")

        allowed = save(limited_client, maintenanceMode=True)
        denied = save(limited_client, sessionTimeout=60)

        assert allowed.status_code == 200
        assert stored(db_session).Maintenance_Mode is True
        assert denied.status_code == 403

    def test_admin_can_change_everything(self, logged_in_client, db_session):
        resp = save(logged_in_client, scanFrequency=3, sessionTimeout=60, maintenanceMode=True)

        assert resp.status_code == 200
        settings = stored(db_session)
        assert (settings.Scan_Frequency, settings.Session_Timeout, settings.Maintenance_Mode) == (3, 60, True)

    def test_check_interval_requires_system_permission(self, limited_client, db_session):
        resp = save(limited_client, checkInterval=2)
        assert resp.status_code == 403
        assert stored(db_session).Check_Interval == 5

    @pytest.mark.parametrize("value", [0, 3, 16, "2", True])
    def test_invalid_check_interval_is_rejected(self, logged_in_client, db_session, value):
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status") as apply:
            resp = save(logged_in_client, checkInterval=value)
        assert resp.status_code == 400
        assert stored(db_session).Check_Interval == 5
        apply.assert_not_called()

    @pytest.mark.parametrize("status", ["applied", "unchanged"])
    def test_check_interval_applies_through_shared_writer(self, logged_in_client, db_session, status):
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=(status, "ok")) as apply:
            resp = save(logged_in_client, checkInterval=2)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["checkInterval"] == 2
        assert stored(db_session).Check_Interval == 2
        apply.assert_called_once_with()

    @pytest.mark.parametrize("reason", ["Config failed to validate", "Nagios reload failed"])
    def test_failed_apply_restores_setting(self, logged_in_client, db_session, reason):
        before = current_settings(logged_in_client)
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=("failed", reason)):
            resp = save(logged_in_client, checkInterval=2)
        assert resp.status_code != 200
        assert reason in resp.get_json()["message"]
        assert stored(db_session).Check_Interval == 5
        assert current_settings(logged_in_client)["version"] == before["version"]

    def test_check_timing_defaults_are_served(self, logged_in_client):
        data = current_settings(logged_in_client)
        assert data["retryInterval"] == 1
        assert data["maxCheckAttempts"] == 3

    @pytest.mark.parametrize("field", ["retryInterval", "maxCheckAttempts"])
    def test_check_timing_requires_system_permission(self, limited_client, db_session, field):
        resp = save(limited_client, **{field: 2})
        assert resp.status_code == 403
        assert "System settings" in resp.get_json()["message"]
        assert stored(db_session).Retry_Interval == 1
        assert stored(db_session).Max_Check_Attempts == 3

    @pytest.mark.parametrize("changes", [
        {"retryInterval": 0}, {"retryInterval": 11}, {"retryInterval": "2"}, {"retryInterval": True},
        {"retryInterval": 2.5}, {"maxCheckAttempts": 0}, {"maxCheckAttempts": 11},
        {"maxCheckAttempts": "3"}, {"maxCheckAttempts": False}, {"maxCheckAttempts": None},
    ])
    def test_out_of_range_check_timing_is_rejected(self, logged_in_client, db_session, changes):
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status") as apply:
            resp = save(logged_in_client, **changes)
        assert resp.status_code == 400
        assert stored(db_session).Retry_Interval == 1
        assert stored(db_session).Max_Check_Attempts == 3
        apply.assert_not_called()

    def test_retry_interval_may_not_exceed_the_check_interval(self, logged_in_client, db_session):
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status") as apply:
            too_long = save(logged_in_client, checkInterval=2, retryInterval=3)
            lowered_interval = save(logged_in_client, checkInterval=1, retryInterval=2)
        assert too_long.status_code == 400
        assert "retry interval" in too_long.get_json()["message"].lower()
        assert lowered_interval.status_code == 400
        assert stored(db_session).Retry_Interval == 1
        apply.assert_not_called()

    def test_retry_interval_equal_to_the_check_interval_is_allowed(self, logged_in_client, db_session):
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=("applied", "ok")):
            resp = save(logged_in_client, checkInterval=2, retryInterval=2)
        assert resp.status_code == 200
        assert stored(db_session).Retry_Interval == 2

    @pytest.mark.parametrize("changes, status", [
        ({"retryInterval": 3}, "applied"),
        ({"maxCheckAttempts": 5}, "applied"),
        ({"retryInterval": 2, "maxCheckAttempts": 4}, "unchanged"),
    ])
    def test_check_timing_applies_through_the_shared_writer(self, logged_in_client, db_session, changes, status):
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=(status, "ok")) as apply:
            resp = save(logged_in_client, **changes)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        for key, value in changes.items():
            assert data[key] == value
        apply.assert_called_once_with()

    def test_failed_apply_restores_check_timing(self, logged_in_client, db_session):
        before = current_settings(logged_in_client)
        with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=("failed", "Config failed to validate")):
            resp = save(logged_in_client, maxCheckAttempts=7, retryInterval=2)
        assert resp.status_code == 422
        assert "Config failed to validate" in resp.get_json()["message"]
        assert stored(db_session).Max_Check_Attempts == 3
        assert stored(db_session).Retry_Interval == 1
        assert current_settings(logged_in_client)["version"] == before["version"]

    def test_a_client_that_omits_the_new_fields_keeps_them_unchanged(self, logged_in_client, db_session):
        payload = current_settings(logged_in_client)
        del payload["retryInterval"], payload["maxCheckAttempts"]
        payload["scanFrequency"] = 12
        resp = logged_in_client.put("/api/system", json=payload)
        assert resp.status_code == 200
        assert stored(db_session).Retry_Interval == 1
        assert stored(db_session).Max_Check_Attempts == 3

    def test_inactive_role_loses_restricted_tabs(self, logged_in_client, db_session, admin_role):
        admin_role.Is_Active = False
        db_session.session.commit()

        resp = save(logged_in_client, sessionTimeout=60)

        assert resp.status_code == 403


class TestMePermissions:
    def test_me_lists_role_permissions(self, logged_in_client, db_session):
        permissions = logged_in_client.get("/api/user/me").get_json()["data"]["permissions"]

        assert "settings.security" in permissions
        assert "settings.system" in permissions

    def test_me_has_no_permissions_when_role_inactive(self, logged_in_client, db_session, admin_role):
        admin_role.Is_Active = False
        db_session.session.commit()

        data = logged_in_client.get("/api/user/me").get_json()["data"]

        assert data["permissions"] == []
        assert data["role"] == admin_role.Name
