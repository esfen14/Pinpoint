"""Offline tests for demo/demo qa: config, plan and destroy safety; vmlab and VBoxManage are never run."""
from pathlib import Path
import io
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qa_vm


class ConfigTests(unittest.TestCase):
    def test_config_isolates_the_qa_vm_on_the_demo_network_without_secrets(self):
        text=qa_vm.config_text(['10.77.1.2','10.77.1.3'])
        self.assertIn('VMLAB_VM="qa-pinpoint-appliance"',text)
        self.assertIn('VMLAB_LAB_HOSTONLY="vboxnet1"',text)
        self.assertIn('VMLAB_LAB_ADDRESS="10.77.1.1/27"',text)
        self.assertIn('VMLAB_LAB_NETWORK="10.77.1.0/27"',text)
        self.assertIn('VMLAB_TARGET_IPS="10.77.1.2,10.77.1.3"',text)
        self.assertNotIn('PASSWORD="',text.replace('VMLAB_ADMIN_PASSWORD=""',''))
    def test_target_ips_come_from_the_linux_catalog(self):
        ips=qa_vm.target_ips()
        self.assertEqual(len(ips),14);self.assertIn('10.77.1.2',ips)


class PlanTests(unittest.TestCase):
    def run_main(self,argv,answer='',exists=False):
        calls=[]
        def runner(argv_,env=None):
            calls.append((argv_,env));return 0
        out=io.StringIO();err=io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            code=qa_vm.main(argv,runner=runner,ask=lambda p:answer,vm_exists=lambda name:exists,state_dir=Path(tmp),out=out,err=err)
        return code,calls,out.getvalue()
    def test_create_without_apply_prints_the_plan_and_runs_nothing(self):
        code,calls,out=self.run_main(['create'])
        self.assertEqual((code,calls),(0,[]))
        for word in ('iso','create','provision','fresh'):self.assertIn(word,out)
    def test_create_apply_runs_vmlab_steps_in_order_with_the_qa_config(self):
        code,calls,_=self.run_main(['create','--apply'])
        self.assertEqual(code,0)
        steps=[c[0][-1] if c[0][-1] in {'iso','create','provision','fresh'} else c[0][1:] for c in calls]
        self.assertEqual([c[0][1] for c in calls],['iso','create','provision','fresh'])
        for argv,env in calls:
            self.assertTrue(argv[0].endswith('scripts/vmlab'))
            self.assertTrue(env['VMLAB_CONFIG'].endswith('vmlab.env'));self.assertIn('VMLAB_STATE_DIR',env)
    def test_create_refuses_when_the_qa_vm_already_exists(self):
        code,calls,_=self.run_main(['create','--apply'],exists=True)
        self.assertEqual((code,calls),(1,[]))
    def test_reset_reverts_then_installs_a_fresh_build(self):
        code,calls,_=self.run_main(['reset'],exists=True)
        self.assertEqual((code,[c[0][1] for c in calls]),(0,['fresh']))
    def test_unknown_commands_fail(self):
        self.assertEqual(self.run_main(['wipe'])[0],2)


class DestroyTests(unittest.TestCase):
    def run_destroy(self,argv,answer,exists=True):
        calls=[]
        def runner(argv_,env=None):
            calls.append(argv_);return 0
        out=io.StringIO();err=io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            code=qa_vm.main(argv,runner=runner,ask=lambda p:answer,vm_exists=lambda name:exists,state_dir=Path(tmp),out=out,err=err)
        return code,calls,out.getvalue()
    def test_destroy_without_apply_only_lists(self):
        code,calls,out=self.run_destroy(['destroy'],'destroy')
        self.assertEqual((code,calls),(0,[]));self.assertIn('qa-pinpoint-appliance',out)
    def test_destroy_apply_needs_the_typed_word(self):
        self.assertEqual(self.run_destroy(['destroy','--apply'],'yes')[:2],(1,[]))
    def test_destroy_apply_removes_only_the_qa_vm(self):
        code,calls,_=self.run_destroy(['destroy','--apply'],'destroy')
        self.assertEqual(code,0)
        self.assertIn(['VBoxManage','controlvm','qa-pinpoint-appliance','poweroff'],calls)
        self.assertIn(['VBoxManage','unregistervm','qa-pinpoint-appliance','--delete'],calls)
        for argv in calls:
            self.assertNotIn('Pinpoint-Final',argv);self.assertNotIn('pinpoint-defense-win01',argv)
    def test_destroy_of_a_missing_vm_is_a_no_op(self):
        code,calls,_=self.run_destroy(['destroy','--apply'],'destroy',exists=False)
        self.assertEqual((code,calls),(0,[]))
if __name__=='__main__':unittest.main()
