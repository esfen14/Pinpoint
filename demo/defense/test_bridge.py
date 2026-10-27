"""Offline checks for the proposed defense bridge inventory; no network mutation."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from defense.bridge import collect_bridge_inventory, normalize_link_inventory, validate_bridge_inventory, validate_veth_peer

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
    def test_collection_pins_process_before_and_after_both_link_observations(self):
        raw_host = [
            {'ifname': 'pdbr0', 'ifindex': 4, 'address': '02:77:01:fe:00:ff', 'addr_info': [], 'ifalias': 'pinpoint-defense:' + OWNER + ':bridge', 'linkinfo': {'info_kind': 'bridge'}},
            {'ifname': 'enp0s8', 'ifindex': 5, 'address': PARENT, 'addr_info': [], 'master': 'pdbr0'},
            {'ifname': 'pd-dhcp01', 'ifindex': 30, 'link_index': 7, 'address': '02:77:01:fe:00:01', 'addr_info': [], 'master': 'pdbr0', 'ifalias': 'pinpoint-defense:' + OWNER + ':dhcp01', 'linkinfo': {'info_kind': 'veth'}},
        ]
        raw_guest = [{'ifname': 'lo', 'ifindex': 1}, {'ifname': 'eth0', 'ifindex': 7, 'link_index': 30, 'address': '02:77:01:00:00:01', 'linkinfo': {'info_kind': 'veth'}}]
        events = []
        def identity(target):
            events.append('identity')
            return (1234, 8765, 'c' * 64)
        def observe(pid):
            events.append('guest')
            return raw_guest
        def host():
            events.append('host')
            return raw_host
        collect_bridge_inventory(OWNER, PARENT, {'dhcp01': 'pd-dhcp01'}, 0, 0, identity, host, observe)
        self.assertEqual(events, ['identity', 'host', 'identity', 'guest', 'identity', 'host', 'identity'])

        attempts = iter([(1234, 8765, 'c' * 64), (1234, 9999, 'c' * 64)])
        with self.assertRaises(ValueError):
            collect_bridge_inventory(OWNER, PARENT, {'dhcp01': 'pd-dhcp01'}, 0, 0, lambda target: next(attempts), lambda: raw_host, lambda pid: raw_guest)

        changed_host = copy.deepcopy(raw_host)
        changed_host.append({'ifname': 'enp0s3', 'ifindex': 9, 'address': '02:00:00:00:00:01', 'addr_info': [], 'master': 'pdbr0'})
        observations = iter([raw_host, changed_host])
        with self.assertRaises(ValueError):
            collect_bridge_inventory(OWNER, PARENT, {'dhcp01': 'pd-dhcp01'}, 0, 0, lambda target: (1234, 8765, 'c' * 64), lambda: next(observations), lambda pid: raw_guest)

    def test_normalization_rejects_missing_address_inventory_and_unknown_types(self):
        raw = [{'ifname': 'pdbr0', 'ifindex': 3, 'address': '02:77:01:fe:00:ff',
                'addr_info': [], 'linkinfo': {'info_kind': 'bridge'}, 'ifalias': 'owned'},
               {'ifname': 'enp0s8', 'ifindex': 4, 'address': PARENT,
                'addr_info': [], 'master': 'pdbr0'}]
        normalized = normalize_link_inventory(raw)
        self.assertEqual(normalized[0]['kind'], 'bridge')
        self.assertEqual(normalized[1]['kind'], 'ether')
        self.assertEqual(normalized[1]['master'], 'pdbr0')
        for mutation in [lambda links: links[0].pop('addr_info'),
                         lambda links: links[0].update(addr_info=[{'family': 'inet'}]),
                         lambda links: links[1].update(master=7),
                         lambda links: links[0].update(linkinfo={'info_kind': 'unknown'}),
                         lambda links: links.append(copy.deepcopy(links[1]))]:
            changed = copy.deepcopy(raw)
            mutation(changed)
            with self.assertRaises(ValueError):
                normalize_link_inventory(changed)

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

    def test_peer_must_match_both_link_indices_and_the_catalog_mac(self):
        host = {'ifindex': 30, 'link_index': 7, 'kind': 'veth', 'alias': 'pinpoint-defense:' + OWNER + ':dhcp01'}
        guest = {'ifname': 'eth0', 'ifindex': 7, 'link_index': 30, 'kind': 'veth', 'mac': '02:77:01:00:00:01'}
        validate_veth_peer(host, guest, OWNER, 'dhcp01')
        for host_change, guest_change in [
            ({'link_index': 8}, {}), ({'ifindex': 31}, {}),
            ({'alias': 'foreign'}, {}), ({'kind': 'ether'}, {}),
            ({}, {'mac': '02:00:00:00:00:01'}), ({}, {'ifname': 'eth1'}),
            ({}, {'kind': 'macvlan'}), ({'ifindex': True}, {}),
        ]:
            with self.assertRaises(ValueError):
                validate_veth_peer(dict(host, **host_change), dict(guest, **guest_change), OWNER, 'dhcp01')


if __name__ == '__main__':
    unittest.main()
