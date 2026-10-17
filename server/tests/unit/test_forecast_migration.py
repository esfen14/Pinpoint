"""The resource forecast migration creates its table, downgrades cleanly and upgrades again."""

import json
import subprocess
import sys
from pathlib import Path


def test_forecast_migration_round_trip():
    result = subprocess.run(
        [sys.executable, "tests/support/forecast_migration_runner.py"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    data = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert data["has_table_after_upgrade"] is True
    assert {"ForecastID", "Hostname", "Service", "Metric", "Kind", "Threshold", "Crossing_At",
            "Slope_Per_Hour", "R_Squared", "Sample_Count", "Window_Hours", "Current_Value",
            "Unit", "Computed_At"} <= set(data["columns"])
    assert data["has_table_after_downgrade"] is False
    assert data["has_table_after_second_upgrade"] is True
