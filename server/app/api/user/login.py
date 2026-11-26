"""Session authentication and expiry enforcement.

Routes
------
POST /api/user/login
    Establish a signed-out session; reject an existing session with 409.
    Optional boolean `remember_me` makes the session cookie persistent and
    exempts it from the idle timeout.
    A suspended account that gives the right password is told it is suspended.
POST /api/user/logout
    End the authenticated session.

Before every request a signed-in session is ended when the account is no longer
Active, when its sign-in details changed (see _auth_stamp) or when it has been
idle too long.
"""
import hashlib
import hmac
import json
import time

from flask_login import login_user, logout_user, login_required, current_user, user_logged_in
from flask import request, current_app, session
from app import db
from app.api.helper import (
    validate_json_data,
    validate_json_fields,
    validate_user_email,
    get_user_by_email,
    normalize_email
)
from app.api.helper.responses import success, error
from app.api.helper.settings_flags import (
    is_failed_login_monitoring_enabled,
    get_session_timeout_minutes
)
from app.api.user import user_bp
from app.logging.user_activity import create_user_log, create_audit_log
from app.system_models import UserStatus


def _record_failed_login(user):
    if not is_failed_login_monitoring_enabled():
        return
    try:
        create_user_log(user.UserID, "Failed login attempt")
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Unable to record failed login attempt for user {user.UserID}"
        )


# ==========================================================
# SESSION REVOCATION
# ==========================================================

def _auth_stamp(user):
    """
    Return a keyed digest of the account fields a session depends on: password,
    role, email, status and the forced password change. A session keeps the
    value from sign-in, so changing any of these ends it. Names and the email
    alert setting are left out on purpose.
    """
    fields = json.dumps([
        user.Hashed_Password,
        user.RoleID,
        user.Email,
        user.Status.value,
        bool(user.Must_Change_Password),
    ])
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, fields.encode(), hashlib.sha256).hexdigest()


def stamp_session(user):
    """Record the account's current sign-in details in this session."""
    session["auth_stamp"] = _auth_stamp(user)


@user_logged_in.connect
def _stamp_on_login(sender, user, **extra):
    stamp_session(user)


def _end_session():
    """Sign the user out and drop everything this module stored in the session."""
    logout_user()
    session.pop("auth_stamp", None)
    session.pop("last_activity", None)
    session.pop("remembered", None)
    session.permanent = False


# ==========================================================
# SESSION TIMEOUT
# ==========================================================

LAST_ACTIVITY_WRITE_SECONDS = 60


@user_bp.before_app_request
def enforce_session_timeout():
    """
    Expire a logged-in session after it has been idle longer than the
    Session Timeout in System Settings. Runs before every request: the
    time of the last request is kept in the signed session cookie, and
    if the gap since then is too long the user is logged out and the
    request is rejected with 401. Otherwise the timestamp is refreshed,
    so any request counts as activity (written at most once a minute).

    A session is also ended, with 401, when the account is no longer Active or
    its sign-in details changed since the session was stamped. A session with no
    stamp is treated as changed.

    The front-end also logs the user out after the same idle period
    (SessionTimeoutWatcher), since background polling keeps making
    requests while a page is open. This check covers the cases the
    browser can't, such as a closed tab or a sleeping machine.
    """
    if not current_user.is_authenticated:
        return None

    if current_user.Status != UserStatus.ACTIVE:
        _end_session()
        return error("Account inactive.", 401)

    if session.get("auth_stamp") != _auth_stamp(current_user):
        _end_session()
        return error("Your account changed. Please log in again.", 401)

    now = time.time()
    last_activity = session.get("last_activity")
    timeout_seconds = get_session_timeout_minutes() * 60

    # A remembered session ("Remember me") is not ended by idleness; it lasts
    # until the persistent cookie expires or the user signs out.
    remembered = bool(session.get("remembered"))
    if (
        not remembered
        and last_activity is not None
        and now - last_activity > timeout_seconds
    ):
        _end_session()
        return error("Session expired. Please log in again.", 401)

    # Write only when stale: a changed session makes Flask send Set-Cookie, and
    # a response that finishes after logout would put a signed-in cookie back
    # (#339). The idle timeout stays accurate to within the throttle.
    if last_activity is None or now - last_activity > LAST_ACTIVITY_WRITE_SECONDS:
        session["last_activity"] = now
    return None


_PASSWORD_CHANGE_ALLOWED_ENDPOINTS = {
    "api.user.login",
    "api.user.logout",
    "api.user.user_permission",
    "api.user.change_password",
}


_SETUP_ALLOWED_ENDPOINTS = {
    "api.user.login",
    "api.user.logout",
    "api.user.user_permission",
    "api.user.complete_setup",
}


@user_bp.before_app_request
def enforce_password_change():
    """Before-request guard that blocks the API for accounts that must finish first-run setup or change their password.

    Signed-out requests and requests outside the API pass through. For a
    flagged account, only the endpoints needed to log out, read the account's
    permissions and complete setup or change the password are allowed; every
    other API call gets a 403 JSON error. Returns None to let the request
    continue.
    """
    if not current_user.is_authenticated:
        return None
    needs_setup = bool(current_user.Needs_Setup)
    if not needs_setup and not current_user.Must_Change_Password:
        return None
    allowed = _SETUP_ALLOWED_ENDPOINTS if needs_setup else _PASSWORD_CHANGE_ALLOWED_ENDPOINTS
    if request.endpoint in allowed:
        return None
    if not (request.blueprint or "").startswith("api"):
        return None
    if needs_setup:
        return error("You must complete first-run setup before continuing.", 403)
    return error("You must change your password before continuing.", 403)


# ==========================================================
# LOGIN / LOGOUT
# ==========================================================

@user_bp.post('/login')
def login():
    """
    Validate credentials and establish a session only when signed out.
    An existing authenticated session receives 409 before credential validation;
    its identity and permissions remain unchanged until explicit logout.

    Expects:
    {
        "email": "email",
        "password": "password"
    }

    Returns:
        Standardized JSON response
    """

    if current_user.is_authenticated:
        return error(
            "You are already signed in. Sign out before logging in to another account.",
            409,
        )

    data = request.get_json()

    err = validate_json_data(data)
    if err is not None:
        return err

    fields = {
        "email": str,
        "password": str
    }

    err = validate_json_fields(data, fields)
    if err is not None:
        return err

    remember_me = data.get("remember_me", False)
    if not isinstance(remember_me, bool):
        return error("Invalid field types: remember_me (expected bool)", 400)

    email = data.get("email")
    password = data.get("password")

    err = validate_user_email(email)
    if err is not None:
        return err

    normalized_email = normalize_email(email)

    user = get_user_by_email(normalized_email)

    if user is None or not user.check_password(password):
        if user is not None:
            _record_failed_login(user)
        else:
            current_app.logger.warning(
                f"Failed login attempt for unknown email '{normalized_email}'."
            )
        return error("Invalid username or password.", 401)

    if user.Status == UserStatus.SUSPENDED:
        return error("This account is suspended. Contact the admin for any concerns.", 403)

    if user.Status != UserStatus.ACTIVE:
        return error("Account inactive.", 403)

    login_user(user)
    session["last_activity"] = time.time()
    session["remembered"] = remember_me
    session.permanent = remember_me
    try:
        if remember_me:
            days = current_app.config["PERMANENT_SESSION_LIFETIME"].days
            create_audit_log(
                user.UserID, f"Signed in ({user.Email}), remembered for {days} days"
            )
        else:
            create_audit_log(user.UserID, f"Signed in ({user.Email})")
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Unable to record login for user {user.UserID}")

    return success(
        {
            "must_change_password": bool(user.Must_Change_Password),
            "needs_setup": bool(user.Needs_Setup),
        },
        message="User logged in.",
    )


@user_bp.post('/logout')
@login_required
def logout():
    """Audit sign-out and end the current authenticated session."""
    try:
        create_audit_log(current_user.UserID, f"Signed out ({current_user.Email})")
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unable to record logout")
    _end_session()
    return success(message="User logged out.")
