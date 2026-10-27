"""Generate guest-only Compose configuration from the validated device catalog."""
import re

ROOT = '/var/lib/pinpoint-defense'
PROJECT = 'pinpoint-defense274'


def document(catalog, image: str, owner: str, root: str, spike: bool) -> dict:
    """Build fixed services; Docker never assigns their demo interfaces or IPs."""
    services = {}
    for device in catalog.devices:
        if device.kind!='linux' or spike and device.name not in {'dhcp01','dynweb01'}:
            continue
        volumes = []
        for source,target,readonly in [(f'{root}/identities/{device.name}','/identity',False),
                                       (f'{root}/data/{device.name}','/data',False),
                                       (f'{root}/context.json','/etc/pinpoint-defense/context.json',True)]:
            volumes.append({'type':'bind','source':source,'target':target,'read_only':readonly,
                            'bind':{'create_host_path':False}})
        if any(p.service=='snmp' for p in device.listeners):
            volumes.append({'type':'bind','source':f'{root}/private/snmp-community',
                            'target':'/run/secrets/snmp-community','read_only':True,
                            'bind':{'create_host_path':False}})
        service = {'image':image,'container_name':f'{PROJECT}-{device.name}',
                   'hostname':device.name,'network_mode':'none','restart':'no',
                   'command':['python3','/opt/pinpoint/defense/node.py','init',device.name],
                   'labels':{'org.pinpoint.defense.issue':'274','org.pinpoint.defense.owner':owner,
                             'org.pinpoint.defense.target':device.name},
                   'volumes':volumes,'tmpfs':['/run:rw,nosuid,nodev,size=16m,mode=0755'],
                   'mem_limit':'192m' if device.name=='db01' else '128m' if device.name=='mail01' else '64m',
                   'pids_limit':96,'cpus':0.5,
                   'logging':{'driver':'json-file','options':{'max-size':'1m','max-file':'2'}}}
        if device.mode=='dhcp' or device.name=='dhcp01':
            service['cap_add']=['NET_ADMIN']
        services[device.name] = service
    return {'name':PROJECT,'services':services}


def compose_document(catalog, image: str, owner: str, *, spike: bool = False) -> dict:
    """Runtime rendering accepts only a pinned image ID and a private owner marker."""
    if not isinstance(image,str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',image):
        raise ValueError('A pinned defense image ID is required')
    if not isinstance(owner,str) or not re.fullmatch(r'[a-f0-9]{48}',owner):
        raise ValueError('Invalid private project ownership marker')
    return document(catalog,image,owner,ROOT,spike)


def compose_template(catalog) -> dict:
    """Generate the review artifact; the managed guest uses compose_document instead."""
    return document(catalog,'${PINPOINT_DEFENSE_IMAGE:?pinned image ID required}',
                    '${PINPOINT_DEFENSE_OWNER:?managed project owner required}',ROOT,False)
