"""The released interface revision and preview recipient revision upgrade together."""
import json
from pathlib import Path
import subprocess
import sys

from alembic.script import ScriptDirectory
import pytest


def test_installer_has_one_migration_head():
    scripts = ScriptDirectory(str(Path(__file__).resolve().parents[2] / 'migrations'))
    assert len(scripts.get_heads()) == 1, 'flask db upgrade must accept the unqualified head'


@pytest.mark.parametrize('before', ['b7d3f1a9c264', 'a79e14c0b621'])
def test_populated_interface_or_recipient_install_upgrades_and_downgrades(before):
    result = subprocess.run(
        [sys.executable, 'tests/support/interface_recipient_migration_runner.py', before],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-3000:]
    report = json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert set(report['upgraded']) == {'DEVICE_INTERFACE', 'HOST_ALERT_RECIPIENT'}
    assert report['preserved_upgrade'] and report['preserved_downgrade'] and report['preserved_reupgrade']
    assert report['other_table_empty'] and report['both_binds_single_version']
    assert not report['foreign_key_errors']
    assert report['history_unchanged'] and report['legacy'] == [['existing']]
