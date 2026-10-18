"""Local lock/fixture processes only; never contact VirtualBox or an appliance."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('control', Path(__file__).with_name('qa_control.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ControlTests(unittest.TestCase):
    def test_competing_handles_and_subprocess_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with c.claim(root=root):
                with self.assertRaises(ValueError):
                    with c.claim(root=root):
                        self.fail('Competing owner entered')
                code = ('import importlib.util; from pathlib import Path; '
                        's=importlib.util.spec_from_file_location("c",' + repr(str(Path(c.__file__))) + '); '
                        'c=importlib.util.module_from_spec(s); s.loader.exec_module(c); '
                        'c.claim(root=Path(' + repr(directory) + ')).__enter__()')
                result = subprocess.run([sys.executable, '-I', '-c', code], capture_output=True, timeout=5)
                self.assertNotEqual(result.returncode, 0)
            with c.claim(root=root):
                pass

    def test_inherited_descriptor_keeps_parent_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with c.claim(root=root) as fd:
                with c.claim(root=root, inherited_fd=fd):
                    pass
                with self.assertRaises(ValueError):
                    with c.claim(root=root):
                        self.fail('Nested release unlocked the parent')

    def test_wrong_unheld_or_closed_descriptor_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other = root / 'other'
            other.write_text('')
            other.chmod(0o600)
            fd = os.open(other, os.O_RDWR)
            try:
                with self.assertRaises(ValueError):
                    with c.claim(root=root, inherited_fd=fd):
                        pass
            finally:
                os.close(fd)
            with self.assertRaises(ValueError):
                with c.claim(root=root, inherited_fd=fd):
                    pass
            # A descriptor to the canonical file is insufficient unless it owns the lock.
            fd = os.open(root / 'controller.lock', os.O_RDWR | os.O_CREAT, 0o600)
            try:
                with self.assertRaises(ValueError):
                    with c.claim(root=root, inherited_fd=fd):
                        pass
            finally:
                os.close(fd)

    def test_private_canonical_root_and_file_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / 'unsafe'
            unsafe.mkdir(mode=0o755)
            with self.assertRaises(ValueError):
                with c.claim(root=unsafe):
                    pass
            link = root / 'link'
            link.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                with c.claim(root=link):
                    pass
            (root / 'controller.lock').symlink_to(root / 'missing')
            with self.assertRaises(ValueError):
                with c.claim(root=root):
                    pass
            (root / 'controller.lock').unlink()
            original = root / 'original'
            original.write_text('')
            original.chmod(0o600)
            os.link(original, root / 'controller.lock')
            with self.assertRaises(ValueError):
                with c.claim(root=root):
                    pass

    def test_environment_cannot_relocate_canonical_store(self):
        expected = Path('/tmp') / f'pinpoint-qa-control-{os.getuid()}'
        with patch.dict(os.environ, HOME='/fake', TMPDIR='/fake', VMLAB_STATE_DIR='/fake'):
            self.assertEqual(c.canonical_root(), expected)

    def test_controller_entry_holds_and_verifies_lock_before_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / 'scripts'
            scripts.mkdir()
            control_root = root / 'control'
            # Fixture copy: no production path override or live controller is used.
            code = Path(c.__file__).read_text().replace(
                "return Path('/tmp') / f'pinpoint-qa-control-{os.getuid()}'",
                'return Path(' + repr(str(control_root)) + ')')
            (scripts / 'qa_control.py').write_text(code)
            (scripts / 'vmlab').write_text(Path(c.__file__).with_name('vmlab').read_text())
            config = root / 'config'
            config.write_text('echo configured >> "$FIXTURE_LOG"\n')
            (scripts / 'vmlab_preflight.py').write_text('raise SystemExit(1)\n')
            log = root / 'calls'
            env = dict(os.environ, VMLAB_CONFIG=str(config), FIXTURE_LOG=str(log))
            for key in (c.FD_ENV, c.PID_ENV):
                env.pop(key, None)
            command = ['/bin/bash', str(scripts / 'vmlab'), 'sync']
            with c.claim(root=control_root) as fd:
                blocked = subprocess.run(command, env=env, capture_output=True, timeout=5)
                self.assertNotEqual(blocked.returncode, 0)
                self.assertFalse(log.exists(), 'No configuration or preflight before exclusion')
                nested_env = dict(env, **{c.FD_ENV: str(fd)})
                nested = subprocess.run(command, env=nested_env, pass_fds=(fd,), capture_output=True, timeout=5)
                self.assertNotEqual(nested.returncode, 0)  # Stops at the fixture preflight.
                self.assertEqual(log.read_text().splitlines(), ['configured'])
                with self.assertRaises(ValueError):
                    with c.claim(root=control_root):
                        self.fail('Controller subprocess released parent claim')
            # A forged marker and a stale FD must not enter configuration either.
            log.unlink()
            forged = dict(env, **{c.FD_ENV: '9999'})
            forged_command = ['/bin/bash', '-c',
                              'export PINPOINT_QA_CONTROL_PID=$$; exec /bin/bash "$1" sync',
                              'fixture', str(scripts / 'vmlab')]
            result = subprocess.run(forged_command, env=forged, capture_output=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(log.exists())


if __name__ == '__main__':
    unittest.main()
