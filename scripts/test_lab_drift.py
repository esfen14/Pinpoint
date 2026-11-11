"""Offline checks for scripts/lab_drift.py; no installer clone or network is used."""
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('lab_drift', Path(__file__).with_name('lab_drift.py'))
lab_drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab_drift)

NAGIOS_SHA = 'a' * 64
PLUGINS_SHA = 'b' * 64
NCPA_SHA = 'c' * 64

DOCKERFILE = '''# comment
FROM ubuntu:22.04
ARG NAGIOS_VERSION=4.5.11
ARG NAGIOS_SHA256=%s
ARG PLUGINS_VERSION=2.4.12
ARG PLUGINS_SHA256=%s
ARG NCPA_SHA256=%s
ARG PYTHON_VERSION=3.14
RUN wget -q https://assets.nagios.com/downloads/nagioscore/releases/nagios-${NAGIOS_VERSION}.tar.gz \\
 && wget -q https://nagios-plugins.org/download/nagios-plugins-${PLUGINS_VERSION}.tar.gz \\
 && wget -q https://assets.nagios.com/downloads/ncpa/check_ncpa.tar.gz
RUN uv pip install -r /tmp/requirements.txt "gunicorn>=25.1"
''' % (NAGIOS_SHA, PLUGINS_SHA, NCPA_SHA)


def manifest_body():
    return {
        'manifest_id': 'pp-mon-baseline-1',
        'platform': {'os': 'ubuntu', 'version': '22.04', 'arch': 'x86_64'},
        'components': {
            'nagios-core': {'version': '4.5.11', 'artifact': {
                'url': 'https://assets.nagios.com/downloads/nagioscore/releases/nagios-4.5.11.tar.gz',
                'sha256': NAGIOS_SHA}},
            'nagios-plugins': {'version': '2.4.12', 'artifact': {
                'url': 'https://nagios-plugins.org/download/nagios-plugins-2.4.12.tar.gz',
                'sha256': PLUGINS_SHA}},
            'check-ncpa': {'version': '1.2.4', 'artifact': {
                'url': 'https://assets.nagios.com/downloads/ncpa/check_ncpa.tar.gz',
                'sha256': NCPA_SHA}},
        },
    }


DEPLOY = 'PYTHON_VERSION="3.14"\nGUNICORN_REQUIREMENT="gunicorn>=25.1"\n'


class DriftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.installer = self.base / 'installer'
        (self.installer / 'setup' / 'manifests').mkdir(parents=True)
        self.write_manifest(1, manifest_body())
        (self.installer / 'setup' / 'deploy-pinpoint-web.sh').write_text(DEPLOY)
        self.dockerfile = self.base / 'Dockerfile'
        self.dockerfile.write_text(DOCKERFILE)

    def write_manifest(self, number, body):
        path = self.installer / 'setup' / 'manifests' / ('pp-mon-baseline-%d.json' % number)
        path.write_text(json.dumps(body))

    def run_main(self):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = lab_drift.main(['--dockerfile', str(self.dockerfile),
                                   '--installer-dir', str(self.installer)])
        return code, out.getvalue() + err.getvalue()

    def differences(self):
        lab = lab_drift.dockerfile_pins(self.dockerfile.read_text())
        installer = lab_drift.installer_pins(self.installer)
        return lab_drift.compare(lab, installer)

    def test_dockerfile_pins_are_read_with_arguments_substituted(self):
        pins = lab_drift.dockerfile_pins(DOCKERFILE)
        self.assertEqual(pins['ubuntu'], '22.04')
        self.assertEqual(pins['nagios_version'], '4.5.11')
        self.assertEqual(pins['nagios_sha256'], NAGIOS_SHA)
        self.assertEqual(pins['nagios_url'],
                         'https://assets.nagios.com/downloads/nagioscore/releases/nagios-4.5.11.tar.gz')
        self.assertEqual(pins['plugins_version'], '2.4.12')
        self.assertEqual(pins['plugins_url'],
                         'https://nagios-plugins.org/download/nagios-plugins-2.4.12.tar.gz')
        self.assertEqual(pins['ncpa_sha256'], NCPA_SHA)
        self.assertEqual(pins['python_version'], '3.14')
        self.assertEqual(pins['gunicorn'], 'gunicorn>=25.1')

    def test_matching_sides_have_no_difference(self):
        self.assertEqual(self.differences(), [])
        code, output = self.run_main()
        self.assertEqual(code, 0, output)
        self.assertIn('pp-mon-baseline-1', output)

    def test_both_sides_expose_the_same_pin_names(self):
        lab = lab_drift.dockerfile_pins(DOCKERFILE)
        installer = lab_drift.installer_pins(self.installer)
        self.assertEqual(sorted(lab), sorted(installer))
        self.assertEqual(sorted(lab), sorted(lab_drift.PIN_NAMES))

    def test_changed_installer_version_is_reported_and_exits_one(self):
        body = manifest_body()
        body['components']['nagios-core']['version'] = '4.5.12'
        body['components']['nagios-core']['artifact']['url'] = (
            'https://assets.nagios.com/downloads/nagioscore/releases/nagios-4.5.12.tar.gz')
        self.write_manifest(1, body)
        names = []
        for name, _lab_value, _installer_value in self.differences():
            names.append(name)
        self.assertEqual(names, ['nagios_version', 'nagios_url'])
        code, output = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('4.5.11', output)
        self.assertIn('4.5.12', output)

    def test_changed_digest_python_gunicorn_and_platform_are_reported(self):
        body = manifest_body()
        body['components']['check-ncpa']['artifact']['sha256'] = 'd' * 64
        body['platform']['version'] = '24.04'
        self.write_manifest(1, body)
        (self.installer / 'setup' / 'deploy-pinpoint-web.sh').write_text(
            'PYTHON_VERSION="3.15"\nGUNICORN_REQUIREMENT="gunicorn>=26"\n')
        names = []
        for name, _lab_value, _installer_value in self.differences():
            names.append(name)
        self.assertEqual(names, ['ubuntu', 'ncpa_sha256', 'python_version', 'gunicorn'])

    def test_pin_missing_from_the_dockerfile_is_a_difference(self):
        self.dockerfile.write_text(DOCKERFILE.replace('ARG PYTHON_VERSION=3.14\n', ''))
        self.assertEqual(self.differences(), [('python_version', None, '3.14')])
        code, output = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('not found', output)

    def test_newest_baseline_manifest_is_used(self):
        body = manifest_body()
        body['manifest_id'] = 'pp-mon-baseline-10'
        body['components']['nagios-plugins']['version'] = '2.5.0'
        self.write_manifest(10, body)
        self.write_manifest(2, manifest_body())
        self.assertEqual(lab_drift.baseline_manifest(self.installer).name, 'pp-mon-baseline-10.json')
        code, output = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('pp-mon-baseline-10', output)

    def test_unreadable_installer_exits_two(self):
        empty = self.base / 'empty'
        empty.mkdir()
        self.installer = empty
        code, output = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn('manifest', output)

    def test_invalid_manifest_exits_two(self):
        (self.installer / 'setup' / 'manifests' / 'pp-mon-baseline-1.json').write_text('{not json')
        code, _output = self.run_main()
        self.assertEqual(code, 2)

    def test_real_dockerfile_yields_every_pin(self):
        text = (ROOT / 'lab' / 'appliance' / 'Dockerfile').read_text()
        pins = lab_drift.dockerfile_pins(text)
        for name in lab_drift.PIN_NAMES:
            self.assertTrue(pins[name], name)
            self.assertNotIn('$', pins[name], name)


if __name__ == '__main__':
    unittest.main()
