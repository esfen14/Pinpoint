# Defense target runtime (issue #274, preparation)

This directory is an unfinished guest runtime for the dedicated VirtualBox
Linux target host. It has not been built or exercised against the appliance.
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
It exposes only `dhcp01` and `dynweb01` for the two-MAC/DHCP architecture spike.
It refuses a conflicting link rather than deleting it. An interrupted attachment
requires inspection; automatic cleanup/recovery is not delivered yet.

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
