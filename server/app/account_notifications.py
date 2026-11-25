"""
account_notifications.py — tells a user by email that an administrator changed
how they sign in.

It uses the mail account saved under Settings -> Email. The message names what
changed and never carries a password. Sending is best effort: a failure is
reported to the caller, who has already saved the change.
"""
from email.message import EmailMessage

from flask import current_app

from app.secrets_store import SecretsError, decrypt
from app.smtp_settings import deliver_message, get_smtp_row, get_smtp_settings

PASSWORD_RESET = "Your password was reset."
EMAIL_CHANGED = "Your sign-in email address was changed."
ROLE_CHANGED = "Your role was changed."

SENT_MESSAGE = "The user was emailed about the change."
NOT_SET_UP_MESSAGE = (
    "Email is not set up, so the user was not emailed. Tell them about the change yourself."
)
FAILED_MESSAGE = "The email to the user could not be sent. Tell them about the change yourself."


def _result(ok, message):
    return {"notification_ok": ok, "notification_message": message}


def _build_message(sender, recipient, changes):
    lines = ["An administrator changed your PinPoint account:", ""]
    for change in changes:
        lines.append(f"- {change}")
    lines.append("")
    lines.append("Contact your administrator if you have any questions.")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = "Your PinPoint account changed"
    message.set_content("\n".join(lines))
    return message


def notify_account_change(recipients, changes):
    """
    Email each address in `recipients` the list of `changes`.

    Returns {} when there is nothing to report, otherwise
    {"notification_ok", "notification_message"}. It never raises, and it logs
    only the type of a send error, because a mail server's reply can repeat the
    mail password.
    """
    if not changes:
        return {}

    try:
        row = get_smtp_row()
        if row is None or not row.Password_Encrypted:
            return _result(False, NOT_SET_UP_MESSAGE)
        password = decrypt(row.Password_Encrypted)
        settings = get_smtp_settings(row)
    except SecretsError:
        current_app.logger.warning("The saved mail password could not be read.")
        return _result(False, FAILED_MESSAGE)
    except Exception:
        current_app.logger.exception("Unable to read the email settings.")
        return _result(False, FAILED_MESSAGE)

    all_sent = True
    for recipient in recipients:
        try:
            message = _build_message(settings["sender"], recipient, changes)
            deliver_message(settings, password, message)
        except Exception as exc:
            current_app.logger.warning(
                f"Unable to send an account change email ({type(exc).__name__})."
            )
            all_sent = False

    if not all_sent:
        return _result(False, FAILED_MESSAGE)
    return _result(True, SENT_MESSAGE)
