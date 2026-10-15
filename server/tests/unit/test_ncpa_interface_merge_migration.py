"""Both published migration heads must upgrade to one head without losing data."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("starting_head", ["7db78f308ee5", "b7d3f1a9c264", "e4a129c7b630", "e79b7d3c2641", "f129a79e6301", "f6d2c8a1b390"])
def test_upgrade_from_each_existing_head_and_roundtrip(starting_head):
    result = subprocess.run(
        [sys.executable, "tests/support/ncpa_interface_merge_runner.py", starting_head],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-3500:]
    report = json.loads(result.stdout.split("REPORT_BEGIN")[1].split("REPORT_END")[0])
    assert len(report["heads"]) == 1
    assert report["system_version"] == report["history_version"] == [[report["heads"][0]]]
    assert report["recipient"] == report["roundtrip_recipient"] == [[1, 1]]
    assert report["polling"] == report["roundtrip_polling"] == 120
    assert report["port"] == 5703
    assert report["interface"] == ["eth-test", 1]
    assert report["history_marker"] == "preserved"
    assert report["roundtrip_port"] == 5703
    assert report["roundtrip_interface"] == ["eth-test", 1]
