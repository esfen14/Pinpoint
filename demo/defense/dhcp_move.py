"""Offline planning for fixed DHCP client address changes.

This module does not inspect or mutate the running lab. A live controller must
separately prove container, network and process ownership, persist recovery
intent, and implement rollback before executing a plan.
"""
from defense.catalog import render_dnsmasq


def plan_move(catalog, target, destination, reservations, observed):
    """Validate the entire reserved client set before planning one change."""
    device=catalog.target(target)
    if device.kind!='linux' or device.mode!='dhcp':
        raise ValueError('A catalog DHCP client is required')
    if not isinstance(destination,str) or destination not in catalog.pool:
        raise ValueError('Destination must be in the fixed DHCP pool')
    render_dnsmasq(catalog,reservations)
    names={d.name for d in catalog.devices if d.mode=='dhcp'}
    if any(reservations[name] is None for name in names):
        raise ValueError('Every client requires a reservation')
    if not isinstance(observed,dict) or set(observed)!=names:
        raise ValueError('All client addresses must be observed')
    if any(observed[name]!=[reservations[name]] for name in names):
        raise ValueError('Client addresses disagree with reservations')
    if destination in {reservations[name] for name in names if name!=target}:
        raise ValueError('Destination is already reserved')
    before=dict(reservations)
    after=dict(before);after[target]=destination
    render_dnsmasq(catalog,after)
    return {'target':target,'before':before,'after':after,'change':before!=after}
