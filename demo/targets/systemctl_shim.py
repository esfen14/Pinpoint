#!/usr/bin/python3 -I
"""The part of systemctl that installing and deploying NCPA needs, for a container with no init.

Installed as /usr/bin/systemctl on the NCPA deploy target only. It manages one unit,
ncpa, by running the same command the real ncpa.service runs (`ncpa -n`).
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

PROGRAM = Path('/usr/local/ncpa/ncpa')
PIDFILE = Path('/run/ncpa-shim.pid')
LOG = Path('/data/ncpa.out.log')
UNITS = ('ncpa', 'ncpa.service')
# Verbs a package script runs that mean nothing without an init system.
IGNORED = ('daemon-reload', 'enable', 'disable', 'list-units')


def running_pid():
    """The saved process, only while it is alive and still is NCPA."""
    try:
        pid = int(PIDFILE.read_text())
        command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')[0]
    except (OSError, ValueError):
        return None
    if command != str(PROGRAM).encode():
        return None
    return pid


def start() -> int:
    if running_pid():
        return 0
    if not PROGRAM.is_file():
        print('NCPA is not installed.', file=sys.stderr)
        return 5
    with open(LOG, 'ab') as log:
        # Detached with no inherited pipes, so an SSH command that ran us can finish.
        process = subprocess.Popen([str(PROGRAM), '-n'], stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log, cwd=str(PROGRAM.parent),
                                   start_new_session=True)
    PIDFILE.write_text(str(process.pid))
    time.sleep(1)
    if process.poll() is not None:
        print('NCPA stopped immediately after starting.', file=sys.stderr)
        return 1
    return 0


def stop() -> int:
    pid = running_pid()
    if pid:
        os.killpg(pid, signal.SIGTERM)
        deadline = time.monotonic() + 10
        while running_pid() and time.monotonic() < deadline:
            time.sleep(0.2)
        if running_pid():
            os.killpg(pid, signal.SIGKILL)
    PIDFILE.unlink(missing_ok=True)
    return 0


def status() -> int:
    if running_pid():
        print('ncpa is active')
        return 0
    print('ncpa is inactive')
    return 3


def main(argv: list[str]) -> int:
    words = []
    for value in argv:
        if not value.startswith('-'):
            words.append(value)
    if words and words[0] in IGNORED:
        return 0
    if len(words) != 2 or words[1] not in UNITS:
        print('This container has no init system; only the ncpa unit is supported.', file=sys.stderr)
        return 1
    verb = words[0]
    if verb == 'start':
        return start()
    if verb == 'stop':
        return stop()
    if verb == 'restart':
        stop()
        return start()
    if verb in ('status', 'is-active'):
        return status()
    print('Unsupported systemctl verb.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
