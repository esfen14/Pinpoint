"""Offline tests for the demo/demo front door; stubs replace every real controller."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

DEMO=Path(__file__).resolve().parents[1]
STUB='import sys,os\nopen(os.environ["STUB_LOG"],"a").write(os.path.basename(__file__)+" "+" ".join(sys.argv[1:])+"\\n")\n'


class FrontDoorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'targets').mkdir()
        for name in ('demo','Pinpoint-Demo-faults.sh'):
            shutil.copy2(DEMO/name,self.root/name)
        (self.root/'appliance').mkdir()
        (self.root/'appliance'/'create_vms.py').write_text(STUB)
        (self.root/'appliance'/'qa_vm.py').write_text(STUB)
        for name in ('presenter','controller','setup'):
            (self.root/'targets'/(name+'.py')).write_text(STUB)
        self.log=self.root/'log'
    def tearDown(self):self.tmp.cleanup()
    def run_demo(self,*args):
        if self.log.exists():self.log.unlink()
        env=dict(os.environ,STUB_LOG=str(self.log))
        result=subprocess.run([str(self.root/'demo'),*args],capture_output=True,text=True,env=env,timeout=20)
        calls=self.log.read_text().splitlines() if self.log.exists() else []
        return result,calls
    def test_lifecycle_and_read_only_commands_reach_the_right_program(self):
        cases={('setup',):['setup.py setup'],('qa','create','--apply'):['qa_vm.py create --apply'],('qa','destroy'):['qa_vm.py destroy'],('create-vms','--apply'):['create_vms.py --apply'],('setup','--apply'):['setup.py setup --apply'],
               ('destroy','--apply'):['setup.py destroy --apply'],
               ('up',):['setup.py up'],('down',):['presenter.py down'],
               ('manifest',):['controller.py manifest'],('preflight',):['controller.py preflight'],
               ('status',):['presenter.py status'],('reset',):['presenter.py reset'],
               ('down','web03','http'):['presenter.py break web03 http'],
               ('up','web03','http'):['presenter.py fix web03 http'],
               ('ports','open','web03','http','8088'):['presenter.py ports open web03 http 8088'],
               ('presenter','manifest'):['presenter.py manifest']}
        for args,expected in cases.items():
            with self.subTest(args=args):
                result,calls=self.run_demo(*args)
                self.assertEqual((result.returncode,calls),(0,expected))
    def test_front_door_keeps_the_fault_input_validation(self):
        for args in (('down','web01','http'),('ports','open','web03','http','80x'),('dhcp-move','web03','10.77.1.25')):
            with self.subTest(args=args):
                result,calls=self.run_demo(*args)
                self.assertNotEqual(result.returncode,0);self.assertEqual(calls,[])
    def test_help_lists_lifecycle_and_fault_commands_under_the_front_door_name(self):
        result,calls=self.run_demo('help')
        self.assertEqual((result.returncode,calls),(0,[]))
        for text in ('demo/demo setup','demo/demo up ','demo/demo destroy','demo/demo down web03 http','demo/demo ports open web03 http 8088'):
            self.assertIn(text,result.stdout)
        self.assertNotIn('Pinpoint-Demo-faults.sh',result.stdout)
    def test_every_command_in_usage_md_is_accepted(self):
        text=(DEMO/'USAGE.md').read_text()
        commands=[]
        for span in re.findall(r'`(demo/demo [^`]+)`',text):
            commands.append(span)
        self.assertGreaterEqual(len(commands),20)
        for command in commands:
            args=command.split()[1:]
            if args[0] in {'help','wall'}:continue  # wall is an endless display loop
            with self.subTest(command=command):
                result,calls=self.run_demo(*args)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(len(calls),1)
    def test_command_help_shows_only_that_commands_examples(self):
        result,calls=self.run_demo('ports','--help')
        self.assertEqual((result.returncode,calls),(0,[]))
        lines=result.stdout.strip().splitlines()
        self.assertTrue(lines and all('demo/demo ports' in l for l in lines))
        result,calls=self.run_demo('setup','--help')
        self.assertEqual((result.returncode,calls),(0,[]));self.assertIn('--apply',result.stdout)
    def test_help_text_covers_every_usage_command_family(self):
        result,_=self.run_demo('help')
        for family in ('setup','up','down','destroy','dhcp-move','address-mode','ports open','ports close','ports restore','reset'):
            self.assertIn('demo/demo '+family,result.stdout)
        self.assertIn('demo/demo presenter manifest',result.stdout)
if __name__=='__main__':unittest.main()
