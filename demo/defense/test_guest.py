"""Guest namespace ownership tests; never invoke Docker or mutate networking."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense.compose import compose_document
from defense.guest import validate_parent, validate_container, attach, validate_spike_target

CATALOG=load_catalog()
OWNER='b'*48
IMAGE='sha256:'+'a'*64
CONTEXT={'version':1,'owner':OWNER,'vm_uuid':'351eb491-f5e1-4854-a7e4-68309ad774ad','parent_mac':'02:77:01:ff:00:02'}


def fixture(target='dynweb01'):
    """Construct Docker's observed shape from independently checked expected fields."""
    service=compose_document(CATALOG,IMAGE,OWNER,spike=True)['services'][target]
    return {'Id':'c'*64,'Name':'/'+service['container_name'],'Image':IMAGE,
            'Config':{'Labels':service['labels'],'Cmd':service['command'],'Hostname':target},
            'State':{'Running':True,'Pid':1234},
            'HostConfig':{'NetworkMode':'none','Privileged':False,'PidMode':'',
                          'CapAdd':service.get('cap_add',[]),'CapDrop':[],
                          'PortBindings':{},'RestartPolicy':{'Name':'no'}},
            'Mounts':[{'Type':'bind','Source':v['source'],'Destination':v['target'],'RW':not v['read_only']} for v in service['volumes']],
            'NetworkSettings':{'Networks':{'none':{}}}}


class GuestTests(unittest.TestCase):
    def test_parent_requires_one_unnumbered_non_bridge_exact_mac(self):
        links=[{'ifname':'enp0s8','address':CONTEXT['parent_mac'],'addr_info':[]}]
        self.assertEqual(validate_parent(CONTEXT,links,0,0),'enp0s8')
        for change in [lambda x:x[0]['addr_info'].append({'family':'inet','local':'10.77.1.4'}),
                       lambda x:x[0].update(master='br0'),lambda x:x.append(copy.deepcopy(x[0])),
                       lambda x:x[0].update(address='02:00:00:00:00:01')]:
            altered=copy.deepcopy(links);change(altered)
            with self.assertRaises(ValueError):validate_parent(CONTEXT,altered,0,0)
        with self.assertRaises(ValueError):validate_parent(CONTEXT,links,1,0)
        with self.assertRaises(ValueError):validate_parent(CONTEXT,links,0,1)

    def test_foreign_runtime_or_mount_capability_image_rejects(self):
        self.assertEqual(validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',fixture()),1234)
        observed=fixture('dhcp01');observed['HostConfig']['CapAdd']=['CAP_NET_ADMIN']
        self.assertEqual(validate_container(CATALOG,CONTEXT,IMAGE,'dhcp01',observed),1234)
        for mutate in [lambda x:x.update(Image='untrusted:latest'),
                       lambda x:x['Config']['Labels'].update({'org.pinpoint.defense.owner':'foreign'}),
                       lambda x:x['HostConfig'].update(Privileged=True),
                       lambda x:x['HostConfig'].update(CapAdd=['SYS_ADMIN']),
                       lambda x:x['HostConfig'].update(NetworkMode='host'),
                       lambda x:x['Mounts'].append({'Type':'bind','Source':'/','Destination':'/host','RW':True}),
                       lambda x:x['State'].update(Pid=0),lambda x:x['State'].update(Running=False)]:
            observed=fixture();mutate(observed)
            with self.assertRaises(ValueError):validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed)

    def test_compose_metadata_labels_are_allowed_without_weakening_owner_pins(self):
        observed=fixture()
        observed['Config']['Labels']['com.docker.compose.project']='pinpoint-defense274'
        self.assertEqual(validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed),1234)
        observed['Config']['Labels']['foreign.owner']='unexpected'
        with self.assertRaises(ValueError):validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed)

    def test_only_two_target_spike_is_exposed_until_live_proof(self):
        validate_spike_target(CATALOG,'dhcp01');validate_spike_target(CATALOG,'dynweb01')
        for target in ['web03','win01','../foreign']:
            with self.assertRaises(ValueError):validate_spike_target(CATALOG,target)

    def test_foreign_container_is_rejected_before_link_mutation(self):
        observed=fixture();observed['Image']='sha256:'+'d'*64
        with patch('defense.guest.observe_container',return_value=observed),patch('defense.guest.command') as run:
            with self.assertRaises(ValueError):attach(CATALOG,CONTEXT,IMAGE,'dynweb01','enp0s8')
            run.assert_not_called()


if __name__=='__main__':unittest.main()
