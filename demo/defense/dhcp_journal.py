"""Durable intent for future DHCP moves; no live network operations here.

Callers must hold the canonical lab claim. A phase is a recovery hint only:
actual container and allocator state must be re-observed before recovery.
"""
import json
import os
from pathlib import Path
import re
import stat

from defense.dhcp_move import plan_move
from defense.node import atomic
from defense.preflight import read_private_json

NAME='dhcp-move.json'
TRANSITIONS={
    'prepared':{'released','rollback_requested'},
    'released':{'server_changed','rollback_requested'},
    'server_changed':{'acquired','rollback_requested'},
    'acquired':{'rollback_requested'},
    'rollback_requested':{'restored'},
    'restored':set(),
}


def validate(catalog,record):
    """Reject foreign, malformed or ambiguous recovery intent."""
    if not isinstance(record,dict) or set(record)!={'version','phase','plan','pins'} or type(record['version']) is not int or record['version']!=1 or not isinstance(record['phase'],str) or record['phase'] not in TRANSITIONS:
        raise ValueError('Invalid DHCP recovery intent')
    plan=record['plan']
    if not isinstance(plan,dict) or set(plan)!={'target','before','after','change'} or plan['change'] is not True:
        raise ValueError('Invalid DHCP recovery plan')
    before=plan['before'];after=plan['after'];target=plan['target']
    if not isinstance(before,dict) or not isinstance(after,dict) or not isinstance(target,str) or target not in after:
        raise ValueError('Invalid DHCP recovery plan')
    expected=plan_move(catalog,target,after[target],before,{name:[addr] for name,addr in before.items()})
    if plan!=expected:raise ValueError('DHCP recovery plan changed')
    names={'dhcp01'} | {d.name for d in catalog.devices if d.mode=='dhcp'}
    pins=record['pins']
    if not isinstance(pins,dict) or set(pins)!=names or any(not isinstance(v,str) or not re.fullmatch(r'[a-f0-9]{64}',v) for v in pins.values()) or len(set(pins.values()))!=len(pins):
        raise ValueError('Invalid DHCP recovery identities')
    return record


def directory(root):
    root=Path(root);info=root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
        raise ValueError('Unsafe DHCP recovery directory')
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    actual=os.fstat(fd)
    if (actual.st_dev,actual.st_ino)!=(info.st_dev,info.st_ino):
        os.close(fd);raise ValueError('DHCP recovery directory changed')
    return fd


def prepare(root,catalog,plan,pins):
    """Persist private intent before a caller performs its first mutation."""
    record=validate(catalog,{'version':1,'phase':'prepared','plan':plan,'pins':pins})
    fd=directory(root)
    try:
        try:
            file_fd=os.open(NAME,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        except FileExistsError:
            raise ValueError('DHCP recovery intent already exists') from None
        with os.fdopen(file_fd,'w') as stream:
            os.fchmod(stream.fileno(),0o600)
            json.dump(record,stream,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.fsync(fd)
    finally:os.close(fd)
    return record


def read(root,catalog):
    """Read only a checked private regular file and validate every field."""
    return validate(catalog,read_private_json(Path(root)/NAME))


def advance(root,catalog,phase):
    """Record only a valid next phase, using atomic durable replacement."""
    record=read(root,catalog)
    if phase not in TRANSITIONS[record['phase']]:raise ValueError('Invalid DHCP recovery transition')
    record['phase']=phase
    validate(catalog,record)
    atomic(Path(root)/NAME,json.dumps(record,sort_keys=True)+'\n')
    return record


def clear(root,catalog):
    """Remove only terminal intent after the caller verifies actual state."""
    record=read(root,catalog)
    if record['phase'] not in {'acquired','restored'}:raise ValueError('DHCP recovery is not complete')
    fd=directory(root)
    try:
        info=os.stat(NAME,dir_fd=fd,follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:
            raise ValueError('Unsafe DHCP recovery intent')
        os.unlink(NAME,dir_fd=fd);os.fsync(fd)
    finally:os.close(fd)
