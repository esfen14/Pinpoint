"""Fixed container service controls; refuse execution outside the owned guest image."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import stat
import subprocess
import sys
import time
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense.bootstrap import dmi_uuid_matches
from defense.catalog import load_catalog, render_dnsmasq
from defense.preflight import read_private_json

IDENTITY = Path('/identity')
DATA = Path('/data')
RUN = Path('/run')
CONTEXT = Path('/etc/pinpoint-defense/context.json')


def command(argv: list[str], *, timeout=30, check=True, input_text=None):
    """Use fixed argv only; daemon/credential output never becomes a public error."""
    try:
        result = subprocess.run(argv,capture_output=True,text=True,input=input_text,timeout=timeout)
        if check and result.returncode:
            raise ValueError('Owned node service operation failed')
        return result
    except (OSError,subprocess.TimeoutExpired):
        raise ValueError('Owned node service operation unavailable') from None


def private_directory(path: Path) -> None:
    """Require an existing same-user private directory, not an adopted/symlink path."""
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
        raise ValueError('Unsafe node state directory')


def atomic(path: Path, value: str, *, public=False) -> None:
    """Durably replace owned state without following links or clobbering foreign files."""
    parent=path.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=os.getuid() or parent.st_mode&0o022:
        raise ValueError('Unsafe writable state parent')
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&(0o022 if public else 0o077):
            raise ValueError('Unsafe existing node state')
    temporary = path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    fd = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644 if public else 0o600)
    try:
        with os.fdopen(fd,'w') as stream:
            os.fchmod(stream.fileno(),0o644 if public else 0o600)
            stream.write(value);stream.flush();os.fsync(stream.fileno())
        temporary.replace(path)
        directory=os.open(path.parent,os.O_DIRECTORY|os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if temporary.exists():temporary.unlink()


def identity(root: Path, device, owner: str) -> dict:
    """Create a unique persistent machine/SSH identity only in its owned volume."""
    private_directory(root)
    if not re.fullmatch(r'[a-f0-9]{48}',owner):
        raise ValueError('Invalid node owner')
    expected={'target':device.name,'owner':owner,'mac':device.mac,'client_id':device.client_id}
    path=root/'identity.json'
    if path.exists():
        saved=read_private_json(path)
        if any(saved.get(k)!=v for k,v in expected.items()) or not re.fullmatch(r'[a-f0-9]{32}',saved.get('machine_id','')):
            raise ValueError('Persistent node identity belongs to another target/project')
    else:
        if any(root.iterdir()):
            raise ValueError('Refusing to adopt an unmarked nonempty identity volume')
        saved=dict(expected,machine_id=uuid.uuid4().hex)
        atomic(path,json.dumps(saved)+'\n')
    machine=root/'machine-id'
    if not machine.exists():atomic(machine,saved['machine_id']+'\n')
    elif machine.is_symlink() or machine.read_text().strip()!=saved['machine_id']:
        raise ValueError('Persistent machine identity changed')
    key=root/'ssh_host_ed25519_key'
    if key.is_symlink() or Path(str(key)+'.pub').is_symlink():
        raise ValueError('Unsafe persistent SSH identity')
    if key.exists():
        info=key.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o077:
            raise ValueError('Unsafe persistent SSH private key')
    if not key.exists():
        command(['ssh-keygen','-q','-t','ed25519','-N','','-C',device.name,'-f',str(key)])
    return saved


def validate_request(catalog, target: str, data: dict) -> dict:
    """Validate a closed command vocabulary before any process or file action."""
    device=catalog.target(target)
    if device.kind!='linux' or not isinstance(data,dict):
        raise ValueError('Invalid Linux node request')
    operation=data.get('operation')
    shapes={'inspect':{'operation'},'baseline':{'operation'},
            'server-config':{'operation','reservations','lease_seconds'},
            'server-stop':{'operation'},'server-start':{'operation'},
            'lease-acquire':{'operation','expected_address'},'lease-release':{'operation'}}
    if operation not in shapes or set(data)!=shapes[operation]:
        raise ValueError('Unsupported node operation or fields')
    if operation.startswith('server-') and target!='dhcp01':
        raise ValueError('DHCP server controls require the server target')
    if operation.startswith('lease-') and device.mode!='dhcp':
        raise ValueError('Lease controls require one of the five DHCP clients')
    if operation=='server-config':render_dnsmasq(catalog,data['reservations'],data['lease_seconds'])
    if operation=='lease-acquire' and data['expected_address'] not in catalog.pool:
        raise ValueError('DHCP acquisition requires a checked pool reservation')
    return data


def validate_network(catalog, device, links: list[dict], routes: list[dict], *, unaddressed=False) -> list[str]:
    """Require the exact MAC/interface, one owned address and no default route."""
    if not isinstance(links,list) or {v.get('ifname') for v in links}!={'lo','eth0'} or routes:
        raise ValueError('Node interface/default-route boundary changed')
    matches=[v for v in links if v.get('ifname')=='eth0']
    if len(matches)!=1 or matches[0].get('address','').lower()!=device.mac:
        raise ValueError('Node MAC identity changed')
    values=[a for a in matches[0].get('addr_info',[]) if a.get('family')=='inet']
    if not values and unaddressed and device.mode=='dhcp':return []
    allowed=set(catalog.pool+catalog.static_slots) if device.mode=='dhcp' else {device.address}
    if len(values)!=1 or values[0].get('local') not in allowed or values[0].get('prefixlen')!=catalog.network.prefixlen:
        raise ValueError('Node does not have exactly one allowed demo address')
    return [values[0]['local']]


def program_specs(catalog, device) -> dict[str,list[str]]:
    """Map catalog protocols to real foreground daemons, never arbitrary commands."""
    services={p.service for p in device.listeners}
    programs={}
    if 'ssh' in services:programs['ssh']=['/usr/sbin/sshd','-D','-e','-f','/run/sshd.conf']
    if services&{'http','https'}:programs['web']=['/usr/sbin/nginx','-c','/run/nginx.conf','-g','daemon off;']
    if 'ftp' in services:programs['ftp']=['/usr/sbin/vsftpd','/run/vsftpd.conf']
    if 'smtp' in services:programs['smtp']=['/usr/sbin/postfix','-c','/run/postfix','start-fg']
    if 'imap' in services:programs['imap']=['/usr/sbin/dovecot','-F','-c','/run/dovecot.conf']
    if 'snmp' in services:programs['snmp']=['/usr/sbin/snmpd','-f','-Lo','-C','-c','/run/snmpd.conf']
    if 'dns' in services:programs['dns']=['/usr/sbin/dnsmasq','--keep-in-foreground','--conf-file=/run/dns.conf']
    if 'dhcp' in services:programs['dhcp']=['/usr/sbin/dnsmasq','--keep-in-foreground','--conf-file=/data/dhcp.conf']
    if 'pgsql' in services:
        programs['pgsql']=['/usr/sbin/runuser','-u','postgres','--','/usr/lib/postgresql/16/bin/postgres',
                           '-D','/data/pgsql','-c','config_file=/run/postgresql.conf']
    if device.mode=='dhcp':
        programs['lease']=['/usr/sbin/dhclient','-4','-d','-v','-cf','/identity/dhclient.conf',
                           '-pf','/run/dhclient.pid','-lf','/identity/dhclient.leases','eth0']
    return programs


def supervisor_config(programs: dict[str,list[str]]) -> str:
    """Use only a root Unix socket and let Supervisor own/reap service groups."""
    lines=['[unix_http_server]','file=/run/supervisor.sock','chmod=0600',
           '[supervisord]','nodaemon=true','user=root','pidfile=/run/supervisord.pid',
           'logfile=/data/supervisor.log','logfile_maxbytes=1MB','logfile_backups=2','loglevel=warn',
           '[rpcinterface:supervisor]','supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface',
           '[supervisorctl]','serverurl=unix:///run/supervisor.sock']
    for name,argv in programs.items():
        if not re.fullmatch(r'[a-z]+',name):raise ValueError('Invalid fixed daemon name')
        lines += [f'[program:{name}]','command='+shlex.join(argv),'autostart=false',
                  'autorestart=false','startsecs=1','stopasgroup=true','killasgroup=true',
                  'stopwaitsecs=10',f'stdout_logfile=/data/{name}.out.log',
                  'stdout_logfile_maxbytes=1MB','stdout_logfile_backups=2',
                  f'stderr_logfile=/data/{name}.err.log','stderr_logfile_maxbytes=1MB',
                  'stderr_logfile_backups=2']
    return '\n'.join(lines)+'\n'


def container_context() -> dict:
    """Refuse physical-host/foreign-container execution before filesystem changes."""
    if os.geteuid()!=0 or not Path('/.dockerenv').is_file() or Path('/sys/class/dmi/id/product_name').read_text().strip()!='VirtualBox':
        raise ValueError('Node controls require the dedicated VirtualBox guest container')
    context=read_private_json(CONTEXT)
    if set(context)!={'version','owner','vm_uuid','parent_mac'} or context['version']!=1:
        raise ValueError('Invalid guest context')
    if not re.fullmatch(r'[a-f0-9]{48}',context.get('owner','')):
        raise ValueError('Invalid guest project owner')
    if not dmi_uuid_matches(context['vm_uuid'],Path('/sys/class/dmi/id/product_uuid').read_text().strip()):
        raise ValueError('Container is running on a foreign guest')
    return context


def service_directory(path: Path, *, uid=None, mode=0o755) -> None:
    """Create only image-defined daemon directories, refusing symlink substitutions."""
    if path.is_symlink():raise ValueError('Unsafe daemon directory')
    path.mkdir(parents=True,exist_ok=True)
    if not path.is_dir():raise ValueError('Invalid daemon directory')
    path.chmod(mode)
    if uid is not None:os.chown(path,uid,uid)


def prepare_services(catalog, device) -> None:
    """Generate fixed protocol configs; init does not start any network listener."""
    private_directory(IDENTITY)
    info=DATA.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:
        raise ValueError('Unsafe persistent service data')
    services={p.service for p in device.listeners}
    # Root-only allocator state must retain the private directory boundary.
    DATA.chmod(0o711 if services&{'http','https','ftp','smtp','imap','pgsql'} else 0o700)
    service_directory(Path('/run/sshd'))
    if 'ssh' in services:
        port=next(p.port for p in device.listeners if p.service=='ssh')
        atomic(RUN/'sshd.conf',f'Port {port}\nListenAddress 0.0.0.0\nHostKey /identity/ssh_host_ed25519_key\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nUsePAM no\nUseDNS no\nPidFile /run/sshd.pid\n')
    if services&{'http','https'}:
        service_directory(DATA/'www')
        atomic(DATA/'www/index.html',device.name+' alive\n',public=True)
        service_directory(RUN/'nginx')
        if 'https' in services and not (IDENTITY/'tls.key').exists():
            command(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','365',
                     '-subj',f'/CN={device.name}.demo.test','-keyout',str(IDENTITY/'tls.key'),'-out',str(IDENTITY/'tls.crt')])
        servers=[]
        for listener in device.listeners:
            if listener.service not in {'http','https'}:continue
            tls=' ssl' if listener.service=='https' else ''
            certificates='ssl_certificate /identity/tls.crt; ssl_certificate_key /identity/tls.key;' if tls else ''
            servers.append(f'server {{ listen {listener.port}{tls}; {certificates} root /data/www; location / {{ try_files $uri /index.html; }} }}')
        atomic(RUN/'nginx.conf','worker_processes 1; pid /run/nginx.pid; error_log /data/web-error.log warn; events { worker_connections 64; } http { access_log off; client_body_temp_path /run/nginx/body; proxy_temp_path /run/nginx/proxy; fastcgi_temp_path /run/nginx/fastcgi; '+''.join(servers)+' }\n')
    if 'ftp' in services:
        service_directory(DATA/'public')
        atomic(DATA/'public/demo.txt','Pinpoint isolated FTP demo\n',public=True)
        service_directory(RUN/'vsftpd-empty')
        atomic(RUN/'vsftpd.conf','listen=YES\nlisten_ipv6=NO\nbackground=NO\nanonymous_enable=YES\nlocal_enable=NO\nwrite_enable=NO\nanon_root=/data/public\nsecure_chroot_dir=/run/vsftpd-empty\nseccomp_sandbox=NO\n')
    if 'smtp' in services:
        service_directory(RUN/'postfix')
        if not (DATA/'mailqueue').exists():
            service_directory(DATA/'mailqueue')
            command(['cp','-a','/var/spool/postfix/.','/data/mailqueue/'])
        atomic(RUN/'postfix/main.cf',f'myhostname = {device.name}.demo.test\nmydestination = localhost\ninet_interfaces = all\ninet_protocols = ipv4\nmynetworks = 127.0.0.0/8\nsmtpd_relay_restrictions = reject_unauth_destination\nqueue_directory = /data/mailqueue\ndata_directory = /var/lib/postfix\nmail_owner = postfix\nsmtp_bind_address = 127.0.0.1\n',public=True)
        atomic(RUN/'postfix/master.cf',Path('/etc/postfix/master.cf').read_text(),public=True)
    if 'imap' in services:
        service_directory(RUN/'dovecot')
        atomic(RUN/'dovecot.conf','protocols = imap\nlisten = *\nssl = no\nbase_dir = /run/dovecot\nlog_path = /data/imap.log\ninfo_log_path = /dev/null\nmail_location = maildir:/data/mailboxes/%u\npassdb {\n driver = passwd\n}\nuserdb {\n driver = passwd\n}\nnamespace inbox {\n inbox = yes\n}\n')
    if 'dns' in services:
        atomic(RUN/'dns.conf','interface=eth0\nbind-interfaces\nport=53\nno-resolv\nno-hosts\naddress=/#/10.77.1.8\nlog-facility=/data/dns.log\nuser=root\n')
    if 'snmp' in services:
        path=Path('/run/secrets/snmp-community')
        value=path.read_text().strip()
        if path.is_symlink() or not re.fullmatch(r'[a-f0-9]{32}',value):raise ValueError('Invalid private SNMP configuration')
        service_directory(DATA/'snmp',mode=0o700)
        atomic(RUN/'snmpd.conf',f'agentAddress udp:161\nrocommunity {value} 10.77.1.0/27\nsysLocation IsolatedDefenseLab\nsysContact DemoOwner\n')
    if 'pgsql' in services:
        postgres=pwd.getpwnam('postgres')
        if not (DATA/'pgsql').exists():
            service_directory(DATA/'pgsql',uid=postgres.pw_uid,mode=0o700)
            command(['/usr/sbin/runuser','-u','postgres','--','/usr/lib/postgresql/16/bin/initdb',
                     '-D','/data/pgsql','--no-locale','--encoding=UTF8','--auth=trust'],timeout=60)
            command(['/usr/sbin/runuser','-u','postgres','--','/usr/lib/postgresql/16/bin/postgres',
                     '--single','-D','/data/pgsql','postgres'],input_text='CREATE ROLE pinpoint_demo LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;\nALTER ROLE pinpoint_demo SET default_transaction_read_only = on;\nREVOKE CREATE ON SCHEMA public FROM PUBLIC;\n')
        atomic(RUN/'postgresql.conf',"data_directory = '/data/pgsql'\nhba_file = '/run/pg_hba.conf'\nlisten_addresses = '*'\nport = 5432\nunix_socket_directories = '/run/pgsql'\nshared_buffers = '16MB'\nmax_connections = 10\n",public=True)
        atomic(RUN/'pg_hba.conf','local all postgres trust\nhost postgres pinpoint_demo 10.77.1.1/32 trust\n',public=True)
        service_directory(RUN/'pgsql',uid=postgres.pw_uid,mode=0o700)
    if device.mode=='dhcp':
        atomic(IDENTITY/'dhclient.conf',f'timeout 20;\nretry 3;\nselect-timeout 1;\nsend host-name "{device.name}";\nsend dhcp-client-identifier "{device.client_id}";\nrequest subnet-mask, broadcast-address, dhcp-lease-time;\n')
    atomic(RUN/'supervisord.conf',supervisor_config(program_specs(catalog,device)))


def supervisor(action: str, program: str | None = None, *, check=True):
    """Invoke only fixed Supervisor verbs and known program names."""
    if action not in {'status','start','stop'} or program is not None and program not in {'ssh','web','ftp','smtp','imap','dns','snmp','pgsql','dhcp','lease'}:
        raise ValueError('Invalid owned daemon action')
    return command(['/usr/bin/supervisorctl','-c','/run/supervisord.conf',action,*([program] if program else [])],check=check)


def network(catalog,device,*,unaddressed=False):
    """Collect current namespace interfaces; no fabricated leases or injected observations."""
    links=json.loads(command(['ip','-j','-4','addr','show']).stdout)
    routes=json.loads(command(['ip','-j','-4','route','show','default']).stdout)
    return validate_network(catalog,device,links,routes,unaddressed=unaddressed)


def network_reason(catalog,device) -> str | None:
    """Return one fixed diagnostic category for the inspected namespace boundary."""
    links=json.loads(command(['ip','-j','-4','addr','show']).stdout)
    routes=json.loads(command(['ip','-j','-4','route','show','default']).stdout)
    if not isinstance(links,list) or {value.get('ifname') for value in links}!={'lo','eth0'}:
        return 'interfaces'
    eth=[value for value in links if value.get('ifname')=='eth0']
    if len(eth)!=1 or eth[0].get('address','').lower()!=device.mac:
        return 'mac'
    if routes:
        return 'default-route'
    try:validate_network(catalog,device,links,routes,unaddressed=True)
    except ValueError:return 'address'
    return None


def listening_ports() -> list[dict]:
    """Read kernel socket tables without returning daemon arguments or credentials."""
    values=set()
    for protocol in ['tcp','udp']:
        for suffix in ['', '6']:
            path=Path('/proc/net')/(protocol+suffix)
            if not path.exists():continue
            for line in path.read_text().splitlines()[1:]:
                columns=line.split()
                if len(columns)<4:continue
                if protocol=='tcp' and columns[3]!='0A':continue
                port=int(columns[1].rsplit(':',1)[1],16)
                if port:values.add((protocol,port))
    return [{'protocol':p,'port':n} for p,n in sorted(values)]


def inspection(catalog,device) -> dict:
    """Report actual sockets and service state; plugin expectations stay separate."""
    reason=network_reason(catalog,device)
    safe=reason is None
    addresses=network(catalog,device,unaddressed=True) if safe else []
    states=[]
    for line in supervisor('status',check=False).stdout.splitlines():
        fields=line.split()
        if len(fields)>=2:states.append({'program':fields[0],'state':fields[1]})
    return {'target':device.name,'network_safe':safe,'network_reason':reason,'addresses':addresses,'mac':device.mac,
            'client_id':device.client_id,'listeners':listening_ports(),'services':states}


def server_config(catalog,request) -> None:
    """Preserve other leases/logs while restarting the one owned DHCP allocator."""
    desired=render_dnsmasq(catalog,request['reservations'],request['lease_seconds'])+'user=root\ngroup=root\n'
    saved=DATA/'reservations.json'
    previous=read_private_json(saved) if saved.exists() else {'reservations':{}}
    supervisor('stop','dhcp',check=False)
    changed={d.mac for d in catalog.devices if d.mode=='dhcp' and previous.get('reservations',{}).get(d.name)!=request['reservations'][d.name]}
    leases=DATA/'dhcp.leases'
    if leases.exists():
        lines=[]
        for line in leases.read_text().splitlines():
            fields=line.split()
            if len(fields)<2 or fields[1].lower() not in changed:lines.append(line)
        atomic(leases,'\n'.join(lines)+'\n',public=True)
    atomic(DATA/'dhcp.conf',desired)
    atomic(saved,json.dumps({'reservations':request['reservations'],'lease_seconds':request['lease_seconds']})+'\n')
    supervisor('start','dhcp')


def handle(catalog,device,request) -> dict:
    """Dispatch the minimal baseline/DHCP spike protocol inside an owned namespace."""
    operation=request['operation']
    if operation=='inspect':return inspection(catalog,device)
    addresses=network(catalog,device,unaddressed=True)
    if operation=='baseline':
        for program in program_specs(catalog,device):
            if program=='lease' or program=='dhcp' and not (DATA/'reservations.json').exists():continue
            status=supervisor('status',program,check=False).stdout.split()
            if len(status)<2 or status[1]!='RUNNING':supervisor('start',program)
    elif operation=='server-config':server_config(catalog,request)
    elif operation=='server-stop':supervisor('stop','dhcp',check=False)
    elif operation=='server-start':
        saved=read_private_json(DATA/'reservations.json')
        server_config(catalog,{'reservations':saved['reservations'],'lease_seconds':saved['lease_seconds']})
    elif operation=='lease-acquire':
        expected=request['expected_address']
        if addresses and addresses!=[expected]:raise ValueError('Release the existing lease before acquiring a different address')
        if not addresses:
            supervisor('start','lease')
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                addresses=network(catalog,device,unaddressed=True)
                if addresses==[expected]:break
                if addresses:raise ValueError('DHCP installed an unexpected address')
                time.sleep(0.25)
            else:
                supervisor('stop','lease',check=False)
                raise ValueError('Real DHCP acquisition timed out')
    elif operation=='lease-release':
        if any(value not in catalog.pool for value in addresses):raise ValueError('A static address requires address-mode controls')
        if addresses:
            command(['/usr/sbin/dhclient','-4','-r','-cf','/identity/dhclient.conf','-pf','/run/dhclient.pid',
                     '-lf','/identity/dhclient.leases','eth0'],timeout=30)
        supervisor('stop','lease',check=False)
        if network(catalog,device,unaddressed=True):raise ValueError('Lease release kept an interface address')
    return inspection(catalog,device)


def main(argv=None) -> int:
    """Use JSON stdin for fixed requests; no command, script, VM name or path input."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['init','control'])
    parser.add_argument('target')
    args=parser.parse_args(argv)
    try:
        os.umask(0o077)
        catalog=load_catalog();device=catalog.target(args.target)
        if device.kind!='linux':raise ValueError('Node image supports Linux devices only')
        request=None
        if args.action=='control':
            text=sys.stdin.read(8193)
            if len(text)>8192:raise ValueError('Request exceeds node protocol limit')
            request=validate_request(catalog,args.target,json.loads(text))
        context=container_context()
        if args.action=='init':
            identity(IDENTITY,device,context['owner'])
            prepare_services(catalog,device)
            os.execv('/usr/bin/supervisord',['supervisord','-n','-c','/run/supervisord.conf'])
        saved=read_private_json(IDENTITY/'identity.json')
        if saved.get('target')!=device.name or saved.get('owner')!=context['owner'] or saved.get('mac')!=device.mac:
            raise ValueError('Persistent node identity mismatch')
        lock=os.open(DATA/'control.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(lock)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or info.st_mode&0o077:
                raise ValueError('Unsafe node control claim')
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            print(json.dumps(handle(catalog,device,request)))
        finally:os.close(lock)
        return 0
    except (OSError,ValueError,TypeError,KeyError):
        print('Owned defense node operation refused or failed; private guest inspection required.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
