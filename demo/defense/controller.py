"""Read-only defense catalog/preflight entry point; lifecycle follows the spike."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

DEMO = Path(__file__).resolve().parents[1]
REPO = DEMO.parent
sys.path.insert(0,str(DEMO))
sys.path.insert(0,str(REPO/'scripts'))
from defense.catalog import load_catalog
from defense.preflight import (VM_NAMES,FORWARDS,read_private_json,check_resources,
                               reject_overlaps,validate_vm,validate_runtime)
from defense.preflight import validate_vm_macs
from defense.preflight import reject_virtualbox_dhcp
import qa_control
import vmlab_preflight

STATE_ROOT = Path.home()/'.local/share/pinpoint-defense/controller'
STATE_FILE = STATE_ROOT/'lab.json'
WINDOWS_ROOT = Path.home()/'.local/share/pinpoint-defense/windows-home'
OWNER_KEY = 'org.pinpoint.defense.issue274'
RAM = {'appliance':4096,'target_host':2048,'windows':3072}


class Collector:
    """Bound every read and the total observation; never print raw child output."""
    def __init__(self):
        self.deadline = time.monotonic()+60

    def run(self, argv: list[str]) -> str:
        """Run one fixed argument-list observation without shell or child stderr."""
        remaining = self.deadline-time.monotonic()
        if remaining <= 0:
            raise ValueError('Host observation deadline exceeded')
        try:
            result = subprocess.run(argv,capture_output=True,text=True,timeout=min(20,remaining),env=dict(os.environ,LC_ALL='C'))
            if result.returncode:
                raise ValueError('Required host observation failed')
            return result.stdout
        except (OSError,subprocess.TimeoutExpired):
            raise ValueError('Required host observation unavailable') from None

    def vbox(self, *args: str) -> str:
        """Collect only bounded VirtualBox metadata, with fixed operations."""
        return self.run(['VBoxManage',*args])


def parse_info(text: str) -> dict:
    """Normalize VirtualBox's quoted storage keys and values."""
    return {k.strip('"'):v.strip('"') for line in text.splitlines() if '=' in line
            for k,v in [line.split('=',1)]}


def merge_nic_policies(data: dict,details: str) -> dict:
    """Cross-check detailed NIC rows because VBox machine output omits this policy."""
    result=dict(data)
    for number in range(1,9):
        rows=re.findall(r'^NIC '+str(number)+r':\s*(.*)$',details,re.M)
        if len(rows)!=1:raise ValueError('Detailed NIC inventory missing or duplicated')
        row=rows[0]
        if data.get(f'nic{number}','none')=='none':
            if row!='disabled':raise ValueError('NIC enabled state disagrees across observations')
            continue
        match=re.search(r'MAC: ([A-Fa-f0-9]{12}),',row)
        policy=re.search(r'Promisc Policy: (deny|allow-vms|allow-all),',row)
        if not match or match[1].lower()!=data.get(f'macaddress{number}','').lower() or not policy:
            raise ValueError('Detailed NIC identity or policy unavailable')
        result[f'nicpromisc{number}']=policy[1]
    return result


def observed_info(collector,identifier: str) -> dict:
    """Read both bounded VBox views; no unobserved NIC policy receives a default."""
    data=parse_info(collector.vbox('showvminfo',identifier,'--machinereadable'))
    return merge_nic_policies(data,collector.vbox('showvminfo',identifier))


def vm_record(data: dict, owner: str | None) -> dict:
    """Keep only nonsecret NIC/management identity fields needed by the gates."""
    nics = []
    for i in range(1,9):
        kind = data.get(f'nic{i}','none')
        if kind == 'none':
            continue
        raw = data.get(f'macaddress{i}','').lower()
        if not re.fullmatch(r'[a-f0-9]{12}',raw):
            raise ValueError('VM MAC inventory unavailable')
        if data.get(f'nicpromisc{i}') not in {'deny','allow-vms','allow-all'}:
            raise ValueError('VM promiscuous policy was not observed')
        nics.append({'slot':i,'type':kind,'network':data.get(f'intnet{i}','') if kind=='intnet' else '',
                     'mac':':'.join(raw[n:n+2] for n in range(0,12,2)),
                     'promiscuous':data[f'nicpromisc{i}']})
    forwards = []
    for key,value in data.items():
        if key.startswith('Forwarding('):
            parts = value.split(',')
            if len(parts) != 6 or not parts[3].isdigit() or not parts[5].isdigit():
                raise ValueError('Invalid management forwarding inventory')
            forwards.append({'host':parts[2],'port':int(parts[3]),'guest_port':int(parts[5]),'protocol':parts[1]})
    return {'name':data.get('name'),'uuid':data.get('UUID','').lower(),'owner':owner,
            'state':data.get('VMState'),'session_pid':data.get('SessionPID'),
            'memory_mib':int(data.get('memory','0')),'nics':nics,'forwards':forwards}


def network_inventory(collector: Collector) -> list[str]:
    """Collect host/Docker ranges plus nonsecret configured VPN IPv4 ranges."""
    occupied = []
    routes = json.loads(collector.run(['ip','-j','-4','route','show','table','all']))
    occupied.extend(r['dst'] for r in routes if r.get('dst') and r['dst']!='default')
    for interface in json.loads(collector.run(['ip','-j','-4','addr','show'])):
        for address in interface.get('addr_info',[]):
            occupied.append(f"{address['local']}/{address['prefixlen']}")
    ids = collector.run(['docker','network','ls','-q']).split()
    if any(not re.fullmatch(r'[a-f0-9]{12,64}',value) for value in ids):
        raise ValueError('Invalid Docker network inventory')
    if ids:
        for network in json.loads(collector.run(['docker','network','inspect',*ids])):
            occupied.extend(c['Subnet'] for c in network['IPAM'].get('Config') or [] if c.get('Subnet'))
    # Do not read vpn.data, secrets, certificates or connection names.
    profiles = collector.run(['nmcli','-t','-f','UUID,TYPE','connection','show']).splitlines()
    active = collector.run(['nmcli','-t','-f','UUID,TYPE','connection','show','--active']).splitlines()
    vpn_types = {'vpn','wireguard','tun','ip-tunnel'}
    if any(row.rsplit(':',1)[-1] in vpn_types for row in active):
        raise ValueError('Active VPN/tunnel prevents defense startup preflight')
    for row in profiles:
        identifier,kind = row.rsplit(':',1)
        if kind not in vpn_types:
            continue
        if not re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',identifier):
            raise ValueError('VPN profile identity unavailable')
        value = collector.run(['nmcli','-g','ipv4.routes,ipv4.addresses','connection','show',identifier])
        occupied.extend(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b',value))
    return occupied


def allocated_mib(root: Path) -> int:
    """Count only owned nonsymlink VDI allocations for conservative disk planning."""
    if not root.exists():
        return 0
    info = root.lstat()
    if root.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Unsafe private VM disk directory')
    total = 0
    for path in root.rglob('*.vdi'):
        info = path.lstat()
        if path.is_symlink() or not path.is_file() or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise ValueError('Unsafe owned virtual disk')
        total += (info.st_blocks*512+1048575)//1048576
    return total


def intended_manifest(catalog) -> dict:
    """Label planned listeners honestly; no live observation is implied."""
    return {'network':str(catalog.network),'device_count':len(catalog.devices),'live_verified':False,
            'devices':[{'target':d.name,'kind':d.kind,'mac':d.mac,'mode':d.mode,
                        'initial_address':d.address,'listeners':[{'service':p.service,
                        'protocol':p.protocol,'port':p.port,'expected_plugin':p.plugin,
                        'monitoring':p.monitoring,'scan_eligible':catalog.scan_eligible(p)}
                        for p in d.listeners]} for d in catalog.devices]}


def collect_preflight(catalog) -> dict:
    """Observe local metadata only; missing preparation never authorizes a start."""
    collector = Collector()
    blockers = []
    state = read_private_json(STATE_FILE) if STATE_FILE.exists() else {}
    pins = state.get('vms',{})
    if not isinstance(pins,dict):
        raise ValueError('Private ownership state is malformed')
    if not state:
        blockers.append('Controller is not prepared; no lifecycle operation is available yet')
    reject_overlaps(network_inventory(collector))
    reject_virtualbox_dhcp(collector.vbox('list','dhcpservers'))
    names = collector.vbox('list','vms').splitlines()
    all_vms, records = [], {}
    for line in names:
        match = re.search(r'\{([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})\}$',line)
        if not match:
            raise ValueError('VirtualBox inventory is malformed')
        identifier = match[1]
        data = observed_info(collector,identifier)
        role = next((r for r,n in VM_NAMES.items() if n==data.get('name')),None)
        owner = None
        if role:
            value = collector.vbox('getextradata',identifier,OWNER_KEY).strip()
            owner = value[7:] if value.startswith('Value: ') else None
        record = vm_record(data,owner)
        all_vms.append(record)
        if role:
            records[role] = record
        elif any(n['network']=='pinpoint-defense' for n in record['nics']):
            blockers.append('A foreign VM is attached to the defense network')
        if record['state']!='poweroff' and role is None:
            blockers.append('An unrelated VM is running or transitional')
    managers,processes = vmlab_preflight.inventory()
    validate_vm_macs(catalog,all_vms)
    listeners = vmlab_preflight.tcp_listeners([2250,18080,2260])
    for role in VM_NAMES:
        if role not in records:
            blockers.append(f'{role}: VM is not prepared')
            continue
        pin = pins.get(role)
        if not isinstance(pin,dict) or set(pin)!={'uuid','owner','macs'}:
            blockers.append(f'{role}: private ownership pin is not prepared')
            continue
        record = records[role]
        try:
            validate_vm(record,role,pin['uuid'],pin['owner'],pin['macs'])
            if record['memory_mib'] != RAM[role]:
                raise ValueError('VM allocation differs from the recorded planning budget')
            forwards = {}
            if record['state']=='running' and FORWARDS[role]:
                forwards = vmlab_preflight.nat_forwards(collector.vbox('debugvm',record['uuid'],'info','nat0'))
            validate_runtime(record,managers,[dict(p,pid=pid) for pid,p in processes.items()],listeners,forwards)
            after = vm_record(observed_info(collector,record['uuid']),record['owner'])
            if after != record:
                raise ValueError('VM configuration changed during observation')
        except ValueError as error:
            blockers.append(f'{role}: {error}')
    final_managers,final_processes = vmlab_preflight.inventory()
    if managers != final_managers or processes != final_processes:
        blockers.append('VM/controller process identity changed during observation')
    if len(managers)!=1:
        blockers.append('Exactly one same-user VirtualBox controller is required')
    memory = re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)
    if not memory:
        raise ValueError('Host memory inventory unavailable')
    available = int(memory[1])//1024
    free = shutil.disk_usage(Path.home()).free//1048576
    # Existing Windows maximum minus allocated blocks; new target-host maximum;
    # 8 GiB snapshot growth, 2 GiB appliance growth, 1 GiB logs, 10 GiB host reserve.
    disk_required = max(40960-allocated_mib(WINDOWS_ROOT),0)+max(16384-allocated_mib(STATE_ROOT/'target-host'),0)+8192+2048+1024+10240
    new_memory = [RAM[r] for r in RAM if records.get(r,{}).get('state')!='running']
    required = sum(new_memory)+3584
    try:
        check_resources(available,free,new_memory,disk_required)
    except ValueError as error:
        blockers.append(str(error))
    if Path('/sys/module/kvm_amd').exists() and new_memory:
        blockers.append('KVM holds AMD-V; owner must release it before any VirtualBox start')
    return {'ready':not blockers,'live_authorized':False,'network':str(catalog.network),
            'expected_device_count':15,'available_mib':available,'required_available_mib':required,
            'free_disk_mib':free,'required_disk_mib':disk_required,'blockers':blockers,
            'vms':{r:{'name':v['name'],'state':v['state']} for r,v in records.items()}}


def main(argv=None) -> int:
    """Expose read-only commands until provision/isolation has been implemented."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    for name in ['manifest','preflight']:
        item = sub.add_parser(name)
        item.add_argument('--json',action='store_true')
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog()
        if args.command=='manifest':
            result = intended_manifest(catalog)
        else:
            with qa_control.claim():
                result = collect_preflight(catalog)
        if args.json:
            print(json.dumps(result,indent=2))
        elif args.command=='manifest':
            print('Intended catalog only; live discovery/monitoring is not verified.')
            for device in result['devices']:
                ports = ', '.join(f"{p['protocol']}/{p['port']} {p['service']}" for p in device['listeners'])
                print(f"{device['target']:12} {device['initial_address']:12} {device['mac']} {device['mode']:6} {ports}")
        else:
            print('Defense startup preflight: '+('READY' if result['ready'] else 'BLOCKED'))
            for reason in result['blockers']:
                print('  '+reason)
        return 0 if args.command=='manifest' or result['ready'] else 1
    except (ValueError,OSError,TypeError,KeyError):
        print('Defense preflight unavailable: required metadata or private state is unsafe/incomplete.',file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
