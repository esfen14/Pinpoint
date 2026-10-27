"""Validate the fixed defense device catalog before it reaches command execution."""
from dataclasses import dataclass
import ipaddress
import json
from pathlib import Path
import re

NETWORK = ipaddress.ip_network('10.77.1.0/27')
TARGETS = ('dhcp01','win01','web03','api02','ftp01','mail01','dns01','db01',
           'snmp02','ssh-alt02','dynweb01','dynapp01','dynmail01','dynsnmp01','dynweb02')
PLUGINS = {'ssh':'check_ssh','http':'check_http','https':'check_http',
           'ftp':'check_ftp','smtp':'check_smtp','imap':'check_tcp','dns':'check_dns',
           'pgsql':'check_pgsql','snmp':'check_snmp','ncpa':'check_ncpa.py',
           'dhcp':None,'tcp':'check_tcp'}
RESERVED_HIGH_PORTS = frozenset({2222,2223,2250,2260,5693,8000,18080,18087,*range(2200,2206)})


@dataclass(frozen=True)
class Listener:
    """One intended listener; its plugin is an expectation, not live monitoring proof."""
    service: str
    protocol: str
    port: int
    plugin: str | None
    monitoring: str = 'pending'


@dataclass(frozen=True)
class Device:
    """Stable catalog identity; DHCP addresses are initial reservations only."""
    number: int
    name: str
    kind: str
    mac: str
    address: str
    mode: str
    client_id: str | None
    listeners: tuple[Listener, ...]


@dataclass(frozen=True)
class Catalog:
    """Validated immutable topology and port scope shared by all lab components."""
    network: ipaddress.IPv4Network
    appliance_address: str
    pool: tuple[str, ...]
    static_slots: tuple[str, ...]
    tcp_range: tuple[int, int]
    udp_ports: tuple[int, ...]
    devices: tuple[Device, ...]

    def target(self, name: str) -> Device:
        """Resolve only an exact catalog name without echoing invalid CLI input."""
        for device in self.devices:
            if device.name == name:
                return device
        raise ValueError('Unknown defense target')

    def scan_eligible(self, listener: Listener) -> bool:
        """Report intended scan inclusion independently of actual plugin state."""
        if listener.protocol == 'tcp':
            return self.tcp_range[0] <= listener.port <= self.tcp_range[1]
        return listener.port in self.udp_ports


def fields(data: object, expected: set[str]) -> None:
    """Reject malformed/extra fields instead of forwarding unknown settings."""
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError('Invalid defense catalog fields')


def parse_catalog(data: dict) -> Catalog:
    """Validate the entire fixed catalog, returning immutable safe values."""
    fields(data, {'version','network','appliance_address','dhcp_pool','static_slots','scan','devices'})
    if data['version'] != 1 or data['network'] != str(NETWORK) or data['appliance_address'] != '10.77.1.1':
        raise ValueError('Unapproved defense network')
    pool = tuple(f'10.77.1.{n}' for n in range(20,30))
    slots = tuple(f'10.77.1.{n}' for n in range(15,20))
    if data['dhcp_pool'] != list(pool) or data['static_slots'] != list(slots):
        raise ValueError('Invalid DHCP pool or transition slots')
    fields(data['scan'], {'tcp','udp'})
    if data['scan'] != {'tcp':[1,10000], 'udp':[53,161]}:
        raise ValueError('Unapproved defense scan ports')
    if not isinstance(data['devices'], list) or len(data['devices']) != len(TARGETS):
        raise ValueError('The defense catalog requires fifteen devices')
    devices = []
    macs, addresses, client_ids = set(), set(), set()
    for number, entry in enumerate(data['devices'], 1):
        fields(entry, {'number','name','kind','mac','address','mode','client_id','listeners'})
        if type(entry['number']) is not int or entry['number'] != number or entry['name'] != TARGETS[number-1]:
            raise ValueError('Invalid defense target identity')
        kind = 'windows' if number == 2 else 'linux'
        mode = 'dhcp' if number >= 11 else 'static'
        expected_address = f'10.77.1.{number+9 if mode == "dhcp" else number+1}'
        if entry['kind'] != kind or entry['mode'] != mode or entry['address'] != expected_address:
            raise ValueError('Invalid device kind or address allocation')
        mac = entry['mac']
        if mac != f'02:77:01:00:00:{number:02x}':
            raise ValueError('Invalid local unicast MAC')
        if mac in macs or entry['address'] in addresses:
            raise ValueError('Duplicate device MAC or address')
        macs.add(mac); addresses.add(entry['address'])
        client_id = entry['client_id']
        if mode == 'dhcp':
            if client_id != 'pinpoint-defense-' + entry['name'] or client_id in client_ids:
                raise ValueError('Invalid persistent DHCP client identity')
            client_ids.add(client_id)
        elif client_id is not None:
            raise ValueError('Static devices cannot have DHCP client identifiers')
        listeners = []
        occupied = set()
        if not isinstance(entry['listeners'], list) or not entry['listeners']:
            raise ValueError('A defense target needs real listener presets')
        for item in entry['listeners']:
            fields(item, {'service','protocol','port','plugin','monitoring'})
            if item['service'] not in PLUGINS or item['plugin'] != PLUGINS[item['service']]:
                raise ValueError('Invalid listener/plugin expectation')
            if item['protocol'] not in {'tcp','udp'} or type(item['port']) is not int or not 1 <= item['port'] <= 65535:
                raise ValueError('Invalid listener port/protocol')
            if item['port'] in RESERVED_HIGH_PORTS and not (entry['name']=='ssh-alt02' and item['service']=='ssh' and item['port']==2223):
                if not (kind=='windows' and item['service']=='ncpa' and item['port']==5693):
                    raise ValueError('Reserved port cannot become a Linux listener preset')
            if (item['service']=='ncpa') != (kind=='windows'):
                raise ValueError('NCPA listener belongs only to the Windows slot')
            if item['monitoring'] not in {'pending','needs_settings','infrastructure'}:
                raise ValueError('Invalid monitoring expectation')
            key = item['protocol'], item['port']
            if key in occupied:
                raise ValueError('Duplicate listener on a target')
            occupied.add(key)
            listeners.append(Listener(**item))
        devices.append(Device(number,entry['name'],kind,mac,entry['address'],mode,client_id,tuple(listeners)))
    return Catalog(NETWORK,'10.77.1.1',pool,slots,(1,10000),(53,161),tuple(devices))


def load_catalog() -> Catalog:
    """Load the versioned catalog only; no CLI-supplied file or environment override."""
    path = Path(__file__).with_name('manifest.json')
    if path.stat().st_size > 131072:
        raise ValueError('Defense catalog exceeds size limit')
    return parse_catalog(json.loads(path.read_text()))


def listener_request(catalog: Catalog, target: str, service: str, port: int,
                     *, occupied: list[tuple[str,int,str]] | None = None) -> Listener:
    """Allow baseline listeners or bounded HTTP/TCP examples; never management/NCPA."""
    device = catalog.target(target)
    if device.kind != 'linux' or type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Listener changes require a Linux demo target and valid port')
    if service == 'dhcp':
        raise ValueError('Use the dedicated DHCP server controls')
    preset = next((p for p in device.listeners if p.service == service and p.port == port),None)
    if preset is None:
        if service not in {'http','tcp'} or not 1024 <= port <= 65535 or port in RESERVED_HIGH_PORTS:
            raise ValueError('Unsupported service/port pair or reserved port')
        preset = Listener(service,'tcp',port,PLUGINS[service])
    for protocol, used_port, used_service in occupied or []:
        if protocol == preset.protocol and used_port == port and used_service != service:
            raise ValueError('Another owned listener already uses this port')
    return preset


def render_dnsmasq(catalog: Catalog, reservations: dict, lease_seconds: int = 600) -> str:
    """Render only known MAC reservations on the isolated NIC with no router/DNS."""
    clients = [d for d in catalog.devices if d.mode == 'dhcp']
    if not isinstance(reservations, dict) or set(reservations) != {d.name for d in clients}:
        raise ValueError('DHCP reservations must cover exactly the five known clients')
    addresses = [v for v in reservations.values() if v is not None]
    if any(not isinstance(v,str) or v not in catalog.pool for v in addresses) or len(set(addresses)) != len(addresses):
        raise ValueError('Invalid or colliding DHCP reservation')
    if type(lease_seconds) is not int or not 60 <= lease_seconds <= 3600:
        raise ValueError('DHCP lease must be 60 through 3600 seconds')
    lines = ['port=0','interface=eth0','bind-interfaces','except-interface=lo',
             'dhcp-authoritative','dhcp-ignore=tag:!known',
             f'dhcp-range={catalog.pool[0]},{catalog.pool[-1]},{catalog.network.netmask},{lease_seconds}s',
             'dhcp-option=option:router','dhcp-option=option:dns-server',
             'dhcp-leasefile=/data/dhcp.leases','log-dhcp','log-facility=/data/dhcp.log']
    for device in clients:
        if reservations[device.name] is not None:
            lines.append(f'dhcp-host={device.mac},{reservations[device.name]}')
    return '\n'.join(lines)+'\n'
