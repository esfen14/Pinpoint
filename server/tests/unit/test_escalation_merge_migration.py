"""Escalation and current-main installs converge without losing either feature."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('starting_head', ['cd74e5f8a2d5', 'e4a7c1d9b305'])
def test_escalation_and_remediation_merge_preserves_populated_installs(starting_head):
    result = subprocess.run(
        [sys.executable, 'tests/support/ncpa_interface_merge_runner.py', starting_head],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-3500:]
    report = json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert len(report['heads']) == 1
    assert report['system_version'] == report['history_version'] == [[report['heads'][0]]]
    assert report['recipient'] == report['roundtrip_recipient'] == [[1, 1]]
    assert report['polling'] == report['roundtrip_polling'] == 120
    assert report['port'] == report['roundtrip_port'] == 5703
    assert report['interface'] == report['roundtrip_interface'] == ['eth-test', 1]
    assert report['history_marker'] == 'preserved'
    assert report['existing_feature_rows_preserved']
    assert report['merge_roundtrip_preserves_features']
