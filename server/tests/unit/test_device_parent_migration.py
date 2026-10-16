"""Populated multi-bind parent migration upgrade/downgrade and SQL constraints."""
import json
import subprocess
import sys

def test_parent_migration_roundtrip():
    result = subprocess.run([sys.executable,'tests/support/device_parent_migration_runner.py'],capture_output=True,text=True,timeout=90)
    assert result.returncode==0, result.stdout+result.stderr
    report=json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert report['empty']==report['reupgrade_empty']==0
    assert report['pairs']==[[1,2],[1,3]]
    assert report['rejected']==[[1,2],[1,1],[1,999],[999,2]]
    assert report['history_unchanged'] and report['removed']
    assert report['history_version']==[['b117d9a2c041']]
    assert report['devices']==[['legacy-1'],['legacy-2'],['legacy-3']]
