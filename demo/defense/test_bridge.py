"""Offline checks for the proposed defense bridge inventory; no network mutation."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from defense.bridge import validate_bridge_inventory

OWNER = 'b' * 48
PARENT = '02:77:01:fe:31:d7'


def inventory():
    """Represent observations made independently in the target-host namespace."""
    return [
        {'name': 'pdbr0', 'kind': 'bridge', 'mac': '02:77:01:fe:00:ff',
         'alias': 'pinpoint-defense:' + OWNER + ':bridge', 'master': None, 'addresses': []},
        {'name': 'enp0s8', 'kind': 'ether', 'mac': PARENT,
         'alias': '', 'master': 'pdbr0', 'addresses': []},
        {'name': 'pd-dhcp01', 'kind': 'veth', 'mac': '02:77:01:fe:00:01',
         'alias': 'pinpoint-defense:' + OWNER + ':dhcp01', 'master': 'pdbr0', 'addresses': []},
    ]


class BridgeInventoryTests(unittest.TestCase):
    def test_accepts_exact_unnumbered_owned_bridge_and_members(self):
        validate_bridge_inventory(inventory(), OWNER, PARENT, {'dhcp01': 'pd-dhcp01'}, 0, 0)

    def test_refuses_foreign_port_management_nic_or_numbered_bridge(self):
        for change in [
            lambda links: links.append({'name': 'enp0s3', 'kind': 'ether', 'mac': '02:00:00:00:00:01', 'alias': '', 'master': 'pdbr0', 'addresses': []}),
            lambda links: links[0]['addresses'].append('10.77.1.1/27'),
            lambda links: links[1].update(mac='02:00:00:00:00:01'),
            lambda links: links[2].update(alias='foreign'),
            lambda links: links[2].update(master='br-other'),
            lambda links: links.append(copy.deepcopy(links[2])),
        ]:
            links = inventory()
            change(links)
            with self.subTest(links=links), self.assertRaises(ValueError):
                validate_bridge_inventory(links, OWNER, PARENT, {'dhcp01': 'pd-dhcp01'}, 0, 0)

    def test_refuses_forwarding_and_unapproved_members(self):
        for members, forwarding4, forwarding6 in [({'dhcp01': 'pd-dhcp01'}, 1, 0),
                                                   ({'dhcp01': 'pd-dhcp01'}, 0, 1),
                                                   ({'win01': 'pd-dhcp01'}, 0, 0),
                                                   ({'dhcp01': 'pd-dhcp01;sh'}, 0, 0)]:
            with self.assertRaises(ValueError):
                validate_bridge_inventory(inventory(), OWNER, PARENT, members, forwarding4, forwarding6)


if __name__ == '__main__':
    unittest.main()
