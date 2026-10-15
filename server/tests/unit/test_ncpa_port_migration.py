"""Backfill and downgrade coverage for the per-device NCPA listener port."""
import json
import subprocess
import sys
from pathlib import Path


def test_port_migration_backfills_deployed_only_and_downgrades():
    result = subprocess.run(
        [sys.executable, "tests/support/ncpa_port_migration_runner.py"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-2500:]
    report = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert report["up"] == [[1, 5693], [2, None], [3, None]]
    assert "Port" not in report["down_columns"]
    assert report["remaining"] == [[1, "DEPLOYED"], [2, "FAILED"], [3, "PENDING_NCPA"]]
