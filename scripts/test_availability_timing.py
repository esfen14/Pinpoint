#!/usr/bin/env python3
"""Offline tests for scripts/availability_timing.py, using a local fake server."""
import contextlib
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import availability_timing  # noqa: E402

NETWORK_HEALTH = "/api/system/network-health/availability?days=7"
REPORT = "/api/system/report/availability?period=last_24h"


class FakeApp:
    """Answers like the appliance: login and the two availability endpoints."""

    def __init__(self):
        self.hosts = 10
        self.report_status = 200
        self.seen = []

    def reply(self, method, path, signed_in):
        if path == "/api/user/login" and method == "POST":
            return 200, "application/json", b'{"success": true}', True
        if path in (NETWORK_HEALTH, REPORT):
            if not signed_in:
                return 401, "text/html", b"Unauthorized", False
            self.seen.append(path)
            if path == REPORT:
                hosts = []
                for number in range(self.hosts):
                    hosts.append({"hostname": f"host{number}"})
                body = {"success": self.report_status == 200, "data": {"hosts": hosts}}
                return self.report_status, "application/json", json.dumps(body).encode(), False
            body = {"success": True, "data": {"days": 7, "daily": []}}
            return 200, "application/json", json.dumps(body).encode(), False
        if path.startswith("/api/"):
            return 404, "text/html", b"not found", False
        return 200, "text/html", b"<!doctype html>", False


class AvailabilityTimingTest(unittest.TestCase):
    def setUp(self):
        self.app = FakeApp()
        app = self.app

        class Handler(BaseHTTPRequestHandler):
            def answer(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                signed_in = "session=ok" in (self.headers.get("Cookie") or "")
                status, kind, body, set_cookie = app.reply(self.command, self.path, signed_in)
                self.send_response(status)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(body)))
                if set_cookie:
                    self.send_header("Set-Cookie", "session=ok; Path=/")
                self.end_headers()
                self.wfile.write(body)

            do_GET = do_POST = answer

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def run_main(self, *extra):
        with tempfile.TemporaryDirectory() as folder:
            secret = Path(folder) / "secret"
            secret.write_text("secret-value\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                code = availability_timing.main([
                    "--base-url", self.base, "--email-file", str(secret),
                    "--password-file", str(secret), "--pause", "0", *extra,
                ])
        self.assertNotIn("secret-value", output.getvalue())
        return code, json.loads(output.getvalue())

    def test_each_endpoint_is_timed_ten_times_and_passes(self):
        code, report = self.run_main()

        self.assertEqual(code, 0)
        self.assertEqual(report["monitored_hosts"], 10)
        for path in (NETWORK_HEALTH, REPORT):
            self.assertEqual(len(report["endpoints"][path]["samples"]), 10)
            self.assertEqual(report["endpoints"][path]["within_limit"], 10)
        # Ten timed requests each, plus the untimed host-count read of the report.
        self.assertEqual(self.app.seen.count(NETWORK_HEALTH), 10)
        self.assertEqual(self.app.seen.count(REPORT), 11)

    def test_wrong_host_count_is_not_measured(self):
        self.app.hosts = 16

        code, report = self.run_main()

        self.assertEqual(code, 2)
        self.assertIn("16", report["error"])
        self.assertNotIn(NETWORK_HEALTH, self.app.seen)

    def test_error_replies_do_not_count_even_when_fast(self):
        self.app.report_status = 200
        original = self.app.reply
        timed = []

        def failing_after_two(method, path, signed_in):
            if path == REPORT and signed_in:
                timed.append(path)
                # Call 1 is the host count; fail timed requests 2 and 3.
                self.app.report_status = 502 if len(timed) in (3, 4) else 200
            return original(method, path, signed_in)

        self.app.reply = failing_after_two

        code, report = self.run_main()

        self.assertEqual(code, 1)
        self.assertEqual(report["endpoints"][REPORT]["within_limit"], 8)
        self.assertFalse(report["endpoints"][REPORT]["passed"])
        self.assertTrue(report["endpoints"][NETWORK_HEALTH]["passed"])

    def test_nine_of_ten_passes_and_the_limit_is_inclusive(self):
        samples = []
        for seconds in [5.0] * 9 + [5.001]:
            samples.append({"seconds": seconds, "ok": True})

        verdict = availability_timing.judge(samples, limit=5.0, required=9)

        self.assertEqual(verdict["within_limit"], 9)
        self.assertTrue(verdict["passed"])
        samples[0]["seconds"] = 6.0
        self.assertFalse(availability_timing.judge(samples, limit=5.0, required=9)["passed"])

    def test_a_slow_reply_is_over_the_limit(self):
        code, report = self.run_main("--limit", "0")

        self.assertEqual(code, 1)
        self.assertEqual(report["endpoints"][NETWORK_HEALTH]["within_limit"], 0)

    def test_probes_record_url_state_status_and_content_type(self):
        code, report = self.run_main("--probe")

        found = {}
        for row in report["probes"]:
            found[(row["path"], row["signed_in"])] = (row["status"], row["content_type"])
        self.assertEqual(found[(REPORT, False)], (401, "text/html"))
        self.assertEqual(found[(REPORT, True)], (200, "application/json"))
        self.assertEqual(found[("/network-health", False)], (200, "text/html"))


if __name__ == "__main__":
    unittest.main()
