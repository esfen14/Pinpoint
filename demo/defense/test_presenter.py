"""Offline tests for fixed presenter service and Docker identity boundaries."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.presenter import service_program, validate_container, lifecycle_order, service, remove_default_route, dhcp_server, dhcp_lease, target_order
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
        running={'network_safe':True,'addresses':['10.77.1.4'],'services':[{'program':'web','state':'RUNNING'}],'listeners':[{'protocol':'tcp','port':80},{'protocol':'tcp','port':443}]}
        stopped={'network_safe':True,'addresses':['10.77.1.4'],'services':[{'program':'web','state':'STOPPED'}],'listeners':[]}
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[running,stopped]), patch('defense.presenter.inspect'), patch('defense.presenter.run') as run:
            service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            self.assertEqual(run.call_args.args[0][-2:],['stop','web'])
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[stopped,stopped]), patch('defense.presenter.run') as run:
            service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            run.assert_not_called()
        unsafe=dict(running,network_safe=False)
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',return_value=unsafe), patch('defense.presenter.run') as run:
            with self.assertRaises(ValueError):service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            run.assert_not_called()
    def test_service_refuses_false_stopped_state_with_listener_remaining(self):
        running={'network_safe':True,'addresses':['10.77.1.4'],'services':[{'program':'web','state':'RUNNING'}],'listeners':[{'protocol':'tcp','port':80},{'protocol':'tcp','port':443}]}
        lingering=dict(running,services=[{'program':'web','state':'STOPPED'}])
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[running,lingering]), patch('defense.presenter.inspect'), patch('defense.presenter.run'):
            with self.assertRaises(ValueError):service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
    def test_smtp_stop_removes_postfix_listener_even_if_supervisor_leaves_it(self):
        running={'network_safe':True,'addresses':['10.77.1.7'],'services':[{'program':'smtp','state':'RUNNING'}],'listeners':[{'protocol':'tcp','port':25}]}
        lingering=dict(running,services=[{'program':'smtp','state':'STOPPED'}])
        stopped=dict(lingering,listeners=[])
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[running,lingering,stopped]), patch('defense.presenter.inspect'), patch('defense.presenter.run') as run:
            service(self.catalog,{'mail01':{'id':'a'*64}},'mail01','smtp','stop')
            self.assertEqual(run.call_args_list[-1].args[0][-4:],['/usr/sbin/postfix','-c','/run/postfix','stop'])
    def test_service_fault_refuses_foreign_host_network(self):
        with patch('defense.presenter.check_host_network',side_effect=ValueError), patch('defense.presenter.node') as node:
            with self.assertRaises(ValueError):service(self.catalog,{'web03':{'id':'a'*64}},'web03','http','stop')
            node.assert_not_called()
    def test_smtp_start_recovers_a_master_orphaned_by_supervisor(self):
        orphan={'network_safe':True,'addresses':['10.77.1.7'],'services':[{'program':'smtp','state':'EXITED'}],'listeners':[{'protocol':'tcp','port':25}]}
        running=dict(orphan,services=[{'program':'smtp','state':'RUNNING'}])
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[orphan,running]), patch('defense.presenter.inspect'), patch('defense.presenter.run') as run:
            service(self.catalog,{'mail01':{'id':'a'*64}},'mail01','smtp','start')
            self.assertEqual(run.call_args_list[0].args[0][-4:],['/usr/sbin/postfix','-c','/run/postfix','stop'])
            self.assertEqual(run.call_args_list[1].args[0][-2:],['start','smtp'])
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
    def test_dhcp_server_rejects_unsafe_network_and_is_idempotent(self):
        server={'network_safe':True,'addresses':['10.77.1.2'],'services':[{'program':'dhcp','state':'STOPPED'}]}
        pins={'dhcp01':{'id':'a'*64}}
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[server,server]), patch('defense.presenter.node_request') as request:
            dhcp_server(self.catalog,pins,'stop');request.assert_not_called()
        with patch('defense.presenter.check_host_network',side_effect=ValueError), patch('defense.presenter.node_request') as request:
            with self.assertRaises(ValueError):dhcp_server(self.catalog,pins,'start')
            request.assert_not_called()
    def test_lease_actions_are_limited_to_catalog_dhcp_clients(self):
        pins={'web03':{},'dynweb01':{}}
        with patch('defense.presenter.node_request') as request:
            with self.assertRaises(ValueError):dhcp_lease(self.catalog,pins,'web03','release')
            with self.assertRaises(ValueError):dhcp_lease(self.catalog,pins,'dynweb01','other')
            request.assert_not_called()
    def test_release_also_stops_an_unaddressed_lease_client(self):
        client={'network_safe':True,'addresses':[],'services':[{'program':'lease','state':'RUNNING'}]}
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.node',side_effect=[client,client]), patch('defense.presenter.node_request') as request:
            dhcp_lease(self.catalog,{'dynweb01':{'id':'a'*64}},'dynweb01','release')
            self.assertEqual(request.call_args.args[2],{'operation':'lease-release'})
    def test_host_fault_selects_one_known_linux_target(self):
        self.assertEqual([d.name for d in target_order(self.catalog,'up','dynweb02')],['dynweb02'])
        for name in ['win01','../bad','unknown']:
            with self.assertRaises(ValueError):target_order(self.catalog,'up',name)
        with self.assertRaises(ValueError):target_order(self.catalog,'destroy','dynweb02')
    def test_container_pins_reject_identity_mount_or_command_changes(self):
        validate_container(self.obj,self.target,self.root,Path('/private/context/context.json'),{'id':'a'*64,'image':'sha256:'+'b'*64})
        for key,value in [('Id','c'*64),('Image','sha256:'+'d'*64),('Name','/foreign')]:
            obj=dict(self.obj,**{key:value})
            with self.assertRaises(ValueError):validate_container(obj,self.target,self.root,Path('/private/context/context.json'),{'id':'a'*64,'image':'sha256:'+'b'*64})
        obj=dict(self.obj,Mounts=self.obj['Mounts'][:-1])
        with self.assertRaises(ValueError):validate_container(obj,self.target,self.root,Path('/private/context/context.json'),{'id':'a'*64,'image':'sha256:'+'b'*64})
if __name__=='__main__':unittest.main()
