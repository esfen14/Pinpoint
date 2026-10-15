"""Native plugin passwords travel on stdin, never in parent or child argv."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import time

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/pinpoint_check_native.py"


def adapter():
    spec = importlib.util.spec_from_file_location("native_resource_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    resource = tmp_path / "resource.cfg"
    resource.write_text("# BEGIN PINPOINT\n$USER2$=synthetic-native-password\n# END PINPOINT\n")
    resource.chmod(0o660)
    plugin = tmp_path / "check_mysql_query"
    plugin.write_text(f'''#!{sys.executable}
import sys
if '--help' in sys.argv:
    print('--extra-opts=[section]@file')
    sys.exit(0)
assert '--extra-opts=pinpoint@-' in sys.argv
data = sys.stdin.read()
assert data == '[pinpoint]\\npassword=synthetic-native-password\\n'
print('OK: rows | rows=2;10;20')
''')
    plugin.chmod(0o755)
    return resource, plugin


def arguments(inputs):
    return ["--resource-file", str(inputs[0]), "--plugin", str(inputs[1]),
            "--resource-slot", "USER2", "-H", "127.0.0.1", "-q", "SELECT 1", "-w", "10", "-c", "20"]


def test_native_extra_opts_receives_password_on_stdin_and_preserves_result(inputs):
    assert adapter().run(arguments(inputs)) == ("OK: rows | rows=2;10;20", 0)


def test_nt_uses_the_secret_ini_key(inputs):
    resource, plugin = inputs
    nt = plugin.with_name('check_nt')
    nt.write_text(plugin.read_text().replace('password=synthetic', 'secret=synthetic'))
    nt.chmod(0o755)
    assert adapter().run(["--resource-file", str(resource), "--plugin", str(nt),
                          "--resource-slot", "USER2", "-H", "127.0.0.1", "-v", "UPTIME"])[1] == 0


def test_unsupported_extra_opts_build_is_blocked(inputs):
    plugin = inputs[1]
    plugin.write_text(plugin.read_text().replace('--extra-opts=[section]@file', 'no secure input'))
    assert adapter().run(arguments(inputs)) == ("UNKNOWN: Installed plugin lacks extra-options support.", 3)


@pytest.mark.parametrize("flag", ["-p", "--password", "--pass", "--extra-opts", "-v", "--verbose"])
def test_native_secret_and_diagnostic_options_cannot_bypass_transport(inputs, flag):
    assert adapter().run(arguments(inputs) + [flag, 'literal'])[1] == 3


def test_unsupported_smb_plugin_is_explicitly_blocked(inputs):
    resource, plugin = inputs
    smb = plugin.with_name('check_disk_smb')
    smb.write_text(plugin.read_text()); smb.chmod(0o755)
    assert adapter().run(arguments((resource, smb)))[1] == 3


def test_native_password_cannot_be_trimmed_by_ini_parser(inputs):
    inputs[0].write_text("# BEGIN PINPOINT\n$USER2$= password \n# END PINPOINT\n")
    assert adapter().run(arguments(inputs))[1] == 3


def test_native_secret_output_is_suppressed(inputs):
    plugin = inputs[1]
    plugin.write_text(plugin.read_text().replace("print('OK: rows | rows=2;10;20')", "print(data)"))
    output, code = adapter().run(arguments(inputs))
    assert code == 3 and 'synthetic-native-password' not in output


@pytest.mark.parametrize("command,expected", [
    ("pinpoint_custom_check_radius!probe!probe!/etc/radius.conf!",
     "pinpoint_custom_check_radius!probe!USER2!/etc/radius.conf!"),
    ("pinpoint_custom_check_mysql_query!SELECT probe!10!20!-u 'probe' -p 'probe'",
     "pinpoint_custom_check_mysql_query!SELECT probe!10!20!-u 'probe' --resource-slot 'USER2'"),
    ("pinpoint_custom_check_nt!UPTIME!-s 'probe' -p '1248'",
     "pinpoint_custom_check_nt!UPTIME!--resource-slot 'USER2' -p '1248'"),
])
def test_generated_custom_commands_use_unexpanded_slot_identifiers(command, expected):
    from app.network_discovery.create_host_cfg import apply_secret_substitutions
    assert apply_secret_substitutions(command, {"probe": "$USER2$"}) == expected


def test_smb_secret_generation_refuses_without_publishing_unsafe_command():
    from app.network_discovery.create_host_cfg import apply_secret_substitutions
    from app.network_discovery.plugin_registry import PluginConfigurationError
    with pytest.raises(PluginConfigurationError, match="secure credential input"):
        apply_secret_substitutions("pinpoint_custom_check_disk_smb!share!-p 'probe'", {"probe": "$USER2$"})


@pytest.mark.skipif(not Path('/proc/self/cmdline').exists(), reason="Linux process inspection")
def test_parent_and_child_process_arguments_do_not_contain_password(inputs, tmp_path):
    ready, release = tmp_path / "ready", tmp_path / "release"
    plugin = inputs[1]
    # The fixture checks the credential received on stdin before holding open.
    plugin.write_text(plugin.read_text().replace("print('OK: rows | rows=2;10;20')", f'''
from pathlib import Path
import time, os
Path({str(ready)!r}).write_text(str(os.getpid()))
deadline = time.monotonic() + 10
while not Path({str(release)!r}).exists():
    if time.monotonic() > deadline: sys.exit(3)
    time.sleep(0.01)
print('OK: rows | rows=2;10;20')
'''))
    parent = subprocess.Popen([sys.executable, '-I', str(SCRIPT), *arguments(inputs)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and parent.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), parent.communicate(timeout=1)
        child_pid = int(ready.read_text())
        for pid in (parent.pid, child_pid):
            assert b'synthetic-native-password' not in Path(f'/proc/{pid}/cmdline').read_bytes()
        assert '--extra-opts=pinpoint@-' in Path(f'/proc/{child_pid}/cmdline').read_text()
        release.touch()
        stdout, stderr = parent.communicate(timeout=5)
        assert parent.returncode == 0 and stderr == ''
        assert stdout.strip() == 'OK: rows | rows=2;10;20'
    finally:
        release.touch()
        if parent.poll() is None:
            parent.kill(); parent.communicate()
