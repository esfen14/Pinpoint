"""Multi-bind escalation upgrade/downgrade preserves installed recipient data."""
import json
from pathlib import Path
import subprocess
import sys


def test_migration_round_trip():
    result = subprocess.run([sys.executable, 'tests/support/escalation_migration_runner.py'],
                            cwd=Path(__file__).resolve().parents[2], capture_output=True,
                            text=True, timeout=180)
    assert result.returncode == 0, (result.stdout + result.stderr)[-3000:]
    report = json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert report['empty'] == report['reupgrade_empty'] == 0
    assert report['preserved'] and report['history_unchanged'] and report['removed']
    assert report['both_binds_single_version']
    assert len(report['invalid_rejected']) == 4
    assert report['rows'] == [[1, 2, 5, 10, 'pinpoint_host_1', 1]]
