"""Offline fresh-VM provisioning contracts; no VirtualBox or SSH operations."""
import json
import io
from contextlib import redirect_stderr, nullcontext
from unittest.mock import patch
from pathlib import Path
import sys
import unittest
import tempfile
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.provision import install_commands, autoinstall_template, postinstall_template, ssh_arguments, creation_commands, prepare, validate_iso_detection
from defense import bootstrap, controller

UUID='351eb491-f5e1-4854-a7e4-68309ad774ad'


class ProvisionTests(unittest.TestCase):
    def test_password_and_private_host_key_use_files_never_command_arguments(self):
        root=Path('/private/defense')
        commands=install_commands(UUID,root,Path('/media/ubuntu.iso'))
        text=json.dumps(commands)
        self.assertNotIn('--user-password=',text)
        self.assertNotIn('--post-install-command=',text)
        self.assertIn('--user-password-file=/private/defense/login-password',text)
        self.assertIn('--post-install-template=/private/defense/postinstall.sh',text)
        self.assertNotIn('startvm',text)
        for bad in ['foreign;sh','../../other']:
            with self.assertRaises(ValueError):install_commands(bad,root,Path('/media/ubuntu.iso'))

    def test_recognized_ubuntu_detection_accepts_only_documented_not_implemented_result(self):
        report='OS TypeId = Ubuntu24_64\nOS Version = 24.04.5 LTS\nOS Flavor = Ubuntu-Server\nUnattended installation supported = yes\n'
        validate_iso_detection(0,report,'')
        validate_iso_detection(1,report,'VBoxManage: error: Code NS_ERROR_NOT_IMPLEMENTED (0x80004001) - Not implemented (extended info not available)\nVBoxManage: error: Context: "DetectIsoOS()" at line 2235 of file VBoxManageMisc.cpp\n')
        for code,out,error in [(1,report,'permission denied'),(1,report,'Failed to open'),(0,report.replace('yes','no'),''),(0,'OS TypeId = Windows10_64','')]:
            with self.assertRaises(ValueError):validate_iso_detection(code,out,error)

    def test_installer_numbers_only_the_nat_interface(self):
        text=autoinstall_template('02:77:01:ff:01:01','02:77:01:ff:01:02')
        self.assertIn('macaddress: "02:77:01:ff:01:02"',text)
        self.assertIn('dhcp4: false',text)
        self.assertIn('link-local: []',text)
        self.assertIn('install-server: true',text)
        self.assertIn('@@VBOX_INSERT_USER_PASSWORD_SHACRYPT512@@',text)
        self.assertNotIn('NOPASSWD:ALL',text)
        with self.assertRaises(ValueError):autoinstall_template('same','same')

    def test_private_postinstall_passes_payload_on_stdin_without_shell_interpolation(self):
        payload={'private_host_key':'PRIVATE_SENTINEL\n$() `x`\n','owner':'b'*48}
        text=postinstall_template(payload)
        self.assertIn("python3 /root/pinpoint-defense-bootstrap.py <<'PINPOINT_PRIVATE_INPUT'",text)
        self.assertNotIn('set -x',text)
        self.assertIn(json.dumps(payload,separators=(',',':')),text)

    def test_creation_preserves_old_vms_and_has_only_exact_loopback_management(self):
        commands=creation_commands(UUID,'b'*48,Path('/private/defense'),['02:77:01:ff:01:01','02:77:01:ff:01:02'])
        verbs=[c[1] for c in commands]
        self.assertNotIn('startvm',verbs)
        self.assertNotIn('unregistervm',verbs)
        self.assertNotIn('clonevm',verbs)
        settings=next(c for c in commands if c[1]=='modifyvm')
        self.assertIn('management,tcp,127.0.0.1,2260,,22',settings)
        self.assertIn('allow-vms',settings)
        self.assertNotIn('bridged',settings)
        self.assertEqual(settings[2],UUID)

    def test_bootstrap_context_refusal_precedes_package_or_filesystem_mutation(self):
        with patch('sys.stdin',io.StringIO('{}')),patch('defense.bootstrap.validate_payload',side_effect=ValueError('PRIVATE_SENTINEL')),patch('defense.bootstrap.run') as run,patch('defense.bootstrap.write') as write,redirect_stderr(io.StringIO()) as error:
            self.assertEqual(bootstrap.main(),1)
            run.assert_not_called();write.assert_not_called()
            self.assertNotIn('PRIVATE_SENTINEL',error.getvalue())

    def test_preview_observes_gates_without_creating_state_or_running_mutations(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);iso=root/'ubuntu.iso';iso.write_text('fixture')
            original_read=Path.read_text
            def read(path,*args,**kwargs):
                return 'MemAvailable: 16000000 kB\n' if str(path)=='/proc/meminfo' else original_read(path,*args,**kwargs)
            observer=SimpleNamespace(vbox=lambda *args:'Ubuntu_64' if args[0]=='unattended' else '')
            with patch.object(controller,'STATE_ROOT',root/'controller'),patch.object(controller,'Collector',return_value=observer),patch.object(controller,'network_inventory',return_value=[]),patch.object(controller,'allocated_mib',return_value=0),patch.object(controller.qa_control,'claim',side_effect=lambda:nullcontext()),patch.object(controller.vmlab_preflight,'inventory',return_value=([42],{})),patch.object(controller.vmlab_preflight,'tcp_listeners',return_value={}),patch('defense.provision.detect_ubuntu'),patch('shutil.disk_usage',return_value=SimpleNamespace(free=100*1024**3)),patch.object(Path,'read_text',read),patch('subprocess.run') as run:
                result=prepare(iso)
                self.assertFalse(result['applied']);self.assertFalse(result['booted'])
                run.assert_not_called()
                self.assertFalse((root/'controller').exists())
                with patch.object(controller.vmlab_preflight,'tcp_listeners',return_value={2260:[('127.0.0.1',1)]}):
                    with self.assertRaises(ValueError):prepare(iso,apply=True)
                run.assert_not_called()
                self.assertFalse((root/'controller').exists())

    def test_ssh_requires_injected_host_key_and_exact_loopback_endpoint(self):
        args=ssh_arguments(Path('/private/defense'))
        text=' '.join(args)
        self.assertIn('StrictHostKeyChecking=yes',text)
        self.assertIn('UserKnownHostsFile=/private/defense/known_hosts',text)
        self.assertIn('HostKeyAlgorithms=ssh-ed25519',text)
        self.assertNotIn('accept-new',text)
        self.assertEqual(args[-1],'defense@127.0.0.1')
        self.assertIn('2260',args)


if __name__=='__main__':unittest.main()
