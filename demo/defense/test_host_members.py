"""Offline tests for VirtualBox host-only membership boundaries."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.host_members import validate_vm_membership

class HostMembersTests(unittest.TestCase):
    def setUp(self):
        self.pins={'appliance':{'uuid':'11111111-1111-4111-8111-111111111111','slot':2,'mac':'08:00:27:aa:bb:01'},
                   'windows':{'uuid':'22222222-2222-4222-8222-222222222222','slot':1,'mac':'02:77:01:00:00:02'}}
        self.records=[{'uuid':p['uuid'],'state':'running','adapters':[{'slot':p['slot'],'type':'hostonly','network':'vboxnet1','mac':p['mac']}]} for p in self.pins.values()]
    def test_exact_two_pinned_members_are_accepted(self):
        self.assertTrue(validate_vm_membership(self.records,self.pins))
    def test_foreign_duplicate_wrong_slot_or_mac_are_refused(self):
        foreign={'uuid':'33333333-3333-4333-8333-333333333333','state':'poweroff','adapters':[{'slot':1,'type':'hostonly','network':'vboxnet1','mac':'08:00:27:aa:bb:03'}]}
        cases=[self.records+[foreign],self.records+[deepcopy(self.records[0])]]
        wrong=deepcopy(self.records);wrong[0]['adapters'][0]['slot']=3;cases.append(wrong)
        wrong=deepcopy(self.records);wrong[0]['adapters'][0]['mac']='08:00:27:aa:bb:09';cases.append(wrong)
        wrong=deepcopy(self.records);wrong[0]['state']='paused';cases.append(wrong)
        for records in cases:
            with self.assertRaises(ValueError):validate_vm_membership(records,self.pins)
    def test_rejects_ambiguous_and_malformed_inventory(self):
        for records in [[],self.records[:1],self.records+[{'uuid':'bad','state':'poweroff','adapters':[]}],
                        [dict(self.records[0],adapters='bad'),self.records[1]]]:
            with self.assertRaises(ValueError):validate_vm_membership(records,self.pins)
        with self.assertRaises(ValueError):validate_vm_membership(self.records,{'windows':self.pins['windows']})
if __name__=='__main__':unittest.main()
