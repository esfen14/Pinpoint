"""Notification policy model defaults remain compatible with existing Nagios config."""

from app.system_models import NotificationPolicy


def test_notification_policy_defaults(db_session):
    policy = NotificationPolicy(Id=1)
    db_session.session.add(policy)
    db_session.session.commit()

    assert policy.Quiet_Hours == []
    assert policy.Host_Options == "d,u,r,f,s"
    assert policy.Service_Options == "w,u,c,r,f,s"
    assert policy.Renotify_Interval == 30
    assert policy.Version == 1
    assert policy.Updated_By is None
