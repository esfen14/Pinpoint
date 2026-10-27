"""Pure host ownership/resource gates; execution is collected separately."""
import ipaddress
import json
import os
from pathlib import Path
import re
import stat

from .catalog import NETWORK

VM_NAMES = {'appliance':'pinpoint-qa-appliance', 'target_host':'pinpoint-defense-targets',
            'windows':'pinpoint-defense-win01'}
FORWARDS = {'appliance':[(2250,22),(18080,80)], 'target_host':[(2260,22)], 'windows':[]}
HOST_RESERVE_MIB = 3072
START_OVERHEAD_MIB = 512


def reject_overlaps(occupied: list[str]) -> None:
    """Reject even supernet/host routes; callers separately omit the default route."""
    try:
        conflict = any(NETWORK.overlaps(ipaddress.ip_network(value,strict=False))
                       for value in occupied)
    except (TypeError,ValueError):
        raise ValueError('Network inventory is invalid or incomplete') from None
    if conflict:
        raise ValueError('Defense subnet overlaps a route, interface, Docker or VPN network')


def check_resources(available_mib: int, free_disk_mib: int, new_vm_mib: list[int],
                    required_disk_mib: int) -> int:
    """Reserve host headroom plus only memory not already committed to running VMs."""
    values = [available_mib,free_disk_mib,required_disk_mib,*new_vm_mib]
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError('Resource inventory is invalid')
    required = sum(new_vm_mib)+HOST_RESERVE_MIB+START_OVERHEAD_MIB
    if available_mib < required:
        raise ValueError(f'Insufficient RAM: need {required} MiB available, observed {available_mib} MiB')
    if free_disk_mib < required_disk_mib:
        raise ValueError(f'Insufficient disk: need {required_disk_mib} MiB free, observed {free_disk_mib} MiB')
    return required


def validate_vm(vm: dict, role: str, expected_uuid: str, expected_owner: str,
                expected_macs: list[str]) -> None:
    """Pin exact VM identity and the entire NIC/forwarding boundary before mutation."""
    if not isinstance(expected_uuid,str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',expected_uuid):
        raise ValueError('Invalid pinned VM UUID')
    if role not in VM_NAMES or vm.get('name') != VM_NAMES[role] or vm.get('uuid') != expected_uuid:
        raise ValueError('Defense VM identity mismatch')
    if not isinstance(expected_owner,str) or not re.fullmatch(r'[a-f0-9]{48}',expected_owner) or vm.get('owner') != expected_owner:
        raise ValueError('Defense VM ownership marker mismatch')
    if vm.get('state') not in {'running','poweroff'}:
        raise ValueError('Defense VM state is transitional or ambiguous')
    nics = vm.get('nics')
    if not isinstance(nics,list) or len(nics) != (1 if role == 'windows' else 2):
        raise ValueError('Unexpected defense VM network adapters')
    if role == 'windows':
        expected = [(1,'intnet','pinpoint-defense')]
        if nics[0].get('mac') != '02:77:01:00:00:02':
            raise ValueError('Windows device MAC changed')
    else:
        expected = [(1,'nat',''),(2,'intnet','pinpoint-defense')]
    if [(n.get('slot'),n.get('type'),n.get('network')) for n in nics] != expected:
        raise ValueError('Defense VM network attachment mismatch')
    if [n.get('mac') for n in nics] != expected_macs or len(set(expected_macs)) != len(expected_macs):
        raise ValueError('Pinned VM MAC identity changed')
    wanted_promisc = ['deny'] if role=='windows' else ['deny','allow-vms' if role=='target_host' else 'deny']
    if [n.get('promiscuous') for n in nics] != wanted_promisc:
        raise ValueError('Unexpected VM promiscuous mode')
    forwards = vm.get('forwards')
    if not isinstance(forwards,list) or len(forwards) != len(FORWARDS[role]):
        raise ValueError('Unexpected defense management forwarding')
    actual = sorted((f.get('host'),f.get('port'),f.get('guest_port'),f.get('protocol')) for f in forwards)
    wanted = sorted(('127.0.0.1',port,guest,'tcp') for port,guest in FORWARDS[role])
    if actual != wanted:
        raise ValueError('Management forwarding must be exact and loopback-only')


def validate_vm_macs(catalog, vms: list[dict]) -> None:
    """Refuse proposed target MACs already used by foreign VM NICs or duplicate lab NICs."""
    assigned = {}
    catalog_macs = {device.mac:device.name for device in catalog.devices}
    for vm in vms:
        for nic in vm['nics']:
            mac = nic['mac']
            if mac in catalog_macs and not (catalog_macs[mac]=='win01' and vm['name']==VM_NAMES['windows']):
                raise ValueError('A proposed target MAC already belongs to another VM NIC')
            assigned.setdefault(mac,[]).append(vm['name'])
    if any(len(names)>1 and any(name in VM_NAMES.values() for name in names) for names in assigned.values()):
        raise ValueError('A defense VM NIC MAC is duplicated')


def validate_runtime(vm: dict, controllers: list[int], processes: list[dict],
                     listeners: dict, runtime_forwards: dict) -> None:
    """Require the controlled process and real NAT socket, not metadata alone."""
    if len(controllers) != 1:
        raise ValueError('Exactly one same-user VirtualBox controller is required')
    matching = [p for p in processes if p.get('uuid','').lower() == vm['uuid'].lower()]
    ports = [f['port'] for f in vm['forwards']]
    if vm['state'] == 'poweroff':
        if matching or any(listeners.get(p) for p in ports):
            raise ValueError('Powered-off VM retains a process or management listener')
        return
    if vm['state'] != 'running' or len(matching) != 1 or matching[0].get('parent') != controllers[0]:
        raise ValueError('VM process and controller ownership disagree')
    if vm.get('session_pid') and str(matching[0]['pid']) != str(vm['session_pid']):
        raise ValueError('VM session PID changed')
    guests = set()
    for item in vm['forwards']:
        sockets = listeners.get(item['port'],[])
        runtime = runtime_forwards.get(item['port'],[])
        if len(sockets) != 1 or sockets[0][0] != '127.0.0.1':
            raise ValueError('Management listener is missing, shared or non-loopback')
        if len(runtime) != 1 or runtime[0][:2] != ('127.0.0.1',item['guest_port']):
            raise ValueError('Controlled VM lacks the expected active NAT socket')
        guests.add(runtime[0][2])
    if len(guests) > 1:
        raise ValueError('Management forwards do not target the same guest')


def read_private_json(path: Path) -> dict:
    """Open bounded same-user private regular state without following symlinks."""
    try:
        parent = path.parent.lstat()
        if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o077:
            raise ValueError()
        directory = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            actual = os.fstat(directory)
            if (parent.st_dev,parent.st_ino) != (actual.st_dev,actual.st_ino):
                raise ValueError()
            fd = os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        finally:
            os.close(directory)
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 1048576:
                raise ValueError()
            data = json.load(stream)
            if not isinstance(data,dict):
                raise ValueError()
            return data
    except (OSError,ValueError):
        raise ValueError('Private defense state is absent, unsafe or malformed') from None
