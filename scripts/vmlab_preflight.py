"""Read-only Linux host proof that VBoxManage and lab listeners share one VM."""
import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
import re
from pathlib import Path
import subprocess
import sys


def validate(info, managers, processes, listeners, ports, forwards):
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
    if (info.get('SessionPID') and info['SessionPID'] != str(pid)) or process['parent'] != managers[0]:
        raise ValueError('SessionPID/process/controller ownership does not agree')
    for port, guest_port in zip(ports, [22, 80]):
        rows = listeners.get(port, [])
        if len(rows) != 1 or rows[0][0] != '127.0.0.1':
            raise ValueError(f'cannot prove exclusive loopback listener ownership on port {port}')
        runtime = forwards.get(port, [])
        if len(runtime) != 1 or runtime[0][:2] != ('127.0.0.1', guest_port):
            raise ValueError(f'controlled VM has no unique active forwarding socket on port {port}')
    if forwards[ports[0]][0][2] != forwards[ports[1]][0][2]:
        raise ValueError('SSH and web forwarding sockets target different guests')


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
                                             'parent': int(status['PPid']), 'path': path,
                                             'start_ticks': process_start(path),
                                             'controller_start_ticks': process_start(Path('/proc') / status['PPid'].strip())}
        except FileNotFoundError:
            continue  # A process exited during the read; later checks still require positive proof.
    return managers, processes


def process_start(path):
    """Include kernel start ticks so a reused PID cannot preserve a running claim."""
    try:
        fields = (path / 'stat').read_text().rsplit(') ', 1)[1].split()
        value = int(fields[19])
        if value < 1:
            raise ValueError()
        return value
    except (IndexError, ValueError):
        raise ValueError('Unavailable process start identity') from None


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


def endpoint_check(ssh_target, ports):
    if (ssh_target.rsplit('@', 1)[-1] != '127.0.0.1' or len(ports) != 2
            or len(set(ports)) != 2 or any(type(p) is not int or p < 1 or p > 65535 for p in ports)):
        raise ValueError('preflight requires distinct valid ports and an explicit 127.0.0.1 SSH target')


def vm_info(vm):
    result = subprocess.run(['VBoxManage', 'showvminfo', vm, '--machinereadable'],
                            capture_output=True, text=True, timeout=20, check=True)
    return dict((key, value.strip('"')) for key, value in
                (line.split('=', 1) for line in result.stdout.splitlines() if '=' in line))


def observe(vm, ssh_target, ports):
    """Collect real host ownership metadata, never deployment/baseline proof.

    Commands are read-only and individually bounded. Callers must still bound
    total collection time and hold the cooperative control lock during live use.
    No SSH, HTTP, credential access or application readiness claim is performed.
    """
    endpoint_check(ssh_target, ports)
    managers, _ = inventory()
    if len(managers) > 1:
        raise ValueError('Duplicate controller contexts')
    info = vm_info(vm)
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', info.get('UUID', '').lower()):
        raise ValueError('Canonical appliance UUID missing')
    managers, processes = inventory()
    forwards = {}
    if info.get('VMState') == 'running':
        runtime = subprocess.run(['VBoxManage', 'debugvm', vm, 'info', 'nat0'],
                                 capture_output=True, text=True, timeout=20, check=True)
        forwards = nat_forwards(runtime.stdout)
    final_info = vm_info(vm)
    final_managers, final_processes = inventory()
    if (any(info.get(k) != final_info.get(k) for k in ('UUID', 'VMState', 'SessionPID'))
            or final_managers != managers or final_processes != processes):
        raise ValueError('VM/controller identity changed during observation')
    validate(info, managers, processes, tcp_listeners(ports), ports, forwards)
    matching = [pid for pid, process in processes.items() if process['uuid'].lower() == info['UUID'].lower()]
    identity = processes[matching[0]] if matching else {}
    return dict(version=1, lab_uuid=info['UUID'].lower(), state=info['VMState'],
                controller_pid=managers[0], vm_pid=matching[0] if matching else None,
                vm_start_ticks=identity.get('start_ticks'),
                controller_start_ticks=identity.get('controller_start_ticks'),
                origin=f'http://127.0.0.1:{ports[1]}', ssh_port=ports[0],
                observed_at=datetime.now(timezone.utc).isoformat(), host_ownership_verified=True,
                running_endpoints_verified=info['VMState'] == 'running', live_authorized=False)



def nat_forwards(text):
    """Parse only active TCP host-forward sockets from the VM runtime NAT debugger."""
    result = {}
    pattern = r'^\s*TCP\[HOST_FORWARD\]\s+(\d+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(\d+)\s+'
    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            fd, host, port, guest, guest_port = match.groups()
            if int(fd) < 0:
                raise ValueError('invalid runtime forwarding descriptor')
            ipaddress.ip_address(host)
            ipaddress.ip_address(guest)
            result.setdefault(int(port), []).append((host, int(guest_port), guest))
    return result

def main():
    """Inspect controller metadata and prove ownership without SSH or VM mutation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new', action='store_true', help='require an unused VM name and no running VM processes')
    parser.add_argument('--json', action='store_true', help='structured host observation only; no application identity or live authorization')
    parser.add_argument('vm')
    parser.add_argument('ssh_target')
    parser.add_argument('ssh_port', type=int)
    parser.add_argument('web_port', type=int)
    args = parser.parse_args()
    try:
        ports = [args.ssh_port, args.web_port]
        endpoint_check(args.ssh_target, ports)
        if args.json and args.new:
            raise ValueError('Structured observations require an existing appliance')
        if not args.new:
            receipt = observe(args.vm, args.ssh_target, ports)
            if args.json:
                print(json.dumps(receipt, sort_keys=True))
            else:
                print(f"Preflight passed: VM {receipt['lab_uuid']} ({receipt['state']}), exclusive control and endpoint ownership.")
            return 0
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
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        # Do not echo command lines, environment, credentials or raw subprocess output.
        print('vmlab: preflight FAILED: ownership is ambiguous or metadata is inaccessible; '
              'inspect host VBoxSVC/VM processes and loopback socket ownership before any mutation.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
