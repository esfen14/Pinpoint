#!/usr/bin/python3 -I
"""Run an installed NCPA client with a protected resource token in memory.

Only USER2..USER256 identifiers reach argv, without dollar signs that Nagios
would expand. The inspected 1.2.4/1.2.5 clients execute in this process: their
parsed options receive the token without exec, a child process or environment
variables. This script is unprivileged, uses only the standard library, and
does not import Flask. It does not install or modify the upstream plugin.

Generated commands must supply --resource-file, --resource-slot and --plugin,
followed by public check arguments. Unsupported versions, unsafe resources,
diagnostic/credential options and secret-bearing results return UNKNOWN.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import io
import os
from pathlib import Path
import re
import signal
import stat
import sys
from urllib.parse import quote, quote_plus

SUPPORTED_VERSIONS = {"1.2.4", "1.2.5"}
MAX_FILE_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 65536


class InputRejected(Exception):
    """Safe failure whose message contains no supplied value or credential."""


class SafeParser(argparse.ArgumentParser):
    """Reject malformed options without argparse echoing their values."""

    def error(self, message):
        raise InputRejected("Invalid check arguments.")


class BoundedOutput(io.StringIO):
    """Capture upstream diagnostics without allowing unlimited memory use."""

    def write(self, value):
        if self.tell() + len(value) > MAX_OUTPUT_BYTES:
            raise InputRejected("NCPA output exceeded the permitted size.")
        return super().write(value)


def parse_arguments(argv):
    """Parse adapter paths and accept only the supported public NCPA flags."""
    parser = SafeParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--resource-file", required=True)
    parser.add_argument("--resource-slot", required=True)
    parser.add_argument("--plugin", required=True)
    adapter, public = parser.parse_known_args(argv)
    # Explicitly parse every public flag; optparse abbreviations and bundled
    # diagnostic flags must not allow a token or URL to be printed.
    checks = SafeParser(add_help=False, allow_abbrev=False)
    for short, long in (("-H", "--hostname"), ("-P", "--port"), ("-M", "--metric"),
                        ("-w", "--warning"), ("-c", "--critical"), ("-u", "--units"),
                        ("-n", "--unit"), ("-q", "--queryargs"), ("-T", "--timeout"),
                        ("-S", "--sleep")):
        checks.add_argument(short, long)
    for short, long in (("-s", "--secure"), ("-p", "--performance"), ("-d", "--delta")):
        checks.add_argument(short, long, action="store_true")
    values = checks.parse_args(public)
    if not values.hostname or not values.metric:
        raise InputRejected("Hostname and metric are required.")
    if not re.fullmatch(r"USER(?:[2-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-6])", adapter.resource_slot):
        raise InputRejected("Invalid managed resource slot.")
    return adapter, public


def read_token(path, slot):
    """Read exactly one owned slot from a bounded, private regular file."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o007:
            raise InputRejected("Unsafe resource file permissions or type.")
        contents = stream.read(MAX_FILE_BYTES + 1)
    if len(contents) > MAX_FILE_BYTES:
        raise InputRejected("Resource file exceeded the permitted size.")
    lines = contents.decode("utf-8").splitlines()
    begin, end = "# BEGIN PINPOINT", "# END PINPOINT"
    if lines.count(begin) != 1 or lines.count(end) != 1 or lines.index(begin) >= lines.index(end):
        raise InputRejected("Invalid managed resource block.")
    first, last = lines.index(begin), lines.index(end)
    wanted = f"${slot}$"
    found = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"\s*(\$USER[0-9]+\$)=(.*)", line)
        if match and match.group(1) == wanted:
            if not first < index < last:
                raise InputRejected("Resource slot is not exclusively managed.")
            found.append(match.group(2))
    if len(found) != 1 or not found[0] or any(ord(char) < 32 for char in found[0]):
        raise InputRejected("Missing or ambiguous managed resource value.")
    return found[0]


def run(argv):
    """Return sanitized plugin output and exit status, restoring process state."""
    original_argv = sys.argv
    original_handler = signal.getsignal(signal.SIGALRM)
    original_timer = signal.getitimer(signal.ITIMER_REAL)
    token = None
    try:
        args, public = parse_arguments(argv)
        token = read_token(args.resource_file, args.resource_slot)
        source = Path(args.plugin).read_bytes()
        if len(source) > MAX_FILE_BYTES:
            raise InputRejected("NCPA client exceeded the permitted size.")
        namespace = {"__name__": "pinpoint_ncpa_client", "__file__": args.plugin}
        diagnostics = BoundedOutput()
        with redirect_stdout(diagnostics), redirect_stderr(diagnostics):
            exec(compile(source, args.plugin, "exec"), namespace)
            if namespace.get("__VERSION__") not in SUPPORTED_VERSIONS:
                raise InputRejected("Unsupported NCPA client version.")
            sys.argv = [args.plugin, *public]
            options = namespace["parse_args"]()
            options.token = token
            namespace["parse_args"] = lambda: options
            output, code = namespace["main"]()
        if not isinstance(output, str) or type(code) is not int or code not in (0, 1, 2, 3):
            raise InputRejected("Invalid NCPA result.")
        if len(output) > MAX_OUTPUT_BYTES:
            raise InputRejected("NCPA output exceeded the permitted size.")
        variants = {token, quote(token, safe=""), quote_plus(token)}
        if any(value in output or value in diagnostics.getvalue() for value in variants):
            raise InputRejected("NCPA returned credential-bearing output.")
        return output, code
    except InputRejected as exc:
        return f"UNKNOWN: {exc}", 3
    except SystemExit:
        # The stock timeout handler prints a public message and exits 3;
        # captured output is never emitted on an exceptional path.
        return "UNKNOWN: NCPA check stopped or exceeded its timeout.", 3
    except Exception:
        return "UNKNOWN: Unable to run the protected NCPA check.", 3
    finally:
        sys.argv = original_argv
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, original_handler)
        signal.setitimer(signal.ITIMER_REAL, *original_timer)
        token = None


if __name__ == "__main__":
    output, code = run(sys.argv[1:])
    print(output)
    sys.exit(code)
