"""`scripts/vmlab` stops the lab VM's automatic upgrades before it installs anything (#350).

Fake VBoxManage, SSH, systemctl and fuser only; no VM is touched.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
GUEST_SCRIPT = REPO / 'lab/stop_auto_upgrades.sh'


class Fakes(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'bin').mkdir()
        self.log = self.root / 'log'

    def executable(self, name, content):
        path = self.root / 'bin' / name
        path.write_text(content)
        path.chmod(0o700)

    def environment(self, **extra):
        path = str(self.root / 'bin') + ':' + os.environ['PATH']
        return dict(os.environ, PATH=path, FAKE_LOG=str(self.log), **extra)


class GuestScriptTests(Fakes):
    """The script that runs inside the appliance."""

    def setUp(self):
        super().setUp()
        # fuser succeeds (lock held) for the first FAKE_BUSY calls.
        self.executable('fuser', '''#!/bin/sh
count=$(cat "$FAKE_LOG.count" 2>/dev/null || echo 0)
count=$((count + 1))
echo "$count" > "$FAKE_LOG.count"
echo "fuser" >> "$FAKE_LOG"
[ "$count" -le "$FAKE_BUSY" ]
''')
        # is-active reports a running upgrade service for the first FAKE_ACTIVE calls.
        self.executable('systemctl', '''#!/bin/sh
echo "systemctl $*" >> "$FAKE_LOG"
[ "$1" = "is-active" ] || exit 0
count=$(cat "$FAKE_LOG.active" 2>/dev/null || echo 0)
count=$((count + 1))
echo "$count" > "$FAKE_LOG.active"
if [ "$count" -le "$FAKE_ACTIVE" ]; then echo activating; else echo inactive; echo inactive; fi
exit 3
''')
        self.executable('sleep', '#!/bin/sh\nexit 0\n')
        self.apt_dir = self.root / 'apt.conf.d'
        self.apt_dir.mkdir()

    def run_script(self, busy=0, active=0, limit='600'):
        env = self.environment(FAKE_BUSY=str(busy), FAKE_ACTIVE=str(active),
                               VMLAB_APT_CONF_DIR=str(self.apt_dir), VMLAB_UPGRADE_WAIT_SECONDS=limit)
        return subprocess.run(['bash', str(GUEST_SCRIPT)], env=env, capture_output=True, text=True, timeout=60)

    def test_disables_new_runs_before_waiting(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        config = (self.apt_dir / '99-vmlab-no-auto-upgrades').read_text()
        self.assertIn('APT::Periodic::Enable "0";', config)
        lines = self.log.read_text().splitlines()
        self.assertEqual(lines[0], 'systemctl disable --now apt-daily.timer apt-daily-upgrade.timer')

    def test_waits_while_a_package_lock_is_held(self):
        result = self.run_script(busy=3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines().count('fuser'), 4)
        self.assertIn('waiting', result.stdout)

    def test_waits_while_an_upgrade_service_runs_without_the_lock(self):
        result = self.run_script(active=2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('waiting', result.stdout)
        self.assertEqual((self.root / 'log.active').read_text().strip(), '3')

    def test_never_stops_or_kills_a_running_upgrade(self):
        self.run_script(busy=2)
        log = self.log.read_text()
        self.assertNotIn('systemctl stop', log)
        self.assertNotIn('systemctl kill', log)

    def test_fails_when_the_lock_is_never_released(self):
        result = self.run_script(busy=1000, limit='30')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('still running', result.stderr)


class VmlabOrderTests(Fakes):
    """`fresh` and `provision` run the guest script before any installer step."""

    def setUp(self):
        super().setUp()
        for name in ['scripts', 'lab', 'state', 'installer/setup']:
            (self.root / name).mkdir(parents=True)
        shutil.copyfile(REPO / 'scripts/vmlab', self.root / 'scripts/vmlab')
        (self.root / 'scripts/vmlab').chmod(0o700)
        shutil.copyfile(GUEST_SCRIPT, self.root / 'lab/stop_auto_upgrades.sh')
        control = (REPO / 'scripts/qa_control.py').read_text()
        control = control.replace("return Path('/tmp') / f'pinpoint-qa-control-{os.getuid()}'",
                                  'return Path(' + repr(str(self.root / 'control')) + ')')
        (self.root / 'scripts/qa_control.py').write_text(control)
        (self.root / 'scripts/vmlab_preflight.py').write_text('')
        for module in ['install-packages.sh', 'install-nagios-core.sh', 'install-nagios-plugins.sh',
                       'configure-snmp.sh', 'configure-nagios.sh']:
            (self.root / 'installer/setup' / module).write_text('')
        (self.root / 'config').write_text('VMLAB_INSTALLER_DIR="%s"\n' % (self.root / 'installer'))
        self.executable('git', '''#!/bin/sh
case "$*" in
  *"remote get-url"*) echo https://example.invalid/repo.git ;;
esac
exit 0
''')
        # "running" until a power-off is requested, then "poweroff" until started.
        self.executable('VBoxManage', '''#!/bin/sh
state="$FAKE_LOG.state"
case "$*" in
  showvminfo*) echo "VMState=\\"$(cat "$state" 2>/dev/null || echo poweroff)\\"" ;;
  controlvm*) echo poweroff > "$state" ;;
  startvm*) echo running > "$state" ;;
  *"list --machinereadable"*) [ -n "$FAKE_NO_SNAPSHOT" ] || echo 'SnapshotName="os-nagios-ready"' ;;
esac
exit 0
''')
        # Record each remote command; keep the stdin of the guest-script call.
        self.executable('ssh', '''#!/bin/sh
for last; do :; done
echo "$last" >> "$FAKE_LOG"
case "$last" in
  "sudo bash -s") cat > "$FAKE_LOG.stdin"; exit "$FAKE_GUEST_STATUS" ;;
  *"tar -C"*) cat > /dev/null ;;
esac
exit 0
''')

    def run_vmlab(self, *args, guest_status='0', no_snapshot=''):
        env = self.environment(VMLAB_CONFIG=str(self.root / 'config'), VMLAB_STATE_DIR=str(self.root / 'state'),
                               FAKE_GUEST_STATUS=guest_status, FAKE_NO_SNAPSHOT=no_snapshot)
        env.pop('PINPOINT_QA_CONTROL_PID', None)
        env.pop('PINPOINT_QA_CONTROL_FD', None)
        return subprocess.run(['bash', str(self.root / 'scripts/vmlab'), *args], env=env,
                              capture_output=True, text=True, timeout=60)

    def first_index(self, lines, text):
        for index, line in enumerate(lines):
            if text in line:
                return index
        self.fail('no remote command contains %r in %r' % (text, lines))

    def assert_guest_script_runs_before(self, module):
        lines = self.log.read_text().splitlines()
        self.assertLess(self.first_index(lines, 'sudo bash -s'), self.first_index(lines, module))
        sent = (self.root / 'log.stdin').read_text()
        self.assertEqual(sent, GUEST_SCRIPT.read_text())

    def test_fresh_stops_upgrades_before_the_app_install(self):
        result = self.run_vmlab('fresh', 'some-branch')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_guest_script_runs_before('deploy-pinpoint-web.sh')

    def test_provision_stops_upgrades_before_the_base_install(self):
        result = self.run_vmlab('provision', no_snapshot='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_guest_script_runs_before('install-packages.sh')

    def test_fresh_installs_nothing_when_the_wait_fails(self):
        result = self.run_vmlab('fresh', 'some-branch', guest_status='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('deploy-pinpoint-web.sh', self.log.read_text())


if __name__ == '__main__':
    unittest.main()
