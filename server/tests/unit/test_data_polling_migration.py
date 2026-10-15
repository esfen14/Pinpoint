"""Populated multi-bind polling migration round trip."""
import json
import subprocess
import sys
from pathlib import Path


def test_populated_upgrade_and_downgrade():
    result = subprocess.run([sys.executable, "tests/support/data_polling_migration_runner.py"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr[-3000:]
    report = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert "Data_Polling_Interval" not in report["columns_before"]
    assert report["polling_after_upgrade"] == [[10, 60]]
    assert "Data_Polling_Interval" not in report["columns_after_downgrade"]
    assert report["check_interval_after_downgrade"] == [[10]]
    assert report["polling_after_reupgrade"] == [[10, 60]]
