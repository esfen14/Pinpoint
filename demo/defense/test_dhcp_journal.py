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
from defense.dhcp_journal import prepare, read, advance, clear, rollback_step

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
    def test_rollback_selects_one_step_from_observed_state(self):
        prepare(self.root,self.catalog,self.plan,self.pins)
        advance(self.root,self.catalog,'rollback_requested')
        record=read(self.root,self.catalog)
        addresses={name:[addr] for name,addr in self.before.items()}
        def decide(reservations,client):
            observed=dict(addresses,dynweb01=client)
            return rollback_step(self.catalog,record,{'pins':self.pins,'reservations':reservations,'addresses':observed,'server_running':True})
        self.assertEqual(decide(self.plan['after'],[self.plan['after']['dynweb01']]),'release')
        self.assertEqual(decide(self.plan['after'],[self.plan['before']['dynweb01']]),'release')
        self.assertEqual(decide(self.plan['after'],[]),'restore_reservations')
        self.assertEqual(decide(self.plan['before'],[self.plan['after']['dynweb01']]),'release')
        self.assertEqual(decide(self.plan['before'],[]),'acquire_original')
        self.assertEqual(decide(self.plan['before'],[self.before['dynweb01']]),'verify_baseline')
    def test_rollback_refuses_untrusted_or_ambiguous_observations(self):
        prepare(self.root,self.catalog,self.plan,self.pins);advance(self.root,self.catalog,'rollback_requested')
        record=read(self.root,self.catalog)
        sample={'pins':dict(self.pins),'reservations':dict(self.before),'addresses':{k:[v] for k,v in self.before.items()},'server_running':True}
        bad=[dict(sample,pins=dict(self.pins,dynweb02='f'*64)),dict(sample,server_running=False),
             dict(sample,server_running=1),dict(sample,reservations=dict(self.before,dynweb02='10.77.1.26')),
             dict(sample,addresses=dict(sample['addresses'],dynweb02=[])),
             dict(sample,addresses=dict(sample['addresses'],dynweb01=['10.77.1.27'])),
             dict(sample,addresses=dict(sample['addresses'],dynweb01=[self.before['dynweb01'],self.plan['after']['dynweb01']])),
             dict(sample,extra=True)]
        for observed in bad:
            with self.subTest(observed=observed),self.assertRaises(ValueError):rollback_step(self.catalog,record,observed)
        record['phase']='prepared'
        with self.assertRaises(ValueError):rollback_step(self.catalog,record,sample)
if __name__=='__main__':unittest.main()
