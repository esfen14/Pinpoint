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
        source = (ROOT / 'client/e2e/auth.setup.ts').read_text()
        self.assertNotIn("|| 'pinpoint'", source)
        self.assertNotIn("|| 'admin@pinpoint.lan'", source)
        self.assertIn('throw new Error', source)

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
