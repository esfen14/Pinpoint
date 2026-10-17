"""Opt-in #173 real Nagios routed acceptance; creates only disposable Docker resources.

Run explicitly from the repository root; never collected by the isolated pytest suite.
No scans, credentials, shared lab mutation, SMTP delivery, or host route changes.
"""

import argparse
import json
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


def run(*args, check=True):
    """Execute a fixed argument vector and return captured output."""
    result = subprocess.run(args, text=True, capture_output=True, timeout=60)
    if check and result.returncode:
        raise RuntimeError(f"Command {args[:3]} failed: {result.stderr}")
    return result.stdout


def wait_for(predicate, description, timeout=35):
    """Wait for observed daemon evidence, failing rather than accepting stale state."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(0.25)
    raise AssertionError(f"Timed out: {description}")


def host_states(path):
    """Read Nagios status blocks; an absent/partial status file is not a pass."""
    if not path.exists():
        return {}
    result = {}
    for block in re.findall(r"hoststatus \{(.*?)\n\s*\}", path.read_text(), re.S):
        fields = dict(re.findall(r"^\s*(\w+)=(.*)$", block, re.M))
        result[fields['host_name']] = fields
    return result


def object_block(kind, fields):
    """Render fixed test-owned object directives without shell interpolation."""
    return f"define {kind} {{\n" + ''.join(f"  {key} {value}\n" for key, value in fields.items()) + '}\n'


def config(directory, redundant):
    """Write exact daemon and object settings for the private one-attempt trial."""
    settings = {
        'log_file': '/evidence/nagios.log', 'cfg_file': '/evidence/objects.cfg',
        'object_cache_file': '/evidence/objects.cache', 'status_file': '/evidence/status.dat',
        'command_file': '/evidence/nagios.cmd', 'lock_file': '/evidence/nagios.lock',
        'temp_file': '/evidence/nagios.tmp', 'temp_path': '/evidence',
        'check_result_path': '/evidence/results', 'log_archive_path': '/evidence',
        'state_retention_file': '/evidence/retention.dat',
        'nagios_user': 'nagios', 'nagios_group': 'nagios',
        'interval_length': 2, 'cached_host_check_horizon': 15,
        'cached_service_check_horizon': 15, 'status_update_interval': 1,
        'check_external_commands': 1, 'command_check_interval': -1,
        'execute_host_checks': 1, 'execute_service_checks': 0,
        'accept_passive_host_checks': 0, 'accept_passive_service_checks': 0,
        'enable_notifications': 1, 'enable_event_handlers': 0,
        'enable_flap_detection': 0, 'retain_state_information': 0,
        'log_initial_states': 1, 'log_host_retries': 1,
        'log_notifications': 1, 'log_external_commands': 1,
        'log_rotation_method': 'n', 'use_syslog': 0,
        'check_for_updates': 0, 'host_check_timeout': 4,
        'service_check_timeout': 4, 'notification_timeout': 4,
    }
    (directory / 'nagios.cfg').write_text(''.join(f'{k}={v}\n' for k, v in settings.items()))
    objects = object_block('timeperiod', {
        'timeperiod_name': 'always', 'alias': 'always',
        **{day: '00:00-24:00' for day in ('sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday')},
    })
    objects += object_block('command', {
        'command_name': 'ping-host',
        'command_line': '/usr/local/nagios/libexec/check_ping -H $HOSTADDRESS$ -w 5000,100% -c 5000,100% -p 1 -t 2',
    })
    objects += object_block('command', {
        'command_name': 'record-notification', 'command_line': '/bin/true',
    })
    objects += object_block('command', {'command_name': 'local-ok', 'command_line': '/bin/true'})
    objects += object_block('contact', {
        'contact_name': 'sink', 'alias': 'disposable sink',
        'host_notification_period': 'always', 'service_notification_period': 'always',
        'host_notification_options': 'd,u,r', 'service_notification_options': 'w,u,c,r',
        'host_notification_commands': 'record-notification',
        'service_notification_commands': 'record-notification',
    })
    addresses = {'parent-a': '10.77.0.3', 'child': '10.77.0.10', 'no-parent': '10.77.0.10'}
    if redundant:
        addresses['parent-b'] = '10.77.0.4'
    for name, address in addresses.items():
        fields = {
            'host_name': name, 'alias': name, 'address': address,
            'check_command': 'ping-host', 'check_period': 'always',
            'max_check_attempts': 1, 'check_interval': 60, 'retry_interval': 1,
            # Forced active checks provide controlled order; normal scheduling is disabled.
            'active_checks_enabled': 0, 'passive_checks_enabled': 0,
            'notifications_enabled': 1, 'notification_period': 'always',
            'notification_options': 'd,u,r', 'notification_interval': 0,
            'first_notification_delay': 0, 'contacts': 'sink',
        }
        if name == 'child':
            fields['parents'] = 'parent-a,parent-b' if redundant else 'parent-a'
        objects += object_block('host', fields)
    # Core requires at least one service; it does not drive these host checks.
    objects += object_block('service', {
        'host_name': 'parent-a', 'service_description': 'local-control',
        'check_command': 'local-ok', 'check_period': 'always',
        'max_check_attempts': 1, 'check_interval': 60, 'retry_interval': 1,
        'active_checks_enabled': 0, 'notifications_enabled': 0,
        'notification_period': 'always', 'notification_interval': 0, 'contacts': 'sink',
    })
    (directory / 'objects.cfg').write_text(objects)
    (directory / 'settings.json').write_text(json.dumps(settings, indent=2))


def trial(args, output, redundant):
    """Exercise real routed loss, temporary DOWN, confirmed UNREACHABLE and recovery."""
    label = 'redundant' if redundant else 'single'
    directory = output / label
    directory.mkdir(mode=0o777)
    directory.chmod(0o777)
    (directory / 'results').mkdir(mode=0o777)
    (directory / 'results').chmod(0o777)
    config(directory, redundant)
    prefix = 'pinpoint173-' + uuid.uuid4().hex[:10]
    containers, networks = [], []
    events = []

    def docker(*command):
        return run('docker', *command)

    def snapshot(phase):
        states = host_states(directory / 'status.dat')
        data = {'phase': phase, 'time': time.time(), 'states': states}
        events.append(data)
        (directory / 'observations.json').write_text(json.dumps(events, indent=2))
        return states

    def force(host):
        # last_check has one-second resolution; ensure the new result is distinguishable.
        time.sleep(1.05)
        requested = int(time.time())
        command = f'[{requested}] SCHEDULE_FORCED_HOST_CHECK;{host};{requested}\n'
        subprocess.run(['docker', 'exec', '-i', engine, 'tee', '/evidence/nagios.cmd'],
                       input=command, text=True, capture_output=True, check=True, timeout=10)
        return wait_for(lambda: (state if (state := host_states(directory / 'status.dat').get(host))
                                 and int(state.get('last_check', 0)) >= requested else None),
                        f'fresh active result for {host}')

    def assert_state(host, expected):
        state = host_states(directory / 'status.dat')[host]
        assert int(state['current_state']) == expected, (host, state)
        assert state['state_type'] == '1', (host, 'not HARD', state)
        assert int(state['last_check']) > 0

    try:
        for suffix, subnet in [('up', '10.77.0.0/29'), ('down', '10.77.0.8/29')]:
            name = prefix + '-' + suffix
            docker('network', 'create', '--internal', '--subnet', subnet, name)
            networks.append(name)
        up, down = networks

        def container(suffix, image, network, address, mount=False):
            name = prefix + '-' + suffix
            command = ['run', '-d', '--name', name, '--network', network, '--ip', address,
                       '--cap-add', 'NET_ADMIN', '--sysctl', 'net.ipv4.ip_forward=1']
            if mount:
                command += ['-v', f'{directory}:/evidence']
            command += ['--entrypoint', 'sleep', image, 'infinity']
            docker(*command)
            containers.append(name)
            return name

        engine = container('engine', args.appliance_image, up, '10.77.0.2', True)
        router_a = container('router-a', args.router_image, up, '10.77.0.3')
        docker('network', 'connect', '--ip', '10.77.0.11', down, router_a)
        router_b = None
        if redundant:
            router_b = container('router-b', args.router_image, up, '10.77.0.4')
            docker('network', 'connect', '--ip', '10.77.0.12', down, router_b)
        child = container('target', args.router_image, down, '10.77.0.10')
        docker('exec', engine, 'ip', 'route', 'replace', '10.77.0.8/29', 'via', '10.77.0.3')
        docker('exec', child, 'ip', 'route', 'replace', '10.77.0.0/29', 'via', '10.77.0.11')
        (directory / 'version.txt').write_text(docker('exec', engine, '/usr/local/nagios/bin/nagios', '--version'))
        (directory / 'validation.txt').write_text(docker('exec', '-u', 'nagios', engine,
                                                       '/usr/local/nagios/bin/nagios', '-v', '/evidence/nagios.cfg'))
        docker('exec', '-u', 'nagios', engine, '/usr/local/nagios/bin/nagios', '-d', '/evidence/nagios.cfg')
        wait_for(lambda: (directory / 'nagios.cmd').exists(), 'external command FIFO')
        for host in (['parent-a', 'parent-b'] if redundant else ['parent-a']) + ['child', 'no-parent']:
            force(host)
            assert_state(host, 0)
        snapshot('baseline-up')
        if redundant:
            # Parents express reachability, not route failover; explicitly select the alternate path.
            docker('exec', engine, 'ip', 'route', 'replace', '10.77.0.8/29', 'via', '10.77.0.4')
            docker('exec', child, 'ip', 'route', 'replace', '10.77.0.0/29', 'via', '10.77.0.12')
            docker('stop', '-t', '0', router_a)
            force('parent-a')
            force('child')
            assert_state('child', 0)
            snapshot('alternate-parent-up')
        remaining = 'parent-b' if redundant else 'parent-a'
        force(remaining)  # Fresh UP in the cache immediately before the physical path fails.
        docker('stop', '-t', '0', router_b if redundant else router_a)
        force('child')
        assert_state('child', 1)
        snapshot('transient-child-down')
        log = directory / 'nagios.log'
        wait_for(lambda: 'HOST NOTIFICATION: sink;child;DOWN;' in log.read_text(), 'child DOWN notification')
        force(remaining)
        assert_state(remaining, 1)
        force('child')
        assert_state('child', 2)
        force('no-parent')
        assert_state('no-parent', 1)
        snapshot('confirmed-unreachable-and-no-parent-down')
        wait_for(lambda: 'HOST NOTIFICATION: sink;child;UNREACHABLE;' in log.read_text(),
                 'child UNREACHABLE notification')
        docker('start', router_b if redundant else router_a)
        force(remaining)
        force('child')
        force('no-parent')
        assert_state('child', 0)
        assert_state('no-parent', 0)
        snapshot('recovered-up')
        lines = [line for line in log.read_text().splitlines() if 'HOST ALERT:' in line or 'HOST NOTIFICATION:' in line]
        (directory / 'state-and-notification-events.log').write_text('\n'.join(lines) + '\n')
        print(f'{label}: PASS (HARD DOWN notification -> UNREACHABLE -> UP; no-parent DOWN control)', flush=True)
    finally:
        for name in reversed(containers):
            run('docker', 'rm', '-f', name, check=False)
        for name in reversed(networks):
            run('docker', 'network', 'rm', name, check=False)
        # Record any cleanup failure; never delete arbitrary resources or ignore leftovers.
        leftovers = run('docker', 'ps', '-a', '--filter', f'name={prefix}', '--format', '{{.Names}}').strip()
        remaining_networks = run('docker', 'network', 'ls', '--filter', f'name={prefix}', '--format', '{{.Name}}').strip()
        (directory / 'cleanup.json').write_text(json.dumps({'containers': leftovers, 'networks': remaining_networks}))
        assert not leftovers and not remaining_networks, 'Owned Docker resources remain'


def main():
    """Require an explicit run flag and keep raw evidence outside the repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True, help='Explicitly authorize disposable Docker trials')
    parser.add_argument('--appliance-image', default='pinpoint-lab-appliance:latest')
    parser.add_argument('--router-image', default='pinpoint-issue117-routing:latest')
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    output = args.output_root or Path(tempfile.mkdtemp(prefix='pinpoint173-evidence-'))
    output.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    repository = Path(__file__).resolve().parents[3]
    if output == repository or repository in output.parents:
        parser.error('--output-root must be outside the repository (raw evidence is not committed)')
    output.chmod(0o755)
    metadata = {
        'commit': run('git', '-C', str(repository), 'rev-parse', 'HEAD').strip(),
        'images': {image: run('docker', 'image', 'inspect', '--format', '{{.Id}}', image).strip()
                   for image in (args.appliance_image, args.router_image)},
    }
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    print(f'Evidence: {output}', flush=True)
    for redundant in (False, True):
        trial(args, output, redundant)


if __name__ == '__main__':
    main()
