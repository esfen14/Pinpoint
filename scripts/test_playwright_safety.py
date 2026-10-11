"""Offline regression checks for credential-safe browser scaffolding."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent


class BrowserSafety(unittest.TestCase):
    def test_dependency_is_exact(self):
        package = json.loads((ROOT / 'client/package.json').read_text())
        lock = json.loads((ROOT / 'client/package-lock.json').read_text())
        pin = package['devDependencies']['@playwright/test']
        self.assertRegex(pin, r'^\d+\.\d+\.\d+$')
        self.assertEqual(pin, lock['packages']['']['devDependencies']['@playwright/test'])

    def test_auth_has_no_fallback_credentials(self):
        source = ''.join(
            (ROOT / name).read_text()
            for name in ('client/e2e/auth.setup.ts', 'client/e2e/auth.restricted.setup.ts')
        )
        self.assertNotIn("|| 'pinpoint'", source)
        self.assertNotIn("|| 'admin@pinpoint.lan'", source)
        self.assertIn('throw new Error', source)

    def test_projects_separate_roles(self):
        result = subprocess.run(
            ['./node_modules/.bin/playwright', 'test', '--list', '--reporter=json'],
            cwd=ROOT / 'client', capture_output=True, text=True, check=True,
        )
        report = json.loads(result.stdout)
        projects = {project['name']: project for project in report['config']['filteredProjects']}
        self.assertEqual(projects['admin']['dependencies'], ['setup-admin'])
        self.assertEqual(projects['restricted']['dependencies'], ['setup-restricted'])
        self.assertNotEqual(
            projects['admin']['use']['storageState'],
            projects['restricted']['use']['storageState'],
        )

        assigned = {}

        def visit(suites):
            for suite in suites:
                for spec in suite.get('specs', []):
                    assigned.setdefault(spec['file'], set()).update(
                        test['projectName'] for test in spec['tests']
                    )
                visit(suite.get('suites', []))

        visit(report['suites'])
        self.assertEqual(assigned['auth.setup.ts'], {'setup-admin'})
        self.assertEqual(assigned['auth.restricted.setup.ts'], {'setup-restricted'})
        self.assertEqual(assigned['smoke.admin.spec.ts'], {'admin'})
        self.assertEqual(assigned['smoke.restricted.spec.ts'], {'restricted'})

    def test_restricted_setup_handles_forced_change(self):
        source = (ROOT / 'client/e2e/auth.restricted.setup.ts').read_text()
        self.assertIn('PINPOINT_RESTRICTED_NEW_PASSWORD', source)
        self.assertIn("getByRole('heading', { name: 'Change your password' })", source)
        self.assertIn("getByRole('button', { name: 'Change password' })", source)

    def test_vmlab_provisions_restricted_credentials_privately(self):
        command = (ROOT / 'scripts/vmlab').read_text()
        helper = (ROOT / 'lab/setup_restricted.py').read_text()
        self.assertIn('setup-restricted', command)
        self.assertIn('restricted-password', command)
        self.assertIn('restricted-new-password', command)
        self.assertNotIn('print(password', helper)
        self.assertIn('require_password_change', helper)
        self.assertIn('receive_email_alerts', helper)
        self.assertIn('/api/user/roles/options', helper)
        self.assertIn('/api/user/accounts', helper)

    def test_live_runner_uses_network_namespace_and_private_state(self):
        source = (ROOT / 'scripts/playwright-lab').read_text()
        self.assertIn('--network none', source)
        self.assertIn('restricted-new-password', source)
        self.assertIn('PINPOINT_ADMIN_PASSWORD', source)
        self.assertIn('trap cleanup EXIT', source)

    def test_sensitive_outputs_ignored(self):
        for name in ('client/.auth/admin.json', 'client/test-results/trace.zip',
                     'client/playwright-report/index.html', 'client/blob-report/report.zip'):
            with self.subTest(name=name):
                result = subprocess.run(['git', 'check-ignore', '--quiet', name], cwd=ROOT)
                self.assertEqual(result.returncode, 0)

    def test_login_capture_disabled(self):
        config = (ROOT / 'client/playwright.config.ts').read_text()
        self.assertIn("trace: 'off'", config)
        self.assertIn("screenshot: 'off'", config)
        self.assertIn("video: 'off'", config)


if __name__ == '__main__':
    unittest.main()
