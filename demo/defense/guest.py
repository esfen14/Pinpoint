"""Root helper for the two-target spike inside the exact owned VirtualBox guest."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.bootstrap import dmi_uuid_matches, management_observation, image_source_hash
from defense.catalog import load_catalog
from defense.compose import ROOT, PROJECT, compose_document
from defense.node import command, validate_network, validate_request, atomic
from defense.preflight import read_private_json


def validate_spike_target(catalog,target: str) -> None:
    """Keep execution limited to the server and one client until the live spike passes."""
    catalog.target(target)
    if target not in {'dhcp01','dynweb01'}:
        raise ValueError('Only the two-target architecture spike is enabled')


def validate_parent(context: dict, links: list[dict], forwarding: int, forwarding6: int) -> str:
    """Require an unnumbered isolated parent and no guest packet forwarding."""
    if forwarding!=0 or forwarding6!=0:
        raise ValueError('Guest forwarding must be disabled before demo attachment')
    matches=[v for v in links if v.get('address','').lower()==context['parent_mac']]
    if len(matches)!=1:
        raise ValueError('Isolated parent MAC missing or duplicated')
    parent=matches[0]
    name=parent.get('ifname','')
    if not re.fullmatch(r'[a-zA-Z0-9_]{1,15}',name) or parent.get('addr_info') or parent.get('master') or parent.get('linkinfo'):
        raise ValueError('Demo parent must be a plain unnumbered NIC outside any bridge')
    return name


def validate_container(catalog,context: dict,image: str,target: str,observed: dict,*,image_labels=None,allow_stopped=False) -> int:
    """Pin runtime identity, image, command, capabilities and every bind before nsenter."""
    validate_spike_target(catalog,target)
    expected=compose_document(catalog,image,context['owner'],spike=True)['services'][target]
    config=observed.get('Config',{});host=observed.get('HostConfig',{})
    state=observed.get('State',{})
    if observed.get('Name')!='/'+expected['container_name'] or observed.get('Image')!=image or not re.fullmatch(r'[a-f0-9]{64}',observed.get('Id','')):
        raise ValueError('Container identity/image changed')
    labels=config.get('Labels') or {}
    wanted=dict(image_labels or {},**expected['labels'])
    if any(labels.get(k)!=v for k,v in wanted.items()) or any(k not in wanted and not k.startswith('com.docker.compose.') for k in labels) or config.get('Cmd')!=expected['command'] or config.get('Hostname')!=target or config.get('Entrypoint'):
        raise ValueError('Container ownership/entrypoint changed')
    if labels.get('com.docker.compose.project',PROJECT)!=PROJECT or labels.get('com.docker.compose.service',target)!=target:
        raise ValueError('Container Compose project/service changed')
    if host.get('NetworkMode')!='none' or host.get('Privileged') is not False or host.get('PidMode') or host.get('PortBindings'):
        raise ValueError('Container escaped the isolated namespace boundary')
    if sorted(host.get('CapAdd') or [])!=sorted(expected.get('cap_add',[])) or host.get('CapDrop') or host.get('RestartPolicy',{}).get('Name')!='no':
        raise ValueError('Unexpected container capabilities/restart policy')
    if host.get('Devices') or host.get('DeviceRequests') or host.get('SecurityOpt'):
        raise ValueError('Unexpected container devices/security configuration')
    mounts=observed.get('Mounts',[])
    actual=sorted((v.get('Type'),v.get('Source'),v.get('Destination'),v.get('RW')) for v in mounts)
    wanted=sorted(('bind',v['source'],v['target'],not v['read_only']) for v in expected['volumes'])
    if actual!=wanted:
        raise ValueError('Container persistent/config mounts changed')
    if set(observed.get('NetworkSettings',{}).get('Networks',{}))!={'none'}:
        raise ValueError('Container has an unexpected Docker network')
    pid=state.get('Pid')
    if state.get('Paused') or state.get('Restarting') or state.get('Dead'):
        raise ValueError('Container state is unsafe or transitional')
    if allow_stopped and state.get('Running') is False and pid==0:return 0
    if state.get('Running') is not True or type(pid) is not int or pid<=1:
        raise ValueError('Container is not running in a stable namespace')
    return pid


def validate_image(image,digest,observed):
    """Require the exact Docker image ID and source fingerprint, never a mutable tag."""
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image) or not re.fullmatch(r'[a-f0-9]{64}',digest):
        raise ValueError('Invalid pinned image/source')
    labels=observed.get('Config',{}).get('Labels') or {}
    if observed.get('Id')!=image or labels.get('org.pinpoint.defense.issue')!='274' or labels.get('org.pinpoint.defense.source')!=digest:
        raise ValueError('Image provenance differs from the current runtime')
    return labels


def trusted_image(image):
    """Collect the immutable image metadata only after source/image state agrees."""
    digest=image_source_hash()
    if read_private_json(Path(ROOT)/'image-source.json')!={'sha256':digest}:
        raise ValueError('Runtime source changed since the image build')
    observed=json.loads(command(['docker','image','inspect',image]).stdout)
    if len(observed)!=1:raise ValueError('Ambiguous pinned image')
    return validate_image(image,digest,observed[0])


def validate_spike_document(catalog,context,image,document):
    """Refuse any drift in the private generated two-service Compose document."""
    if document!=compose_document(catalog,image,context['owner'],spike=True):
        raise ValueError('Private spike Compose differs from its validated catalog')


def node_request(catalog,context,image,target,request):
    """Send only the closed node protocol on stdin after checking its owned runtime."""
    validate_spike_target(catalog,target);validate_request(catalog,target,request)
    observed=observe_container(target)
    # Reject foreign image/owner/mounts before any further Docker exec.
    expected_labels=trusted_image(image) if observed.get('Image')==image else None
    validate_container(catalog,context,image,target,observed,image_labels=expected_labels)
    response=command(['docker','exec','-i',observed['Id'],'python3','/opt/pinpoint/defense/node.py','control',target],
                     input_text=json.dumps(request),timeout=60)
    result=json.loads(response.stdout)
    if result.get('target')!=target or set(result)!={'target','network_safe','addresses','mac','client_id','listeners','services'}:
        raise ValueError('Unexpected node result')
    return result


def spike_up(catalog,context,image,parent):
    """Create/start only two pinned network-none containers, attach them, leave daemons stopped."""
    document=read_private_json(Path(ROOT)/'spike-compose.json')
    validate_spike_document(catalog,context,image,document)
    labels=trusted_image(image)
    names=command(['docker','ps','-a','--format','{{.Names}}']).stdout.splitlines()
    expected={PROJECT+'-dhcp01':'dhcp01',PROJECT+'-dynweb01':'dynweb01'}
    if len(names)!=len(set(names)) or any(name not in expected for name in names):
        raise ValueError('Foreign or ambiguous containers prevent spike startup')
    for name in names:
        validate_container(catalog,context,image,expected[name],observe_container(expected[name]),image_labels=labels,allow_stopped=True)
    atomic(Path(ROOT)/'spike-intent.json',json.dumps({'version':1,'operation':'spike-up','phase':'starting','targets':['dhcp01','dynweb01']})+'\n')
    command(['docker','compose','-f',str(Path(ROOT)/'spike-compose.json'),'up','-d','--no-build','--no-recreate','dhcp01','dynweb01'],timeout=90)
    for target in ['dhcp01','dynweb01']:
        validate_container(catalog,context,image,target,observe_container(target),image_labels=labels)
    # The manually controlled parent may remain down after image build/reboot.
    guest_context()
    command(['ip','link','set','dev',parent,'up'])
    results=[]
    for target in ['dhcp01','dynweb01']:
        attach(catalog,context,image,target,parent)
        deadline=time.monotonic()+15
        while True:
            try:
                result=node_request(catalog,context,image,target,{'operation':'inspect'})
                if not result['network_safe']:raise ValueError('Attached node boundary failed')
                results.append(result);break
            except ValueError:
                if time.monotonic()>=deadline:raise
                time.sleep(0.25)
    atomic(Path(ROOT)/'spike-intent.json',json.dumps({'version':1,'operation':'spike-up','phase':'attached','targets':['dhcp01','dynweb01']})+'\n')
    return {'targets':results,'note':'Daemon/DHCP start requires explicit checked node operations.'}


def stop_target(catalog,context,image,target):
    """Stop the selected exact-owned container without deleting persistent identity/data."""
    validate_spike_target(catalog,target)
    observed=observe_container(target)
    validate_container(catalog,context,image,target,observed,image_labels=trusted_image(image),allow_stopped=True)
    if observed['State']['Running']:
        command(['docker','stop','--time','15',observed['Id']],timeout=30)
    after=observe_container(target)
    validate_container(catalog,context,image,target,after,image_labels=trusted_image(image),allow_stopped=True)
    if after['State']['Running']:raise ValueError('Owned container did not stop')
    return {'target':target,'running':False,'persistent_state_retained':True}


def observe_container(target: str) -> dict:
    """Read one exact fixed container without exposing Docker environment or output."""
    result=json.loads(command(['docker','inspect','--type','container',PROJECT+'-'+target]).stdout)
    if len(result)!=1:raise ValueError('Ambiguous owned container')
    return result[0]


def namespace(catalog,context,image,target):
    """Recheck container ownership and return its PID and process-start identity."""
    observed=observe_container(target)
    pid=validate_container(catalog,context,image,target,observed,image_labels=trusted_image(image))
    info=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    return pid,info[19],observed['Id']


def attach(catalog,context,image,target,parent):
    """Attach one macvlan; never use the physical host Docker or assign a DHCP address."""
    # This first validation also protects callers that have not run main().
    observed=observe_container(target)
    validate_container(catalog,context,image,target,observed,image_labels=trusted_image(image) if observed.get('Image')==image else None)
    pid,started,container_id=namespace(catalog,context,image,target)
    device=catalog.target(target)
    def execute(argv):
        """Revalidate the process namespace before each fixed operation."""
        if namespace(catalog,context,image,target)!=(pid,started,container_id):
            raise ValueError('Container namespace changed during attachment')
        return command(argv)
    prefix=['nsenter','--target',str(pid),'--net','--']
    links=json.loads(execute(prefix+['ip','-j','-d','addr','show']).stdout)
    if {v.get('ifname') for v in links}=={'lo','eth0'}:
        eth=next(v for v in links if v.get('ifname')=='eth0')
        if eth.get('ifalias')!='pinpoint-defense:'+context['owner']+':'+target or eth.get('linkinfo',{}).get('info_kind')!='macvlan' or eth.get('linkinfo',{}).get('info_data',{}).get('mode')!='bridge':
            raise ValueError('Existing attachment ownership/type changed')
        routes=json.loads(execute(prefix+['ip','-j','-4','route','show','default']).stdout)
        validate_network(catalog,device,links,routes,unaddressed=True)
        return {'target':target,'attached':True,'reused':True}
    if len(links)!=1 or links[0].get('ifname')!='lo':
        raise ValueError('Container already contains an unowned interface')
    name='pd-'+target
    # A leftover link requires private inspection; never adopt/delete it by name.
    if command(['ip','link','show','dev',name],check=False).returncode==0:
        raise ValueError('Guest attachment name already occupied')
    execute(['ip','link','add','link',parent,'name',name,'address',device.mac,'type','macvlan','mode','bridge'])
    execute(['ip','link','set','dev',name,'alias','pinpoint-defense:'+context['owner']+':'+target])
    execute(['ip','link','set','dev',name,'netns',str(pid)])
    execute(prefix+['ip','link','set','dev',name,'name','eth0'])
    # There is no demo IPv6 requirement; prevent automatic link-local numbering.
    execute(prefix+['sysctl','-w','net.ipv6.conf.all.disable_ipv6=1','net.ipv6.conf.default.disable_ipv6=1'])
    execute(prefix+['ip','link','set','dev','lo','up'])
    execute(prefix+['ip','link','set','dev','eth0','up'])
    if device.mode=='static':
        execute(prefix+['ip','address','add',device.address+'/'+str(catalog.network.prefixlen),'dev','eth0'])
    links=json.loads(execute(prefix+['ip','-j','addr','show']).stdout)
    routes=json.loads(execute(prefix+['ip','-j','-4','route','show','default']).stdout)
    validate_network(catalog,device,links,routes,unaddressed=True)
    return {'target':target,'attached':True,'reused':False}


def guest_context():
    """Validate root-owned private state, DMI and unnumbered parent before mutation."""
    if os.geteuid()!=0 or Path('/.dockerenv').exists() or Path('/sys/class/dmi/id/product_name').read_text().strip()!='VirtualBox':
        raise ValueError('Guest helper requires the dedicated VirtualBox Linux VM')
    context=read_private_json(Path(ROOT)/'context.json')
    if set(context)!={'version','owner','vm_uuid','parent_mac'} or context['version']!=1 or not re.fullmatch(r'[a-f0-9]{48}',context.get('owner','')) or not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}',context.get('parent_mac','')):
        raise ValueError('Invalid private guest context')
    if not dmi_uuid_matches(context['vm_uuid'],Path('/sys/class/dmi/id/product_uuid').read_text().strip()):
        raise ValueError('Guest VM UUID changed')
    management_observation()
    runtime=read_private_json(Path(ROOT)/'runtime.json')
    if set(runtime)!={'image'}:raise ValueError('Invalid pinned image state')
    compose_document(load_catalog(),runtime['image'],context['owner'],spike=True)
    trusted_image(runtime['image'])
    links=json.loads(command(['ip','-j','-d','addr','show']).stdout)
    parent=validate_parent(context,links,int(Path('/proc/sys/net/ipv4/ip_forward').read_text()),
                           int(Path('/proc/sys/net/ipv6/conf/all/forwarding').read_text()))
    running=command(['docker','ps','--format','{{.Names}}']).stdout.splitlines()
    if any(v not in {PROJECT+'-dhcp01',PROJECT+'-dynweb01'} for v in running):
        raise ValueError('Unexpected running containers on the dedicated guest')
    return context,runtime['image'],parent


def main(argv=None):
    """Expose only fixed attach/inspect operations; creation belongs to provisioning."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['attach','inspect','spike-up','node','stop'])
    parser.add_argument('target',nargs='?')
    args=parser.parse_args(argv)
    try:
        os.umask(0o077)
        catalog=load_catalog()
        if args.operation=='spike-up':
            if args.target is not None:raise ValueError('Spike startup takes no target argument')
        else:validate_spike_target(catalog,args.target)
        request=None
        if args.operation=='node':
            payload=sys.stdin.read(8193)
            if len(payload)>8192:raise ValueError('Node request exceeds limit')
            request=validate_request(catalog,args.target,json.loads(payload))
        context,image,parent=guest_context()
        fd=os.open(Path(ROOT)/'guest.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or info.st_mode&0o077:
                raise ValueError('Unsafe guest control lock')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            context,image,parent=guest_context()
            if args.operation=='attach':result=attach(catalog,context,image,args.target,parent)
            elif args.operation=='spike-up':result=spike_up(catalog,context,image,parent)
            elif args.operation=='node':result=node_request(catalog,context,image,args.target,request)
            elif args.operation=='stop':result=stop_target(catalog,context,image,args.target)
            else:
                observed=observe_container(args.target)
                validate_container(catalog,context,image,args.target,observed,image_labels=trusted_image(image),allow_stopped=True)
                result={'target':args.target,'running':True,'owned':True,'image_pinned':True}
            print(json.dumps(result))
        finally:os.close(fd)
        return 0
    except (OSError,ValueError,TypeError,KeyError):
        print('Owned guest operation refused or failed; private inspection required.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
