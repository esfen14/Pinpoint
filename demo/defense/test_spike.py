"""Offline two-target lifecycle, image provenance and fixed node-dispatch contracts."""
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense import bootstrap,guest
from defense.catalog import load_catalog
from defense.compose import compose_document
from defense.test_guest import fixture,CONTEXT,IMAGE

CATALOG=load_catalog()


class SpikeTests(unittest.TestCase):
    def test_manual_parent_has_only_pinned_mac_no_dhcp_or_addresses(self):
        text=bootstrap.parent_network(CONTEXT)
        self.assertIn('MACAddress='+CONTEXT['parent_mac'],text)
        self.assertIn('ActivationPolicy=manual',text)
        self.assertIn('DHCP=no',text)
        self.assertIn('LinkLocalAddressing=no',text)
        self.assertNotIn('Address=',text.replace('MACAddress=','MATCH='))
        with self.assertRaises(ValueError):bootstrap.parent_network(dict(CONTEXT,parent_mac='bad;sh'))

    def test_source_digest_tracks_changed_code_and_refuses_symlinked_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in bootstrap.RUNTIME_FILES:
                (root/name).write_text(name);(root/name).chmod(0o600)
            first=bootstrap.image_source_hash(root)
            (root/'node.py').write_text('changed')
            self.assertNotEqual(first,bootstrap.image_source_hash(root))
            (root/'node.py').unlink();(root/'node.py').symlink_to(root/'guest.py')
            with self.assertRaises(ValueError):bootstrap.image_source_hash(root)
        unit=bootstrap.build_unit()
        self.assertNotIn('ConditionPathExists=!',unit)
        self.assertIn('pinpoint-defense-ready.service',unit)

    def test_image_requires_pinned_hash_and_current_source_label(self):
        observed={'Id':IMAGE,'Config':{'Labels':{'org.pinpoint.defense.issue':'274','org.pinpoint.defense.source':'c'*64,'org.opencontainers.image.version':'24.04'}}}
        self.assertEqual(guest.validate_image(IMAGE,'c'*64,observed),observed['Config']['Labels'])
        for mutation in [lambda v:v.update(Id='sha256:'+'d'*64),lambda v:v['Config']['Labels'].update({'org.pinpoint.defense.source':'d'*64})]:
            data=copy.deepcopy(observed);mutation(data)
            with self.assertRaises(ValueError):guest.validate_image(IMAGE,'c'*64,data)

    def test_container_inherits_only_labels_from_exact_trusted_image_and_has_no_entrypoint_override(self):
        labels={'org.opencontainers.image.version':'24.04','org.pinpoint.defense.source':'c'*64}
        observed=fixture();observed['Config']['Labels'].update(labels)
        self.assertEqual(guest.validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed,image_labels=labels),1234)
        observed['Config']['Labels']['org.opencontainers.image.version']='foreign'
        with self.assertRaises(ValueError):guest.validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed,image_labels=labels)
        observed=fixture();observed['Config']['Entrypoint']=['sh','-c']
        with self.assertRaises(ValueError):guest.validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed)

    def test_stopped_container_can_be_validated_without_adopting_foreign_persistent_state(self):
        observed=fixture();observed['State'].update(Running=False,Pid=0)
        self.assertEqual(guest.validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed,allow_stopped=True),0)
        observed['Mounts'][0]['Source']='/foreign'
        with self.assertRaises(ValueError):guest.validate_container(CATALOG,CONTEXT,IMAGE,'dynweb01',observed,allow_stopped=True)

    def test_private_compose_must_match_the_generated_two_target_document(self):
        expected=compose_document(CATALOG,IMAGE,CONTEXT['owner'],spike=True)
        guest.validate_spike_document(CATALOG,CONTEXT,IMAGE,expected)
        for change in [lambda v:v['services'].update(foreign={}),lambda v:v['services']['dhcp01'].update(network_mode='host')]:
            document=copy.deepcopy(expected);change(document)
            with self.assertRaises(ValueError):guest.validate_spike_document(CATALOG,CONTEXT,IMAGE,document)

    def test_spike_start_refuses_foreign_container_before_compose_link_or_exec(self):
        document=compose_document(CATALOG,IMAGE,CONTEXT['owner'],spike=True)
        with patch.object(guest,'read_private_json',return_value=document),patch.object(guest,'trusted_image',return_value={}),patch.object(guest,'command',return_value=SimpleNamespace(stdout='foreign-container\n')) as run:
            with self.assertRaises(ValueError):guest.spike_up(CATALOG,CONTEXT,IMAGE,'enp0s8')
            self.assertTrue(all(c.args[0][:3]==['docker','ps','-a'] for c in run.call_args_list))
        with patch.object(guest,'read_private_json',return_value={}),patch.object(guest,'command') as run:
            with self.assertRaises(ValueError):guest.spike_up(CATALOG,CONTEXT,IMAGE,'enp0s8')
            run.assert_not_called()

    def test_docker_restart_probe_refuses_any_container_before_service_mutation(self):
        with patch.object(guest,'guest_context',return_value=(CONTEXT,IMAGE,'enp0s8')),patch.object(guest,'command',return_value=SimpleNamespace(stdout='container-id\n')) as run:
            with self.assertRaises(ValueError):guest.verify_restart()
            self.assertNotIn(['systemctl','restart','docker.service'],[c.args[0] for c in run.call_args_list])
        with patch.object(guest,'guest_context',return_value=(CONTEXT,IMAGE,'enp0s8')),patch.object(guest,'command',return_value=SimpleNamespace(stdout='')) as run,patch.object(guest,'host_status',return_value={'safe':True}):
            self.assertTrue(guest.verify_restart()['safe'])
            self.assertIn(['systemctl','restart','docker.service'],[c.args[0] for c in run.call_args_list])

    def test_reset_spike_removes_only_exact_owned_containers_then_rebuilds(self):
        dhcp=fixture('dhcp01');web=fixture('dynweb01')
        labels={'org.pinpoint.defense.issue':'274','org.pinpoint.defense.source':'c'*64}
        dhcp['Config']['Labels'].update(labels);web['Config']['Labels'].update(labels)
        def execute(argv,**kwargs):
            if argv==['docker','ps','-a','--format','{{.Names}}']:
                return SimpleNamespace(stdout='pinpoint-defense274-dhcp01\npinpoint-defense274-dynweb01\n')
            if argv==['docker','image','inspect',IMAGE]:
                return SimpleNamespace(stdout=json.dumps([{'Config':{'Labels':labels}}]))
            return SimpleNamespace(stdout='')
        with patch.object(guest,'owned_context',return_value=CONTEXT),patch.object(guest,'management_observation'),patch.object(guest,'read_private_json',return_value={'image':IMAGE}),patch.object(guest,'observe_container',side_effect=[dhcp,web]),patch.object(guest,'command',side_effect=execute) as run:
            self.assertTrue(guest.reset_spike()['image_rebuilt'])
            self.assertIn(['docker','rm','-f','c'*64], [c.args[0] for c in run.call_args_list])
            self.assertIn(['/usr/bin/python3','/opt/pinpoint-defense/bootstrap.py','build'], [c.args[0] for c in run.call_args_list])

    def test_reset_spike_refuses_foreign_container_without_removal_or_build(self):
        with patch.object(guest,'owned_context',return_value=CONTEXT),patch.object(guest,'management_observation'),patch.object(guest,'read_private_json',return_value={'image':IMAGE}),patch.object(guest,'command',return_value=SimpleNamespace(stdout='foreign\n')) as run:
            with self.assertRaises(ValueError):guest.reset_spike()
            self.assertNotIn(['docker','rm','-f','foreign'], [c.args[0] for c in run.call_args_list])
            self.assertNotIn(['/usr/bin/python3','/opt/pinpoint-defense/bootstrap.py','build'], [c.args[0] for c in run.call_args_list])

    def test_checked_node_dispatch_uses_container_id_and_json_stdin_only(self):
        result={'target':'dynweb01','network_safe':True,'network_reason':None,'addresses':['10.77.1.20'],'mac':CATALOG.target('dynweb01').mac,'client_id':CATALOG.target('dynweb01').client_id,'listeners':[],'services':[]}
        with patch.object(guest,'observe_container',return_value=fixture()),patch.object(guest,'trusted_image',return_value={}),patch.object(guest,'command',return_value=SimpleNamespace(stdout=json.dumps(result))) as run:
            self.assertEqual(guest.node_request(CATALOG,CONTEXT,IMAGE,'dynweb01',{'operation':'inspect'}),result)
            args=run.call_args.args[0]
            self.assertEqual(args[:4],['docker','exec','-i','c'*64])
            self.assertEqual(json.loads(run.call_args.kwargs['input_text']),{'operation':'inspect'})

    def test_node_inspection_reason_is_fixed_and_not_a_raw_namespace_error(self):
        device=CATALOG.target('dynweb01')
        links=[{'ifname':'lo'},{'ifname':'eth0','address':device.mac,'addr_info':[]}]
        with patch('defense.node.command',return_value=SimpleNamespace(stdout=json.dumps(links))),patch('defense.node.network_reason',return_value='address'),patch('defense.node.supervisor',return_value=SimpleNamespace(stdout='')):
            result=__import__('defense.node',fromlist=['inspection']).inspection(CATALOG,device)
        self.assertFalse(result['network_safe'])
        self.assertEqual(result['network_reason'],'address')
        self.assertNotIn('secret',json.dumps(result))

    def test_node_network_reason_never_exposes_link_data(self):
        node=__import__('defense.node',fromlist=['network_reason'])
        device=CATALOG.target('dynweb01')
        for links,routes,expected in [([{'ifname':'lo'}],[],'interfaces'),([{'ifname':'lo'},{'ifname':'eth0','address':'02:00:00:00:00:01','addr_info':[]}],[],'mac'),([{'ifname':'lo'},{'ifname':'eth0','address':device.mac,'addr_info':[]}],[{'dst':'default'}],'default-route')]:
            with patch('defense.node.command',side_effect=[SimpleNamespace(stdout=json.dumps(links)),SimpleNamespace(stdout=json.dumps(routes))]):
                self.assertEqual(node.network_reason(CATALOG,device),expected)

    def test_node_protocol_refuses_shell_unknown_target_and_unowned_runtime_before_exec(self):
        with patch.object(guest,'observe_container') as observe,patch.object(guest,'command') as run:
            for target,request in [('dynweb01',{'operation':'shell','command':'id'}),('web03',{'operation':'inspect'}),('win01',{'operation':'inspect'})]:
                with self.assertRaises(ValueError):guest.node_request(CATALOG,CONTEXT,IMAGE,target,request)
            observe.assert_not_called();run.assert_not_called()
        observed=fixture();observed['Image']='sha256:'+'d'*64
        with patch.object(guest,'observe_container',return_value=observed),patch.object(guest,'command') as run:
            with self.assertRaises(ValueError):guest.node_request(CATALOG,CONTEXT,IMAGE,'dynweb01',{'operation':'inspect'})
            run.assert_not_called()


if __name__=='__main__':unittest.main()
