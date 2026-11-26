"""
Tests for "Remember me" on POST /api/user/login (#337).

A remembered sign-in gets a persistent session cookie (30 days) and skips the
idle timeout; an ordinary sign-in keeps the browser-session cookie and the idle
timeout. The idle gap is simulated by ageing the session record, as in
test_session_timeout.py.
"""
from datetime import timedelta

import pytest

import config as config_module
from app.system_models import ActivityLog, SystemSettings, User, UserStatus
from tests.support.session_helpers import set_idle_minutes

LOGIN = {"email": "admin@example.com", "password": "AdminPass1!"}


def login(client, **extra):
    """Sign in as the admin fixture user, adding any extra JSON fields."""
    return client.post("/api/user/login", json={**LOGIN, **extra})


def session_cookie(response):
    """Return the Set-Cookie header for the session cookie, or None."""
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("session="):
            return header
    return None


def set_session_timeout(db_session, minutes):
    db_session.session.add(SystemSettings(Id=1, Session_Timeout=minutes))
    db_session.session.commit()


class TestRememberMeLogin:
    def test_remembered_login_sets_persistent_cookie(self, client, db_session, admin_user):
        resp = login(client, remember_me=True)

        assert resp.status_code == 200
        assert "Expires=" in session_cookie(resp)

    def test_unremembered_login_sets_browser_session_cookie(self, client, db_session, admin_user):
        resp = login(client)

        assert resp.status_code == 200
        assert "Expires=" not in session_cookie(resp)

    def test_false_behaves_like_omitted(self, client, db_session, admin_user):
        resp = login(client, remember_me=False)

        assert resp.status_code == 200
        assert "Expires=" not in session_cookie(resp)

    @pytest.mark.parametrize("value", ["true", 1, "yes", None, []])
    def test_non_boolean_is_rejected(self, client, db_session, admin_user, value):
        resp = login(client, remember_me=value)

        assert resp.status_code == 400
        assert "remember_me" in resp.get_json()["message"]
        assert client.get("/api/user/me").status_code == 401

    def test_wrong_password_never_remembers(self, client, db_session, admin_user):
        resp = client.post(
            "/api/user/login",
            json={"email": "admin@example.com", "password": "nope", "remember_me": True},
        )

        assert resp.status_code == 401
        assert session_cookie(resp) is None


class TestRememberedSessionIdleTimeout:
    def test_remembered_session_survives_idle_gap(self, client, db_session, admin_user):
        set_session_timeout(db_session, 15)
        login(client, remember_me=True)
        set_idle_minutes(client, 60 * 24 * 7)

        assert client.get("/api/user/me").status_code == 200

    def test_unremembered_session_still_expires(self, client, db_session, admin_user):
        set_session_timeout(db_session, 15)
        login(client)
        set_idle_minutes(client, 16)

        assert client.get("/api/user/me").status_code == 401

    def test_me_reports_remembered_flag(self, client, db_session, admin_user):
        login(client, remember_me=True)

        assert client.get("/api/user/me").get_json()["data"]["remembered"] is True

    def test_me_reports_not_remembered(self, client, db_session, admin_user):
        login(client)

        assert client.get("/api/user/me").get_json()["data"]["remembered"] is False

    def test_logout_ends_remembered_session(self, client, db_session, admin_user):
        login(client, remember_me=True)

        assert client.post("/api/user/logout").status_code == 200
        assert client.get("/api/user/me").status_code == 401
        with client.session_transaction() as sess:
            assert "remembered" not in sess

    def test_next_plain_login_is_not_remembered(self, client, db_session, admin_user):
        login(client, remember_me=True)
        client.post("/api/user/logout")
        set_session_timeout(db_session, 15)
        login(client)
        set_idle_minutes(client, 16)

        assert client.get("/api/user/me").status_code == 401

    def test_deactivated_account_is_signed_out_even_if_remembered(
        self, client, db_session, admin_user
    ):
        login(client, remember_me=True)
        user = db_session.session.get(User, admin_user.UserID)
        user.Status = UserStatus.INACTIVE
        db_session.session.commit()

        resp = client.get("/api/user/me")

        assert resp.status_code == 401
        assert client.get("/api/user/me").status_code == 401


class TestRememberMeAudit:
    def test_audit_entry_notes_remembered_sign_in(self, client, db_session, admin_user):
        login(client, remember_me=True)

        actions = [row.Action_Type for row in db_session.session.query(ActivityLog).all()]
        assert "Signed in (admin@example.com), remembered for 30 days" in actions

    def test_audit_entry_plain_sign_in_unchanged(self, client, db_session, admin_user):
        login(client)

        actions = [row.Action_Type for row in db_session.session.query(ActivityLog).all()]
        assert "Signed in (admin@example.com)" in actions


class TestSessionCookieConfig:
    def test_remembered_lifetime_defaults_to_30_days(self, app):
        assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(days=30)

    def test_cookie_flags(self, app):
        assert app.config["SESSION_COOKIE_HTTPONLY"] is True
        assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"

    def test_lifetime_days_env_override(self, monkeypatch):
        monkeypatch.setenv("PINPOINT_REMEMBER_ME_DAYS", "7")

        assert config_module.remember_me_lifetime() == timedelta(days=7)

    @pytest.mark.parametrize("value", ["0", "-3", "abc", "1.5"])
    def test_lifetime_days_env_rejects_bad_value(self, monkeypatch, value):
        monkeypatch.setenv("PINPOINT_REMEMBER_ME_DAYS", value)

        with pytest.raises(ValueError):
            config_module.remember_me_lifetime()
