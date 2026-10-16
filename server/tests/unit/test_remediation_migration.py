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
# restart_remote_service migration (c7a1f4d92e60)
# ==========================================================

@pytest.fixture(scope="module")
def remote_report():
    result = subprocess.run(
        [sys.executable, "tests/support/remediation_remote_restart_migration_runner.py"],
        cwd=SERVER_DIR, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    body = result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0]
    return json.loads(body)


def test_remote_migration_adds_the_device_columns_off_by_default(remote_report):
    assert remote_report["version"] == [["c7a1f4d92e60"]]
    assert remote_report["kept_after_upgrade"] == ["keep", "local"]
    assert remote_report["names_with_remote"] == ["keep", "local", "remote"]
    columns = remote_report["ssh_columns"]
    assert "Remote_Restart_Services" in columns
    assert columns["Remote_Restart_Enabled"] in ("false", "0")


def test_remote_migration_downgrade_drops_only_the_new_type_and_columns(remote_report):
    assert remote_report["version_after_downgrade"] == [["b8e3d5f2a417"]]
    assert remote_report["names_after_downgrade"] == ["keep", "local"]
    assert "Remote_Restart_Enabled" not in remote_report["ssh_columns_after_downgrade"]
    assert remote_report["version_after_reupgrade"] == [["c7a1f4d92e60"]]
    assert remote_report["names_after_reupgrade"] == ["keep", "local"]
