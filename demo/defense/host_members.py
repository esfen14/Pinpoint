"""Offline validation of a complete VirtualBox host-only VM inventory.

This validates supplied observations only. The future live observer must collect
all VMs, pin their identities privately, and recheck processes under the host
claim. It does not account for non-VirtualBox network namespaces.
"""
import re
import time
import uuid

MAC=re.compile(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}')
ADAPTER_TYPES={'nat','natnetwork','intnet','bridged','hostonly','generic'}


def valid_uuid(value):
    if not isinstance(value,str):return False
    try:return str(uuid.UUID(value))==value
    except ValueError:return False


def valid_mac(value):
    return isinstance(value,str) and MAC.fullmatch(value) is not None


def validate_vm_membership(records,pins):
    """Require exactly the two privately pinned VMs on the host-only segment."""
    if not isinstance(pins,dict) or set(pins)!={'appliance','windows'}:
        raise ValueError('Both host-only VM pins are required')
    for pin in pins.values():
        if not isinstance(pin,dict) or set(pin)!={'uuid','slot','mac'} or not valid_uuid(pin['uuid']) or type(pin['slot']) is not int or not 1<=pin['slot']<=8 or not valid_mac(pin['mac']):
            raise ValueError('Invalid host-only VM pin')
    if len({p['uuid'] for p in pins.values()})!=2 or len({p['mac'] for p in pins.values()})!=2:
        raise ValueError('Duplicate host-only VM identity')
    if not isinstance(records,list) or not 2<=len(records)<=256:
        raise ValueError('Incomplete VirtualBox inventory')
    seen=set();members=[]
    for record in records:
        if not isinstance(record,dict) or set(record)!={'uuid','state','adapters'} or not valid_uuid(record['uuid']) or record['uuid'] in seen or not isinstance(record['state'],str) or not record['state']:
            raise ValueError('Invalid or duplicate VM observation')
        seen.add(record['uuid'])
        adapters=record['adapters']
        if not isinstance(adapters,list) or len(adapters)>8:raise ValueError('Invalid VM adapter inventory')
        slots=set()
        for adapter in adapters:
            if not isinstance(adapter,dict) or set(adapter)!={'slot','type','network','mac'} or type(adapter['slot']) is not int or not 1<=adapter['slot']<=8 or adapter['slot'] in slots or not isinstance(adapter['type'],str) or not isinstance(adapter['network'],str) or not valid_mac(adapter['mac']):
                raise ValueError('Invalid VM adapter observation')
            slots.add(adapter['slot'])
            if adapter['type'] not in ADAPTER_TYPES:
                raise ValueError('Unknown VM adapter type')
            if adapter['type']=='hostonly' and not adapter['network']:
                raise ValueError('Missing host-only adapter name')
            if adapter['type']!='hostonly' and adapter['network']:
                raise ValueError('Ambiguous non-host-only adapter')
            if adapter['network']=='vboxnet1':
                if adapter['type']!='hostonly':raise ValueError('Ambiguous host-only attachment')
                members.append((record['uuid'],record['state'],adapter['slot'],adapter['mac']))
    expected={(pin['uuid'],'running',pin['slot'],pin['mac']) for pin in pins.values()}
    if len(members)!=2 or set(members)!=expected:
        raise ValueError('Host-only VM membership changed')
    return True


def parse_vm_observation(text,identifier):
    """Parse only bounded fixed NIC fields from one machine-readable VM view."""
    import json
    if not isinstance(text,str) or len(text)>1048576 or not valid_uuid(identifier):
        raise ValueError('Invalid VM observation')
    values={}
    for line in text.splitlines():
        if '=' not in line:continue
        key,value=line.split('=',1)
        if not re.fullmatch(r'(?:UUID|VMState|nic[1-8]|macaddress[1-8]|hostonlyadapter[1-8])',key):continue
        if key in values:raise ValueError('Duplicate VM field')
        try:parsed=json.loads(value)
        except (ValueError,TypeError):raise ValueError('Malformed VM field') from None
        if not isinstance(parsed,str):raise ValueError('Malformed VM field')
        values[key]=parsed
    if values.get('UUID')!=identifier or not values.get('VMState'):
        raise ValueError('VM identity or state changed')
    adapters=[]
    for slot in range(1,9):
        name=str(slot);kind=values.get('nic'+name)
        if kind is None:raise ValueError('Incomplete VM adapter inventory')
        if kind=='none':continue
        if kind not in ADAPTER_TYPES:
            raise ValueError('Unknown VM adapter type')
        raw=values.get('macaddress'+name,'').lower()
        if not re.fullmatch(r'[a-f0-9]{12}',raw):raise ValueError('Invalid VM MAC')
        network=values.get('hostonlyadapter'+name,'') if kind=='hostonly' else ''
        if kind=='hostonly' and not network:raise ValueError('Missing host-only adapter name')
        adapters.append({'slot':slot,'type':kind,'network':network,
                         'mac':':'.join(raw[i:i+2] for i in range(0,12,2))})
    return {'uuid':identifier,'state':values['VMState'],'adapters':adapters}


def collect_vm_inventory(observe):
    """Collect bounded VM NIC metadata twice around fixed-argv observations.

    The observer itself must enforce a subprocess timeout; the total deadline
    is checked before every call. No host or VM mutation is performed.
    """
    deadline=time.monotonic()+40
    def call(argv):
        if time.monotonic()>=deadline:raise ValueError('VM inventory deadline exceeded')
        return observe(argv)
    def identifiers(text):
        if not isinstance(text,str) or len(text)>1048576:raise ValueError('Invalid VM inventory')
        found=[]
        for line in text.splitlines():
            match=re.fullmatch(r'".*" \{([a-f0-9-]{36})\}',line)
            if not match or not valid_uuid(match[1]) or match[1] in found:
                raise ValueError('Invalid or duplicated VM inventory')
            found.append(match[1])
        if not 2<=len(found)<=64:raise ValueError('Incomplete or oversized VM inventory')
        return found
    first=identifiers(call(['VBoxManage','list','vms']))
    records=[parse_vm_observation(call(['VBoxManage','showvminfo',identifier,'--machinereadable']),identifier)
             for identifier in first]
    if identifiers(call(['VBoxManage','list','vms']))!=first:
        raise ValueError('VM inventory changed during observation')
    repeated=[parse_vm_observation(call(['VBoxManage','showvminfo',identifier,'--machinereadable']),identifier)
              for identifier in first]
    if repeated!=records or identifiers(call(['VBoxManage','list','vms']))!=first:
        raise ValueError('VM configuration changed during observation')
    return records
