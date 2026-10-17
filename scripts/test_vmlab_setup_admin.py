"""Exercise setup-admin with synthetic credentials and fake SSH/API endpoints."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class SetupAdminTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ['scripts', 'lab', 'bin', 'state']:
            (self.root / name).mkdir()
        shutil.copyfile(Path(__file__).with_name('vmlab'), self.root / 'scripts/vmlab')
        (self.root / 'scripts/vmlab_preflight.py').write_text('raise SystemExit(0)\n')
        self.executable('VBoxManage', '#!/bin/sh\nexit 0\n')
        self.executable('ssh', '''#!/bin/sh
case "$*" in
  *"sudo cat /root/pinpoint-install-credentials.txt"*) cat "$FAKE_CREDENTIALS" ;;
  *"sudo rm -f /root/pinpoint-install-credentials.txt"*) touch "$FAKE_REMOVED" ;;
  *) exit 1 ;;
esac
''')
        (self.root / 'config').write_text('VMLAB_WEB_PORT=18091\n')
        self.credentials = self.root / 'credentials'
        self.credentials.write_text('')
        self.responses = self.root / 'responses.json'
        self.calls = self.root / 'calls.jsonl'
        (self.root / 'lab/smoke.py').write_text('''import json, os
from pathlib import Path
class Client:
    def __init__(self, base):
        self.base = base
    def call(self, method, path, body=None):
        with Path(os.environ['FAKE_CALLS']).open('a') as output:
            output.write(json.dumps([self.base, method, path, body]) + '\\n')
        response = json.loads(Path(os.environ['FAKE_RESPONSES']).read_text())[path]
        if response == 'unavailable':
            raise OSError('synthetic-secret-from-transport')
        return response
''')
        self.saved_email = 'synthetic-saved@lab.example.com'
        self.saved_password = 'SyntheticSaved-Secret9!'
        self.installer_email = 'synthetic-bootstrap@example.invalid'
        self.installer_password = 'SyntheticInstaller-Secret9!'

    def executable(self, name, content):
        path = self.root / 'bin' / name
        path.write_text(content)
        path.chmod(0o700)

    def run_setup(self, responses, saved=False, credentials=''):
        self.calls.unlink(missing_ok=True)
        (self.root / 'removed').unlink(missing_ok=True)
        self.responses.write_text(json.dumps(responses))
        self.credentials.write_text(credentials)
        if saved:
            (self.root / 'state/admin-email').write_text(self.saved_email)
            (self.root / 'state/admin-password').write_text(self.saved_password)
        env = dict(os.environ, PATH=str(self.root / 'bin') + ':' + os.environ['PATH'],
                   VMLAB_CONFIG=str(self.root / 'config'), VMLAB_STATE_DIR=str(self.root / 'state'),
                   FAKE_CREDENTIALS=str(self.credentials), FAKE_REMOVED=str(self.root / 'removed'),
                   FAKE_CALLS=str(self.calls), FAKE_RESPONSES=str(self.responses))
        result = subprocess.run(['bash', str(self.root / 'scripts/vmlab'), 'setup-admin'],
                                env=env, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        private_values = [path.read_text() for path in (self.root / 'state').glob('admin-*')]
        for value in private_values + [self.saved_email, self.saved_password, self.installer_email,
                                       self.installer_password, 'synthetic-secret-from-transport']:
            self.assertNotIn(value, output)
        return result

    def api_calls(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_previous_and_current_installer_labels_complete_setup(self):
        for label in ['Username (email):', 'Username (temporary placeholder email):']:
            with self.subTest(label=label):
                result = self.run_setup({
                    '/api/user/login': [200, {'success': True, 'data': {'needs_setup': True}}],
                    '/api/user/complete-setup': [200, {'success': True}],
                }, saved=True, credentials=f'{label}\n{self.installer_email}\nPassword:\n{self.installer_password}\n')
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = self.api_calls()
                self.assertEqual([call[2] for call in calls], ['/api/user/login', '/api/user/complete-setup'])
                self.assertTrue(all(call[0] == 'http://127.0.0.1:18091' for call in calls))
                self.assertEqual(calls[0][3], {'email': self.installer_email, 'password': self.installer_password})
                self.assertEqual((self.root / 'state/admin-email').read_text(), 'lab-admin@vmlab.example.com')
                self.assertEqual((self.root / 'state/admin-password').read_text(), calls[1][3]['new_password'])
                for filename in ['admin-email', 'admin-password']:
                    self.assertEqual((self.root / 'state' / filename).stat().st_mode & 0o777, 0o600)
                self.assertTrue((self.root / 'removed').exists())

    def test_stale_state_is_rejected_at_current_endpoint(self):
        result = self.run_setup({'/api/user/login': [401, {'success': False}]}, saved=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('already set up', result.stdout)
        self.assertEqual(self.api_calls(), [['http://127.0.0.1:18091', 'POST', '/api/user/login',
                                           {'email': self.saved_email, 'password': self.saved_password}]])
        self.assertEqual((self.root / 'state/admin-password').read_text(), self.saved_password)
        self.assertFalse((self.root / 'removed').exists())

    def test_saved_login_requires_explicit_completed_setup(self):
        for flags in [{'needs_setup': True, 'must_change_password': False},
                      {'needs_setup': False, 'must_change_password': True}, {},
                      {'needs_setup': False}]:
            with self.subTest(flags=flags):
                result = self.run_setup({
                    '/api/user/login': [200, {'success': True}],
                    '/api/user/me': [200, {'success': True, 'data': flags}],
                }, saved=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / 'removed').exists())

    def test_valid_saved_login_is_confirmed_through_current_endpoint(self):
        result = self.run_setup({
            '/api/user/login': [200, {'success': True}],
            '/api/user/me': [200, {'success': True, 'data': {'needs_setup': False, 'must_change_password': False}}],
        }, saved=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[2] for call in self.api_calls()], ['/api/user/login', '/api/user/me'])
        self.assertTrue(all(call[0] == 'http://127.0.0.1:18091' for call in self.api_calls()))
        self.assertIn('already set up', result.stdout)
        self.assertFalse((self.root / 'removed').exists())

    def test_unavailable_endpoint_does_not_expose_transport_details(self):
        result = self.run_setup({'/api/user/login': 'unavailable'}, saved=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)

    def test_setup_failure_preserves_installer_credentials_and_saved_state(self):
        result = self.run_setup({
            '/api/user/login': [200, {'success': True, 'data': {'needs_setup': True}}],
            '/api/user/complete-setup': [400, {'success': False, 'message': self.installer_password}],
        }, saved=True, credentials=f'Username (temporary placeholder email):\n{self.installer_email}\nPassword:\n{self.installer_password}\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / 'state/admin-password').read_text(), self.saved_password)
        self.assertFalse((self.root / 'removed').exists())

    def test_missing_installer_and_host_credentials_fails_without_api_calls(self):
        result = self.run_setup({})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.api_calls(), [])
        self.assertFalse((self.root / 'removed').exists())


if __name__ == '__main__':
    unittest.main()
