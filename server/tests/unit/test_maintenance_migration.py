"""The maintenance window migration creates both tables, downgrades cleanly and upgrades again."""

import json
import subprocess
import sys
from pathlib import Path


def test_maintenance_migration_round_trip():
    result = subprocess.run(
        [sys.executable, "tests/support/maintenance_migration_runner.py"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    data = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert data["has_table_after_upgrade"] is True
    assert {"WindowID", "NetDiscoveryID", "Start_At", "End_At", "Recurrence", "Recurrence_Until",
            "Time_Zone", "Comment", "Status", "Last_Occurrence_Sent", "Created_At",
            "Created_By"} <= set(data["columns"])
    assert data["has_occurrence_table_after_upgrade"] is True
    assert data["has_table_after_downgrade"] is False
    assert data["has_occurrence_table_after_downgrade"] is False
    assert data["has_table_after_second_upgrade"] is True
