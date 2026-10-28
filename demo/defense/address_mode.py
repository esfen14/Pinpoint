"""Journaled DHCP-to-static and static-to-DHCP address changes for one demo client.

Callers hold the canonical lab claim. A client always ends with exactly one
address: its reserved pool address (DHCP mode) or one unused static slot outside
the pool. A private intent file is written before the first change and removed
only after the final state is verified, so an interrupted change can be rolled
back with recover().
"""
import ipaddress
import json
import os
from pathlib import Path
import stat

NAME='address-mode.json'


def intent_exists(root):
    """Any entry at the fixed name, including a dangling symlink, counts."""
    return os.path.lexists(Path(root)/NAME)


def client(catalog,target):
    device=catalog.target(target)
    if device.kind!='linux' or device.mode!='dhcp':
        raise ValueError('Address modes apply only to the five DHCP clients')
    return device


def valid_address(value):
    if not isinstance(value,str):
        raise ValueError('Invalid address')
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        raise ValueError('Invalid address') from None


def show(catalog,state):
    """Describe the observed single address as dhcp, static or unaddressed."""
    addresses=state['addresses']
    if not addresses:
        return {'mode':'unaddressed','address':None}
    if len(addresses)!=1:
        raise ValueError('Client has more than one address')
    if addresses[0] in catalog.pool:
        return {'mode':'dhcp','address':addresses[0]}
    if addresses[0] in catalog.static_slots:
        return {'mode':'static','address':addresses[0]}
    raise ValueError('Client has an address outside the demo plan')


def write_intent(root,target,original,desired):
    record={'version':1,'target':target,'original':original,'desired':desired}
    fd=os.open(Path(root)/NAME,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(record,stream)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def read_intent(root,catalog):
    path=Path(root)/NAME
    if not os.path.lexists(path):
        return None
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1 or info.st_size>4096:
            raise ValueError('Unsafe address-mode intent')
        with os.fdopen(fd,'r',closefd=False) as stream:
            record=json.load(stream)
    except json.JSONDecodeError:
        raise ValueError('Malformed address-mode intent') from None
    finally:
        os.close(fd)
    if not isinstance(record,dict) or set(record)!={'version','target','original','desired'} or record['version']!=1:
        raise ValueError('Malformed address-mode intent')
    client(catalog,record['target'])
    pair=(record['original'],record['desired'])
    if pair[0] in catalog.pool and pair[1] in catalog.static_slots:
        return record
    if pair[0] in catalog.static_slots and pair[1] in catalog.pool:
        return record
    raise ValueError('Address-mode intent has an address outside the demo plan')


def clear(root):
    os.unlink(Path(root)/NAME)


def to_static(root,catalog,lab,target,address,*,occupied):
    """Release the lease and hold one unused static slot; roll back on failure."""
    client(catalog,target)
    valid_address(address)
    if address not in catalog.static_slots:
        raise ValueError('Static address must be an unused slot outside the DHCP pool')
    if address in occupied:
        raise ValueError('Static address is already in use')
    state=lab.state()
    if state['addresses']==[address]:
        return
    if state['addresses']!=[state['reserved']] or state['reserved'] not in catalog.pool:
        raise ValueError('Client must hold its reserved DHCP address first')
    write_intent(root,target,state['reserved'],address)
    try:
        lab.release()
        lab.add_static(address)
        if lab.state()['addresses']!=[address]:
            raise ValueError('Static address was not applied')
    except Exception:
        recover(root,catalog,lab)
        raise
    clear(root)


def to_dhcp(root,catalog,lab,target):
    """Drop the static address and reacquire the reservation; roll back on failure."""
    client(catalog,target)
    state=lab.state()
    if state['addresses']==[state['reserved']]:
        return
    if len(state['addresses'])!=1 or state['addresses'][0] not in catalog.static_slots:
        raise ValueError('Client does not hold a static slot address')
    if not state['server_running']:
        raise ValueError('Allocator is not running')
    original=state['addresses'][0]
    write_intent(root,target,original,state['reserved'])
    try:
        lab.remove_static(original)
        lab.acquire(state['reserved'])
        if lab.state()['addresses']!=[state['reserved']]:
            raise ValueError('Reservation was not acquired')
    except Exception:
        recover(root,catalog,lab)
        raise
    clear(root)


def recover(root,catalog,lab):
    """Return the client to the address recorded before the interrupted change."""
    record=read_intent(root,catalog)
    if record is None:
        return
    original,desired=record['original'],record['desired']
    addresses=lab.state()['addresses']
    if addresses!=[original]:
        if original in catalog.pool:
            if addresses==[desired]:
                lab.remove_static(desired)
            elif addresses:
                raise ValueError('Client address changed unexpectedly')
            lab.acquire(original)
        else:
            if addresses==[desired]:
                lab.release()
            elif addresses:
                raise ValueError('Client address changed unexpectedly')
            lab.add_static(original)
        if lab.state()['addresses']!=[original]:
            raise ValueError('Original address was not restored')
    clear(root)
