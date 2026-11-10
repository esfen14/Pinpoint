"""Offline tests for the appliance and Windows VM creation commands; VBoxManage is never run."""
from pathlib import Path
import io
import os
import sys
import tempfile
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
    def test_windows_install_uses_a_template_without_a_product_key(self):
        cmds=create_vms.windows_install_command('pinpoint-defense-win01',Path('/iso/w.iso'),Path('/p/password'),Path('/t/x.xml'))
        self.assertIn('--script-template=/t/x.xml',cmds)
        self.assertIn('--image-index=1',cmds)
        self.assertFalse([c for c in cmds if c.startswith('--key')])
    def test_template_loses_only_the_product_key_element(self):
        directory=Path(tempfile.mkdtemp())
        source=directory/'in.xml'
        source.write_text('<UserData>\n    <ProductKey>\n        <Key>@@K@@</Key>\n    </ProductKey>\n    <AcceptEula>true</AcceptEula>\n</UserData>\n')
        create_vms.write_keyless_template(source,directory/'out.xml')
        result=(directory/'out.xml').read_text()
        self.assertNotIn('ProductKey',result);self.assertIn('<AcceptEula>true</AcceptEula>',result)
    def test_template_without_a_product_key_element_is_an_error(self):
        directory=Path(tempfile.mkdtemp())
        (directory/'in.xml').write_text('<x/>')
        with self.assertRaises(ValueError):
            create_vms.write_keyless_template(directory/'in.xml',directory/'out.xml')
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
        code=create_vms.main(argv,runner=runner,out=out,err=io.StringIO(),template_writer=lambda:None)
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
    def run_download(self,argv,present=False):
        downloads=[]
        out=io.StringIO()
        err=io.StringIO()
        home=Path(tempfile.mkdtemp())
        old_default=create_vms.WINDOWS_ISO_DEFAULT
        old_appliance=create_vms.APPLIANCE_ISO_DEFAULT
        create_vms.WINDOWS_ISO_DEFAULT=home/'win.iso'
        create_vms.APPLIANCE_ISO_DEFAULT=home/'ubuntu.iso'
        if present:
            (home/'win.iso').write_text('x')
        def runner(argv_):
            if argv_[:2]==['VBoxManage','showvminfo']:raise ValueError('none')
            if argv_[:3]==['VBoxManage','list','systemproperties']:return 'Default machine folder: /vms\n'
            return ''
        def downloader(url,target):
            downloads.append((url,target))
        try:
            code=create_vms.main(argv,runner=runner,out=out,err=err,downloader=downloader,template_writer=lambda:None)
        finally:
            create_vms.WINDOWS_ISO_DEFAULT=old_default
            create_vms.APPLIANCE_ISO_DEFAULT=old_appliance
        return code,downloads,out.getvalue(),err.getvalue(),home
    def test_plan_names_the_download_but_does_not_fetch_it(self):
        code,downloads,out,_,home=self.run_download(['--download-windows-iso'])
        self.assertEqual(code,0);self.assertEqual(downloads,[])
        self.assertIn('will be downloaded from https://go.microsoft.com',out)
        self.assertIn('--iso='+str(home/'win.iso'),out)
    def test_apply_downloads_once_and_skips_a_present_file(self):
        code,downloads,_,_,home=self.run_download(['--apply','--download-windows-iso'])
        self.assertEqual(code,0);self.assertEqual(downloads,[(create_vms.WINDOWS_ISO_URL,home/'win.iso')])
        code,downloads,out,_,_=self.run_download(['--apply','--download-windows-iso'],present=True)
        self.assertEqual(downloads,[]);self.assertIn('already present',out)
    def test_a_given_path_and_the_download_option_conflict(self):
        code,downloads,_,err,_=self.run_download(['--windows-iso','/iso/w.iso','--download-windows-iso'])
        self.assertEqual(code,1);self.assertEqual(downloads,[]);self.assertIn('not both',err)
    def test_apply_rejects_a_missing_iso_path(self):
        code,_,_,err,_=self.run_download(['--apply','--windows-iso','/nonexistent/w.iso'])
        self.assertEqual(code,1);self.assertIn('not found',err)
    def test_appliance_download_uses_the_vmlab_iso_path(self):
        old=os.environ.get('VMLAB_ISO')
        os.environ['VMLAB_ISO']='/tmp/shared.iso'
        try:
            self.assertEqual(create_vms.appliance_iso_default(),Path('/tmp/shared.iso'))
        finally:
            if old is None:
                del os.environ['VMLAB_ISO']
            else:
                os.environ['VMLAB_ISO']=old
    def test_unknown_arguments_fail(self):
        self.assertEqual(self.run_main(['--wipe'])[0],2)
if __name__=='__main__':unittest.main()
