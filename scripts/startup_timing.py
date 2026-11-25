#!/usr/bin/env python3
"""Time Pinpoint's start-up for TC-NFR-07 (REQ-NFR-05).

Each sample starts the clock, runs the restart command, then signs in and calls
/api/system/dashboard/summary until it returns data. The case passes when the
median of the samples is at most the limit. The clock includes the restart
command itself, so the time spent reaching the appliance counts against the app.

    scripts/startup_timing.py --base-url http://127.0.0.1:18080 \\
        --email-file FILE --password-file FILE -- <command that restarts Pinpoint>

Restarting is disruptive: only point it at an appliance you may restart. With
--probe it also records status and content type for the URLs behind the
"returns to login" and "plain text without UI" observations. The password is read
from a file and never printed. Standard library only.

Exit status: 0 median within the limit, 1 over the limit, 2 not measured.
"""
import argparse
import http.cookiejar
import json
import math
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

LOGIN_PATH = "/api/user/login"
SUMMARY_PATH = "/api/system/dashboard/summary"
# Replies that mean "still starting". Any other refusal will not fix itself.
STARTING_STATUSES = (None, 502, 503, 504)
REQUEST_TIMEOUT = 10
# (path, why it is probed): the API URL typed directly, then two mistyped addresses.
PROBE_PATHS = (SUMMARY_PATH, "/api/system/dashbord/summary", "/dashbord")


class MeasurementError(Exception):
    """The run cannot produce a valid timing (bad login, failed restart)."""


def new_session():
    """Return a URL opener with its own empty cookie jar."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request(session, base, path, body=None):
    """
    Send one request (POST when body is given). Return (status, content type, bytes);
    status is None when the server could not be reached.
    """
    data = json.dumps(body).encode() if body is not None else None
    outgoing = urllib.request.Request(base.rstrip("/") + path, data=data)
    if data is not None:
        outgoing.add_header("Content-Type", "application/json")
    try:
        with session.open(outgoing, timeout=REQUEST_TIMEOUT) as response:
            return response.status, response.headers.get_content_type(), response.read()
    except urllib.error.HTTPError as error:
        with error:
            return error.code, error.headers.get_content_type(), error.read()
    except OSError:
        return None, None, b""


def has_summary_data(raw):
    """True when the body is a successful summary with host and service counts."""
    try:
        body = json.loads(raw)
        data = body["data"]
        return body["success"] is True and "hosts" in data and "services" in data
    except (ValueError, KeyError, TypeError):
        return False


def sign_in(session, base, email, password):
    """Post the login and return its status."""
    status, _, _ = request(session, base, LOGIN_PATH, {"email": email, "password": password})
    return status


def take_sample(base, email, password, restart, timeout, interval, clock=time.monotonic):
    """
    Restart Pinpoint with restart() and time it until the dashboard summary returns
    data. Returns a dict with seconds (None when not ready within timeout), the
    restart command's own duration and the statuses seen before it was ready.
    """
    started = clock()
    restart()
    restarted = clock()
    session = new_session()
    signed_in = False
    seen = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not signed_in:
            status = sign_in(session, base, email, password)
            if status == 200:
                signed_in = True
            elif status not in STARTING_STATUSES:
                raise MeasurementError(f"login refused with HTTP {status}")
        if signed_in:
            status, _, raw = request(session, base, SUMMARY_PATH)
            if status == 200 and has_summary_data(raw):
                return {
                    "ready": True,
                    "seconds": round(clock() - started, 3),
                    "restart_command_seconds": round(restarted - started, 3),
                    "statuses_before_ready": seen,
                }
            if status not in STARTING_STATUSES and status != 200:
                raise MeasurementError(f"summary refused with HTTP {status}")
        seen.append(status)
        time.sleep(interval)
    return {
        "ready": False,
        "seconds": None,
        "restart_command_seconds": round(restarted - started, 3),
        "statuses_before_ready": seen,
    }


def judge(seconds, limit):
    """
    Return the median of the sample times and whether it is within limit. A None
    sample (never ready) counts as slower than any measured time.
    """
    ordered = []
    for value in seconds:
        ordered.append(math.inf if value is None else value)
    median = statistics.median(ordered)
    if math.isinf(median):
        return {"median_seconds": None, "passed": False}
    return {"median_seconds": median, "passed": median <= limit}


def probe(base, email, password):
    """Record status and content type of the probe URLs, signed out and signed in."""
    signed_out = new_session()
    signed_in = new_session()
    status = sign_in(signed_in, base, email, password)
    if status != 200:
        raise MeasurementError(f"login refused with HTTP {status}")
    rows = []
    for is_signed_in, session in ((False, signed_out), (True, signed_in)):
        for path in PROBE_PATHS:
            status, content_type, _ = request(session, base, path)
            rows.append({
                "path": path,
                "signed_in": is_signed_in,
                "status": status,
                "content_type": content_type,
            })
    return rows


def run_restart(command):
    """Run the restart command without a shell; fail the run if it fails."""
    done = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if done.returncode != 0:
        raise MeasurementError(
            f"restart command exited {done.returncode}: {done.stderr.strip()[-500:]}"
        )


def read_secret(path):
    """Return the stripped contents of a credential file."""
    with open(path, encoding="utf-8") as handle:
        return handle.read().strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email-file", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--limit", type=float, default=10.0, help="seconds")
    parser.add_argument("--timeout", type=float, default=120.0, help="seconds per sample")
    parser.add_argument("--interval", type=float, default=0.25, help="seconds between tries")
    parser.add_argument("--settle", type=float, default=30.0, help="seconds between samples")
    parser.add_argument("--probe", action="store_true", help="also record the symptom URLs")
    parser.add_argument("restart", nargs="+", help="restart command, after --")
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error("--samples must be at least 1")

    report = {"base_url": args.base_url, "limit_seconds": args.limit, "samples": []}
    try:
        email = read_secret(args.email_file)
        password = read_secret(args.password_file)
        # Prove the login and the URL work before restarting anything.
        status = sign_in(new_session(), args.base_url, email, password)
        if status != 200:
            raise MeasurementError(f"login before the first restart returned HTTP {status}")
        for number in range(1, args.samples + 1):
            if number > 1:
                time.sleep(args.settle)
            sample = take_sample(
                args.base_url, email, password,
                lambda: run_restart(args.restart),
                timeout=args.timeout, interval=args.interval,
            )
            report["samples"].append(sample)
            print(f"sample {number}: {sample['seconds']} s", file=sys.stderr)
        if args.probe:
            report["probes"] = probe(args.base_url, email, password)
    except (MeasurementError, OSError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
        print(json.dumps(report, indent=2))
        return 2

    seconds = []
    for sample in report["samples"]:
        seconds.append(sample["seconds"])
    report.update(judge(seconds, args.limit))
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
