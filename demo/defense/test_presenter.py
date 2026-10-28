"""Offline tests for fixed presenter service and Docker identity boundaries."""
from pathlib import Path
import sys
import tempfile
import json
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.presenter import service_program, validate_container, lifecycle_order, service, remove_default_route, dhcp_server, dhcp_lease, target_order
from defense.catalog import load_catalog
from defense import presenter

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
        with patch('defense.presenter.check_host_network'), patch('defense.presenter.reserved_address',return_value='10.77.1.20'), patch('defense.presenter.node',side_effect=[client,client]), patch('defense.presenter.node_request') as request:
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
    def test_pending_dhcp_intent_blocks_mutation_before_loading_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(presenter,'ROOT',root), patch.object(presenter,'read_pins') as pins, patch.object(presenter,'lifecycle') as lifecycle:
                (root/'dhcp-move.json').write_text('incomplete')
                self.assertEqual(presenter.main(['up']),1)
                pins.assert_not_called();lifecycle.assert_not_called()
                (root/'dhcp-move.json').unlink()
                with patch.object(presenter,'check_host_network'):
                    self.assertEqual(presenter.main(['up']),0)
                lifecycle.assert_called_once()
    def test_pending_intent_symlink_and_untrusted_directory_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'dhcp-move.json').symlink_to(root/'missing')
            with patch.object(presenter,'ROOT',root), patch.object(presenter,'read_pins') as pins:
                self.assertEqual(presenter.main(['down']),1)
                pins.assert_not_called()
                (root/'dhcp-move.json').unlink();root.chmod(0o755)
                self.assertEqual(presenter.main(['down']),1)
                pins.assert_not_called()
                root.chmod(0o700)
    def test_pending_intent_blocks_all_presenter_mutations_but_allows_status(self):
        commands=[['enroll'],['up'],['down'],['host-stop','dynweb01'],['host-start','dynweb01'],
                  ['dhcp-server','stop'],['dhcp-server','start'],['dhcp-lease','release','dynweb01'],
                  ['dhcp-lease','acquire','dynweb01'],['dhcp-move','dynweb01','10.77.1.25'],['break','web03','http'],['fix','web03','http']]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'dhcp-move.json').mkdir()
            with patch.object(presenter,'ROOT',root), patch.object(presenter,'read_pins') as pins, patch.object(presenter,'enroll') as enroll:
                for command in commands:
                    with self.subTest(command=command):self.assertEqual(presenter.main(command),1)
                pins.assert_not_called();enroll.assert_not_called()
            pins={d.name:{} for d in self.catalog.devices if d.kind=='linux'}
            with patch.object(presenter,'ROOT',root), patch.object(presenter,'read_pins',return_value=pins), patch.object(presenter,'inspect',return_value={'State':{'Running':False}}) as inspect:
                self.assertEqual(presenter.main(['status']),0)
                self.assertEqual(inspect.call_count,14)
    def test_moved_dhcp_client_uses_the_saved_reservation(self):
        device=self.catalog.target('dynweb01');pins={'dhcp01':{'id':'a'*64}}
        with patch.object(presenter,'node',return_value={'target':'dhcp01','reservations':{'dynweb01':'10.77.1.25'},'supervisor_state':'RUNNING'}):
            self.assertEqual(presenter.reserved_address(self.catalog,pins,device),'10.77.1.25')
    def test_dhcp_docker_adapter_uses_pinned_processes_and_fixed_operations(self):
        names=['dhcp01']+[d.name for d in self.catalog.devices if d.mode=='dhcp']
        pins={name:{'id':format(i,'064x')} for i,name in enumerate(names,1)}
        pids={name:100+i for i,name in enumerate(names)}
        def inspect(device,pin):return {'State':{'Running':True,'Pid':pids[device.name]}}
        reservations={d.name:d.address for d in self.catalog.devices if d.mode=='dhcp'}
        def request(device,pin,value):
            if value['operation']=='server-observe':return {'target':'dhcp01','reservations':reservations,'lease_seconds':600,'supervisor_state':'RUNNING'}
            if device.name=='dhcp01':return {'target':'dhcp01','network_safe':True,'addresses':['10.77.1.2']}
            return {'target':device.name,'network_safe':True,'observed_mac':device.mac,'client_id':device.client_id,'addresses':[device.address]}
        stat='1 (container) '+' '.join(['0']*19+['123'])
        with patch.object(presenter,'check_host_network'),patch.object(presenter,'inspect',side_effect=inspect),patch.object(presenter,'observe_process') as observe,patch('pathlib.Path.read_text',return_value=stat),patch.object(presenter,'node_request',side_effect=request) as node_request:
            lab=presenter.DockerDhcpLab(self.catalog,pins)
            state=lab.snapshot()
            self.assertEqual(state['reservations'],reservations)
            self.assertEqual(state['pins'],{name:pin['id'] for name,pin in pins.items()})
            lab.release('dynweb01')
            self.assertEqual(node_request.call_args.args[2],{'operation':'lease-release'})
            pids['dynweb01']+=1
            with self.assertRaises(ValueError):lab.release('dynweb01')
            self.assertTrue(observe.called)
    def test_move_and_recovery_dispatch_to_the_owned_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value={'owned':'pins'}),patch.object(presenter,'DockerDhcpLab') as lab,patch.object(presenter.dhcp_control,'move') as move:
                self.assertEqual(presenter.main(['dhcp-move','dynweb01','10.77.1.25']),0)
                move.assert_called_once_with(root,unittest.mock.ANY,lab.return_value,'dynweb01','10.77.1.25')
            (root/'dhcp-move.json').write_text('pending')
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value={'owned':'pins'}),patch.object(presenter,'DockerDhcpLab') as lab,patch.object(presenter.dhcp_control,'recover') as recover:
                self.assertEqual(presenter.main(['dhcp-recover']),0)
                recover.assert_called_once_with(root,unittest.mock.ANY,lab.return_value)
    def test_move_runs_through_docker_adapter_and_restores_on_failure(self):
        from defense.test_dhcp_control import FakeLab
        fake=FakeLab(self.catalog)
        names=['dhcp01']+[d.name for d in self.catalog.devices if d.mode=='dhcp']
        pins={name:{'id':fake.pins[name]} for name in names}
        pids={name:100+i for i,name in enumerate(names)}
        def inspect(device,pin):return {'State':{'Running':True,'Pid':pids[device.name]}}
        def request(device,pin,value):
            op=value['operation']
            if op=='server-observe':return {'target':'dhcp01','reservations':dict(fake.reservations),'lease_seconds':600,'supervisor_state':'RUNNING'}
            if op=='server-config':fake.configure(value['reservations'])
            elif op=='lease-release':fake.release(device.name)
            elif op=='lease-acquire':fake.acquire(device.name,value['expected_address'])
            if device.name=='dhcp01':return {'target':'dhcp01','network_safe':True,'addresses':['10.77.1.2']}
            return {'target':device.name,'network_safe':True,'observed_mac':device.mac,'client_id':device.client_id,'addresses':list(fake.addresses[device.name])}
        stat='1 (container) '+' '.join(['0']*19+['123'])
        with tempfile.TemporaryDirectory() as directory,patch.object(presenter,'ROOT',Path(directory)),patch.object(presenter,'check_host_network'),patch.object(presenter,'inspect',side_effect=inspect),patch.object(presenter,'observe_process'),patch('pathlib.Path.read_text',return_value=stat),patch.object(presenter,'node_request',side_effect=request),patch.object(presenter,'remove_default_route') as route,patch.object(presenter,'node') as baseline:
            lab=presenter.DockerDhcpLab(self.catalog,pins)
            fake.fail='acquire'
            with self.assertRaises(RuntimeError):presenter.dhcp_control.move(Path(directory),self.catalog,lab,'dynweb01','10.77.1.25')
            self.assertEqual(fake.addresses['dynweb01'],['10.77.1.20'])
            self.assertFalse((Path(directory)/'dhcp-move.json').exists())
            lab.restore_baseline()
            route.assert_called_with(pins['dhcp01'])
            self.assertEqual(baseline.call_args.args[2],'baseline')
            presenter.dhcp_control.move(Path(directory),self.catalog,lab,'dynweb01','10.77.1.25')
            self.assertEqual(fake.addresses['dynweb01'],['10.77.1.25'])
class ParentAttachmentCheckTests(unittest.TestCase):
    def observe(self,foreign=False):
        links=[{'ifname':'vboxnet1','ifindex':7},{'ifname':'eno1','ifindex':2}]
        networks={'a':{'Name':'pinpoint274-host-test','Driver':'macvlan','Options':{'parent':'vboxnet1'}},
                  'b':{'Name':'x','Driver':'macvlan','Options':{'parent':'vboxnet1'}} if foreign else {'Name':'x','Driver':'bridge','Options':{}}}
        def run(argv,**kwargs):
            if argv[:2]==['ip','-j']:return json.dumps(links)
            if argv[:3]==['docker','network','ls']:return 'a\nb\n'
            if argv[:3]==['docker','network','inspect']:return json.dumps([networks[n] for n in argv[3:]])
            raise AssertionError(argv)
        return run
    def test_owned_network_only_is_accepted_and_foreign_network_refused(self):
        with patch.object(presenter,'run',side_effect=self.observe()):presenter.check_parent_attachments()
        with patch.object(presenter,'run',side_effect=self.observe(True)):
            with self.assertRaises(ValueError):presenter.check_parent_attachments()
class PortControlTests(unittest.TestCase):
    def setUp(self):
        self.catalog=presenter.load_catalog();self.pins={d.name:{'id':'a'*64,'image':'sha256:'+'b'*64} for d in self.catalog.devices if d.kind=='linux'}
        self.extras=[];self.commands=[]
    def exec_helper(self,argv,**kwargs):
        self.commands.append(argv)
        if argv[:2]!=['docker','exec'] or argv[3:5]!=['python3','-c']:raise AssertionError(argv)
        action=argv[6]
        if action=='list':return ''.join('%d\n'%p for p in self.extras)
        if action=='open':self.extras.append(int(argv[8]))
        if action=='close':self.extras.remove(int(argv[7]))
        return ''
    def node(self,device,pin,operation):
        listeners=[{'protocol':'tcp','port':p} for p in [80,443]+self.extras]
        return {'network_safe':True,'addresses':[device.address],'listeners':listeners,'services':[]}
    def patches(self):
        return (patch.object(presenter,'check_host_network'),patch.object(presenter,'inspect'),patch.object(presenter,'node',side_effect=self.node),
                patch.object(presenter,'run',side_effect=self.exec_helper))
    def call(self,function,*args):
        a,b,c,d=self.patches()
        with a,b,c,d:return function(self.catalog,self.pins,*args)
    def test_open_close_list_and_restore_extra_listeners(self):
        self.call(presenter.port_open,'web03','http',8088)
        self.call(presenter.port_open,'web03','tcp',8089)
        self.assertEqual(self.call(presenter.port_list,'web03'),{'baseline':[80,443],'extra':[8088,8089]})
        self.call(presenter.port_close,'web03',8088)
        self.assertEqual(self.extras,[8089])
        self.call(presenter.port_restore,'web03')
        self.assertEqual(self.extras,[])
    def test_wrong_target_reserved_baseline_and_colliding_ports_are_refused_before_any_exec(self):
        for args in [('win01','http',8088),('foreign','http',8088),('web03','http',5693),('web03','http',2223),('web03','http',18080),
                     ('web03','ftp',8088),('web03','http',80),('web03','http',443),('web03','tcp',22),('web03','http',True),('web03','http','8088')]:
            with self.subTest(args=args),self.assertRaises(ValueError):self.call(presenter.port_open,*args)
        self.assertEqual(self.commands,[])
        self.call(presenter.port_open,'web03','http',8088)
        with self.assertRaises(ValueError):self.call(presenter.port_open,'web03','http',8088)
    def test_close_refuses_ports_that_are_not_extra_listeners(self):
        for port in (80,5693,8088):
            with self.subTest(port=port),self.assertRaises(ValueError):self.call(presenter.port_close,'web03',port)
        self.assertFalse([c for c in self.commands if c[6]=='close'])
    def test_failed_open_is_rolled_back_so_no_listener_is_left_behind(self):
        original=self.node
        def silent(device,pin,operation):
            value=original(device,pin,operation)
            value['listeners']=[l for l in value['listeners'] if l['port']!=8088]
            return value
        a,b,c,d=self.patches()
        with a,b,patch.object(presenter,'node',side_effect=silent),d:
            with self.assertRaises(ValueError):presenter.port_open(self.catalog,self.pins,'web03','http',8088)
        self.assertEqual(self.extras,[])
    def test_restore_all_visits_every_linux_target_and_ports_commands_are_dispatched(self):
        with patch.object(presenter,'port_restore') as restore:
            presenter.port_restore_all(self.catalog,self.pins)
        self.assertEqual([c.args[2] for c in restore.call_args_list],[d.name for d in self.catalog.devices if d.kind=='linux'])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value=self.pins),patch.object(presenter,'port_open') as opened:
                self.assertEqual(presenter.main(['ports','open','web03','http','8088']),0)
                opened.assert_called_once()
            (root/'dhcp-move.json').write_text('pending')
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value=self.pins),patch.object(presenter,'port_open') as opened,patch.object(presenter,'port_list',return_value={'baseline':[],'extra':[]}) as listed:
                self.assertEqual(presenter.main(['ports','open','web03','http','8088']),1)
                opened.assert_not_called()
                self.assertEqual(presenter.main(['ports','list','web03']),0)
class AddressModeCommandTests(unittest.TestCase):
    def setUp(self):
        self.catalog=presenter.load_catalog();self.pins={d.name:{'id':'a'*64,'image':'sha256:'+'b'*64} for d in self.catalog.devices if d.kind=='linux'}
        self.addresses={d.name:[d.address] for d in self.catalog.devices if d.mode=='dhcp'}
        self.commands=[];self.requests=[]
    def fake_run(self,argv,**kwargs):
        self.commands.append(argv)
        if argv[:5]==['docker','exec','--privileged','a'*64,'ip']:
            verb,address=argv[6],argv[7].split('/')[0]
            if verb=='add':self.addresses['dynweb01']=[address]
            if verb=='del':self.addresses['dynweb01']=[]
        return ''
    def node(self,device,pin,operation):
        if device.name=='dhcp01':return {'network_safe':True,'addresses':['10.77.1.2'],'services':[{'program':'dhcp','state':'RUNNING'}]}
        return {'network_safe':True,'addresses':list(self.addresses[device.name]),'services':[]}
    def request(self,device,pin,value):
        self.requests.append((device.name,value['operation']))
        if value['operation']=='lease-release':self.addresses[device.name]=[]
        if value['operation']=='lease-acquire':self.addresses[device.name]=[value['expected_address']]
        return {}
    def patches(self):
        return (patch.object(presenter,'check_host_network'),patch.object(presenter,'inspect'),patch.object(presenter,'node',side_effect=self.node),
                patch.object(presenter,'node_request',side_effect=self.request),patch.object(presenter,'run',side_effect=self.fake_run),
                patch.object(presenter,'reserved_address',side_effect=lambda catalog,pins,device:device.address))
    def test_static_then_dhcp_uses_fixed_ip_commands_and_the_node_lease_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700)
            a,b,c,d,e,f=self.patches()
            with patch.object(presenter,'ROOT',root),a,b,c,d,e,f:
                presenter.address_mode_set(self.catalog,self.pins,'dynweb01','static','10.77.1.15')
                self.assertEqual(self.addresses['dynweb01'],['10.77.1.15'])
                self.assertEqual(presenter.address_mode_show(self.catalog,self.pins,'dynweb01'),{'mode':'static','address':'10.77.1.15'})
                presenter.address_mode_set(self.catalog,self.pins,'dynweb01','dhcp',None)
                self.assertEqual(self.addresses['dynweb01'],['10.77.1.20'])
            ip_commands=[c for c in self.commands if c[:5]==['docker','exec','--privileged','a'*64,'ip']]
            self.assertEqual(ip_commands,[['docker','exec','--privileged','a'*64,'ip','addr','add','10.77.1.15/27','dev','eth0'],
                                          ['docker','exec','--privileged','a'*64,'ip','addr','del','10.77.1.15/27','dev','eth0']])
    def test_address_already_held_by_another_client_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700);self.addresses['dynapp01']=['10.77.1.15']
            a,b,c,d,e,f=self.patches()
            with patch.object(presenter,'ROOT',root),a,b,c,d,e,f:
                with self.assertRaises(ValueError):presenter.address_mode_set(self.catalog,self.pins,'dynweb01','static','10.77.1.15')
            self.assertEqual(self.commands,[])
    def test_commands_dispatch_and_an_address_intent_blocks_other_mutations_but_not_show_or_recover(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700)
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value=self.pins),patch.object(presenter,'address_mode_set') as changed,patch.object(presenter,'address_mode_show',return_value={'mode':'dhcp','address':'10.77.1.20'}):
                self.assertEqual(presenter.main(['address-mode','static','dynweb01','10.77.1.15']),0)
                changed.assert_called_once_with(unittest.mock.ANY,self.pins,'dynweb01','static','10.77.1.15')
                (root/'address-mode.json').write_text('pending')
                self.assertEqual(presenter.main(['address-mode','dhcp','dynweb01']),1)
                self.assertEqual(presenter.main(['dhcp-move','dynweb01','10.77.1.25']),1)
                self.assertEqual(presenter.main(['dhcp-recover']),1)
                self.assertEqual(presenter.main(['address-mode','show','dynweb01']),0)
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value=self.pins),patch.object(presenter,'address_mode_recover') as recover:
                self.assertEqual(presenter.main(['address-mode','recover']),0)
                recover.assert_called_once()
class VmPinTests(unittest.TestCase):
    UUIDS={'appliance':'11111111-1111-4111-8111-111111111111','windows':'22222222-2222-4222-8222-222222222222'}
    def records(self,extra=None):
        items=[{'uuid':self.UUIDS['appliance'],'state':'running','adapters':[{'slot':2,'type':'hostonly','network':'vboxnet1','mac':'08:00:27:fa:10:0a'}]},
               {'uuid':self.UUIDS['windows'],'state':'running','adapters':[{'slot':1,'type':'hostonly','network':'vboxnet1','mac':'02:77:01:00:00:02'}]}]
        return items+(extra or [])
    def names(self,windows='pinpoint-defense-win01'):
        return '"Pinpoint-Final" {%s}\n"%s" {%s}\n'%(self.UUIDS['appliance'],windows,self.UUIDS['windows'])
    def test_pins_come_from_exactly_the_two_named_host_only_members(self):
        pins=presenter.derive_vm_pins(self.records(),self.names())
        self.assertEqual(pins,{'appliance':{'uuid':self.UUIDS['appliance'],'slot':2,'mac':'08:00:27:fa:10:0a'},
                               'windows':{'uuid':self.UUIDS['windows'],'slot':1,'mac':'02:77:01:00:00:02'}})
    def test_wrong_names_or_extra_members_are_not_pinned(self):
        extra={'uuid':'33333333-3333-4333-8333-333333333333','state':'poweroff','adapters':[{'slot':1,'type':'hostonly','network':'vboxnet1','mac':'08:00:27:aa:bb:03'}]}
        with self.assertRaises(ValueError):presenter.derive_vm_pins(self.records(),self.names('other-vm'))
        with self.assertRaises(ValueError):presenter.derive_vm_pins(self.records([extra]),self.names())
    def test_preflight_refuses_a_changed_vm_membership(self):
        pins=presenter.derive_vm_pins(self.records(),self.names())
        changed=self.records();changed[0]['state']='paused'
        counters=iter([(8000,40000,(0,0)),(8000,40000,(0,0))])
        with patch.object(presenter,'check_host_network'):
            with self.assertRaises(ValueError):
                presenter.preflight({},counters=lambda:next(counters),inventory=lambda:['10.77.1.0/27'],sleep=lambda s:None,vm_pins=pins,vm_records=lambda:changed)
class PreflightTests(unittest.TestCase):
    def run_preflight(self,available=8000,disk=40000,swap=(0,0),occupied=None,pins=None):
        occupied=occupied if occupied is not None else ['192.168.57.0/24','10.77.1.0/27']
        counters=iter([(available,disk,(100,200)),(available,disk,(100+swap[0],200+swap[1]))])
        vms=VmPinTests();records=vms.records()
        with patch.object(presenter,'check_host_network') as network:
            result=presenter.preflight({},counters=lambda:next(counters),inventory=lambda:occupied,sleep=lambda seconds:None,
                                       vm_pins=presenter.derive_vm_pins(records,vms.names()),vm_records=lambda:records)
        return network,result
    def test_healthy_host_reports_measurements(self):
        network,result=self.run_preflight()
        network.assert_called_once()
        self.assertEqual(result,{'available_mib':8000,'free_disk_mib':40000,'swap_pages_per_second':0.0})
    def test_collision_low_memory_low_disk_and_swap_thrash_are_refused(self):
        for kwargs in ({'occupied':['10.77.1.0/27','10.0.0.0/8']},{'available':3000},{'disk':1000},{'swap':(400,400)}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):self.run_preflight(**kwargs)
    def test_preflight_command_is_read_only_and_ignores_a_dhcp_intent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'dhcp-move.json').write_text('pending')
            with patch.object(presenter,'ROOT',root),patch.object(presenter,'read_pins',return_value={}),patch.object(presenter,'read_vm_pins',return_value={}),patch.object(presenter,'preflight',return_value={'available_mib':1,'free_disk_mib':2,'swap_pages_per_second':0.0}) as check:
                self.assertEqual(presenter.main(['preflight']),0)
                check.assert_called_once()
if __name__=='__main__':unittest.main()
