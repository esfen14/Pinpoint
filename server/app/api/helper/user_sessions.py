"""
Server-side sign-in records (UserSession), which make logout and credential
changes final whatever cookie a client still holds. Only create_session and the
purge it runs add or remove rows; callers commit.
"""
import secrets
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from flask import current_app

from app import db
from app.system_models import UserSession


def utc_now():
    """Return the current time as naive UTC, the form SQLite stores."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_session(user_id, remembered):
    """Add a record for a new sign-in and return its random session id."""
    purge_dead_sessions()
    now = utc_now()
    session_id = secrets.token_urlsafe(32)
    db.session.add(UserSession(
        SessionID=session_id,
        UserID=user_id,
        Created_At=now,
        Last_Activity=now,
        Remembered=remembered,
    ))
    return session_id


def get_live_session(session_id, user_id):
    """Return the user's unrevoked record, or None."""
    if not isinstance(session_id, str):
        return None
    record = db.session.get(UserSession, session_id)
    if record is None or record.UserID != user_id or record.Revoked_At is not None:
        return None
    return record


def revoke_session(session_id):
    """Revoke one sign-in. An unknown or already revoked id changes nothing."""
    db.session.execute(
        sa.update(UserSession)
        .where(UserSession.SessionID == session_id, UserSession.Revoked_At.is_(None))
        .values(Revoked_At=utc_now())
    )


def revoke_user_sessions(user_id, keep=None):
    """Revoke every sign-in of a user, except the session id given as keep."""
    query = sa.update(UserSession).where(
        UserSession.UserID == user_id, UserSession.Revoked_At.is_(None)
    )
    if keep is not None:
        query = query.where(UserSession.SessionID != keep)
    db.session.execute(query.values(Revoked_At=utc_now()))


def purge_dead_sessions():
    """
    Delete revoked records, and records idle for longer than a remembered cookie
    lasts, since no cookie can use them any more.
    """
    oldest = utc_now() - current_app.config["PERMANENT_SESSION_LIFETIME"]
    db.session.execute(sa.delete(UserSession).where(sa.or_(
        UserSession.Revoked_At.is_not(None),
        UserSession.Last_Activity < oldest,
    )))
