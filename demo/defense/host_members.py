"""Offline validation of a complete VirtualBox host-only VM inventory.

This validates supplied observations only. The future live observer must collect
all VMs, pin their identities privately, and recheck processes under the host
claim. It does not account for non-VirtualBox network namespaces.
"""
import re
import uuid

MAC=re.compile(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}')


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
            if adapter['network']=='vboxnet1':
                if adapter['type']!='hostonly':raise ValueError('Ambiguous host-only attachment')
                members.append((record['uuid'],record['state'],adapter['slot'],adapter['mac']))
    expected={(pin['uuid'],'running',pin['slot'],pin['mac']) for pin in pins.values()}
    if len(members)!=2 or set(members)!=expected:
        raise ValueError('Host-only VM membership changed')
    return True
