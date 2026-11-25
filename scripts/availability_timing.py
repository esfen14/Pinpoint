#!/usr/bin/env python3
"""Time Pinpoint's availability endpoints for TC-NFR-08 (REQ-NFR-06).

Signs in, confirms the report lists the expected number of monitored hosts, then
requests each availability endpoint (with the query the web interface sends) a
number of times, one at a time. An endpoint passes when enough of its requests
return data within the limit; an error reply never counts, however fast.

    scripts/availability_timing.py --base-url http://127.0.0.1:18080 \\
        --email-file FILE --password-file FILE

Read-only. With --probe it also records status and content type for the URLs
behind the "returns to login" and "plain text without UI" observations. The
password is read from a file and never printed. Standard library only.

Exit status: 0 both endpoints pass, 1 one fails, 2 not measured.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from startup_timing import MeasurementError, new_session, read_secret, request, sign_in  # noqa: E402

NETWORK_HEALTH_PATH = "/api/system/network-health/availability?days=7"
REPORT_PATH = "/api/system/report/availability?period=last_24h"
ENDPOINTS = (NETWORK_HEALTH_PATH, REPORT_PATH)
# The two API URLs typed directly, a mistyped API address, the two pages that show
# the same data, and a mistyped page address.
PROBE_PATHS = ENDPOINTS + (
    "/api/system/report/availabilty",
    "/network-health",
    "/reports",
    "/report",
)


def reply_data(status, raw):
    """Return the response's data object, or None when the reply is not a success."""
    if status != 200:
        return None
    try:
        body = json.loads(raw)
        if body["success"] is not True:
            return None
        return body["data"]
    except (ValueError, KeyError, TypeError):
        return None


def count_monitored_hosts(session, base):
    """Return how many monitored hosts the availability report lists."""
    status, _, raw = request(session, base, REPORT_PATH)
    data = reply_data(status, raw)
    if data is None or "hosts" not in data:
        raise MeasurementError(f"could not read the host list (HTTP {status})")
    return len(data["hosts"])


def time_request(session, base, path, clock=time.monotonic):
    """Request path once and return its status, content type, duration and verdict."""
    started = clock()
    status, content_type, raw = request(session, base, path)
    seconds = clock() - started
    return {
        "seconds": round(seconds, 3),
        "status": status,
        "content_type": content_type,
        "bytes": len(raw),
        "ok": reply_data(status, raw) is not None,
    }


def judge(samples, limit, required):
    """Count the samples that returned data within limit and compare with required."""
    within = 0
    slowest = 0.0
    for sample in samples:
        if sample["ok"] and sample["seconds"] <= limit:
            within += 1
        slowest = max(slowest, sample["seconds"])
    return {"within_limit": within, "slowest_seconds": slowest, "passed": within >= required}


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email-file", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--hosts", type=int, default=10, help="monitored hosts required")
    parser.add_argument("--requests", type=int, default=10, help="per endpoint")
    parser.add_argument("--required", type=int, default=9, help="requests within the limit")
    parser.add_argument("--limit", type=float, default=5.0, help="seconds")
    parser.add_argument("--pause", type=float, default=2.0, help="seconds between requests")
    parser.add_argument("--probe", action="store_true", help="also record the symptom URLs")
    args = parser.parse_args(argv)
    if not 1 <= args.required <= args.requests:
        parser.error("--required must be between 1 and --requests")

    report = {"base_url": args.base_url, "limit_seconds": args.limit, "endpoints": {}}
    try:
        email = read_secret(args.email_file)
        password = read_secret(args.password_file)
        session = new_session()
        status = sign_in(session, args.base_url, email, password)
        if status != 200:
            raise MeasurementError(f"login refused with HTTP {status}")
        hosts = count_monitored_hosts(session, args.base_url)
        report["monitored_hosts"] = hosts
        if hosts != args.hosts:
            raise MeasurementError(f"{hosts} monitored hosts, the case needs {args.hosts}")
        for path in ENDPOINTS:
            samples = []
            for number in range(1, args.requests + 1):
                if number > 1:
                    time.sleep(args.pause)
                sample = time_request(session, args.base_url, path)
                samples.append(sample)
                print(f"{path} {number}: {sample['seconds']} s, HTTP {sample['status']}", file=sys.stderr)
            result = judge(samples, args.limit, args.required)
            result["samples"] = samples
            report["endpoints"][path] = result
        if args.probe:
            report["probes"] = probe(args.base_url, email, password)
    except (MeasurementError, OSError) as error:
        report["error"] = str(error)
        print(json.dumps(report, indent=2))
        return 2

    passed = True
    for result in report["endpoints"].values():
        if not result["passed"]:
            passed = False
    report["passed"] = passed
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
