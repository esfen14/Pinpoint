"""Image build only: copy Nagios's signed apt repository files and the newest NCPA package.

The NCPA deploy target serves these files as repo.nagios.com, because the demo network
has no route to the internet. The files are kept byte for byte, so apt on the target
still checks Nagios's own signature when PinPoint deploys the agent.
"""
import hashlib
from pathlib import Path
import re
import subprocess
import sys

BASE = 'https://repo.nagios.com'
KEY = 'GPG-KEY-NAGIOS-V3'
INDEX_FILES = ('InRelease', 'Release', 'Release.gpg', 'Packages', 'Packages.gz')
PACKAGE_PATH = re.compile(r'pool/main/ncpa-[0-9]+(?:\.[0-9]+)*-[0-9]+\.amd64\.deb')
LIMIT = 100 * 1024 * 1024


def download(url: str) -> bytes:
    """Fetch one bounded file over verified HTTPS. The server refuses Python's own client."""
    data = subprocess.run(['curl', '-fsSL', '--proto', '=https', '--retry', '2', '--max-time', '600',
                           '--max-filesize', str(LIMIT), url], capture_output=True, check=True).stdout
    if len(data) > LIMIT:
        raise ValueError('Repository file is larger than expected')
    return data


def verify_signature(key: Path, signed: Path) -> None:
    """Refuse a repository index that Nagios's published key did not sign."""
    keyring = Path('/tmp/nagios-mirror-keyring.gpg')
    subprocess.run(['gpg', '--batch', '--yes', '--dearmor', '-o', str(keyring), str(key)], check=True)
    subprocess.run(['gpgv', '--keyring', str(keyring), str(signed)], check=True)
    keyring.unlink()


def signed_hash(release: str, name: str) -> str:
    """Read one file's SHA256 from the signed release text."""
    in_section = False
    for line in release.splitlines():
        if line == 'SHA256:':
            in_section = True
        elif in_section and line.startswith(' '):
            fields = line.split()
            if len(fields) == 3 and fields[2] == name:
                return fields[0]
        elif in_section:
            break
    raise ValueError('Release file does not list ' + name)


def newest_ncpa(packages: str) -> dict:
    """Pick the highest amd64 NCPA version, which is the one `apt-get install ncpa` takes."""
    found = []
    for block in packages.split('\n\n'):
        fields = {}
        for line in block.splitlines():
            if ': ' in line and not line.startswith(' '):
                name, value = line.split(': ', 1)
                fields[name] = value
        if fields.get('Package') != 'ncpa' or fields.get('Architecture') != 'amd64':
            continue
        version = []
        for part in re.findall(r'[0-9]+', fields['Version']):
            version.append(int(part))
        found.append((version, fields))
    if not found:
        raise ValueError('The repository has no NCPA package')
    newest = max(found, key=lambda item: item[0])[1]
    # Only the downloaded package's path is used, and old entries are not all alike.
    if not PACKAGE_PATH.fullmatch(newest.get('Filename', '')):
        raise ValueError('Unexpected NCPA package path')
    return newest


def check(data: bytes, expected: str, name: str) -> None:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(name + ' does not match its published checksum')


def mirror(root: Path, codename: str, fetch=download, verify=verify_signature) -> str:
    """Write the mirror under root in the same layout as the real server."""
    if not re.fullmatch(r'[a-z]+', codename):
        raise ValueError('Invalid release codename')
    repository = root / 'deb' / codename
    repository.mkdir(parents=True, exist_ok=True)
    (root / KEY).write_bytes(fetch(BASE + '/' + KEY))
    files = {}
    for name in INDEX_FILES:
        files[name] = fetch(f'{BASE}/deb/{codename}/{name}')
        (repository / name).write_bytes(files[name])
    verify(root / KEY, repository / 'InRelease')
    release = files['InRelease'].decode()
    for name in ('Packages', 'Packages.gz'):
        check(files[name], signed_hash(release, name), name)
    package = newest_ncpa(files['Packages'].decode())
    data = fetch(f"{BASE}/deb/{codename}/{package['Filename']}")
    check(data, package.get('SHA256', ''), package['Filename'])
    target = repository / package['Filename']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return package['Version']


if __name__ == '__main__':
    version = mirror(Path(sys.argv[1]), sys.argv[2])
    print('Mirrored NCPA', version)
