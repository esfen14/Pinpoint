"""One-use fresh target-host installer; private payload arrives only through stdin."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path('/var/lib/pinpoint-defense')
SOURCE=Path('/opt/pinpoint-defense')


def run(argv):
    """Run fixed setup commands with output kept in the private installation log."""
    with Path('/var/log/pinpoint-defense-bootstrap.log').open('ab') as output:
        subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=output,check=True,timeout=1800)


def write(path,text,mode=0o600):
    """Create a fresh fixed destination without following existing symlinks."""
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'w') as output:output.write(text)


def validate_payload(payload):
    """Reject foreign host execution, malformed keys and paths before any write."""
    if os.geteuid()!=0 or Path('/.dockerenv').exists() or Path('/sys/class/dmi/id/product_name').read_text().strip()!='VirtualBox':
        raise ValueError('Fresh bootstrap requires the dedicated VirtualBox VM')
    if set(payload)!={'context','private_host_key','public_host_key','authorized_key','files'}:
        raise ValueError('Invalid bootstrap payload')
    context=payload['context']
    if set(context)!={'version','owner','vm_uuid','parent_mac'} or context['version']!=1 or not re.fullmatch(r'[a-f0-9]{48}',context['owner']):
        raise ValueError('Invalid bootstrap ownership')
    if Path('/sys/class/dmi/id/product_uuid').read_text().strip().lower()!=context['vm_uuid']:
        raise ValueError('Bootstrap VM UUID mismatch')
    if not re.fullmatch(r'(?:[a-f0-9]{2}:){5}[a-f0-9]{2}',context['parent_mac']):
        raise ValueError('Invalid bootstrap parent identity')
    if not payload['private_host_key'].startswith('-----BEGIN OPENSSH PRIVATE KEY-----\n') or not payload['private_host_key'].endswith('-----END OPENSSH PRIVATE KEY-----\n'):
        raise ValueError('Invalid injected private host key')
    for name in ['public_host_key','authorized_key']:
        if not re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/=]+(?: [a-zA-Z0-9_-]+)?\n?',payload[name]):
            raise ValueError('Invalid injected public key')
    allowed={'__init__.py','catalog.py','compose.py','manifest.json','preflight.py','node.py','guest.py','Dockerfile','Dockerfile.dockerignore'}
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
        run(['systemctl','disable','--now','ssh.socket'])
        run(['systemctl','stop','ssh.service'])
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
        config=Path('/etc/ssh/sshd_config.d/00-defense.conf')
        write(config,'ListenAddress 10.0.2.15\nHostKey /etc/ssh/ssh_host_ed25519_key\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nAllowUsers defense\n',0o644)
        # No general sudo or Docker group access for the management account.
        run(['gpasswd','-d','defense','sudo'])
        write(Path('/etc/sudoers.d/90-pinpoint-defense'),'defense ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-defense-guest\n',0o440)
        write(Path('/usr/local/sbin/pinpoint-defense-guest'),'#!/bin/sh\nexec /usr/bin/python3 /opt/pinpoint-defense/demo/defense/guest.py "$@"\n',0o755)
        run(['/usr/sbin/visudo','-cf','/etc/sudoers.d/90-pinpoint-defense'])
        run(['apt-get','update'])
        run(['apt-get','install','-y','--no-install-recommends','docker.io','docker-compose-v2','iproute2','procps'])
        write(SOURCE/'bootstrap.py',Path(__file__).read_text())
        write(Path('/etc/systemd/system/pinpoint-defense-build.service'),
              '[Unit]\nDescription=Prepare the owned defense target image\n'
              'Wants=network-online.target\nAfter=network-online.target docker.service\n'
              'Requires=docker.service\nConditionPathExists=!/var/lib/pinpoint-defense/prepared.json\n'
              '[Service]\nType=oneshot\nUMask=0077\nTimeoutStartSec=45min\n'
              'ExecStart=/usr/bin/python3 /opt/pinpoint-defense/bootstrap.py build\n'
              '[Install]\nWantedBy=multi-user.target\n',0o644)
        run(['systemctl','enable','pinpoint-defense-build.service'])
        # Docker enables forwarding during setup. No demo containers exist yet.
        write(Path('/etc/sysctl.d/90-pinpoint-defense.conf'),'net.ipv4.ip_forward=0\nnet.ipv6.conf.all.forwarding=0\nnet.ipv6.conf.all.disable_ipv6=1\nnet.ipv6.conf.default.disable_ipv6=1\n',0o644)
        run(['sysctl','--system'])
        run(['/usr/sbin/sshd','-t'])
        run(['systemctl','enable','ssh.service'])
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
    if Path('/sys/class/dmi/id/product_uuid').read_text().strip().lower()!=context['vm_uuid']:
        raise ValueError('Image build guest UUID mismatch')
    if (ROOT/'prepared.json').exists():return
    if subprocess.run(['docker','ps','-aq'],capture_output=True,text=True,check=True,timeout=15).stdout.strip():
        raise ValueError('Fresh build refuses an existing container')
    run(['docker','build','--iidfile',str(ROOT/'image-id'),'-f',str(SOURCE/'demo'/'defense'/'Dockerfile'),str(SOURCE)])
    image=(ROOT/'image-id').read_text().strip()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ValueError('Build did not produce a pinned image')
    write(ROOT/'runtime.json',json.dumps({'image':image})+'\n')
    sys.path.insert(0,str(SOURCE/'demo'))
    from defense.catalog import load_catalog
    from defense.compose import compose_document
    catalog=load_catalog()
    for parent in ['identities','data','private']:(ROOT/parent).mkdir(mode=0o700)
    for device in catalog.devices:
        if device.kind=='linux':
            (ROOT/'identities'/device.name).mkdir(mode=0o700)
            (ROOT/'data'/device.name).mkdir(mode=0o700)
    import secrets
    write(ROOT/'private'/'snmp-community',secrets.token_hex(16)+'\n')
    write(ROOT/'spike-compose.json',json.dumps(compose_document(catalog,image,context['owner'],spike=True)))
    run(['sysctl','--system'])
    write(ROOT/'prepared.json',json.dumps({'version':1,'prepared':True,'containers_started':False})+'\n')


if __name__=='__main__':
    if sys.argv[1:]==['build']:
        try:build_image()
        except Exception:
            print('Owned image build failed; inspect the private guest log.',file=sys.stderr)
            raise SystemExit(1)
    elif sys.argv[1:]:raise SystemExit(2)
    else:raise SystemExit(main())
