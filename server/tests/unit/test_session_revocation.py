"""
Tests for ending a signed-in session after an account change (#218) and for the
server-side session record that makes logout final (#339), both enforced by
enforce_session_timeout in app/api/user/login.py.

Each test signs the user in on its own client, changes the account the way an
administrator would, then checks that client's next request.
"""
from datetime import timedelta

import pytest
from flask import g, request_started

from app.api.helper.user_sessions import utc_now
from app.system_models import UserSession, UserStatus
from tests.support.session_helpers import get_session_record
from tests.unit.test_management import _make_user

PASSWORD = "TestPass1!abc"
NEW_PASSWORD = "BrandNewPass1!xyz"
SUSPENDED_MESSAGE = "This account is suspended. Contact the admin for any concerns."


@pytest.fixture(autouse=True)
def fresh_user_per_request(app):
    """The test app context outlives a request, so drop Flask-Login's cached user:
    these tests send requests from several clients."""
    def forget(sender, **extra):
        g.pop("_login_user", None)

    with request_started.connected_to(forget, app):
        yield


@pytest.fixture
def target(db_session, admin_role):
    return _make_user(db_session, admin_role, "target@example.com")


@pytest.fixture
def target_client(app, target):
    client = app.test_client()
    response = client.post("/api/user/login", json={"email": target.Email, "password": PASSWORD})
    assert response.status_code == 200
    return client


def change_account(db_session, user, **changes):
    if "password" in changes:
        user.set_password(changes.pop("password"))
    for name, value in changes.items():
        setattr(user, name, value)
    db_session.session.commit()


class TestAccountChangeEndsSession:
    @pytest.mark.parametrize("changes", [
        {"password": NEW_PASSWORD},
        {"Email": "renamed@example.com"},
        {"Must_Change_Password": True},
    ])
    def test_next_request_is_rejected(self, target_client, db_session, target, changes):
        change_account(db_session, target, **changes)

        response = target_client.get("/api/user/me")

        assert response.status_code == 401
        assert "account changed" in response.get_json()["message"]
        assert target_client.get("/api/user/me").status_code == 401

    def test_role_change_ends_the_session(self, target_client, db_session, target, regular_role):
        change_account(db_session, target, RoleID=regular_role.RoleID)

        assert target_client.get("/api/user/me").status_code == 401

    @pytest.mark.parametrize("status", [UserStatus.SUSPENDED, UserStatus.INACTIVE])
    def test_status_change_ends_the_session(self, target_client, db_session, target, status):
        change_account(db_session, target, Status=status)

        assert target_client.get("/api/user/me").status_code == 401

    def test_name_and_alert_changes_keep_the_session(self, target_client, db_session, target):
        change_account(
            db_session, target,
            First_Name="Renamed", Last_Name="Person", Receive_Email_Alerts=False,
        )

        assert target_client.get("/api/user/me").status_code == 200

    def test_a_session_without_a_stamp_is_rejected(self, target_client):
        with target_client.session_transaction() as sess:
            del sess["auth_stamp"]

        assert target_client.get("/api/user/me").status_code == 401

    def test_the_session_holds_no_password_hash(self, target_client, target):
        with target_client.session_transaction() as sess:
            assert target.Hashed_Password not in str(dict(sess))

    def test_signing_in_again_works_after_a_change(self, target_client, db_session, target):
        change_account(db_session, target, password=NEW_PASSWORD)
        target_client.get("/api/user/me")

        response = target_client.post(
            "/api/user/login", json={"email": target.Email, "password": NEW_PASSWORD},
        )

        assert response.status_code == 200
        assert target_client.get("/api/user/me").status_code == 200

    def test_changing_own_password_keeps_the_session(self, target_client):
        response = target_client.post("/api/user/change-password", json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        })

        assert response.status_code == 200
        assert target_client.get("/api/user/me").status_code == 200

    def test_first_run_setup_keeps_the_session(self, target_client, db_session, target):
        change_account(db_session, target, Needs_Setup=True)

        response = target_client.post("/api/user/complete-setup", json={
            "current_password": PASSWORD,
            "new_email": "owner@pinpoint-owner.com",
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        })

        assert response.status_code == 200
        assert target_client.get("/api/user/me").status_code == 200


class TestRefusedSignIn:
    @pytest.mark.parametrize("status, message", [
        (UserStatus.SUSPENDED, SUSPENDED_MESSAGE),
        (UserStatus.INACTIVE, "Account inactive."),
    ])
    def test_message_matches_the_status(self, client, db_session, target, status, message):
        change_account(db_session, target, Status=status)

        response = client.post("/api/user/login", json={"email": target.Email, "password": PASSWORD})

        assert response.status_code == 403
        assert response.get_json()["message"] == message

    def test_a_wrong_password_does_not_reveal_suspension(self, client, db_session, target):
        change_account(db_session, target, Status=UserStatus.SUSPENDED)

        response = client.post("/api/user/login", json={"email": target.Email, "password": "wrong"})

        assert response.status_code == 401
        assert response.get_json()["message"] == "Invalid username or password."


def sign_in(client, email, **extra):
    response = client.post("/api/user/login", json={"email": email, "password": PASSWORD, **extra})
    assert response.status_code == 200
    return client


def copy_cookie(client):
    return client.get_cookie("session").value


def replay(app, cookie):
    """Send a saved session cookie from a fresh client and return the response."""
    client = app.test_client()
    client.set_cookie("session", cookie)
    return client.get("/api/user/me")


def live_rows(db_session):
    db_session.session.expire_all()
    return db_session.session.query(UserSession).filter(UserSession.Revoked_At.is_(None)).count()


class TestServerSideSession:
    @pytest.mark.parametrize("remember_me", [False, True])
    def test_a_cookie_copied_before_logout_is_rejected(self, app, client, target, remember_me):
        sign_in(client, target.Email, remember_me=remember_me)
        cookie = copy_cookie(client)
        assert replay(app, cookie).status_code == 200

        assert client.post("/api/user/logout").status_code == 200

        response = replay(app, cookie)
        assert response.status_code == 401
        assert "Session ended" in response.get_json()["message"]

    def test_logout_leaves_the_users_other_sessions(self, app, target_client, target):
        other = sign_in(app.test_client(), target.Email)

        other.post("/api/user/logout")

        assert target_client.get("/api/user/me").status_code == 200

    @pytest.mark.parametrize("sid", [None, "unknown"])
    def test_a_cookie_without_a_known_session_is_rejected(self, target_client, sid):
        with target_client.session_transaction() as sess:
            if sid is None:
                del sess["sid"]
            else:
                sess["sid"] = sid

        assert target_client.get("/api/user/me").status_code == 401

    def test_another_users_session_id_is_rejected(
        self, app, db_session, admin_role, target_client
    ):
        _make_user(db_session, admin_role, "other@example.com")
        other = sign_in(app.test_client(), "other@example.com")
        other_sid = get_session_record(other).SessionID
        with target_client.session_transaction() as sess:
            sess["sid"] = other_sid

        assert target_client.get("/api/user/me").status_code == 401
        assert other.get("/api/user/me").status_code == 200

    def test_a_suspended_session_stays_dead_after_reactivation(
        self, app, logged_in_client, target, db_session
    ):
        client = sign_in(app.test_client(), target.Email, remember_me=True)
        for status in ("Suspended", "Active"):
            response = logged_in_client.put(f"/api/user/accounts/{target.UserID}", json={
                "first_name": target.First_Name,
                "last_name": target.Last_Name,
                "email": target.Email,
                "role_id": target.RoleID,
                "status": status,
            })
            assert response.status_code == 200
        # Reactivation forces a password change; undo it so only the record
        # keeps the old session out.
        db_session.session.refresh(target)
        target.Must_Change_Password = False
        db_session.session.commit()

        assert client.get("/api/user/me").status_code == 401

    def test_changing_own_password_revokes_other_sessions(self, app, db_session, target_client, target):
        sign_in(app.test_client(), target.Email)

        response = target_client.post("/api/user/change-password", json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        })

        assert response.status_code == 200
        assert live_rows(db_session) == 1
        assert target_client.get("/api/user/me").status_code == 200

    def test_sign_in_removes_dead_records(self, app, db_session, target_client, target):
        sign_in(app.test_client(), target.Email).post("/api/user/logout")
        record = get_session_record(target_client)
        record.Last_Activity = utc_now() - timedelta(days=31)
        db_session.session.commit()

        sign_in(app.test_client(), target.Email)

        db_session.session.expire_all()
        assert db_session.session.query(UserSession).count() == 1
