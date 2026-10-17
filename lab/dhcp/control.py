"""Own and control the opt-in Docker DHCP segment for issue #187.

All Docker mutations use exact names and a per-run owner token. The test bridge
lives inside the switch container's network namespace, never on the host.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
RANGE = "10.79.0.0/28"
SERVER_IP = "10.79.0.1"
APPLIANCE_IP = "10.79.0.2"
POOL = ("10.79.0.5", "10.79.0.6")
MACS = {"client1": "02:79:00:00:00:01", "client2": "02:79:00:00:00:02"}
PREFIX = "pinpoint-dhcp187"
NETWORK = f"{PREFIX}-mgmt"
ROLES = ("switch", "appliance", "client1", "client2")
OWNER_LABEL = "org.pinpoint.dhcp.owner"
ROLE_LABEL = "org.pinpoint.dhcp.role"
STATE_DIR = Path.home() / ".local/share/pinpoint-dhcp-lab-187"
STATE_FILE = STATE_DIR / "owner.json"
EVIDENCE_ROOT = Path.home() / "pinpoint-test-results/issue-187-dhcp"
WEB_PORT = 18087


def run(argv: list[str], *, input_text: str | None = None, timeout: int = 45,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a bounded argument-list command, returning output without a shell."""
    return subprocess.run(argv, input=input_text, text=True, capture_output=True,
                          timeout=timeout, check=check)


def docker(*args: str, input_text: str | None = None, timeout: int = 45,
           check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run one bounded Docker command with captured output."""
    return run(["docker", *args], input_text=input_text, timeout=timeout, check=check)


def name(role: str) -> str:
    """Return the fixed name of one lab container."""
    if role not in ROLES:
        raise ValueError(f"invalid role: {role}")
    return f"{PREFIX}-{role}"


def validate_range(candidate: str, occupied: list[str]) -> None:
    """Reject any route, interface or Docker subnet overlapping the test range."""
    test = ipaddress.ip_network(candidate, strict=True)
    if candidate != RANGE:
        raise ValueError("unapproved test range")
    for value in occupied:
        other = ipaddress.ip_network(value, strict=False)
        if test.overlaps(other):
            raise ValueError(f"test range overlap: {other}")


def require_owned(labels: dict[str, str], token: str, role: str) -> None:
    """Refuse mutation unless both the private owner token and role match."""
    if labels.get(OWNER_LABEL) != token or labels.get(ROLE_LABEL) != role:
        raise ValueError(f"resource ownership mismatch for {role}")


def render_dnsmasq(reservations: dict[str, str | None]) -> str:
    """Render one segment-bound allocator with fixed infrastructure and known MACs."""
    active = [address for address in reservations.values() if address is not None]
    if len(active) != len(set(active)):
        raise ValueError("duplicate DHCP reservation")
    if any(address not in POOL for address in active):
        raise ValueError("reservation outside DHCP pool")
    lines = [
        "port=0", "interface=brdhcp", "bind-interfaces", "except-interface=lo",
        "dhcp-authoritative", "dhcp-ignore=tag:!known",
        f"dhcp-range={POOL[0]},{POOL[1]},255.255.255.240,10m",
        "dhcp-option=option:router", "dhcp-option=option:dns-server",
        "dhcp-leasefile=/tmp/dnsmasq.leases", "log-dhcp",
    ]
    for client in MACS:
        address = reservations.get(client)
        if address is not None:
            lines.append(f"dhcp-host={MACS[client]},{address}")
    return "\n".join(lines) + "\n"


def require_test_address(addresses: list[str], expected: str) -> None:
    """Reject a missing lease or any stale/extra address on the DHCP NIC."""
    if addresses != [expected]:
        raise ValueError(f"unexpected test address: {addresses}; expected {expected}")


def state() -> dict:
    """Read the local owner marker without following a symbolic link."""
    if STATE_FILE.is_symlink() or STATE_DIR.is_symlink() or not STATE_FILE.is_file():
        raise ValueError("DHCP lab owner state is absent or unsafe")
    data = json.loads(STATE_FILE.read_text())
    if data.get("version") != 1 or not isinstance(data.get("token"), str) or len(data["token"]) < 32:
        raise ValueError("DHCP lab owner state is invalid")
    return data


def save_state(data: dict) -> None:
    """Atomically save nonsecret reservations and the private owner token."""
    temporary = STATE_DIR / "owner.json.tmp"
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(STATE_FILE)


def inspect_container(role: str) -> dict:
    """Read Docker's metadata for one fixed lab container."""
    result = docker("inspect", name(role))
    return json.loads(result.stdout)[0]


def check_container(role: str, token: str) -> dict:
    """Return a container only after its exact owner labels are verified."""
    item = inspect_container(role)
    require_owned(item["Config"].get("Labels") or {}, token, role)
    return item


def check_network(token: str) -> dict:
    """Verify ownership of the separate Docker bridge for loopback management."""
    item = json.loads(docker("network", "inspect", NETWORK).stdout)[0]
    require_owned(item.get("Labels") or {}, token, "mgmt")
    if item.get("Driver") != "bridge" or item.get("Attachable"):
        raise ValueError("management network is not the expected private bridge")
    return item


def preflight() -> None:
    """Check route collision, Docker access, loopback port and unused names."""
    docker("info", "--format", "{{.ServerVersion}}")
    occupied = []
    for route in json.loads(run(["ip", "-j", "-4", "route", "show", "table", "all"]).stdout):
        destination = route.get("dst")
        if destination and destination != "default":
            occupied.append(destination)
    for interface in json.loads(run(["ip", "-j", "-4", "addr", "show"]).stdout):
        for address in interface.get("addr_info", []):
            occupied.append(f"{address['local']}/{address['prefixlen']}")
    networks = json.loads(docker("network", "inspect", *docker("network", "ls", "-q").stdout.split()).stdout)
    for network in networks:
        for config in network.get("IPAM", {}).get("Config") or []:
            if config.get("Subnet"):
                occupied.append(config["Subnet"])
    # Existing VM demo uses this internal range even while powered off.
    occupied.append("10.77.0.0/28")
    validate_range(RANGE, occupied)
    if STATE_DIR.exists():
        raise ValueError("existing DHCP lab state; use status/down, or resolve ownership")
    for role in ROLES:
        if docker("container", "inspect", name(role), check=False).returncode == 0:
            raise ValueError(f"container {name(role)} already exists")
    if docker("network", "inspect", NETWORK, check=False).returncode == 0:
        raise ValueError(f"network {NETWORK} already exists")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", WEB_PORT))


def build_images() -> None:
    """Build dedicated images without changing the regular Docker lab."""
    docker("build", "-q", "-t", f"{PREFIX}-appliance-base:latest", "-f",
           str(ROOT / "lab/appliance/Dockerfile"), str(ROOT), timeout=1200)
    docker("build", "-q", "-t", f"{PREFIX}-appliance:latest", "-f",
           str(ROOT / "lab/dhcp/appliance.Dockerfile"), str(ROOT), timeout=300)
    docker("build", "-q", "-t", f"{PREFIX}-node:latest", "-f",
           str(ROOT / "lab/dhcp/Dockerfile"), str(ROOT), timeout=600)


def create_resources(data: dict) -> None:
    """Create a private management path, switch and distinct target containers."""
    token = data["token"]
    docker("network", "create", "--driver", "bridge", "--label", f"{OWNER_LABEL}={token}",
           "--label", f"{ROLE_LABEL}=mgmt", NETWORK)
    common = ["--label", f"{OWNER_LABEL}={token}"]
    docker("run", "-d", "--name", name("switch"), *common,
           "--label", f"{ROLE_LABEL}=switch", "--network", "none", "--pid", "host",
           "--cap-add", "NET_ADMIN", f"{PREFIX}-node:latest")
    docker("run", "-d", "--name", name("appliance"), *common,
           "--label", f"{ROLE_LABEL}=appliance", "--network", NETWORK,
           "--cap-add", "NET_ADMIN", "--cap-add", "NET_RAW",
           "-p", f"127.0.0.1:{WEB_PORT}:80", "-v", f"{ROOT}:/src:ro",
           f"{PREFIX}-appliance:latest")
    for client in MACS:
        docker("run", "-d", "--name", name(client), *common,
               "--label", f"{ROLE_LABEL}={client}", "--network", NETWORK,
               "--cap-add", "NET_ADMIN", "--hostname", client,
               "--entrypoint", "/usr/local/bin/dhcp-client-entrypoint",
               f"{PREFIX}-node:latest", client)


def attach(role: str, port: str, token: str) -> None:
    """Move a fresh veth peer from the switch into an owned container namespace."""
    item = check_container(role, token)
    check_container("switch", token)
    pid = item["State"]["Pid"]
    if not item["State"]["Running"] or not isinstance(pid, int) or pid < 2:
        raise ValueError(f"{role} has no running namespace")
    switch = name("switch")
    docker("exec", switch, "ip", "link", "add", port, "type", "veth", "peer", "name", port + "c")
    docker("exec", switch, "ip", "link", "set", port, "master", "brdhcp")
    docker("exec", switch, "ip", "link", "set", port, "up")
    docker("exec", switch, "ip", "link", "set", port + "c", "netns", str(pid))
    docker("exec", name(role), "ip", "link", "set", port + "c", "name", "eth1")
    if role in MACS:
        docker("exec", name(role), "ip", "link", "set", "eth1", "address", MACS[role])
    docker("exec", name(role), "ip", "link", "set", "eth1", "up")


def make_bridge(data: dict) -> None:
    """Create the only test bridge inside the switch, then attach owned peers."""
    switch = name("switch")
    docker("exec", switch, "ip", "link", "add", "brdhcp", "type", "bridge")
    docker("exec", switch, "ip", "addr", "add", f"{SERVER_IP}/28", "dev", "brdhcp")
    docker("exec", switch, "ip", "link", "set", "brdhcp", "up")
    for role, port in (("appliance", "va"), ("client1", "v1"), ("client2", "v2")):
        attach(role, port, data["token"])
    docker("exec", name("appliance"), "ip", "addr", "add", f"{APPLIANCE_IP}/28", "dev", "eth1")


def server_running() -> bool:
    """Check the recorded server PID within the owned switch container."""
    result = docker("exec", name("switch"), "sh", "-c",
                    'test -s /tmp/dnsmasq.pid || exit 1; '
                    'pid=$(cat /tmp/dnsmasq.pid); '
                    'test "$(cat /proc/$pid/comm 2>/dev/null)" = dnsmasq && '
                    'test "$(readlink /proc/$pid/ns/net)" = "$(readlink /proc/self/ns/net)"',
                    check=False)
    return result.returncode == 0


def stop_server(data: dict) -> None:
    """Stop only the PID recorded in the owned switch namespace."""
    check_container("switch", data["token"])
    if server_running():
        docker("exec", name("switch"), "sh", "-c", 'kill -TERM "$(cat /tmp/dnsmasq.pid)"')
        for _ in range(20):
            if not server_running():
                return
            time.sleep(0.2)
        raise TimeoutError("dnsmasq did not stop")


def start_server(data: dict) -> None:
    """Start exactly one dnsmasq, with a new log path per reservation generation."""
    check_container("switch", data["token"])
    if server_running():
        raise ValueError("DHCP allocator already running")
    data["generation"] = data.get("generation", 0) + 1
    config = render_dnsmasq(data["reservations"])
    log_path = f"/tmp/dnsmasq-{data['generation']}.log"
    config += f"log-facility={log_path}\n"
    docker("exec", "-i", name("switch"), "tee", "/tmp/dnsmasq.conf", input_text=config)
    docker("exec", "-d", name("switch"), "sh", "-c",
           'echo $$ > /tmp/dnsmasq.pid; exec dnsmasq --no-daemon --conf-file=/tmp/dnsmasq.conf 2>/tmp/dnsmasq.err')
    for _ in range(20):
        if server_running():
            save_state(data)
            return
        time.sleep(0.2)
    error = docker("exec", name("switch"), "cat", "/tmp/dnsmasq.err", check=False).stdout
    raise RuntimeError(f"dnsmasq failed to start: {error[:300]}")


def client_addresses(client: str) -> list[str]:
    """Read only the added test interface's current IPv4 addresses."""
    result = docker("exec", name(client), "ip", "-j", "-4", "addr", "show", "dev", "eth1")
    interfaces = json.loads(result.stdout)
    return [item["local"] for interface in interfaces for item in interface.get("addr_info", [])]


def release(client: str, data: dict) -> None:
    """Release that client's DHCP lease and require the OS to remove its address."""
    check_container(client, data["token"])
    if client_addresses(client):
        result = docker("exec", name(client), "dhclient", "-4", "-r", "-cf",
                        "/etc/dhcp/dhclient-eth1.conf", "-pf", "/run/dhclient.eth1.pid",
                        "-lf", "/tmp/dhclient.eth1.leases", "eth1", timeout=35)
        print(result.stdout.strip())
    if client_addresses(client):
        raise ValueError(f"{client} kept an address after DHCP release")


def acquire(client: str, data: dict) -> None:
    """Request a real bounded lease and assert the single expected OS address."""
    check_container(client, data["token"])
    expected = data["reservations"].get(client)
    if expected not in POOL:
        raise ValueError(f"{client} has no reservation")
    if not server_running():
        raise ValueError("DHCP server is not running")
    result = docker("exec", name(client), "timeout", "35", "dhclient", "-4", "-v", "-1",
                    "-cf", "/etc/dhcp/dhclient-eth1.conf", "-pf", "/run/dhclient.eth1.pid",
                    "-lf", "/tmp/dhclient.eth1.leases", "eth1", timeout=40)
    require_test_address(client_addresses(client), expected)
    print(result.stderr.strip() or result.stdout.strip())


def reserve(client: str, address: str | None, data: dict) -> None:
    """Replace server policy and its lease file after checking both clients."""
    if client not in MACS or (address is not None and address not in POOL):
        raise ValueError("invalid client or reservation")
    new = dict(data["reservations"])
    new[client] = address
    render_dnsmasq(new)
    stop_server(data)
    # Keep the other client's lease when changing one reservation. A wholesale
    # truncate made client-1's B lease disappear from server evidence on A reuse.
    docker("exec", name("switch"), "sh", "-c",
           f"test ! -f /tmp/dnsmasq.leases || sed -i '/ {MACS[client]} /d' /tmp/dnsmasq.leases")
    data["reservations"] = new
    start_server(data)


def wait_api() -> None:
    """Bound appliance startup to three minutes through loopback management."""
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{WEB_PORT}/api/user/me", timeout=3)
            return
        except urllib.error.HTTPError as error:
            if error.code == 401:
                return
        except (urllib.error.URLError, TimeoutError, ConnectionResetError):
            pass
        time.sleep(2)
    raise TimeoutError("appliance API did not become ready within 180 seconds")


def setup() -> None:
    """Create the opt-in segment and obtain client-1's initial real A lease."""
    preflight()
    build_images()
    STATE_DIR.mkdir(mode=0o700, parents=True)
    data = {"version": 1, "token": secrets.token_hex(24),
            "reservations": {"client1": POOL[0], "client2": None}, "generation": 0}
    save_state(data)
    try:
        create_resources(data)
        make_bridge(data)
        start_server(data)
        acquire("client1", data)
        wait_api()
    except Exception:
        try:
            teardown()
        except Exception as cleanup_error:
            print(f"cleanup failed: {cleanup_error}", file=sys.stderr)
        raise
    print(f"ready: http://127.0.0.1:{WEB_PORT}; DHCP segment {RANGE}; client1 {POOL[0]}")


def evidence(data: dict) -> Path:
    """Save raw DHCP, network, identity and appliance evidence outside the repo."""
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = EVIDENCE_ROOT / stamp
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    (output / "owner.json").write_text(json.dumps({"range": RANGE, "roles": list(ROLES),
                                                   "generation": data.get("generation")}, indent=2))
    for role in ROLES:
        try:
            check_container(role, data["token"])
        except subprocess.CalledProcessError:
            continue
        (output / f"{role}-docker.log").write_text(docker("logs", name(role), check=False).stderr)
        if role == "switch":
            for filename in ("dnsmasq.conf", "dnsmasq.leases", "dnsmasq.err"):
                result = docker("exec", name(role), "cat", f"/tmp/{filename}", check=False)
                (output / filename).write_text(result.stdout + result.stderr)
            for generation in range(1, data.get("generation", 0) + 1):
                filename = f"dnsmasq-{generation}.log"
                result = docker("exec", name(role), "cat", f"/tmp/{filename}", check=False)
                (output / filename).write_text(result.stdout + result.stderr)
            (output / "switch-links.txt").write_text(docker("exec", name(role), "ip", "-br", "link").stdout)
        else:
            for filename, args in (("addresses.txt", ["ip", "-4", "addr"]),
                                   ("routes.txt", ["ip", "-4", "route"]),
                                   ("machine-id.txt", ["cat", "/etc/machine-id"])):
                (output / f"{role}-{filename}").write_text(docker("exec", name(role), *args, check=False).stdout)
            if role in MACS:
                for filename, path in (("leases.txt", "/tmp/dhclient.eth1.leases"),
                                       ("host-key.txt", "/etc/ssh/ssh_host_ed25519_key.pub")):
                    (output / f"{role}-{filename}").write_text(
                        docker("exec", name(role), "cat", path, check=False).stdout)
    print(f"raw evidence: {output}")
    return output


def teardown() -> None:
    """Preserve logs, remove only exactly owned resources, then remove state."""
    data = state()
    token = data["token"]
    for role in ROLES:
        if docker("container", "inspect", name(role), check=False).returncode == 0:
            check_container(role, token)
    if docker("network", "inspect", NETWORK, check=False).returncode == 0:
        check_network(token)
    evidence(data)
    for role in reversed(ROLES):
        if docker("container", "inspect", name(role), check=False).returncode == 0:
            docker("rm", "-f", name(role))
    if docker("network", "inspect", NETWORK, check=False).returncode == 0:
        docker("network", "rm", NETWORK)
    STATE_FILE.unlink()
    STATE_DIR.rmdir()
    print("owned DHCP lab containers, network and lease namespace removed")


def show_status(data: dict) -> None:
    """Print current owned runtime state without mutating the lab."""
    check_network(data["token"])
    for role in ROLES:
        item = check_container(role, data["token"])
        addresses = client_addresses(role) if role in MACS else []
        print(f"{role}: {item['State']['Status']} test={','.join(addresses) or '-'} id={item['Id'][:12]}")
    print(f"range={RANGE} reservations={data['reservations']} allocator={'up' if server_running() else 'down'}")


def main() -> int:
    """Dispatch fixed lifecycle commands; never accept arbitrary Docker arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("up", "down", "status", "evidence", "move", "reuse",
                                             "reserve", "release", "acquire", "reset",
                                             "server-stop", "server-start", "client-restart"))
    parser.add_argument("client", nargs="?", choices=tuple(MACS))
    parser.add_argument("address", nargs="?", choices=POOL)
    args = parser.parse_args()
    if args.command == "up":
        setup()
        return 0
    data = state()
    if args.command == "down":
        teardown()
    elif args.command == "status":
        show_status(data)
    elif args.command == "evidence":
        evidence(data)
    elif args.command == "server-stop":
        stop_server(data)
    elif args.command == "server-start":
        start_server(data)
    elif args.command == "reserve":
        if args.client is None or args.address is None:
            parser.error("reserve requires client and address")
        reserve(args.client, args.address, data)
    elif args.command == "release":
        if args.client is None:
            parser.error("release requires client")
        release(args.client, data)
    elif args.command == "acquire":
        if args.client is None:
            parser.error("acquire requires client")
        acquire(args.client, data)
    elif args.command == "move":
        release("client1", data)
        old = data["reservations"]["client1"]
        reserve("client1", POOL[1] if old == POOL[0] else POOL[0], data)
        acquire("client1", data)
    elif args.command == "reuse":
        if data["reservations"]["client1"] != POOL[1]:
            raise ValueError("move client1 to B before client2 reuses A")
        reserve("client2", POOL[0], data)
        acquire("client2", data)
    elif args.command == "reset":
        for client in MACS:
            release(client, data)
        reserve("client2", None, data)
        reserve("client1", POOL[0], data)
        acquire("client1", data)
    elif args.command == "client-restart":
        if args.client is None:
            parser.error("client-restart requires client")
        check_container(args.client, data["token"])
        release(args.client, data)
        docker("restart", name(args.client), timeout=90)
        attach(args.client, "v1" if args.client == "client1" else "v2", data["token"])
        if data["reservations"].get(args.client):
            acquire(args.client, data)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, TimeoutError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as error:
        print(f"dhcp-lab: {error}", file=sys.stderr)
        raise SystemExit(1)
