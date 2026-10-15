"""
Generated Nagios config for the event handler (app/network_discovery/host_config_templates.py).

Nothing may change for objects an enabled action does not cover, or when no action is enabled,
or when the handler program is not installed on this machine (Nagios rejects an undefined
command). Every macro in the handler command must be single-quoted (threat T3).
"""
import re

import pytest

from app.network_discovery import host_config_templates as templates
from app.network_discovery.create_host_cfg import _create_host_cfg_file
from app.system_models import RemediationAction, RemediationActionType, RemediationScope

HOST = {"host_name": "web-01", "alias": "web-01", "address": "10.0.0.1", "contact_groups": "system_users"}
OTHER_HOST = {"host_name": "db-01", "alias": "db-01", "address": "10.0.0.2", "contact_groups": "system_users"}
SERVICE = {"host_name": "web-01", "service_name": "HTTP", "contact_groups": "system_users"}
OTHER_SERVICE = {"host_name": "web-01", "service_name": "SSH", "contact_groups": "system_users"}
OTHER_HOST_SERVICE = {"host_name": "db-01", "service_name": "HTTP", "contact_groups": "system_users"}
HANDLER = "/usr/local/sbin/pinpoint-event-handler"


@pytest.fixture()
def handler_installed(monkeypatch):
    """Pretend the handler program exists, as it does on the appliance."""
    monkeypatch.setattr(templates, "handler_exists", lambda path: True)


def add_action(db_session, **changes):
    fields = dict(
        Name="restart-web", Action_Type=RemediationActionType.RECORD_ONLY, Scope_Kind=RemediationScope.SERVICE,
        Host_Pattern="web-*", Service_Pattern="HTTP", Parameters={}, Enabled=True,
        Max_Runs_Per_Hour=2, Cooldown_Seconds=600, Version=1,
    )
    fields.update(changes)
    db_session.session.add(RemediationAction(**fields))
    db_session.session.commit()


def plain(item, service=False):
    return templates.create_service(item, "check_http") if service else templates.create_host(item)


# ==========================================================
# NOTHING CHANGES WITHOUT AN ENABLED ACTION
# ==========================================================

def test_no_action_leaves_objects_and_commands_unchanged(db_session, handler_installed):
    assert "event_handler" not in templates.create_host(HOST)
    assert "event_handler" not in templates.create_service(SERVICE, "check_http")
    assert templates.create_event_handler_commands() == ""


def test_a_disabled_action_changes_nothing(db_session, handler_installed):
    baseline = (templates.create_host(HOST), templates.create_service(SERVICE, "check_http"))
    add_action(db_session, Enabled=False)
    assert (templates.create_host(HOST), templates.create_service(SERVICE, "check_http")) == baseline
    assert templates.create_event_handler_commands() == ""


def test_full_config_is_byte_identical_when_no_action_is_enabled(app, db_session, tmp_path, plain_alert_email, handler_installed):
    app.config["HOST_CONFIG_DIR"] = tmp_path
    baseline = _create_host_cfg_file({}).read_bytes()
    add_action(db_session, Enabled=False)
    assert _create_host_cfg_file({}).read_bytes() == baseline


def test_enabled_actions_do_nothing_when_the_handler_is_not_installed(db_session, monkeypatch):
    monkeypatch.setattr(templates, "handler_exists", lambda path: False)
    baseline = templates.create_service(SERVICE, "check_http")
    add_action(db_session)
    assert templates.create_service(SERVICE, "check_http") == baseline
    assert templates.create_event_handler_commands() == ""


@pytest.mark.parametrize("path", ["/usr/local/sbin/pinpoint event", "/usr/local/sbin/x;y", "relative/path", "/a/$(id)"])
def test_an_unsafe_handler_path_is_never_written_into_config(db_session, monkeypatch, path):
    monkeypatch.setattr(templates, "handler_exists", lambda p: True)
    monkeypatch.setattr(templates, "EVENT_HANDLER_PATH", path)
    add_action(db_session)
    assert templates.event_handler_path() is None
    assert templates.create_event_handler_commands() == ""
    assert "event_handler" not in templates.create_service(SERVICE, "check_http")


# ==========================================================
# ONLY COVERED OBJECTS GET THE HANDLER
# ==========================================================

def test_a_covered_service_gets_the_handler_and_nothing_else_changes(db_session, handler_installed):
    baseline = templates.create_service(SERVICE, "check_http")
    add_action(db_session)
    covered = templates.create_service(SERVICE, "check_http")
    assert "    event_handler                   pinpoint_event_handler_service" in covered
    assert "    event_handler_enabled           1" in covered
    removed = [line for line in covered.split("\n") if "event_handler" not in line]
    assert "\n".join(removed) == baseline
    assert covered.rstrip().endswith("}")


@pytest.mark.parametrize("item", [OTHER_SERVICE, OTHER_HOST_SERVICE])
def test_other_services_are_rendered_exactly_as_before(db_session, handler_installed, item):
    baseline = templates.create_service(item, "check_http")
    add_action(db_session)
    assert templates.create_service(item, "check_http") == baseline


def test_hosts_are_untouched_by_a_service_scope_action(db_session, handler_installed):
    baseline = templates.create_host(HOST)
    add_action(db_session)
    assert templates.create_host(HOST) == baseline


def test_a_host_scope_action_covers_matching_hosts_only(db_session, handler_installed):
    add_action(db_session, Scope_Kind=RemediationScope.HOST, Host_Pattern="web-*", Service_Pattern=None)
    assert "event_handler                   pinpoint_event_handler_host" in templates.create_host(HOST)
    assert "event_handler" not in templates.create_host(OTHER_HOST)
    assert "event_handler" not in templates.create_service(SERVICE, "check_http")


def test_wildcard_patterns_are_matched_the_same_way_as_in_the_consumer(db_session, handler_installed):
    add_action(db_session, Host_Pattern="*", Service_Pattern="HT*")
    assert "event_handler" in templates.create_service(SERVICE, "check_http")
    assert "event_handler" in templates.create_service(OTHER_HOST_SERVICE, "check_http")
    assert "event_handler" not in templates.create_service(OTHER_SERVICE, "check_http")


def test_an_object_covered_by_two_actions_gets_one_handler_line(db_session, handler_installed):
    add_action(db_session, Name="one")
    add_action(db_session, Name="two")
    assert templates.create_service(SERVICE, "check_http").count("event_handler ") == 1


# ==========================================================
# THE COMMAND DEFINITIONS
# ==========================================================

def test_both_commands_are_defined_once_when_an_action_is_enabled(db_session, handler_installed):
    add_action(db_session)
    commands = templates.create_event_handler_commands()
    assert commands.count("define command {") == 2
    assert "command_name    pinpoint_event_handler_service" in commands
    assert "command_name    pinpoint_event_handler_host" in commands
    assert f"/usr/bin/python3 -I {HANDLER} service " in commands
    assert f"/usr/bin/python3 -I {HANDLER} host " in commands


def test_every_macro_is_single_quoted(db_session, handler_installed):
    add_action(db_session)
    commands = templates.create_event_handler_commands()
    macros = re.findall(r"\$[A-Z]+\$", commands)
    assert macros, "expected Nagios macros in the command lines"
    assert len(re.findall(r"'\$[A-Z]+\$'", commands)) == len(macros)
    assert '"' not in commands and "`" not in commands


def test_the_full_config_contains_the_commands_only_when_enabled(app, db_session, tmp_path, plain_alert_email, handler_installed):
    app.config["HOST_CONFIG_DIR"] = tmp_path
    baseline = _create_host_cfg_file({}).read_bytes()
    assert b"pinpoint_event_handler" not in baseline
    add_action(db_session)
    configured = _create_host_cfg_file({}).read_bytes()
    assert configured.count(b"command_name    pinpoint_event_handler_service") == 1
    assert configured.count(b"command_name    pinpoint_event_handler_host") == 1
    assert baseline != configured
