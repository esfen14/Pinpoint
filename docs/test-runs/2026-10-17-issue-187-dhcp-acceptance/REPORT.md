# Test run: issue #187 isolated DHCP acceptance

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `46e1047a` (isolated DHCP lab and acceptance runner) |
| Plan | [`server/tests/plans/DHCP_LAB_ACCEPTANCE.md`](../../../server/tests/plans/DHCP_LAB_ACCEPTANCE.md) |
| Tester and owner | Codex, exclusive owner of the token-labeled `pinpoint-dhcp187-*` Docker resources; the ordinary static `pinpoint-lab` remained separate |
| Range and management | Approved DHCP-only `10.79.0.0/28`; appliance `10.79.0.2`, server `10.79.0.1`, A `10.79.0.5`, B `10.79.0.6`; loopback API `127.0.0.1:18087` |
| Raw evidence | Lab host `~/pinpoint-test-results/issue-187-dhcp/`; cycle-1 `20261017T025109186498Z/acceptance.json`, cycle-2 `20261017T025733224391Z/acceptance.json`; browser screenshots/Playwright logs in `20261017T024447969278Z/` and `20261017T025727776312Z/`; raw data not committed |

## Result

**Overall: Pass.** Cycle 1: Pass 9, Fail 0, Blocked 0. Cycle 2, from a
torn-down and newly provisioned lab: Pass 5, Fail 0, Blocked 0. The live runner
exited zero and removed its owned resources.

## Cases

| Case | Result | Observation and raw evidence | Issue |
|---|---|---|---|
| Initial A, cycle 1 | Pass | Client-1 got a real dnsmasq A lease on its non-Docker-IPAM test NIC; client/server logs show DISCOVER/OFFER/REQUEST/ACK. Real discovery made Pinpoint device ID 2 / Nagios `dev-79c4cc` at A; generated Nagios config validated and a fresh UP check appeared at 02:39:32 UTC. 63.2 s. | #187 |
| Pre-move History marker | Pass | Lowering only client-1's test NIC on its running container produced a real Nagios host DOWN archive event. NIC and HTTP/SSH were restored before the move. 32.8 s. | #187 |
| Unchanged A renewal | Pass | The running DHCP client received another server ACK for A; rescan kept the same device. 73.2 s. | #187 |
| Same running client A→B | Pass | Explicit release, changed reservation and reacquire produced a real B DISCOVER/OFFER/REQUEST/ACK and server lease. OS test NIC held B alone; container ID, boot ID, MAC, DHCP client ID, machine ID and SSH host key matched before/after. HTTP/SSH answered at B. Pinpoint stayed ID 2, Nagios stayed `dev-79c4cc`; old A address history closed, generated Nagios address changed to B, config validated and reloaded with a fresh UP check at 02:41:18 UTC. 54.3 s. | #187 |
| Client-2 reuses A | Pass | A different client MAC and SSH host key received A through DHCP; both B and A were present in server leases and on the respective OS test NICs. Real discovery created separate Pinpoint ID 3 / Nagios `dev-cf3608` at A; fresh UP check appeared at 02:44:27 UTC. Review API returned no identity review item for this unambiguous reuse; no client-1 identity attribution. 139.1 s. | #187 |
| Browser Inventory and History | Pass | Real Chromium sign-in showed client-1 at B and client-2 at A in Inventory; filtering History by client-1's stable Nagios host name showed its earlier DOWN event. Three screenshots and `playwright.log` retained outside the repo. 5.7 s. | #187 |
| Persistent restart | Pass | Restarted the same client-1 container and reattached its test NIC; persistent identifiers matched, real DHCP reacquired B, and rescan retained ID 2. 74.9 s. | #187 |
| DHCP outage and recovery | Pass | Server stop allowed the client OS address to expire to no test address (`[]`); after restart it reacquired B and rescan completed. 183.3 s. | #187 |
| B→A→B round trip | Pass | Client-2 released A; real DHCP/scans moved client-1 back to A then B while retaining Pinpoint ID 2, with Nagios config validation at each address. 117.3 s. | #187 |
| Clean primary repeat | Pass | New lab instance, lease set and appliance after the complete first-cycle teardown. Client-1 retained its new lab's Pinpoint ID 2 / Nagios `dev-317792` from A to B, with fresh UP checks at 02:53:09 and 02:55:09 UTC; distinct client-2 became ID 3 / Nagios `dev-32030f` at A with a fresh UP check at 02:56:43 UTC. A new real DOWN History event and second Chromium Inventory/History checkpoint passed. Primary case times: 122.2, 32.8, 85.3, 122.1 and 5.4 s. | #187 |

## Scope, safety and earlier attempts

The switch uses a private network namespace with `CAP_NET_ADMIN`, one dnsmasq
allocator bound only to `brdhcp`, and no published DHCP port or host network.
The appliance and server static addresses sit outside the two-address pool.
Setup checked route/Docker-network overlap, fixed names, owner state and the
loopback port. Each scan checked that appliance discovery settings contained
only the approved range. The normal static Docker lab was not mutated. The
controller captured evidence and removed only its token-labeled resources
between cycles and after cycle 2. Post-run checks found no
`pinpoint-dhcp187-*` container or Docker network and no owner marker; six
ordinary `pinpoint-lab-*` containers remained running.

An earlier cycle passed the product and DHCP matrix but the browser attempted
client-2 Inventory before its first Nagios snapshot, so that browser case
failed. The runner now waits for the fresh snapshot; cycle 1 above includes a
passing browser result. An earlier harness lookup also counted a displaced
`ADDRESS_UNKNOWN` historical record as an active A owner; lookup now requires
exactly one `ACTIVE` record. Those harness attempts were preserved as failures
in raw evidence and are not counted as acceptance passes.

This run covers isolated IPv4 DHCP and the named Pinpoint/Nagios/browser paths.
It does not cover physical or routed discovery without a MAC, cloned identities,
IPv6, DHCP failover, NCPA deployment or installer/systemd behavior.

## Cleanup and verification

Both cycle teardowns and the no-owned-resource check passed. The ordinary
static `scripts/lab smoke` passed 9/9 checks after DHCP teardown, including
discovery and all five target rows. `scripts/verify.sh all` passed: 3,761
backend tests passed with 14 skipped; 864 frontend tests passed across 69
files; frontend build and lint completed with zero errors (existing warnings).

## Sanitization

- [x] No passwords, owner tokens, full MAC addresses, DHCP client IDs, machine IDs, SSH keys, private paths or database dumps in this report.
- [x] Raw leases, Nagios logs, Docker logs and screenshots remain on the lab host.
