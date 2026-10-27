"""Offline input and process identity checks for host-only DHCP attachment."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.host_attach import attach, validate_request, validate_process


class HostAttachTests(unittest.TestCase):
    def test_only_catalog_dhcp_targets_and_exact_process_shape_are_accepted(self):
        request={'target':'dynweb01','pid':1234,'start_ticks':900,'container_id':'a'*64}
        self.assertEqual(validate_request(request),request)
        for change in [dict(target='web03'),dict(target='../bad'),dict(pid=True),dict(pid=1),
                       dict(start_ticks=0),dict(container_id='bad'),dict(extra='command')]:
            with self.assertRaises(ValueError):validate_request(dict(request,**change))

    def test_container_cgroup_and_process_start_must_both_match(self):
        request={'target':'dynweb01','pid':1234,'start_ticks':900,'container_id':'a'*64}
        cgroup='0::/system.slice/docker-'+request['container_id']+'.scope\n'
        validate_process(request,900,cgroup)
        for tick,group in [(901,cgroup),(900,cgroup.replace('a'*64,'b'*64)),(900,'0::/\n')]:
            with self.assertRaises(ValueError):validate_process(request,tick,group)

    def test_wrong_context_and_wrong_namespace_refuse_before_network_commands(self):
        request={'target':'dynweb01','pid':1234,'start_ticks':900,'container_id':'a'*64}
        with patch('defense.host_attach.run') as run:
            with self.assertRaises(ValueError):attach(request,{'version':1})
            run.assert_not_called()
        with patch('defense.host_attach.os.readlink',side_effect=['host','container']),patch('defense.host_attach.run') as run:
            with self.assertRaises(ValueError):attach(request,{'version':2,'mode':'host-only'})
            run.assert_not_called()


if __name__=='__main__':unittest.main()
