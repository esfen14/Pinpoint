"""Presenter controls for the existing issue-274 laptop Docker pilot."""
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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from defense.catalog import load_catalog, listener_request
from defense import address_mode, dhcp_control, dhcp_journal
from defense.host_attach import observe_process
from defense.host_members import validate_parent_attachments, validate_vm_membership, collect_vm_inventory
from defense.host_resources import swap_rate, check_host_resources, reject_foreign_overlaps
import qa_control

ROOT=Path.home()/'.local/share/pinpoint-defense/host-docker'
PILOT=ROOT/'pilot-catalog'
CONTEXT=ROOT/'context/context.json'
PINS=ROOT/'presenter-pins.json'
PROGRAMS={'ssh':'ssh','http':'web','https':'web','ftp':'ftp','smtp':'smtp','imap':'imap','dns':'dns','snmp':'snmp','pgsql':'pgsql'}


def require_no_dhcp_intent(root):
    """Refuse mutations while any DHCP recovery intent occupies its fixed name.

    Caller must hold the canonical claim, as must the future journal writer.
    Any entry, including malformed data or a dangling symlink, blocks changes.
    """
    fd=dhcp_journal.directory(root)
    try:
        for name in (dhcp_journal.NAME,address_mode.NAME):
            try:
                os.stat(name,dir_fd=fd,follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError('DHCP recovery intent requires inspection')
    finally:
        os.close(fd)


def service_program(catalog,target,service):
    device=catalog.target(target)
    if device.kind!='linux' or service not in PROGRAMS or service not in {x.service for x in device.listeners}:
        raise ValueError('Service is not a permitted target preset')
    return PROGRAMS[service]


def validate_container(obj,device,root,context,pin):
    if not isinstance(obj,dict) or obj.get('Id')!=pin['id'] or obj.get('Image')!=pin['image']:
        raise ValueError('Container identity changed')
    if not re.fullmatch(r'[0-9a-f]{64}',obj['Id']) or not re.fullmatch(r'sha256:[0-9a-f]{64}',obj['Image']):
        raise ValueError('Invalid immutable identity')
    config=obj.get('Config',{}); host=obj.get('HostConfig',{})
    if obj.get('Name')!='/pinpoint274-host-'+device.name+'-pilot' or config.get('Cmd')!=['python3','/opt/pinpoint/defense/node.py','init',device.name]:
        raise ValueError('Unexpected container command or name')
    labels=config.get('Labels') or {}
    if labels.get('org.pinpoint.defense.issue')!='274' or labels.get('org.pinpoint.defense.role')!='temporary-pilot':
        raise ValueError('Container is not the owned pilot')
    if host.get('Privileged') or host.get('NetworkMode')!=('none' if device.mode=='dhcp' else 'pinpoint274-host-test'):
        raise ValueError('Container privilege or network changed')
    mounts={(m.get('Source'),m.get('Destination'),m.get('RW'),m.get('Type')) for m in obj.get('Mounts',[])}
    data_root=root.parent/'pilot-web03' if device.name=='web03' else root/device.name
    expected={(str(data_root/'identity'),'/identity',True,'bind'),(str(data_root/'data'),'/data',True,'bind'),
              (str(context),'/etc/pinpoint-defense/context.json',False,'bind')}
    if device.name in {'snmp02','dynsnmp01'}:
        expected.add((str(root/'private/snmp-community'),'/run/secrets/snmp-community',False,'bind'))
    if mounts!=expected:raise ValueError('Container mounts changed')
    return obj


def run(argv,*,input_text=None,timeout=30):
    try:
        result=subprocess.run(argv,input=input_text,capture_output=True,text=True,timeout=timeout)
        if result.returncode:raise ValueError('Docker operation failed')
        return result.stdout
    except (OSError,subprocess.TimeoutExpired):raise ValueError('Docker operation unavailable') from None


def inspect(device,pin):
    data=json.loads(run(['docker','inspect',pin['id']]))
    if len(data)!=1:raise ValueError('Container inspection failed')
    return validate_container(data[0],device,PILOT,CONTEXT,pin)


def read_pins():
    info=PINS.lstat()
    if not PINS.is_file() or PINS.is_symlink() or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:
        raise ValueError('Unsafe presenter pins')
    value=json.loads(PINS.read_text())
    if set(value)!={d.name for d in load_catalog().devices if d.kind=='linux'}:raise ValueError('Incomplete presenter pins')
    return value


def node(device,pin,operation):
    obj=inspect(device,pin)
    if not obj['State']['Running']:raise ValueError('Target container is stopped')
    output=run(['docker','exec','-i',pin['id'],'python3','/opt/pinpoint/defense/node.py','control',device.name],input_text=json.dumps({'operation':operation}))
    result=json.loads(output)
    if result.get('target')!=device.name:raise ValueError('Target response changed')
    return result


def reserved_address(catalog,pins,device):
    """Use the saved allocator reservation for a DHCP client's current address."""
    if device.mode!='dhcp':return device.address
    server=node(catalog.target('dhcp01'),pins['dhcp01'],'server-observe')
    address=server.get('reservations',{}).get(device.name)
    if address not in catalog.pool:
        raise ValueError('DHCP reservation unavailable')
    return address


def enroll(catalog):
    if PINS.exists() or PINS.is_symlink():raise ValueError('Presenter pins already exist')
    pins={}
    for device in (d for d in catalog.devices if d.kind=='linux'):
        data=json.loads(run(['docker','inspect','pinpoint274-host-'+device.name+'-pilot']))
        if len(data)!=1:raise ValueError('Pilot target missing')
        pin={'id':data[0]['Id'],'image':data[0]['Image']}
        validate_container(data[0],device,PILOT,CONTEXT,pin)
        observed=node(device,pin,'inspect')
        if not observed.get('network_safe') or observed.get('addresses')!=[device.address]:raise ValueError('Pilot target network is not ready')
        pins[device.name]=pin
    fd=os.open(PINS,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(pins,stream);stream.write('\n')
    return pins


def service(catalog,pins,target,name,action):
    program=service_program(catalog,target,name)
    if action not in {'start','stop'}:raise ValueError('Invalid service action')
    check_host_network(pins)
    device=catalog.target(target);pin=pins[target]
    before=node(device,pin,'inspect')
    if not before.get('network_safe') or before.get('addresses')!=[reserved_address(catalog,pins,device)]:raise ValueError('Unsafe target network')
    states={v['program']:v['state'] for v in before['services']}
    if program not in states:raise ValueError('Owned service is unavailable')
    if program=='smtp':
        return smtp_service(device,pin,before,action)
    desired='RUNNING' if action=='start' else 'STOPPED'
    if states[program]!=desired:
        inspect(device,pin)
        run(['docker','exec',pin['id'],'/usr/bin/supervisorctl','-c','/run/supervisord.conf',action,program])
    after=node(device,pin,'inspect')
    if {v['program']:v['state'] for v in after['services']}.get(program)!=desired:raise ValueError('Service did not reach requested state')
    expected={(item.protocol,item.port) for item in device.listeners if PROGRAMS.get(item.service)==program}
    observed={(item.get('protocol'),item.get('port')) for item in after.get('listeners',[])}
    if action=='start' and not expected.issubset(observed) or action=='stop' and expected & observed:
        raise ValueError('Service listener did not reach requested state')
    return after


def smtp_service(device,pin,before,action):
    """Control Supervisor and the Postfix master, which can outlive its wrapper."""
    def state(value):return {v['program']:v['state'] for v in value['services']}.get('smtp')
    def listening(value):return {'protocol':'tcp','port':25} in value.get('listeners',[])
    def supervisor(verb):
        inspect(device,pin)
        run(['docker','exec',pin['id'],'/usr/bin/supervisorctl','-c','/run/supervisord.conf',verb,'smtp'])
    def stop_master():
        inspect(device,pin)
        run(['docker','exec',pin['id'],'/usr/sbin/postfix','-c','/run/postfix','stop'])
    if action=='stop':
        if state(before) in {'RUNNING','STARTING'}:supervisor('stop')
        current=node(device,pin,'inspect')
        if listening(current):stop_master()
        after=node(device,pin,'inspect')
        if listening(after) or state(after) in {'RUNNING','STARTING'}:raise ValueError('SMTP did not stop')
    else:
        if state(before)!='RUNNING':
            if listening(before):stop_master()
            supervisor('start')
        after=node(device,pin,'inspect')
        if state(after)!='RUNNING' or not listening(after):raise ValueError('SMTP did not start')
    return after


MAX_EXTRA_PORTS=4


def helper_call(pin,*args):
    """Run the fixed in-container port helper; arguments are validated by the callers."""
    source=Path(__file__).with_name('extra_listener.py').read_text()
    return run(['docker','exec',pin['id'],'python3','-c',source,*args],timeout=30)


def port_target(catalog,pins,target):
    device=catalog.target(target)
    if device.kind!='linux':raise ValueError('Port controls require a Linux demo target')
    check_host_network(pins)
    pin=pins[target];inspect(device,pin)
    return device,pin


def extra_ports(pin):
    ports=[]
    for line in helper_call(pin,'list').split():
        if not line.isdigit():raise ValueError('Unexpected helper output')
        ports.append(int(line))
    return sorted(ports)


def observed_tcp(device,pin):
    current=node(device,pin,'inspect')
    expected=device.address if device.mode=='static' else None
    if not current.get('network_safe') or expected is not None and current.get('addresses')!=[expected]:
        raise ValueError('Unsafe target network')
    return {item.get('port') for item in current.get('listeners',[]) if item.get('protocol')=='tcp'}


def port_list(catalog,pins,target):
    device,pin=port_target(catalog,pins,target)
    return {'baseline':[item.port for item in device.listeners],'extra':extra_ports(pin)}


def port_open(catalog,pins,target,service,port):
    """Open one checked HTTP/TCP port that is not a baseline, reserved or already used port."""
    if not isinstance(service,str) or type(port) is not int:raise ValueError('Invalid port request')
    listener_request(catalog,target,service,port)
    device,pin=port_target(catalog,pins,target)
    if any(item.port==port for item in device.listeners):raise ValueError('Baseline ports use break and fix')
    if port in observed_tcp(device,pin):raise ValueError('Port is already in use')
    if len(extra_ports(pin))>=MAX_EXTRA_PORTS:raise ValueError('Too many extra ports on this target')
    helper_call(pin,'open',service,str(port))
    try:
        if port not in observed_tcp(device,pin):raise ValueError('Listener did not start')
    except BaseException:
        try:helper_call(pin,'close',str(port))
        except ValueError:pass
        raise


def port_close(catalog,pins,target,port):
    if type(port) is not int:raise ValueError('Invalid port request')
    device,pin=port_target(catalog,pins,target)
    if port not in extra_ports(pin):raise ValueError('Only extra ports opened here can be closed')
    helper_call(pin,'close',str(port))
    if port in observed_tcp(device,pin):raise ValueError('Listener did not stop')


def port_restore(catalog,pins,target):
    device,pin=port_target(catalog,pins,target)
    for port in extra_ports(pin):
        helper_call(pin,'close',str(port))
    if extra_ports(pin):raise ValueError('Extra ports remain')


def port_restore_all(catalog,pins):
    for device in catalog.devices:
        if device.kind=='linux':
            port_restore(catalog,pins,device.name)


class DockerAddressClient:
    """Fixed Docker adapter for one DHCP client's single address."""
    def __init__(self,catalog,pins,target):
        self.catalog=catalog;self.pins=pins
        self.device=address_mode.client(catalog,target);self.pin=pins[target]
    def state(self):
        check_host_network(self.pins);inspect(self.device,self.pin)
        current=node(self.device,self.pin,'inspect')
        if not current.get('network_safe'):raise ValueError('Unsafe client network')
        server=node(self.catalog.target('dhcp01'),self.pins['dhcp01'],'inspect')
        running={v['program']:v['state'] for v in server['services']}.get('dhcp')=='RUNNING'
        return {'addresses':list(current['addresses']),'reserved':reserved_address(self.catalog,self.pins,self.device),'server_running':running}
    def release(self):
        inspect(self.device,self.pin)
        node_request(self.device,self.pin,{'operation':'lease-release'})
    def acquire(self,address):
        inspect(self.device,self.pin)
        node_request(self.device,self.pin,{'operation':'lease-acquire','expected_address':address})
    def ip_address(self,verb,address):
        inspect(self.device,self.pin)
        valid=ipaddress.ip_address(address)
        if valid not in self.catalog.network:raise ValueError('Address is outside the demo network')
        run(['docker','exec','--privileged',self.pin['id'],'ip','addr',verb,'%s/%d'%(valid,self.catalog.network.prefixlen),'dev','eth0'])
    def add_static(self,address):
        self.ip_address('add',address)
    def remove_static(self,address):
        self.ip_address('del',address)


def address_mode_show(catalog,pins,target):
    return address_mode.show(catalog,DockerAddressClient(catalog,pins,target).state())


def address_mode_set(catalog,pins,target,mode,address):
    lab=DockerAddressClient(catalog,pins,target)
    if mode=='static':
        occupied=set()
        for device in catalog.devices:
            if device.mode=='dhcp' and device.name!=target:
                occupied.update(DockerAddressClient(catalog,pins,device.name).state()['addresses'])
        address_mode.to_static(ROOT,catalog,lab,target,address,occupied=occupied)
    elif mode=='dhcp':
        address_mode.to_dhcp(ROOT,catalog,lab,target)
    else:
        raise ValueError('Invalid address mode')


def address_mode_recover(catalog,pins):
    record=address_mode.read_intent(ROOT,catalog)
    if record is not None:
        address_mode.recover(ROOT,catalog,DockerAddressClient(catalog,pins,record['target']))


EPHEMERAL_PORT_START=32768
# Real daemons that also open a second socket: dnsmasq answers DNS over TCP, snmpd opens SMUX, dhclient binds UDP 68.
COMPANIONS={'dns01':{('tcp',53)},'snmp02':{('tcp',199)},'dynsnmp01':{('tcp',199)}}


def observed_manifest(catalog,pins,vm_pins):
    """Read-only record of what is actually running: MAC, IP, live listeners, expected plugins."""
    check_host_network(pins)
    devices=[];consistent=True
    for device in catalog.devices:
        entry={'number':device.number,'name':device.name,'kind':device.kind,'mode':device.mode}
        if device.kind!='linux':
            mac=vm_pins['windows']['mac']
            entry.update(observed=False,mac=mac,mac_matches=mac==device.mac,ip=device.address,
                         listeners=[{'service':l.service,'protocol':l.protocol,'port':l.port,'plugin':l.plugin,'live':None} for l in device.listeners],
                         unexpected_listeners=[],companion_listeners=[],plugin_status='expected',
                         note='Windows VM: IP and listener are not observable by the presenter; the MAC comes from the pinned VM and the rest from Pinpoint')
            consistent=consistent and entry['mac_matches']
            devices.append(entry);continue
        pin=pins[device.name];inspect(device,pin)
        current=node(device,pin,'inspect')
        addresses=current.get('addresses') or []
        ip=addresses[0] if len(addresses)==1 else None
        observed={(item.get('protocol'),item.get('port')) for item in current.get('listeners',[])}
        expected={(l.protocol,l.port) for l in device.listeners}
        listeners=[]
        for l in device.listeners:
            listeners.append({'service':l.service,'protocol':l.protocol,'port':l.port,'plugin':l.plugin,'live':(l.protocol,l.port) in observed})
        companions=set(COMPANIONS.get(device.name,()))
        if device.mode=='dhcp':
            companions.add(('udp',68))
        unexpected=[];companion=[]
        for protocol,port in sorted(observed-expected,key=lambda item:(item[0],item[1])):
            if (protocol,port) in companions:
                companion.append({'protocol':protocol,'port':port})
            elif port<EPHEMERAL_PORT_START:
                unexpected.append({'protocol':protocol,'port':port})
        entry.update(observed=True,mac=current.get('observed_mac'),mac_matches=current.get('observed_mac')==device.mac,ip=ip,
                     ip_matches=ip==reserved_address(catalog,pins,device),listeners=listeners,companion_listeners=companion,unexpected_listeners=unexpected,plugin_status='expected')
        consistent=consistent and entry['mac_matches'] and entry['ip_matches'] and all(l['live'] for l in listeners) and not unexpected
        devices.append(entry)
    return {'network':str(catalog.network),'appliance_address':catalog.appliance_address,'devices':devices,
            'vms':{'appliance_mac':vm_pins['appliance']['mac'],'windows_mac':vm_pins['windows']['mac']},'consistent':consistent}


def dhcp_intent_present():
    return os.path.lexists(ROOT/dhcp_journal.NAME)


def running(device,pins):
    try:
        return bool(inspect(device,pins[device.name])['State']['Running'])
    except ValueError:
        return False


def static_clients(catalog,pins):
    names=[]
    for device in catalog.devices:
        if device.mode=='dhcp' and running(device,pins) and address_mode_show(catalog,pins,device.name)['mode']=='static':
            names.append(device.name)
    return names


def misplaced_clients(catalog,pins):
    moves=[]
    for device in catalog.devices:
        if device.mode=='dhcp' and reserved_address(catalog,pins,device)!=device.address:
            moves.append((device.name,device.address))
    return moves


def verify_baseline(catalog,pins):
    """Every Linux target runs, holds its catalog address, runs all daemons and has no extra ports."""
    if dhcp_intent_present() or address_mode.intent_exists(ROOT):
        raise ValueError('A recovery intent remains')
    for device in catalog.devices:
        if device.kind!='linux':continue
        pin=pins[device.name]
        if not inspect(device,pin)['State']['Running']:raise ValueError('Target is not running')
        current=node(device,pin,'inspect')
        if not current.get('network_safe') or current.get('addresses')!=[device.address]:raise ValueError('Target address is not the baseline')
        if any(v['state']!='RUNNING' for v in current['services']):raise ValueError('A target daemon is not running')
        if extra_ports(pin):raise ValueError('Extra ports remain')


def reset(catalog,pins):
    """Idempotently return the lab to its baseline, recovering interrupted changes first."""
    check_host_network(pins)
    if dhcp_intent_present():
        dhcp_control.recover(ROOT,catalog,DockerDhcpLab(catalog,pins))
    address_mode_recover(catalog,pins)
    for name in static_clients(catalog,pins):
        address_mode_set(catalog,pins,name,'dhcp',None)
    lifecycle(catalog,pins,'up')
    for name,address in misplaced_clients(catalog,pins):
        dhcp_control.move(ROOT,catalog,DockerDhcpLab(catalog,pins),name,address)
    port_restore_all(catalog,pins)
    verify_baseline(catalog,pins)


def lifecycle_order(catalog,action):
    if action not in {'up','down'}:raise ValueError('Unsupported lifecycle action')
    devices=[d for d in catalog.devices if d.kind=='linux']
    return devices if action=='up' else list(reversed(devices))


def target_order(catalog,action,target=None):
    devices=lifecycle_order(catalog,action)
    if target is None:return devices
    device=catalog.target(target)
    if device.kind!='linux':raise ValueError('Host control requires a Linux pilot target')
    return [device]


def read_host_counters():
    """Return available RAM and free disk in MiB and the cumulative swap-in/out page counters."""
    available=None
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            available=int(line.split()[1])//1024
    counters={}
    for line in Path('/proc/vmstat').read_text().splitlines():
        name,_,value=line.partition(' ')
        if name in ('pswpin','pswpout'):
            counters[name]=int(value)
    if available is None or set(counters)!={'pswpin','pswpout'}:
        raise ValueError('Host resource counters unavailable')
    free=shutil.disk_usage(ROOT).free//(1024*1024)
    return available,free,(counters['pswpin'],counters['pswpout'])


def observed_ranges():
    """Host, Docker and VPN IPv4 ranges, using the fixed read-only inventory from the controller."""
    from defense.controller import Collector, network_inventory
    return network_inventory(Collector())


VM_NAMES={'Pinpoint-Final':'appliance','pinpoint-defense-win01':'windows'}


def observe_vbox(argv):
    if argv[:1]!=['VBoxManage']:raise ValueError('Only fixed VirtualBox observations are allowed')
    return run(argv,timeout=20)


def derive_vm_pins(records,names_text):
    """Pin the two named VMs from a complete inventory; any other host-only member refuses."""
    uuids={}
    for line in names_text.splitlines():
        match=re.fullmatch(r'"(.*)" \{([a-f0-9-]{36})\}',line)
        if match and match[1] in VM_NAMES:
            if VM_NAMES[match[1]] in uuids:raise ValueError('Duplicate lab VM name')
            uuids[VM_NAMES[match[1]]]=match[2]
    if set(uuids)!={'appliance','windows'}:raise ValueError('Lab VMs not found by exact name')
    pins={}
    for record in records:
        for adapter in record['adapters']:
            if adapter['network']!='vboxnet1':continue
            for role,uuid in uuids.items():
                if record['uuid']==uuid:pins[role]={'uuid':uuid,'slot':adapter['slot'],'mac':adapter['mac']}
    if set(pins)!={'appliance','windows'}:raise ValueError('Lab VMs are not on the host-only network')
    validate_vm_membership(records,pins)
    return pins


VM_PINS=PINS.with_name('vm-pins.json')


def enroll_vms():
    if VM_PINS.exists() or VM_PINS.is_symlink():raise ValueError('VM pins already exist')
    pins=derive_vm_pins(collect_vm_inventory(observe_vbox),run(['VBoxManage','list','vms'],timeout=20))
    fd=os.open(VM_PINS,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(pins,stream);stream.write('\n')
    return pins


def read_vm_pins():
    info=VM_PINS.lstat()
    if not VM_PINS.is_file() or VM_PINS.is_symlink() or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:
        raise ValueError('Unsafe VM pins')
    return json.loads(VM_PINS.read_text())


def preflight(pins,counters=read_host_counters,inventory=observed_ranges,sleep=time.sleep,interval=5,vm_pins=None,vm_records=None):
    """Read-only gate: isolated owned network, no subnet collision, RAM/disk reserve, no swap thrash."""
    check_host_network(pins)
    if vm_pins is None:raise ValueError('VM pins are required')
    validate_vm_membership((vm_records or (lambda:collect_vm_inventory(observe_vbox)))(),vm_pins)
    reject_foreign_overlaps(inventory(),'10.77.1.0/27')
    first=counters();sleep(interval);second=counters()
    rate=swap_rate(first[2],second[2],interval)
    check_host_resources(second[0],second[1],rate)
    return {'available_mib':second[0],'free_disk_mib':second[1],'swap_pages_per_second':rate}


def check_parent_attachments():
    """Refuse host links or Docker networks, other than the owned one, that use vboxnet1."""
    links=json.loads(run(['ip','-j','-d','link','show']))
    names=run(['docker','network','ls','-q']).split()
    networks=[]
    if names:
        networks=json.loads(run(['docker','network','inspect',*names]))
    validate_parent_attachments(links,networks,'vboxnet1','pinpoint274-host-test')


def check_host_network(pins):
    """Refuse to operate unless the fixed network is virtual, isolated and owned."""
    parent=Path('/sys/class/net/vboxnet1')
    if parent.resolve()!=Path('/sys/devices/virtual/net/vboxnet1') or (parent/'device').exists() or (parent/'master').exists():
        raise ValueError('Host-only parent changed')
    links=json.loads(run(['ip','-j','-4','addr','show','dev','vboxnet1']))
    if len(links)!=1:raise ValueError('Host-only interface missing')
    addresses=[(a.get('local'),a.get('prefixlen')) for a in links[0].get('addr_info',[]) if a.get('family')=='inet']
    if addresses!=[('192.168.57.1',24)]:raise ValueError('Host-only addressing changed')
    dhcp=run(['VBoxManage','list','dhcpservers'])
    if 'HostInterfaceNetworking-vboxnet1' in dhcp:raise ValueError('Foreign host-only DHCP server configured')
    networks=json.loads(run(['docker','network','inspect','pinpoint274-host-test']))
    if len(networks)!=1:raise ValueError('Pilot network missing')
    net=networks[0]
    if net.get('Driver')!='macvlan' or net.get('Options')!={'parent':'vboxnet1'} or (net.get('Labels') or {}).get('org.pinpoint.defense.issue')!='274':
        raise ValueError('Pilot network identity changed')
    if net.get('IPAM',{}).get('Config')!=[{'Subnet':'10.77.1.0/27','Gateway':'10.77.1.30'}]:raise ValueError('Pilot network addressing changed')
    if not set((net.get('Containers') or {}).keys()).issubset({pin['id'] for pin in pins.values()}):raise ValueError('Foreign container joined pilot network')
    check_parent_attachments()


def remove_default_route(pin):
    """Docker IPAM creates a default gateway; remove only the known pilot route."""
    routes=json.loads(run(['docker','exec',pin['id'],'ip','-j','-4','route','show','default']))
    if routes:
        if len(routes)!=1 or routes[0].get('gateway')!='10.77.1.30' or routes[0].get('dev')!='eth0':raise ValueError('Unexpected default route')
        run(['docker','exec','--privileged',pin['id'],'ip','route','del','default'])


def attach_dynamic(device,pin,obj):
    pid=obj['State'].get('Pid')
    if type(pid) is not int or pid<=1:raise ValueError('Dynamic container process unavailable')
    stat=Path('/proc')/str(pid)/'stat'
    ticks=int(stat.read_text().rsplit(')',1)[1].split()[19])
    request={'target':device.name,'pid':pid,'start_ticks':ticks,'container_id':pin['id']}
    output=run(['docker','run','-i','--rm','--privileged','--read-only','--pid','host','--network','host','--cgroupns','host',
                '--mount','type=bind,src='+str(CONTEXT)+',dst=/etc/pinpoint-defense/context.json,readonly',pin['image'],
                'python3','/opt/pinpoint/defense/host_attach.py'],input_text=json.dumps(request))
    if json.loads(output)!={'target':device.name,'attached':True,'address_assigned':False}:raise ValueError('Dynamic attachment failed')


def lifecycle(catalog,pins,action,target=None):
    order=target_order(catalog,action,target)
    check_host_network(pins)
    if target is not None and action=='up' and order[0].mode=='dhcp':
        server=node(catalog.target('dhcp01'),pins['dhcp01'],'inspect')
        if not server.get('network_safe') or {v['program']:v['state'] for v in server['services']}.get('dhcp')!='RUNNING':
            raise ValueError('DHCP allocator is not running')
    for d in order:inspect(d,pins[d.name])
    for d in order:
        pin=pins[d.name];obj=inspect(d,pin)
        if action=='down':
            if obj['State']['Running']:run(['docker','stop','--time','15',pin['id']],timeout=40)
            print(d.name,'stopped',flush=True)
            continue
        if not obj['State']['Running']:
            run(['docker','start',pin['id']]);obj=inspect(d,pin)
        if d.mode=='static':remove_default_route(pin)
        deadline=time.monotonic()+20
        while True:
            try:
                current=node(d,pin,'inspect')
                break
            except ValueError:
                if time.monotonic()>=deadline:raise
                time.sleep(0.25)
        if d.mode=='dhcp' and current.get('interfaces')==['lo']:
            attach_dynamic(d,pin,inspect(d,pin))
            current=node(d,pin,'inspect')
        if not current.get('network_safe'):raise ValueError('Target network is not ready')
        node(d,pin,'baseline')
        if d.mode=='dhcp':
            expected=reserved_address(catalog,pins,d)
            node_request(d,pin,{'operation':'lease-acquire','expected_address':expected})
        else:expected=d.address
        current=node(d,pin,'inspect')
        if current.get('addresses')!=[expected]:raise ValueError('Target address changed')
        print(d.name,'ready',flush=True)


def node_request(device,pin,request):
    obj=inspect(device,pin)
    if not obj['State']['Running']:raise ValueError('Target container is stopped')
    result=json.loads(run(['docker','exec','-i',pin['id'],'python3','/opt/pinpoint/defense/node.py','control',device.name],input_text=json.dumps(request),timeout=60))
    if result.get('target')!=device.name:raise ValueError('Target response changed')
    return result


class DockerDhcpLab:
    """Fixed Docker adapter for the five owned clients and their allocator."""
    def __init__(self,catalog,pins):
        self.catalog=catalog;self.pins=pins;self.processes={}
        self.names=['dhcp01']+[d.name for d in catalog.devices if d.mode=='dhcp']
        check_host_network(pins)
        for name in self.names:
            device=catalog.target(name);pin=pins[name];obj=inspect(device,pin)
            pid=obj.get('State',{}).get('Pid')
            if not obj.get('State',{}).get('Running') or type(pid) is not int or pid<=1:
                raise ValueError('DHCP container is not running')
            ticks=int((Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19])
            request={'target':name,'pid':pid,'start_ticks':ticks,'container_id':pin['id']}
            observe_process(request);self.processes[name]=request
    def check(self,name):
        device=self.catalog.target(name);pin=self.pins[name];obj=inspect(device,pin)
        request=self.processes[name]
        if not obj.get('State',{}).get('Running') or obj['State'].get('Pid')!=request['pid']:
            raise ValueError('DHCP container process changed')
        observe_process(request)
        return device,pin
    def request(self,name,request):
        check_host_network(self.pins)
        device,pin=self.check(name)
        result=node_request(device,pin,request)
        self.check(name)
        return result
    def snapshot(self):
        check_host_network(self.pins)
        identities={}
        for name in self.names:
            self.check(name);identities[name]=self.pins[name]['id']
        addresses={}
        for name in self.names[1:]:
            result=self.request(name,{'operation':'inspect'});device=self.catalog.target(name)
            if result.get('network_safe') is not True or result.get('observed_mac')!=device.mac or result.get('client_id')!=device.client_id:
                raise ValueError('DHCP client observation changed')
            addresses[name]=result.get('addresses')
        server=self.request('dhcp01',{'operation':'inspect'})
        if server.get('network_safe') is not True or server.get('addresses')!=[self.catalog.target('dhcp01').address]:
            raise ValueError('DHCP allocator network changed')
        try:
            saved=self.request('dhcp01',{'operation':'server-observe'})
            reservations=saved['reservations'];duration=saved['lease_seconds']
            running=saved['supervisor_state']=='RUNNING'
        except (ValueError,KeyError):
            # Only a valid durable intent permits a torn allocator configuration
            # to be repaired. A new move cannot use an unobservable allocator.
            record=dhcp_journal.read(ROOT,self.catalog)
            if record['pins']!=identities:raise ValueError('Recovery identities changed')
            reservations=None;duration=600;running=False
        for name in self.names:self.check(name)
        return {'pins':identities,'reservations':reservations,'addresses':addresses,
                'lease_seconds':duration,'server_running':running}
    def restore_baseline(self):
        """Reapply the fixed allocator baseline that `up` applies after a container restart."""
        device,pin=self.check('dhcp01')
        remove_default_route(pin)
        node(device,pin,'baseline')
        self.check('dhcp01')
    def release(self,name):
        self.request(name,{'operation':'lease-release'})
    def configure(self,reservations):
        self.request('dhcp01',{'operation':'server-config','reservations':reservations,'lease_seconds':600})
    def acquire(self,name,address):
        self.request(name,{'operation':'lease-acquire','expected_address':address})


def dhcp_server(catalog,pins,action):
    """Stop or resume the sole saved allocator without changing reservations."""
    if action not in {'start','stop'}:raise ValueError('Invalid DHCP server action')
    check_host_network(pins)
    device=catalog.target('dhcp01');pin=pins[device.name]
    before=node(device,pin,'inspect')
    if not before.get('network_safe') or before.get('addresses')!=[device.address]:raise ValueError('Unsafe DHCP server network')
    states={v['program']:v['state'] for v in before['services']}
    if 'dhcp' not in states:raise ValueError('DHCP server unavailable')
    desired='RUNNING' if action=='start' else 'STOPPED'
    if states['dhcp']!=desired:node_request(device,pin,{'operation':'server-'+action})
    after=node(device,pin,'inspect')
    if {v['program']:v['state'] for v in after['services']}.get('dhcp')!=desired:raise ValueError('DHCP server state not reached')
    return after


def dhcp_lease(catalog,pins,target,action):
    """Release or reacquire only the selected client's reserved address."""
    device=catalog.target(target)
    if device.kind!='linux' or device.mode!='dhcp' or action not in {'release','acquire'}:
        raise ValueError('A catalog DHCP client and fixed lease action are required')
    check_host_network(pins)
    pin=pins[target];before=node(device,pin,'inspect')
    expected=reserved_address(catalog,pins,device)
    if not before.get('network_safe') or before.get('addresses') not in ([],[expected]):
        raise ValueError('DHCP client state is unsafe')
    if action=='acquire':
        server=node(catalog.target('dhcp01'),pins['dhcp01'],'inspect')
        if not server.get('network_safe') or {v['program']:v['state'] for v in server['services']}.get('dhcp')!='RUNNING':
            raise ValueError('DHCP allocator is not running')
        request={'operation':'lease-acquire','expected_address':expected}
    else:request={'operation':'lease-release'}
    if action=='release' or (action=='acquire' and not before['addresses']):
        node_request(device,pin,request)
    after=node(device,pin,'inspect')
    if not after.get('network_safe') or after.get('addresses')!=([expected] if action=='acquire' else []):
        raise ValueError('DHCP lease state not reached')
    return after


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('enroll');sub.add_parser('status');sub.add_parser('preflight');sub.add_parser('enroll-vms');sub.add_parser('manifest');sub.add_parser('reset')
    mode=sub.add_parser('address-mode');mode.add_argument('mode_action',choices=('show','static','dhcp','recover'));mode.add_argument('mode_rest',nargs='*')
    ports=sub.add_parser('ports');ports.add_argument('ports_action',choices=('list','open','close','restore'));ports.add_argument('rest',nargs='+');sub.add_parser('up');sub.add_parser('down')
    for action in ('host-stop','host-start'):
        p=sub.add_parser(action);p.add_argument('target')
    server=sub.add_parser('dhcp-server');server.add_argument('action',choices=('start','stop'))
    lease=sub.add_parser('dhcp-lease');lease.add_argument('action',choices=('release','acquire'));lease.add_argument('target')
    move=sub.add_parser('dhcp-move');move.add_argument('target');move.add_argument('address')
    sub.add_parser('dhcp-recover')
    for action in ('break','fix'):
        p=sub.add_parser(action);p.add_argument('target');p.add_argument('service')
    args=parser.parse_args(argv)
    try:
        catalog=load_catalog()
        with qa_control.claim():
            exempt=args.command in {'status','dhcp-recover','preflight','manifest','reset'} or (args.command=='ports' and args.ports_action=='list') or (args.command=='address-mode' and args.mode_action in {'show','recover'})
            if not exempt:
                require_no_dhcp_intent(ROOT)
            if args.command=='dhcp-recover' and address_mode.intent_exists(ROOT):
                raise ValueError('Address-mode recovery must finish first')
            if args.command=='address-mode' and args.mode_action=='recover' and os.path.lexists(ROOT/dhcp_journal.NAME):
                raise ValueError('DHCP recovery must finish first')
            if args.command=='enroll-vms':
                enroll_vms();print('Pinned the 2 lab VMs on vboxnet1.');return 0
            pins=enroll(catalog) if args.command=='enroll' else read_pins()
            if args.command=='enroll':print('Pinned 14 existing laptop pilot containers.');return 0
            if args.command in {'up','down'}:
                lifecycle(catalog,pins,args.command)
            elif args.command in {'host-stop','host-start'}:
                lifecycle(catalog,pins,'down' if args.command=='host-stop' else 'up',args.target)
            elif args.command=='dhcp-server':
                dhcp_server(catalog,pins,args.action)
                print('DHCP server','started' if args.action=='start' else 'stopped')
            elif args.command=='dhcp-lease':
                result=dhcp_lease(catalog,pins,args.target,args.action)
                print(args.target,','.join(result['addresses']) or 'lease released')
            elif args.command=='dhcp-move':
                dhcp_control.move(ROOT,catalog,DockerDhcpLab(catalog,pins),args.target,args.address)
                print(args.target,'DHCP move completed')
            elif args.command=='dhcp-recover':
                dhcp_control.recover(ROOT,catalog,DockerDhcpLab(catalog,pins))
                print('DHCP recovery completed')
            elif args.command=='manifest':
                result=observed_manifest(catalog,pins,read_vm_pins())
                print(json.dumps(result,indent=2))
                if not result['consistent']:return 1
            elif args.command=='reset':
                reset(catalog,pins);print('Reset complete: baseline verified')
            elif args.command=='address-mode':
                action,rest=args.mode_action,args.mode_rest
                if action=='show' and len(rest)==1:
                    result=address_mode_show(catalog,pins,rest[0]);print(rest[0],result['mode'],result['address'] or '-')
                elif action=='static' and len(rest)==2:
                    address_mode_set(catalog,pins,rest[0],'static',rest[1]);print(rest[0],'static',rest[1])
                elif action=='dhcp' and len(rest)==1:
                    address_mode_set(catalog,pins,rest[0],'dhcp',None);print(rest[0],'dhcp')
                elif action=='recover' and not rest:
                    address_mode_recover(catalog,pins);print('Address-mode recovery completed')
                else:raise ValueError('Invalid address-mode request')
            elif args.command=='ports':
                action,rest=args.ports_action,args.rest
                def number(value):
                    if not value.isdigit():raise ValueError('Invalid port')
                    return int(value)
                if action=='list' and len(rest)==1:
                    result=port_list(catalog,pins,rest[0])
                    print(rest[0],'baseline',','.join(map(str,result['baseline'])) or '-','extra',','.join(map(str,result['extra'])) or '-')
                elif action=='open' and len(rest)==3:
                    port_open(catalog,pins,rest[0],rest[1],number(rest[2]));print(rest[0],'port',rest[2],'open')
                elif action=='close' and len(rest)==2:
                    port_close(catalog,pins,rest[0],number(rest[1]));print(rest[0],'port',rest[1],'closed')
                elif action=='restore' and len(rest)==1:
                    if rest[0]=='all':port_restore_all(catalog,pins)
                    else:port_restore(catalog,pins,rest[0])
                    print(rest[0],'extra ports restored')
                else:raise ValueError('Invalid ports request')
            elif args.command=='preflight':
                result=preflight(pins,vm_pins=read_vm_pins())
                print('Preflight OK: %d MiB RAM available, %d MiB disk free, swap %.1f pages/s'%(result['available_mib'],result['free_disk_mib'],result['swap_pages_per_second']))
            elif args.command=='status':
                for d in catalog.devices:
                    if d.kind!='linux':continue
                    obj=inspect(d,pins[d.name])
                    if not obj['State']['Running']:
                        print(d.name,'stopped');continue
                    result=node(d,pins[d.name],'inspect')
                    states=', '.join(x['program']+'='+x['state'] for x in result['services'])
                    print(d.name,','.join(result['addresses']) or 'unaddressed',states)
            else:
                result=service(catalog,pins,args.target,args.service,'stop' if args.command=='break' else 'start')
                print(args.target,args.service,'stopped' if args.command=='break' else 'running')
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,json.JSONDecodeError):
        if args.command in {'dhcp-move','dhcp-recover'} and ((ROOT/dhcp_journal.NAME).exists() or (ROOT/dhcp_journal.NAME).is_symlink()):
            print('DHCP move incomplete; run presenter dhcp-recover after resolving the lab issue.',file=sys.stderr)
            return 1
        if args.command=='address-mode' and address_mode.intent_exists(ROOT):
            print('Address change incomplete; run presenter address-mode recover after resolving the lab issue.',file=sys.stderr)
            return 1
        print('Presenter control refused: pilot state or requested operation is unavailable.',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
