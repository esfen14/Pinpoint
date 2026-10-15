"""Isolated VM ownership checks; no VirtualBox or guest is invoked."""
import importlib.util
from pathlib import Path
import unittest
import os
import subprocess
import tempfile

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).with_name('vmlab_preflight.py'))
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class OwnershipTests(unittest.TestCase):
    def check(self, state='running', managers=(10,), processes=None, listeners=None, session='20'):
        if processes is None:
            processes = {20: {'uuid': 'vm-id', 'parent': 10, 'sockets': {'ssh', 'web'}}}
        if listeners is None:
            listeners = {2250: [('127.0.0.1', 'ssh')], 18080: [('127.0.0.1', 'web')]}
        return preflight.validate({'UUID': 'vm-id', 'VMState': state, 'SessionPID': session},
                                  list(managers), processes, listeners, [2250, 18080])

    def test_proven_running_owner(self):
        self.check()

    def test_duplicate_managers_even_when_offline(self):
        with self.assertRaisesRegex(ValueError, 'VBoxSVC'):
            self.check('poweroff', managers=(10, 11), processes={}, listeners={})

    def test_poweroff_with_inherited_endpoint(self):
        with self.assertRaises(ValueError):
            self.check('poweroff', processes={})

    def test_poweroff_with_inherited_process(self):
        with self.assertRaises(ValueError):
            self.check('poweroff', listeners={})

    def test_clean_poweroff(self):
        self.check('poweroff', processes={}, listeners={})

    def test_duplicate_uuid(self):
        with self.assertRaises(ValueError):
            self.check(processes={20: {'uuid': 'vm-id', 'parent': 10, 'sockets': {'ssh', 'web'}},
                                  21: {'uuid': 'vm-id', 'parent': 10, 'sockets': set()}})

    def test_missing_session_pid(self):
        with self.assertRaises(ValueError):
            self.check(session='')

    def test_wrong_session_pid(self):
        with self.assertRaises(ValueError):
            self.check(session='21')

    def test_wrong_controller(self):
        with self.assertRaises(ValueError):
            self.check(processes={20: {'uuid': 'vm-id', 'parent': 11, 'sockets': {'ssh', 'web'}}})

    def test_listener_owned_by_other_process(self):
        with self.assertRaises(ValueError):
            self.check(listeners={2250: [('127.0.0.1', 'foreign')], 18080: [('127.0.0.1', 'web')]})

    def test_missing_or_wildcard_or_duplicate_listener(self):
        for rows in [[], [('0.0.0.0', 'ssh')], [('127.0.0.1', 'ssh'), ('::', 'other')]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.check(listeners={2250: rows, 18080: [('127.0.0.1', 'web')]})

    def test_transitional_state_is_ambiguous(self):
        with self.assertRaises(ValueError):
            self.check('restoring')


class CommandGateTests(unittest.TestCase):
    def test_rejected_preflight_prevents_all_mutation_commands(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            log = path / 'calls'
            for command in ['python3', 'VBoxManage', 'ssh', 'curl', 'tar', 'npm', 'git']:
                executable = path / command
                executable.write_text('#!/bin/sh\necho "' + command + '" >> "$GATE_LOG"\nexit 1\n')
                executable.chmod(0o700)
            config = path / 'config'
            config.write_text('')
            env = dict(os.environ, PATH=str(path) + ':' + os.environ['PATH'],
                       VMLAB_CONFIG=str(config), VMLAB_STATE_DIR=str(path / 'state'), GATE_LOG=str(log))
            for command in ['create', 'prepare', 'provision', 'up', 'down', 'revert', 'fresh',
                            'sync', 'health', 'setup-admin', 'setup-restricted', 'smoke', 'ncpa', 'alerts', 'targets']:
                with self.subTest(command=command):
                    log.write_text('')
                    result = subprocess.run(['bash', str(root / 'scripts/vmlab'), command],
                                            env=env, capture_output=True, text=True, timeout=5)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(log.read_text().splitlines(), ['python3'])
                    self.assertFalse((path / 'state').exists())


if __name__ == '__main__':
    unittest.main()
