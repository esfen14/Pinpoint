"""Offline validation for a proposed isolated bridge; no live lifecycle yet."""
import re

from .catalog import load_catalog


def collect_bridge_inventory(owner, parent_mac, members, forwarding4, forwarding6,
                             identity, observe_host, observe_guest):
    """Cross-check a complete bridge snapshot and veth peers around pinned PIDs.

    The caller supplies bounded observers and must independently validate the
    container/image ownership, forwarding values and guest network namespace.
    This function never invokes commands or changes links.
    """
    if not isinstance(members, dict) or not members:
        raise ValueError('At least one pinned target is required')
    pinned = {}
    for target in members:
        value = identity(target)
        if (not isinstance(value, tuple) or len(value) != 3 or type(value[0]) is not int or value[0] <= 1
                or not str(value[1]).isdigit() or int(value[1]) <= 0
                or not isinstance(value[2], str) or not re.fullmatch(r'[a-f0-9]{64}', value[2])):
            raise ValueError('Invalid container process identity')
        pinned[target] = value

    def check_identities():
        for target, value in pinned.items():
            if identity(target) != value:
                raise ValueError('Container identity changed during observation')

    first = observe_host()
    normalized = normalize_link_inventory(first)
    validate_bridge_inventory(normalized, owner, parent_mac, members, forwarding4, forwarding6)
    check_identities()
    for target, name in members.items():
        host = next((item for item in first if item.get('ifname') == name), None)
        guest_links = observe_guest(pinned[target][0])
        if not isinstance(guest_links, list) or any(not isinstance(item, dict) for item in guest_links):
            raise ValueError('Incomplete guest inventory')
        if len(guest_links) != 2 or {item.get('ifname') for item in guest_links} != {'lo', 'eth0'}:
            raise ValueError('Guest namespace interface boundary changed')
        peer = next(item for item in guest_links if item.get('ifname') == 'eth0')
        if not isinstance(host, dict):
            raise ValueError('Host peer missing')
        host_view = {'ifindex': host.get('ifindex'), 'link_index': host.get('link_index'),
                     'kind': host.get('linkinfo', {}).get('info_kind'), 'alias': host.get('ifalias')}
        guest_view = {'ifindex': peer.get('ifindex'), 'link_index': peer.get('link_index'),
                      'kind': peer.get('linkinfo', {}).get('info_kind'),
                      'ifname': peer.get('ifname'), 'mac': peer.get('address')}
        validate_veth_peer(host_view, guest_view, owner, target)
        check_identities()
    last = observe_host()
    if last != first:
        raise ValueError('Host link inventory changed during observation')
    check_identities()
    return normalized


def normalize_link_inventory(links):
    """Normalize one complete `ip -j -d addr show` result; never infer omissions."""
    if not isinstance(links, list):
        raise ValueError('Invalid link inventory')
    result = []
    for link in links:
        if not isinstance(link, dict):
            raise ValueError('Invalid link record')
        name, index, mac = link.get('ifname'), link.get('ifindex'), link.get('address')
        addresses, master = link.get('addr_info'), link.get('master')
        info = link.get('linkinfo', {})
        if (not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,15}', name)
                or type(index) is not int or index <= 0 or not isinstance(mac, str)
                or not isinstance(addresses, list) or not isinstance(info, dict)
                or master is not None and not isinstance(master, str)):
            raise ValueError('Incomplete link record')
        kind = info.get('info_kind', 'ether')
        if kind not in {'ether', 'bridge', 'veth', 'macvlan'}:
            raise ValueError('Unsupported link kind')
        normalized_addresses = []
        for address in addresses:
            if not isinstance(address, dict) or not isinstance(address.get('local'), str) or type(address.get('prefixlen')) is not int:
                raise ValueError('Incomplete link address')
            normalized_addresses.append(f"{address['local']}/{address['prefixlen']}")
        alias = link.get('ifalias', '')
        if not isinstance(alias, str):
            raise ValueError('Invalid link alias')
        result.append({'name': name, 'kind': kind, 'mac': mac.lower(), 'master': master,
                       'alias': alias, 'addresses': normalized_addresses})
    names = [link['name'] for link in result]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate link names')
    return result


def validate_veth_peer(host, guest, owner, target):
    """Compare independently observed host and container veth peer identities.

    The caller must separately pin the container PID and process start time
    around both observations; link indices alone do not provide that proof.
    """
    if not isinstance(owner, str) or not re.fullmatch(r'[a-f0-9]{48}', owner):
        raise ValueError('Invalid owner')
    if not isinstance(target, str):
        raise ValueError('Invalid target')
    device = load_catalog().target(target)
    if device.kind != 'linux' or not isinstance(host, dict) or not isinstance(guest, dict):
        raise ValueError('Invalid peer inventory')
    indices = [host.get('ifindex'), host.get('link_index'), guest.get('ifindex'), guest.get('link_index')]
    if any(type(index) is not int or index <= 0 for index in indices):
        raise ValueError('Peer link index missing')
    if (host.get('kind') != 'veth' or host.get('alias') != f'pinpoint-defense:{owner}:{target}'
            or guest.get('kind') != 'veth' or guest.get('ifname') != 'eth0'
            or guest.get('mac') != device.mac
            or host['ifindex'] != guest['link_index'] or host['link_index'] != guest['ifindex']):
        raise ValueError('Veth peer identity changed')


def validate_bridge_inventory(links, owner, parent_mac, members, forwarding4, forwarding6):
    """Reject an unowned, numbered, incomplete or unexpectedly connected bridge.

    `links` is an independently collected and normalized complete host link
    inventory. This validator does not collect or mutate a live namespace.
    Namespace peer identity and bridge netfilter policy need separate checks.
    """
    if not isinstance(owner, str) or not re.fullmatch(r'[a-f0-9]{48}', owner):
        raise ValueError('Invalid owner')
    if not isinstance(parent_mac, str) or not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}', parent_mac):
        raise ValueError('Invalid parent MAC')
    if type(forwarding4) is not int or type(forwarding6) is not int or (forwarding4, forwarding6) != (0, 0):
        raise ValueError('IP forwarding must be off')
    if (not isinstance(members, dict)
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in members.items())
            or len(members) != len(set(members.values()))):
        raise ValueError('Invalid bridge members')
    catalog = load_catalog()
    for target, name in members.items():
        if catalog.target(target).kind != 'linux' or name != 'pd-' + target or len(name) > 15:
            raise ValueError('Invalid catalog bridge member')
    if not isinstance(links, list) or any(not isinstance(link, dict) for link in links):
        raise ValueError('Invalid link inventory')
    names = [link.get('name') for link in links]
    if any(not isinstance(name, str) for name in names) or len(names) != len(set(names)):
        raise ValueError('Incomplete or duplicate link inventory')
    bridges = [link for link in links if link.get('name') == 'pdbr0']
    if len(bridges) != 1:
        raise ValueError('Owned bridge missing')
    bridge = bridges[0]
    if (bridge.get('kind') != 'bridge' or bridge.get('alias') != f'pinpoint-defense:{owner}:bridge'
            or bridge.get('master') is not None or bridge.get('addresses') != []):
        raise ValueError('Bridge identity or addressing changed')
    parents = [link for link in links if link.get('mac') == parent_mac]
    if len(parents) != 1:
        raise ValueError('Parent missing or duplicated')
    parent = parents[0]
    if (parent.get('kind') != 'ether' or parent.get('name') == 'pdbr0'
            or parent.get('master') != 'pdbr0' or parent.get('addresses') != []):
        raise ValueError('Parent is not an isolated bridge port')
    expected = {parent['name'], *members.values()}
    ports = [link for link in links if link.get('master') == 'pdbr0']
    if {link['name'] for link in ports} != expected:
        raise ValueError('Unexpected bridge membership')
    for target, name in members.items():
        port = next(link for link in ports if link['name'] == name)
        if (port.get('kind') != 'veth' or port.get('alias') != f'pinpoint-defense:{owner}:{target}'
                or port.get('addresses') != []):
            raise ValueError('Bridge port ownership changed')
