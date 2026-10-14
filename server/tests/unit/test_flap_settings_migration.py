"""
tests/unit/test_flap_settings_migration.py — The flap detection settings migration
(migrations/versions/c5e2a8f4d716_flap_detection_settings.py).

Runs the migration on throwaway SQLite files (in a subprocess, see
tests/support/flap_settings_migration_runner.py) with an existing settings row, and
checks that the new columns default to "flap detection on, Nagios's own thresholds",
that other settings are untouched, and that it downgrades and upgrades again.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[2]
NEW_COLUMNS = ("Flap_Detection_Enabled", "Flap_Low_Threshold", "Flap_High_Threshold")


@pytest.fixture(scope="module")
def report():
    result = subprocess.run(
        [sys.executable, "tests/support/flap_settings_migration_runner.py"],
        cwd=SERVER_DIR, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    body = result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0]
    return json.loads(body)


def test_upgrade_reaches_the_new_revision(report):
    assert report["version"] == [["c5e2a8f4d716"]]
    assert report["version_after_reupgrade"] == [["c5e2a8f4d716"]]


def test_the_new_columns_are_added(report):
    for column in NEW_COLUMNS:
        assert column not in report["columns_before"]
        assert column in report["columns_after"]


def test_an_existing_row_keeps_flap_detection_on_with_nagios_thresholds(report):
    # (Check_Interval, Flap_Detection_Enabled, low, high); the saved interval of 10 is untouched.
    assert report["flap_after_upgrade"] == [[10, 1, None, None]]


def test_downgrade_drops_only_the_new_columns(report):
    for column in NEW_COLUMNS:
        assert column not in report["columns_after_downgrade"]
    assert "Check_Interval" in report["columns_after_downgrade"]
    assert report["check_interval_after_downgrade"] == [[10]]


def test_upgrade_again_restores_the_defaults(report):
    assert report["flap_after_reupgrade"] == [[10, 1, None, None]]
