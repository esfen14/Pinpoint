"""Fixed unattended-install and pinned-SSH inputs for a fresh target-host VM."""
import json
from pathlib import Path
import re
import subprocess


def validate_iso_detection(code: int,stdout: str,stderr: str) -> None:
    """Accept Ubuntu Server 24.04 only, including VBox's documented partial-detection code.

    Upstream UnattendedImpl.cpp maps S_FALSE to E_NOTIMPL even after identifying
    Linux media; its prepare method explicitly permits E_NOTIMPL. Other errors
    and incomplete/unsupported detection remain fatal.
    """
    required=[r'OS TypeId\s*=\s*Ubuntu24_64',r'OS Version\s*=\s*24\.04\.\d+ LTS',
              r'OS Flavor\s*=\s*Ubuntu-Server',r'Unattended installation supported\s*=\s*yes']
    if any(not re.search(pattern,stdout) for pattern in required):
        raise ValueError('Supported Ubuntu Server 24.04 media was not detected')
    if code==0 and not stderr.strip():return
    lines=stderr.strip().splitlines()
    if code!=1 or len(lines)!=2 or lines[0]!='VBoxManage: error: Code NS_ERROR_NOT_IMPLEMENTED (0x80004001) - Not implemented (extended info not available)' or not re.fullmatch(r'VBoxManage: error: Context: "DetectIsoOS\(\)" at line \d+ of file VBoxManageMisc\.cpp',lines[1]):
        raise ValueError('Unexpected installation-media detection error')


def detect_ubuntu(iso: Path) -> None:
    """Bound a read-only media detector and suppress raw diagnostics on refusal."""
    result=subprocess.run(['VBoxManage','unattended','detect','--iso='+str(iso)],capture_output=True,text=True,timeout=30)
    validate_iso_detection(result.returncode,result.stdout,result.stderr)


def install_commands(identifier: str, root: Path, iso: Path) -> list[list[str]]:
    """Prepare existing exact-owned powered-off VM media; never boot or expose secrets."""
    if not re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',identifier):
        raise ValueError('Invalid target-host UUID')
    if not root.is_absolute() or not iso.is_absolute():
        raise ValueError('Installer paths must be absolute')
    return [['VBoxManage','unattended','install',identifier,'--iso='+str(iso),
             '--user=defense','--user-password-file='+str(root/'login-password'),
             '--full-user-name=Pinpoint Defense','--hostname=defense-targets.demo.test',
             '--locale=en_US','--time-zone=UTC','--no-install-additions',
             '--script-template='+str(root/'autoinstall.yaml'),
             '--post-install-template='+str(root/'postinstall.sh'),
             '--auxiliary-base-path='+str(root/'media'/'Unattended-'),
             '--start-vm=none']]


def autoinstall_template(nat_mac: str,parent_mac: str) -> str:
    """Bind installation networking to the distinct pinned NAT/internal NIC MACs."""
    for mac in [nat_mac,parent_mac]:
        if not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}',mac):
            raise ValueError('Invalid target-host MAC')
    if nat_mac==parent_mac:raise ValueError('Target-host NIC MACs must differ')
    return f'''#cloud-config
autoinstall:
  version: 1
  apt:
    geoip: false
    fallback: offline-install
    primary:
      - arches: [default]
        uri: https://archive.ubuntu.com/ubuntu
  locale: en_US.UTF-8
  keyboard:
    layout: us
  shutdown: poweroff
  storage:
    layout:
      name: direct
    swap:
      size: 0
  ssh:
    install-server: true
    allow-pw: false
  network:
    version: 2
    ethernets:
      management:
        match:
          macaddress: "{nat_mac}"
        dhcp4: true
        dhcp6: false
        link-local: []
      demo:
        match:
          macaddress: "{parent_mac}"
        dhcp4: false
        dhcp6: false
        accept-ra: false
        link-local: []
        optional: true
  identity:
    hostname: defense-targets
    username: defense
    realname: Pinpoint Defense
    password: '@@VBOX_INSERT_USER_PASSWORD_SHACRYPT512@@'
  user-data:
    ssh_deletekeys: false
    ssh_genkeytypes: []
  late-commands:
    - cp /cdrom/vboxpostinstall.sh /target/root/vboxpostinstall.sh
    - chmod 700 /target/root/vboxpostinstall.sh
    - curtin in-target --target=/target -- /bin/bash /root/vboxpostinstall.sh --direct
'''


def postinstall_template(payload: dict) -> str:
    """Keep private material in a mode-0600 template and feed Python through stdin."""
    bootstrap=Path(__file__).with_name('bootstrap.py').read_text()
    return ("#!/bin/bash\nset -euo pipefail\numask 077\n"
            "cat > /root/pinpoint-defense-bootstrap.py <<'PINPOINT_BOOTSTRAP_CODE'\n"+
            bootstrap+"\nPINPOINT_BOOTSTRAP_CODE\n"
            "python3 /root/pinpoint-defense-bootstrap.py <<'PINPOINT_PRIVATE_INPUT'\n"+
            json.dumps(payload,separators=(',',':'))+"\nPINPOINT_PRIVATE_INPUT\n"
            "rm -f /root/pinpoint-defense-bootstrap.py /root/vboxpostinstall.sh\n")


def ssh_arguments(root: Path) -> list[str]:
    """Use the pre-injected host key, never TOFU or a process argument containing a secret."""
    if not root.is_absolute():raise ValueError('SSH state path must be absolute')
    return ['ssh','-F','/dev/null','-o','BatchMode=yes','-o','IdentitiesOnly=yes',
            '-o','StrictHostKeyChecking=yes','-o','GlobalKnownHostsFile=/dev/null',
            '-o','UserKnownHostsFile='+str(root/'known_hosts'),
            '-o','HostKeyAlgorithms=ssh-ed25519','-o','ConnectTimeout=10',
            '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2',
            '-i',str(root/'management-key'),'-p','2260','defense@127.0.0.1']


def creation_commands(identifier: str,owner: str,root: Path,macs: list[str]) -> list[list[str]]:
    """Create only the new pinned VM; this plan contains no start/delete/clone command."""
    install_commands(identifier,root,root/'placeholder.iso')
    if not re.fullmatch(r'[a-f0-9]{48}',owner) or len(macs)!=2 or len(set(macs))!=2:
        raise ValueError('Invalid target-host ownership/MACs')
    autoinstall_template(*macs)
    name='pinpoint-defense-targets'
    disk=root/'vm'/name/(name+'.vdi')
    raw=[m.replace(':','') for m in macs]
    return [['VBoxManage','createvm','--name',name,'--uuid',identifier,'--ostype','Ubuntu_64','--basefolder',str(root/'vm'),'--register'],
            ['VBoxManage','setextradata',identifier,'org.pinpoint.defense.issue274',owner],
            ['VBoxManage','modifyvm',identifier,'--memory','2048','--cpus','2','--nic1','nat','--macaddress1',raw[0],
             '--nat-pf1','management,tcp,127.0.0.1,2260,,22','--nicpromisc1','deny',
             '--nic2','intnet','--intnet2','pinpoint-defense','--macaddress2',raw[1],'--nicpromisc2','allow-vms',
             *[v for n in range(3,9) for v in [f'--nic{n}','none']],
             '--audio-driver','none','--graphicscontroller','vmsvga','--vram','16','--rtc-use-utc','on',
             '--boot1','disk','--boot2','dvd','--boot3','none','--boot4','none'],
            ['VBoxManage','createmedium','disk','--filename',str(disk),'--size','16384','--format','VDI'],
            ['VBoxManage','storagectl',identifier,'--name','SATA','--add','sata','--controller','IntelAhci'],
            ['VBoxManage','storageattach',identifier,'--storagectl','SATA','--port','0','--device','0','--type','hdd','--medium',str(disk)],
            ['VBoxManage','storagectl',identifier,'--name','IDE','--add','ide','--controller','PIIX4'],
            ['VBoxManage','storageattach',identifier,'--storagectl','IDE','--port','1','--device','0','--type','dvddrive','--medium','emptydrive']]


def prepare(iso: Path, *, apply=False) -> dict:
    """Preview or create fresh powered-off media under the shared host claim; never boot."""
    import os
    import secrets
    import shutil
    import subprocess
    import uuid
    import sys
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/'scripts'))
    sys.path.insert(0,str(repo/'demo'))
    import qa_control
    import vmlab_preflight
    from defense.controller import Collector,STATE_ROOT,WINDOWS_ROOT,network_inventory,allocated_mib,parse_info,vm_record,OWNER_KEY,observed_info
    from defense.catalog import load_catalog
    from defense.preflight import reject_overlaps,reject_virtualbox_dhcp,check_resources,validate_vm,validate_vm_macs
    from defense.node import atomic,private_directory
    root=STATE_ROOT/'target-host'
    with qa_control.claim():
        collector=Collector()
        if iso.is_symlink() or not iso.is_absolute() or not iso.is_file():raise ValueError('A local regular Ubuntu server ISO is required')
        if root.exists():raise ValueError('Target-host preparation already exists; inspect and resume its exact pinned state')
        reject_overlaps(network_inventory(collector))
        reject_virtualbox_dhcp(collector.vbox('list','dhcpservers'))
        records=[]
        for line in collector.vbox('list','vms').splitlines():
            match=re.search(r'\{([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})\}$',line)
            if not match:raise ValueError('VM inventory is incomplete')
            record=vm_record(observed_info(collector,match[1]),None)
            if record['name']=='pinpoint-defense-targets':raise ValueError('Target-host name already belongs to an existing VM')
            if record['state']!='poweroff':raise ValueError('All VMs must be off before fresh target-host preparation')
            if any(n['network']=='pinpoint-defense' for n in record['nics']) and record['name']!='pinpoint-defense-win01':
                raise ValueError('An unexpected VM is attached to the proposed segment')
            if any(f['port']==2260 for f in record['forwards']):raise ValueError('Management port is already configured on another VM')
            records.append(record)
        managers,processes=vmlab_preflight.inventory()
        if len(managers)!=1 or processes:raise ValueError('Host controller/process ownership is ambiguous')
        if vmlab_preflight.tcp_listeners([2260]).get(2260):raise ValueError('Target management endpoint is occupied')
        validate_vm_macs(load_catalog(),records)
        memory=re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)
        if not memory:raise ValueError('Memory inventory unavailable')
        available=int(memory[1])//1024
        free=shutil.disk_usage(Path.home()).free//1048576
        required_disk=max(40960-allocated_mib(WINDOWS_ROOT),0)+16384+8192+2048+1024+10240
        check_resources(available,free,[2048],required_disk)
        detect_ubuntu(iso)
        summary={'name':'pinpoint-defense-targets','memory_mib':2048,'disk_max_mib':16384,
                 'network':'pinpoint-defense','management':'127.0.0.1:2260',
                 'demo_parent':'unnumbered','available_mib':available,'required_prepare_mib':5632,
                 'free_disk_mib':free,'required_disk_mib':required_disk,'applied':False,
                 'booted':False,'ssh_trust':'pre-generated injected ed25519 host key'}
        if not apply:return summary
        os.umask(0o077)
        # Every existing ancestor in the task-owned store must already be private.
        parent=Path.home()/'.local/share/pinpoint-defense'
        private_directory(parent)
        if not STATE_ROOT.exists():STATE_ROOT.mkdir(mode=0o700)
        private_directory(STATE_ROOT)
        root.mkdir(mode=0o700);(root/'media').mkdir(mode=0o700)
        identifier=str(uuid.uuid4());owner=secrets.token_hex(24)
        occupied={n['mac'] for r in records for n in r['nics']}|{d.mac for d in load_catalog().devices}
        macs=[]
        while len(macs)<2:
            value='02:77:01:fe:'+':'.join(f'{v:02x}' for v in secrets.token_bytes(2))
            if value not in occupied and value not in macs:macs.append(value)
        state={'version':1,'uuid':identifier,'owner':owner,'macs':macs,'phase':'planned','iso':str(iso)}
        atomic(root/'state.json',json.dumps(state)+'\n')
        log=root/'prepare.log'
        def execute(argv):
            """Keep unattended/key metadata in a private log, never in a public error."""
            with log.open('ab') as output:
                result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=output,timeout=120)
            if result.returncode:raise ValueError('Target-host preparation command failed; inspect its private log')
        for name in ['management-key','host-key']:
            execute(['ssh-keygen','-q','-t','ed25519','-N','','-C','pinpoint-defense','-f',str(root/name)])
        atomic(root/'login-password',secrets.token_urlsafe(32)+'\n')
        files={name:(Path(__file__).parent/name).read_text() for name in
               ['__init__.py','catalog.py','compose.py','manifest.json','preflight.py','node.py','guest.py','Dockerfile','Dockerfile.dockerignore','bootstrap.py']}
        public=(root/'host-key.pub').read_text()
        payload={'context':{'version':1,'owner':owner,'vm_uuid':identifier,'parent_mac':macs[1]},
                 'private_host_key':(root/'host-key').read_text(),'public_host_key':public,
                 'authorized_key':(root/'management-key.pub').read_text(),'files':files}
        atomic(root/'known_hosts','[127.0.0.1]:2260 '+public)
        atomic(root/'autoinstall.yaml',autoinstall_template(*macs))
        atomic(root/'postinstall.sh',postinstall_template(payload))
        for argv in creation_commands(identifier,owner,root,macs):execute(argv)
        state['phase']='created';atomic(root/'state.json',json.dumps(state)+'\n')
        data=observed_info(Collector(),identifier)
        actual_owner=Collector().vbox('getextradata',identifier,OWNER_KEY).strip()
        validate_vm(vm_record(data,actual_owner[7:] if actual_owner.startswith('Value: ') else None),'target_host',identifier,owner,macs)
        for argv in install_commands(identifier,root,iso):execute(argv)
        data=observed_info(Collector(),identifier)
        actual_owner=Collector().vbox('getextradata',identifier,OWNER_KEY).strip()
        validate_vm(vm_record(data,actual_owner[7:] if actual_owner.startswith('Value: ') else None),'target_host',identifier,owner,macs)
        state['phase']='media-ready';atomic(root/'state.json',json.dumps(state)+'\n')
        return dict(summary,applied=True,uuid=identifier,phase='media-ready')


def validate_media_resume(state: dict,data: dict,root: Path,iso: Path) -> None:
    """Resume only a never-booted creation phase with its exact disk and empty DVD."""
    disk=str(root/'vm/pinpoint-defense-targets/pinpoint-defense-targets.vdi')
    if state.get('phase')!='created' or state.get('iso')!=str(iso):
        raise ValueError('Media resumption requires the exact created phase and original ISO')
    if data.get('SATA-0-0')!=disk or data.get('IDE-1-0')!='emptydrive':
        raise ValueError('Prepared storage differs from the original owned layout')
    for key,value in data.items():
        if re.fullmatch(r'(?:SATA|IDE)-[0-9]+-[0-9]+',key) and value not in {disk,'emptydrive','none'}:
            raise ValueError('Unexpected attached installation medium')


def resume_media(iso: Path,*,apply=False) -> dict:
    """Resume exact private creation state without recreating or starting any VM."""
    import os
    import sys
    import stat
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/'scripts'));sys.path.insert(0,str(repo/'demo'))
    import qa_control
    import vmlab_preflight
    from defense.controller import Collector,STATE_ROOT,OWNER_KEY,observed_info,vm_record
    from defense.preflight import read_private_json,validate_vm,validate_runtime
    from defense.node import atomic
    root=STATE_ROOT/'target-host'
    with qa_control.claim():
        state=read_private_json(root/'state.json')
        collector=Collector();data=observed_info(collector,state['uuid'])
        owner=collector.vbox('getextradata',state['uuid'],OWNER_KEY).strip()
        record=vm_record(data,owner[7:] if owner.startswith('Value: ') else None)
        validate_vm(record,'target_host',state['uuid'],state['owner'],state['macs'])
        if record['state']!='poweroff':raise ValueError('Media preparation requires the owned VM powered off')
        managers,processes=vmlab_preflight.inventory()
        validate_runtime(record,managers,[dict(p,pid=pid) for pid,p in processes.items()],vmlab_preflight.tcp_listeners([2260]),{})
        if processes:raise ValueError('Other VM processes prevent media resumption')
        validate_media_resume(state,data,root,iso)
        if iso.is_symlink() or not iso.is_file():raise ValueError('Original regular ISO is unavailable')
        detect_ubuntu(iso)
        result={'uuid':state['uuid'],'phase':state['phase'],'applied':False,'booted':False}
        if not apply:return result
        for name in ['login-password','autoinstall.yaml','postinstall.sh','host-key','management-key']:
            info=(root/name).lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o077:
                raise ValueError('Unsafe private installation input')
        os.umask(0o077)
        for argv in install_commands(state['uuid'],root,iso):
            with (root/'prepare.log').open('ab') as output:
                completed=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=output,timeout=120)
            if completed.returncode:raise ValueError('Private media preparation failed')
        data=observed_info(Collector(),state['uuid'])
        owner=Collector().vbox('getextradata',state['uuid'],OWNER_KEY).strip()
        validate_vm(vm_record(data,owner[7:] if owner.startswith('Value: ') else None),'target_host',state['uuid'],state['owner'],state['macs'])
        state['phase']='media-ready';atomic(root/'state.json',json.dumps(state)+'\n')
        return dict(result,phase='media-ready',applied=True)


def validate_install_boot(state,data,root,kvm_loaded,available,free_disk,required_disk,*,allow_ejected=False):
    """Require exact unbooted installer storage plus the one-VM capacity gate."""
    from defense.preflight import check_resources
    disk=str(root/'vm/pinpoint-defense-targets/pinpoint-defense-targets.vdi')
    media=str(root/'media/Unattended-aux-iso.viso')
    if state.get('phase')!='media-ready' or data.get('VMState')!='poweroff' or data.get('memory')!='2048':
        raise ValueError('Installer boot requires the exact powered-off media-ready VM')
    allowed_media={media,'emptydrive'} if allow_ejected else {media}
    if data.get('SATA-0-0')!=disk or data.get('IDE-1-0') not in allowed_media:
        raise ValueError('Installer disk/media pins changed')
    for key,value in data.items():
        if re.fullmatch(r'(?:SATA|IDE)-[0-9]+-[0-9]+',key) and value not in {disk,media,'none','emptydrive'}:
            raise ValueError('Unexpected installation storage')
    if kvm_loaded:raise ValueError('KVM still holds hardware virtualization')
    check_resources(available,free_disk,[2048],required_disk)


def validate_installed_boot(state,data,root,kvm_loaded,available,free_disk,required_disk):
    """Require the prior installation phase before the first disk-only verification boot."""
    if state.get('phase')!='installing':
        raise ValueError('Disk-only verification requires a prior installer run')
    validate_install_boot(dict(state,phase='media-ready'),data,root,kvm_loaded,available,free_disk,required_disk,allow_ejected=True)


def start_install(*,apply=False,installed=False):
    """Boot the saved target-host for installation or its first disk-only verification."""
    import os
    import shutil
    import sys
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/'scripts'));sys.path.insert(0,str(repo/'demo'))
    import qa_control
    import vmlab_preflight
    from defense.controller import Collector,STATE_ROOT,WINDOWS_ROOT,OWNER_KEY,observed_info,vm_record,network_inventory,allocated_mib
    from defense.preflight import read_private_json,validate_vm,validate_runtime,reject_overlaps,reject_virtualbox_dhcp
    from defense.node import atomic
    root=STATE_ROOT/'target-host'
    with qa_control.claim():
        state=read_private_json(root/'state.json');collector=Collector()
        reject_overlaps(network_inventory(collector));reject_virtualbox_dhcp(collector.vbox('list','dhcpservers'))
        for line in collector.vbox('list','vms').splitlines():
            match=re.search(r'\{([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})\}$',line)
            if not match:raise ValueError('Incomplete VM inventory')
            info=observed_info(collector,match[1])
            if info.get('VMState')!='poweroff':raise ValueError('Other VMs must remain off during installation')
            if match[1]!=state['uuid'] and info.get('name')!='pinpoint-defense-win01' and any(info.get(f'intnet{i}')=='pinpoint-defense' and info.get(f'nic{i}')=='intnet' for i in range(1,9)):
                raise ValueError('Foreign VM on the defense segment')
        data=observed_info(collector,state['uuid'])
        owner=collector.vbox('getextradata',state['uuid'],OWNER_KEY).strip()
        record=vm_record(data,owner[7:] if owner.startswith('Value: ') else None)
        validate_vm(record,'target_host',state['uuid'],state['owner'],state['macs'])
        managers,processes=vmlab_preflight.inventory()
        validate_runtime(record,managers,[dict(p,pid=pid) for pid,p in processes.items()],vmlab_preflight.tcp_listeners([2260]),{})
        if processes:raise ValueError('Other running VM processes prevent installation boot')
        memory=re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)
        if not memory:raise ValueError('Missing host memory inventory')
        required=max(40960-allocated_mib(WINDOWS_ROOT),0)+max(16384-allocated_mib(root/'vm'),0)+8192+2048+1024+10240
        available=int(memory[1])//1024;free=shutil.disk_usage(Path.home()).free//1048576
        gate=validate_installed_boot if installed else validate_install_boot
        gate(state,data,root,Path('/sys/module/kvm').exists(),available,free,required)
        result={'uuid':state['uuid'],'phase':state['phase'],'available_mib':available,'free_disk_mib':free,'applied':False}
        if not apply:return result
        os.umask(0o077)
        state['phase']='starting-installed' if installed else 'starting-install';atomic(root/'state.json',json.dumps(state)+'\n')
        try:
            commands=[]
            if installed:
                commands.append(['VBoxManage','storageattach',state['uuid'],'--storagectl','IDE','--port','1','--device','0','--type','dvddrive','--medium','emptydrive'])
            commands.extend([['VBoxManage','modifyvm',state['uuid'],'--boot1','disk','--boot2','none' if installed else 'dvd','--boot3','none','--boot4','none'],['VBoxManage','startvm',state['uuid'],'--type','headless']])
            for argv in commands:
                with (root/'install-start.log').open('ab') as output:
                    completed=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=output,timeout=45)
                if completed.returncode:raise ValueError('Owned installer start failed')
        except Exception:
            state['phase']='start-needs-inspection';atomic(root/'state.json',json.dumps(state)+'\n')
            raise
        state['phase']='installed-boot-unverified' if installed else 'installing';atomic(root/'state.json',json.dumps(state)+'\n')
        return dict(result,phase=state['phase'],applied=True)


def validate_disk_chain(root,attached,chain):
    """Require a bounded private differencing chain ending at the original owned VDI."""
    vmroot=root/'vm/pinpoint-defense-targets'
    base=str(vmroot/'pinpoint-defense-targets.vdi')
    if not chain or len(chain)>8 or chain[0].get('Location')!=attached:raise ValueError('Invalid attached disk chain')
    identifiers=[]
    for i,record in enumerate(chain):
        path=Path(record.get('Location',''));identifier=record.get('UUID','')
        if not path.is_absolute() or '..' in path.parts or not path.is_relative_to(vmroot) or record.get('State')!='created' or not re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',identifier):
            raise ValueError('Disk ancestry escaped the private owned VM')
        if i and chain[i-1].get('Parent UUID')!=identifier:raise ValueError('Disk parent identity mismatch')
        identifiers.append(identifier)
    if len(set(identifiers))!=len(identifiers) or chain[-1].get('Location')!=base or chain[-1].get('Parent UUID')!='base':
        raise ValueError('Disk chain does not reach the original owned disk')
    return attached


def observed_owned_disk(collector,root,attached):
    """Resolve snapshot media through VBox's ancestry, checking every private regular file."""
    import os
    import stat
    chain=[];current=attached
    for _ in range(8):
        raw=collector.vbox('showmediuminfo','disk',current)
        record={}
        for key in ['UUID','Parent UUID','State','Location']:
            values=re.findall(r'^'+re.escape(key)+r':\s*(.*)$',raw,re.M)
            if len(values)!=1:raise ValueError('Disk ancestry metadata missing or duplicated')
            record[key]=values[0].strip()
        path=Path(record['Location']);info=path.lstat()
        if path.resolve()!=path or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o022:
            raise ValueError('Unsafe owned disk path or permissions')
        chain.append(record)
        if record['Parent UUID']=='base':return validate_disk_chain(root,attached,chain)
        if not re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',record['Parent UUID']):
            raise ValueError('Invalid parent disk UUID')
        current=record['Parent UUID']
    raise ValueError('Disk ancestry is too deep or cyclic')


def maintenance_boot_plan(state,data,root):
    """Boot stock media for an owned installed guest; no unattended or disk creation path."""
    identifier=state.get('uuid','');iso=state.get('iso','')
    install_commands(identifier,root,Path(iso))
    if state.get('phase')!='installed-needs-forwarding-guard' or data.get('VMState')!='poweroff' or data.get('memory')!='2048':
        raise ValueError('Maintenance requires the exact installed powered-off state')
    if data.get('SATA-0-0')!=state.get('disk_path',str(root/'vm/pinpoint-defense-targets/pinpoint-defense-targets.vdi')):
        raise ValueError('Installed maintenance disk changed')
    for key,value in data.items():
        if re.fullmatch(r'IDE-[0-9]+-[0-9]+',key) and value not in {'none','emptydrive'}:
            raise ValueError('Detach private/setup media before live maintenance')
    return [['VBoxManage','storageattach',identifier,'--storagectl','IDE','--port','0','--device','0','--type','dvddrive','--medium',iso],
            ['VBoxManage','modifyvm',identifier,'--boot1','dvd','--boot2','disk','--boot3','none','--boot4','none'],
            ['VBoxManage','startvm',identifier,'--type','headless']]


def start_maintenance(*,apply=False):
    """Preview or boot stock-ISO maintenance after exact host ownership and one-VM gates."""
    import os
    import shutil
    import sys
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/'scripts'));sys.path.insert(0,str(repo/'demo'))
    import qa_control
    import vmlab_preflight
    from defense.controller import Collector,STATE_ROOT,WINDOWS_ROOT,OWNER_KEY,observed_info,vm_record,network_inventory,allocated_mib
    from defense.catalog import load_catalog
    from defense.preflight import read_private_json,validate_vm,validate_runtime,reject_overlaps,reject_virtualbox_dhcp,check_resources,validate_vm_macs
    from defense.node import atomic
    root=STATE_ROOT/'target-host'
    with qa_control.claim():
        state=read_private_json(root/'state.json');collector=Collector()
        reject_overlaps(network_inventory(collector));reject_virtualbox_dhcp(collector.vbox('list','dhcpservers'))
        records=[]
        for line in collector.vbox('list','vms').splitlines():
            match=re.search(r'\{([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})\}$',line)
            if not match:raise ValueError('Incomplete VM inventory')
            info=observed_info(collector,match[1]);record=vm_record(info,None);records.append(record)
            if record['state']!='poweroff':raise ValueError('All VMs must be off for stock-ISO maintenance')
            if match[1]!=state['uuid'] and any(n['network']=='pinpoint-defense' for n in record['nics']):
                windows=read_private_json(WINDOWS_ROOT/'state.json')
                owner=collector.vbox('getextradata',match[1],OWNER_KEY).strip()
                record['owner']=owner[7:] if owner.startswith('Value: ') else None
                validate_vm(record,'windows',windows['uuid'],windows['owner'],['02:77:01:00:00:02'])
        validate_vm_macs(load_catalog(),records)
        data=observed_info(collector,state['uuid']);owner=collector.vbox('getextradata',state['uuid'],OWNER_KEY).strip()
        record=vm_record(data,owner[7:] if owner.startswith('Value: ') else None)
        validate_vm(record,'target_host',state['uuid'],state['owner'],state['macs'])
        managers,processes=vmlab_preflight.inventory()
        validate_runtime(record,managers,[dict(p,pid=pid) for pid,p in processes.items()],vmlab_preflight.tcp_listeners([2260]),{})
        if processes:raise ValueError('Unexpected VM processes prevent maintenance')
        iso=Path(state['iso'])
        if iso.is_symlink() or not iso.is_file():raise ValueError('Original stock ISO unavailable')
        detect_ubuntu(iso)
        state['disk_path']=observed_owned_disk(collector,root,data.get('SATA-0-0',''))
        commands=maintenance_boot_plan(state,data,root)
        available=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)[1])//1024
        free=shutil.disk_usage(Path.home()).free//1048576
        required=max(40960-allocated_mib(WINDOWS_ROOT),0)+max(16384-allocated_mib(root/'vm'),0)+8192+2048+1024+10240
        check_resources(available,free,[2048],required)
        result={'uuid':state['uuid'],'available_mib':available,'free_disk_mib':free,'required_disk_mib':required,
                'kvm_release_required':Path('/sys/module/kvm').exists(),'applied':False,'stock_iso_only':True}
        if not apply:return result
        if result['kvm_release_required']:raise ValueError('KVM still holds hardware virtualization')
        os.umask(0o077)
        state['phase']='maintenance-starting';atomic(root/'state.json',json.dumps(state)+'\n')
        for argv in commands:
            with (root/'maintenance-start.log').open('ab') as output:
                completed=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=output,timeout=45)
            if completed.returncode:raise ValueError('Owned maintenance start failed; inspect private state')
        state['phase']='maintenance-live-boot';atomic(root/'state.json',json.dumps(state)+'\n')
        return dict(result,applied=True)


def main(argv=None):
    """Prepare installer media only; starting and transitioning existing VMs is separate."""
    import argparse
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--resume-media',action='store_true')
    parser.add_argument('--start-install',action='store_true')
    parser.add_argument('--boot-installed',action='store_true')
    parser.add_argument('--maintenance-boot',action='store_true')
    args=parser.parse_args(argv)
    try:
        if sum([args.resume_media,args.start_install,args.boot_installed,args.maintenance_boot])>1:raise ValueError('Choose one preparation action')
        operation=resume_media if args.resume_media else prepare
        result=start_maintenance(apply=args.apply) if args.maintenance_boot else start_install(apply=args.apply,installed=args.boot_installed) if args.start_install or args.boot_installed else operation(args.iso,apply=args.apply)
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError):
        print('Target-host preparation refused or failed; inspect host gates and private state.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
