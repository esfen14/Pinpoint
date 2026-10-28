"""Offline contracts for guest-only Compose/node operations; no live daemons."""
import copy
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense.compose import compose_document, compose_template
from defense.node import validate_request, validate_network, identity, supervisor_config, program_specs, atomic, server_config, main as node_main
from defense.preflight import reject_virtualbox_dhcp

CATALOG = load_catalog()


class ComposeTests(unittest.TestCase):
    def test_all_fourteen_linux_devices_have_no_docker_numbered_interface(self):
        doc=compose_document(CATALOG,'sha256:'+'a'*64,'b'*48)
        self.assertEqual(set(doc['services']),{d.name for d in CATALOG.devices if d.kind=='linux'})
        self.assertNotIn('networks',doc)
        for target,service in doc['services'].items():
            self.assertEqual(service['network_mode'],'none')
            self.assertNotIn('ports',service)
            self.assertNotIn('mac_address',service)
            self.assertNotIn('ipv4_address',service)
            self.assertNotIn('pid',service)
            self.assertNotIn('privileged',service)
            self.assertEqual(service['restart'],'no')
            self.assertNotIn('SYS_ADMIN',service.get('cap_add',[]))
            mounts={v['target']:v for v in service['volumes']}
            self.assertEqual(mounts['/identity']['source'],f'/var/lib/pinpoint-defense/identities/{target}')
            self.assertTrue(mounts['/etc/pinpoint-defense/context.json']['read_only'])
            self.assertTrue(all(not v['bind']['create_host_path'] for v in service['volumes']))
            self.assertEqual(service['labels']['org.pinpoint.defense.target'],target)

    def test_only_dhcp_roles_get_network_administration_capability(self):
        doc=compose_document(CATALOG,'sha256:'+'a'*64,'b'*48)
        for name,service in doc['services'].items():
            self.assertEqual('NET_ADMIN' in service.get('cap_add',[]), name=='dhcp01' or CATALOG.target(name).mode=='dhcp')

    def test_fixed_spike_can_start_two_distinct_macs_without_full_catalog(self):
        doc=compose_document(CATALOG,'sha256:'+'a'*64,'b'*48,spike=True)
        self.assertEqual(set(doc['services']),{'dhcp01','dynweb01'})
        self.assertNotEqual(CATALOG.target('dhcp01').mac,CATALOG.target('dynweb01').mac)

    def test_template_is_generated_from_catalog_and_has_no_secret_values(self):
        stored=json.loads(Path(__file__).with_name('compose.yaml').read_text())
        self.assertEqual(stored,compose_template(CATALOG))
        text=json.dumps(stored)
        self.assertNotIn('community_string',text)
        self.assertNotIn('PASSWORD',text)
        with self.assertRaises(ValueError):compose_document(CATALOG,'untrusted:latest','b'*48)
        with self.assertRaises(ValueError):compose_document(CATALOG,'sha256:'+'a'*64,'../foreign')


class NodeTests(unittest.TestCase):
    def test_host_container_context_requires_explicit_mode_and_matching_host_identity(self):
        from defense.node import container_context
        host={'version':2,'mode':'host-only','owner':'b'*48,
              'vm_uuid':'821464dc-e7ce-4067-8eec-5cb1c61d3632','parent_mac':'0a:00:27:00:00:01'}
        def read(path,*args,**kwargs):
            if str(path).endswith('/product_name'):return 'Physical laptop\n'
            if str(path).endswith('/product_uuid'):return host['vm_uuid']+'\n'
            raise AssertionError('Unexpected file read')
        with patch('os.geteuid',return_value=0),patch('pathlib.Path.is_file',return_value=True), \
             patch('pathlib.Path.read_text',read),patch('defense.node.read_private_json',return_value=host):
            self.assertEqual(container_context(),host)
        for changed in [dict(host,mode='bridge'),dict(host,version=1),dict(host,vm_uuid='foreign'),dict(host,parent_mac='bad')]:
            with patch('os.geteuid',return_value=0),patch('pathlib.Path.is_file',return_value=True), \
                 patch('pathlib.Path.read_text',read),patch('defense.node.read_private_json',return_value=changed):
                with self.assertRaises(ValueError):container_context()

    def test_invalid_commands_reject_before_subprocess_or_file_mutation(self):
        bad=[('web03',{'operation':'shell','command':'id'}),
             ('foreign',{'operation':'inspect'}),('win01',{'operation':'baseline'}),
             ('web03',{'operation':'server-stop'}),
             ('dynweb01',{'operation':'lease-acquire','expected_address':'192.168.1.1'}),
             ('dynweb01',{'operation':'lease-acquire','expected_address':'10.77.1.15'}),
             ('dynweb01',{'operation':'inspect','extra':'SENTINEL_SECRET'})]
        with patch('subprocess.run') as run:
            for target,data in bad:
                with self.subTest(target=target,data=data),self.assertRaises(ValueError):validate_request(CATALOG,target,data)
            run.assert_not_called()

    def test_dhcp_commands_are_confined_to_server_and_five_clients(self):
        reservations={d.name:d.address for d in CATALOG.devices if d.mode=='dhcp'}
        validate_request(CATALOG,'dhcp01',{'operation':'server-config','reservations':reservations,'lease_seconds':600})
        validate_request(CATALOG,'dynapp01',{'operation':'lease-acquire','expected_address':'10.77.1.25'})
        with self.assertRaises(ValueError):validate_request(CATALOG,'web03',{'operation':'lease-release'})

    def test_allocator_observation_is_server_only_and_read_only(self):
        self.assertEqual(validate_request(CATALOG,'dhcp01',{'operation':'server-observe'}),{'operation':'server-observe'})
        for target,request in [('web03',{'operation':'server-observe'}),('dhcp01',{'operation':'server-observe','extra':'bad'})]:
            with self.assertRaises(ValueError):validate_request(CATALOG,target,request)
        from defense.node import handle
        expected={'target':'dhcp01','reservations':{},'lease_seconds':600,'supervisor_state':'RUNNING'}
        with patch('defense.node.network',return_value=['10.77.1.2']),patch('defense.node.observe_server',return_value=expected) as observe,patch('defense.node.server_config') as mutate:
            self.assertEqual(handle(CATALOG,CATALOG.target('dhcp01'),{'operation':'server-observe'}),expected)
            observe.assert_called_once();mutate.assert_not_called()

    def test_allocator_observation_refuses_torn_or_unsafe_state(self):
        from defense.node import observe_server
        from defense.catalog import render_dnsmasq
        reservations={d.name:d.address for d in CATALOG.devices if d.mode=='dhcp'}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);saved=root/'reservations.json';config=root/'dhcp.conf'
            atomic(saved,json.dumps({'reservations':reservations,'lease_seconds':600}))
            atomic(config,render_dnsmasq(CATALOG,reservations,600)+'user=root\ngroup=root\n')
            running=type('Result',(),{'stdout':'dhcp RUNNING pid 123, uptime 0:01:00','returncode':0})()
            with patch('defense.node.DATA',root),patch('defense.node.supervisor',return_value=running):
                result=observe_server(CATALOG)
                self.assertEqual(result,{'target':'dhcp01','reservations':reservations,'lease_seconds':600,'supervisor_state':'RUNNING'})
                atomic(config,'partial')
                with self.assertRaises(ValueError):observe_server(CATALOG)
                config.unlink();config.symlink_to(saved)
                with self.assertRaises(ValueError):observe_server(CATALOG)
                config.unlink();atomic(config,render_dnsmasq(CATALOG,reservations,600)+'user=root\ngroup=root\n')
                config.chmod(0o644)
                with self.assertRaises(ValueError):observe_server(CATALOG)

    def test_allocator_observation_rejects_changes_and_inconsistent_supervisor(self):
        from defense.node import observe_server
        from defense.catalog import render_dnsmasq
        reservations={d.name:d.address for d in CATALOG.devices if d.mode=='dhcp'}
        moved=dict(reservations,dynweb01='10.77.1.25')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def write_settings(values):
                atomic(root/'reservations.json',json.dumps({'reservations':values,'lease_seconds':600}))
                atomic(root/'dhcp.conf',render_dnsmasq(CATALOG,values,600)+'user=root\ngroup=root\n')
            write_settings(reservations)
            running=type('Result',(),{'stdout':'dhcp RUNNING pid 123','returncode':0})()
            def change(*args,**kwargs):
                write_settings(moved)
                return running
            with patch('defense.node.DATA',root),patch('defense.node.supervisor',side_effect=change):
                with self.assertRaises(ValueError):observe_server(CATALOG)
            bad=type('Result',(),{'stdout':'dhcp RUNNING pid 123','returncode':1})()
            with patch('defense.node.DATA',root),patch('defense.node.supervisor',return_value=bad):
                with self.assertRaises(ValueError):observe_server(CATALOG)

    def test_peer_ping_is_fixed_and_cannot_accept_a_user_supplied_destination(self):
        self.assertEqual(validate_request(CATALOG,'web03',{'operation':'peer-ping'}),{'operation':'peer-ping'})
        with self.assertRaises(ValueError):validate_request(CATALOG,'win01',{'operation':'peer-ping'})
        with self.assertRaises(ValueError):validate_request(CATALOG,'web03',{'operation':'peer-ping','destination':'192.0.2.1'})

    def test_peer_ping_runs_only_bounded_icmp_to_the_fixed_windows_address(self):
        from defense.node import handle
        device=CATALOG.target('web03')
        with patch('defense.node.network',return_value=['10.77.1.4']),patch('defense.node.command',return_value=type('Result',(),{'returncode':0})()) as run:
            self.assertEqual(handle(CATALOG,device,{'operation':'peer-ping'}),{'target':'web03','peer':'win01','reachable':True})
            run.assert_called_once_with(['/bin/ping','-n','-I','eth0','-c','3','-W','2','10.77.1.3'],timeout=8,check=False)
        with patch('defense.node.network',return_value=[]),patch('defense.node.command') as run:
            with self.assertRaises(ValueError):handle(CATALOG,device,{'operation':'peer-ping'})
            run.assert_not_called()

    def test_network_requires_exact_own_mac_one_address_and_no_default_route(self):
        target=CATALOG.target('dynweb01')
        links=[{'ifname':'lo','address':'00:00:00:00:00:00','addr_info':[{'family':'inet','local':'127.0.0.1'}]},
               {'ifname':'eth0','address':target.mac,'addr_info':[{'family':'inet','local':'10.77.1.20','prefixlen':27}]}]
        self.assertEqual(validate_network(CATALOG,target,links,[]),['10.77.1.20'])
        for mutate, routes in [(lambda x:x[1].update(address='02:00:00:00:00:99'),[]),
                               (lambda x:x[1]['addr_info'].append({'family':'inet','local':'10.77.1.21','prefixlen':27}),[]),
                               (lambda x:None,[{'dst':'default','gateway':'10.0.2.2'}])]:
            data=copy.deepcopy(links);mutate(data)
            with self.assertRaises(ValueError):validate_network(CATALOG,target,data,routes)
        links[1]['addr_info']=[]
        validate_network(CATALOG,target,links,[],unaddressed=True)
        with self.assertRaises(ValueError):validate_network(CATALOG,target,links,[])

    def test_identity_is_persistent_and_private_and_foreign_identity_refuses(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=CATALOG.target('dynweb01')
            def keygen(argv,**kwargs):
                path=Path(argv[argv.index('-f')+1]);path.write_text('PRIVATE_SENTINEL');path.chmod(0o600)
                Path(str(path)+'.pub').write_text('ssh-ed25519 PUBLIC_SENTINEL')
            with patch('defense.node.command',side_effect=keygen) as run:
                first=identity(root,target,'b'*48);second=identity(root,target,'b'*48)
                self.assertEqual(first,second)
                self.assertEqual(run.call_count,1)
                self.assertNotIn('PRIVATE_SENTINEL',json.dumps(first))
            (root/'ssh_host_ed25519_key').chmod(0o644)
            with self.assertRaises(ValueError):identity(root,target,'b'*48)
            with self.assertRaises(ValueError):identity(root,CATALOG.target('dynapp01'),'b'*48)

    def test_public_daemon_config_remains_readable_under_private_umask(self):
        with tempfile.TemporaryDirectory() as folder:
            old=os.umask(0o077)
            try:
                path=Path(folder)/'postgresql.conf';atomic(path,'public settings\n',public=True)
                self.assertEqual(path.stat().st_mode&0o777,0o644)
            finally:os.umask(old)

    def test_server_reservation_move_preserves_other_clients_real_lease_evidence(self):
        reservations={d.name:d.address for d in CATALOG.devices if d.mode=='dhcp'}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            atomic(root/'reservations.json',json.dumps({'reservations':reservations,'lease_seconds':600}))
            first=CATALOG.target('dynweb01');second=CATALOG.target('dynapp01')
            atomic(root/'dhcp.leases',f'123 {first.mac} 10.77.1.20 first *\n456 {second.mac} 10.77.1.21 second *\n')
            # dnsmasq can create readable lease evidence inside the private data dir.
            (root/'dhcp.leases').chmod(0o644)
            moved=dict(reservations,dynweb01='10.77.1.25')
            with patch('defense.node.DATA',root),patch('defense.node.supervisor') as control:
                server_config(CATALOG,{'reservations':moved,'lease_seconds':600})
                self.assertNotIn(first.mac,(root/'dhcp.leases').read_text())
                self.assertIn(second.mac,(root/'dhcp.leases').read_text())
                self.assertEqual(control.call_count,2)

    def test_runtime_context_failure_precedes_identity_or_daemon_mutation(self):
        with patch('defense.node.container_context',side_effect=ValueError('SENTINEL_PRIVATE_DETAIL')), \
             patch('defense.node.identity') as mutate,patch('subprocess.run') as run,redirect_stderr(io.StringIO()) as error:
            self.assertEqual(node_main(['init','web03']),1)
            mutate.assert_not_called();run.assert_not_called()
            self.assertNotIn('SENTINEL_PRIVATE_DETAIL',error.getvalue())

    def test_control_refuses_changed_persistent_dhcp_client_identifier(self):
        target=CATALOG.target('dynweb01')
        saved={'target':target.name,'owner':'b'*48,'mac':target.mac,'client_id':'foreign-client'}
        with patch('defense.node.container_context',return_value={'owner':'b'*48}), \
             patch('defense.node.read_private_json',return_value=saved), \
             patch('sys.stdin',io.StringIO('{"operation":"inspect"}')), \
             patch('defense.node.handle') as handle,redirect_stderr(io.StringIO()):
            self.assertEqual(node_main(['control',target.name]),1)
            handle.assert_not_called()

    def test_every_protocol_uses_real_daemon_and_supervisor_keeps_groups_owned(self):
        commands=set()
        for device in CATALOG.devices:
            if device.kind!='linux':continue
            specs=program_specs(CATALOG,device)
            for value in specs.values():commands.add(Path(value[0]).name)
            cfg=supervisor_config(specs)
            self.assertIn('autostart=false',cfg)
            self.assertIn('stopasgroup=true',cfg)
            self.assertIn('killasgroup=true',cfg)
            self.assertNotIn('[inet_http_server]',cfg)
        for daemon in ['sshd','nginx','vsftpd','postfix','dovecot','snmpd','dnsmasq','runuser']:
            self.assertIn(daemon,commands)

    def test_virtualbox_cannot_supply_second_dhcp_allocator(self):
        reject_virtualbox_dhcp('NetworkName: HostInterfaceNetworking-vboxnet0\nEnabled: Yes\n')
        reject_virtualbox_dhcp('NetworkName: pinpoint-defense\nEnabled: No\n')
        with self.assertRaises(ValueError):reject_virtualbox_dhcp('NetworkName: pinpoint-defense\nEnabled: Yes\n')
        with self.assertRaises(ValueError):reject_virtualbox_dhcp('NetworkName: pinpoint-defense\n')


if __name__=='__main__':unittest.main()
