"""Offline tests for container creation commands; nothing runs Docker or sudo."""
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from targets import create
from targets.catalog import load_catalog

CATALOG=load_catalog()
ROOT=Path('/home/u/.local/share/pinpoint-defense/host-docker')
OWNER='a'*48
UUID='5fb21051-8a4f-45b0-a7f0-de3cedceab83'
MAC='0a:00:27:00:00:01'


def steps():
    return create.host_steps(CATALOG,ROOT,OWNER,UUID,MAC,'community-secret')


class HostStepTests(unittest.TestCase):
    def test_context_file_is_root_private_and_has_the_host_only_shape(self):
        writes=[s for s in steps() if s.input_text and s.argv[-1].endswith('context.json')]
        self.assertEqual(len(writes),1)
        self.assertEqual(json.loads(writes[0].input_text),{'version':2,'mode':'host-only','owner':OWNER,'vm_uuid':UUID,'parent_mac':MAC})
        self.assertEqual(writes[0].argv[:2],['sudo','tee'])
    def test_every_device_gets_private_identity_and_data_directories_where_the_presenter_expects(self):
        text=[' '.join(s.argv) for s in steps()]
        for device in CATALOG.devices:
            if device.kind!='linux':continue
            base=ROOT/'pilot-web03' if device.name=='web03' else ROOT/'pilot-catalog'/device.name
            for leaf in ('identity','data'):
                self.assertTrue(any('install -d -m 700 -o root -g root '+str(base/leaf) in t for t in text),(device.name,leaf))
    def test_snmp_community_is_written_only_for_the_catalog_snmp_pair_path(self):
        writes=[s for s in steps() if s.input_text=='community-secret\n']
        self.assertEqual(len(writes),1)
        self.assertTrue(writes[0].argv[-1].endswith('pilot-catalog/private/snmp-community'))


    def test_root_directory_is_user_owned_but_container_state_is_root_owned(self):
        first=steps()[0]
        self.assertEqual(first.argv[0],'mkdir');self.assertNotIn('sudo',first.argv)
        self.assertTrue(all(s.argv[0]=='sudo' for s in steps()[1:]))


class ContainerTests(unittest.TestCase):
    def test_static_target_joins_the_macvlan_with_its_catalog_address_and_mac(self):
        device=CATALOG.target('web03')
        argv=create.container_command(device,ROOT,'image:tag')
        self.assertEqual(argv[:2],['docker','create'])
        self.assertIn('pinpoint274-host-web03-pilot',argv)
        self.assertEqual(argv[argv.index('--network')+1],'pinpoint274-host-test')
        self.assertEqual(argv[argv.index('--ip')+1],device.address)
        self.assertEqual(argv[argv.index('--mac-address')+1],device.mac)
        self.assertNotIn('--privileged',argv)
    def test_dhcp_client_has_no_network_and_net_admin_only(self):
        argv=create.container_command(CATALOG.target('dynweb01'),ROOT,'image:tag')
        self.assertEqual(argv[argv.index('--network')+1],'none')
        self.assertIn('NET_ADMIN',argv);self.assertNotIn('--ip',argv)
    def test_command_labels_and_mounts_match_what_the_presenter_validates(self):
        for device in CATALOG.devices:
            if device.kind!='linux':continue
            argv=create.container_command(device,ROOT,'image:tag')
            self.assertEqual(argv[-5:],['image:tag','python3','/opt/pinpoint/targets/node.py','init',device.name])
            self.assertIn('org.pinpoint.defense.role=temporary-pilot',argv)
            self.assertIn('org.pinpoint.defense.issue=274',argv)
            mounts=[argv[i+1] for i,a in enumerate(argv) if a=='--mount']
            self.assertEqual(len(mounts),4 if device.name in {'snmp02','dynsnmp01'} else 3,device.name)
    def test_network_and_image_commands(self):
        net=create.network_command()
        self.assertEqual(net[:4],['docker','network','create','-d']);self.assertIn('parent=vboxnet1',net)
        self.assertIn('10.77.1.30',net);self.assertIn('org.pinpoint.defense.issue=274',net)
        build=create.build_command(Path('/repo'),'image:tag')
        self.assertEqual(build[:2],['docker','build']);self.assertEqual(build[-1],'/repo')
    def test_fourteen_create_commands_cover_exactly_the_linux_devices(self):
        names=[a for argv in create.container_commands(CATALOG,ROOT,'i:t') for a in argv if a.startswith('pinpoint274-host-') and a.endswith('-pilot')]
        self.assertEqual(len(names),14);self.assertEqual(len(set(names)),14)


class ApplyTests(unittest.TestCase):
    def test_existing_objects_are_skipped_so_rerun_is_safe(self):
        log=[]
        def runner(argv,input_text=None):
            log.append(argv)
            if argv[:3]==['docker','image','inspect']:return '[{"Id":"sha256:new"}]'
            if argv[:2]==['docker','inspect']:return '[{"Image":"sha256:new"}]'
            if argv[:3]==['docker','network','inspect']:return '[{}]'
            return ''
        create.apply(CATALOG,ROOT,Path('/repo'),runner,owner=OWNER,vm_uuid=UUID,parent_mac=MAC,community='c',image='i:t')
        self.assertFalse([a for a in log if a[:2]==['docker','create'] or a[:3]==['docker','network','create']])

class StaleImageTests(unittest.TestCase):
    def test_existing_containers_from_an_older_image_are_refused(self):
        def runner(argv,input_text=None):
            if argv[:3]==['docker','image','inspect']:return '[{"Id":"sha256:new"}]'
            if argv[:2]==['docker','inspect']:return '[{"Image":"sha256:old"}]'
            return ''
        with self.assertRaises(ValueError) as caught:
            create.apply(CATALOG,ROOT,Path('/repo'),runner,owner=OWNER,vm_uuid=UUID,parent_mac=MAC,community='c',image='i:t')
        self.assertIn('older image',str(caught.exception))


class KeepOwnerTests(unittest.TestCase):
    def test_an_existing_context_file_is_never_overwritten(self):
        log=[]
        def runner(argv,input_text=None):
            log.append((argv,input_text))
            if argv[:3]==['docker','image','inspect']:return '[{"Id":"sha256:n"}]'
            if argv[:2]==['docker','inspect']:return '[{"Image":"sha256:n"}]'
            return '[{}]'
        create.apply(CATALOG,ROOT,Path('/repo'),runner,owner=OWNER,vm_uuid=UUID,parent_mac=MAC,community='c',image='i:t')
        self.assertFalse([a for a,i in log if a[:2]==['sudo','tee']])
    def test_a_missing_context_file_is_written(self):
        log=[]
        def runner(argv,input_text=None):
            log.append(argv)
            if argv[:3]==['sudo','test','-e']:raise ValueError('absent')
            if argv[:3]==['docker','image','inspect']:return '[{"Id":"sha256:n"}]'
            if argv[:2]==['docker','inspect']:return '[{"Image":"sha256:n"}]'
            return '[{}]'
        create.apply(CATALOG,ROOT,Path('/repo'),runner,owner=OWNER,vm_uuid=UUID,parent_mac=MAC,community='c',image='i:t')
        self.assertTrue([a for a in log if a[:2]==['sudo','tee']])


class CommunityTests(unittest.TestCase):
    def test_generated_community_matches_what_the_node_accepts(self):
        import re
        self.assertRegex(create.new_community(),r'[a-f0-9]{32}')


class PinTests(unittest.TestCase):
    def test_pins_use_the_presenter_format(self):
        def runner(argv):
            return json.dumps([{'Id':'1'*64,'Image':'sha256:'+'2'*64}])
        pins=create.read_pins(CATALOG,runner)
        self.assertEqual(len(pins),14)
        self.assertEqual(pins['web03'],{'id':'1'*64,'image':'sha256:'+'2'*64})
if __name__=='__main__':unittest.main()
