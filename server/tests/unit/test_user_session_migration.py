"""USER_SESSION multi-bind migration upgrade and downgrade (#339)."""
import json
import subprocess
import sys


def test_user_session_migration_roundtrip():
    result = subprocess.run(
        [sys.executable, 'tests/support/user_session_migration_runner.py'],
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.split('REPORT_BEGIN')[1].split('REPORT_END')[0])
    assert report['columns'] == [
        'SessionID', 'UserID', 'Created_At', 'Last_Activity', 'Remembered', 'Revoked_At',
    ]
    assert report['indexed'] == ['UserID']
    assert report['history_unchanged'] and report['removed'] and report['restored']
