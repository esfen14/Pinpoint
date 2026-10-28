"""Offline tests for the portable presenter fault script; a stub replaces the real lab."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'Pinpoint-Demo-faults.sh'
STUB='#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$STUB_LOG"\n'


class FaultScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'demo').mkdir()
        self.script=self.root/'demo'/SCRIPT.name
        shutil.copy2(SCRIPT,self.script)
        stub=self.root/'demo'/'demo';stub.write_text(STUB);stub.chmod(0o755)
        self.log=self.root/'log'
    def tearDown(self):self.tmp.cleanup()
    def run_script(self,*args,script=None):
        env=dict(os.environ,STUB_LOG=str(self.log))
        if self.log.exists():self.log.unlink()
        result=subprocess.run([str(script or self.script),*args],capture_output=True,text=True,env=env,timeout=20)
        called=self.log.read_text().split() if self.log.exists() else None
        return result.returncode,called
    def test_service_and_host_faults_dispatch_to_fixed_presenter_commands(self):
        cases={('down','web03','http'):['presenter','break','web03','http'],
               ('up','web03','http'):['presenter','fix','web03','http'],
               ('down','dynapp01','host'):['presenter','host-stop','dynapp01'],
               ('up','dynapp01','host'):['presenter','host-start','dynapp01'],
               ('status',):['presenter','status'],
               ('dhcp-move','dynweb01','10.77.1.25'):['presenter','dhcp-move','dynweb01','10.77.1.25'],
               ('dhcp-recover',):['presenter','dhcp-recover'],
               ('ports','list','web03'):['presenter','ports','list','web03'],
               ('ports','open','web03','http','8088'):['presenter','ports','open','web03','http','8088'],
               ('ports','open','api02','tcp','20080'):['presenter','ports','open','api02','tcp','20080'],
               ('ports','close','web03','8088'):['presenter','ports','close','web03','8088'],
               ('ports','restore','web03'):['presenter','ports','restore','web03'],
               ('ports','restore','all'):['presenter','ports','restore','all'],
               ('address-mode','show','dynweb01'):['presenter','address-mode','show','dynweb01'],
               ('address-mode','static','dynweb01','10.77.1.15'):['presenter','address-mode','static','dynweb01','10.77.1.15'],
               ('address-mode','dhcp','dynapp01'):['presenter','address-mode','dhcp','dynapp01'],
               ('address-mode','recover'):['presenter','address-mode','recover']}
        for args,expected in cases.items():
            with self.subTest(args=args):
                code,called=self.run_script(*args)
                self.assertEqual((code,called),(0,expected))
    def test_unknown_targets_services_and_extra_arguments_are_rejected(self):
        bad=[('down','web01','http'),('down','web03','rm'),('down','web03','http','x'),('down','web03'),('up','win01','host'),
             ('down','web03;id','http'),('dhcp-move','web03','10.77.1.25'),('dhcp-move','dynweb01','10.77.1.25;id'),
             ('dhcp-move','dynweb01','8.8.8.8'),('ports',),('ports','open','web03','ftp','8088'),('ports','open','web03','http','80x'),
             ('ports','open','win01','http','8088'),('ports','open','web03','http','8088;id'),('ports','close','web03'),('ports','restore','all','x'),('ports','list','all'),('ports','kill','web03'),('address-mode',),('address-mode','static','web03','10.77.1.15'),('address-mode','static','dynweb01','8.8.8.8'),
             ('address-mode','static','dynweb01','10.77.1.15;id'),('address-mode','static','dynweb01'),('address-mode','dhcp','dynweb01','x'),('address-mode','recover','x'),('address-mode','show'),('address-mode','wipe','dynweb01'),('frobnicate',),('status','x')]
        for args in bad:
            with self.subTest(args=args):
                code,called=self.run_script(*args)
                self.assertNotEqual(code,0);self.assertIsNone(called)
    def test_documents_style_symlink_finds_the_repository(self):
        link=self.root/'Pinpoint-Demo-faults.sh';link.symlink_to(self.script)
        self.assertEqual(self.run_script('status',script=link),(0,['presenter','status']))
if __name__=='__main__':unittest.main()
