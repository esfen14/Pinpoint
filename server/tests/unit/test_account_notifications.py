"""
Tests for the email sent when an administrator changes another account's
sign-in details (#218, app/account_notifications.py).

SMTP is mocked; no mail server is contacted.
"""
import smtplib
from unittest.mock import patch

import pytest

from app.secrets_store import encrypt
from app.system_models import PasswordResetRequest, SmtpSettings
from tests.unit.test_management import _make_user

NEW_PASSWORD = "BrandNewPass1!xyz"
SMTP_PASSWORD = "mail-app-password"
OLD_EMAIL = "target@example.com"
NEW_EMAIL = "renamed@example.com"


@pytest.fixture
def target(db_session, admin_role):
    return _make_user(db_session, admin_role, OLD_EMAIL)


@pytest.fixture
def mail_account(app, db_session, monkeypatch):
    monkeypatch.setitem(app.config, "SECRET_KEY_IS_TEMPORARY", False)
    db_session.session.add(SmtpSettings(
        Id=1, Provider="custom", Host="mail.example.org", Port=587, Tls="starttls",
        Username="monitoring@example.org", Sender="monitoring@example.org",
        Password_Encrypted=encrypt(SMTP_PASSWORD),
    ))
    db_session.session.commit()


@pytest.fixture
def smtp():
    with patch("app.smtp_settings.smtplib.SMTP") as mock:
        yield mock


def sent_messages(smtp):
    connection = smtp.return_value.__enter__.return_value
    messages = []
    for call in connection.send_message.call_args_list:
        messages.append(call.args[0])
    return messages


def edit(client, user, **changes):
    body = {
        "first_name": user.First_Name,
        "last_name": user.Last_Name,
        "email": user.Email,
        "role_id": user.RoleID,
        "status": user.Status.value,
    }
    body.update(changes)
    return client.put(f"/api/user/accounts/{user.UserID}", json=body)


class TestEditAccount:
    def test_password_reset_emails_the_account_without_the_password(
        self, logged_in_client, target, mail_account, smtp,
    ):
        response = edit(logged_in_client, target, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD)

        assert response.status_code == 200
        assert response.get_json()["data"]["notification_ok"] is True
        [message] = sent_messages(smtp)
        assert message["To"] == OLD_EMAIL
        assert "password was reset" in message.get_content()
        assert NEW_PASSWORD not in message.as_string()

    def test_email_change_emails_the_old_and_new_address(
        self, logged_in_client, target, mail_account, smtp,
    ):
        response = edit(logged_in_client, target, email=NEW_EMAIL)

        assert response.status_code == 200
        recipients = []
        for message in sent_messages(smtp):
            recipients.append(message["To"])
        assert recipients == [OLD_EMAIL, NEW_EMAIL]

    def test_role_change_emails_the_account(
        self, logged_in_client, target, regular_role, mail_account, smtp,
    ):
        edit(logged_in_client, target, role_id=regular_role.RoleID)

        [message] = sent_messages(smtp)
        assert "role was changed" in message.get_content()

    @pytest.mark.parametrize("changes", [{"first_name": "Renamed"}, {"status": "Suspended"}])
    def test_other_changes_send_nothing(
        self, logged_in_client, target, mail_account, smtp, changes,
    ):
        response = edit(logged_in_client, target, **changes)

        assert response.status_code == 200
        assert "notification_ok" not in (response.get_json().get("data") or {})
        assert sent_messages(smtp) == []

    def test_a_rejected_edit_sends_nothing(self, logged_in_client, target, mail_account, smtp):
        edit(logged_in_client, target, email="not-an-email")

        assert sent_messages(smtp) == []

    def test_without_mail_settings_the_change_is_saved_and_the_admin_is_told(
        self, logged_in_client, db_session, target, smtp,
    ):
        response = edit(logged_in_client, target, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD)

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["notification_ok"] is False
        assert "not set up" in data["notification_message"]
        db_session.session.refresh(target)
        assert target.check_password(NEW_PASSWORD)
        assert sent_messages(smtp) == []

    @pytest.mark.parametrize("failure", [
        smtplib.SMTPAuthenticationError(535, b"bad credentials " + SMTP_PASSWORD.encode()),
        OSError("connection refused"),
    ])
    def test_a_failed_send_keeps_the_change_and_hides_the_mail_password(
        self, logged_in_client, db_session, target, mail_account, smtp, failure, caplog,
    ):
        smtp.return_value.__enter__.return_value.login.side_effect = failure

        response = edit(logged_in_client, target, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD)

        assert response.status_code == 200
        assert response.get_json()["data"]["notification_ok"] is False
        db_session.session.refresh(target)
        assert target.check_password(NEW_PASSWORD)
        assert SMTP_PASSWORD not in response.get_data(as_text=True)
        assert SMTP_PASSWORD not in caplog.text


class TestResolvePasswordRequest:
    def test_resolving_emails_the_account(
        self, logged_in_client, db_session, target, mail_account, smtp,
    ):
        logged_in_client.post("/api/user/forgot-password", json={"email": OLD_EMAIL})
        pending = db_session.session.scalars(db_session.select(PasswordResetRequest)).one()

        response = logged_in_client.post(
            f"/api/user/password-requests/{pending.RequestID}/resolve",
            json={"password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD},
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["notification_ok"] is True
        [message] = sent_messages(smtp)
        assert message["To"] == OLD_EMAIL
        assert NEW_PASSWORD not in message.as_string()
