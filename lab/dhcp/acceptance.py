"""Bounded live DHCP identity acceptance against real Pinpoint and Nagios.

Run only on the dedicated, approved issue #187 range. It creates a clean lab,
drives real DHCP and discovery, writes raw evidence outside the repository, and
tears down owned resources. Browser checks are run separately at checkpoints.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.cookiejar
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


CONTROL_PATH = Path(__file__).with_name("control.py")
CONTROL_SPEC = importlib.util.spec_from_file_location("dhcp_control", CONTROL_PATH)
control = importlib.util.module_from_spec(CONTROL_SPEC)
CONTROL_SPEC.loader.exec_module(control)
BASE_URL = f"http://127.0.0.1:{control.WEB_PORT}"


def wait_until(read, accept, *, timeout: float, interval: float = 3,
               clock=time.monotonic, sleep=time.sleep):
    """Poll until accepted or raise a timeout containing the last observation."""
    deadline = clock() + timeout
    last = None
    while clock() < deadline:
        last = read()
        if accept(last):
            return last
        sleep(interval)
    raise TimeoutError(f"wait timed out after {timeout}s; last={last!r}")


def assert_client_move(before: dict, after: dict) -> None:
    """Require unchanged runtime and all persistent identifiers plus only B."""
    for key in ("container_id", "boot_id", "mac", "client_id", "machine_id", "host_key"):
        assert before[key] == after[key], f"client {key} changed"
    assert before["addresses"] == [control.POOL[0]], "client A address missing before move"
    assert after["addresses"] == [control.POOL[1]], "client B address is not exclusive"


def assert_device_move(before: dict, after: dict) -> None:
    """Require one Pinpoint ID and Nagios host name across A-to-B."""
    assert before["id"] == after["id"], "Pinpoint device id changed"
    assert before["nagios_host_name"] == after["nagios_host_name"], "Nagios host name changed"
    assert before["ip_address"] == control.POOL[0], "initial device address is not A"
    assert after["ip_address"] == control.POOL[1], "moved device address is not B"


def assert_distinct_reuse(first: dict, second: dict) -> None:
    """Require A's new owner to have its own logical and Nagios identity."""
    assert first["id"] != second["id"], "IP reuse inherited the first device id"
    assert first["nagios_host_name"] != second["nagios_host_name"], "IP reuse inherited Nagios host name"
    assert first["ip_address"] == control.POOL[1], "first client no longer owns B"
    assert second["ip_address"] == control.POOL[0], "second client did not own A"


class Api:
    """Cookie-authenticated lab API; only the known loopback appliance is used."""

    def __init__(self):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        """Return a successful JSON response or raise with a sanitized status."""
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(BASE_URL + path, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with self.opener.open(request, timeout=20) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"API {method} {path} returned HTTP {error.code}") from error
        if not payload.get("success"):
            raise RuntimeError(f"API {method} {path} did not succeed: {payload.get('message')}")
        return payload.get("data") or {}

    def login(self) -> None:
        """Authenticate with the seeded disposable lab account."""
        password = os.environ.get("DHCP_LAB_ADMIN_PASSWORD", "Password123!")
        self.call("POST", "/api/user/login", {"email": "admin@test.com", "password": password})


def client_identity(client: str, data: dict) -> dict:
    """Read runtime, MAC, configured client ID, machine ID and SSH host key."""
    item = control.check_container(client, data["token"])
    def cat(path: str) -> str:
        return control.docker("exec", control.name(client), "cat", path).stdout.strip()
    return {
        "container_id": item["Id"],
        "boot_id": cat("/proc/sys/kernel/random/boot_id"),
        "mac": cat("/sys/class/net/eth1/address"),
        "client_id": cat("/etc/dhcp/dhclient-eth1.conf"),
        "machine_id": cat("/etc/machine-id"),
        "host_key": cat("/etc/ssh/ssh_host_ed25519_key.pub").split()[1],
        "addresses": control.client_addresses(client),
    }


def server_lease(client: str, address: str) -> None:
    """Require a current dnsmasq lease record for the client and address."""
    leases = control.docker("exec", control.name("switch"), "cat", "/tmp/dnsmasq.leases").stdout
    fields = [line.split() for line in leases.splitlines()]
    assert any(len(row) >= 3 and row[1] == control.MACS[client] and row[2] == address
               for row in fields), f"server has no {client} lease at {address}"


def probe_service(address: str) -> None:
    """Require HTTP and SSH host-key responses over the appliance test NIC."""
    appliance = control.name("appliance")
    control.docker("exec", appliance, "curl", "-fsS", "--max-time", "5", f"http://{address}/")
    result = control.docker("exec", appliance, "ssh-keyscan", "-T", "5", "-t", "ed25519",
                            address, timeout=10)
    assert "ssh-ed25519" in result.stdout, f"SSH did not answer at {address}"


def scan(api: Api, *, timeout: int = 360) -> dict:
    """Run real discovery only when the appliance's range is exactly approved."""
    settings = api.call("GET", "/api/system/discovery-settings").get("settings") or {}
    assert settings.get("networks") == [control.RANGE], "unapproved discovery setting; no scan started"
    api.call("POST", "/api/system/discover/start")
    outcome = wait_until(lambda: api.call("GET", "/api/system/discover/status"),
                         lambda item: str(item.get("status", "")).lower() in
                         {"success", "failed", "error", "interrupted"},
                         timeout=timeout, interval=4)
    assert str(outcome["status"]).lower() == "success", f"discovery failed: {outcome}"
    return outcome


def device_at(api: Api, address: str) -> dict:
    """Find one ACTIVE device; displaced records can retain historical IPs."""
    query = urllib.parse.quote(address, safe="")
    rows = api.call("GET", f"/api/system/hosts/lookup?search={query}").get("items") or []
    matches = [row for row in rows if row.get("ip_address") == address and row.get("state") == "ACTIVE"]
    assert len(matches) == 1, f"expected one active device at {address}, found {len(matches)}; rows={rows}"
    return matches[0]


def host_status(api: Api, hostname: str) -> dict | None:
    """Read the latest Pinpoint snapshot for one Nagios host."""
    rows = api.call("GET", "/api/system/network-health/hosts?per_page=100").get("items") or []
    return next((row for row in rows if row.get("hostname") == hostname), None)


def wait_up(api: Api, hostname: str, address: str, *, newer_than: str = "") -> dict:
    """Bound a fresh UP snapshot for the stable Nagios host at its new IP."""
    return wait_until(lambda: host_status(api, hostname),
                      lambda row: bool(row) and str(row.get("state", "")).upper() == "UP"
                      and row.get("ip_address") == address
                      and bool(row.get("last_check")) and row["last_check"] > newer_than,
                      timeout=240, interval=5)


def nagios_config(hostname: str, address: str) -> None:
    """Require one generated host stanza at address and a valid Nagios config."""
    appliance = control.name("appliance")
    content = control.docker("exec", appliance, "cat",
                             "/usr/local/nagios/etc/objects/hosts.cfg").stdout
    stanzas = re.findall(r"define host\s*\{([^}]+)\}", content, re.S)
    matches = [stanza for stanza in stanzas if re.search(rf"\bhost_name\s+{re.escape(hostname)}(?:\s|$)", stanza)]
    assert len(matches) == 1, f"expected one Nagios host stanza for {hostname}"
    assert re.search(rf"\baddress\s+{re.escape(address)}(?:\s|$)", matches[0]), "Nagios address is stale"
    control.docker("exec", appliance, "/usr/local/nagios/bin/nagios", "-v",
                   "/usr/local/nagios/etc/nagios.cfg", timeout=90)


def address_history(api: Api, device_id: int, old: str, new: str) -> None:
    """Require the old address closed and the new one current on the same ID."""
    rows = api.call("GET", f"/api/system/hosts/{device_id}/addresses").get("addresses") or []
    assert any(row["ip_address"] == old and not row["current"] for row in rows), "old address history missing"
    assert any(row["ip_address"] == new and row["current"] for row in rows), "new current address missing"


def pre_move_events(api: Api, hostname: str) -> list[dict]:
    """Read real Nagios host DOWN events from the archive-backed API."""
    query = urllib.parse.urlencode({"preset": "24h", "type": "host", "hostname": hostname,
                                    "new_state": "DOWN", "per_page": 100})
    rows = api.call("GET", f"/api/system/history/alerts?{query}").get("items") or []
    return [row for row in rows if row.get("hostname") == hostname
            and row.get("type") == "host" and row.get("new_state") == "DOWN"]


def make_history_marker(api: Api, hostname: str, data: dict) -> dict:
    """Drop only client-1's test NIC until Nagios records a real host alert."""
    before = {row.get("event_id") for row in pre_move_events(api, hostname)}
    client = control.name("client1")
    control.docker("exec", client, "ip", "link", "set", "eth1", "down")
    try:
        api.call("POST", f"/api/system/network-health/hosts/{urllib.parse.quote(hostname, safe='')}/recheck")
        event = wait_until(lambda: pre_move_events(api, hostname),
                           lambda rows: next((row for row in rows if row.get("event_id") not in before), None),
                           timeout=240, interval=5)
        marker = next(row for row in event if row.get("event_id") not in before)
    finally:
        control.docker("exec", client, "ip", "link", "set", "eth1", "up")
    if control.client_addresses("client1") != [control.POOL[0]]:
        control.acquire("client1", data)
    probe_service(control.POOL[0])
    return {"event_id": marker.get("event_id"), "timestamp": marker.get("timestamp"),
            "hostname": hostname}


def browser_checkpoint(first_host: str, second_host: str, data: dict) -> Path:
    """Drive real Inventory and History pages in Chromium and save screenshots."""
    client_dir = control.ROOT / "client"
    playwright = client_dir / "node_modules/.bin/playwright"
    if not playwright.exists():
        raise RuntimeError("install client dependencies with npm ci before browser acceptance")
    output = control.evidence(data)
    vite_log = (output / "vite.log").open("w")
    environment = os.environ.copy()
    environment["API_PROXY_TARGET"] = BASE_URL
    environment["ISSUE187_LAB_URL"] = "http://127.0.0.1:5174"
    environment["ISSUE187_FIRST_HOST"] = first_host
    environment["ISSUE187_SECOND_HOST"] = second_host
    environment["ISSUE187_EVIDENCE_DIR"] = str(output)
    environment["PINPOINT_ADMIN_USER"] = "admin@test.com"
    environment["PINPOINT_ADMIN_PASSWORD"] = os.environ.get("DHCP_LAB_ADMIN_PASSWORD", "Password123!")
    vite = subprocess.Popen(["npm", "run", "dev", "--", "--host", "127.0.0.1",
                             "--port", "5174", "--strictPort"], cwd=client_dir,
                            env=environment, stdout=vite_log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        def ready():
            if vite.poll() is not None:
                raise RuntimeError(f"Vite exited with {vite.returncode}")
            try:
                with urllib.request.urlopen("http://127.0.0.1:5174/login", timeout=2) as response:
                    return response.status == 200
            except (urllib.error.URLError, TimeoutError, ConnectionResetError):
                return False
        wait_until(ready, bool, timeout=40, interval=1)
        result = subprocess.run([str(playwright), "test", "--project", "issue-187-live",
                                 "--reporter", "line"], cwd=client_dir, env=environment,
                                text=True, capture_output=True, timeout=180, check=False)
        (output / "playwright.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"browser checkpoint failed with exit {result.returncode}; see {output / 'playwright.log'}")
        return output
    finally:
        os.killpg(vite.pid, signal.SIGTERM)
        vite.wait(timeout=10)
        vite_log.close()


def record(results: list[dict], case: str, action) -> bool:
    """Run one case, preserve a timestamped pass/fail and avoid synthetic success."""
    started = time.monotonic()
    try:
        detail = action() or {}
        results.append({"case": case, "result": "Pass", "elapsed_seconds": round(time.monotonic() - started, 1),
                        "detail": detail})
        return True
    except Exception as error:
        results.append({"case": case, "result": "Fail", "elapsed_seconds": round(time.monotonic() - started, 1),
                        "first_failure": f"{type(error).__name__}: {error}"})
        return False


def run_cycle(number: int, *, full_matrix: bool, lease_seconds: int) -> tuple[list[dict], Path]:
    """Run primary cases on a fresh lab; cycle one also exercises the matrix."""
    results: list[dict] = []
    control.setup(lease_seconds)
    data = control.state()
    api = Api()
    output: Path | None = None
    try:
        api.login()
        def record_case(case: str, action) -> bool:
            passed = record(results, case, action)
            if not passed:
                control.evidence(data)
            return passed

        first = client_identity("client1", data)
        assert first["addresses"] == [control.POOL[0]]
        server_lease("client1", control.POOL[0])
        probe_service(control.POOL[0])

        def initial():
            scan(api)
            device = device_at(api, control.POOL[0])
            nagios_config(device["nagios_host_name"], control.POOL[0])
            host = wait_up(api, device["nagios_host_name"], control.POOL[0])
            return {"device": device, "host": host}
        baseline: dict = {}
        if record_case("initial discovery and check at A", lambda: baseline.update(initial())):
            device_a = baseline["device"]
            before_check = baseline["host"]["last_check"]
        else:
            device_a = None
            before_check = ""

        marker_ok = (record_case("pre-move browser history marker",
                                 lambda: make_history_marker(api, device_a["nagios_host_name"], data))
                     if device_a else False)

        if full_matrix:
            def renewal():
                path = f"/tmp/dnsmasq-{data['generation']}.log"
                before = control.docker("exec", control.name("switch"), "cat", path).stdout.count("DHCPACK(brdhcp) 10.79.0.5")
                wait_until(lambda: control.docker("exec", control.name("switch"), "cat", path).stdout.count("DHCPACK(brdhcp) 10.79.0.5"),
                           lambda count: count > before, timeout=lease_seconds + 30, interval=5)
                control.require_test_address(control.client_addresses("client1"), control.POOL[0])
                if device_a:
                    scan(api)
                    assert device_at(api, control.POOL[0])["id"] == device_a["id"]
                return {"address": control.POOL[0]}
            record_case("unchanged-address renewal", renewal)

        def moved():
            control.release("client1", data)
            control.reserve("client1", control.POOL[1], data)
            control.acquire("client1", data)
            after = client_identity("client1", data)
            assert_client_move(first, after)
            server_lease("client1", control.POOL[1])
            probe_service(control.POOL[1])
            scan(api)
            device_b = device_at(api, control.POOL[1])
            if device_a:
                assert_device_move(device_a, device_b)
                address_history(api, device_a["id"], control.POOL[0], control.POOL[1])
            nagios_config(device_b["nagios_host_name"], control.POOL[1])
            host = wait_up(api, device_b["nagios_host_name"], control.POOL[1], newer_than=before_check)
            return {"device": device_b, "host": host, "before": first, "after": after}
        move_detail: dict = {}
        move_ok = record_case("same-running-client A-to-B", lambda: move_detail.update(moved()))

        def reused():
            control.reserve("client2", control.POOL[0], data)
            control.acquire("client2", data)
            second = client_identity("client2", data)
            assert second["mac"] != first["mac"] and second["host_key"] != first["host_key"]
            server_lease("client1", control.POOL[1])
            server_lease("client2", control.POOL[0])
            probe_service(control.POOL[0])
            scan(api)
            other = device_at(api, control.POOL[0])
            if move_ok:
                assert_distinct_reuse(move_detail["device"], other)
            host = wait_up(api, other["nagios_host_name"], control.POOL[0])
            review = api.call("GET", "/api/system/discover/review").get("items") or []
            return {"device": other, "host": host,
                    "review_kinds": [item.get("kind") for item in review]}
        reuse_detail: dict = {}
        reuse_ok = record_case("client-2 reuses released A", lambda: reuse_detail.update(reused()))

        if move_ok and reuse_ok and marker_ok:
            record_case("browser Inventory and pre-move History",
                        lambda: {"raw_evidence": str(browser_checkpoint(
                            move_detail["device"]["nagios_host_name"],
                            reuse_detail["device"]["nagios_host_name"], data))})
        else:
            results.append({"case": "browser Inventory and pre-move History", "result": "Blocked",
                            "first_failure": "required move, reuse or history marker did not pass"})

        if full_matrix:
            def restart():
                before = client_identity("client1", data)
                control.release("client1", data)
                control.docker("restart", control.name("client1"), timeout=90)
                control.attach("client1", "v1", data["token"])
                control.acquire("client1", data)
                after = client_identity("client1", data)
                for key in ("container_id", "mac", "client_id", "machine_id", "host_key"):
                    assert before[key] == after[key], f"restart changed {key}"
                scan(api)
                if move_ok:
                    assert device_at(api, control.POOL[1])["id"] == move_detail["device"]["id"]
                return {"address": after["addresses"]}
            record_case("persistent-identity restart", restart)

            def outage():
                control.stop_server(data)
                observed = wait_until(lambda: control.client_addresses("client1"),
                                      lambda addresses: addresses != [control.POOL[1]],
                                      timeout=lease_seconds * 2 + 30, interval=5)
                control.start_server(data)
                try:
                    wait_until(lambda: control.client_addresses("client1"),
                               lambda addresses: addresses == [control.POOL[1]],
                               timeout=lease_seconds + 30, interval=5)
                except TimeoutError:
                    control.acquire("client1", data)
                server_lease("client1", control.POOL[1])
                scan(api)
                return {"after_expiry": observed, "recovered": control.client_addresses("client1")}
            record_case("server outage and recovery", outage)

            def round_trip():
                if reuse_ok:
                    control.release("client2", data)
                    control.reserve("client2", None, data)
                control.release("client1", data)
                control.reserve("client1", control.POOL[0], data)
                control.acquire("client1", data)
                scan(api)
                at_a = device_at(api, control.POOL[0])
                if device_a:
                    assert at_a["id"] == device_a["id"]
                nagios_config(at_a["nagios_host_name"], control.POOL[0])
                control.release("client1", data)
                control.reserve("client1", control.POOL[1], data)
                control.acquire("client1", data)
                scan(api)
                at_b = device_at(api, control.POOL[1])
                assert at_b["id"] == at_a["id"]
                nagios_config(at_b["nagios_host_name"], control.POOL[1])
                return {"device_id": at_b["id"]}
            record_case("repeat B-to-A and A-to-B", round_trip)

        output = control.evidence(data)
        (output / "acceptance.json").write_text(json.dumps({"cycle": number,
                                                             "commit": control.run(["git", "-C", str(control.ROOT), "rev-parse", "HEAD"]).stdout.strip(),
                                                             "range": control.RANGE, "lease_seconds": lease_seconds,
                                                             "cases": results}, indent=2) + "\n")
        return results, output
    finally:
        if output is None:
            try:
                control.evidence(data)
            except Exception as error:
                print(f"evidence capture failed: {error}", file=sys.stderr)
        control.teardown()


def main() -> int:
    """Run one full matrix and a second clean primary sequence with fixed bounds."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lease-seconds", type=int, default=90)
    args = parser.parse_args()
    if not 60 <= args.lease_seconds <= 3600:
        parser.error("lease-seconds must be 60..3600")
    all_results = []
    for cycle in (1, 2):
        try:
            results, output = run_cycle(cycle, full_matrix=cycle == 1,
                                        lease_seconds=args.lease_seconds)
            print(f"cycle {cycle} raw evidence: {output}")
            all_results.extend(results)
        except Exception as error:
            print(f"cycle {cycle} failed before all cases: {error}", file=sys.stderr)
            return 1
    for result in all_results:
        print(f"{result['result']:4} {result['case']} ({result['elapsed_seconds']}s)")
    return 0 if all(result["result"] == "Pass" for result in all_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
