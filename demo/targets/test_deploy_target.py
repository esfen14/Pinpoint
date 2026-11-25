"""Offline tests for the NCPA deploy target's mirror and systemctl stand-in (#336)."""
import hashlib
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from targets import fetch_mirror, node, systemctl_shim
from targets.catalog import load_catalog

CATALOG = load_catalog()
TARGET = CATALOG.target('ssh-alt02')

OLD = b'old package'
NEW = b'new package'


def repository(new_data=NEW, filename='pool/main/ncpa-3.10.0-1.amd64.deb'):
    packages = ''
    for version, path, data in [('3.9.1-1', 'pool/main/ncpa-3.9.1-1_amd64.deb', OLD),
                                ('3.10.0-1', filename, NEW)]:
        packages += (f'Package: ncpa\nVersion: {version}\nArchitecture: amd64\nFilename: {path}\n'
                     f'SHA256: {hashlib.sha256(data).hexdigest()}\n\n')
    index = packages.encode()
    release = f'SHA256:\n {hashlib.sha256(index).hexdigest()} {len(index)} Packages\n {hashlib.sha256(b"gz").hexdigest()} 2 Packages.gz\n'
    base = 'https://repo.nagios.com/deb/noble/'
    return {'https://repo.nagios.com/GPG-KEY-NAGIOS-V3': b'key', base + 'InRelease': release.encode(),
            base + 'Release': release.encode(), base + 'Release.gpg': b'signature',
            base + 'Packages': index, base + 'Packages.gz': b'gz', base + filename: new_data}


class MirrorTests(unittest.TestCase):
    def test_copies_signed_files_unchanged_and_only_the_newest_package(self):
        files = repository()
        checked = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = fetch_mirror.mirror(root, 'noble', fetch=files.__getitem__,
                                          verify=lambda key, signed: checked.append(signed.name))
            self.assertEqual(version, '3.10.0-1')
            self.assertEqual(checked, ['InRelease'])
            for url, data in files.items():
                self.assertEqual((root / url.removeprefix('https://repo.nagios.com/')).read_bytes(), data)
            self.assertEqual(len(list(root.rglob('*.deb'))), 1)

    def test_refuses_a_changed_package_and_an_unexpected_path(self):
        for files in [repository(new_data=b'tampered'), repository(filename='../ncpa.deb')]:
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                fetch_mirror.mirror(Path(directory), 'noble', fetch=files.__getitem__, verify=lambda *a: None)

    def test_refuses_an_index_that_the_signed_release_does_not_match(self):
        files = repository()
        files['https://repo.nagios.com/deb/noble/Packages'] += b'\n'
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            fetch_mirror.mirror(Path(directory), 'noble', fetch=files.__getitem__, verify=lambda *a: None)


class ShimTests(unittest.TestCase):
    def call(self, *argv):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return systemctl_shim.main(list(argv))

    def test_package_script_verbs_succeed_without_doing_anything(self):
        with patch.object(systemctl_shim.subprocess, 'Popen') as popen:
            for argv in [('daemon-reload',), ('enable', 'ncpa'), ('disable', 'ncpa'),
                         ('list-units', '--full', '-all')]:
                self.assertEqual(self.call(*argv), 0)
            popen.assert_not_called()

    def test_only_the_ncpa_unit_is_managed(self):
        with patch.object(systemctl_shim.subprocess, 'Popen') as popen:
            self.assertEqual(self.call('restart', 'nginx'), 1)
            self.assertEqual(self.call('reboot'), 1)
            popen.assert_not_called()

    def test_status_reports_inactive_and_start_needs_the_package(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(systemctl_shim, 'PIDFILE', Path(directory) / 'pid'), \
             patch.object(systemctl_shim, 'PROGRAM', Path(directory) / 'ncpa'):
            self.assertEqual(self.call('status', 'ncpa', '--no-pager'), 3)
            self.assertEqual(self.call('start', 'ncpa'), 5)
            self.assertEqual(self.call('stop', 'ncpa'), 0)

    def test_a_saved_pid_of_another_program_is_not_treated_as_ncpa(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(systemctl_shim, 'PIDFILE', Path(directory) / 'pid'):
            systemctl_shim.PIDFILE.write_text('1')
            self.assertIsNone(systemctl_shim.running_pid())


class NodeTests(unittest.TestCase):
    def secret(self, directory, value):
        path = Path(directory) / 'deploy-password'
        path.write_text(value)
        path.chmod(0o600)
        return patch.object(node, 'DEPLOY_SECRET', path)

    def test_deploy_features_need_both_the_target_and_its_mounted_password(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(node, 'DEPLOY_SECRET', Path(directory) / 'absent'):
                self.assertFalse(node.deploy_enabled(TARGET))
                self.assertNotIn('mirror', node.program_specs(CATALOG, TARGET))
                self.assertIn('PasswordAuthentication no\n', node.sshd_config(TARGET, 2223))
            with self.secret(directory, 'a' * 24):
                self.assertTrue(node.deploy_enabled(TARGET))
                self.assertIn('mirror', node.program_specs(CATALOG, TARGET))
                for device in CATALOG.devices:
                    if device.kind != 'linux' or device.name == 'ssh-alt02':
                        continue
                    self.assertFalse(node.deploy_enabled(device), device.name)
                    self.assertNotIn('mirror', node.program_specs(CATALOG, device))

    def test_deploy_target_allows_passwords_and_sftp_but_never_root(self):
        with tempfile.TemporaryDirectory() as directory, self.secret(directory, 'a' * 24):
            text = node.sshd_config(TARGET, 2223)
        for line in ['Port 2223', 'PasswordAuthentication yes', 'UsePAM yes', 'PermitRootLogin no',
                     'Subsystem sftp internal-sftp']:
            self.assertIn(line + '\n', text)

    def test_password_is_set_through_standard_input_only(self):
        with tempfile.TemporaryDirectory() as directory, self.secret(directory, 'ab' * 12 + '\n'), \
             patch.object(node, 'command') as run:
            node.set_deploy_password()
        run.assert_called_once_with(['/usr/sbin/chpasswd'], input_text='labadmin:' + 'ab' * 12 + '\n')

    def test_a_malformed_password_file_changes_nothing(self):
        for value in ['', 'short', 'a' * 24 + '\nroot:x', 'A' * 24]:
            with tempfile.TemporaryDirectory() as directory, self.secret(directory, value), \
                 patch.object(node, 'command') as run:
                with self.assertRaises(ValueError):
                    node.set_deploy_password()
                run.assert_not_called()

    def test_mirror_serves_only_loopback(self):
        text = node.mirror_config()
        self.assertIn('listen 127.0.0.1:443 ssl;', text)
        self.assertEqual(text.count('listen '), 1)

    def test_loopback_mirror_socket_is_not_reported_as_a_device_listener(self):
        table = ('  sl  local_address rem_address   st\n'
                 '   0: 0100007F:01BB 00000000:0000 0A\n'
                 '   1: 00000000:08AF 00000000:0000 0A\n')
        def read(path, *args, **kwargs):
            return table if str(path) == '/proc/net/tcp' else 'header\n'
        with patch('pathlib.Path.exists', return_value=True), patch('pathlib.Path.read_text', read):
            self.assertEqual(node.listening_ports(hidden={('tcp', node.MIRROR_SOCKET)}),
                             [{'protocol': 'tcp', 'port': 2223}])
            self.assertEqual(len(node.listening_ports()), 2)

    def test_baseline_restarts_an_installed_agent(self):
        with tempfile.TemporaryDirectory() as directory, self.secret(directory, 'a' * 24), \
             patch.object(node, 'NCPA_PROGRAM', Path(directory) / 'ncpa'), \
             patch.object(node, 'command') as run:
            node.restart_agent(TARGET)
            run.assert_not_called()
            node.NCPA_PROGRAM.write_text('installed')
            node.restart_agent(TARGET)
            run.assert_called_once_with(['/usr/bin/systemctl', 'start', 'ncpa'], check=False)
            node.restart_agent(CATALOG.target('web03'))
            run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
