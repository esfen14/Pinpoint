"""Both published topology/current-main heads converge without losing rows."""
import json
import subprocess
import sys

import pytest


@pytest.mark.parametrize('starting_head', ['b117d9a2c041', '99f584ed8151'])
def test_topology_merge_preserves_populated_installs(starting_head):
    result = subprocess.run(
        [sys.executable, 'tests/support/topology_merge_runner.py', starting_head],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]
    report = json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert report['single_head']
    assert report['existing_preserved']
    assert report['roundtrip_preserved']
    assert report['history_preserved']
    assert report['parents'] == [[1, 2], [1, 3]]
