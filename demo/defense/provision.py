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
    from defense.controller import Collector,STATE_ROOT,WINDOWS_ROOT,network_inventory,allocated_mib,parse_info,vm_record,OWNER_KEY
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
            record=vm_record(parse_info(collector.vbox('showvminfo',match[1],'--machinereadable')),None)
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
               ['__init__.py','catalog.py','compose.py','manifest.json','preflight.py','node.py','guest.py','Dockerfile','Dockerfile.dockerignore']}
        public=(root/'host-key.pub').read_text()
        payload={'context':{'version':1,'owner':owner,'vm_uuid':identifier,'parent_mac':macs[1]},
                 'private_host_key':(root/'host-key').read_text(),'public_host_key':public,
                 'authorized_key':(root/'management-key.pub').read_text(),'files':files}
        atomic(root/'known_hosts','[127.0.0.1]:2260 '+public)
        atomic(root/'autoinstall.yaml',autoinstall_template(*macs))
        atomic(root/'postinstall.sh',postinstall_template(payload))
        for argv in creation_commands(identifier,owner,root,macs):execute(argv)
        state['phase']='created';atomic(root/'state.json',json.dumps(state)+'\n')
        data=parse_info(Collector().vbox('showvminfo',identifier,'--machinereadable'))
        actual_owner=Collector().vbox('getextradata',identifier,OWNER_KEY).strip()
        validate_vm(vm_record(data,actual_owner[7:] if actual_owner.startswith('Value: ') else None),'target_host',identifier,owner,macs)
        for argv in install_commands(identifier,root,iso):execute(argv)
        data=parse_info(Collector().vbox('showvminfo',identifier,'--machinereadable'))
        actual_owner=Collector().vbox('getextradata',identifier,OWNER_KEY).strip()
        validate_vm(vm_record(data,actual_owner[7:] if actual_owner.startswith('Value: ') else None),'target_host',identifier,owner,macs)
        state['phase']='media-ready';atomic(root/'state.json',json.dumps(state)+'\n')
        return dict(summary,applied=True,uuid=identifier,phase='media-ready')


def main(argv=None):
    """Prepare installer media only; starting and transitioning existing VMs is separate."""
    import argparse
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(argv)
    try:
        print(json.dumps(prepare(args.iso,apply=args.apply),indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError):
        print('Target-host preparation refused or failed; inspect host gates and private state.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
