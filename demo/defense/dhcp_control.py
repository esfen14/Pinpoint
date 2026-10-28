"""Journaled DHCP move and recovery; caller supplies the checked lab adapter.

The caller must hold the presenter claim, and the adapter must verify network,
container and process ownership on every snapshot and operation.
"""
from defense import dhcp_journal
from defense.dhcp_move import plan_move


def snapshot(lab,record=None):
    state=lab.snapshot()
    required={'pins','reservations','addresses','lease_seconds','server_running'}
    if not isinstance(state,dict) or set(state)!=required or type(state['server_running']) is not bool or state['lease_seconds']!=600:
        raise ValueError('Incomplete DHCP state')
    if record is not None and state['pins']!=record['pins']:
        raise ValueError('DHCP container identities changed')
    return state


def matches(state,record,reservations):
    return (state['pins']==record['pins'] and state['server_running'] is True
            and state['reservations']==reservations
            and state['addresses']=={name:[address] for name,address in reservations.items()})


def recover(root,catalog,lab):
    """Restore original reservations after an interrupted or failed move."""
    record=dhcp_journal.read(root,catalog)
    if record['phase'] not in {'rollback_requested','restored'}:
        record=dhcp_journal.advance(root,catalog,'rollback_requested')
    original=record['plan']['before'];after=record['plan']['after'];target=record['plan']['target']
    # A restarted allocator container comes back without its daemons or safe routes.
    lab.restore_baseline()
    state=snapshot(lab,record)
    if not isinstance(state['addresses'],dict) or set(state['addresses'])!=set(original):
        raise ValueError('Incomplete client observations')
    for name,address in original.items():
        if name!=target and state['addresses'][name]!=[address]:
            raise ValueError('Another DHCP client changed')
    current=state['addresses'][target]
    if current not in ([],[original[target]],[after[target]]):
        raise ValueError('Target address changed unexpectedly')
    if state['reservations'] not in (None,original,after):
        raise ValueError('Allocator reservations changed unexpectedly')
    if record['phase']=='restored':
        if not matches(state,record,original):raise ValueError('Restored baseline changed')
        dhcp_journal.clear(root,catalog);return
    if current and (current!=[original[target]] or state['reservations']!=original or not state['server_running']):
        lab.release(target)
        state=snapshot(lab,record)
        if state['addresses'].get(target)!=[]:raise ValueError('Client release failed')
    if state['reservations']!=original or not state['server_running']:
        lab.configure(original)
        state=snapshot(lab,record)
        if state['reservations']!=original or not state['server_running']:
            raise ValueError('Allocator restoration failed')
    if state['addresses'].get(target)==[]:
        lab.acquire(target,original[target])
        state=snapshot(lab,record)
    if not matches(state,record,original):raise ValueError('Rollback baseline not restored')
    dhcp_journal.advance(root,catalog,'restored')
    dhcp_journal.clear(root,catalog)


def move(root,catalog,lab,target,destination):
    """Move a single client and automatically restore the original on failure."""
    before=snapshot(lab)
    if not before['server_running']:raise ValueError('Allocator is not running')
    plan=plan_move(catalog,target,destination,before['reservations'],before['addresses'])
    if not plan['change']:return
    record=dhcp_journal.prepare(root,catalog,plan,before['pins'])
    try:
        # Reapply the checked baseline so the running allocator has loaded the
        # reservations we observed before any client is released.
        lab.configure(plan['before'])
        if not matches(snapshot(lab,record),record,plan['before']):
            raise ValueError('Allocator baseline was not verified')
        lab.release(target)
        state=snapshot(lab,record)
        expected=dict(before['addresses']);expected[target]=[]
        if state['addresses']!=expected or state['reservations']!=plan['before'] or not state['server_running']:
            raise ValueError('Client release was not verified')
        dhcp_journal.advance(root,catalog,'released')
        lab.configure(plan['after'])
        state=snapshot(lab,record)
        if state['addresses']!=expected or state['reservations']!=plan['after'] or not state['server_running']:
            raise ValueError('Allocator change was not verified')
        dhcp_journal.advance(root,catalog,'server_changed')
        lab.acquire(target,destination)
        state=snapshot(lab,record)
        if not matches(state,record,plan['after']):raise ValueError('New DHCP lease was not verified')
        dhcp_journal.advance(root,catalog,'acquired')
        dhcp_journal.clear(root,catalog)
    except (Exception,KeyboardInterrupt):
        try:recover(root,catalog,lab)
        except (Exception,KeyboardInterrupt):pass
        raise
