"""The notification policy migration seeds defaults and supports downgrade."""

import json
import subprocess
import sys
from pathlib import Path


def test_notification_policy_migration_round_trip():
    result = subprocess.run(
        [sys.executable, "tests/support/notification_policy_migration_runner.py"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    data = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert data["rows"] == [[1, "[]", "d,u,r,f,s", "w,u,c,r,f,s", 30, 1]]
    assert "NOTIFICATION_POLICY" not in data["tables_after_downgrade"]
