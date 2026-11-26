"""
Tests for the idle session timeout (enforce_session_timeout in
app/api/user/login.py), driven by SystemSettings.Session_Timeout.

The last-activity time lives in the session's database record, so tests
move it into the past there instead of waiting for real time to pass.
"""
import pytest

from app.system_models import SystemSettings
from tests.support.session_helpers import get_last_activity, set_idle_minutes


def set_session_timeout(db_session, minutes):
    db_session.session.add(SystemSettings(Id=1, Session_Timeout=minutes))
    db_session.session.commit()


class TestSessionTimeout:
    def test_login_records_last_activity(self, logged_in_client):
        assert get_last_activity(logged_in_client) is not None

    def test_request_within_timeout_succeeds(self, logged_in_client, db_session):
        set_session_timeout(db_session, 15)
        set_idle_minutes(logged_in_client, 10)

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == 200

    def test_request_refreshes_last_activity(self, logged_in_client, db_session):
        set_session_timeout(db_session, 15)
        set_idle_minutes(logged_in_client, 10)
        before = get_last_activity(logged_in_client)

        logged_in_client.get("/api/user/me")

        assert get_last_activity(logged_in_client) > before

    def test_request_after_timeout_is_rejected(self, logged_in_client, db_session):
        set_session_timeout(db_session, 15)
        set_idle_minutes(logged_in_client, 16)

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == 401
        body = resp.get_json()
        assert body["success"] is False
        assert "Session expired" in body["message"]

    def test_expired_session_stays_logged_out(self, logged_in_client, db_session):
        set_session_timeout(db_session, 15)
        set_idle_minutes(logged_in_client, 16)
        logged_in_client.get("/api/user/me")

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == 401
        assert get_last_activity(logged_in_client) is None

    def test_longer_setting_allows_longer_idle(self, logged_in_client, db_session):
        set_session_timeout(db_session, 60)
        set_idle_minutes(logged_in_client, 40)

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == 200

    @pytest.mark.parametrize("idle_minutes, expected_status", [(29, 200), (31, 401)])
    def test_defaults_to_30_minutes_without_settings_row(
        self, logged_in_client, idle_minutes, expected_status
    ):
        set_idle_minutes(logged_in_client, idle_minutes)

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == expected_status

    def test_logout_clears_last_activity(self, logged_in_client):
        resp = logged_in_client.post("/api/user/logout")

        assert resp.status_code == 200
        assert get_last_activity(logged_in_client) is None

    def test_a_new_sign_in_starts_with_fresh_activity(self, logged_in_client, db_session):
        set_session_timeout(db_session, 15)
        set_idle_minutes(logged_in_client, 120)
        logged_in_client.get("/api/user/me")

        login = logged_in_client.post(
            "/api/user/login",
            json={"email": "admin@example.com", "password": "AdminPass1!"},
        )
        resp = logged_in_client.get("/api/user/me")

        assert login.status_code == 200
        assert resp.status_code == 200


class TestActivityThrottle:
    """Last_Activity is written at most once a minute (#339). Only a remembered
    session then sends the cookie again, to renew its expiry."""

    def test_fresh_activity_is_not_rewritten(self, logged_in_client):
        set_idle_minutes(logged_in_client, 0.5)
        before = get_last_activity(logged_in_client)

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == 200
        assert resp.headers.get_all("Set-Cookie") == []
        assert get_last_activity(logged_in_client) == before

    def test_stale_activity_is_rewritten_without_a_cookie(self, logged_in_client):
        set_idle_minutes(logged_in_client, 2)
        before = get_last_activity(logged_in_client)

        resp = logged_in_client.get("/api/user/me")

        assert resp.status_code == 200
        assert resp.headers.get_all("Set-Cookie") == []
        assert get_last_activity(logged_in_client) > before

    @pytest.mark.parametrize("idle_minutes, renewed", [(0.5, False), (2, True)])
    def test_remembered_session_renews_its_cookie_when_stale(
        self, client, admin_user, idle_minutes, renewed
    ):
        client.post(
            "/api/user/login",
            json={
                "email": "admin@example.com",
                "password": "AdminPass1!",
                "remember_me": True,
            },
        )
        set_idle_minutes(client, idle_minutes)

        resp = client.get("/api/user/me")

        assert resp.status_code == 200
        assert bool(resp.headers.get_all("Set-Cookie")) is renewed
