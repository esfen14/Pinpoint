"""
tests/unit/test_remediation_actions.py — The code-defined remediation action registry
(app/remediation_actions.py): types, parameter validation and the record_only action.
"""
import pytest

from app import remediation_actions as registry


def test_shipped_types():
    assert list(registry.ACTION_TYPES) == ["record_only", "restart_local_service"]


def test_each_type_describes_itself_for_the_form():
    info = registry.describe_types()
    assert info[0] == {
        "key": "record_only",
        "label": "Record only",
        "description": info[0]["description"],
        "parameters": [],
    }
    assert info[0]["description"]


def test_record_only_accepts_no_parameters():
    cleaned, errors = registry.validate_parameters("record_only", {})
    assert (cleaned, errors) == ({}, {})


def test_missing_parameters_are_treated_as_empty():
    assert registry.validate_parameters("record_only", None) == ({}, {})


@pytest.mark.parametrize("hostile", [
    {"command": "rm -rf /"},
    {"path": "/etc/passwd"},
    {"unit": "nagios; reboot"},
    {"x": "$(id)"},
])
def test_unknown_parameters_are_refused_with_a_field_error(hostile):
    cleaned, errors = registry.validate_parameters("record_only", hostile)
    assert cleaned == {}
    assert set(errors) == set(hostile)


def test_parameters_must_be_an_object():
    cleaned, errors = registry.validate_parameters("record_only", ["a"])
    assert cleaned == {}
    assert "parameters" in errors


def test_unknown_action_type_is_an_error():
    cleaned, errors = registry.validate_parameters("restart_everything", {})
    assert cleaned == {}
    assert "actionType" in errors


def test_record_only_changes_nothing_and_says_so():
    result = registry.run_action("record_only", {}, registry.RunContext(
        hostname="web-01", service="HTTP", state="CRITICAL"))
    assert result.outcome == "succeeded"
    assert result.output == "recorded"


def test_running_an_unknown_type_fails_without_raising():
    result = registry.run_action("nope", {}, registry.RunContext(hostname="h", service=None, state="DOWN"))
    assert result.outcome == "failed"
    assert "Unknown" in result.output


def test_a_crashing_action_is_reported_as_failed_not_raised(monkeypatch):
    def boom(params, context):
        raise RuntimeError("password=hunter2")

    monkeypatch.setitem(registry.ACTION_TYPES, "record_only", registry.ActionType(
        key="record_only", label="x", description="x", parameters=[], validate=lambda p: ({}, {}), run=boom))
    result = registry.run_action("record_only", {}, registry.RunContext(hostname="h", service=None, state="DOWN"))
    assert result.outcome == "failed"
    assert "hunter2" not in result.output


def test_an_action_that_overruns_its_timeout_is_reported_as_timed_out(monkeypatch):
    import time

    monkeypatch.setitem(registry.ACTION_TYPES, "record_only", registry.ActionType(
        key="record_only", label="x", description="x", parameters=[], validate=lambda p: ({}, {}),
        run=lambda params, context: time.sleep(1), timeout_seconds=0.05))
    result = registry.run_action("record_only", {}, registry.RunContext(hostname="h", service=None, state="DOWN"))
    assert result.outcome == "timed_out"


# ==========================================================
# restart_local_service
# ==========================================================

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

RUN = "app.remediation_actions.subprocess.run"
CTX = registry.RunContext(hostname="nagios-host", service="Nagios Core", state="CRITICAL")
CTX_MAINTENANCE = registry.RunContext(
    hostname="nagios-host", service="Nagios Core", state="CRITICAL", maintenance_mode=True)


def test_permitted_units_are_listed_for_the_form():
    restart = next(t for t in registry.describe_types() if t["key"] == "restart_local_service")
    assert restart["parameters"] == [{
        "name": "unit", "label": "Service to restart", "type": "choice",
        "choices": list(registry.RESTARTABLE_UNITS), "required": True,
    }]
    assert "pinpoint-gunicorn" not in registry.RESTARTABLE_UNITS


def test_restart_accepts_a_listed_unit():
    assert registry.validate_parameters("restart_local_service", {"unit": "nagios"}) == ({"unit": "nagios"}, {})


@pytest.mark.parametrize("bad", [
    {}, {"unit": ""}, {"unit": "sshd"}, {"unit": "nagios; reboot"}, {"unit": "../nagios"},
    {"unit": "nagios.service"}, {"unit": "nagios "}, {"unit": ["nagios"]}, {"unit": None},
    {"unit": "nagios", "command": "id"},
])
def test_restart_refuses_anything_not_on_the_list(bad):
    cleaned, errors = registry.validate_parameters("restart_local_service", bad)
    assert cleaned == {} and errors


def test_restart_runs_sudo_with_an_argument_list_and_no_shell():
    with patch(RUN, return_value=SimpleNamespace(
            returncode=0, stdout="", stderr="")) as run:
        result = registry.run_action("restart_local_service", {"unit": "nagios"}, CTX)
    assert result.outcome == "succeeded"
    assert "exit code 0" in result.output
    args, kwargs = run.call_args
    assert args[0] == ["sudo", "-n", "/usr/bin/systemctl", "restart", "nagios"]
    assert kwargs.get("shell", False) is False
    assert kwargs["timeout"] > 0


def test_restart_refuses_a_unit_off_the_list_at_run_time():
    with patch(RUN) as run:
        result = registry.run_action("restart_local_service", {"unit": "sshd"}, CTX)
    assert result.outcome == "failed"
    assert "not on the list" in result.output
    run.assert_not_called()


def test_restart_is_refused_in_maintenance_mode():
    with patch(RUN) as run:
        result = registry.run_action("restart_local_service", {"unit": "nagios"}, CTX_MAINTENANCE)
    assert result.outcome == "failed"
    assert "Maintenance Mode" in result.output
    run.assert_not_called()


def test_restart_records_a_nonzero_exit_code_and_redacts_output():
    done = SimpleNamespace(returncode=5, stdout="", stderr="Unit failed password=hunter2")
    with patch(RUN, return_value=done):
        result = registry.run_action("restart_local_service", {"unit": "nagios"}, CTX)
    assert result.outcome == "failed"
    assert "exit code 5" in result.output
    assert "hunter2" not in result.output


def test_restart_reports_a_missing_sudo_rule_without_a_raw_exception():
    with patch(RUN, side_effect=OSError("secret=abc")):
        result = registry.run_action("restart_local_service", {"unit": "nagios"}, CTX)
    assert result.outcome == "failed"
    assert "abc" not in result.output


def test_restart_times_out_and_reports_it():
    with patch(RUN, side_effect=subprocess.TimeoutExpired("sudo", 1)):
        result = registry.run_action("restart_local_service", {"unit": "nagios"}, CTX)
    assert result.outcome == "timed_out"
