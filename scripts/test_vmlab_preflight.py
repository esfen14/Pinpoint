"""Isolated VM ownership checks; no VirtualBox or guest is invoked."""
import importlib.util
from pathlib import Path
import unittest
import os
import subprocess
import tempfile
import shlex
import sys
from unittest.mock import patch
from datetime import datetime, timezone
from contextlib import redirect_stdout, redirect_stderr
import io
import json

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).with_name('vmlab_preflight.py'))
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class OwnershipTests(unittest.TestCase):
    def check(self, state='running', managers=(10,), processes=None, listeners=None, session='20', forwards=None):
        if processes is None:
            processes = {20: {'uuid': 'vm-id', 'parent': 10}}
        if listeners is None:
            listeners = {2250: [('127.0.0.1', 'ssh')], 18080: [('127.0.0.1', 'web')]}
        if forwards is None:
            forwards = {2250: [('127.0.0.1', 22, '10.0.2.15')], 18080: [('127.0.0.1', 80, '10.0.2.15')]}
        return preflight.validate({'UUID': 'vm-id', 'VMState': state, 'SessionPID': session},
                                  list(managers), processes, listeners, [2250, 18080], forwards)

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
            self.check(processes={20: {'uuid': 'vm-id', 'parent': 10},
                                  21: {'uuid': 'vm-id', 'parent': 10}})

    def test_version_without_session_pid_uses_unique_controlled_process(self):
        self.check(session='')

    def test_wrong_session_pid(self):
        with self.assertRaises(ValueError):
            self.check(session='21')

    def test_wrong_controller(self):
        with self.assertRaises(ValueError):
            self.check(processes={20: {'uuid': 'vm-id', 'parent': 11}})

    def test_missing_runtime_forward_is_ambiguous(self):
        with self.assertRaises(ValueError):
            self.check(forwards={})

    def test_wrong_guest_service_or_address_is_ambiguous(self):
        for rows in [[('127.0.0.1', 23, '10.0.2.15')], [('0.0.0.0', 22, '10.0.2.15')]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.check(forwards={2250: rows, 18080: [('127.0.0.1', 80, '10.0.2.15')]})

    def test_runtime_duplicate_forward_or_mixed_guest_is_ambiguous(self):
        for rows in [[('127.0.0.1', 22, '10.0.2.15')] * 2, [('127.0.0.1', 22, '10.0.2.16')]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.check(forwards={2250: rows, 18080: [('127.0.0.1', 80, '10.0.2.15')]})

    def test_running_vm_without_a_process_is_ambiguous(self):
        with self.assertRaises(ValueError):
            self.check(processes={})

    def test_runtime_nat_parser_ignores_connections_and_requires_real_forwards(self):
        data = '''TCP[SYN_SENT] 23 127.0.0.1 2250 10.0.2.15 22 0 0
  TCP[HOST_FORWARD] 18 127.0.0.1 2250 10.0.2.15 22 0 0
  TCP[HOST_FORWARD] 19 127.0.0.1 18080 10.0.2.15 80 0 0'''
        self.assertEqual(preflight.nat_forwards(data), {2250: [('127.0.0.1', 22, '10.0.2.15')],
                                                     18080: [('127.0.0.1', 80, '10.0.2.15')]})

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

    def test_changed_ownership_blocks_ssh_and_bootstrap_fallback(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            log = path / 'calls'
            python = path / 'python3'
            python.write_text('#!/bin/sh\ncase "$2" in */qa_control.py) exec '
                              + shlex.quote(sys.executable) + ' "$@" ;; esac\necho python3 >> "$GATE_LOG"\n'
                              'if [ "$(wc -l < "$GATE_LOG")" -eq 1 ]; then exit 0; fi\nexit 1\n')
            python.chmod(0o700)
            for command in ['VBoxManage', 'ssh', 'tar']:
                executable = path / command
                executable.write_text('#!/bin/sh\necho "' + command + '" >> "$GATE_LOG"\nexit 1\n')
                executable.chmod(0o700)
            config = path / 'config'
            config.write_text('')
            env = dict(os.environ, PATH=str(path) + ':' + os.environ['PATH'],
                       VMLAB_CONFIG=str(config), VMLAB_STATE_DIR=str(path / 'state'), GATE_LOG=str(log))
            for command, expected in [('sync', 2), ('prepare', 3)]:
                with self.subTest(command=command):
                    log.write_text('')
                    result = subprocess.run(['bash', str(root / 'scripts/vmlab'), command],
                                            env=env, capture_output=True, text=True, timeout=5)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(log.read_text().splitlines(), ['python3'] * expected)


class ObservationTests(unittest.TestCase):
    UUID = '12345678-1234-1234-1234-123456789abc'

    def observe(self, *, changed=False, state='running'):
        info = f'UUID="{self.UUID}"\nVMState="{state}"\nSessionPID="20"\n'
        nat = ('TCP[HOST_FORWARD] 18 127.0.0.1 2250 10.0.2.15 22 0 0\n'
               'TCP[HOST_FORWARD] 19 127.0.0.1 18080 10.0.2.15 80 0 0')
        outputs = [info, nat, info.replace('SessionPID="20"', 'SessionPID="21"') if changed else info]
        if state == 'poweroff':
            outputs = [info, info]
        processes = {20: {'uuid': self.UUID, 'parent': 10, 'start_ticks': 200, 'controller_start_ticks': 100}}
        listeners = {2250: [('127.0.0.1', 'ssh')], 18080: [('127.0.0.1', 'web')]}
        if state == 'poweroff':
            processes, listeners = {}, {}
        with patch.object(preflight, 'inventory', return_value=([10], processes)), \
                patch.object(preflight, 'tcp_listeners', return_value=listeners), \
                patch.object(preflight, 'subprocess') as commands:
            commands.run.side_effect = [subprocess.CompletedProcess([], 0, stdout=o) for o in outputs]
            receipt = preflight.observe('fixture', 'lab@127.0.0.1', [2250, 18080])
            self.assertTrue(all(call.kwargs['timeout'] == 20 for call in commands.run.call_args_list))
            self.assertTrue(all(not call.kwargs.get('shell') for call in commands.run.call_args_list))
            return receipt

    def test_structured_host_observation_does_not_claim_runtime_readiness(self):
        receipt = self.observe()
        self.assertEqual(receipt['lab_uuid'], self.UUID)
        self.assertEqual(receipt['origin'], 'http://127.0.0.1:18080')
        self.assertTrue(receipt['host_ownership_verified'])
        self.assertFalse(receipt['live_authorized'])
        self.assertNotIn('runtime_identity_verified', receipt)
        self.assertNotIn('target_revision', receipt)
        self.assertEqual(receipt['controller_pid'], 10)
        self.assertEqual(receipt['vm_pid'], 20)
        self.assertEqual(receipt['vm_start_ticks'], 200)
        self.assertEqual(receipt['controller_start_ticks'], 100)
        self.assertLess(abs((datetime.now(timezone.utc) - datetime.fromisoformat(receipt['observed_at'])).total_seconds()), 2)

    def test_changed_session_is_rejected(self):
        with self.assertRaises(ValueError):
            self.observe(changed=True)

    def test_poweroff_observation_has_no_running_endpoint_claim(self):
        receipt = self.observe(state='poweroff')
        self.assertIsNone(receipt['vm_pid'])
        self.assertFalse(receipt['running_endpoints_verified'])

    def test_invalid_identity_or_endpoint_rejects_before_commands(self):
        with patch.object(preflight, 'subprocess') as commands:
            for target, ports in [('lab@remote', [2250, 18080]), ('lab@127.0.0.1', [2250, 2250])]:
                with self.assertRaises(ValueError):
                    preflight.observe('fixture', target, ports)
            commands.run.assert_not_called()

    def test_changed_process_identity_is_rejected(self):
        with patch.object(preflight, 'vm_info', return_value={'UUID': self.UUID, 'VMState': 'poweroff'}), \
                patch.object(preflight, 'inventory', side_effect=[([10], {}), ([10], {}), ([11], {})]):
            with self.assertRaises(ValueError):
                preflight.observe('fixture', 'lab@127.0.0.1', [2250, 18080])

    def test_json_entry_returns_only_receipt_and_sanitizes_failure(self):
        args = ['preflight', '--json', 'fixture', 'lab@127.0.0.1', '2250', '18080']
        receipt = self.observe()
        output = io.StringIO()
        with patch.object(sys, 'argv', args), patch.object(preflight, 'observe', return_value=receipt), redirect_stdout(output):
            self.assertEqual(preflight.main(), 0)
        self.assertEqual(json.loads(output.getvalue()), receipt)
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', args), patch.object(preflight, 'observe', side_effect=ValueError('private-fixture')), \
                redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(preflight.main(), 1)
        self.assertEqual(output.getvalue(), '')
        self.assertNotIn('private-fixture', errors.getvalue())

    def test_kernel_start_ticks_parse_and_missing_identity_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'stat').write_text('20 (fixture ) name) ' + ' '.join(['S'] + ['0'] * 18 + ['123']))
            self.assertEqual(preflight.process_start(root), 123)
            for text in ['malformed', '20 (fixture) ' + ' '.join(['S'] + ['0'] * 19)]:
                (root / 'stat').write_text(text)
                with self.assertRaises(ValueError):
                    preflight.process_start(root)


if __name__ == '__main__':
    unittest.main()
