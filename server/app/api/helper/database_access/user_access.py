"""User lookups by id or email, the Super Admin lookup and email-uniqueness checks. Email comparisons ignore case."""

import sqlalchemy  as sa
from app import db
from app.system_models import User



# =========== Get From Database ==============
def get_user_by_id(user_id: int):
    """Return the User with this id, or None."""
    return db.session.get(User, user_id)

def get_super_admin():
    """The super admin is the first account ever created (lowest UserID)."""
    return db.session.scalar(sa.select(User).order_by(User.UserID).limit(1))

def is_super_admin(user_id: int) -> bool:
    """Return True if user_id belongs to the Super Admin, the first account ever created."""
    super_admin = get_super_admin()
    return super_admin is not None and super_admin.UserID == user_id

def get_user_by_email(user_email: str):
    """Return the User whose email matches case-insensitively, or None."""
    return db.session.scalar(
        sa.select(User)
        .where(
            sa.func.lower(User.Email) == user_email.lower()
        )
    )

def get_all_users():
    """Return every User row as a list."""
    return db.session.scalars(
        sa.select(User)
    ).all()

# =========== Check From Database =============
def exists_user_by_id(user_id):
    """Return True if a User with this id exists."""
    return db.session.scalar(
        sa.select(
            sa.exists()
            .where(
                User.UserID == user_id
            )
        )
    )
    
def exists_user_by_email(user_email):
    """Return True if a User with this email exists, ignoring case."""
    return  db.session.scalar(
        sa.select(
            sa.exists()
            .where(
                sa.func.lower(User.Email) == user_email.lower()
            )
        )
    )

def has_email(email, id):
    """Return True if the user with this id has this email, ignoring case.

    Used to tell an unchanged email apart from a clash with another account.
    """
    return db.session.scalar(
        sa.select(
            sa.exists()
            .where(
                sa.func.lower(User.Email) == email.lower(),
                User.UserID == id
            )
        )
    )