"""One-use fresh target-host installer; private payload arrives only through stdin."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
import stat
import signal
import hashlib
from contextlib import contextmanager

ROOT=Path('/var/lib/pinpoint-defense')
SOURCE=Path('/opt/pinpoint-defense')
RUNTIME_FILES=('__init__.py','catalog.py','compose.py','manifest.json','preflight.py',
               'node.py','guest.py','Dockerfile','Dockerfile.dockerignore','bootstrap.py')


def parent_network(context):
    """Let the controller own only the pinned demo NIC's unnumbered link state."""
    mac=context.get('parent_mac','')
    if not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}',mac):raise ValueError('Invalid parent MAC')
    return ('[Match]\nMACAddress='+mac+'\n[Link]\nActivationPolicy=manual\nRequiredForOnline=no\n'
            '[Network]\nDHCP=no\nLinkLocalAddressing=no\nIPv6AcceptRA=no\nIPForward=no\n')


def build_unit():
    """Check source/image provenance at each boot instead of trusting a stale marker."""
    return ('[Unit]\nDescription=Prepare the owned defense target image\n'
            'Wants=network-online.target\nAfter=network-online.target docker.service pinpoint-defense-ready.service\n'
            'Requires=docker.service pinpoint-defense-ready.service\n'
            '[Service]\nType=oneshot\nUMask=0077\nTimeoutStartSec=45min\n'
            'ExecStart=/usr/bin/python3 /opt/pinpoint-defense/bootstrap.py build\n'
            '[Install]\nWantedBy=multi-user.target\n')


def image_source_hash(directory=None):
    """Hash the fixed bounded regular runtime sources, refusing substituted links."""
    directory=directory or SOURCE/'demo'/'defense'
    digest=hashlib.sha256()
    for name in RUNTIME_FILES:
        path=directory/name
        try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        except OSError:raise ValueError('Unsafe or missing image source') from None
        with os.fdopen(fd,'rb') as source:
            info=os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o022 or info.st_size>1048576:
                raise ValueError('Unsafe image source')
            data=source.read(1048577)
        digest.update(name.encode()+b'\0'+str(len(data)).encode()+b'\0'+data)
    return digest.hexdigest()


def docker_settings():
    """Keep Docker from enabling host forwarding at daemon/network startup."""
    return {'ip-forward':False}


def docker_guard_dropin():
    """Reset and verify forwarding on every daemon start, including later reboots."""
    return '[Service]\nExecStartPost=/usr/bin/python3 /opt/pinpoint-defense/bootstrap.py guard\n'


def ready_unit():
    """Repeat account hardening after cloud-init and before target/image activation."""
    return ('[Unit]\nDescription=Verify owned defense guest boundaries\n'
            'Wants=cloud-final.service\nRequires=docker.service\n'
            'After=cloud-final.service docker.service\nBefore=pinpoint-defense-build.service\n'
            '[Service]\nType=oneshot\nRemainAfterExit=yes\nUMask=0077\n'
            'ExecStart=/usr/bin/python3 /opt/pinpoint-defense/bootstrap.py ready\n'
            '[Install]\nWantedBy=multi-user.target\n')


def owned_context():
    """Prove the dedicated root VirtualBox guest before any restrictive mutation."""
    sys.path.insert(0,str(SOURCE/'demo'))
    from defense.preflight import read_private_json
    if os.geteuid()!=0 or Path('/.dockerenv').exists() or Path('/sys/class/dmi/id/product_name').read_text().strip()!='VirtualBox':
        raise ValueError('Operation requires the owned guest')
    context=read_private_json(ROOT/'context.json')
    if set(context)!={'version','owner','vm_uuid','parent_mac'} or context['version']!=1 or not re.fullmatch(r'[a-f0-9]{48}',context.get('owner','')) or not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}',context.get('parent_mac','')):
        raise ValueError('Invalid guest ownership state')
    if not dmi_uuid_matches(context['vm_uuid'],Path('/sys/class/dmi/id/product_uuid').read_text().strip()):
        raise ValueError('Guest UUID mismatch')
    return context


def forwarding_values():
    """Read real IPv4 and IPv6 forwarding values, without assuming sysctl succeeded."""
    return (int(Path('/proc/sys/net/ipv4/ip_forward').read_text()),
            int(Path('/proc/sys/net/ipv6/conf/all/forwarding').read_text()))


def guard_forwarding():
    """Refuse foreign execution, disable both forwarding families and verify it."""
    owned_context()
    run(['sysctl','-w','net.ipv4.ip_forward=0','net.ipv6.conf.all.forwarding=0'])
    if forwarding_values()!=(0,0):raise ValueError('Forwarding remains enabled')


def build_parent(context):
    """Find the exact plain unnumbered demo NIC before disconnecting it for a build."""
    result=subprocess.run(['ip','-j','-d','addr','show'],capture_output=True,text=True,check=True,timeout=15)
    links=json.loads(result.stdout)
    matches=[v for v in links if v.get('address','').lower()==context['parent_mac']]
    if len(matches)!=1:raise ValueError('Demo parent is missing or duplicated')
    parent=matches[0];name=parent.get('ifname','')
    if not re.fullmatch(r'[a-zA-Z0-9_]{1,15}',name) or parent.get('addr_info') or parent.get('master') or parent.get('linkinfo'):
        raise ValueError('Demo parent must be plain and unnumbered')
    return name,'UP' in parent.get('flags',[])


@contextmanager
def build_network():
    """Allow build NAT only with demo NIC down; failure leaves that NIC down."""
    context=owned_context();parent,was_up=build_parent(context)
    def interrupted(signum,frame):
        """Make normal service cancellation unwind the forwarding cleanup."""
        raise SystemExit(128+signum)
    old={sig:signal.signal(sig,interrupted) for sig in [signal.SIGTERM,signal.SIGINT]}
    success=False
    try:
        run(['ip','link','set','dev',parent,'down'])
        # Re-observe the exact disconnected NIC before opening a build-only gateway.
        actual,is_up=build_parent(context)
        if actual!=parent or is_up:raise ValueError('Build parent changed or remains up')
        run(['sysctl','-w','net.ipv4.ip_forward=1'])
        yield
        success=True
    finally:
        try:
            run(['sysctl','-w','net.ipv4.ip_forward=0','net.ipv6.conf.all.forwarding=0'])
            if forwarding_values()!=(0,0):raise ValueError('Build cleanup failed')
            if success and was_up:run(['ip','link','set','dev',parent,'up'])
        finally:
            for sig,handler in old.items():signal.signal(sig,handler)


def harden_management(root=Path('/')):
    """Remove supplementary groups and only the generated user's cloud-init sudo rule."""
    management_uid()
    cloud=root/'etc/sudoers.d/90-cloud-init-users'
    fd=None
    if cloud.exists() or cloud.is_symlink():
        try:fd=os.open(cloud,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        except OSError:raise ValueError('Unsafe cloud-init sudo file') from None
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o022 or info.st_size>65536:
                raise ValueError('Unsafe cloud-init sudo file')
            text=os.read(fd,65537).decode()
            clean='\n'.join(line for line in text.splitlines() if not re.match(r'^\s*defense\s+ALL\s*=',line))+'\n'
            if text!=clean:
                parent=cloud.parent.lstat()
                if not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=os.getuid() or parent.st_mode&0o022:
                    raise ValueError('Unsafe sudo configuration directory')
                temporary=cloud.with_name('.defense-'+uuid.uuid4().hex)
                try:
                    output=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(output,'w') as stream:
                        stream.write(clean);stream.flush();os.fchmod(stream.fileno(),0o440);os.fsync(stream.fileno())
                    if (cloud.lstat().st_dev,cloud.lstat().st_ino)!=(info.st_dev,info.st_ino):
                        raise ValueError('Sudo file changed during hardening')
                    temporary.replace(cloud)
                finally:
                    if temporary.exists():temporary.unlink()
        finally:os.close(fd)
    run(['usermod','--groups','','defense'])


def validate_management(groups,sudo):
    """Require just the primary group and the single fixed sudo helper grant."""
    grants=[re.sub(r'\s+',' ',line.strip()) for line in sudo.splitlines() if line.strip().startswith('(')]
    if set(groups)!={'defense'} or grants!=['(root) NOPASSWD: /usr/local/sbin/pinpoint-defense-guest']:
        raise ValueError('Management privileges exceed the fixed helper')


def management_uid():
    """Require the fresh install's fixed unprivileged account, never UID zero."""
    try:
        result=subprocess.run(['id','-u','defense'],capture_output=True,text=True,check=True,timeout=15)
        if result.stdout.strip()!='1000':raise ValueError('Management UID changed')
        return 1000
    except (OSError,subprocess.SubprocessError):
        raise ValueError('Management account unavailable') from None


def management_observation():
    """Verify effective grants rather than treating file changes as privilege proof."""
    management_uid()
    try:
        groups=subprocess.run(['id','-nG','defense'],capture_output=True,text=True,check=True,timeout=15)
        sudo=subprocess.run(['sudo','-n','-l','-U','defense'],capture_output=True,text=True,check=True,timeout=15,env=dict(os.environ,LC_ALL='C'))
        validate_management(groups.stdout.split(),sudo.stdout)
    except (OSError,subprocess.SubprocessError):
        raise ValueError('Management privilege observation unavailable') from None


def ready():
    """Reapply least privilege after cloud-init; no targets start on a failed gate."""
    guard_forwarding();harden_management();management_observation()


def dmi_uuid_matches(expected,observed) -> bool:
    """Compare the pinned UUID using only the two documented SMBIOS byte orders."""
    if not isinstance(expected,str) or not isinstance(observed,str):return False
    pattern=r'[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}'
    if not re.fullmatch(pattern,expected) or not re.fullmatch(pattern,observed):return False
    identifier=uuid.UUID(expected)
    return observed.lower() in {str(identifier),str(uuid.UUID(bytes=identifier.bytes_le))}


def run(argv):
    """Run fixed setup commands with output kept in the private installation log."""
    with Path('/var/log/pinpoint-defense-bootstrap.log').open('ab') as output:
        subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=output,check=True,timeout=1800,
                       env=dict(os.environ,DEBIAN_FRONTEND='noninteractive',NEEDRESTART_MODE='a'))


def configure_unit(action,unit):
    """Configure only fixed units offline; the installer has no running target systemd."""
    if action not in {'enable','disable'} or unit not in {'ssh.socket','ssh.service','pinpoint-defense-build.service','pinpoint-defense-ready.service'}:
        raise ValueError('Unsupported offline service configuration')
    run(['env','SYSTEMD_OFFLINE=1','systemctl',action,unit])


def write(path,text,mode=0o600):
    """Create a fresh fixed destination without following existing symlinks."""
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'w') as output:output.write(text)


def configure_ssh_preservation(directory=Path('/etc/cloud/cloud.cfg.d')):
    """Preserve only our injected host key rather than cloud-init rotating it at first boot."""
    write(directory/'99-defense-pinned-ssh.cfg','ssh_deletekeys: false\nssh_genkeytypes: []\n')


def configure_hardening(root=Path('/'),*,context=None):
    """Install fixed fresh-guest forwarding and post-cloud-init guards, never generic hooks."""
    docker=root/'etc/docker';dropin=root/'etc/systemd/system/docker.service.d'
    for directory in [docker,dropin]:
        if directory.is_symlink():raise ValueError('Unsafe hardening config directory')
        directory.mkdir(mode=0o755,parents=True,exist_ok=True)
        info=directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o022:
            raise ValueError('Unsafe hardening directory ownership')
    if context is None:context=owned_context()
    network=root/'etc/systemd/network'
    if network.is_symlink():raise ValueError('Unsafe network config directory')
    network.mkdir(parents=True,exist_ok=True,mode=0o755)
    info=network.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o022:
        raise ValueError('Unsafe network configuration ownership')
    write(network/'05-pinpoint-defense.network',parent_network(context),0o644)
    write(docker/'daemon.json',json.dumps(docker_settings())+'\n',0o644)
    write(dropin/'90-pinpoint-defense.conf',docker_guard_dropin(),0o644)
    write(root/'etc/systemd/system/pinpoint-defense-ready.service',ready_unit(),0o644)
    configure_unit('enable','pinpoint-defense-ready.service')


def validate_payload(payload):
    """Reject foreign host execution, malformed keys and paths before any write."""
    if os.geteuid()!=0 or Path('/.dockerenv').exists() or Path('/sys/class/dmi/id/product_name').read_text().strip()!='VirtualBox':
        raise ValueError('Fresh bootstrap requires the dedicated VirtualBox VM')
    if set(payload)!={'context','private_host_key','public_host_key','authorized_key','files'}:
        raise ValueError('Invalid bootstrap payload')
    context=payload['context']
    if set(context)!={'version','owner','vm_uuid','parent_mac'} or context['version']!=1 or not re.fullmatch(r'[a-f0-9]{48}',context['owner']):
        raise ValueError('Invalid bootstrap ownership')
    if not dmi_uuid_matches(context['vm_uuid'],Path('/sys/class/dmi/id/product_uuid').read_text().strip()):
        raise ValueError('Bootstrap VM UUID mismatch')
    if not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}',context['parent_mac']):
        raise ValueError('Invalid bootstrap parent identity')
    if not payload['private_host_key'].startswith('-----BEGIN OPENSSH PRIVATE KEY-----\n') or not payload['private_host_key'].endswith('-----END OPENSSH PRIVATE KEY-----\n'):
        raise ValueError('Invalid injected private host key')
    for name in ['public_host_key','authorized_key']:
        if not re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/=]+(?: [a-zA-Z0-9_-]+)?\n?',payload[name]):
            raise ValueError('Invalid injected public key')
    allowed={'__init__.py','catalog.py','compose.py','manifest.json','preflight.py','node.py','guest.py','Dockerfile','Dockerfile.dockerignore','bootstrap.py'}
    if set(payload['files'])!=allowed or any(not isinstance(v,str) or len(v)>1048576 for v in payload['files'].values()):
        raise ValueError('Invalid fixed runtime source bundle')
    if ROOT.exists() or SOURCE.exists():raise ValueError('Refusing to overwrite an existing guest preparation')


def main():
    """Install fixed guest prerequisites, build the pinned image and leave targets stopped."""
    try:
        os.umask(0o077)
        text=sys.stdin.read(2097153)
        if len(text)>2097152:raise ValueError('Bootstrap input too large')
        payload=json.loads(text);validate_payload(payload)
        ROOT.mkdir(mode=0o700);SOURCE.mkdir(mode=0o700)
        write(ROOT/'context.json',json.dumps(payload['context'])+'\n')
        source=SOURCE/'demo'/'defense';source.mkdir(parents=True,mode=0o700)
        for name,value in payload['files'].items():write(source/name,value)
        # Configure only the management sshd. The demo parent remains unnumbered.
        configure_unit('disable','ssh.socket')
        key=Path('/etc/ssh/ssh_host_ed25519_key')
        for path in [key,Path(str(key)+'.pub')]:
            if path.is_symlink():raise ValueError('Unsafe installer host key')
            path.unlink(missing_ok=True)
        write(key,payload['private_host_key'])
        write(Path(str(key)+'.pub'),payload['public_host_key'],0o644)
        sshdir=Path('/home/defense/.ssh');sshdir.mkdir(mode=0o700,exist_ok=False)
        write(sshdir/'authorized_keys',payload['authorized_key'])
        import pwd
        account=pwd.getpwnam('defense')
        os.chown(sshdir,account.pw_uid,account.pw_gid)
        os.chown(sshdir/'authorized_keys',account.pw_uid,account.pw_gid)
        configure_ssh_preservation()
        config=Path('/etc/ssh/sshd_config.d/00-defense.conf')
        write(config,'ListenAddress 10.0.2.15\nHostKey /etc/ssh/ssh_host_ed25519_key\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nAllowUsers defense\n',0o644)
        # No general sudo or Docker group access for the management account.
        harden_management()
        write(Path('/etc/sudoers.d/90-pinpoint-defense'),'defense ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-defense-guest\n',0o440)
        write(Path('/usr/local/sbin/pinpoint-defense-guest'),'#!/bin/sh\nexec /usr/bin/python3 /opt/pinpoint-defense/demo/defense/guest.py "$@"\n',0o755)
        run(['/usr/sbin/visudo','-cf','/etc/sudoers.d/90-pinpoint-defense'])
        run(['apt-get','update'])
        run(['apt-get','install','-y','--no-install-recommends','docker.io','docker-compose-v2','iproute2','procps'])
        write(SOURCE/'bootstrap.py',Path(__file__).read_text())
        configure_hardening(context=payload['context'])
        write(Path('/etc/systemd/system/pinpoint-defense-build.service'),build_unit(),0o644)
        configure_unit('enable','pinpoint-defense-build.service')
        # Docker enables forwarding during setup. No demo containers exist yet.
        write(Path('/etc/sysctl.d/90-pinpoint-defense.conf'),'net.ipv4.ip_forward=0\nnet.ipv6.conf.all.forwarding=0\nnet.ipv6.conf.all.disable_ipv6=1\nnet.ipv6.conf.default.disable_ipv6=1\n',0o644)
        run(['sysctl','--system'])
        run(['/usr/sbin/sshd','-t'])
        configure_unit('enable','ssh.service')
        write(ROOT/'installed.json',json.dumps({'version':1,'installed':True,'image_built':False})+'\n')
        return 0
    except Exception:
        print('Private target-host bootstrap failed; inspect its private setup log.',file=sys.stderr)
        return 1


def build_image():
    """Build after a real guest boot, before any demo container or allocator exists."""
    os.umask(0o077)
    sys.path.insert(0,str(SOURCE/'demo'))
    from defense.preflight import read_private_json
    if os.geteuid()!=0 or Path('/.dockerenv').exists() or Path('/sys/class/dmi/id/product_name').read_text().strip()!='VirtualBox':
        raise ValueError('Image build requires the dedicated guest')
    context=read_private_json(ROOT/'context.json')
    if not dmi_uuid_matches(context['vm_uuid'],Path('/sys/class/dmi/id/product_uuid').read_text().strip()):
        raise ValueError('Image build guest UUID mismatch')
    ready()
    digest=image_source_hash()
    from defense.node import atomic,private_directory
    old_runtime=read_private_json(ROOT/'runtime.json') if (ROOT/'runtime.json').exists() else {}
    source_pin=read_private_json(ROOT/'image-source.json') if (ROOT/'image-source.json').exists() else {}
    if (ROOT/'prepared.json').exists() and source_pin=={'sha256':digest}:
        from defense.guest import validate_image
        observed=json.loads(subprocess.run(['docker','image','inspect',old_runtime['image']],capture_output=True,text=True,check=True,timeout=15).stdout)
        if len(observed)!=1:raise ValueError('Ambiguous pinned image')
        validate_image(old_runtime['image'],digest,observed[0])
        return
    if subprocess.run(['docker','ps','-aq'],capture_output=True,text=True,check=True,timeout=15).stdout.strip():
        raise ValueError('Fresh build refuses an existing container')
    with build_network():
        run(['docker','build','--label','org.pinpoint.defense.source='+digest,'--iidfile',str(ROOT/'image-id'),'-f',str(SOURCE/'demo'/'defense'/'Dockerfile'),str(SOURCE)])
    image=(ROOT/'image-id').read_text().strip()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ValueError('Build did not produce a pinned image')
    atomic(ROOT/'runtime.json',json.dumps({'image':image})+'\n')
    atomic(ROOT/'image-source.json',json.dumps({'sha256':digest})+'\n')
    sys.path.insert(0,str(SOURCE/'demo'))
    from defense.catalog import load_catalog
    from defense.compose import compose_document
    catalog=load_catalog()
    for parent in ['identities','data','private']:
        (ROOT/parent).mkdir(mode=0o700,exist_ok=True);private_directory(ROOT/parent)
    for device in catalog.devices:
        if device.kind=='linux':
            (ROOT/'identities'/device.name).mkdir(mode=0o700,exist_ok=True)
            private_directory(ROOT/'identities'/device.name)
            (ROOT/'data'/device.name).mkdir(mode=0o700,exist_ok=True)
            info=(ROOT/'data'/device.name).lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Unsafe existing target data')
    import secrets
    secret=ROOT/'private'/'snmp-community'
    if not secret.exists():write(secret,secrets.token_hex(16)+'\n')
    info=secret.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or info.st_mode&0o077:raise ValueError('Unsafe private SNMP state')
    atomic(ROOT/'spike-compose.json',json.dumps(compose_document(catalog,image,context['owner'],spike=True)))
    run(['sysctl','--system'])
    atomic(ROOT/'prepared.json',json.dumps({'version':1,'prepared':True,'containers_started':False})+'\n')


if __name__=='__main__':
    if sys.argv[1:] in [['guard'],['ready']]:
        try:
            (guard_forwarding if sys.argv[1]=='guard' else ready)()
        except Exception:
            print('Owned guest hardening refused or failed; inspect private setup log.',file=sys.stderr)
            raise SystemExit(1)
    elif sys.argv[1:]==['build']:
        try:build_image()
        except Exception:
            print('Owned image build failed; inspect the private guest log.',file=sys.stderr)
            raise SystemExit(1)
    elif sys.argv[1:]:raise SystemExit(2)
    else:raise SystemExit(main())
