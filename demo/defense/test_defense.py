"""Offline defense-lab contracts; no Docker, VM, SSH or network execution."""
import copy
from contextlib import nullcontext
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog, parse_catalog, listener_request, render_dnsmasq
from defense.preflight import check_resources, reject_overlaps, validate_vm, validate_runtime, read_private_json
from defense.preflight import validate_vm_macs
from defense.controller import main


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()
        self.raw = json.loads(Path(__file__).with_name('manifest.json').read_text())

    def test_one_fifteen_device_catalog_and_five_real_dhcp_identities(self):
        self.assertEqual(len(self.catalog.devices), 15)
        self.assertEqual(sum(d.kind == 'linux' for d in self.catalog.devices), 14)
        clients = [d for d in self.catalog.devices if d.mode == 'dhcp']
        self.assertEqual({d.name for d in clients}, {'dynweb01','dynapp01','dynmail01','dynsnmp01','dynweb02'})
        self.assertEqual(len({d.mac for d in self.catalog.devices}), 15)
        self.assertEqual(len({d.client_id for d in clients}), 5)
        self.assertEqual(self.catalog.target('win01').mac, '02:77:01:00:00:02')
        self.assertEqual(self.catalog.target('win01').address, '10.77.1.3')
        self.assertEqual(str(self.catalog.network), '10.77.1.0/27')

    def test_catalog_contains_required_real_protocols_and_ports(self):
        expected = {'dhcp01':('dhcp','udp',67),'win01':('ncpa','tcp',5693),
                    'web03':('https','tcp',443),'api02':('http','tcp',8081),
                    'ftp01':('ftp','tcp',21),'mail01':('imap','tcp',143),
                    'dns01':('dns','udp',53),'db01':('pgsql','tcp',5432),
                    'snmp02':('snmp','udp',161),'ssh-alt02':('ssh','tcp',2223),
                    'dynweb01':('http','tcp',80),'dynapp01':('http','tcp',8080),
                    'dynmail01':('smtp','tcp',25),'dynsnmp01':('snmp','udp',161),
                    'dynweb02':('http','tcp',9090)}
        for target, item in expected.items():
            self.assertIn(item, {(p.service,p.protocol,p.port) for p in self.catalog.target(target).listeners})

    def test_manifest_rejects_missing_foreign_duplicate_and_misplaced_devices(self):
        for mutate in [lambda d:d['devices'].pop(),
                       lambda d:d['devices'][0].update(name='foreign'),
                       lambda d:d['devices'][1].update(mac=d['devices'][0]['mac']),
                       lambda d:d['devices'][0].update(address='10.77.1.20'),
                       lambda d:d.update(network='192.168.1.0/24'),
                       lambda d:d['devices'][0]['listeners'][0].update(port=True),
                       lambda d:d['devices'][2]['listeners'][0].update(port=5693)]:
            data=copy.deepcopy(self.raw);mutate(data)
            with self.assertRaises(ValueError):parse_catalog(data)

    def test_listener_validation_rejects_wrong_target_reserved_injection_and_collision(self):
        for args in [('win01','http',8088),('foreign','http',8088),
                     ('web03','http;id',8088),('web03','http',5693),
                     ('web03','http',2260),('web03','http',18080),
                     ('web03','ftp',8021),('web03','http',True),
                     ('dhcp01','dhcp',67)]:
            with self.subTest(args=args),self.assertRaises(ValueError):
                listener_request(self.catalog,*args)
        with self.assertRaises(ValueError):
            listener_request(self.catalog,'web03','http',8088, occupied=[('tcp',8088,'tcp')])

    def test_listener_baseline_and_high_examples_have_scan_eligibility(self):
        self.assertEqual(listener_request(self.catalog,'ssh-alt02','ssh',2223).plugin,'check_ssh')
        self.assertTrue(self.catalog.scan_eligible(listener_request(self.catalog,'web03','http',8088)))
        self.assertFalse(self.catalog.scan_eligible(listener_request(self.catalog,'web03','http',20080)))

    def test_dnsmasq_only_known_clients_on_demo_interface_without_gateway(self):
        reservations={d.name:d.address for d in self.catalog.devices if d.mode=='dhcp'}
        config=render_dnsmasq(self.catalog,reservations)
        self.assertIn('interface=eth0\nbind-interfaces\n',config)
        self.assertIn('dhcp-range=10.77.1.20,10.77.1.29,255.255.255.224,600s',config)
        self.assertIn('dhcp-option=option:router\n',config)
        self.assertIn('dhcp-ignore=tag:!known',config)
        self.assertEqual(config.count('dhcp-host='),5)
        reservations['dynweb02']=reservations['dynweb01']
        with self.assertRaises(ValueError):render_dnsmasq(self.catalog,reservations)
        reservations['dynweb02']='10.77.1.15'
        with self.assertRaises(ValueError):render_dnsmasq(self.catalog,reservations)


def vm_fixture(role='target_host', state='poweroff'):
    names={'target_host':'pinpoint-defense-targets','appliance':'pinpoint-qa-appliance','windows':'pinpoint-defense-win01'}
    nics=[{'slot':1,'type':'nat','network':'','mac':'02:77:01:fe:00:01','promiscuous':'deny'},
          {'slot':2,'type':'intnet','network':'pinpoint-defense','mac':'02:77:01:fe:00:02','promiscuous':'allow-vms' if role=='target_host' else 'deny'}]
    forwards=[{'host':'127.0.0.1','port':2260,'guest_port':22,'protocol':'tcp'}]
    if role=='appliance':forwards=[{'host':'127.0.0.1','port':2250,'guest_port':22,'protocol':'tcp'}, {'host':'127.0.0.1','port':18080,'guest_port':80,'protocol':'tcp'}]
    if role=='windows':
        nics=[{'slot':1,'type':'intnet','network':'pinpoint-defense','mac':'02:77:01:00:00:02','promiscuous':'deny'}];forwards=[]
    return {'name':names[role],'uuid':'11111111-1111-4111-8111-111111111111','owner':'a'*48,
            'state':state,'nics':nics,'forwards':forwards}


class PreflightTests(unittest.TestCase):
    def test_only_collisions_reject_including_host_routes_docker_vpn_and_default_unknown(self):
        reject_overlaps(['10.77.0.0/28','10.78.0.0/24','10.79.0.0/28','172.17.0.0/16'])
        for occupied in [['10.77.1.0/24'],['10.77.1.3/32'],['10.0.0.0/8'],['0.0.0.0/0'],['invalid']]:
            with self.assertRaises(ValueError):reject_overlaps(occupied)

    def test_resources_count_only_new_vm_allocations_and_keep_reserve(self):
        self.assertEqual(check_resources(12800,70000,[4096,2048,3072],60000),12800)
        check_resources(6656,70000,[3072],60000)
        for available,disk,alloc,budget in [(8940,70000,[4096,2048,3072],60000),
                                           (6655,70000,[3072],60000),
                                           (20000,59999,[3072],60000)]:
            with self.assertRaises(ValueError):check_resources(available,disk,alloc,budget)

    def test_vm_refuses_identity_foreign_adapter_forward_and_network_drift(self):
        baseline=vm_fixture();macs=[n['mac'] for n in baseline['nics']]
        validate_vm(baseline,'target_host',baseline['uuid'],baseline['owner'],macs)
        mutations=[lambda d:d.update(uuid='22222222-2222-4222-8222-222222222222'),
                   lambda d:d.update(owner='foreign'),lambda d:d.update(name='foreign'),
                   lambda d:d['nics'][1].update(type='bridged'),
                   lambda d:d['nics'][1].update(network='pinpoint-demo'),
                   lambda d:d['nics'][1].update(mac='02:77:01:fe:01:02'),
                   lambda d:d['nics'][1].update(promiscuous='allow-all'),
                   lambda d:d['nics'].append({'slot':3,'type':'nat','network':'','mac':'02:00:00:00:00:03'}),
                   lambda d:d['forwards'][0].update(host='0.0.0.0'),
                   lambda d:d['forwards'].append({'host':'127.0.0.1','port':8080,'guest_port':80,'protocol':'tcp'})]
        for mutate in mutations:
            data=copy.deepcopy(baseline);mutate(data)
            with self.assertRaises(ValueError):validate_vm(data,'target_host',baseline['uuid'],baseline['owner'],macs)

    def test_windows_has_no_nat_or_bridged_nic(self):
        data=vm_fixture('windows');macs=[n['mac'] for n in data['nics']]
        validate_vm(data,'windows',data['uuid'],data['owner'],macs)
        data['nics'][0]['type']='nat'
        with self.assertRaises(ValueError):validate_vm(data,'windows',data['uuid'],data['owner'],macs)

    def test_proposed_container_mac_cannot_already_belong_to_vm_nic(self):
        catalog=load_catalog();windows=vm_fixture('windows')
        validate_vm_macs(catalog,[windows])
        foreign=vm_fixture();foreign['name']='foreign';foreign['nics'][0]['mac']=catalog.target('dynweb01').mac
        with self.assertRaises(ValueError):validate_vm_macs(catalog,[windows,foreign])
        foreign['nics'][0]['mac']=windows['nics'][0]['mac']
        with self.assertRaises(ValueError):validate_vm_macs(catalog,[windows,foreign])

    def test_runtime_requires_one_controller_exact_process_and_actual_nat_socket(self):
        data=vm_fixture(state='running')
        process={'pid':20,'uuid':data['uuid'],'parent':10}
        listeners={2260:[('127.0.0.1','socket:[99]')]}
        forwards={2260:[('127.0.0.1',22,'10.0.2.15')]}
        validate_runtime(data,[10],[process],listeners,forwards)
        for managers,procs,sockets,nat in [([], [process],listeners,forwards),
                                          ([10,11],[process],listeners,forwards),
                                          ([10],[dict(process,parent=11)],listeners,forwards),
                                          ([10],[process],{},forwards),
                                          ([10],[process],listeners,{}),
                                          ([10],[process],{2260:[('::','socket:[99]')]},forwards)]:
            with self.assertRaises(ValueError):validate_runtime(data,managers,procs,sockets,nat)
        data['state']='poweroff'
        with self.assertRaises(ValueError):validate_runtime(data,[10],[process],listeners,forwards)
        validate_runtime(data,[10],[],{}, {})

    def test_private_state_refuses_symlink_public_mode_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'state.json';path.write_text('{"ok":true}');path.chmod(0o600)
            self.assertEqual(read_private_json(path),{'ok':True})
            link=root/'link';link.symlink_to(path)
            with self.assertRaises(ValueError):read_private_json(link)
            path.chmod(0o644)
            with self.assertRaises(ValueError):read_private_json(path)
            path.chmod(0o600);path.write_text('bad')
            with self.assertRaises(ValueError):read_private_json(path)
            other=root/'actual';other.mkdir(mode=0o700);(other/'state.json').write_text('{}');(other/'state.json').chmod(0o600)
            parent=root/'alias';parent.symlink_to(other,target_is_directory=True)
            with self.assertRaises(ValueError):read_private_json(parent/'state.json')

    def test_manifest_cli_is_offline_and_labels_expectations(self):
        output=io.StringIO()
        with patch('subprocess.run',side_effect=AssertionError('unexpected external execution')),patch('sys.stdout',output):
            self.assertEqual(main(['manifest','--json']),0)
        data=json.loads(output.getvalue())
        self.assertEqual(data['device_count'],15)
        self.assertFalse(data['live_verified'])
        self.assertEqual(len(data['devices']),15)

    def test_public_cli_error_never_echoes_private_child_or_state_details(self):
        output=io.StringIO()
        with patch('defense.controller.qa_control.claim',return_value=nullcontext()), \
             patch('defense.controller.collect_preflight',side_effect=ValueError('SENTINEL_PRIVATE_AUTH')), \
             patch('sys.stderr',output):
            self.assertEqual(main(['preflight','--json']),1)
        self.assertNotIn('SENTINEL_PRIVATE_AUTH',output.getvalue())
        self.assertIn('unsafe/incomplete',output.getvalue())


if __name__=='__main__':unittest.main()
