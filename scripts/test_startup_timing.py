#!/usr/bin/env python3
"""Offline tests for scripts/startup_timing.py, using a local fake server."""
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
import startup_timing  # noqa: E402

SUMMARY = {"success": True, "data": {"hosts": {"total": 1}, "services": {"total": 2}}}


class FakeApp:
    """Answers like the appliance: 502 while starting, then login and summary."""

    def __init__(self):
        self.starting_replies = 0
        self.login_status = 200
        self.summary = SUMMARY
        self.logins = 0

    def reply(self, method, path, signed_in):
        if self.starting_replies > 0:
            self.starting_replies -= 1
            return 502, "text/html", b"<h1>Bad Gateway</h1>", False
        if path == "/api/user/login" and method == "POST":
            self.logins += 1
            body = {"success": self.login_status == 200}
            return self.login_status, "application/json", json.dumps(body).encode(), self.login_status == 200
        if path == "/api/system/dashboard/summary":
            if not signed_in:
                return 401, "application/json", b'{"success": false}', False
            return 200, "application/json", json.dumps(self.summary).encode(), False
        if path.startswith("/api/"):
            return 404, "text/html", b"not found", False
        return 200, "text/html", b"<!doctype html>", False


class StartupTimingTest(unittest.TestCase):
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

    def sample(self, restart=lambda: None, timeout=5):
        return startup_timing.take_sample(
            self.base, "qa@example.com", "pw", restart, timeout=timeout, interval=0.01
        )

    def test_sample_waits_until_the_summary_returns_data(self):
        def restart():
            self.app.starting_replies = 3

        sample = self.sample(restart)

        self.assertTrue(sample["ready"])
        self.assertEqual(sample["statuses_before_ready"], [502, 502, 502])
        self.assertGreater(sample["seconds"], 0)

    def test_the_clock_includes_the_restart_command(self):
        ticks = iter([100.0, 104.0, 109.0])

        sample = startup_timing.take_sample(
            self.base, "qa@example.com", "pw", lambda: None,
            timeout=30, interval=0.01, clock=lambda: next(ticks),
        )

        self.assertEqual(sample["restart_command_seconds"], 4.0)
        self.assertEqual(sample["seconds"], 9.0)

    def test_refused_login_stops_at_once(self):
        self.app.login_status = 401

        with self.assertRaises(startup_timing.MeasurementError):
            self.sample()
        self.assertEqual(self.app.logins, 1)

    def test_summary_without_data_is_not_ready(self):
        self.app.summary = {"success": True, "data": None}

        sample = self.sample(timeout=0.1)

        self.assertFalse(sample["ready"])
        self.assertIsNone(sample["seconds"])

    def test_verdict_uses_the_median_and_the_limit_is_inclusive(self):
        verdict = startup_timing.judge([30.0, 10.0, 2.0], limit=10.0)

        self.assertEqual(verdict, {"median_seconds": 10.0, "passed": True})
        self.assertFalse(startup_timing.judge([2.0, 10.01, 30.0], limit=10.0)["passed"])

    def test_a_sample_that_never_became_ready_counts_as_over_the_limit(self):
        self.assertTrue(startup_timing.judge([1.0, 2.0, None], limit=10.0)["passed"])
        self.assertEqual(
            startup_timing.judge([1.0, None, None], limit=10.0),
            {"median_seconds": None, "passed": False},
        )

    def test_probes_record_url_state_status_and_content_type(self):
        rows = startup_timing.probe(self.base, "qa@example.com", "pw")

        found = {}
        for row in rows:
            found[(row["path"], row["signed_in"])] = (row["status"], row["content_type"])
        self.assertEqual(found[("/api/system/dashboard/summary", False)], (401, "application/json"))
        self.assertEqual(found[("/api/system/dashboard/summary", True)], (200, "application/json"))
        self.assertEqual(found[("/api/system/dashbord/summary", True)], (404, "text/html"))
        self.assertEqual(found[("/dashbord", False)], (200, "text/html"))


    def test_main_restarts_once_per_sample_and_exits_by_the_verdict(self):
        with tempfile.TemporaryDirectory() as folder:
            secret = Path(folder) / "secret"
            secret.write_text("value\n")
            counter = Path(folder) / "restarts"
            append = f"open({str(counter)!r}, 'a').write('x')"
            arguments = [
                "--base-url", self.base, "--email-file", str(secret),
                "--password-file", str(secret), "--settle", "0", "--interval", "0.01",
            ]
            restart = ["--", sys.executable, "-c", append]
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                within = startup_timing.main(arguments + restart)
                restarts = counter.read_text()
                over = startup_timing.main(arguments + ["--limit", "0"] + restart)
                failed = startup_timing.main(
                    arguments + ["--", sys.executable, "-c", "raise SystemExit(1)"]
                )

        self.assertEqual((within, over, failed), (0, 1, 2))
        self.assertEqual(restarts, "xxx")
        self.assertNotIn("value", output.getvalue())


if __name__ == "__main__":
    unittest.main()
