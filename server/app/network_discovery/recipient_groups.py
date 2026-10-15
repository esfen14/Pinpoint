"""One eligibility calculation for generated recipient groups and escalation choices."""
import sqlalchemy as sa

from app import db
from app.system_models import HostAlertRecipient, User, UserStatus


def recipient_groups():
    """Return eligible contacts and known groups, retaining empty groups for explanations.

    Names are fixed literals or numeric device IDs. No commit or filesystem work.
    The writer decides which per-device groups are needed by generated objects.
    """
    users = db.session.scalars(sa.select(User).where(
        User.Status == UserStatus.ACTIVE, User.Receive_Email_Alerts.is_(True)
    )).all()
    emails = {user.UserID: user.Email for user in users}
    groups = {'system_users': [user.Email for user in users]}
    for row in db.session.scalars(sa.select(HostAlertRecipient).order_by(
            HostAlertRecipient.NetDiscoveryID, HostAlertRecipient.UserID)):
        members = groups.setdefault(f'pinpoint_host_{row.NetDiscoveryID}', [])
        if row.UserID in emails:
            members.append(emails[row.UserID])
    return users, groups
