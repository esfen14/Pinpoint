"""
tests/unit/test_remediation_migration.py — The remediation tables migration
(migrations/versions/e4a7c1d9b305_remediation_tables.py).

Runs the migration on throwaway SQLite files (in a subprocess, see
tests/support/remediation_migration_runner.py) and checks that it creates the action and run
tables with the documented columns, refuses a repeated event for the same action, and
downgrades and upgrades again.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[2]
ACTION_COLUMNS = {
    "Id", "Name", "Action_Type", "Scope_Kind", "Host_Pattern", "Service_Pattern", "Parameters",
    "Enabled", "Max_Runs_Per_Hour", "Cooldown_Seconds", "Version", "Updated_By", "Updated_At",
}
RUN_COLUMNS = {
    "Id", "Event_Key", "Action_Id", "Action_Name", "Hostname", "Service", "State", "State_Type",
    "Attempt", "Received_At", "Started_At", "Finished_At", "Outcome", "Reason", "Output",
}


@pytest.fixture(scope="module")
def report():
    result = subprocess.run(
        [sys.executable, "tests/support/remediation_migration_runner.py"],
        cwd=SERVER_DIR, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    body = result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0]
    return json.loads(body)


def test_upgrade_reaches_the_new_revision(report):
    assert report["version"] == [["e4a7c1d9b305"]]
    assert report["version_after_reupgrade"] == [["e4a7c1d9b305"]]


def test_tables_are_created_by_the_upgrade_only(report):
    assert report["tables_before"] == []
    assert report["tables_after"] == ["REMEDIATION_ACTION", "REMEDIATION_RUN"]


def test_tables_have_the_documented_columns(report):
    assert set(report["action_columns"]) == ACTION_COLUMNS
    assert set(report["run_columns"]) == RUN_COLUMNS


def test_the_same_event_cannot_be_recorded_twice_for_one_action(report):
    assert report["duplicate_run_rejected"] is True


def test_downgrade_removes_the_tables_and_upgrade_restores_them(report):
    assert report["tables_after_downgrade"] == []
    assert report["tables_after_reupgrade"] == ["REMEDIATION_ACTION", "REMEDIATION_RUN"]


BOTH = ["remediation.manage", "remediation.view"]


def test_upgrade_adds_both_permissions_and_grants_them_to_the_administrator(report):
    assert report["permissions"] == {"existing": BOTH, "administrator": BOTH}


def test_downgrade_removes_the_permissions_and_their_grants_and_upgrade_restores_them(report):
    assert report["permissions_after_downgrade"] == {"existing": [], "administrator": []}
    assert report["permissions_after_reupgrade"] == {"existing": BOTH, "administrator": BOTH}


# ==========================================================
# restart_local_service migration (b8e3d5f2a417)
# ==========================================================

@pytest.fixture(scope="module")
def restart_report():
    result = subprocess.run(
        [sys.executable, "tests/support/remediation_restart_migration_runner.py"],
        cwd=SERVER_DIR, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    body = result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0]
    return json.loads(body)


def test_restart_migration_keeps_existing_actions_and_accepts_the_new_type(restart_report):
    assert restart_report["version"] == [["b8e3d5f2a417"]]
    assert restart_report["kept_after_upgrade"] == ["keep"]
    assert restart_report["names_with_restart"] == ["keep", "restart"]


def test_restart_migration_downgrade_drops_only_the_new_type_and_upgrade_returns(restart_report):
    assert restart_report["version_after_downgrade"] == [["a4c8e1b7d933"]]
    assert restart_report["names_after_downgrade"] == ["keep"]
    assert restart_report["version_after_reupgrade"] == [["b8e3d5f2a417"]]
    assert restart_report["names_after_reupgrade"] == ["keep"]


# ==========================================================
# safety controls migration (f155a3c7d2b1)
# ==========================================================

@pytest.fixture(scope="module")
def safety_report():
    result = subprocess.run(
        [sys.executable, "tests/support/remediation_safety_migration_runner.py"],
        cwd=SERVER_DIR, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    body = result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0]
    return json.loads(body)


def test_safety_migration_adds_the_columns_and_state_table_with_safe_defaults(safety_report):
    assert safety_report["version"] == [["f155a3c7d2b1"]]
    assert safety_report["tables_before"] == ["REMEDIATION_ACTION", "REMEDIATION_RUN"]
    assert safety_report["tables_after"] == [
        "REMEDIATION_ACTION", "REMEDIATION_CONSUMER_STATE", "REMEDIATION_RUN"]
    assert {"Remediation_Enabled", "Remediation_Retention_Days"} <= set(safety_report["settings_columns_after"])
    assert "Run_When_Acknowledged" in safety_report["action_columns_after"]
    assert set(safety_report["state_columns"]) == {
        "Id", "Last_Tick_At", "Last_Error", "Dropped_Count", "Dropped_At"}
    # Existing rows keep today's behavior: switch on, 90 days, restarts not run on acknowledged problems.
    assert safety_report["settings_defaults"] == [[1, 90]]
    assert safety_report["action_default"] == [[0]]
    assert safety_report["runs_kept"] == 1


def test_safety_migration_accepts_the_new_skip_outcomes(safety_report):
    assert safety_report["new_outcomes_accepted"] == [
        "SKIPPED_KILL_SWITCH", "SKIPPED_MAINTENANCE", "SKIPPED_DOWNTIME", "SKIPPED_ACKNOWLEDGED"]


def test_safety_migration_downgrades_and_upgrades_again(safety_report):
    assert safety_report["version_after_downgrade"] == [["d117f3b8a053"]]
    assert safety_report["tables_after_downgrade"] == ["REMEDIATION_ACTION", "REMEDIATION_RUN"]
    assert not {"Remediation_Enabled", "Remediation_Retention_Days"} & set(
        safety_report["settings_columns_after_downgrade"])
    assert "Run_When_Acknowledged" not in safety_report["action_columns_after_downgrade"]
    # Rows with an outcome the older schema cannot hold are removed; older rows stay.
    assert safety_report["runs_after_downgrade"] == ["SUCCEEDED"]
    assert safety_report["version_after_reupgrade"] == [["f155a3c7d2b1"]]
    assert safety_report["tables_after_reupgrade"] == [
        "REMEDIATION_ACTION", "REMEDIATION_CONSUMER_STATE", "REMEDIATION_RUN"]
