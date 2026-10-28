"""Behavioral tests for DHCP/static address-mode transactions using a fake client."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense import address_mode


class Crash(BaseException):
    pass


class FakeClient:
    def __init__(self,reserved='10.77.1.20'):
        self.addresses=[reserved];self.reserved=reserved;self.server_running=True
        self.fail=None;self.calls=[]
    def state(self):
        return {'addresses':list(self.addresses),'reserved':self.reserved,'server_running':self.server_running}
    def step(self,name):
        self.calls.append(name)
        if self.fail==name:
            self.fail=None;raise RuntimeError('interrupted at '+name)
        if self.fail=='crash:'+name:
            self.fail=None;raise Crash()
    def release(self):
        self.step('release');self.addresses=[]
    def acquire(self,address):
        self.step('acquire')
        if not self.server_running:raise ValueError('Allocator is not running')
        if address!=self.reserved:raise ValueError('wrong reservation')
        self.addresses=[address]
    def add_static(self,address):
        self.step('add_static')
        if self.addresses:raise ValueError('Client already has an address')
        self.addresses=[address]
    def remove_static(self,address):
        self.step('remove_static')
        if self.addresses!=[address]:raise ValueError('Static address changed')
        self.addresses=[]


class AddressModeTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog();self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name);self.root.chmod(0o700);self.client=FakeClient()
    def tearDown(self):self.tmp.cleanup()
    def intent(self):return (self.root/'address-mode.json').exists()
    def static(self,address='10.77.1.15',occupied=()):
        address_mode.to_static(self.root,self.catalog,self.client,'dynweb01',address,occupied=set(occupied))
    def test_show_reports_dhcp_then_static_mode(self):
        self.assertEqual(address_mode.show(self.catalog,self.client.state()),{'mode':'dhcp','address':'10.77.1.20'})
        self.static()
        self.assertEqual(address_mode.show(self.catalog,self.client.state()),{'mode':'static','address':'10.77.1.15'})
    def test_dhcp_to_static_to_dhcp_leaves_exactly_one_address_each_time_and_clears_intent(self):
        self.static()
        self.assertEqual(self.client.addresses,['10.77.1.15']);self.assertFalse(self.intent())
        address_mode.to_dhcp(self.root,self.catalog,self.client,'dynweb01')
        self.assertEqual(self.client.addresses,['10.77.1.20']);self.assertFalse(self.intent())
    def test_repeating_either_transition_is_idempotent(self):
        self.static();self.client.calls.clear();self.static()
        self.assertEqual(self.client.calls,[])
        address_mode.to_dhcp(self.root,self.catalog,self.client,'dynweb01');self.client.calls.clear()
        address_mode.to_dhcp(self.root,self.catalog,self.client,'dynweb01')
        self.assertEqual(self.client.calls,[])
    def test_unsafe_targets_addresses_and_collisions_are_refused_without_changes(self):
        cases=[('dynweb01','10.77.1.25',()),('dynweb01','10.77.1.20',()),('dynweb01','10.77.1.4',()),('dynweb01','10.77.1.1',()),
               ('dynweb01','10.77.1.30',()),('dynweb01','8.8.8.8',()),('dynweb01','10.77.1.15',('10.77.1.15',)),
               ('web03','10.77.1.15',()),('win01','10.77.1.15',()),('foreign','10.77.1.15',()),('dynweb01','10.77.1.15;id',())]
        for target,address,occupied in cases:
            with self.subTest(target=target,address=address):
                with self.assertRaises(ValueError):
                    address_mode.to_static(self.root,self.catalog,self.client,target,address,occupied=set(occupied))
        self.assertEqual(self.client.calls,[]);self.assertFalse(self.intent())
    def test_static_to_static_is_refused_and_dhcp_return_needs_a_running_allocator(self):
        self.static()
        with self.assertRaises(ValueError):self.static('10.77.1.16')
        self.client.server_running=False
        with self.assertRaises(ValueError):address_mode.to_dhcp(self.root,self.catalog,self.client,'dynweb01')
        self.assertEqual(self.client.addresses,['10.77.1.15']);self.assertFalse(self.intent())
    def test_failure_during_static_change_rolls_back_to_the_original_lease(self):
        for step in ('release','add_static'):
            with self.subTest(step=step):
                self.client=FakeClient();self.client.fail=step
                with self.assertRaises(RuntimeError):self.static()
                self.assertEqual(self.client.addresses,['10.77.1.20']);self.assertFalse(self.intent())
    def test_allocator_outage_on_return_rolls_back_to_the_static_address(self):
        self.static()
        self.client.fail='acquire'
        with self.assertRaises(RuntimeError):address_mode.to_dhcp(self.root,self.catalog,self.client,'dynweb01')
        self.assertEqual(self.client.addresses,['10.77.1.15']);self.assertFalse(self.intent())
    def test_interrupted_process_leaves_intent_and_recovery_restores_the_original_mode(self):
        for step in ('release','add_static'):
            with self.subTest(step=step):
                self.client=FakeClient();self.client.fail='crash:'+step
                with self.assertRaises(Crash):self.static()
                self.assertTrue(self.intent())
                address_mode.recover(self.root,self.catalog,self.client)
                self.assertEqual(self.client.addresses,['10.77.1.20']);self.assertFalse(self.intent())
        self.client=FakeClient();self.static();self.client.fail='crash:remove_static'
        with self.assertRaises(Crash):address_mode.to_dhcp(self.root,self.catalog,self.client,'dynweb01')
        address_mode.recover(self.root,self.catalog,self.client)
        self.assertEqual(self.client.addresses,['10.77.1.15']);self.assertFalse(self.intent())
    def test_recovery_without_intent_is_a_noop_and_repeats_safely(self):
        address_mode.recover(self.root,self.catalog,self.client);self.assertEqual(self.client.calls,[])
        self.client.fail='crash:release'
        with self.assertRaises(Crash):self.static()
        address_mode.recover(self.root,self.catalog,self.client);address_mode.recover(self.root,self.catalog,self.client)
        self.assertEqual(self.client.addresses,['10.77.1.20'])
    def test_recovery_refuses_unexpected_state_and_keeps_the_intent(self):
        self.client.fail='crash:release'
        with self.assertRaises(Crash):self.static()
        self.client.addresses=['10.77.1.29']
        with self.assertRaises(ValueError):address_mode.recover(self.root,self.catalog,self.client)
        self.assertTrue(self.intent())
    def test_unsafe_or_malformed_intent_is_refused_and_exists_check_sees_any_entry(self):
        path=self.root/'address-mode.json'
        for text in ('not json','{"target":"web03"}',json.dumps({'version':1,'target':'dynweb01','original':'8.8.8.8','desired':'10.77.1.15'})):
            path.write_text(text);path.chmod(0o600)
            with self.subTest(text=text[:20]),self.assertRaises(ValueError):address_mode.recover(self.root,self.catalog,self.client)
            self.assertTrue(address_mode.intent_exists(self.root))
        path.unlink()
        path.symlink_to(self.root/'elsewhere')
        self.assertTrue(address_mode.intent_exists(self.root))
if __name__=='__main__':unittest.main()
