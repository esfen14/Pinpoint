"""Behavioral tests for DHCP moves and interrupted rollback using fake devices."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense.dhcp_control import move, recover


class FakeLab:
    def __init__(self,catalog):
        self.catalog=catalog
        self.reservations={d.name:d.address for d in catalog.devices if d.mode=='dhcp'}
        self.addresses={name:[address] for name,address in self.reservations.items()}
        self.pins={name:format(i,'064x') for i,name in enumerate(['dhcp01',*self.reservations],1)}
        self.fail=None;self.config_calls=0;self.broken=False;self.restarted=False;self.baseline_calls=0
    def restore_baseline(self):
        self.baseline_calls+=1;self.restarted=False
    def snapshot(self):
        if self.restarted:raise ValueError('Allocator baseline missing after restart')
        return {'pins':dict(self.pins),'reservations':None if self.broken else dict(self.reservations),
                'addresses':{name:list(addresses) for name,addresses in self.addresses.items()},
                'lease_seconds':600,'server_running':not self.broken}
    def release(self,name):
        self.addresses[name]=[]
        if self.fail=='release':self.fail=None;raise RuntimeError('interrupted after release')
        if self.fail=='crash':self.fail=None;raise SimulatedCrash()
    def configure(self,reservations):
        self.config_calls+=1
        self.reservations=dict(reservations)
        self.broken=False
        if self.fail=='torn' and self.config_calls==2:
            self.fail=None;self.broken=True;raise RuntimeError('allocator configuration interrupted')
        if self.fail=='configure' and self.config_calls==2:self.fail=None;raise RuntimeError('interrupted after configuration')
        if self.fail=='crash_configure' and self.config_calls==2:self.fail=None;raise SimulatedCrash()
    def acquire(self,name,address):
        if self.reservations[name]!=address:raise ValueError('wrong reservation')
        self.addresses[name]=[address]
        if self.fail=='acquire':self.fail=None;raise RuntimeError('interrupted after acquisition')
        if self.fail=='crash_acquire':self.fail=None;raise SimulatedCrash()


class SimulatedCrash(BaseException):
    pass


class MoveTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog();self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name);self.lab=FakeLab(self.catalog)
        self.baseline=self.lab.snapshot()
    def tearDown(self):self.tmp.cleanup()
    def test_move_updates_only_the_selected_device_and_clears_intent(self):
        move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.25')
        state=self.lab.snapshot()
        self.assertEqual(state['addresses']['dynweb01'],['10.77.1.25'])
        self.assertEqual(state['reservations']['dynweb01'],'10.77.1.25')
        for name in self.baseline['addresses']:
            if name!='dynweb01':self.assertEqual(state['addresses'][name],self.baseline['addresses'][name])
        self.assertFalse((self.root/'dhcp-move.json').exists())
        move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.26')
        self.assertEqual(self.lab.addresses['dynweb01'],['10.77.1.26'])
        self.assertEqual(self.lab.reservations['dynweb01'],'10.77.1.26')
    def test_interrupted_operations_restore_original_state(self):
        for phase in ['release','configure','torn','acquire']:
            with self.subTest(phase=phase):
                self.lab=FakeLab(self.catalog);self.lab.fail=phase
                with self.assertRaises(RuntimeError):move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.25')
                self.assertEqual(self.lab.snapshot(),self.baseline)
                self.assertFalse((self.root/'dhcp-move.json').exists())
    def test_unsafe_or_colliding_destination_does_not_change_state(self):
        for address in ['10.77.1.21','10.77.1.15','10.77.1.25;id']:
            with self.assertRaises(ValueError):move(self.root,self.catalog,self.lab,'dynweb01',address)
        self.assertEqual(self.lab.snapshot(),self.baseline)
        self.assertFalse((self.root/'dhcp-move.json').exists())
    def test_interrupted_rollback_retains_intent_for_later_recovery(self):
        self.lab.fail='configure'
        original=self.lab.configure
        calls=0
        def always_fail(values):
            nonlocal calls
            calls+=1
            self.lab.reservations=dict(values)
            if calls==1:return
            raise RuntimeError('allocator unavailable')
        self.lab.configure=always_fail
        with self.assertRaises(RuntimeError):move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.25')
        self.assertTrue((self.root/'dhcp-move.json').exists())
        self.lab.configure=original;self.lab.fail=None
        recover(self.root,self.catalog,self.lab)
        self.assertEqual(self.lab.snapshot(),self.baseline)
        self.assertFalse((self.root/'dhcp-move.json').exists())
    def test_recovery_restores_allocator_baseline_after_container_restart(self):
        self.lab.fail='crash'
        with self.assertRaises(SimulatedCrash):move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.25')
        self.lab.restarted=True
        recover(self.root,self.catalog,self.lab)
        self.assertEqual(self.lab.baseline_calls,1)
        self.assertEqual(self.lab.snapshot(),self.baseline)
        self.assertFalse((self.root/'dhcp-move.json').exists())
    def test_process_termination_leaves_intent_for_later_recovery(self):
        for phase in ['crash','crash_configure','crash_acquire']:
            with self.subTest(phase=phase):
                self.lab=FakeLab(self.catalog);self.lab.fail=phase
                with self.assertRaises(SimulatedCrash):move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.25')
                self.assertTrue((self.root/'dhcp-move.json').exists())
                recover(self.root,self.catalog,self.lab)
                self.assertEqual(self.lab.snapshot(),self.baseline)
                self.assertFalse((self.root/'dhcp-move.json').exists())
    def test_foreign_client_change_stops_recovery_and_preserves_journal(self):
        acquire=self.lab.acquire
        def interfere(name,address):
            acquire(name,address)
            self.lab.addresses['dynweb02']=[]
        self.lab.acquire=interfere
        with self.assertRaises(ValueError):move(self.root,self.catalog,self.lab,'dynweb01','10.77.1.25')
        self.assertTrue((self.root/'dhcp-move.json').exists())
        with self.assertRaises(ValueError):recover(self.root,self.catalog,self.lab)
        self.assertTrue((self.root/'dhcp-move.json').exists())

if __name__=='__main__':unittest.main()
