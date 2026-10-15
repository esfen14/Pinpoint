#!/usr/bin/python3 -I
"""
pinpoint_event_handler.py — the Nagios event handler: leaves one small note for PinPoint.

Nagios runs this as the `nagios` user when a covered host or service changes state. It does
not fix anything. It validates its arguments and writes ONE file to the spool folder; the
PinPoint consumer (app/remediation.py) reads that file, decides, and records what it did.

The installer copies this file to /usr/local/sbin/pinpoint-event-handler (root:root, 755).
The spool folder is /usr/local/nagios/var/spool/pinpoint-events (nagios:pinpoint, 2770); the
installer creates it. Standard library only; it does not import the application.

Usage (the quotes are in the Nagios command definition):

    pinpoint-event-handler service STATE STATETYPE ATTEMPT HOST SERVICE LASTCHANGE
    pinpoint-event-handler host    STATE STATETYPE ATTEMPT HOST         LASTCHANGE

Everything is untrusted. A value outside the allowed characters or lengths, a state that is
not a Nagios state for that kind, or a wrong number of arguments is refused and nothing is
written. The program never opens a shell, the network, or any file but the spool folder.

Exit status: 0 written (or the folder is full and the event was dropped quietly),
1 rejected input, 2 misuse, 3 the spool could not be written.
"""
import json
import os
import re
import sys
import time

SPOOL_DIR = "/usr/local/nagios/var/spool/pinpoint-events"
MAX_SPOOL_FILES = 1000
FILE_MODE = 0o660

HOST_STATES = {"UP", "DOWN", "UNREACHABLE"}
SERVICE_STATES = {"OK", "WARNING", "CRITICAL", "UNKNOWN"}
STATE_TYPES = {"SOFT", "HARD"}

MAX_HOST_LENGTH = 100
MAX_SERVICE_LENGTH = 150
MAX_ATTEMPT = 100
NAME_RE = re.compile(r"[A-Za-z0-9 ._:/-]+", re.ASCII)
NUMBER_RE = re.compile(r"[0-9]{1,12}", re.ASCII)


class InputRejected(Exception):
    """Invalid arguments. The message names the problem and never echoes the value."""


def check_name(value, what, max_length):
    """Return value when it uses only allowed characters, has no "..", and is 1..max_length long."""
    if not value or len(value) > max_length or not NAME_RE.fullmatch(value) or ".." in value:
        raise InputRejected(f"invalid {what}")
    return value


def check_number(value, what, maximum=None):
    """Return value as a positive int (digits only); maximum caps it when given."""
    if not NUMBER_RE.fullmatch(value):
        raise InputRejected(f"invalid {what}")
    number = int(value)
    if number < 1 or (maximum is not None and number > maximum):
        raise InputRejected(f"invalid {what}")
    return number


def parse(argv):
    """Validate the arguments and return the event as a dict. Raises InputRejected."""
    if not argv or argv[0] not in ("host", "service"):
        raise InputRejected("first argument must be host or service")
    kind = argv[0]
    expected = 7 if kind == "service" else 6
    if len(argv) != expected:
        raise InputRejected("wrong number of arguments")

    state, state_type, attempt, host = argv[1], argv[2], argv[3], argv[4]
    allowed_states = SERVICE_STATES if kind == "service" else HOST_STATES
    if state not in allowed_states:
        raise InputRejected("invalid state")
    if state_type not in STATE_TYPES:
        raise InputRejected("invalid state type")

    service = None
    if kind == "service":
        service = check_name(argv[5], "service", MAX_SERVICE_LENGTH)
    return {
        "v": 1,
        "kind": kind,
        "host": check_name(host, "host", MAX_HOST_LENGTH),
        "service": service,
        "state": state,
        "state_type": state_type,
        "attempt": check_number(attempt, "attempt", MAX_ATTEMPT),
        "last_change": check_number(argv[-1], "last change"),
    }


def write_event(event, spool_dir):
    """
    Write the event as one JSON line. It goes to a temporary dot-name first and is renamed to
    <epoch_ns>-<pid>.json, so the consumer never sees a half-written file. Returns 0, or 0
    without writing when the folder already holds MAX_SPOOL_FILES entries.
    """
    if sum(1 for _ in os.scandir(spool_dir)) >= MAX_SPOOL_FILES:
        return 0
    stem = f"{time.time_ns()}-{os.getpid()}"
    temporary = os.path.join(spool_dir, f".{stem}.tmp")
    final = os.path.join(spool_dir, f"{stem}.json")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(temporary, flags, FILE_MODE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
        if hasattr(os, "chmod"):
            os.chmod(temporary, FILE_MODE)
        os.rename(temporary, final)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return 0


def main(argv=None, spool_dir=SPOOL_DIR):
    """Entry point. Returns the exit status; prints a one-line reason to stderr on failure."""
    argv = sys.argv[1:] if argv is None else argv
    try:
        event = parse(argv)
    except InputRejected as problem:
        print(f"pinpoint-event-handler: {problem}", file=sys.stderr)
        return 1 if argv else 2
    if not os.path.isdir(spool_dir):
        print("pinpoint-event-handler: spool folder missing", file=sys.stderr)
        return 3
    try:
        return write_event(event, spool_dir)
    except OSError:
        print("pinpoint-event-handler: could not write the spool file", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
