"""Regression contracts for guest forwarding and account hardening; offline only."""
from contextlib import nullcontext
import copy
import io
import json
import os
import signal
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense import bootstrap

CONTEXT={'version':1,'owner':'b'*48,'vm_uuid':'821464dc-e7ce-4067-8eec-5cb1c61d3632','parent_mac':'02:77:01:fe:31:d7'}
LINKS=[{'ifname':'enp0s8','address':CONTEXT['parent_mac'],'addr_info':[],'flags':['BROADCAST','MULTICAST','UP']}]


class HardeningTests(unittest.TestCase):
    def test_docker_restart_is_guarded_independently_of_one_time_image_marker(self):
        self.assertEqual(bootstrap.docker_settings(),{'ip-forward':False})
        unit=bootstrap.docker_guard_dropin()
        self.assertIn('ExecStartPost=/usr/bin/python3 /opt/pinpoint-defense/bootstrap.py guard',unit)
        self.assertNotIn('prepared.json',unit)
        ready=bootstrap.ready_unit()
        self.assertIn('cloud-final.service',ready)
        self.assertIn('After=cloud-final.service docker.service',ready)
        self.assertIn('bootstrap.py ready',ready)
        self.assertNotIn('ConditionPathExists=!',ready)

    def test_boot_guard_refuses_foreign_context_before_sysctl_or_account_changes(self):
        with patch.object(bootstrap,'owned_context',side_effect=ValueError('foreign')),patch.object(bootstrap,'run') as run:
            with self.assertRaises(ValueError):bootstrap.guard_forwarding()
            run.assert_not_called()

    def test_boot_guard_resets_observed_ipv4_one_and_verifies_both_values(self):
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'run') as run,patch.object(bootstrap,'forwarding_values',return_value=(0,0)):
            bootstrap.guard_forwarding()
            self.assertIn(['sysctl','-w','net.ipv4.ip_forward=0','net.ipv6.conf.all.forwarding=0'],[c.args[0] for c in run.call_args_list])
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'run'),patch.object(bootstrap,'forwarding_values',return_value=(1,0)):
            with self.assertRaises(ValueError):bootstrap.guard_forwarding()

    def test_build_gateway_exists_only_with_exact_demo_parent_down_and_cleans_on_failure(self):
        events=[]
        def run(argv):events.append(argv)
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'build_parent',side_effect=[('enp0s8',True),('enp0s8',False)]),patch.object(bootstrap,'run',side_effect=run),patch.object(bootstrap,'forwarding_values',return_value=(0,0)):
            with self.assertRaises(RuntimeError):
                with bootstrap.build_network():
                    events.append(['BUILD']);raise RuntimeError('build failed')
        down=['ip','link','set','dev','enp0s8','down']
        enable=['sysctl','-w','net.ipv4.ip_forward=1']
        disable=['sysctl','-w','net.ipv4.ip_forward=0','net.ipv6.conf.all.forwarding=0']
        self.assertLess(events.index(down),events.index(enable))
        self.assertLess(events.index(enable),events.index(['BUILD']))
        self.assertIn(disable,events)
        self.assertNotIn(['ip','link','set','dev','enp0s8','up'],events)

    def test_successful_build_turns_forwarding_off_before_restoring_parent(self):
        events=[]
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'build_parent',side_effect=[('enp0s8',True),('enp0s8',False)]),patch.object(bootstrap,'run',side_effect=lambda argv:events.append(argv)),patch.object(bootstrap,'forwarding_values',return_value=(0,0)):
            with bootstrap.build_network():events.append(['BUILD'])
        off=events.index(['sysctl','-w','net.ipv4.ip_forward=0','net.ipv6.conf.all.forwarding=0'])
        self.assertLess(off,events.index(['ip','link','set','dev','enp0s8','up']))
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'build_parent',side_effect=ValueError('numbered parent')),patch.object(bootstrap,'run') as run:
            with self.assertRaises(ValueError):
                with bootstrap.build_network():self.fail('unsafe build ran')
            run.assert_not_called()

    def test_build_cannot_enable_forwarding_if_parent_did_not_go_down(self):
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'build_parent',return_value=('enp0s8',True)),patch.object(bootstrap,'run') as run,patch.object(bootstrap,'forwarding_values',return_value=(0,0)):
            with self.assertRaises(ValueError):
                with bootstrap.build_network():self.fail('numbered gateway opened')
            self.assertNotIn(['sysctl','-w','net.ipv4.ip_forward=1'],[c.args[0] for c in run.call_args_list])

    def test_service_cancellation_closes_gateway_and_restores_signal_handler(self):
        previous=signal.getsignal(signal.SIGTERM);events=[]
        with patch.object(bootstrap,'owned_context',return_value=CONTEXT),patch.object(bootstrap,'build_parent',side_effect=[('enp0s8',True),('enp0s8',False)]),patch.object(bootstrap,'run',side_effect=lambda argv:events.append(argv)),patch.object(bootstrap,'forwarding_values',return_value=(0,0)):
            with self.assertRaises(SystemExit):
                with bootstrap.build_network():signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
        self.assertEqual(signal.getsignal(signal.SIGTERM),previous)
        self.assertIn(['sysctl','-w','net.ipv4.ip_forward=0','net.ipv6.conf.all.forwarding=0'],events)
        self.assertNotIn(['ip','link','set','dev','enp0s8','up'],events)

    def test_management_cleanup_removes_every_supplementary_group_and_only_known_user_sudo(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'etc/sudoers.d').mkdir(parents=True);(root/'etc/sudoers.d').chmod(0o750)
            cloud=root/'etc/sudoers.d/90-cloud-init-users'
            cloud.write_text('# cloud-init\ndefense ALL=(ALL) NOPASSWD:ALL\nother ALL=(ALL) ALL\n');cloud.chmod(0o440)
            with patch.object(bootstrap,'run') as run,patch.object(bootstrap,'management_uid',return_value=1000):
                bootstrap.harden_management(root)
            self.assertIn(['usermod','--groups','','defense'],[c.args[0] for c in run.call_args_list])
            self.assertNotIn('defense ALL',cloud.read_text())
            self.assertIn('other ALL',cloud.read_text())
            self.assertEqual(cloud.stat().st_mode&0o777,0o440)
            outside=root/'foreign';outside.write_text('UNCHANGED')
            cloud.unlink();cloud.symlink_to(outside)
            with patch.object(bootstrap,'management_uid',return_value=1000),self.assertRaises(ValueError):bootstrap.harden_management(root)
            self.assertEqual(outside.read_text(),'UNCHANGED')

    def test_management_uid_zero_or_foreign_account_fails_before_cleanup(self):
        from types import SimpleNamespace
        for value in ['0','999','bad']:
            with patch('subprocess.run',return_value=SimpleNamespace(stdout=value)):
                with self.assertRaises(ValueError):bootstrap.management_uid()
        with patch.object(bootstrap,'management_uid',side_effect=ValueError('wrong uid')),patch.object(bootstrap,'run') as run:
            with self.assertRaises(ValueError):bootstrap.harden_management(Path('/nonexistent-fixture'))
            run.assert_not_called()

    def test_account_observation_rejects_lxd_disk_or_unrestricted_sudo(self):
        allowed='    (root) NOPASSWD: /usr/local/sbin/pinpoint-defense-guest\n'
        bootstrap.validate_management(['defense'],allowed)
        for groups,sudo in [(['defense','lxd'],allowed),(['defense','disk'],allowed),(['defense'],allowed+'    (ALL) NOPASSWD: ALL\n'),(['defense'],'')]:
            with self.assertRaises(ValueError):bootstrap.validate_management(groups,sudo)


if __name__=='__main__':unittest.main()
