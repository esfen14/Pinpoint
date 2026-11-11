"""Smoke checks for the local lab (scripts/lab smoke).

Logs in, runs Network Discovery against the lab network, and waits until
Pinpoint shows every target as monitored and up. Standard library only; talks
to http://127.0.0.1:8000. Exit status 0 when every check passes.

    scripts/lab smoke [--base-url URL] [--discovery-timeout S] [--hosts-timeout S]

With --lab-script (scripts/lab passes it) the smoke test also enables the SSH plugin
and checks the service it creates, then takes a target's sshd down with
`scripts/lab break`, checks the alert, and brings it back with `fix` (#315).

With --mail-sink-url (scripts/lab passes it) it also saves the Email settings against the lab
mail sink (lab/mail), sends the test email, and checks that the break/fix alert's notification
mail reaches the sink through Nagios, `/bin/mail` and msmtp (#316).

For a real appliance (scripts/vmlab smoke) pass the administrator's --email and
--password and, if discovery does not already cover the lab, --set-network CIDR.
"""
import argparse
import http.cookiejar
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

TARGETS = ["web01", "web02", "app01", "snmp01", "legacy01"]
DEFAULT_EMAIL = "admin@test.com"
DEFAULT_PASSWORD = "Password123!"


class Client:
    """A tiny cookie-keeping JSON client for the Pinpoint API."""

    def __init__(self, base):
        self.base = base.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with self.opener.open(request, timeout=30) as response:
                return response.status, json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.loads(error.read() or b"{}")
            except ValueError:
                return error.code, {}


results = []


def check(name, ok, detail=""):
    """Record and print one PASS/FAIL line."""
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    return ok


def ensure_discovery_network(api, cidr):
    """
    Make sure Network Discovery scans cidr. Appliances installed by the installer
    scan the subnet of their own interface, not the lab network. Reads the settings,
    and only if cidr is missing writes them back with the network added.
    """
    status, body = api.call("GET", "/api/system/discovery-settings")
    settings = (body.get("data") or {}).get("settings")
    if status != 200 or not isinstance(settings, dict):
        return check(f"read discovery settings", False, f"HTTP {status}")
    networks = list(settings.get("networks") or [])
    if cidr in networks:
        return check(f"discovery already covers {cidr}", True)
    settings["networks"] = networks + [cidr]
    status, body = api.call("PUT", "/api/system/discovery-settings", settings)
    return check(f"add {cidr} to the discovery networks", status == 200 and body.get("success"), f"HTTP {status}: {body.get('message')}")


def wait_for(predicate, timeout, interval=5):
    """Poll predicate() until it returns a truthy value or the timeout passes."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return None


def plugin_service_checks(api, plugin_name, timeout, interval=5):
    """
    Enable plugin_name, then wait until every service it created reports OK.
    Returns True when the plugin was found, enabled and its services are healthy.
    """
    status, body = api.call("GET", f"/api/plugin?search={plugin_name}&per_page=100")
    plugin_id = None
    for item in (body.get("data") or {}).get("items") or []:
        if item.get("name") == plugin_name:
            plugin_id = item.get("id")
    if not check(f"plugin {plugin_name} is in the Plugin Manager", status == 200 and plugin_id is not None, f"HTTP {status}"):
        return False

    status, body = api.call("POST", f"/api/plugin/{plugin_id}/enable")
    if not check(f"enable {plugin_name}", status == 200 and body.get("success"), f"HTTP {status}: {body.get('message')}"):
        return False

    def services():
        _, listing = api.call("GET", f"/api/plugin/{plugin_id}/services?per_page=100")
        return (listing.get("data") or {}).get("items") or []

    def all_ok():
        items = services()
        if not items:
            return None
        for item in items:
            if (item.get("status") or {}).get("kind") != "ok":
                return None
        return items

    healthy = wait_for(all_ok, timeout, interval=interval)
    if healthy:
        detail = f"{len(healthy)} services OK"
    else:
        kinds = []
        for item in services():
            kinds.append(f"{item.get('service')}: {(item.get('status') or {}).get('kind')}")
        detail = "; ".join(kinds) or "no service was created"
    return check(f"{plugin_name} created services and they report OK", bool(healthy), detail)


def active_alert_keys(api):
    """Return the set of (hostname, service_name) pairs in the active alerts feed."""
    status, body = api.call("GET", "/api/system/dashboard/alerts?limit=100&ack_filter=all")
    keys = set()
    if status != 200:
        return keys
    for alert in (body.get("data") or {}).get("alerts") or []:
        keys.add((alert.get("hostname"), alert.get("service_name")))
    return keys


def run_lab_script(path):
    """Return a function that runs `path <args>` and gives (exit code, output)."""
    def run(*arguments):
        result = subprocess.run([path, *arguments], capture_output=True, text=True, timeout=120)
        return result.returncode, (result.stdout + result.stderr).strip()
    return run


SINK_SETTINGS = {
    "provider": "custom", "host": "mail01", "port": 587, "tls": "starttls",
    "username": "lab-smtp-user", "sender": "pinpoint@lab.test",
    # The sink's own login; spaces and "#" check the helper's quoting.
    "password": "lab smtp pass #1",
}


def sink_messages(url, clear=False):
    request = urllib.request.Request(url.rstrip("/") + "/messages", method="DELETE" if clear else "GET")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read() or b"[]")


def smtp_settings_checks(api, sink_url, email):
    """Save the Email settings (runs pinpoint-apply-smtp through sudo) and send the test email."""
    sink_messages(sink_url, clear=True)
    status, body = api.call("GET", "/api/system/smtp-settings")
    version = ((body.get("data") or {}).get("settings") or {}).get("version", 0)
    status, body = api.call("PUT", "/api/system/smtp-settings", dict(SINK_SETTINGS, version=version))
    if not check("save the Email settings against the lab mail sink", status == 200 and body.get("success"),
                 f"HTTP {status}: {body.get('message')}"):
        return False
    status, body = api.call("POST", "/api/system/smtp-settings/test")
    result = body.get("data") or {}
    if not check("the test email is sent over STARTTLS with a login", status == 200 and result.get("ok"),
                 str(result.get("message") or result.get("details") or f"HTTP {status}")[:120]):
        return False
    received = [m for m in sink_messages(sink_url) if email in m["to"]]
    return check("the sink received the test email", bool(received), f"{len(received)} message(s) to {email}")


def notification_mail_check(sink_url, timeout, interval=5):
    """Nagios mails the alert through /bin/mail and msmtp; the sink must receive it."""
    found = wait_for(lambda: sink_messages(sink_url) or None, timeout, interval=interval)
    return check("the alert's notification email reaches the sink through msmtp", bool(found),
                 found[0]["subject"][:80] if found else f"none in {timeout}s")


def alert_checks(api, lab, target, service, timeout, interval=5):
    """
    Take target's service down with lab("break", ...), wait for a new alert, bring it
    back with lab("fix", ...) (always, even when a check fails) and wait for the alert
    to clear. Pinpoint names discovered hosts dev-xxxxxx, so the alert is the pair that
    was not in the feed before the break.
    """
    before = active_alert_keys(api)
    code, output = lab("break", target, service)
    if not check(f"break {target} {service}", code == 0, output[:80]):
        return False

    new_key = None
    try:
        def new_alert():
            for key in active_alert_keys(api) - before:
                return key
            return None

        new_key = wait_for(new_alert, timeout, interval=interval)
        check("a new alert appears in the active alerts feed", new_key is not None,
              f"{new_key[0]} / {new_key[1]}" if new_key else f"none in {timeout}s")
    finally:
        code, output = lab("fix", target, service)
        check(f"fix {target} {service}", code == 0, output[:80])

    if new_key is None:
        return False
    cleared = wait_for(lambda: new_key not in active_alert_keys(api), timeout, interval=interval)
    return check("the alert clears after the service is back", cleared is not None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--discovery-timeout", type=int, default=1200)
    parser.add_argument("--hosts-timeout", type=int, default=240)
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="administrator email (default: the lab's seeded user)")
    parser.add_argument("--password", default=os.environ.get("SMOKE_PASSWORD", DEFAULT_PASSWORD),
                        help="administrator password (or set SMOKE_PASSWORD, which keeps it out of the process list)")
    parser.add_argument("--set-network", metavar="CIDR", help="add this network to Network Discovery if missing")
    parser.add_argument("--expect-ips", default="", metavar="IP,IP,...",
                        help="check the targets by address instead of by name (real appliances name hosts dev-xxxxxx)")
    parser.add_argument("--lab-script", metavar="PATH",
                        help="path to scripts/lab: also check an enabled plugin and a break/fix alert (local Docker lab only)")
    parser.add_argument("--mail-sink-url", metavar="URL",
                        help="lab mail sink (scripts/lab passes it): also check the Email settings and notification mail")
    parser.add_argument("--plugin", default="check_ssh", help="plugin to enable (default: check_ssh)")
    parser.add_argument("--break-target", default="web01", help="lab target to take down (default: web01)")
    parser.add_argument("--break-service", default="ssh", help="its service to stop: ssh, http or snmp (default: ssh)")
    parser.add_argument("--service-timeout", type=int, default=300, help="seconds to wait for a service check or an alert")
    args = parser.parse_args()
    api = Client(args.base_url)

    status, body = api.call("POST", "/api/user/login", {"email": args.email, "password": args.password})
    if not check("log in as the administrator", status == 200 and body.get("success"), f"HTTP {status}"):
        print("Is the appliance running and are the credentials right?")
        return 1
    if body.get("data", {}).get("needs_setup"):
        check("administrator has completed first-run setup", False, "run: scripts/vmlab setup-admin")
        return 1
    if body.get("data", {}).get("must_change_password"):
        check("administrator has no pending password change", False, "sign in once in the browser and set a new password")
        return 1
    if args.set_network and not ensure_discovery_network(api, args.set_network):
        return 1

    status, body = api.call("POST", "/api/system/discover/start")
    if not check("start Network Discovery", status in (200, 202) and body.get("success"), f"HTTP {status}: {body.get('message')}"):
        return 1

    def discovery_finished():
        _, current = api.call("GET", "/api/system/discover/status")
        data = current.get("data") or {}
        return data if str(data.get("status")).lower() in {"success", "failed", "error", "cancelled", "stopped"} else None

    started = time.time()
    outcome = wait_for(discovery_finished, args.discovery_timeout, interval=4)
    took = int(time.time() - started)
    check(
        "discovery finishes and applies the Nagios config",
        bool(outcome) and str(outcome.get("status")).lower() == "success",
        f"{outcome.get('status')}, {took}s, {outcome.get('message')}" if outcome else f"no result after {took}s",
    )

    def host_items():
        _, listing = api.call("GET", "/api/system/network-health/hosts?per_page=100")
        data = listing.get("data") or {}
        return data.get("items") or data.get("hosts") or []

    expected = [ip.strip() for ip in args.expect_ips.split(",") if ip.strip()]
    if expected:
        # By address: a total-host count can be satisfied by unrelated hosts (the
        # installer's default range finds the VirtualBox NAT's own addresses).
        def states():
            return {str(h.get("ip_address")): str(h.get("state")).lower() for h in host_items()}

        wait_for(lambda: all(states().get(ip) == "up" for ip in expected), args.hosts_timeout, interval=10)
        final = states()
        for ip in expected:
            check(f"{ip} is monitored and Up", final.get(ip) == "up", f"state: {final.get(ip, 'not in the host table')}")
    else:
        def hosts_up():
            _, summary = api.call("GET", "/api/system/network-health/summary")
            hosts = (summary.get("data") or {}).get("hosts") or {}
            return hosts if hosts.get("up", 0) >= len(TARGETS) + 1 else None

        hosts = wait_for(hosts_up, args.hosts_timeout, interval=10)
        check(
            "Pinpoint shows the targets and localhost as up",
            bool(hosts),
            f"{hosts['up']} up of {hosts['total']}" if hosts else "not all hosts up in time",
        )
        names = [str(item.get("hostname") or item.get("host_name") or "") for item in host_items()]
        for target in TARGETS:
            check(f"host table lists {target}", any(target in name for name in names))

    mail_ready = bool(args.mail_sink_url) and smtp_settings_checks(api, args.mail_sink_url, args.email)

    if args.lab_script:
        if plugin_service_checks(api, args.plugin, args.service_timeout):
            if mail_ready:
                sink_messages(args.mail_sink_url, clear=True)
            alert_checks(api, run_lab_script(args.lab_script), args.break_target, args.break_service, args.service_timeout)
            if mail_ready:
                notification_mail_check(args.mail_sink_url, args.service_timeout)

    failed = results.count(False)
    print(f"\n{len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
