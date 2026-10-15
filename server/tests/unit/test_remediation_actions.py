"""
tests/unit/test_remediation_actions.py — The code-defined remediation action registry
(app/remediation_actions.py): types, parameter validation and the record_only action.
"""
import pytest

from app import remediation_actions as registry


def test_record_only_is_the_only_type_shipped_here():
    assert list(registry.ACTION_TYPES) == ["record_only"]


def test_each_type_describes_itself_for_the_form():
    info = registry.describe_types()
    assert info == [{
        "key": "record_only",
        "label": "Record only",
        "description": info[0]["description"],
        "parameters": [],
    }]
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
