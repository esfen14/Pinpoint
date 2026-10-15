"""Read-only Linux host proof that VBoxManage and lab listeners share one VM."""
import argparse
import ipaddress
import os
from pathlib import Path
import subprocess
import sys


def validate(info, managers, processes, listeners, ports):
    """Reject ambiguous controller, session or TCP socket ownership observations."""
    if len(managers) != 1:
        raise ValueError('expected exactly one VBoxSVC for this user; duplicate or missing control context')
    uuid = info.get('UUID')
    if not uuid:
        raise ValueError('VirtualBox did not provide the appliance UUID')
    matching = {pid: p for pid, p in processes.items() if p['uuid'].lower() == uuid.lower()}
    state = info.get('VMState')
    if state == 'poweroff':
        if matching or any(listeners.get(port) for port in ports):
            raise ValueError('manager reports poweroff but a VM process or lab listener remains')
        return
    if state != 'running':
        raise ValueError('VM state is ambiguous; only running or poweroff is accepted')
    if len(matching) != 1:
        raise ValueError('expected exactly one process for the appliance UUID')
    pid, process = next(iter(matching.items()))
    if info.get('SessionPID') != str(pid) or process['parent'] != managers[0]:
        raise ValueError('SessionPID/process/controller ownership does not agree')
    for port in ports:
        rows = listeners.get(port, [])
        if len(rows) != 1 or rows[0][0] != '127.0.0.1' or rows[0][1] not in process['sockets']:
            raise ValueError(f'cannot prove exclusive loopback listener ownership on port {port}')


def inventory():
    """Read same-user VBox processes from host procfs, failing on hidden metadata."""
    if Path('/proc/1/comm').read_text().strip() not in {'systemd', 'init'}:
        raise ValueError('run preflight on the Linux host, outside a container or PID sandbox')
    managers, processes = [], {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            status = dict(line.split(':', 1) for line in (path / 'status').read_text().splitlines() if ':' in line)
            if int(status['Uid'].split()[0]) != os.getuid():
                continue
            name = status['Name'].strip()
            if name == 'VBoxSVC':
                managers.append(int(path.name))
            elif name in {'VBoxHeadless', 'VirtualBoxVM'}:
                args = (path / 'cmdline').read_bytes().decode().split('\0')
                if '--startvm' not in args or args.index('--startvm') + 1 >= len(args):
                    raise ValueError('cannot identify a running VirtualBox process')
                processes[int(path.name)] = {'uuid': args[args.index('--startvm') + 1],
                                             'parent': int(status['PPid']), 'path': path}
        except FileNotFoundError:
            continue  # A process exited during the read; later checks still require positive proof.
    return managers, processes


def tcp_listeners(ports):
    """Read listening socket inodes for both address families, including conflicts."""
    result = {}
    for family in ['tcp', 'tcp6']:
        for line in Path('/proc/net', family).read_text().splitlines()[1:]:
            fields = line.split()
            address, port_hex = fields[1].split(':')
            port = int(port_hex, 16)
            if fields[3] != '0A' or port not in ports:
                continue
            raw = bytes.fromhex(address)
            raw = b''.join(raw[i:i + 4][::-1] for i in range(0, len(raw), 4))
            result.setdefault(port, []).append((str(ipaddress.ip_address(raw)), f'socket:[{fields[9]}]'))
    return result


def main():
    """Inspect controller metadata and prove ownership without SSH or VM mutation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new', action='store_true', help='require an unused VM name and no running VM processes')
    parser.add_argument('vm')
    parser.add_argument('ssh_target')
    parser.add_argument('ssh_port', type=int)
    parser.add_argument('web_port', type=int)
    args = parser.parse_args()
    try:
        ports = [args.ssh_port, args.web_port]
        if args.ssh_target.rsplit('@', 1)[-1] != '127.0.0.1' or len(set(ports)) != 2 or any(p < 1 or p > 65535 for p in ports):
            raise ValueError('preflight requires distinct valid ports and an explicit 127.0.0.1 SSH target')
        managers, initial_processes = inventory()
        if len(managers) > 1:
            raise ValueError('duplicate VBoxSVC control contexts; do not start/stop or restore any VM')
        if args.new:
            registered = subprocess.run(['VBoxManage', 'list', 'vms'], capture_output=True,
                                        text=True, timeout=20, check=True).stdout
            if any(line.startswith('"' + args.vm + '" ') for line in registered.splitlines()):
                raise ValueError('the requested new VM already exists')
            managers, processes = inventory()
            if len(managers) != 1 or initial_processes or processes or tcp_listeners(ports):
                raise ValueError('creation requires unambiguous control, no running VMs and unused ports')
            print('Preflight passed: new VM name, unused endpoints and exclusive control.')
            return 0
        proc = subprocess.run(['VBoxManage', 'showvminfo', args.vm, '--machinereadable'],
                              capture_output=True, text=True, timeout=20, check=True)
        info = dict((key, value.strip('"')) for key, value in
                    (line.split('=', 1) for line in proc.stdout.splitlines() if '=' in line))
        managers, processes = inventory()
        for process in processes.values():
            process['sockets'] = set()
            if process['uuid'].lower() == info.get('UUID', '').lower():
                process['sockets'] = {os.readlink(fd) for fd in (process['path'] / 'fd').iterdir()}
        validate(info, managers, processes, tcp_listeners(ports), ports)
        print(f"Preflight passed: VM {info['UUID']} ({info['VMState']}), exclusive control and endpoint ownership.")
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        # Do not echo command lines, environment, credentials or raw subprocess output.
        print('vmlab: preflight FAILED: ownership is ambiguous or metadata is inaccessible; '
              'inspect host VBoxSVC/VM processes and loopback socket ownership before any mutation.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
