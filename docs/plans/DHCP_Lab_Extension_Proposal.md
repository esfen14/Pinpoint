# DHCP lab extension proposal

**Status:** Docker feasibility proven on 2026-10-17; supported lab and product acceptance remain pending (#187).  
**Date:** 2026-10-15  
**Tracking:** [Issue #177](https://github.com/esfen14/Pinpoint/issues/177)

This plan feeds the discovery and identity contract in
[Data Model and Integrations](../../spec%20files/Data_Model_and_Integrations.md),
[Device Inventory requirements](../../spec%20files/Device_Inventory_Requirements.md),
and the lab workflow in
[Agent Workflow and CI](../../spec%20files/Agent_Workflow_and_CI.md).
If implemented, update the [Local Lab manual](../manuals/Local_Lab.md) and
[VM Lab Plan](VM_Lab_Plan.md) to describe the supported commands and limits.
This proposal does not change product behavior or claim new test coverage.

## Purpose

Add an optional lab mode in which a real DHCP server assigns addresses to real
DHCP clients. Its primary test moves **the same running target** from address A
to address B, then uses actual discovery, the browser and Nagios to verify that
Pinpoint follows that device without losing its identity or history.

[Issue #164's controlled discovery run](../test-runs/2026-10-15-issue-164-identity-review/REPORT.md)
and browser/merge checks did not move a live target through DHCP. This extension
would close that distinct gap; it does not retroactively turn those results into
DHCP acceptance evidence.

## Current baseline

The Docker lab in `lab/compose.yaml` uses static Compose addresses on an isolated
`10.78.0.0/24` bridge. Its target image and entrypoint do not run a DHCP client.
The VM demo in `demo/demo_lab.py` also generates static netplan addresses on its
`10.77.0.0/28` internal network. Neither is currently a DHCP test environment;
the [Local Lab manual](../manuals/Local_Lab.md#what-it-cannot-test) explicitly
excludes DHCP lease changes.

Docker normally assigns addresses itself through its networking system;
changing a Compose address or reconnecting a container with another Docker IP
would not prove a client obtained a lease from a DHCP server. See the
[Docker bridge networking documentation](https://docs.docker.com/engine/network/drivers/bridge/).

## Proposed topology

Use a separate, opt-in environment with a dedicated isolated Ethernet segment:

```text
Browser -- loopback management access -- Pinpoint appliance
                                             |
                             isolated DHCP test segment
                                  |          |          |
                              DHCP server  client-1   client-2
                               static IP   DHCP       DHCP
```

| Component | Role |
|---|---|
| Pinpoint appliance | Static test-interface address; discover only the test subnet |
| DHCP server | Static address outside the pool; controlled reservations and lease logs |
| client-1 | Persistent Linux target with SSH and HTTP; changes from A to B |
| client-2 | Separate persistent identity; receives the released address A for reuse tests |
| Management access | Separate from the scanned segment; preserves control during lease changes |

Choose a collision-free subnet during implementation, checking host, VPN,
Docker and VM routes. Reserve appliance/server addresses outside the lease pool.
Record the permitted scan range explicitly; any new QA range must be reflected
in the [approved QA scope](../qa/QA_Journeys_and_Scope.md) before a run. Do not
assume that the existing VM QA allowlist authorizes a new subnet.

Use dnsmasq as the proposed server: its interface binding, address reservations,
lease controls and DHCP logging are documented in the
[official manual](https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html).
The implementation must confirm its exact configuration and reload behavior,
including how changed reservations and an existing lease interact.
DNS service is unnecessary for the first phase.

## Delivery options

### Feasibility decision (2026-10-17)

Choose the Docker option for implementation. A throwaway test used a dedicated
switch container with `--network none`, host PID visibility and `CAP_NET_ADMIN`
to create a bridge and move veth peers into the appliance and client network
namespaces. The appliance and client kept separate Docker management interfaces.
Docker assigned no address on their added `eth1` test interfaces. `dnsmasq`
bound to the switch bridge at `10.79.0.1/28`; the appliance had static
`10.79.0.2/28`, and `dhclient` received `10.79.0.5` then `10.79.0.6` on the
same running client. The client released A before reacquiring; the server was
stopped, its reservation changed and old lease cleared, then restarted. Both
transactions had DISCOVER/OFFER/REQUEST/ACK, A was absent after B was installed,
and the appliance pinged both addresses. The container ID and boot ID were
unchanged. The trial repeated successfully with the switch limited to
`CAP_NET_ADMIN`; full `--privileged` was unnecessary. This confirms **restart**
of dnsmasq for reservation changes, not a SIGHUP-only reload recipe.

The switch's host PID view and network capability are still significant
privileges, so the mode must remain explicit and isolated. No host networking,
host bridge or published DHCP port was used. Its bridge existed only inside the
switch namespace; DHCP broadcasts could not reach physical, VPN or normal lab
interfaces. The measured image was 350 MB, three idle containers used about
1.3 MiB, 0.4 MiB and 2.2 MiB in a single Docker stats sample, and the final
trial took about 13 seconds after image build. These are feasibility costs, not
an estimate for a full appliance or acceptance run. All owned containers and
the management network were removed, with no change to host IPv4 routes. The
existing `pinpoint-lab` remained running and untouched. The exact experiment,
including the first failed server restart due to an unwritable reused log
file, is recorded in the [feasibility report](../test-runs/2026-10-17-issue-187-docker-feasibility/REPORT.md).

The tested `10.79.0.0/28` is a feasibility segment only. It was selected after
checking current host routes, active NetworkManager connections and Docker
subnets (and the documented VM `10.77.0.0/28`). It is **not** an approved QA
scan range until `QA_Journeys_and_Scope.md` is updated. The experiment performed
no discovery scan. A production helper must also check routes and ownership
again at each setup, and prove teardown of its own resources.

**Docker option — first feasibility check, given the selected Docker lab.**
Keep the normal fast lab unchanged and investigate a separate DHCP profile.
The DHCP client interface must acquire its address from the test DHCP server,
without a competing Docker address allocator on that interface. Merely adding
a DHCP server to the existing Compose bridge is insufficient.

A candidate is a lab-owned Linux bridge with veth interfaces attached to
container network namespaces, managed by a narrowly scoped setup/cleanup helper.
This is a proposed design, not a verified recipe: it needs host network
administration privileges (normally `CAP_NET_ADMIN` or root), careful ownership
checks and reliable cleanup. Do not grant broader host access to the regular
lab profile.
Keep any ordinary Docker management interface outside the discovery range.
Before integrating commands, prove a real DHCP exchange, an A-to-B move on an
unchanged running container, appliance connectivity and complete teardown in a
throwaway environment. If the required privileges or maintenance cost are
unacceptable, stop this option and use the VM option rather than simulate DHCP.

**VM option — preferred for faithful DHCP acceptance.**
Use a dedicated internal virtual switch, a small DHCP server VM, a real Pinpoint
appliance and two Linux client VMs configured for DHCP on their test interfaces.
Keep management/NAT separate. Reuse image-building patterns from `demo/`, but
create a distinct profile; do not convert the existing static demo globally.
This avoids the Docker interface/IPAM workaround and also permits later tests
with systemd and NCPA. Existing VM ownership/preflight rules still apply before
any start, restore, snapshot or network change. Budget a server and two client
VMs in addition to the appliance, including their memory, disks and boot time;
the feasibility decision must record measured cost before choosing this path.

## Deterministic same-device test

Before starting, record the tested commit, allocated subnet, approved scan range,
exclusive environment owner, network attachment inventory, selected DHCP client
and lease duration. Set a deadline for each lease acquisition, address change,
discovery, Nagios validation/reload and check recovery; record the chosen values
and elapsed times in the run report. A timeout is a failed case with preserved
logs and state, not permission to substitute an injected observation.

1. Start client-1 once. Record its runtime/container ID or VM UUID and boot ID,
   test-interface MAC, DHCP client identifier, machine ID and SSH host-key
   fingerprint. Generate unique identities per client and persist them; do not
   ship both clients with cloned SSH host keys or machine IDs. Machine ID and
   boot ID are lab evidence, not assumed Pinpoint discovery inputs.
2. Reserve A for client-1 and acquire a real lease. Save the DHCP exchange/log,
   lease record and the client's interface address. Discover through Pinpoint's
   normal workflow and enable monitoring. Record its device ID, Nagios host
   name, ports and at least one history sample.
3. Change the server policy to assign B to that same client. Explicitly release
   and reacquire the lease with the selected OS DHCP client. Do not rely on a
   short lease or ordinary renewal alone: either may retain A. Keep the target
   running; do not recreate its container, reboot its VM, replace its NIC or
   regenerate its keys to cause the move.
4. Verify the server acknowledged B, the OS installed B and removed A, and the
   recorded runtime identity, MAC, client identifier and host key are unchanged.
   SSH/HTTP must answer at B. Allow normal ARP convergence; record timings.
5. Run real discovery of the permitted subnet. Verify one logical device retains
   its device ID and Nagios host name, its current address becomes B, monitoring
   config uses B, validation/reload succeeds and a fresh check runs against B.
   In the browser, confirm the updated address and accessible pre-move history.
   A normal unambiguous move must not require a manual merge.
6. Give A to client-2, whose MAC and host key differ. Discover again and verify
   the old address does not cause client-2 to inherit client-1's identity or
   history. Confirm any review outcome follows the current
   [identity contract](../../spec%20files/Data_Model_and_Integrations.md#network-discovery-and-nagios-configuration).
   Record its own device ID, Nagios name, ports and history association.
7. Preserve the evidence bundle, then tear down only owned resources. Verify
   no owned bridge, namespace, VM, data directory, reservation or lease state
   remains unless the documented reset deliberately retains persistent client
   identities for another scenario. Recheck host routes and network interfaces.

For each step, capture a timestamped pass/fail entry and a bounded timeout. On
failure, preserve the DHCP server log and lease file, client DHCP journal and
`ip -4 addr`/route output, network attachment inventory, discovery scan output
and review items, generated Nagios host configuration plus validation/reload and
check output, and browser screenshots or a screen recording of inventory and
history. Sanitize credentials and private identifiers before committing a
[test-run report](../test-runs/README.md); keep raw evidence on the lab host.
Record the last successful step, the first failed assertion, elapsed time and
cleanup result so a later run can reproduce the failure.

Injected discovery observations, direct application database edits or manual
assignment of B cannot serve as acceptance proof for this sequence.

## Test matrix

| Case | Expected result |
|---|---|
| Renew a lease without changing its address | Device and monitoring identity remain stable |
| Same running client moves A to B | Real lease/address change; same Pinpoint device; checks resume at B |
| Different client takes released A | No silent merge or history attribution to the previous owner |
| Restart client-1 with its persistent identity | Rediscovery does not create an unnecessary duplicate |
| DHCP server stops, then returns | Record behavior before/after lease expiry; no false identity assignment; recovery after a valid lease |
| Repeat A-to-B and B-to-A | Repeatable outcome without leftover reservations or stale monitoring addresses |

Every case uses a bounded wait and saves the same failure evidence as the
primary sequence. The outage case is separate from the no-reboot primary case. Observe the
selected DHCP client's real renewal/rebinding/expiry behavior; do not impose a
fabricated expiry result. Keep lease durations configurable and record them.
Routed discovery without a visible MAC, deliberately cloned identities, IPv6,
DHCP failover and NCPA deployment are later extensions, not phase-one blockers.

## Isolation and lifecycle requirements

- Bind DHCP only to the dedicated lab interface. Publish no DHCP ports and use
  no host networking or connection to the physical LAN. No DHCP broadcasts may
  reach a household, office or VPN network.
- Allow only one DHCP allocator on the segment. Exclude static infrastructure
  from its pool; exclude management interfaces from discovery.
- Give every project, bridge, namespace, VM and data directory an ownership
  marker. Check ownership before mutation or teardown; leave shared labs alone.
- Reset leases, reservations and target identities through explicit operations.
  Resetting a test scenario must preserve identities unless that scenario
  intentionally creates a new device.
- Preserve logs before cleanup. Cleanup removes only owned lab resources and
  restores any host networking changes made by the helper.

## Implementation stages and completion criteria

1. **Feasibility:** choose Docker or VM after the Docker experiment; document
   required privileges, isolation, resource cost and a reliable A-to-B procedure.
2. **Lab support:** add an opt-in configuration, persistent client identities,
   lease control, status/evidence collection and teardown. Likely touch points
   are `lab/`, `scripts/lab`, or a dedicated `demo/` profile; finalize filenames
   after the feasibility decision.
3. **Acceptance runner:** drive real lease changes and discovery; assert the
   network and identity facts above. Keep browser/Nagios evidence alongside the
   automated assertions. Give every wait a bounded timeout and useful failure
   evidence.
4. **Documentation and verification:** update the supported lab manuals and
   relevant owning specifications; run `scripts/verify.sh` for the changed
   areas. Record an actual run under `docs/test-runs/` using its report rules.

The extension is complete only when the same-device move and IP-reuse cases
pass with real DHCP, repeat from a clean lab, and leave no owned resources after
teardown. Evidence must include the tested commit, environment ownership,
client continuity, leases and OS addresses, scan results, device/Nagios identity,
check recovery timing and browser/history results. Until then, retain the
current manual's DHCP limitation. This document alone is not a passed test.


