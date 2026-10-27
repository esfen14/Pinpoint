"""Offline durability and refusal tests for DHCP move recovery intent."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense.dhcp_move import plan_move
from defense.dhcp_journal import prepare, read, advance, clear

class DhcpJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.catalog=load_catalog();self.before={d.name:d.address for d in self.catalog.devices if d.mode=='dhcp'}
        self.plan=plan_move(self.catalog,'dynweb01','10.77.1.25',self.before,{k:[v] for k,v in self.before.items()})
        self.pins={name:format(i,'064x') for i,name in enumerate(['dhcp01',*self.before],1)}
    def tearDown(self):self.temp.cleanup()
    def test_private_record_and_closed_phase_transitions(self):
        prepare(self.root,self.catalog,self.plan,self.pins)
        self.assertEqual(read(self.root,self.catalog)['phase'],'prepared')
        self.assertEqual((self.root/'dhcp-move.json').stat().st_mode & 0o777,0o600)
        with self.assertRaises(ValueError):clear(self.root,self.catalog)
        with self.assertRaises(ValueError):advance(self.root,self.catalog,'acquired')
        advance(self.root,self.catalog,'released');advance(self.root,self.catalog,'server_changed')
        advance(self.root,self.catalog,'acquired');clear(self.root,self.catalog)
        self.assertFalse((self.root/'dhcp-move.json').exists())
    def test_rollback_requires_explicit_intent_before_cleanup(self):
        prepare(self.root,self.catalog,self.plan,self.pins)
        advance(self.root,self.catalog,'rollback_requested')
        with self.assertRaises(ValueError):clear(self.root,self.catalog)
        advance(self.root,self.catalog,'restored');clear(self.root,self.catalog)
    def test_refuses_colliding_existing_files_and_invalid_pins(self):
        bad=dict(self.pins);bad['dynweb02']=bad['dynweb01']
        with self.assertRaises(ValueError):prepare(self.root,self.catalog,self.plan,bad)
        self.assertFalse((self.root/'dhcp-move.json').exists())
        foreign=self.root/'foreign';foreign.write_text('keep');(self.root/'dhcp-move.json').symlink_to(foreign)
        with self.assertRaises(ValueError):prepare(self.root,self.catalog,self.plan,self.pins)
        self.assertEqual(foreign.read_text(),'keep')
    def test_refuses_permissive_directory_before_creating_intent(self):
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):prepare(self.root,self.catalog,self.plan,self.pins)
        self.assertFalse((self.root/'dhcp-move.json').exists())
        self.root.chmod(0o700)
    def test_refuses_tampering_and_unsafe_permissions(self):
        prepare(self.root,self.catalog,self.plan,self.pins)
        path=self.root/'dhcp-move.json';record=json.loads(path.read_text())
        record['plan']['after']['dynweb02']='10.77.1.26';path.write_text(json.dumps(record))
        with self.assertRaises(ValueError):read(self.root,self.catalog)
        path.chmod(0o644)
        with self.assertRaises(ValueError):read(self.root,self.catalog)
if __name__=='__main__':unittest.main()
