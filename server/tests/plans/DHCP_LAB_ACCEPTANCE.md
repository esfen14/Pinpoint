# Opt-in DHCP lab acceptance for issue #187

Run only with exclusive ownership of the dedicated Docker lab and approved
`10.79.0.0/28` range. The ordinary static Docker/VM labs are separate. Never
run this plan in CI, on a physical/VPN subnet or against an appliance whose
discovery settings contain any other range.

## Entry and exit

1. Record the candidate Git commit and ensure the checkout is clean except for
   the candidate. Check host, VPN, Docker and VM routes. `scripts/dhcp-lab up`
   refuses overlap, reused names, missing ownership state and a busy loopback
   port. The runner creates two successive clean labs itself.
2. Run `scripts/dhcp-accept --lease-seconds 90`. It uses bounded real scans,
   real `dhclient` renewal/release/acquire, dnsmasq reservations, Nagios config
   validation, host checks and API identity/history inspection. A failed case
   writes raw evidence immediately; the runner reports Pass/Fail per case,
   keeps raw evidence under `~/pinpoint-test-results/issue-187-dhcp/`, then
   removes its owned containers, network, lease namespace and owner marker.
3. Use `scripts/dhcp-lab status` and `scripts/dhcp-lab evidence` only on a
   currently owned lab. `scripts/dhcp-lab down` captures logs before removing
   resources. Verify no `pinpoint-dhcp187-*` container/network or owner marker
   remains, and compare host routes with pre-run output.
4. Review the raw case JSON and screenshots, then write a sanitized
   `docs/test-runs/<date>-issue-187-.../REPORT.md`. Name the exact tested commit,
   owner, range, client continuity, DHCP/OS addresses, scan/review outcomes,
   Pinpoint/Nagios identity, fresh check timing, browser/history and cleanup.
   A failed case stays failed. Never commit raw leases, logs, credentials, keys
   or database dumps.

## Matrix and bounds

| Case | Action and assertion | Bound |
|---|---|---|
| Initial A | Client-1 receives A from dnsmasq; real scan finds one device and Nagios checks it UP | DHCP 35 s; scan 360 s; check 240 s |
| Pre-move History event | Drop only client-1's test NIC while its container stays running; force a real Nagios host check, require an archive-backed DOWN event, restore NIC and service | Alert 240 s; DHCP 35 s if needed |
| Unchanged renewal | Wait for the running `dhclient` to renew A with server ACK; rescan retains device | Lease duration + 30 s; scan 360 s |
| A to B, same runtime | Release A, change only reservation, restart dnsmasq, reacquire B. Assert container/boot/MAC/client ID/machine ID/SSH key unchanged; no A in OS; SSH/HTTP at B; same device/Nagios name and address history; config validates and fresh UP check at B | DHCP 35 s; scan 360 s; check 240 s |
| Client-2 reuses A | Distinct MAC/host key gets real A lease; real scan yields distinct device/Nagios identity and no attribution of client-1 history | DHCP 35 s; scan 360 s |
| Persistent restart | Restart client-1 container, reattach its NIC with the same MAC, reacquire lease, rescan | Docker 90 s; DHCP 35 s; scan 360 s |
| DHCP outage/recovery | Stop server; observe actual address state through expiry; restore server and lease; rescan | 2× lease + 30 s, then lease + 30 s; scan 360 s |
| B-to-A/A-to-B | Release client-2's A, then move client-1 back and forth using real DHCP and scans | Two DHCP 35 s and scan 360 s bounds |
| Clean primary repeat | Tear down, recreate, repeat initial A, A-to-B and A reuse on a new appliance | Same per-step bounds |

The test range is validated against active routes and Docker IPAM before each
clean setup. The switch is `--network none` with `CAP_NET_ADMIN`; only its
network namespace contains the DHCP bridge. The separate Docker management
bridge carries the loopback web port and no DHCP packets from the test bridge.
The server config binds only `brdhcp`, excludes DNS, serves only known client
MACs, and keeps appliance/server static addresses outside the pool. Reservation
changes restart dnsmasq with a fresh log file and remove only the changed
client's old lease.

## Browser checkpoints

After the A-to-B scan and A reuse, the runner starts Vite on loopback 5174
against the loopback appliance and executes the `issue-187-live` Playwright
project. It signs into the actual UI, confirms client-1 at B and client-2 at A
in Device Inventory, then filters History by client-1's stable Nagios host name
and confirms its real pre-move DOWN host event remains visible. Screenshots
and Playwright/Vite logs go to the raw evidence directory outside the
repository. Install the frontend dependencies with `npm ci` before this run.
If the browser cannot start, the checkpoint fails; API evidence does not replace
it.
