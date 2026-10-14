"""
tests/unit/test_check_timing_migration.py — The retry interval and maximum check
attempts migration (migrations/versions/b7d3f1a9c8e5_check_retry_interval_and_attempts.py).

Runs the migration on throwaway SQLite files (in a subprocess, see
tests/support/check_timing_migration_runner.py) with an existing settings row, and
checks that the new columns default to the values the generated config always
used, that other settings are untouched, and that it downgrades and upgrades again.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[2]
NEW_COLUMNS = ("Retry_Interval", "Max_Check_Attempts")


@pytest.fixture(scope="module")
def report():
    result = subprocess.run(
        [sys.executable, "tests/support/check_timing_migration_runner.py"],
        cwd=SERVER_DIR, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    body = result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0]
    return json.loads(body)


def test_upgrade_reaches_the_new_revision(report):
    assert report["version"] == [["b7d3f1a9c8e5"]]
    assert report["version_after_reupgrade"] == [["b7d3f1a9c8e5"]]


def test_the_new_columns_are_added(report):
    for column in NEW_COLUMNS:
        assert column not in report["columns_before"]
        assert column in report["columns_after"]


def test_an_existing_row_gets_the_values_the_config_always_used(report):
    # (Check_Interval, Retry_Interval, Max_Check_Attempts); the saved interval of 10 is untouched.
    assert report["timing_after_upgrade"] == [[10, 1, 3]]


def test_downgrade_drops_only_the_new_columns(report):
    for column in NEW_COLUMNS:
        assert column not in report["columns_after_downgrade"]
    assert "Check_Interval" in report["columns_after_downgrade"]
    assert report["check_interval_after_downgrade"] == [[10]]


def test_upgrade_again_restores_the_defaults(report):
    assert report["timing_after_reupgrade"] == [[10, 1, 3]]
