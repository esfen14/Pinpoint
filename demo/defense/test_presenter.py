"""Offline tests for fixed presenter service and Docker identity boundaries."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.presenter import service_program, validate_container, lifecycle_order, service, remove_default_route
from defense.catalog import load_catalog

class PresenterTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog()
        self.target=self.catalog.target('web03')
        self.root=Path('/private/pilot-catalog')
        self.obj={'Id':'a'*64,'Name':'/pinpoint274-host-web03-pilot','Image':'sha256:'+'b'*64,
                  'State':{'Running':True},'Config':{'Cmd':['python3','/opt/pinpoint/defense/node.py','init','web03'],
                  'Labels':{'org.pinpoint.defense.issue':'274','org.pinpoint.defense.role':'temporary-pilot'}},
                  'HostConfig':{'NetworkMode':'pinpoint274-host-test','Privileged':False},
                  'Mounts':[{'Type':'bind','Source':str(self.root.parent/'pilot-web03'/'identity'),'Destination':'/identity','RW':True},
                            {'Type':'bind','Source':str(self.root.parent/'pilot-web03'/'data'),'Destination':'/data','RW':True},
                            {'Type':'bind','Source':'/private/context/context.json','Destination':'/etc/pinpoint-defense/context.json','RW':False}]}
    def test_only_catalog_service_pairs_and_fixed_supervisor_program(self):
        self.assertEqual(service_program(self.catalog,'web03','http'),'web')
        self.assertEqual(service_program(self.catalog,'web03','https'),'web')
        for target,service in [('web03','ssh'),('dhcp01','dhcp'),('web03','http;id'),('../bad','http')]:
            with self.assertRaises(ValueError): service_program(self.catalog,target,service)
    def test_lifecycle_order_keeps_allocator_first_on_start_and_last_on_stop(self):
        start=lifecycle_order(self.catalog,'up'); stop=lifecycle_order(self.catalog,'down')
        self.assertEqual(len(start),14)
        self.assertEqual(start[0].name,'dhcp01')
        self.assertEqual(stop[-1].name,'dhcp01')
        self.assertEqual([x.name for x in stop],list(reversed([x.name for x in start])))
        with self.assertRaises(ValueError):lifecycle_order(self.catalog,'destroy')
    def test_service_is_idempotent_and_checks_the_result(self):
        running={'network_safe':True,'addresses':['10.77.1.4'],'services':[{'program':'web','state':'RUNNING'}]}
        stopped={'network_safe':True,'addresses':['10.77.1.4'],'services':[{'program':'web','state':'STOPPED'}]}
        with patch('defense.presenter.node',side_effect=[running,stopped]), patch('defense.presenter.inspect'), patch('defense.presenter.run') as run:
            service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            self.assertEqual(run.call_args.args[0][-2:],['stop','web'])
        with patch('defense.presenter.node',side_effect=[stopped,stopped]), patch('defense.presenter.run') as run:
            service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            run.assert_not_called()
        unsafe=dict(running,network_safe=False)
        with patch('defense.presenter.node',return_value=unsafe), patch('defense.presenter.run') as run:
            with self.assertRaises(ValueError):service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            run.assert_not_called()
    def test_only_known_docker_default_route_can_be_removed(self):
        pin={'id':'a'*64}
        with patch('defense.presenter.run',side_effect=['[{"gateway":"10.77.1.30","dev":"eth0"}]','']) as run:
            remove_default_route(pin)
            self.assertEqual(run.call_count,2)
        with patch('defense.presenter.run',return_value='[{"gateway":"192.168.1.1","dev":"eth0"}]') as run:
            with self.assertRaises(ValueError):remove_default_route(pin)
            self.assertEqual(run.call_count,1)
        with patch('defense.presenter.run',return_value='[]') as run:
            remove_default_route(pin)
            self.assertEqual(run.call_count,1)
    def test_container_pins_reject_identity_mount_or_command_changes(self):
        validate_container(self.obj,self.target,self.root,Path('/private/context/context.json'),{'id':'a'*64,'image':'sha256:'+'b'*64})
        for key,value in [('Id','c'*64),('Image','sha256:'+'d'*64),('Name','/foreign')]:
            obj=dict(self.obj,**{key:value})
            with self.assertRaises(ValueError):validate_container(obj,self.target,self.root,Path('/private/context/context.json'),{'id':'a'*64,'image':'sha256:'+'b'*64})
        obj=dict(self.obj,Mounts=self.obj['Mounts'][:-1])
        with self.assertRaises(ValueError):validate_container(obj,self.target,self.root,Path('/private/context/context.json'),{'id':'a'*64,'image':'sha256:'+'b'*64})
if __name__=='__main__':unittest.main()
