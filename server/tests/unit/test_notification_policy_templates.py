"""Generated notification directives and default compatibility."""
from app.system_models import NotificationPolicy
from app.network_discovery.create_host_cfg import _create_host_cfg_file
from app.network_discovery.host_config_templates import (
    create_host, create_service, create_contact_template, create_notification_timeperiod,
)

HOST = {"host_name": "h", "alias": "alias", "address": "10.0.0.1", "contact_groups": "system_users"}
SERVICE = {"host_name": "h", "service_name": "ssh", "contact_groups": "system_users"}


def test_default_templates_preserve_existing_output(db_session):
    host = create_host(HOST)
    service = create_service(SERVICE, "check_ssh")
    contact = create_contact_template("generic-contact")
    assert "notification_interval           30\n    notification_period             24x7" in host
    assert "notification_period" not in service
    assert "notification_options" not in service
    assert "service_notification_period     24x7" in contact
    assert create_notification_timeperiod() == ""


def test_full_config_includes_period_only_with_quiet_hours(app, db_session, tmp_path):
    app.config['HOST_CONFIG_DIR'] = tmp_path
    baseline = _create_host_cfg_file({}).read_bytes()
    db_session.session.add(NotificationPolicy(
        Id=1, Quiet_Hours=[{"weekday": "monday", "start": "09:00", "end": "10:00"}],
    ))
    db_session.session.flush()
    configured = _create_host_cfg_file({}).read_bytes()
    assert b"define timeperiod {" in configured
    assert b"pinpoint_notify" in configured
    assert baseline != configured


def test_quiet_hours_render_allowed_complement_and_references(db_session):
    db_session.session.add(NotificationPolicy(
        Id=1, Quiet_Hours=[{"weekday": "monday", "start": "09:00", "end": "10:00"}],
        Host_Options="d,r", Service_Options="w,c", Renotify_Interval=15,
    ))
    db_session.session.flush()
    period = create_notification_timeperiod()
    assert "define timeperiod {" in period
    assert "timeperiod_name" in period and "pinpoint_notify" in period
    assert "monday" in period and "00:00-09:00,10:00-24:00" in period
    assert "tuesday" in period and "00:00-24:00" in period
    assert "notification_period             pinpoint_notify" in create_host(HOST)
    assert "notification_options" in create_host(HOST)
    assert "notification_period" in create_service(SERVICE, "check_ssh")
    assert "service_notification_period     pinpoint_notify" in create_contact_template("generic-contact")
