"""Attach a fixed DHCP pilot to the pinned host-only adapter, never a LAN NIC."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.catalog import load_catalog
from defense.node import container_context


def validate_request(request):
    """Accept only a catalog DHCP target and pinned Docker process identity."""
    if not isinstance(request,dict) or set(request)!={'target','pid','start_ticks','container_id'}:
        raise ValueError('Invalid host attachment request')
    target=request['target']
    if not isinstance(target,str) or load_catalog().target(target).mode!='dhcp':
        raise ValueError('Attachment requires a catalog DHCP client')
    if type(request['pid']) is not int or request['pid']<=1 or type(request['start_ticks']) is not int or request['start_ticks']<=0:
        raise ValueError('Invalid container process')
    if not isinstance(request['container_id'],str) or not re.fullmatch(r'[a-f0-9]{64}',request['container_id']):
        raise ValueError('Invalid Docker container identity')
    return request


def validate_process(request,start_ticks,cgroup):
    """Refuse a reused PID or a process outside the exact Docker cgroup."""
    expected='/system.slice/docker-'+request['container_id']+'.scope'
    if type(start_ticks) is not int or start_ticks!=request['start_ticks'] or not isinstance(cgroup,str):
        raise ValueError('Container process identity changed')
    if cgroup.strip()!='0::'+expected:
        raise ValueError('Container cgroup identity changed')


def observe_process(request):
    """Read the process start and cgroup without trusting a process name."""
    path=Path('/proc')/str(request['pid'])
    try:
        stat=path.joinpath('stat').read_text().rsplit(')',1)[1].split()
        validate_process(request,int(stat[19]),path.joinpath('cgroup').read_text())
    except (OSError,IndexError,ValueError):
        raise ValueError('Container process unavailable or changed') from None


def run(argv,*,check=True):
    """Run bounded fixed arguments, suppressing sensitive child output on error."""
    try:
        result=subprocess.run(argv,capture_output=True,text=True,timeout=20)
    except (OSError,subprocess.SubprocessError):
        raise ValueError('Attachment command unavailable') from None
    if check and result.returncode:raise ValueError('Attachment command failed')
    return result


def attach(request,context):
    """Move one fixed macvlan into an owned DHCP container without assigning an IP."""
    validate_request(request)
    if context.get('version')!=2 or context.get('mode')!='host-only':
        raise ValueError('Host-only context is required')
    if os.readlink('/proc/1/ns/net')!=os.readlink('/proc/self/ns/net'):
        raise ValueError('The helper must use the host network namespace')
    parent=Path('/sys/class/net/vboxnet1')
    if parent.resolve()!=Path('/sys/devices/virtual/net/vboxnet1') or parent.joinpath('device').exists():
        raise ValueError('The pinned parent is not a virtual host-only interface')
    links=json.loads(run(['ip','-j','-d','addr','show','dev','vboxnet1']).stdout)
    if len(links)!=1 or links[0].get('address','').lower()!=context['parent_mac'] or links[0].get('master'):
        raise ValueError('Host-only parent identity changed')
    ipv4=[(a.get('local'),a.get('prefixlen')) for a in links[0].get('addr_info',[]) if a.get('family')=='inet']
    if ipv4!=[('192.168.57.1',24)]:raise ValueError('Host-only parent address changed')
    target=request['target'];pid=str(request['pid']);device=load_catalog().target(target)
    name='pd-'+target;prefix=['nsenter','--target',pid,'--net','--']
    observe_process(request)
    if run(['ip','link','show','dev',name],check=False).returncode==0:
        raise ValueError('Attachment name already exists')
    links=json.loads(run(prefix+['ip','-j','addr','show']).stdout)
    if len(links)!=1 or links[0].get('ifname')!='lo':raise ValueError('Container network is not empty')
    def execute(argv):
        observe_process(request)
        return run(argv)
    execute(['ip','link','add','link','vboxnet1','name',name,'address',device.mac,'type','macvlan','mode','bridge'])
    execute(['ip','link','set','dev',name,'alias','pinpoint-defense:'+context['owner']+':'+target])
    execute(['ip','link','set','dev',name,'netns',pid])
    execute(prefix+['ip','link','set','dev',name,'name','eth0'])
    execute(prefix+['sysctl','-w','net.ipv6.conf.all.disable_ipv6=1','net.ipv6.conf.default.disable_ipv6=1'])
    execute(prefix+['ip','link','set','dev','lo','up'])
    execute(prefix+['ip','link','set','dev','eth0','up'])
    return {'target':target,'attached':True,'address_assigned':False}


def main():
    """Read the bounded request from stdin and print only a nonsecret result."""
    try:
        text=sys.stdin.read(4097)
        if len(text)>4096:raise ValueError('Request is too large')
        request=validate_request(json.loads(text));context=container_context()
        print(json.dumps(attach(request,context)))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError):
        print('Host-only attachment refused; inspect owned state.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
