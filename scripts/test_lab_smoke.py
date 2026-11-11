"""Offline tests for the plugin and alert checks in lab/smoke.py (issue #315)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lab"))
import smoke  # noqa: E402


class FakeApi:
    """Answers the Pinpoint routes the new checks use, from a small state."""

    def __init__(self, plugins=None, service_kind="ok", alert_on_break=True, clear_on_fix=True):
        if plugins is None:
            plugins = [{"id": 7, "name": "check_ssh"}]
        self.plugins = plugins
        self.service_kind = service_kind
        self.alert_on_break = alert_on_break
        self.clear_on_fix = clear_on_fix
        self.enabled = False
        self.down = False
        self.calls = []

    def call(self, method, path, body=None):
        self.calls.append((method, path))
        if method == "GET" and path.startswith("/api/plugin?"):
            return 200, {"data": {"items": self.plugins}}
        if method == "POST" and path.endswith("/enable"):
            self.enabled = True
            return 200, {"success": True, "data": {"status": "Active"}}
        if method == "GET" and path.endswith("/services?per_page=100"):
            items = []
            if self.enabled:
                items.append({"service": "ssh-22-tcp", "device": {"hostname": "dev-aaaaaa"},
                              "monitored": True, "status": {"kind": self.service_kind}})
            return 200, {"data": {"items": items}}
        if method == "GET" and path.startswith("/api/system/dashboard/alerts"):
            alerts = []
            if self.down and self.alert_on_break:
                alerts.append({"hostname": "dev-aaaaaa", "service_name": "ssh-22-tcp", "plugin_output": "refused"})
            return 200, {"data": {"alerts": alerts}}
        return 404, {}


class FakeLab:
    """Stands in for `scripts/lab`: records break and fix and flips the fake API."""

    def __init__(self, api, fix_ok=True):
        self.api = api
        self.fix_ok = fix_ok
        self.commands = []

    def __call__(self, *arguments):
        self.commands.append(arguments)
        if arguments[0] == "break":
            self.api.down = True
        if arguments[0] == "fix":
            if self.api.clear_on_fix:
                self.api.down = False
        return 0, "ok"


class PluginCheckTests(unittest.TestCase):
    def setUp(self):
        smoke.results.clear()

    def test_enable_then_service_ok_passes(self):
        api = FakeApi()
        self.assertTrue(smoke.plugin_service_checks(api, "check_ssh", timeout=1, interval=0))
        self.assertTrue(api.enabled)
        self.assertNotIn(False, smoke.results)

    def test_missing_plugin_fails(self):
        api = FakeApi(plugins=[])
        self.assertFalse(smoke.plugin_service_checks(api, "check_ssh", timeout=1, interval=0))
        self.assertIn(False, smoke.results)
        self.assertFalse(api.enabled)

    def test_service_never_ok_fails(self):
        api = FakeApi(service_kind="critical")
        self.assertFalse(smoke.plugin_service_checks(api, "check_ssh", timeout=0.05, interval=0.01))
        self.assertIn(False, smoke.results)

    def test_only_exact_plugin_name_is_used(self):
        api = FakeApi(plugins=[{"id": 1, "name": "check_ssh_extra"}])
        self.assertFalse(smoke.plugin_service_checks(api, "check_ssh", timeout=1, interval=0))
        self.assertFalse(api.enabled)


class AlertCheckTests(unittest.TestCase):
    def setUp(self):
        smoke.results.clear()

    def test_break_alert_fix_clear_passes(self):
        api = FakeApi()
        lab = FakeLab(api)
        self.assertTrue(smoke.alert_checks(api, lab, "web01", "ssh", timeout=1, interval=0))
        self.assertEqual([c[0] for c in lab.commands], ["break", "fix"])
        self.assertEqual(lab.commands[0], ("break", "web01", "ssh"))
        self.assertNotIn(False, smoke.results)

    def test_no_alert_fails_but_target_is_still_fixed(self):
        api = FakeApi(alert_on_break=False)
        lab = FakeLab(api)
        self.assertFalse(smoke.alert_checks(api, lab, "web01", "ssh", timeout=0.05, interval=0.01))
        self.assertEqual([c[0] for c in lab.commands], ["break", "fix"])
        self.assertIn(False, smoke.results)

    def test_alert_that_never_clears_fails(self):
        api = FakeApi(clear_on_fix=False)
        lab = FakeLab(api)
        self.assertFalse(smoke.alert_checks(api, lab, "web01", "ssh", timeout=0.05, interval=0.01))
        self.assertIn(False, smoke.results)

    def test_preexisting_alert_is_not_mistaken_for_new_one(self):
        api = FakeApi()
        api.down = True  # alert already active before the break
        lab = FakeLab(api)
        self.assertFalse(smoke.alert_checks(api, lab, "web01", "ssh", timeout=0.05, interval=0.01))


if __name__ == "__main__":
    unittest.main()
