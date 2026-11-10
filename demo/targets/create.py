"""Commands that create the fourteen demo containers, matching what presenter.validate_container pins.

Pure builders (tested offline) plus apply(), which runs them through an injected runner.
Container-private files are root-owned because the containers run as root and
their node code requires same-user private state.
"""
from dataclasses import dataclass
import json
from pathlib import Path

NETWORK='pinpoint274-host-test'
PARENT='vboxnet1'
SUBNET='10.77.1.0/27'
GATEWAY='10.77.1.30'
IMAGE_TAG='pinpoint-defense-host274:setup'
CONTAINER_PATH='/opt/pinpoint/targets/node.py'
LABELS=('org.pinpoint.defense.issue=274','org.pinpoint.defense.role=temporary-pilot')
SNMP_TARGETS=('snmp02','dynsnmp01')


@dataclass(frozen=True)
class Step:
    argv: list
    input_text: str | None = None


def new_community():
    """The node code accepts exactly 32 lowercase hex characters."""
    import secrets
    return secrets.token_hex(16)


def pilot(root):
    return Path(root)/'pilot-catalog'


def device_root(root,device):
    """web03 keeps its historical location; the presenter validates exactly this."""
    if device.name=='web03':
        return Path(root)/'pilot-web03'
    return pilot(root)/device.name


def linux_devices(catalog):
    result=[]
    for device in catalog.devices:
        if device.kind=='linux':
            result.append(device)
    return result


def context_path(root):
    return Path(root)/'context'/'context.json'


def host_steps(catalog,root,owner,vm_uuid,parent_mac,community,keep_context=False,keep_secret=False):
    """Root-owned private directories and files; context and SNMP secret via stdin, never argv."""
    steps=[]
    steps.append(Step(['mkdir','-p','-m','700',str(root)]))  # user-owned: the presenter keeps its pins and journals here
    private_dirs=[pilot(root),pilot(root)/'private',context_path(root).parent]
    for directory in private_dirs:
        steps.append(Step(['sudo','install','-d','-m','700','-o','root','-g','root',str(directory)]))
    for device in linux_devices(catalog):
        base=device_root(root,device)
        steps.append(Step(['sudo','install','-d','-m','700','-o','root','-g','root',str(base)]))
        for leaf in ('identity','data'):
            steps.append(Step(['sudo','install','-d','-m','700','-o','root','-g','root',str(base/leaf)]))
    context=json.dumps({'version':2,'mode':'host-only','owner':owner,'vm_uuid':vm_uuid,'parent_mac':parent_mac})
    if not keep_context:
        steps.append(Step(['sudo','tee',str(context_path(root))],context+'\n'))
        steps.append(Step(['sudo','chmod','600',str(context_path(root))]))
    if not keep_secret:
        secret=pilot(root)/'private'/'snmp-community'
        steps.append(Step(['sudo','tee',str(secret)],community+'\n'))
        steps.append(Step(['sudo','chmod','600',str(secret)]))
    return steps


def build_command(repo,tag=IMAGE_TAG):
    return ['docker','build','-f',str(Path(repo)/'demo'/'targets'/'Dockerfile'),'-t',tag,str(repo)]


def network_command():
    return ['docker','network','create','-d','macvlan','-o','parent='+PARENT,'--subnet',SUBNET,'--gateway',GATEWAY,
            '--label','org.pinpoint.defense.issue=274',NETWORK]


def memory_limit(device):
    if device.name=='db01':
        return '192m'
    if device.name=='mail01':
        return '128m'
    return '64m'


def container_command(device,root,image):
    """`docker create` (not run): the presenter starts, attaches and baselines each container."""
    base=device_root(root,device)
    dhcp_client=device.mode=='dhcp'
    argv=['docker','create','--name','pinpoint274-host-'+device.name+'-pilot','--hostname',device.name,
          '--network','none' if dhcp_client else NETWORK]
    if not dhcp_client:
        argv+=['--ip',device.address,'--mac-address',device.mac]
    for label in LABELS:
        argv+=['--label',label]
    argv+=['--restart','no','--memory',memory_limit(device),'--pids-limit','96','--cpus','0.5',
           '--tmpfs','/run:rw,nosuid,nodev,size=16m,mode=0755',
           '--log-driver','json-file','--log-opt','max-size=1m','--log-opt','max-file=2']
    if dhcp_client or device.name=='dhcp01':
        argv+=['--cap-add','NET_ADMIN']
    mounts=[(base/'identity','/identity',False),(base/'data','/data',False),
            (context_path(root),'/etc/pinpoint-defense/context.json',True)]
    if device.name in SNMP_TARGETS:
        mounts.append((pilot(root)/'private'/'snmp-community','/run/secrets/snmp-community',True))
    for source,target,readonly in mounts:
        spec='type=bind,src=%s,dst=%s'%(source,target)
        if readonly:
            spec+=',readonly'
        argv+=['--mount',spec]
    argv+=[image,'python3',CONTAINER_PATH,'init',device.name]
    return argv


def container_commands(catalog,root,image):
    commands=[]
    for device in linux_devices(catalog):
        commands.append(container_command(device,root,image))
    return commands


def exists(runner,argv):
    try:
        runner(argv)
        return True
    except (OSError,ValueError):
        return False


def apply(catalog,root,repo,runner,owner,vm_uuid,parent_mac,community,image=IMAGE_TAG):
    """Create what is missing; anything that already exists is left untouched. Re-runnable."""
    keep_context=exists(runner,['sudo','test','-e',str(context_path(root))])
    keep_secret=exists(runner,['sudo','test','-e',str(pilot(root)/'private'/'snmp-community')])
    for step in host_steps(catalog,root,owner,vm_uuid,parent_mac,community,keep_context,keep_secret):
        runner(step.argv,step.input_text)
    runner(build_command(repo,image))
    if not exists(runner,['docker','network','inspect',NETWORK]):
        runner(network_command())
    built=json.loads(runner(['docker','image','inspect',image]))[0]['Id']
    for device,argv in zip(linux_devices(catalog),container_commands(catalog,root,image)):
        name='pinpoint274-host-'+device.name+'-pilot'
        if exists(runner,['docker','inspect',name]):
            if json.loads(runner(['docker','inspect',name]))[0].get('Image')!=built:
                raise ValueError(name+' uses an older image than the one just built; run demo/demo destroy --apply, then setup again')
        else:
            runner(argv)


def read_pins(catalog,runner):
    """Container id and image id for each created container, in the presenter's pin format."""
    pins={}
    for device in linux_devices(catalog):
        data=json.loads(runner(['docker','inspect','pinpoint274-host-'+device.name+'-pilot']))
        if len(data)!=1:
            raise ValueError('Created container missing')
        pins[device.name]={'id':data[0]['Id'],'image':data[0]['Image']}
    return pins
