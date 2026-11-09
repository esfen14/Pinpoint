"""Create the two VMs the demo keeps: the Pinpoint appliance and the Windows NCPA test VM.

`python3 demo/appliance/create_vms.py [--apply] [--appliance-iso ISO] [--windows-iso ISO]`
prints the VBoxManage plan and changes nothing without --apply. Existing VMs are
never touched. Both VMs use the host-only network vboxnet1; the appliance also has
NAT with the web UI forwarded to 127.0.0.1:18080. Installing the application on the
appliance is `scripts/vmlab`; the Windows NCPA agent is installed inside Windows
(demo/appliance/WINDOWS_READY.md), so those steps stay manual.
"""
import argparse
from pathlib import Path
import subprocess
import sys

PARENT='vboxnet1'
APPLIANCE_VM='Pinpoint-Final'
WINDOWS_VM='pinpoint-defense-win01'
WINDOWS_MAC='02:77:01:00:00:02'
WEB_PORT=18080
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


def windows_install_command(name,iso,password_file):
    """Unattended Windows install; the password comes from a private file, never an argument."""
    return ['VBoxManage','unattended','install',name,'--iso='+str(iso),'--user=presenter',
            '--user-password-file='+str(password_file),'--install-additions']


def iso_attach_command(name,iso):
    return ['VBoxManage','storageattach',name,'--storagectl','SATA','--port','1','--device','0','--type','dvddrive','--medium',str(iso)]


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


def main(argv=None,runner=default_runner,out=sys.stdout,err=sys.stderr):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--appliance-iso',type=Path)
    parser.add_argument('--windows-iso',type=Path)
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
    plans=[(APPLIANCE_VM,appliance_commands(APPLIANCE_VM,folder/APPLIANCE_VM/(APPLIANCE_VM+'.vdi')),args.appliance_iso,None),
           (WINDOWS_VM,windows_commands(WINDOWS_VM,folder/WINDOWS_VM/(WINDOWS_VM+'.vdi')),args.windows_iso,windows_install_command)]
    try:
        for name,commands,iso,installer in plans:
            exists=vm_exists(runner,name)
            print('%s %s'%(name,'exists: left untouched' if exists else 'will be created'),file=out)
            if exists:
                continue
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
                    runner(installer(name,iso,args.windows_password_file))
    except (OSError,ValueError,subprocess.SubprocessError):
        print('VM creation stopped; re-run is safe, existing VMs are kept.',file=err)
        return 1
    print('\nStill manual: install the application on the appliance (scripts/vmlab), set its adapter 2 address 10.77.1.1/27,'
          ' install NCPA in Windows and take the ncpa-ready snapshot (demo/appliance/README.md).',file=out)
    if not args.apply:
        print('Nothing was changed. Add --apply to create the missing VMs.',file=out)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
