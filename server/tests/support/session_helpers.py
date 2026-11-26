"""Read and age the server-side session record behind a test client."""
from datetime import timedelta

from app import db
from app.api.helper.user_sessions import utc_now
from app.system_models import UserSession


def get_session_record(client):
    """Return the UserSession row the client's cookie points at, or None."""
    with client.session_transaction() as sess:
        sid = sess.get("sid")
    if sid is None:
        return None
    db.session.expire_all()
    return db.session.get(UserSession, sid)


def set_idle_minutes(client, minutes):
    record = get_session_record(client)
    record.Last_Activity = utc_now() - timedelta(minutes=minutes)
    db.session.commit()


def get_last_activity(client):
    record = get_session_record(client)
    return None if record is None else record.Last_Activity
