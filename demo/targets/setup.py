"""Plan, preflight and teardown for the Docker demo lab (`demo/demo setup|destroy`).

Prints a plan and changes nothing without --apply. Container creation under
--apply is deliberately not implemented yet: see issue #298 and the progress notes.
"""
import ipaddress
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from targets.catalog import load_catalog

NETWORK_NAME='pinpoint274-host-test'
PARENT='vboxnet1'
SUBNET=ipaddress.ip_network('10.77.1.0/27')
MIN_AVAILABLE_MIB=3072
OWNER_ISSUE=('org.pinpoint.defense.issue','274')
OWNER_ROLE=('org.pinpoint.defense.role','temporary-pilot')
CONFIRMATION='destroy'


def plan(catalog):
    """Ordered steps; the container count and names come from the catalog."""
    names=[]
    for device in catalog.devices:
        if device.kind=='linux':
            names.append(device.name)
    steps=['1. Preflight: Docker, VirtualBox, host-only network %s, subnet and VPN conflicts, memory'%PARENT,
           '2. Build the image from demo/targets/Dockerfile',
           '3. Create the network %s (macvlan on %s, %s)'%(NETWORK_NAME,PARENT,SUBNET),
           '4. Create the %d containers: %s'%(len(names),', '.join(names)),
           '5. Attach the DHCP interfaces of the five DHCP clients',
           '6. Enroll the containers (pin their identities for the presenter controls)',
           '7. Check the appliance and the Windows VM are attached to %s'%PARENT,
           '8. Print the pass/fail summary']
    return steps


def manual_checklist():
    """Steps that need a person, each with a command or place to check it."""
    return [('Appliance adapter 2 on the host-only network',
             'VBoxManage showvminfo <appliance-vm> | grep "NIC 2"   (expect host-only %s)'%PARENT),
            ('Appliance address 10.77.1.1/27 on that adapter',
             'in the appliance: ip -br -4 address   (see demo/appliance/PRESENTER_SETUP.md)'),
            ('Windows credentials and NCPA registration',
             'in Pinpoint: NCPA Deployment, Register an agent I installed; then the Windows CPU, memory and disk checks are OK'),
            ('Pinpoint discovery network 10.77.1.0/27',
             'Pinpoint Settings, Discovery, Networks lists 10.77.1.0/27'),
            ('Nagios timing check_interval 1, max_check_attempts 1 (optional, faster alerts)',
             'in the appliance: grep -E "check_interval|max_check_attempts" on the service template')]


def preflight(runner,available_mib):
    """Read-only checks; returns (name, ok, detail) rows. `runner` returns command output or raises."""
    rows=[]
    try:
        runner(['docker','version'])
        rows.append(('Docker',True,'available'))
    except (OSError,subprocess.SubprocessError,ValueError):
        rows.append(('Docker',False,'docker is not available to this user'))
    try:
        runner(['VBoxManage','--version'])
        listing=runner(['VBoxManage','list','hostonlyifs'])
        present=False
        for line in listing.splitlines():
            if line.strip()=='Name: '+PARENT or line.strip()=='Name:            '+PARENT:
                present=True
        rows.append(('Host-only network '+PARENT,present,'present' if present else PARENT+' not found'))
    except (OSError,subprocess.SubprocessError,ValueError):
        rows.append(('Host-only network '+PARENT,False,'VBoxManage is not available'))
    conflicts=[]
    try:
        routes=json.loads(runner(['ip','-j','route','show']))
        for route in routes:
            destination=route.get('dst','')
            if destination=='default' or route.get('dev')==PARENT:
                continue
            try:
                other=ipaddress.ip_network(destination,strict=False)
            except ValueError:
                continue
            if other.overlaps(SUBNET):
                conflicts.append('%s via %s'%(destination,route.get('dev')))
    except (OSError,subprocess.SubprocessError,ValueError):
        conflicts.append('routes unreadable')
    rows.append(('Subnet conflicts',not conflicts,', '.join(conflicts) or 'none'))
    rows.append(('Memory',available_mib>=MIN_AVAILABLE_MIB,'%d MiB available, %d MiB needed'%(available_mib,MIN_AVAILABLE_MIB)))
    return rows


def default_runner(argv):
    result=subprocess.run(argv,capture_output=True,text=True,timeout=30)
    if result.returncode:
        raise ValueError('command failed')
    return result.stdout


def default_available_mib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])//1024
    return 0


def owned(inspected):
    """True only for a container carrying both owner labels and the pilot name."""
    if len(inspected)!=1:
        return False
    labels=inspected[0].get('Config',{}).get('Labels') or {}
    name=inspected[0].get('Name','')
    return labels.get(OWNER_ISSUE[0])==OWNER_ISSUE[1] and labels.get(OWNER_ROLE[0])==OWNER_ROLE[1] and name.startswith('/pinpoint274-host-')


def destroy(runner,apply,ask,out,err):
    """Remove only demo-owned containers and the owned network, after a typed confirmation."""
    ids=runner(['docker','ps','-a','-q','--filter','name=pinpoint274-host-']).split()
    victims=[]
    for identifier in ids:
        inspected=json.loads(runner(['docker','inspect',identifier]))
        if not owned(inspected):
            print('Container %s is not owned by the demo lab; refusing.'%identifier[:12],file=err)
            return 1
        victims.append((identifier,inspected[0]['Name'].lstrip('/')))
    network=json.loads(runner(['docker','network','inspect',NETWORK_NAME]) or '[]')
    network_owned=len(network)==1 and network[0].get('Driver')=='macvlan' and (network[0].get('Labels') or {}).get(OWNER_ISSUE[0])==OWNER_ISSUE[1]
    print('Would remove:' if not apply else 'Removing:',file=out)
    for identifier,name in victims:
        print('  container',name,file=out)
    if network_owned:
        print('  network',NETWORK_NAME,file=out)
    if not victims and not network_owned:
        print('  nothing',file=out)
    if not apply:
        print('Nothing was changed. Add --apply and type "%s" to remove them.'%CONFIRMATION,file=out)
        return 0
    if ask('Type "%s" to remove these demo-owned objects: '%CONFIRMATION)!=CONFIRMATION:
        print('Not confirmed; nothing was removed.',file=err)
        return 1
    for identifier,name in victims:
        runner(['docker','rm','-f',identifier])
    if network_owned:
        runner(['docker','network','rm',NETWORK_NAME])
    print('Removed.',file=out)
    return 0


def main(argv,runner=default_runner,available_mib=default_available_mib,ask=input,out=sys.stdout,err=sys.stderr):
    if not argv or argv[0] not in {'setup','destroy'} or any(a!='--apply' for a in argv[1:]) or len(argv)>2:
        print('usage: demo/demo setup [--apply] | demo/demo destroy [--apply]',file=err)
        return 2
    apply='--apply' in argv[1:]
    if argv[0]=='destroy':
        try:
            return destroy(runner,apply,ask,out,err)
        except (OSError,ValueError,subprocess.SubprocessError):
            print('Destroy refused: Docker state could not be read.',file=err)
            return 1
    catalog=load_catalog()
    rows=preflight(runner,available_mib())
    print('Preflight',file=out)
    for name,ok,detail in rows:
        print('  %-4s %s: %s'%('ok' if ok else 'FAIL',name,detail),file=out)
    print('\nPlan (nothing is changed without --apply)',file=out)
    for step in plan(catalog):
        print('  '+step,file=out)
    print('\nManual steps (cannot be scripted)',file=out)
    for title,check in manual_checklist():
        print('  [ ] %s\n      check: %s'%(title,check),file=out)
    if any(not ok for _,ok,_ in rows):
        print('\nSummary: FAIL, fix the blockers above first.',file=out)
        return 1
    if apply:
        print('Container creation (steps 2 to 6) is not implemented yet; it needs review. Nothing was changed.',file=err)
        return 2
    print('\nSummary: preflight passed; no changes made.',file=out)
    return 0


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
