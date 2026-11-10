"""Create the two VMs the demo keeps: the Pinpoint appliance and the Windows NCPA test VM.

`python3 demo/appliance/create_vms.py [--apply] [--appliance-iso ISO | --download-appliance-iso]
[--windows-iso ISO | --download-windows-iso]` prints the VBoxManage plan and changes nothing without --apply. Existing VMs are
never touched. Both VMs use the host-only network vboxnet1; the appliance also has
NAT with the web UI forwarded to 127.0.0.1:18080. Installing the application on the
appliance is `scripts/vmlab`; the Windows NCPA agent is installed inside Windows
(demo/appliance/WINDOWS_READY.md), so those steps stay manual.
"""
import argparse
import os
import re
from pathlib import Path
import subprocess
import sys

PARENT='vboxnet1'
APPLIANCE_VM='Pinpoint-Final'
WINDOWS_VM='pinpoint-defense-win01'
WINDOWS_MAC='02:77:01:00:00:02'
WEB_PORT=18080
# The appliance ISO is the same file `scripts/vmlab iso` uses (VMLAB_ISO), so one download serves both.
APPLIANCE_ISO_URL='https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso'
APPLIANCE_ISO_DEFAULT=Path.home()/'Downloads/ubuntu-22.04.5-live-server-amd64.iso'
# Microsoft's evaluation download of Windows 10 Enterprise 22H2 (about 5.5 GB, 90-day evaluation).
WINDOWS_ISO_URL='https://go.microsoft.com/fwlink/p/?LinkID=2208844&clcid=0x409&culture=en-us&country=US'
WINDOWS_ISO_DEFAULT=Path.home()/'Downloads/Windows10-Enterprise-Eval-22H2-x64.iso'
# VirtualBox's Windows answer file has a ProductKey element; with an empty key, evaluation media stop
# with "Windows cannot find the Microsoft Software License Terms", and a key of the wrong edition
# leaves "No images are available". Evaluation media need no key, so we use VirtualBox's own template
# with that element removed.
VBOX_TEMPLATE=Path('/usr/share/virtualbox/UnattendedTemplates/win_nt6_unattended.xml')
KEYLESS_TEMPLATE=Path.home()/'.cache/pinpoint-demo/win_nt6_unattended_no_key.xml'
DEFAULT_STATE=Path.home()/'.local/share/pinpoint-defense/windows-home'


def appliance_commands(name,disk):
    return [['VBoxManage','createvm','--name',name,'--ostype','Ubuntu_64','--register'],
            ['VBoxManage','modifyvm',name,'--memory','4096','--cpus','4','--audio-driver=none','--graphicscontroller=vmsvga',
             '--rtc-use-utc=on','--nic1=nat','--nic2=hostonly','--host-only-adapter2='+PARENT],
            ['VBoxManage','modifyvm',name,'--nat-pf1=web,tcp,127.0.0.1,%d,,80'%WEB_PORT],
            ['VBoxManage','createmedium','disk','--filename',str(disk),'--size','40960'],
            ['VBoxManage','storagectl',name,'--name','SATA','--add','sata','--controller','IntelAhci'],
            ['VBoxManage','storageattach',name,'--storagectl','SATA','--port','0','--device','0','--type','hdd','--medium',str(disk)]]


def windows_commands(name,disk):
    mac=WINDOWS_MAC.replace(':','')
    return [['VBoxManage','createvm','--name',name,'--ostype','Windows10_64','--register'],
            ['VBoxManage','modifyvm',name,'--memory','3072','--cpus','2','--audio-driver=none','--graphicscontroller=vboxsvga',
             '--nic1=hostonly','--host-only-adapter1='+PARENT,'--mac-address1='+mac],
            ['VBoxManage','createmedium','disk','--filename',str(disk),'--size','40960'],
            ['VBoxManage','storagectl',name,'--name','SATA','--add','sata','--controller','IntelAhci'],
            ['VBoxManage','storageattach',name,'--storagectl','SATA','--port','0','--device','0','--type','hdd','--medium',str(disk)]]


def write_keyless_template(source=VBOX_TEMPLATE,target=KEYLESS_TEMPLATE):
    """VirtualBox's Windows answer-file template without the ProductKey element (no secrets in it)."""
    text=source.read_text()
    stripped=re.sub(r'[ \t]*<ProductKey>.*?</ProductKey>[ \t]*\n','',text,flags=re.DOTALL)
    if stripped==text:
        raise ValueError('The VirtualBox answer-file template has no ProductKey element to remove: %s'%source)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(stripped)


def windows_install_command(name,iso,password_file,template=KEYLESS_TEMPLATE):
    """Unattended Windows install; the password comes from a private file, never an argument."""
    return ['VBoxManage','unattended','install',name,'--iso='+str(iso),'--user=presenter',
            '--user-password-file='+str(password_file),'--image-index=1','--script-template='+str(template),'--install-additions']


def iso_attach_command(name,iso):
    return ['VBoxManage','storageattach',name,'--storagectl','SATA','--port','1','--device','0','--type','dvddrive','--medium',str(iso)]


def appliance_iso_default():
    configured=os.environ.get('VMLAB_ISO')
    if configured:
        return Path(configured)
    return APPLIANCE_ISO_DEFAULT


def default_downloader(url,target):
    """Resumable download to target (via a .part file); an existing file is kept."""
    if target.exists():
        return
    target.parent.mkdir(parents=True,exist_ok=True)
    part=target.with_name(target.name+'.part')
    result=subprocess.run(['curl','-fL','-C','-','-o',str(part),url])
    if result.returncode:
        raise ValueError('Download failed; re-run to resume')
    part.rename(target)


def resolve_iso(given,download,default_path,url,label,downloader,apply,out):
    """The ISO to use: a path the user gave, or the default path after an optional download."""
    if given and download:
        raise ValueError('Give either a %s ISO path or the download option, not both'%label)
    if given:
        if apply and not given.exists():
            raise ValueError('%s ISO not found: %s'%(label,given))
        return given
    if not download:
        return None
    if default_path.exists():
        print('%s ISO already present: %s'%(label,default_path),file=out)
    else:
        print('%s ISO will be downloaded from %s to %s'%(label,url,default_path),file=out)
        if apply:
            downloader(url,default_path)
            print('Downloaded. sha256:',file=out)
            digest=subprocess.run(['sha256sum',str(default_path)],capture_output=True,text=True).stdout.strip()
            print('  '+digest,file=out)
    return default_path


def default_runner(argv):
    result=subprocess.run(argv,capture_output=True,text=True,timeout=600)
    if result.returncode:
        raise ValueError('VBoxManage failed')
    return result.stdout


def vm_exists(runner,name):
    try:
        runner(['VBoxManage','showvminfo',name,'--machinereadable'])
        return True
    except (OSError,ValueError,subprocess.SubprocessError):
        return False


def machine_folder(runner):
    for line in runner(['VBoxManage','list','systemproperties']).splitlines():
        if line.startswith('Default machine folder:'):
            return Path(line.split(':',1)[1].strip())
    raise ValueError('Default machine folder unknown')


def main(argv=None,runner=default_runner,out=sys.stdout,err=sys.stderr,downloader=default_downloader,template_writer=write_keyless_template):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--appliance-iso',type=Path)
    parser.add_argument('--windows-iso',type=Path)
    parser.add_argument('--download-appliance-iso',action='store_true',help='download Ubuntu 22.04.5 live-server (about 2 GB) unless it is already present')
    parser.add_argument('--download-windows-iso',action='store_true',help='download the Windows 10 Enterprise evaluation ISO (about 5.5 GB) unless it is already present')
    parser.add_argument('--windows-password-file',type=Path,default=DEFAULT_STATE/'login-password')
    try:
        args=parser.parse_args(argv)
    except SystemExit:
        return 2
    try:
        folder=machine_folder(runner)
    except (OSError,ValueError,subprocess.SubprocessError):
        folder=Path('<VirtualBox machine folder>')
        if args.apply:
            print('VBoxManage is not available.',file=err)
            return 1
    plans=[(APPLIANCE_VM,appliance_commands(APPLIANCE_VM,folder/APPLIANCE_VM/(APPLIANCE_VM+'.vdi')),(args.appliance_iso,args.download_appliance_iso,appliance_iso_default(),APPLIANCE_ISO_URL,'Appliance'),None),
           (WINDOWS_VM,windows_commands(WINDOWS_VM,folder/WINDOWS_VM/(WINDOWS_VM+'.vdi')),(args.windows_iso,args.download_windows_iso,WINDOWS_ISO_DEFAULT,WINDOWS_ISO_URL,'Windows'),windows_install_command)]
    try:
        for name,commands,iso_choice,installer in plans:
            exists=vm_exists(runner,name)
            print('%s %s'%(name,'exists: left untouched' if exists else 'will be created'),file=out)
            if exists:
                continue
            iso=resolve_iso(*iso_choice,downloader,args.apply,out)
            for command in commands:
                print('  '+' '.join(command),file=out)
            if iso:
                print('  '+' '.join(iso_attach_command(name,iso)),file=out)
            if installer and iso:
                print('  '+' '.join(installer(name,iso,args.windows_password_file)),file=out)
            if args.apply:
                for command in commands:
                    runner(command)
                if iso:
                    runner(iso_attach_command(name,iso))
                if installer and iso:
                    template_writer()
                    runner(installer(name,iso,args.windows_password_file))
    except (OSError,ValueError,subprocess.SubprocessError) as problem:
        print(problem if str(problem) else 'VM creation stopped',file=err)
        print('VM creation stopped; re-run is safe, existing VMs are kept.',file=err)
        return 1
    print('\nStill manual: install the application on the appliance (scripts/vmlab), set its adapter 2 address 10.77.1.1/27,'
          ' install NCPA in Windows and take the ncpa-ready snapshot (demo/appliance/README.md).',file=out)
    if not args.apply:
        print('Nothing was changed. Add --apply to create the missing VMs.',file=out)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
