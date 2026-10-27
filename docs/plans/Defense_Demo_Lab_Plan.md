# One defense demo lab (#274)

## Owner-directed host Docker transition

On 2026-10-27 the owner chose to run Linux target containers directly on the
laptop and connect the VirtualBox VMs through an isolated host-only adapter.
This supersedes the proposed target-host bridge/veth migration below. The
existing target-host remains the source of the original device identities,
service data and lease state until an explicit, verified migration is available.
No physical adapter is to be attached to the demo network.

A separate VirtualBox host-only adapter `vboxnet1` and an issue-owned temporary
Docker macvlan pilot were created. The adapter uses a VirtualBox-allowed host
address in `192.168.57.0/24`; the VM and pilot retain their `10.77.1.0/27`
demo addresses on the same Ethernet segment. A separate existing enabled
VirtualBox DHCP configuration belongs to `vboxnet0`; no VM was attached to it
and it was left unchanged. Windows now uses `vboxnet1` at `10.77.1.3`.
Fourteen temporary catalog containers are running on the laptop; the five DHCP
clients acquired their reserved `.20` through `.24` addresses from `dhcp01`.
Windows pinged all fourteen addresses successfully on 2026-10-27. These are
fresh pilot identities and data; the original target-host data remains intact.

The device runtime has an explicit host-only context with a host DMI identity
pin, private owner and adapter MAC; the old VirtualBox-only context is still
validated separately. A fixed attachment helper creates unnumbered macvlan
interfaces for the DHCP clients on the virtual adapter. The live pilot used a
short-lived privileged helper with a read-only root filesystem and no Docker
socket; this is not yet a complete supported host controller. Presenter commands now stop and start the existing pinned pilot containers,
restore the DHCP attachments, show local service status, and stop or start
allowlisted preset services, individual target stop/start, DHCP allocator
stop/start, and reserved lease release/reacquisition. Live tests passed for
these controls, a full down/up cycle, individual static/DHCP Docker restarts,
and Windows ping to the targets. Host reboot, Docker daemon restart, original identity/data
migration, broader fault controls and appliance acceptance remain pending. Per the owner's
direction, use ping only for connectivity tests.

Status: **host Docker pilot reachable from Windows; supported lifecycle and appliance acceptance remain pending**.
Tracking: [#274](https://github.com/esfen14/Pinpoint/issues/274).
No new scan range is authorized by this document. Existing supported commands
remain in the [VM lab plan](VM_Lab_Plan.md) and [demo manual](../../demo/README.md).

## Previous internal-network checkpoint

The earlier target-host topology had fourteen containers and five DHCP leases,
but ping between Windows and the Linux targets failed. That result remains in
the [ping-refresh report](../test-runs/2026-10-27-issue-274-ping-refresh/REPORT.md).
The owner's subsequent choice of host Docker supersedes that topology.

## Earlier internal-network follow-up preparation

At that checkpoint, the Windows-to-target result had not changed. Source review confirmed that
VirtualBox Internal Networking is implemented as an Ethernet switch with
broadcast/multicast and promiscuous-mode support, while the `nicpromisc` policy
is documented for bridged adapters. Therefore the prior `allow-all` trial on
this Internal Network does not identify the failure. See the [VirtualBox 7.2
networking guide](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/networkingdetails.html)
and [`VBoxManage` 7.2 reference](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/vboxmanage.html).

Added an offline-tested, fixed `peer-ping` request that sends three ICMP
requests from an addressed Linux container to the Windows address `10.77.1.3`.
It has no caller-provided destination and reports only a boolean result. The
guarded maintenance path has since refreshed the running image from the current
source. `reset-lab` was used to
prevalidates the full catalog and persistent volumes, stops all validated
containers before removing their objects, and never removes volumes. Preserve
the fourteen target identity/data volumes and DHCP lease state during that
refresh. Afterward,
stage 3 uses only Windows `ping` and this fixed Linux `ping`; do not add ARP,
port probes, scans, or packet capture.

## Proposed bridge/veth review

The next candidate keeps the VirtualBox internal segment, Windows NIC and
catalog MACs; it replaces each guest macvlan with a veth pair. Its host end and
the exact unnumbered internal NIC would join one unnumbered guest bridge. The
other end would reside in the verified container namespace with that target's
catalog MAC. The NAT management NIC and Docker bridges must never join it.
The [Linux bridge documentation](https://docs.kernel.org/networking/bridge.html)
describes Ethernet forwarding between bridge ports: IP forwarding set to zero
alone does not prevent that forwarding. The fixed ownership and complete
membership checks are therefore necessary, and a bridge must never be accepted
just because its name matches.

The first offline guard validates a normalized complete link inventory: the
bridge and veth host ports carry the private owner alias; exactly one pinned
parent and the expected catalog ports belong to the bridge; all are unnumbered;
both IP forwarding values are zero; and foreign or duplicate ports are refused.
The fixed guest `bridge-status` operation now wires these checks to bounded
host and namespace observations while holding the guest control lock and
revalidating container process identity. It is prepared in source but has not
been applied to the installed VM or observed on a live bridge. Before it can
guard live changes, the controller must verify actual bridge netfilter behavior, precise parent
and bridge MACs, interruption cleanup, and that image builds cannot bridge the
demo NIC to management. Linux documents that bridge traffic can encounter
netfilter rules separately from ordinary IP forwarding; see the
[bridge netfilter section](https://docs.kernel.org/networking/bridge.html#netfilter).

No change to the currently running topology is implied by the offline guard.
For a future migration, validate every existing container and its identity/data
mounts first, retain leases, and use a recorded transaction with a deterministic
rollback. An interruption must leave the demo parent disconnected until owned
bridge membership is reverified. Never remove or adopt a link solely by name.
After any authorized migration, the user-directed reachability test remains
ping only. A ping pass would still leave product discovery, service checks,
physical-network isolation acceptance and presenter lifecycle pending.

An additional bounded trial set both running demo adapters to `allow-all` at
the same time, after verifying their saved UUIDs, owners, MACs and process
ownership. Windows ping to `web03` and `web03` peer-ping to Windows both got no
reply. The Windows adapter was restored to `deny` and the target-host adapter
to `allow-vms`; both restoration commands succeeded. This rules out that
particular adapter-policy change as a complete remedy, but does not establish
the root cause or prove that a bridge will work. Only ping was used for the
connectivity trial.

## Transition and recovery

Use a new VirtualBox Internal Network named `pinpoint-defense`, with candidate
subnet `10.77.1.0/27`. The 2026-10-27 host IPv4 route/interface and Docker
inventory found no overlap with that candidate or the three documented existing
lab ranges. This observation expires when routes, VPNs or VM/Docker networks
change. Before adoption, inspect the guest routes and configured host VPN
profiles too, then repeat collision checks at every start.

Reuse the exact QA appliance UUID `351eb491-f5e1-4854-a7e4-68309ad774ad` if its
current installed state and recovery can be verified. Give its isolated NIC
`10.77.1.1/27`. Retain its NAT loopback SSH/web forwards. Build one separately
owned `pinpoint-defense-targets` Ubuntu VM from the local stock Ubuntu ISO, with
a new disk, new MACs, a unique machine ID and separate private management
credentials. Inject a generated host SSH key through private unattended files
and pin its public key before the first management connection. Preserve the old
base; its legacy unpinned SSH bootstrap is not the new management trust path.
Budget 2048 MiB for this VM and retain 4096 MiB for the appliance. Proposed
target-host NAT SSH forward: `127.0.0.1:2260` to guest 22, subject to an unused
port check. The target-host's second NIC joins only `pinpoint-defense` and has
no IPv4 or IPv6 address, no default route and no DHCP client. Containers use
that NIC as a macvlan parent; VirtualBox NIC 2 uses `allow-vms` promiscuous
mode. Prove that setting sufficient before considering alternatives.

The old base and five target disks remain powered off as transition recovery
resources. Their retention does not create a second running presenter lab.
Remove the old launcher from the active presenter path only after the new
command set and Documents shortcut work. No disk deletion is planned in this
issue. The inventory also found unrelated `Pinpoint-Final` and `Nagios-Demo`
attached to the old `pinpoint-demo` network; the latter has a physical bridged
NIC. Neither belongs in the new network or the controller allowlist. Do not
reuse the old internal network for the new DHCP story.

Before changing the appliance or its scope:

1. Acquire the canonical host control claim, pass ownership preflight and check
   guest Git status/service paths. Save private application/configuration
   backups, including the current discovery settings, and preserve guest edits.
2. Record endpoint identity and take a powered-off `issue274-before-defense`
   snapshot. Record its UUID privately and prove a nonsecret marker restores
   through the actual SSH and HTTP endpoints, following the existing VM plan.
   Retain any baseline data needed outside that marker trial. Existing snapshot
   names alone do not prove a backup of the present state.
3. Stop the appliance before changing its NIC 2 attachment. Configure the new
   guest address and explicit scan scope with automation inactive until the
   isolation and collision gates pass. Update the owning workflow specification
   for this demo range before the first new product discovery. Normal QA scope
   stays governed by its own reviewed queues.
4. On failed feasibility, preserve logs and stop only owned new resources.
   Restore the recorded pre-transition snapshot/configuration and old NIC 2
   attachment through the guarded controller. Prove endpoint identity, guest
   address, saved scan scope and baseline health. Preserve all existing disks.
   A failed restore halts further mutations for owner recovery.

## Catalog and addressing

The manifest will be the source for provisioning, command target choices,
listener presets, `status` and `wall`. Planning MACs are local unicast addresses
under `02:77:01:00:00:NN`, NN equal to the target's catalog number; prove no
collision before assigning them. Each Linux device also needs its own persistent
machine ID, DHCP client ID where applicable, SSH key and data volume.

| Target | Demo address | Real baseline listeners | Plugin proof required |
|---|---|---|---|
| dhcp01 | .2 | OpenSSH 22; dnsmasq UDP 67 | check_ssh; DHCP transactions separately, not a normal UDP-67 check |
| win01 | .3 | Official Windows NCPA 5693 | Authenticated manual registration and real NCPA metric |
| web03 | .4 | nginx HTTP 80 and HTTPS 443 | check_http, including TLS configuration |
| api02 | .5 | HTTP 8081 | check_http after fingerprint |
| ftp01 | .6 | FTP daemon 21 | check_ftp valid greeting/protocol probe |
| mail01 | .7 | SMTP daemon 25, IMAP daemon 143 | check_smtp; check_tcp IMAP greeting |
| dns01 | .8 | DNS daemon UDP 53 | check_dns response and query settings |
| db01 | .9 | PostgreSQL 5432 | check_pgsql only after safe settings verified; otherwise discovered only |
| snmp02 | .10 | snmpd UDP 161 | check_snmp with privately configured settings |
| ssh-alt02 | .11 | OpenSSH 2223 | check_ssh after fingerprint |
| dynweb01 | DHCP initially .20 | HTTP 80; OpenSSH for identity | check_http/check_ssh |
| dynapp01 | DHCP initially .21 | HTTP 8080; OpenSSH for identity | check_http/check_ssh |
| dynmail01 | DHCP initially .22 | SMTP 25; OpenSSH for identity | check_smtp/check_ssh |
| dynsnmp01 | DHCP initially .23 | snmpd UDP 161; OpenSSH for identity | check_snmp/check_ssh |
| dynweb02 | DHCP initially .24 | HTTP 9090; OpenSSH for identity | check_http/check_ssh |

Addresses in the table are suffixes within the candidate `/27`. Pool: .20-.29;
checked static transition slots: .15-.19. Infrastructure is outside both. The
target-host does not count as a discovered device. `dhcp01` does count. With
Windows present there are fourteen Linux containers plus one Windows VM.
Before Windows, a fifteenth Linux `win-slot` may use .3, explicitly labelled as
a stand-in; it has no fake Windows/NCPA claim and cannot pass final acceptance.

The owner subsequently identified local installation media named
`Win10_22H2_English_x64v1.iso`, stated no purchased license was available and
selected Home for testing. A new exact-owned `pinpoint-defense-win01` is now
installed with Home build 19045 and NCPA 3.5.0; its local API and powered-off
baseline are recorded in the [Windows preparation report](../test-runs/2026-10-27-issue-274-windows-home-install/REPORT.md).
Activation/licensed-Windows acceptance, actual appliance registration and the
all-fifteen count remain pending. This preparation does not pass the architecture
spike or authorize a new product scan scope.

Only dnsmasq in `dhcp01` allocates on the demo segment. Docker must assign no
address on any client's demo interface. Keep management on separate guest-only
Docker interfaces; prevent forwarding between management/NAT and the demo NIC.
Run only real daemons with valid protocol replies. Enabling a plugin or opening
a socket alone is insufficient proof that Nagios monitors the intended service.
Enable only proven needed plugins and bounded TCP/UDP scan ports on the appliance.

## Command execution and secret exposure review

The work-issue workflow section 4 says: "the change touches a sensitive module
(see `spec files/Engineering_Standards.md`)" under "Needs a person". Engineering
Standards includes "command execution paths" and requires an explicit injection
and secret-exposure review. The new presenter controller falls within that rule.
This section defines the review boundaries. The owner subsequently directed
continuation after the remaining Linux/controller/network scope was explained;
that authorization is recorded in the issue progress. Implement within these
boundaries and explicitly review injection/secret exposure with the negative
tests below. Resource, ownership and actual isolation gates still precede any
live mutation or product scan.

| Boundary | Proposed enforcement | Required negative/recovery test |
|---|---|---|
| Host control | Use `qa_control.py` canonical held claim and existing host/process/endpoint ownership preflight; recheck immediately before mutation | Concurrent claim, stale descriptor, duplicate controller and endpoint drift fail before SSH/VBox mutation |
| VM targets | Pin exact owned names and UUIDs in private state; require expected NICs, adapters, MACs and NAT loopback forwards | Foreign name/UUID, extra adapter, physical bridge, host-only demo NIC or unexpected network member fails closed |
| Container targets | Fixed manifest names plus owner/role labels, image and expected network/volume identity; no arbitrary VM/container name or exec argument | Missing/mismatched ownership, changed image/mount/network and arbitrary shell input refused |
| Subnet and scans | Fixed approved CIDR, reject all route/interface/VM/Docker/VPN overlap; prove sole internal segment and allowlisted membership; scoped appliance scan with no overlap | Conflicting route/subnet, foreign NIC, default route, alternate scan range and simultaneous discovery refused |
| Injection | Argument-list subprocesses, fixed guest helper operation enum, validated JSON on stdin; target/service enums and strict integer/IP parsing; never construct a shell program from CLI text | Shell metacharacters, option-shaped names, control characters and malicious JSON fields rejected before subprocess |
| Listener controls | Preset service/port pairs; additional HTTP/TCP only on unused approved high ports inside configured scan eligibility; reserve NCPA, SSH/control and infrastructure ports | Collisions, reserved 5693, management ports, wrong protocol/target, close of an unowned listener and interruption tested |
| Listener lifetime | Persist intent before mutation, record owned process/unit and verify actual open/closed socket; baseline restore repeatable after interruption | Crash between intent/start/close; stale PID; repeated restore; management still reachable |
| DHCP/static | Restrict to five manifest clients and static slots; server restart reservation pattern; durable prior-mode intent, exact address ownership and bounded ARP duplicate check | Existing address, extra address, DHCP timeout, interrupted transition, failed rollback and repeated reset |
| Identity | Keep runtime/container ID, persistent MAC/client ID/machine ID/host key through address transitions; exactly one demo address | Before/after continuity plus product device/Nagios/history association; refuse replacement as evidence |
| Privileges | All Docker/network capabilities live inside the dedicated target-host; no host Docker socket mount, host net/PID namespace or physical bridge; narrowly scoped guest helper | Inspect capabilities/mounts/interfaces and attempt invalid operation; no host networking changes |
| Credentials | Generate/store privately with owner-only permissions outside repo; no default passwords copied from old script, no token/secret in argv/output; NCPA reads private token through stdin/file | Sentinel secrets absent from stdout/stderr, exceptions, argv, status/wall and evidence; unsafe file/symlink permissions refused |
| Windows | Owner explicitly identifies licensed VM/image; isolated NIC only for defense; read-only status without token; install official NCPA ahead of recording | Foreign VM refusal, firewall/API/metric verification, process/disk name probe, ncpa-ready powered-off snapshot |
| Reset/down | Preview names exactly what restores; owned snapshots/leases/listeners only; preserve identities and logs; no Pinpoint database reset | Wrong owner/snapshot, mixed ownership, interrupted reset and second apply; final baseline comparison |

An unavailable or ambiguous observation must stop the operation. Captured guest
output may contain secrets and must stay private; report fixed error categories
instead. Validate helper destinations and existing state files against symlinks,
unexpected ownership and permissive modes. The old `shell`, `creds` and free-form
service-unit mechanisms are not part of the proposed presenter command set.

## Feasibility and resource gates

First run a small, bounded spike using two distinct container MACs and a real
DHCP client. From the same appliance, prove ARP/MAC separation, valid service
responses, a complete DHCP DISCOVER/OFFER/REQUEST/ACK, and management survival
when one target stops. Capture on the guest demo NIC and host physical interface
with bounded, narrowly filtered DHCP captures; save privately and commit only
sanitized counts. Prove there is no DHCP exposure on the physical interface and
no guest forwarding path to it. Windows reachability remains pending the image.
If VirtualBox/macvlan fails, revise and re-review the topology before expanding.

The read-only resource sample was 8705 MiB available RAM and 81785 MiB free disk
(approximately 8.5 GiB and 79.9 GiB respectively),
with all inventoried VMs off. These are observations, not capacity
approval. Planned Linux start needs 4096 + 2048 + 3072 = 9216 MiB available before
start, plus measured controller overhead. With a 3072 MiB Windows allocation,
that becomes 12288 MiB before overhead. Re-evaluate the allocation against the
actual owner-supplied Windows image. Every start must refuse insufficient
capacity rather than depend on swap. Require free disk for remaining virtual
disk growth, retained snapshot growth and bounded logs; calculate from actual
images before setting the threshold. Measure boot/scan/check peak RAM and
`vmstat` swap activity, retaining at least 3072 MiB available afterward.

## Presenter migration and acceptance sequence

Sources are the three files in `~/Documents/Pinpoint-Demo/` inventoried in the
report. The current shell launcher hardcodes an absolute checkout and five old
VM names. Migrate its behavior into a portable repository entrypoint and replace
the Documents launcher with a shortcut to that versioned entrypoint, after the
replacement works. Preserve a private copy of all source files before changing
the shortcut. Scan text for credentials before copying prose into Git. Adapt the
walkthrough/cue card to the manifest and exact commands below.

Proposed entrypoint: `demo/demo`. Required operations: `preflight`, `up`,
`status`, `wall`, `down`; `ports list/open/close/restore`; `fault host-down/host-up`;
`dhcp leases/move/server-stop/server-start/reset`;
`address-mode show/static/dhcp`; `windows status`; `reset --preview/--apply`.
These names describe the intended interface and are not available yet.

After feasibility, run the complete catalog with the appliance's approved bounded
scope; record each discovered MAC/IP, protocol response and actual plugin/service,
with a valid Nagios candidate/reload and live check. Then verify:

1. Listener addition → rescan → identified/monitored port; close → failed Nagios
   check; restore → healthy. A closed port becomes Missing only after five
   unsuccessful scans; archival defaults to 30 days after Missing. Record the
   effective configured archive interval; do not promise immediate deletion.
2. Selected host down/up with unchanged identity/data and working management;
   wrong targets/ports, interrupted cleanup and repeated undo.
3. Five distinct simultaneous DHCP leases; A-to-B for the same running client;
   another client takes released A. Record runtime/MAC/client ID/host-key
   continuity and normal Pinpoint discovery/history/check association.
4. Same running client DHCP → unused static slot → DHCP with exactly one address.
   Include duplicate refusal, server-down return/rollback, interrupted change,
   repeated reset and final healthy baseline. Keep logs before restoring.
5. After owner supplies Windows, install official NCPA with a private 32-hex
   token, verify firewall and authenticated disk/process APIs from the appliance,
   snapshot powered off as `ncpa-ready`, register through **Register an agent I
   installed**, and show one real metric. Replace win-slot and repeat the final
   all-fifteen count. Existing Windows-named VMs are not implied authorization.
6. Execute the full adapted walkthrough twice from a clean owned baseline. Save
   separate counts, five-lease tables, scan/registration/HARD-alert/recovery
   durations, RAM/swap/disk samples, all undo outcomes and final healthy state.

Record results under `docs/test-runs/`; neither this plan nor mocked tests earn
live acceptance credit. File product defects separately and keep the issue-187
DHCP controller independent. Update the owning specifications/manuals as each
supported workflow ships; run tooling/backend checks, docs and the final full
verification gate before a ready-for-review PR.
