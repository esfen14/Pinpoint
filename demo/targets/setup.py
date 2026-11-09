"""Plan, preflight, creation and teardown for the Docker demo lab (`demo/demo setup|destroy`).

Prints a plan and changes nothing without --apply. Creation commands are built in
create.py; their live run needs the real Docker and VirtualBox lab (issue #298).
"""
import ipaddress
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from targets.catalog import load_catalog
from targets import create

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
    try:
        addresses=json.loads(runner(['ip','-j','-4','addr','show','dev',PARENT]))
        up=False
        for link in addresses:
            for info in link.get('addr_info',[]):
                if info.get('local')=='192.168.57.1':
                    up=True
        rows.append(('Host-only address',up,'192.168.57.1 present' if up else PARENT+' has no address: start a VM attached to it (Windows or the appliance), then re-run'))
    except (OSError,subprocess.SubprocessError,ValueError):
        rows.append(('Host-only address',False,PARENT+' has no address: start a VM attached to it (Windows or the appliance), then re-run'))
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


def vm_attachments(runner):
    """Read-only: each demo VM must have a host-only adapter on vboxnet1."""
    rows=[]
    for name in ('Pinpoint-Final','pinpoint-defense-win01'):
        try:
            info=runner(['VBoxManage','showvminfo',name,'--machinereadable'])
        except (OSError,ValueError,subprocess.SubprocessError):
            rows.append(('VM '+name,False,'not found'))
            continue
        attached='hostonlyadapter' in info and '="'+PARENT+'"' in info
        rows.append(('VM '+name,attached,'on '+PARENT if attached else 'not attached to '+PARENT))
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


def default_start():
    subprocess.run([sys.executable,'-I',str(Path(__file__).with_name('presenter.py')),'up'],check=True,timeout=900)


def lab_complete(catalog,runner):
    for device in catalog.devices:
        if device.kind=='linux':
            try:
                runner(['docker','inspect','pinpoint274-host-'+device.name+'-pilot'])
            except (OSError,ValueError,subprocess.SubprocessError):
                return False
    return True


def default_create_lab(catalog,out):
    """Create the network, image and fourteen containers, pin them, then start them with the presenter."""
    import os
    import secrets
    from targets import presenter
    repo=Path(__file__).resolve().parents[2]
    uuid=subprocess.run(['sudo','cat','/sys/class/dmi/id/product_uuid'],capture_output=True,text=True,check=True,timeout=60).stdout.strip()
    mac=Path('/sys/class/net/'+PARENT+'/address').read_text().strip()

    def runner(argv,input_text=None):
        result=subprocess.run(argv,input=input_text,capture_output=True,text=True,timeout=1800)
        if result.returncode:
            raise ValueError('command failed: '+argv[0]+' '+' '.join(argv[1:3]))
        return result.stdout
    create.apply(catalog,presenter.ROOT,repo,runner,owner=secrets.token_hex(24),vm_uuid=uuid,parent_mac=mac,community=create.new_community())
    pins=create.read_pins(catalog,runner)
    if presenter.PINS.is_file() and not presenter.PINS.is_symlink():
        presenter.PINS.unlink()  # pins always describe the containers that exist now
    fd=os.open(presenter.PINS,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(pins,stream)
        stream.write('\n')
    print('Containers created and pinned; starting them with the presenter.',file=out)
    subprocess.run([sys.executable,'-I',str(Path(__file__).with_name('presenter.py')),'up'],check=True,timeout=900)


def main(argv,runner=default_runner,available_mib=default_available_mib,ask=input,out=sys.stdout,err=sys.stderr,create_lab=default_create_lab,start=default_start):
    if not argv or argv[0] not in {'setup','destroy','up'} or any(a!='--apply' for a in argv[1:]) or len(argv)>2:
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
    if argv[0]=='up':
        if apply:
            print('usage: demo/demo up',file=err)
            return 2
        try:
            if not lab_complete(catalog,runner):
                print('Containers are missing; creating them first.',file=out)
                create_lab(catalog,out)
            start()
        except (OSError,ValueError,subprocess.SubprocessError):
            print('Up stopped: a step failed. Run demo/demo setup to see the plan and preflight.',file=err)
            return 1
        return 0
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
        try:
            create_lab(catalog,out)
        except (OSError,ValueError,subprocess.SubprocessError) as problem:
            print('Setup stopped: %s. It is safe to re-run; existing objects are kept.'%(problem or 'a creation step failed'),file=err)
            return 1
        vm_rows=vm_attachments(runner)
        print('\nVM attachment',file=out)
        for name,ok,detail in vm_rows:
            print('  %-4s %s: %s'%('ok' if ok else 'FAIL',name,detail),file=out)
        if any(not ok for _,ok,_ in vm_rows):
            print('\nSummary: FAIL, containers are up but a VM is missing or not on %s. Run demo/demo create-vms, then see demo/appliance/README.md.'%PARENT,file=out)
            return 1
        print('\nSummary: PASS, containers created and started. Next: demo/demo presenter enroll-vms, then demo/demo presenter preflight.',file=out)
        return 0
    print('\nSummary: preflight passed; no changes made.',file=out)
    return 0


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
