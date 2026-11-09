"""Offline tests for demo/demo setup and destroy: plan, preflight and destroy rules; no Docker or VirtualBox."""
from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from targets import setup
from targets.catalog import load_catalog

CATALOG=load_catalog()


def good_runner(argv):
    """Fake read-only command output for a healthy host."""
    if argv[:2]==['docker','version']:return 'Docker 27'
    if argv[:2]==['VBoxManage','--version']:return '7.2.14'
    if argv[:3]==['VBoxManage','list','hostonlyifs']:return 'Name: vboxnet1\nIPAddress: 192.168.57.1\n'
    if argv[:2]==['ip','-j']:return '[{"dst":"default","dev":"wlan0"},{"dst":"192.168.1.0/24","dev":"wlan0"},{"dst":"192.168.57.0/24","dev":"vboxnet1"}]'
    raise AssertionError('unexpected command %r'%(argv,))


class PlanTests(unittest.TestCase):
    def test_plan_names_every_step_in_order_and_the_fourteen_containers(self):
        steps=setup.plan(CATALOG)
        text='\n'.join(steps)
        linux=[d.name for d in CATALOG.devices if d.kind=='linux']
        self.assertEqual(len(linux),14)
        for name in linux:self.assertIn(name,text)
        order=[text.index(word) for word in ('Preflight','Build the image','Create the network','Create the 14 containers','Attach the DHCP','Enroll','Check the appliance')]
        self.assertEqual(order,sorted(order))
    def test_checklist_gives_a_check_command_for_every_manual_step(self):
        items=setup.manual_checklist()
        titles=' '.join(i[0] for i in items)
        for word in ('adapter','Windows','discovery','Nagios'):self.assertIn(word,titles)
        for title,check in items:
            self.assertTrue(check.strip(),title)


class PreflightTests(unittest.TestCase):
    def test_healthy_host_has_no_blockers(self):
        results=setup.preflight(good_runner,available_mib=8192)
        self.assertEqual([r for r in results if not r[1]],[])
    def test_missing_docker_missing_hostonly_and_low_ram_are_blockers(self):
        def runner(argv):
            if argv[:2]==['docker','version']:raise OSError('no docker')
            if argv[:3]==['VBoxManage','list','hostonlyifs']:return 'Name: vboxnet9\n'
            return good_runner(argv)
        failed={r[0] for r in setup.preflight(runner,available_mib=1024) if not r[1]}
        self.assertEqual(failed,{'Docker','Host-only network vboxnet1','Memory'})
    def test_a_route_overlapping_the_demo_subnet_on_another_interface_is_a_blocker(self):
        def runner(argv):
            if argv[:2]==['ip','-j']:return '[{"dst":"10.77.1.0/24","dev":"tun0"}]'
            return good_runner(argv)
        failed={r[0] for r in setup.preflight(runner,available_mib=8192) if not r[1]}
        self.assertEqual(failed,{'Subnet conflicts'})


class MainTests(unittest.TestCase):
    def run_main(self,argv,runner=good_runner,answer='',mem=8192):
        out=io.StringIO();err=io.StringIO()
        code=setup.main(argv,runner=runner,available_mib=lambda:mem,ask=lambda prompt:answer,out=out,err=err)
        return code,out.getvalue(),err.getvalue()
    def test_setup_without_apply_prints_plan_and_checklist_and_runs_nothing_mutating(self):
        calls=[]
        def runner(argv):
            calls.append(argv);return good_runner(argv)
        code,out,_=self.run_main(['setup'],runner)
        self.assertEqual(code,0)
        self.assertIn('Plan (nothing is changed without --apply)',out)
        self.assertIn('Manual steps',out)
        for argv in calls:self.assertNotIn(argv[1],{'run','create','rm','network','build'})
    def test_setup_with_a_blocker_fails_even_for_the_plan(self):
        def runner(argv):
            if argv[:2]==['docker','version']:raise OSError('x')
            return good_runner(argv)
        code,out,_=self.run_main(['setup'],runner)
        self.assertEqual(code,1);self.assertIn('FAIL',out)
    def test_setup_apply_refuses_container_creation_until_it_is_reviewed(self):
        code,_,err=self.run_main(['setup','--apply'])
        self.assertEqual(code,2);self.assertIn('not implemented',err)
    def test_unknown_arguments_are_rejected(self):
        self.assertEqual(self.run_main(['setup','--force'])[0],2)
        self.assertEqual(self.run_main(['destroy','x'])[0],2)


OWNED='[{"Id":"%s","Name":"/pinpoint274-host-web03-pilot","Config":{"Labels":{"org.pinpoint.defense.issue":"274","org.pinpoint.defense.role":"temporary-pilot"}}}]'


class DestroyTests(unittest.TestCase):
    def make(self,containers,network_ok=True):
        log=[]
        def runner(argv):
            log.append(argv)
            if argv[:3]==['docker','ps','-a']:return '\n'.join(containers)
            if argv[:3]==['docker','network','inspect']:
                return '[{"Name":"pinpoint274-host-test","Driver":"macvlan","Labels":{"org.pinpoint.defense.issue":"274"}}]' if network_ok else '[]'
            if argv[:2]==['docker','inspect']:return OWNED%argv[2]
            return ''
        return runner,log
    def test_without_apply_destroy_only_lists(self):
        runner,log=self.make(['a'*64])
        out=io.StringIO()
        code=setup.destroy(runner,apply=False,ask=lambda p:'destroy',out=out,err=io.StringIO())
        self.assertEqual(code,0);self.assertIn('pinpoint274-host-web03-pilot',out.getvalue())
        self.assertFalse([a for a in log if a[1] in {'rm','stop'} or a[:3]==['docker','network','rm']])
    def test_apply_needs_the_typed_confirmation(self):
        runner,log=self.make(['a'*64])
        code=setup.destroy(runner,apply=True,ask=lambda p:'yes',out=io.StringIO(),err=io.StringIO())
        self.assertEqual(code,1)
        self.assertFalse([a for a in log if a[1] in {'rm','stop'}])
    def test_apply_removes_only_owned_containers_and_the_owned_network(self):
        runner,log=self.make(['a'*64])
        code=setup.destroy(runner,apply=True,ask=lambda p:'destroy',out=io.StringIO(),err=io.StringIO())
        self.assertEqual(code,0)
        self.assertIn(['docker','rm','-f','a'*64],log)
        self.assertIn(['docker','network','rm','pinpoint274-host-test'],log)
    def test_a_container_without_the_owner_labels_is_never_removed(self):
        def runner(argv):
            if argv[:3]==['docker','ps','-a']:return 'b'*64
            if argv[:2]==['docker','inspect']:return '[{"Id":"%s","Name":"/web03","Config":{"Labels":{}}}]'%('b'*64)
            if argv[:3]==['docker','network','inspect']:return '[]'
            raise AssertionError(argv)
        err=io.StringIO()
        code=setup.destroy(runner,apply=True,ask=lambda p:'destroy',out=io.StringIO(),err=err)
        self.assertEqual(code,1);self.assertIn('not owned',err.getvalue())
if __name__=='__main__':unittest.main()
