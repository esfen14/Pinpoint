"""The device interface migration creates the table, downgrades cleanly and upgrades again."""

import json
import subprocess
import sys
from pathlib import Path


def test_device_interface_migration_round_trip():
    result = subprocess.run(
        [sys.executable, "tests/support/device_interface_migration_runner.py"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    data = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert data["has_table_after_upgrade"] is True
    assert set(data["columns"]) == {
        "DeviceInterfaceID", "If_Index", "Name", "Speed_Bps", "Admin_Status", "Oper_Status",
        "Monitored", "Present", "Last_Seen_At", "NetDiscoveryID",
    }
    assert data["has_table_after_downgrade"] is False
    assert data["has_table_after_second_upgrade"] is True
