# Test run: issue #187 Docker DHCP feasibility

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `f53cc067` (proposal baseline; experiment was outside the repository) |
| Plan | `docs/plans/DHCP_Lab_Extension_Proposal.md` feasibility stage |
| Tester and owner | Codex, exclusive owner of `p187-*` throwaway resources; existing `pinpoint-lab` was not changed |
| Environment | Linux host, Docker Engine 29.7.2, Ubuntu 22.04 test image; isolated `10.79.0.0/28`; no Pinpoint database or Nagios used |
| Raw evidence | Lab host `/tmp/pinpoint-187-feasibility/evidence/` (not committed; may be removed by host cleanup) |

## Result

**Overall: Partial.** The Docker DHCP design is feasible. No product acceptance
case was attempted; the opt-in supported helper and approved QA range do not yet
exist.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Observation and raw evidence | Issue |
|---|---|---|---|
| Real DHCP on an interface without Docker IPAM | Pass | `acquire-a.txt` has DISCOVER/OFFER/REQUEST/ACK for A; `address-a.txt` shows a dynamic test address. Docker supplied only the separate management interface. | #187 |
| Same running client A to B | Pass | Explicit `dhclient -r`, server reservation and lease reset, restart, then DISCOVER/OFFER/REQUEST/ACK for B. `address-b.txt` contains B and no A; `runtime.txt` and matching `boot-id-*` show unchanged runtime. | #187 |
| Appliance connectivity | Pass | `appliance-ping-a.txt` and `appliance-ping-b.txt` each show 2/2 replies. | #187 |
| Isolation and minimum privilege | Pass | Switch had `--network none`, `--pid host`, `CAP_NET_ADMIN`, no published port or host network; management used a separate internal Docker network. Host routes and active connections were checked. | #187 |
| Owned-resource cleanup | Pass | `residual-containers.txt` and `residual-networks.txt` are empty after the final run; host IPv4 routes match pre-run. | #187 |
| Pinpoint discovery, Nagios and browser history | Skipped | The throwaway image did not include Pinpoint; this is the later acceptance stage. | #187 |
| Six-case DHCP matrix and clean repeat | Skipped | The supported setup/runner and QA approval are pending. | #187 |

## Procedure, cost and deviations

Build an Ubuntu 22.04 image with `iproute2`, `dnsmasq-base` and
`isc-dhcp-client`. Start a switch with no Docker network, host PID visibility
and `CAP_NET_ADMIN`, plus separate appliance/client containers on an internal
management network. In the switch namespace create a bridge and veth peers,
move peers into the appliance/client namespaces, statically address the bridge
and appliance, and run dnsmasq bound to the bridge. Run `dhclient -4 -1` on the
client test interface; release with `dhclient -4 -r`. Stop dnsmasq by its
specific recorded PID, clear its lab lease file, change the reservation,
restart it with a new writable log file, then reacquire. The full repeatable
command sequence is retained at `/tmp/pinpoint-187-feasibility/run.sh` on the
lab host; its exit trap removes only its named and labeled containers/network.

The first restart attempt reused a dnsmasq log file that the new process could
not write, so B timed out after 30 seconds. That attempt was cleaned up. Using
a fresh log file made the restart succeed; two subsequent full A-to-B trials
passed, the second with `CAP_NET_ADMIN` in place of `--privileged`. This is a
lab control finding, not a Pinpoint product result.

The image size was 350 MB. A single idle Docker sample showed about 1.3 MiB
for the switch, 0.4 MiB for the appliance placeholder and 2.2 MiB for the
client; the final trial took about 13 seconds after image build. Full Pinpoint
appliance cost remains unmeasured. The design requires Docker daemon access,
host PID visibility for namespace attachment and `CAP_NET_ADMIN` in the
switch, plus `CAP_NET_ADMIN` for client interface configuration. A supported
helper must guard these privileges and verify ownership before mutations.

## Follow-up

- Implement the owned, opt-in Docker helper and record its tested commit.
- Approve the selected range in QA scope before any discovery scan.
- Run the real six-case product matrix twice for the primary cases and report
  failures as failures, with raw evidence outside the repository.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths.
- [x] No addresses outside the documented feasibility range.
- [x] Raw evidence is referenced by location and name, not pasted.
