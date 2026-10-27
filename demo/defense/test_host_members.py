"""Offline tests for VirtualBox host-only membership boundaries."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.host_members import validate_vm_membership, collect_vm_inventory

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
    def test_validator_refuses_ambiguous_non_hostonly_records(self):
        foreign={'uuid':'33333333-3333-4333-8333-333333333333','state':'running','adapters':[{'slot':1,'type':'mystery','network':'','mac':'08:00:27:aa:bb:03'}]}
        with self.assertRaises(ValueError):validate_vm_membership(self.records+[foreign],self.pins)
        foreign['adapters'][0].update(type='hostonly',network='')
        with self.assertRaises(ValueError):validate_vm_membership(self.records+[foreign],self.pins)
    def test_collector_reads_complete_fixed_uuid_inventory(self):
        lines=''.join('"device" {'+p['uuid']+'}\n' for p in self.pins.values())
        def observe(argv):
            if argv==['VBoxManage','list','vms']:return lines
            self.assertEqual(argv[:2],['VBoxManage','showvminfo'])
            pin=next(p for p in self.pins.values() if p['uuid']==argv[2])
            values={'UUID':pin['uuid'],'VMState':'running'}
            for slot in range(1,9):values['nic'+str(slot)]='hostonly' if slot==pin['slot'] else 'none'
            values['hostonlyadapter'+str(pin['slot'])]='vboxnet1'
            values['macaddress'+str(pin['slot'])]=pin['mac'].replace(':','').upper()
            return ''.join(k+'="'+v+'"\n' for k,v in values.items())
        self.assertTrue(validate_vm_membership(collect_vm_inventory(observe),self.pins))
    def test_collector_rechecks_inventory_after_observations(self):
        pins=list(self.pins.values());count=0
        def observe(argv):
            nonlocal count
            if argv==['VBoxManage','list','vms']:
                count+=1
                return ''.join('"device" {'+p['uuid']+'}\n' for p in (pins if count==1 else pins[:1]))
            pin=next(p for p in pins if p['uuid']==argv[2])
            fields={'UUID':pin['uuid'],'VMState':'running'}
            for slot in range(1,9):fields['nic'+str(slot)]='hostonly' if slot==pin['slot'] else 'none'
            fields['hostonlyadapter'+str(pin['slot'])]='vboxnet1';fields['macaddress'+str(pin['slot'])]=pin['mac'].replace(':','').upper()
            return ''.join(k+'="'+v+'"\n' for k,v in fields.items())
        with self.assertRaises(ValueError):collect_vm_inventory(observe)
    def test_collector_refuses_adapter_changes_during_observation(self):
        pins=list(self.pins.values());calls={p['uuid']:0 for p in pins}
        def observe(argv):
            if argv==['VBoxManage','list','vms']:
                return ''.join('"device" {'+p['uuid']+'}\n' for p in pins)
            pin=next(p for p in pins if p['uuid']==argv[2]);calls[pin['uuid']]+=1
            fields={'UUID':pin['uuid'],'VMState':'running'}
            for slot in range(1,9):fields['nic'+str(slot)]='hostonly' if slot==pin['slot'] else 'none'
            fields['hostonlyadapter'+str(pin['slot'])]='vboxnet1' if calls[pin['uuid']]==1 else 'other'
            fields['macaddress'+str(pin['slot'])]=pin['mac'].replace(':','').upper()
            return ''.join(k+'="'+v+'"\n' for k,v in fields.items())
        with self.assertRaises(ValueError):collect_vm_inventory(observe)
    def test_collector_refuses_missing_unknown_or_ambiguous_metadata(self):
        pin=self.pins['windows'];uid=pin['uuid']
        vm='UUID="'+uid+'"\nVMState="running"\n'+''.join('nic'+str(i)+'="'+('hostonly' if i==1 else 'none')+'"\n' for i in range(1,9))+'macaddress1="027701000002"\n'
        other=self.pins['appliance']['uuid']
        for broken in [vm,vm+'hostonlyadapter1=""\n',vm+'hostonlyadapter1="vboxnet1"\nnic1="nat"\n']:
            calls=[]
            def observe(argv):
                calls.append(argv)
                if argv[-2:]==['list','vms']:return '"first" {'+uid+'}\n"second" {'+other+'}\n'
                return broken
            with self.assertRaises(ValueError):collect_vm_inventory(observe)
            self.assertGreaterEqual(len(calls),2)
    def test_rejects_ambiguous_and_malformed_inventory(self):
        for records in [[],self.records[:1],self.records+[{'uuid':'bad','state':'poweroff','adapters':[]}],
                        [dict(self.records[0],adapters='bad'),self.records[1]]]:
            with self.assertRaises(ValueError):validate_vm_membership(records,self.pins)
        with self.assertRaises(ValueError):validate_vm_membership(self.records,{'windows':self.pins['windows']})
if __name__=='__main__':unittest.main()
