# Defense target runtime (issue #274, preparation)

This directory is the in-progress guest runtime for the dedicated VirtualBox
Linux target host. The two-target DHCP exchange and all fourteen Linux
containers, baseline services, and five DHCP leases have been prepared. The
ping-only reachability pass from the Windows VM received a reply only from
Windows itself; all fourteen Linux target pings timed out. Appliance discovery
and product integration remain pending.
The existing `lab/compose.yaml` is a separate five-target Docker lab.

`compose.yaml` is a generated review artifact containing fourteen Linux targets.
Windows remains a separate VM. The managed guest will render the same document
with a pinned image ID and its private ownership marker. Each container starts
with Docker networking disabled and no published ports. Persistent identity and
data directories must already exist; Compose must not create or adopt them.
Only the DHCP server and clients receive `NET_ADMIN`.

The Docker build uses the repository root as its context and
`demo/defense/Dockerfile` as its file. Its adjacent `Dockerfile.dockerignore`
limits the context to runtime Python files and the manifest, independently of
the existing root ignore file. Build and run belong inside the target-host VM;
do not run this Compose file against the laptop's Docker daemon.

`node.py` initializes persistent machine/SSH identities and fixed configurations
for real SSH, HTTP/TLS, FTP, SMTP, IMAP, DNS, SNMP, PostgreSQL and DHCP daemons.
Supervisor owns the processes, with automatic listener startup disabled until
explicit baseline controls. The JSON command vocabulary currently covers
inspection, baseline service startup and DHCP server/client operations. It does
not yet provide listener changes, host lifecycle or DHCP/static transactions.
SNMP configuration is supplied through a private file; no community value is
passed in daemon arguments or committed here.

`guest.py` checks the VirtualBox UUID, private root-owned context, unnumbered
parent MAC, disabled forwarding, exact container ownership, pinned image,
command, capabilities and bind mounts before attaching an explicit macvlan.
`spike-up` is limited to `dhcp01` and `dynweb01`; that pair has exchanged a real
DHCP offer/lease on the isolated guest network. `lab-up` starts and attaches all
fourteen Linux targets after memory/disk checks; fixed node operations start
the catalog daemons and five reserved DHCP clients separately. Both paths refuse
conflicting links rather than deleting them. An interrupted attachment requires
inspection; automatic cleanup/recovery is not delivered yet. Windows pinged its
own address, but no Linux target replied. A trial `allow-all` setting on the
target VM NIC did not improve ping and was reverted to `allow-vms`.

The host-facing `demo/demo` still exposes only read-only `manifest` and
`preflight`. `provision.py` separately previews or prepares a fresh Ubuntu Server 24.04 VM
and private unattended media. It injects a generated ed25519 SSH host key before
the first managed connection. It never boots, clones or deletes a VM. An existing
preparation requires inspection and explicit resumption of its saved UUID; it is
never recreated. The build runs as a one-use guest systemd service after a real
boot, leaves all containers stopped, then disables forwarding. Installer execution,
pinned SSH verification, Compose lifecycle and an end-to-end spike runner remain
pending.

Preview only (no VM or file creation):

```bash
python3 -I demo/defense/provision.py --iso /absolute/path/to/ubuntu-server.iso
```

The issue owner authorized preparing the new VM. `--apply` creates only the new
VM and private installation media, after repeating ownership, route, port and
resource gates. Passwords and private keys enter through private files/stdin,
never command arguments. Setup artifacts contain credentials and must remain
outside Git in the private controller store. Installation completion must include
media cleanup. The management account has no Docker group or unrestricted sudo;
only the fixed guest helper is permitted through sudo.

VirtualBox may report `NS_ERROR_NOT_IMPLEMENTED` while identifying supported
Ubuntu media. The detector accepts only the exact diagnostic plus a complete
supported Ubuntu Server 24.04 report, consistent with
[upstream detection/preparation behavior](https://github.com/VirtualBox/virtualbox/blob/main/src/VBox/Main/src-server/UnattendedImpl.cpp).
Other errors remain fatal. These files neither authorize a product
scan nor establish live protocol, memory or isolation acceptance.

Offline checks (no Docker/VM changes):

```bash
python3 -I demo/defense/test_defense.py
python3 -I demo/defense/test_runtime.py
python3 -I demo/defense/test_guest.py
python3 -I demo/defense/test_provision.py
scripts/verify.sh docs
```

A preparation stopped in `created` may resume only media generation with
`--resume-media` (preview) and `--resume-media --apply`. This checks the saved
UUID/owner/MACs, powered-off process/endpoint boundary, exact disk and empty DVD;
it never recreates storage. `media-ready` means installation has not started.

`--start-install` previews the first boot; `--start-install --apply` boots only
the saved `media-ready` VM after rechecking the exact disk/media/NIC/owner,
processes, isolated segment, KVM release and one-VM resource budget. Other VMs
must be powered off. A start failure becomes `start-needs-inspection`; retries
never recreate the VM or silently reset installation state. Ubuntu powers off
at installation completion; disk-only boot and private-media cleanup still need
to precede normal use. This boot gate is separate from the stricter full-lab
startup capacity gate.

Guest UUID checks account for the two SMBIOS UUID byte orders controlled by
VirtualBox's documented
[`--system-uuid-le` setting](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/vboxmanage.html).
They accept only the pinned VM UUID or its exact field-byte conversion; malformed
or foreign UUIDs still fail. Service enable/disable operations in the installer
use `SYSTEMD_OFFLINE=1`; starting the image build belongs to the installed OS.

`--boot-installed` (preview) / `--boot-installed --apply` performs only the first
disk-only verification boot after the saved installation phase and a confirmed
powered-off VM. It detaches the private DVD and repeats the one-VM capacity,
ownership and endpoint gates. A successful start is labelled
`installed-boot-unverified` until actual pinned SSH and guest observations pass.

The first actual installation required console recovery for UUID byte order,
offline systemd, an interactive package notice and cloud-init key rotation.
Original pinned SSH is now verified. Docker re-enables IPv4 forwarding on later
boots; the helper refuses attachment, and durable forwarding plus remaining
`lxd` group cleanup must precede target activation. See the
[installation report](../../docs/test-runs/2026-10-27-issue-274-linux-target-host-install/REPORT.md).
No fully repeatable installation or live target workflow is claimed yet.

Offline hardening now defines a Docker `ip-forward: false` configuration and an
every-start guard that resets/verifies both forwarding families. A separate
ready service repeats group/sudo cleanup after cloud-init, and attachment checks
effective management privileges. Image builds temporarily allow NAT only while
the exact unnumbered demo NIC is down; normal cancellation resets forwarding and
failures leave the NIC down. This is not yet applied/retested on the installed
VM. Docker configuration behavior follows the
[daemon reference](https://github.com/docker/cli/blob/master/docs/reference/dockerd.md).

The private guest helper has `spike-up`, `lab-up`, `inspect TARGET`,
`node TARGET` (JSON stdin), and `stop TARGET`. Spike startup checks every
existing container and the exact private Compose document, then creates only
network-none containers and attaches their macvlans. `lab-up` extends that
guarded lifecycle to the fourteen catalog Linux devices after guest resource
checks. The live run started the catalog daemons and acquired five reserved
DHCP leases. The ping-only Windows-to-target pass reached only Windows itself;
all Linux target addresses timed out. The target VM NIC retains the planned
`allow-vms` policy after a trial `allow-all` setting made no difference. The
two-target DHCP exchange is live-verified; appliance discovery and product
connectivity remain pending. Guest operations are not yet wired to the
presenter CLI.

Every boot checks the runtime source fingerprint and pinned image/source label;
changed code rebuilds only when no containers exist, preserving identity/data
and SNMP settings. A stale prepared marker cannot authorize execution. Container
validation permits only metadata inherited from that exact image, required
project/target ownership and Compose metadata; entrypoint/device overrides fail.
The demo NIC has a MAC-matched networkd configuration with manual activation,
no DHCP/link-local/RA addresses or forwarding; the controller raises it only
after safety gates. This follows the
[networkd activation policy](https://www.freedesktop.org/software/systemd/man/250/systemd.network.html).

`provision.py --maintenance-boot` previews a stock-ISO repair of the saved
installed VM; `--apply` requires fresh host gates and KVM release. It verifies
snapshot-disk ancestry back to the original private VDI, refuses attached setup
media, and never invokes unattended installation or creates/replaces a disk.
The private guest helper also has read-only `host-status` safety flags and a
fixed `verify-restart` preparation probe; the latter refuses every container
object before restarting only Docker and rechecking the boundary. Neither
operation is a product scan or an authorization for target DHCP activation.
