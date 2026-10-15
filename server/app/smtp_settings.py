"""
smtp_settings.py — the mail account behind Settings -> Email.

PinPoint does not send Nagios notification mail itself: the appliance ships
msmtp, and a root-owned helper (/usr/local/sbin/pinpoint-apply-smtp) writes
/etc/msmtprc from one JSON object on stdin. The web server is unprivileged, so
it runs the helper through `sudo -n`. Gmail and custom relays over STARTTLS are
supported; Gmail needs an app password, not the account's normal password.

The password is passed through exactly as typed (spaces included: Google shows
app passwords in groups of four). It is kept encrypted (app/secrets_store.py)
so a later save can leave it blank, and no API ever returns it.

The test email is sent from here with smtplib rather than through msmtp,
because /etc/msmtprc is readable only by root and the nagios group. smtplib
also gives the real SMTP reply, which is what lets a rejected login be told
apart from a blocked port or a wrong host.
"""
import base64
import json
import re
import smtplib
import socket
import ssl
import subprocess
from email.message import EmailMessage

import sqlalchemy as sa

from app import db
from app.system_models import SmtpSettings

HELPER_PATH = "/usr/local/sbin/pinpoint-apply-smtp"
HELPER_TIMEOUT = 20
SMTP_TIMEOUT = 15

GMAIL = {"provider": "gmail", "host": "smtp.gmail.com", "port": 587, "tls": "starttls"}
CUSTOM = {"provider": "custom", "host": "", "port": 587, "tls": "starttls"}
PRESETS = {"gmail": GMAIL, "custom": CUSTOM}

# Match the installed helper, including its 253-character host limit.
HOST_PATTERN = re.compile(r"[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?")
HELPER_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$")
MAX_PASSWORD_LENGTH = 200

# What a rejected Gmail login looks like, whichever way smtplib reports it.
AUTH_FAILURE_PATTERN = re.compile(r"\b535\b|BadCredentials|Username and Password not accepted", re.IGNORECASE)


class SmtpSettingsError(Exception):
    """Invalid input. The message is shown to the administrator and never contains a password."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class MailHelperError(Exception):
    """The root helper refused the settings or could not run. `rejected` is True when it refused them."""
    def __init__(self, message, rejected):
        super().__init__(message)
        self.message = message
        self.rejected = rejected


def is_printable_ascii(value):
    """Return whether all characters can safely occupy one helper config line."""
    return all(0x20 <= ord(char) <= 0x7e for char in value)


# ==========================================================
# STORED SETTINGS
# ==========================================================

def get_smtp_row():
    return db.session.get(SmtpSettings, 1)


def get_smtp_settings(row=None):
    """The settings as the API returns them. Never includes the password, only whether one is saved."""
    row = row if row is not None else get_smtp_row()
    if row is None:
        return {**GMAIL, "username": "", "sender": "", "passwordSet": False,
                "configured": False, "version": 0, "updatedAt": None}
    return {
        "provider": row.Provider,
        "host": row.Host,
        "port": row.Port,
        "tls": row.Tls,
        "username": row.Username,
        "sender": row.Sender,
        "passwordSet": bool(row.Password_Encrypted),
        "configured": True,
        "version": row.Version,
        "updatedAt": row.Updated_At.isoformat() if row.Updated_At else None,
    }


# ==========================================================
# VALIDATION
# ==========================================================

def validate_smtp_settings(data, has_saved_password):
    """
    Check a PUT body and return {provider, host, port, tls, username, sender, password}.
    `password` is None when the administrator left it blank to keep the saved one. The
    password is never trimmed or changed. Raises SmtpSettingsError.
    """
    if not isinstance(data, dict):
        raise SmtpSettingsError("Send the email settings as a JSON object.")

    provider = data.get("provider", "gmail")
    if not isinstance(provider, str) or provider not in PRESETS:
        raise SmtpSettingsError("Choose Gmail or Other SMTP relay as the provider.")
    preset = PRESETS[provider].copy()

    if data.get("tls", preset["tls"]) != "starttls":
        raise SmtpSettingsError("Only STARTTLS is supported." if provider == "gmail" else "The tls mode must be starttls.")
    if provider == "gmail":
        if data.get("host", preset["host"]) != preset["host"]:
            raise SmtpSettingsError(f"The Gmail host must be {preset['host']}.")
        if data.get("port", preset["port"]) != preset["port"] or isinstance(data.get("port"), bool):
            raise SmtpSettingsError(f"The Gmail port must be {preset['port']}.")
    else:
        host, port = data.get("host"), data.get("port")
        if not isinstance(host, str) or not HOST_PATTERN.fullmatch(host):
            raise SmtpSettingsError("The host must be a host name or IPv4 address, at most 253 characters.")
        if type(port) is not int or not 1 <= port <= 65535:
            raise SmtpSettingsError("The port must be a whole number from 1 to 65535.")
        preset.update(host=host, port=port)

    username = data.get("username")
    if provider == "gmail":
        if not isinstance(username, str) or not username or len(username) > 254:
            raise SmtpSettingsError("Enter the full Gmail address as the username.")
        if not is_printable_ascii(username) or not EMAIL_PATTERN.match(username):
            raise SmtpSettingsError("The username must be a full email address, for example you@gmail.com.")
    elif not isinstance(username, str) or not username or len(username) > 254 or not is_printable_ascii(username):
        raise SmtpSettingsError("The username must contain 1 to 254 printable ASCII characters.")

    sender = data.get("sender")
    if sender is None or sender == "":
        sender = username
    if not isinstance(sender, str) or len(sender) > 254 or not is_printable_ascii(sender) or not EMAIL_PATTERN.match(sender):
        raise SmtpSettingsError("The sender must be a valid email address.")

    if provider == "custom" and not HELPER_EMAIL_PATTERN.fullmatch(sender):
        raise SmtpSettingsError("The sender must be a valid email address accepted by the mail helper.")

    password = data.get("password")
    if password is None or password == "":
        if not has_saved_password:
            raise SmtpSettingsError("Enter the app password." if provider == "gmail" else "Enter the relay password.")
        password = None
    else:
        if not isinstance(password, str):
            raise SmtpSettingsError("The password must be text.")
        password_limit = MAX_PASSWORD_LENGTH if provider == "gmail" else 256
        if len(password) > password_limit:
            raise SmtpSettingsError(f"The password can be at most {password_limit} characters.")
        if not is_printable_ascii(password):
            raise SmtpSettingsError("The password can only contain printable ASCII characters.")

    return {**preset, "username": username, "sender": sender, "password": password}


# ==========================================================
# ROOT HELPER
# ==========================================================

def run_apply_helper(values, password):
    """
    Send the settings to the root helper as one JSON object on stdin (never as
    arguments). Raises MailHelperError with credential-redacted helper stderr when it refuses
    them (exit 1) or when it cannot be run.
    """
    payload = json.dumps({
        "host": values["host"], "port": values["port"], "tls": values["tls"],
        "username": values["username"], "password": password, "sender": values["sender"],
    })
    try:
        result = subprocess.run(
            ["sudo", "-n", HELPER_PATH],
            input=payload, capture_output=True, text=True, timeout=HELPER_TIMEOUT, check=False,
        )
    except FileNotFoundError:
        raise MailHelperError("The mail helper is not installed on this server.", rejected=False)
    except subprocess.TimeoutExpired:
        raise MailHelperError("The mail helper did not finish in time.", rejected=False)

    if result.returncode == 0:
        return
    reason = redact_mail_secret((result.stderr or "").strip(), password) or f"The mail helper failed (exit {result.returncode})."
    raise MailHelperError(reason, rejected=result.returncode == 1)


# ==========================================================
# TEST EMAIL
# ==========================================================

def redact_mail_secret(text, password):
    """Remove the SMTP credential and common encodings from diagnostic text."""
    if not password:
        return text
    variants = {password, repr(password), json.dumps(password), base64.b64encode(password.encode()).decode()}
    for secret in sorted(variants, key=len, reverse=True):
        text = text.replace(secret, "[redacted]")
    return text


def classify_relay_error(exc, host, port):
    """Classify relay failures with generic guidance and no raw server text."""
    code = classify_smtp_error(exc, host, port)["code"]
    messages = {
        "auth_failed": "The SMTP relay rejected the login. Check the username and password or app token.",
        "host_not_found": f"Could not find {host}. Check the SMTP host and the server's DNS.",
        "connect_failed": f"Could not connect to {host} on port {port}. Check the port and firewall.",
        "tls_failed": "The secure (STARTTLS) connection to the mail server could not be set up.",
        "rejected": "The SMTP relay refused the sender or recipient address.",
        "send_failed": "The test email could not be sent through the SMTP relay.",
    }
    return {"code": code, "message": messages[code],
            "explanation": "Check your relay's SMTP submission settings and sending permissions.", "details": ""}


def classify_smtp_error(exc, host, port):
    """
    Turn an smtplib/socket error into {code, message, explanation, details}: message is plain
    language, explanation says technically what happened and what to check, and details is the
    server's own text.
    """
    details = str(exc)
    if isinstance(exc, smtplib.SMTPResponseException):
        error_text = exc.smtp_error.decode("utf-8", "replace") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
        details = f"{exc.smtp_code} {error_text}".strip()

    if isinstance(exc, smtplib.SMTPAuthenticationError) or AUTH_FAILURE_PATTERN.search(details):
        return {"code": "auth_failed", "details": details,
                "message": "Gmail rejected the login. Make sure you entered an app password, "
                           "not your normal password, and that 2-Step Verification is on.",
                "explanation": "The connection to Gmail worked, but Gmail answered the login with a 535 "
                               "authentication error (BadCredentials). Gmail does not accept an account's normal "
                               "password over SMTP. It needs a 16-character app password, which can only be created "
                               "once 2-Step Verification is on for the Google account. Also check that the username "
                               "is the full Gmail address and that the app password was copied completely."}
    if isinstance(exc, socket.gaierror):
        return {"code": "host_not_found", "details": details,
                "message": f"Could not find {host}. Check the server's DNS and internet access.",
                "explanation": f"The name {host} could not be resolved to an IP address (a DNS lookup failure). "
                               "The server may have no DNS server configured, no route to the internet, or a "
                               "firewall blocking DNS."}
    if isinstance(exc, (ConnectionRefusedError, TimeoutError, socket.timeout, smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError)) \
            or (isinstance(exc, OSError) and not isinstance(exc, (ssl.SSLError, smtplib.SMTPException))):
        return {"code": "connect_failed", "details": details,
                "message": f"Could not connect to {host} on port {port}. "
                           f"The appliance needs outbound access to {host} on port {port}; a firewall may be blocking it.",
                "explanation": f"The TCP connection to {host}:{port} was refused, timed out or was dropped before "
                               "Gmail answered, so no login was attempted. This usually means a firewall or network "
                               f"policy blocks outbound port {port}, or the server has no internet route."}
    if isinstance(exc, (ssl.SSLError, smtplib.SMTPNotSupportedError)):
        return {"code": "tls_failed", "details": details,
                "message": "The secure (STARTTLS) connection to the mail server could not be set up.",
                "explanation": "The server connected, but the upgrade to an encrypted STARTTLS session failed. "
                               "Common causes are a wrong system clock, missing CA certificates, or a proxy or "
                               "firewall that intercepts the connection."}
    if isinstance(exc, (smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused)):
        return {"code": "rejected", "details": details,
                "message": "The mail server refused the sender or recipient address.",
                "explanation": "The login worked, but the server refused the message itself. Check that the "
                               "sender is the Gmail account (Gmail rewrites other From addresses) and that the "
                               "recipient address is valid."}
    return {"code": "send_failed", "details": details, "message": "The test email could not be sent.",
            "explanation": "The send failed in a way PinPoint does not recognise. The mail server's own reply "
                           "is shown below."}


def send_test_email(settings, password, recipient):
    """
    Send a test message over STARTTLS with the saved settings. Returns
    {"ok": True, "recipient"} or {"ok": False, "code", "message", "details"}.
    """
    message = EmailMessage()
    message["From"] = settings["sender"]
    message["To"] = recipient
    message["Subject"] = "PinPoint test email"
    message.set_content(
        "This is a test email from PinPoint. If you can read it, notification email is set up correctly."
    )
    try:
        with smtplib.SMTP(settings["host"], settings["port"], timeout=SMTP_TIMEOUT) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(settings["username"], password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        classify = classify_smtp_error if settings["provider"] == "gmail" else classify_relay_error
        result = classify(exc, settings["host"], settings["port"])
        return {"ok": False, **{key: redact_mail_secret(value, password) for key, value in result.items()}}
    return {"ok": True, "recipient": recipient}
