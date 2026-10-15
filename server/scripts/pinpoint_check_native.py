#!/usr/bin/python3 -I
"""Supply supported native Nagios plugin passwords through extra-options stdin.

The resource reader is shared with the NCPA adapter. Only the installed
check_nt, check_radius, check_mysql_query and check_snmp (SNMP v3 passphrases,
--auth-slot and --priv-slot) executables are supported, and
their help must advertise extra-options. No credential file is created, and
the parent/child argv contains only public fields and a bare USERn identifier.
SMB is deliberately excluded because its plugin exposes child credentials.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
from urllib.parse import quote, quote_plus

# -I removes the script directory from sys.path. Load only the known sibling
# by absolute path; neither script runs privileged or imports application code.
spec = importlib.util.spec_from_file_location("pinpoint_ncpa_resource_reader", Path(__file__).with_name("pinpoint_check_ncpa.py"))
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)

PUBLIC_FLAGS = {
    "check_nt": {"-H", "-v", "-p", "-w", "-c", "-l"},
    "check_radius": {"-H", "-u", "-F", "-P"},
    "check_mysql_query": {"-H", "-q", "-w", "-c", "-u", "-d", "-P"},
    "check_snmp": {"-H", "-p", "-o", "-P", "-L", "-U", "-a", "-x", "-w", "-c", "-l", "-u"},
}
# check_snmp reads two passphrases; each has its own slot flag and extra-options key.
SNMP_SLOT_KEYS = (("auth_slot", "authpasswd"), ("priv_slot", "privpasswd"))
SLOT_PATTERN = r"USER(?:[2-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-6])"


def parse_arguments(argv):
    """Accept only generated public arguments for an allowlisted native plugin."""
    parser = resources.SafeParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--resource-file", required=True)
    parser.add_argument("--resource-slot")
    parser.add_argument("--auth-slot")
    parser.add_argument("--priv-slot")
    parser.add_argument("--plugin", required=True)
    args, public = parser.parse_known_args(argv)
    name = Path(args.plugin).name
    if name not in PUBLIC_FLAGS:
        raise resources.InputRejected("Unsupported native credential transport.")
    checks = resources.SafeParser(add_help=False, allow_abbrev=False)
    for flag in PUBLIC_FLAGS[name]:
        checks.add_argument(flag)
    checks.parse_args(public)
    if (args.auth_slot or args.priv_slot) and name != "check_snmp":
        raise resources.InputRejected("Unsupported native credential transport.")
    if args.resource_slot and name == "check_snmp":
        raise resources.InputRejected("Unsupported native credential transport.")
    for slot in (args.resource_slot, args.auth_slot, args.priv_slot):
        if slot and not resources.re.fullmatch(SLOT_PATTERN, slot):
            raise resources.InputRejected("Invalid managed resource slot.")
    return args, public


def credentials(args):
    """Return [(extra-options key, slot)] for the slots the command supplied."""
    if Path(args.plugin).name == "check_snmp":
        return [(key, getattr(args, attribute)) for attribute, key in SNMP_SLOT_KEYS if getattr(args, attribute)]
    if not args.resource_slot:
        return []
    return [("secret" if Path(args.plugin).name == "check_nt" else "password", args.resource_slot)]


def run(argv):
    """Return a sanitized check result; kill the entire check group on timeout."""
    tokens = []
    process = None
    try:
        args, public = parse_arguments(argv)
        stdin = None
        wanted = credentials(args)
        if wanted:
            lines = []
            for key, slot in wanted:
                token = resources.read_token(args.resource_file, slot)
                # The native INI parser trims surrounding whitespace. Refuse
                # instead of changing the password that reaches authentication.
                if token != token.strip() or any(char in token for char in "\r\n\x00"):
                    raise resources.InputRejected("Password cannot be represented safely as extra-options.")
                tokens.append(token)
                lines.append(f"{key}={token}\n")
            help_result = subprocess.run([args.plugin, "--help"], stdin=subprocess.DEVNULL,
                                         capture_output=True, timeout=5)
            if b"--extra-opts" not in help_result.stdout:
                raise resources.InputRejected("Installed plugin lacks extra-options support.")
            public = ["--extra-opts=pinpoint@-", *public]
            stdin = "[pinpoint]\n" + "".join(lines)
        process = subprocess.Popen([args.plugin, *public], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        stdout, stderr = process.communicate(stdin, timeout=60)
        if len(stdout) + len(stderr) > resources.MAX_OUTPUT_BYTES:
            raise resources.InputRejected("Plugin output exceeded the permitted size.")
        if any(value in stdout or value in stderr
               for token in tokens for value in {token, quote(token, safe=""), quote_plus(token)}):
            raise resources.InputRejected("Plugin returned credential-bearing output.")
        if process.returncode not in (0, 1, 2, 3):
            raise resources.InputRejected("Invalid native plugin result.")
        return stdout.rstrip("\n"), process.returncode
    except resources.InputRejected as exc:
        return f"UNKNOWN: {exc}", 3
    except subprocess.TimeoutExpired:
        return "UNKNOWN: Native plugin exceeded its timeout.", 3
    except Exception:
        return "UNKNOWN: Unable to run the protected native check.", 3
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        tokens = None


if __name__ == "__main__":
    output, code = run(sys.argv[1:])
    print(output)
    sys.exit(code)
