"""Install NCPA in the Windows test VM and (optionally) register it in Pinpoint.

`python3 demo/appliance/install_ncpa_windows.py --installer NCPA.exe --sha256 HASH --token-file FILE
[--windows-password-file FILE] [--port 5693] [--apply]
[--register --pinpoint-email EMAIL --pinpoint-password-file FILE [--pinpoint-url URL]]`

Without --apply it prints the plan and changes nothing. With --apply it checks the
installer's SHA-256 on this machine, then uses `VBoxManage guestcontrol` to copy and
silently install it, write the agent token and port into NCPA's configuration, set the
Windows address 10.77.1.3/27, open the firewall to the appliance 10.77.1.1 only and
confirm the agent answers on its port. Every step can be re-run. The VM must already be
running (Windows installed, Guest Additions present).

Secrets are never arguments: the Windows password, the NCPA token and the Pinpoint
password are read from files. The token reaches the guest as a copied file, not on a
command line. Windows licensing and the first Windows install are out of scope
(demo/demo create-vms).
"""
import argparse
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

WINDOWS_VM='pinpoint-defense-win01'
WINDOWS_USER='presenter'
WINDOWS_IP='10.77.1.3'
WINDOWS_PREFIX=27
APPLIANCE_IP='10.77.1.1'
NCPA_PORT=5693
DEFAULT_STATE=Path.home()/'.local/share/pinpoint-defense/windows-home'
DEFAULT_PINPOINT_URL='http://127.0.0.1:18080'
GUEST_TEMP='C:\\Windows\\Temp'
GUEST_CONFIG_DIR='C:\\Program Files\\Nagios\\NCPA\\etc\\ncpa.cfg.d'
GUEST_SNIPPET=GUEST_CONFIG_DIR+'\\pinpoint.cfg'
POWERSHELL='C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
FIREWALL_RULE='Pinpoint NCPA'


def validate_installer_name(name):
    """The installer file name ends up inside PowerShell text, so only plain names are accepted."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.exe',name):
        raise ValueError('The installer file name must be letters, digits, dot, dash or underscore and end in .exe: %s'%name)
    return name


def validate_sha256(value):
    if not re.fullmatch(r'[0-9a-fA-F]{64}',value or ''):
        raise ValueError('--sha256 must be 64 hexadecimal characters')
    return value.lower()


def validate_port(port):
    if not isinstance(port,int) or not 1<=port<=65535:
        raise ValueError('The port must be 1 to 65535')
    return port


def validate_token(token):
    """Pinpoint's registration needs 32 hexadecimal characters; the same token is set in NCPA."""
    if not re.fullmatch(r'[0-9a-fA-F]{32}',token or ''):
        raise ValueError('The NCPA token file must hold 32 hexadecimal characters (for example: python3 -c "import secrets;print(secrets.token_hex(16))")')
    return token


def read_secret_file(path,label):
    try:
        return Path(path).read_text().strip()
    except OSError:
        raise ValueError('%s file cannot be read: %s'%(label,path))


def sha256_of(path):
    digest=hashlib.sha256()
    with open(path,'rb') as handle:
        for block in iter(lambda:handle.read(1<<20),b''):
            digest.update(block)
    return digest.hexdigest()


def config_snippet(token,port):
    """NCPA configuration read from ncpa.cfg.d: the API token and the listener port."""
    return '[api]\ncommunity_string = %s\n\n[listener]\nport = %d\n'%(token,port)


def guest_auth(password_file):
    return ['--username',WINDOWS_USER,'--passwordfile',str(password_file)]


def guest_run(vm,password_file,script):
    """Run one PowerShell script in the guest; the password comes from a file."""
    return ['VBoxManage','guestcontrol',vm,'run']+guest_auth(password_file)+['--exe',POWERSHELL,'--','powershell.exe','-NoProfile','-NonInteractive','-Command',script]


def guest_copy(vm,password_file,source,target_directory):
    return ['VBoxManage','guestcontrol',vm,'copyto']+guest_auth(password_file)+['--target-directory',target_directory,str(source)]


def hash_script(name,sha256):
    path=GUEST_TEMP+'\\'+name
    return ("$h=(Get-FileHash -Algorithm SHA256 -Path '%s').Hash.ToLower(); "
            "if($h -ne '%s'){throw 'Installer hash in the guest does not match'}; 'Installer hash verified in the guest'")%(path,sha256)


def install_script(name):
    """Silent install, skipped when the ncpa service already exists, so a re-run is safe."""
    path=GUEST_TEMP+'\\'+name
    return ("if(-not (Get-Service ncpa -ErrorAction SilentlyContinue)){"
            "Start-Process -Wait -FilePath '%s' -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-'}; "
            "if(-not (Get-Service ncpa -ErrorAction SilentlyContinue)){throw 'NCPA service missing after install'}; "
            "New-Item -Force -ItemType Directory -Path '%s' | Out-Null")%(path,GUEST_CONFIG_DIR)


def network_script():
    """Static lab address on the only active adapter; no default route is configured."""
    return ("$a=Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1; "
            "if(-not $a){throw 'No active network adapter'}; "
            "Set-NetIPInterface -InterfaceIndex $a.ifIndex -Dhcp Disabled; "
            "Get-NetIPAddress -InterfaceIndex $a.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false; "
            "New-NetIPAddress -InterfaceIndex $a.ifIndex -IPAddress %s -PrefixLength %d | Out-Null; "
            "'Address set to %s/%d'")%(WINDOWS_IP,WINDOWS_PREFIX,WINDOWS_IP,WINDOWS_PREFIX)


def firewall_script(port):
    """Replace the installer's own NCPA rules with one that admits only the appliance."""
    return ("Get-NetFirewallRule -DisplayName 'NCPA*' -ErrorAction SilentlyContinue | Remove-NetFirewallRule; "
            "Get-NetFirewallRule -DisplayName '%s' -ErrorAction SilentlyContinue | Remove-NetFirewallRule; "
            "New-NetFirewallRule -DisplayName '%s' -Direction Inbound -Protocol TCP -LocalPort %d -RemoteAddress %s -Action Allow -Profile Domain,Private,Public | Out-Null; "
            "'Firewall admits %s only on port %d'")%(FIREWALL_RULE,FIREWALL_RULE,port,APPLIANCE_IP,APPLIANCE_IP,port)


def service_script():
    return "Set-Service ncpa -StartupType Automatic; Restart-Service ncpa; 'ncpa service restarted'"


def verify_script(port):
    """Authenticated check from inside the guest; the token is read from NCPA's file, never typed."""
    return ("$t=(Select-String -Path '%s' -Pattern '^community_string\\s*=\\s*(\\S+)').Matches[0].Groups[1].Value; "
            "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true}; "
            "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; "
            "$code=0; for($i=0;$i -lt 6 -and $code -ne 200;$i++){try{$code=(Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri ('https://127.0.0.1:%d/api/cpu/percent?token='+$t)).StatusCode}catch{Start-Sleep 5}}; "
            "if($code -ne 200){throw 'NCPA did not answer on port %d'}; 'NCPA answers on port %d'")%(GUEST_SNIPPET,port,port,port)


def cleanup_script(name):
    return "Remove-Item -Force -ErrorAction SilentlyContinue '%s'; 'Installer removed from the guest'"%(GUEST_TEMP+'\\'+name)


def default_runner(argv):
    result=subprocess.run(argv,capture_output=True,text=True,timeout=1800)
    if result.returncode:
        raise ValueError('%s failed: %s'%(' '.join(argv[:3]),(result.stderr or result.stdout).strip()[-300:]))
    return result.stdout


def default_http(method,url,body=None,_opener=[]):
    """JSON request with a session cookie kept for the whole run."""
    if not _opener:
        _opener.append(urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())))
    data=json.dumps(body).encode() if body is not None else None
    request=urllib.request.Request(url,data=data,method=method,headers={'Content-Type':'application/json'})
    try:
        with _opener[0].open(request,timeout=60) as response:
            return response.status,json.loads(response.read() or b'{}')
    except urllib.error.HTTPError as problem:
        try:
            return problem.code,json.loads(problem.read() or b'{}')
        except ValueError:
            return problem.code,{}


def register_in_pinpoint(http,base_url,email,password,token,port,out):
    """Sign in, find the device at the Windows address and register its agent. 409 (already registered) is success."""
    base=base_url.rstrip('/')
    status,_=http('POST',base+'/api/user/login',{'email':email,'password':password})
    if status!=200:
        raise ValueError('Pinpoint sign-in failed (HTTP %d); check the URL, e-mail and password file'%status)
    try:
        status,body=http('GET',base+'/api/system/deployment/ncpa/register-candidates')
        if status!=200:
            raise ValueError('Pinpoint register-candidates failed (HTTP %d)'%status)
        device_id=None
        for device in body.get('data',{}).get('devices',[]):
            if device.get('ip_address')==WINDOWS_IP:
                device_id=device.get('device_id')
        if device_id is None:
            raise ValueError('Pinpoint has no device at %s to register. Run Rescan Network in Pinpoint, then re-run this command'%WINDOWS_IP)
        status,body=http('POST','%s/api/system/deployment/ncpa/%d/register'%(base,device_id),{'token':token,'port':port})
        if status==409:
            print('Pinpoint already has an agent registered for %s'%WINDOWS_IP,file=out)
        elif status==200:
            print('Registered the NCPA agent for %s in Pinpoint'%WINDOWS_IP,file=out)
        else:
            raise ValueError('Pinpoint registration failed (HTTP %d): %s'%(status,body.get('message','no message')))
    finally:
        http('POST',base+'/api/user/logout')


def show(command,out):
    print('  '+' '.join(command),file=out)


def main(argv=None,runner=default_runner,out=sys.stdout,err=sys.stderr,http=default_http):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--vm',default=WINDOWS_VM)
    parser.add_argument('--installer',type=Path,required=True,help='the NCPA Windows installer (.exe) you downloaded')
    parser.add_argument('--sha256',help='expected SHA-256 of the installer (required with --apply)')
    parser.add_argument('--token-file',type=Path,required=True,help='file holding the 32-hex-character NCPA token')
    parser.add_argument('--port',type=int,default=NCPA_PORT)
    parser.add_argument('--windows-password-file',type=Path,default=DEFAULT_STATE/'login-password')
    parser.add_argument('--register',action='store_true',help='after installing, register the agent in Pinpoint through its API')
    parser.add_argument('--pinpoint-url',default=DEFAULT_PINPOINT_URL)
    parser.add_argument('--pinpoint-email')
    parser.add_argument('--pinpoint-password-file',type=Path)
    try:
        args=parser.parse_args(argv)
    except SystemExit:
        return 2
    try:
        validate_port(args.port)
        name=validate_installer_name(args.installer.name)
        if args.apply and not args.sha256:
            raise ValueError('--sha256 is required with --apply; take it from the NCPA download page or your own record')
        expected=validate_sha256(args.sha256) if args.sha256 else '<sha256 you give>'
        if args.register and not (args.pinpoint_email and args.pinpoint_password_file):
            raise ValueError('--register needs --pinpoint-email and --pinpoint-password-file')
        token=None
        if args.apply or args.token_file.exists():
            token=validate_token(read_secret_file(args.token_file,'NCPA token'))
        if args.apply:
            for path,label in ((args.installer,'Installer'),(args.windows_password_file,'Windows password')):
                if not Path(path).is_file():
                    raise ValueError('%s file not found: %s'%(label,path))
    except ValueError as problem:
        print(problem,file=err)
        return 2
    try:
        actual=sha256_of(args.installer) if args.installer.is_file() else None
        if args.apply and actual!=expected:
            raise ValueError('Installer SHA-256 does not match: expected %s, got %s. Nothing was changed.'%(expected,actual))
        state=None
        try:
            for line in runner(['VBoxManage','showvminfo',args.vm,'--machinereadable']).splitlines():
                if line.startswith('VMState='):
                    state=line.split('=',1)[1].strip('"')
        except (OSError,ValueError,subprocess.SubprocessError):
            if args.apply:
                raise ValueError('VM %s does not exist (create it with demo/demo create-vms)'%args.vm)
        if args.apply and state!='running':
            raise ValueError('VM %s is not running (state: %s). Start it and sign in once, then re-run'%(args.vm,state))
        print('VM %s: %s'%(args.vm,state or 'not found'),file=out)
        password=args.windows_password_file
        snippet_dir=Path(tempfile.mkdtemp(prefix='pinpoint-ncpa-')) if args.apply else Path('<temporary directory>')
        snippet=snippet_dir/'pinpoint.cfg'
        steps=[('Copy the installer to the guest',guest_copy(args.vm,password,args.installer,GUEST_TEMP)),
               ('Verify the installer hash in the guest',guest_run(args.vm,password,hash_script(name,expected))),
               ('Install NCPA silently (skipped when already installed)',guest_run(args.vm,password,install_script(name))),
               ('Copy the NCPA token and port (a temporary file holding the token)',guest_copy(args.vm,password,snippet,GUEST_CONFIG_DIR)),
               ('Set the Windows address %s/%d'%(WINDOWS_IP,WINDOWS_PREFIX),guest_run(args.vm,password,network_script())),
               ('Open the firewall to %s only on port %d'%(APPLIANCE_IP,args.port),guest_run(args.vm,password,firewall_script(args.port))),
               ('Start the ncpa service automatically',guest_run(args.vm,password,service_script())),
               ('Verify the agent answers on port %d'%args.port,guest_run(args.vm,password,verify_script(args.port))),
               ('Remove the installer from the guest',guest_run(args.vm,password,cleanup_script(name)))]
        for label,command in steps:
            print(label,file=out)
            show(command,out)
        if args.register:
            print('Register the agent in Pinpoint at %s (device %s, port %d)'%(args.pinpoint_url,WINDOWS_IP,args.port),file=out)
        if not args.apply:
            print('\nNothing was changed. Add --apply to run these steps.',file=out)
            return 0
        try:
            snippet_fd=os.open(str(snippet),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(snippet_fd,'w') as handle:
                handle.write(config_snippet(token,args.port))
            for label,command in steps:
                print('==> '+label,file=out)
                result=runner(command)
                if result and result.strip():
                    print(result.strip(),file=out)
        finally:
            shutil.rmtree(snippet_dir,ignore_errors=True)
        if args.register:
            register_in_pinpoint(http,args.pinpoint_url,args.pinpoint_email,read_secret_file(args.pinpoint_password_file,'Pinpoint password'),token,args.port,out)
    except (OSError,ValueError,subprocess.SubprocessError) as problem:
        print(problem if str(problem) else 'NCPA install stopped',file=err)
        print('Stopped; every step can be re-run.',file=err)
        return 1
    print('\nNCPA is installed and answering. Take the ncpa-ready snapshot while the VM is off if you want a restore point.',file=out)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
