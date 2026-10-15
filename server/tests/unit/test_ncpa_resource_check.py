"""NCPA credential transport: private storage, real argv and safe plugin results."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/pinpoint_check_ncpa.py"


def adapter():
    spec = importlib.util.spec_from_file_location("ncpa_resource_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    resource = tmp_path / "resource.cfg"
    resource.write_text("$USER1$=/plugins\n# BEGIN PINPOINT\n$USER2$=synthetic token&value\n# END PINPOINT\n")
    resource.chmod(0o660)
    plugin = tmp_path / "check_ncpa.py"
    plugin.write_text('''import optparse
__VERSION__ = '1.2.4'
def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-H')
    parser.add_option('-M')
    parser.add_option('-P')
    parser.add_option('-t', '--token', default='')
    return parser.parse_args()[0]
def main():
    options = parse_args()
    assert options.token
    return 'OK: CPU | cpu=12%;80;90', 0
''')
    return resource, plugin


def arguments(inputs):
    resource, plugin = inputs
    return ["--resource-file", str(resource), "--resource-slot", "USER2",
            "--plugin", str(plugin), "-H", "127.0.0.1", "-P", "5694", "-M", "cpu/percent"]


def test_result_and_performance_data_preserved_without_mutating_argv(inputs):
    original = sys.argv[:]
    assert adapter().run(arguments(inputs)) == ("OK: CPU | cpu=12%;80;90", 0)
    assert sys.argv == original


@pytest.mark.parametrize("flag", ["-t", "--token", "--token=literal", "-tliteral", "-v", "--verbose", "-D", "--debug"])
def test_secret_and_diagnostic_options_are_rejected(inputs, flag):
    output, code = adapter().run(arguments(inputs) + [flag])
    assert code == 3
    assert "synthetic" not in output


@pytest.mark.parametrize("contents", [
    "$USER2$=outside\n", "# BEGIN PINPOINT\n$USER2$=one\n$USER2$=two\n# END PINPOINT\n",
    "# BEGIN PINPOINT\n$USER2$=one\n", "# BEGIN PINPOINT\n$USER3$=one\n# END PINPOINT\n",
])
def test_missing_or_ambiguous_owned_slot_is_rejected(inputs, contents):
    inputs[0].write_text(contents)
    assert adapter().run(arguments(inputs))[1] == 3


def test_world_readable_and_symlink_resources_are_rejected(inputs, tmp_path):
    resource, _ = inputs
    resource.chmod(0o664)
    assert adapter().run(arguments(inputs))[1] == 3
    resource.chmod(0o660)
    link = tmp_path / "link"
    link.symlink_to(resource)
    assert adapter().run(arguments((link, inputs[1])))[1] == 3


@pytest.mark.parametrize("body", [
    "raise RuntimeError(options.token)",
    "print(options.token); return options.token, 2",
    "from urllib.parse import quote; return quote(options.token, safe=''), 2",
    "from urllib.parse import quote_plus; return quote_plus(options.token), 2",
])
def test_credential_output_and_exceptions_are_suppressed(inputs, body):
    resource, plugin = inputs
    plugin.write_text(plugin.read_text().replace("return 'OK: CPU | cpu=12%;80;90', 0", body))
    output, code = adapter().run(arguments(inputs))
    assert "synthetic" not in output
    assert code == 3


def test_unsupported_plugin_version_is_explicitly_rejected(inputs):
    plugin = inputs[1]
    plugin.write_text(plugin.read_text().replace("1.2.4", "9.9.9"))
    assert adapter().run(arguments(inputs)) == ("UNKNOWN: Unsupported NCPA client version.", 3)


@pytest.mark.skipif(not Path('/proc/self/cmdline').exists(), reason="Linux process inspection")
def test_running_check_keeps_token_out_of_process_arguments_and_has_no_child(inputs, tmp_path):
    # The plugin runs until the test releases it. The only credential file is
    # resource.cfg; neither the executable nor the subprocess argv embeds it.
    plugin = inputs[1]
    ready, release = tmp_path / "ready", tmp_path / "release"
    plugin.write_text(plugin.read_text().replace(
        "return 'OK: CPU | cpu=12%;80;90', 0",
        f"from pathlib import Path; import time\n    Path({str(ready)!r}).touch()\n"
        f"    deadline = time.monotonic() + 10\n    while not Path({str(release)!r}).exists():\n"
        "        if time.monotonic() > deadline: return 'UNKNOWN: test timeout', 3\n"
        "        time.sleep(0.01)\n    return 'OK: CPU | cpu=12%;80;90', 0"))
    process = subprocess.Popen([sys.executable, "-I", str(SCRIPT), *arguments(inputs)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), process.communicate(timeout=1)
        assert b"synthetic token&value" not in Path(f"/proc/{process.pid}/cmdline").read_bytes()
        children = Path(f"/proc/{process.pid}/task/{process.pid}/children").read_text().strip()
        assert children == ""
        release.touch()
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0
        assert stdout.strip() == "OK: CPU | cpu=12%;80;90"
        assert stderr == ""
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
