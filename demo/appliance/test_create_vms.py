"""Offline tests for the appliance and Windows VM creation commands; VBoxManage is never run."""
from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import create_vms


class CommandTests(unittest.TestCase):
    def test_appliance_has_nat_with_web_forward_and_the_host_only_demo_adapter(self):
        text=[' '.join(c) for c in create_vms.appliance_commands('Pinpoint-Final',Path('/vm/a.vdi'))]
        joined='\n'.join(text)
        self.assertIn('createvm --name Pinpoint-Final --ostype Ubuntu_64 --register',joined)
        self.assertIn('--nic1=nat',joined);self.assertIn('--nic2=hostonly',joined);self.assertIn('--host-only-adapter2=vboxnet1',joined)
        self.assertIn('--nat-pf1=web,tcp,127.0.0.1,18080,,80',joined)
        self.assertNotIn('bridged',joined);self.assertNotIn('intnet',joined)
    def test_windows_uses_only_the_host_only_adapter_with_the_catalog_mac(self):
        joined='\n'.join(' '.join(c) for c in create_vms.windows_commands('pinpoint-defense-win01',Path('/vm/w.vdi')))
        self.assertIn('--nic1=hostonly',joined);self.assertIn('--host-only-adapter1=vboxnet1',joined)
        self.assertIn('--mac-address1=027701000002',joined)
        self.assertIn('--memory 3072',joined);self.assertIn('--cpus 2',joined)
        self.assertNotIn('nat',joined.replace('unattended',''))
    def test_install_commands_take_secrets_from_files_never_arguments(self):
        cmds=create_vms.windows_install_command('pinpoint-defense-win01',Path('/iso/w.iso'),Path('/p/password'))
        self.assertIn('--user-password-file=/p/password',cmds)
        self.assertNotIn('--user-password',' '.join(a for a in cmds if not a.startswith('--user-password-file')))


class MainTests(unittest.TestCase):
    def run_main(self,argv,existing=()):
        calls=[]
        def runner(argv_):
            calls.append(argv_)
            if argv_[:2]==['VBoxManage','showvminfo'] and argv_[2] in existing:return 'x'
            if argv_[:2]==['VBoxManage','showvminfo']:raise ValueError('none')
            if argv_[:3]==['VBoxManage','list','systemproperties']:return 'Default machine folder: /vms\n'
            return ''
        out=io.StringIO()
        code=create_vms.main(argv,runner=runner,out=out,err=io.StringIO())
        return code,calls,out.getvalue()
    def test_without_apply_it_only_prints_the_plan(self):
        code,calls,out=self.run_main(['--windows-iso','/iso/w.iso'])
        self.assertEqual(code,0);self.assertIn('createvm',out)
        self.assertFalse([c for c in calls if c[1] in {'createvm','modifyvm','createmedium'}])
    def test_apply_skips_a_vm_that_already_exists(self):
        code,calls,_=self.run_main(['--apply'],existing=('Pinpoint-Final','pinpoint-defense-win01'))
        self.assertEqual(code,0)
        self.assertFalse([c for c in calls if c[1] in {'createvm','modifyvm','createmedium'}])
    def test_apply_creates_missing_vms(self):
        code,calls,_=self.run_main(['--apply'])
        self.assertEqual(code,0)
        self.assertEqual(len([c for c in calls if c[1]=='createvm']),2)
    def test_unknown_arguments_fail(self):
        self.assertEqual(self.run_main(['--wipe'])[0],2)
if __name__=='__main__':unittest.main()
