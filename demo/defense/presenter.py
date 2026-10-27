"""Presenter controls for the existing issue-274 laptop Docker pilot."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from defense.catalog import load_catalog
from defense import dhcp_journal
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
        try:
            os.stat(dhcp_journal.NAME,dir_fd=fd,follow_symlinks=False)
        except FileNotFoundError:
            return
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
    if not before.get('network_safe') or before.get('addresses')!=[device.address]:raise ValueError('Unsafe target network')
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
            node_request(d,pin,{'operation':'lease-acquire','expected_address':d.address})
        current=node(d,pin,'inspect')
        if current.get('addresses')!=[d.address]:raise ValueError('Target address changed')
        print(d.name,'ready',flush=True)


def node_request(device,pin,request):
    obj=inspect(device,pin)
    if not obj['State']['Running']:raise ValueError('Target container is stopped')
    result=json.loads(run(['docker','exec','-i',pin['id'],'python3','/opt/pinpoint/defense/node.py','control',device.name],input_text=json.dumps(request),timeout=60))
    if result.get('target')!=device.name:raise ValueError('Target response changed')
    return result


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
    if not before.get('network_safe') or before.get('addresses') not in ([],[device.address]):
        raise ValueError('DHCP client state is unsafe')
    if action=='acquire':
        server=node(catalog.target('dhcp01'),pins['dhcp01'],'inspect')
        if not server.get('network_safe') or {v['program']:v['state'] for v in server['services']}.get('dhcp')!='RUNNING':
            raise ValueError('DHCP allocator is not running')
        request={'operation':'lease-acquire','expected_address':device.address}
    else:request={'operation':'lease-release'}
    if action=='release' or (action=='acquire' and not before['addresses']):
        node_request(device,pin,request)
    after=node(device,pin,'inspect')
    if not after.get('network_safe') or after.get('addresses')!=([device.address] if action=='acquire' else []):
        raise ValueError('DHCP lease state not reached')
    return after


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('enroll');sub.add_parser('status');sub.add_parser('up');sub.add_parser('down')
    for action in ('host-stop','host-start'):
        p=sub.add_parser(action);p.add_argument('target')
    server=sub.add_parser('dhcp-server');server.add_argument('action',choices=('start','stop'))
    lease=sub.add_parser('dhcp-lease');lease.add_argument('action',choices=('release','acquire'));lease.add_argument('target')
    for action in ('break','fix'):
        p=sub.add_parser(action);p.add_argument('target');p.add_argument('service')
    args=parser.parse_args(argv)
    try:
        catalog=load_catalog()
        with qa_control.claim():
            if args.command!='status':
                require_no_dhcp_intent(ROOT)
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
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
        print('Presenter control refused: pilot state or requested operation is unavailable.',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
