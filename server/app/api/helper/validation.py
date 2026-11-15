"""Request validation helpers: password policy, JSON body and field checks, user and role existence, status values and email checks. Each returns None when the input is valid, or an error response tuple to return from the route."""

from app.system_models import UserStatus
from email_validator import validate_email, EmailNotValidError
from .database_access import *
from .responses import error
from .settings_flags import is_strong_password_policy_enabled

"""
This is a separation of concern that requires checking of input
"""
# ================= PASSWORD  =====================

STRONG_MIN_PASSWORD_LENGTH = 12
RELAXED_MIN_PASSWORD_LENGTH = 8


def validate_password(password):
    """Check a password against the active password policy.

    With the strong policy on, it needs at least 12 characters with an
    uppercase letter, a lowercase letter, a digit and a special character.
    With it off, only a minimum of 8 characters applies. Returns None if
    valid, otherwise a 400 error response.
    """
    password = password.strip()
    if not password:
        return error("Password must not be empty.", 400)

    # Strong Password Policy (Settings > Security) governs whether the full
    # complexity rule applies or just a minimum length. Checked live per
    # request rather than cached, since Settings can change between calls.
    if not is_strong_password_policy_enabled():
        if len(password) < RELAXED_MIN_PASSWORD_LENGTH:
            return error(f"Password must be at least {RELAXED_MIN_PASSWORD_LENGTH} characters long", 400)
        return None

    if len(password) < STRONG_MIN_PASSWORD_LENGTH:
        return error(f"Password must be at least {STRONG_MIN_PASSWORD_LENGTH} characters long", 400)
    if not any(char.isupper() for char in password):
        return error("Password must contain an uppercase letter.", 400)
    if not any(char.islower() for char in password):
        return error("Password must contain a lowercase letter.", 400)
    if not any(char.isdigit() for char in password):
        return error("Password must contain a number.", 400)
    if not any(not char.isalnum() for char in password):
        return error("Password must contain a special character.", 400)
    return None

def validate_password_is_same(password, confirm_password):
    """Return a 400 error response if the two passwords differ, otherwise None."""
    if not password == confirm_password:
        return error("Password is not the same.", 400)
    return None

# ================= USER  =========================
def validate_user_exists(user):
    
    """Check that a user id (an int) refers to an existing user.

    Returns a 400 error response for a non-int, a 404 if the user does not
    exist, otherwise None.
    """
    exists = True
    if isinstance(user, int):
        exists = exists_user_by_id(user)
    else:
        return error("Invalid Datatype.", 400)
    
    if not exists:
        return error("User does not exist.", 404)
    
    return None

def validate_user_not_exists(user):
    
    """Check that a user id (an int) does not refer to an existing user.

    Returns a 400 error response for a non-int, a 409 if the user exists,
    otherwise None.
    """
    exists = True
    if isinstance(user, int):
        exists = exists_user_by_id(user)
    else:
        return error("Invalid Datatype.", 400)
    
    if exists:
        return error("User already exists.", 409)
    
    return None

# ================= ROLE  ========================
def validate_role_exists(role):
    
    """Check that a role id (an int) refers to an existing role.

    Returns a 400 error response for a non-int, a 404 if the role does not
    exist, otherwise None.
    """
    exists = True
    if isinstance(role, int):
        exists = exists_role_by_id(role)
    else:
        return error("Invalid Datatype.", 400)
    
    if not exists:
        return error("Role does not exist.", 404)
    
    return None

def validate_role_not_exists(role):
    """Check that a role id (an int) or a role name (a non-numeric string) is not in use.

    Returns a 400 error response for any other type, a 409 if the role
    exists, otherwise None.
    """
    exists = True
    if isinstance(role, int):
        exists = exists_role_by_id(role)
    elif isinstance(role, str) and not role.isdigit():
        exists = exists_role_by_name(role)
    else:
        return error("Invalid Datatype.", 400)
    
    if exists:
        return error("Role already exists.", 409)
    
    return None

def validate_role_name_available(role):
    """Return a 409 error response if a role already has this name (ignoring case), otherwise None."""
    if exists_role_by_name(role):
        return error("That role name is already taken.", 409)
    return None

# ================= PERMISSION  ==================
def validate_permission_exists(permission):
    
    """Check that a permission id (an int) refers to an existing permission.

    Returns a 400 error response for a non-int, a 404 if it does not exist,
    otherwise None.
    """
    exists = True
    if isinstance(permission, int):
        exists = exists_permission_by_id(permission)
    else:
        return error("Invalid Datatype.", 400)
    
    if not exists:
        return error("Permission does not exist.", 404)
    
    return None

# ================== JSON  =======================
def validate_json_data(data):
    """Check that a request body is a non-empty JSON object.

    Returns a 400 error response if it is missing, not an object or empty,
    otherwise None.
    """
    if data is None:
        return error("No JSON data provided", 400)

    if not isinstance(data, dict):
        return error("JSON body must be an object", 400)
    
    if len(data) == 0:
        return error("JSON body must not be empty", 400)
    
    return None

def validate_json_fields(data, required_fields):
    """
    Args:
        data (json or dict): the data from the frontend
        required_fields (dict): a dict of the fields and their datatype

    Returns:
        tuple or None: (response, status_code) if error, None if valid
    """
    missing = []
    invalid_types = []

    for field, expected_type in required_fields.items():
        if field not in data:
            missing.append(field)
            continue

        if not isinstance(data[field], expected_type):
            invalid_types.append(
                f"{field} (expected {expected_type.__name__})"
            )

    if missing:
        return error(f"Fields: {', '.join(missing)} are required", 400)

    if invalid_types:
        return error(f"Invalid field types: {', '.join(invalid_types)}", 400)

    return None

# ================ USERSTATUS ====================
def validate_userstatus(status):
    """Return None if the text matches a UserStatus value (ignoring case and surrounding spaces), otherwise a 400 error response."""
    status = status.strip().lower()
    for main_status in UserStatus:
        if status == main_status.value.lower():
            return None
    return error("Not a valid status", 400)

# =================== EMAIL ======================
def validate_user_email(email):
    """Return None if the text is a syntactically valid email address, otherwise a 400 error response.

    Deliverability is not checked.
    """
    try:
        validate_email(email, check_deliverability=False)
        return None
    except EmailNotValidError:
        return error("Not a valid email.", 400)

PLACEHOLDER_EMAIL_DOMAIN = "pinpoint.lan"
RESERVED_EMAIL_DOMAINS = (
    "local", "lan", "test", "example", "invalid", "localhost", "internal", "home.arpa",
)


def validate_deliverable_email_domain(email):
    """Reject email domains that cannot receive mail.

    Returns a 400 error response for the installer placeholder domain and for
    reserved domains such as local, lan, test and example (and their
    subdomains), otherwise None.
    """
    domain = str(email).rsplit("@", 1)[-1].strip().lower().rstrip(".")
    if domain == PLACEHOLDER_EMAIL_DOMAIN or domain.endswith("." + PLACEHOLDER_EMAIL_DOMAIN):
        return error("Enter a real email address, not the installer placeholder.", 400)
    for reserved in RESERVED_EMAIL_DOMAINS:
        if domain == reserved or domain.endswith("." + reserved):
            return error(f"The domain '{domain}' is reserved and cannot receive email.", 400)
    return None


def validate_email_available(email):
    """Return a 409 error response if an account already uses this email, otherwise None."""
    if exists_user_by_email(email):
        return error("Email already exists.", 409)
    return None
