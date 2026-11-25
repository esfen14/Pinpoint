"""
Tests for ending a signed-in session after an account change (#218,
enforce_session_timeout in app/api/user/login.py).

Each test signs the user in on its own client, changes the account the way an
administrator would, then checks that client's next request.
"""
import pytest

from app.system_models import UserStatus
from tests.unit.test_management import _make_user

PASSWORD = "TestPass1!abc"
NEW_PASSWORD = "BrandNewPass1!xyz"
SUSPENDED_MESSAGE = "This account is suspended. Contact the admin for any concerns."


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
