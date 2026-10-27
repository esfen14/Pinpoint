# Connect the appliance and register Windows

This guide is for the current laptop pilot. The owner selected the existing
`Pinpoint-Final` VM as the appliance. Its adapter 2 is attached to the isolated
VirtualBox host-only adapter `vboxnet1`; its NAT adapter forwards the web UI to
`http://127.0.0.1:18080`. The Windows VM and fourteen host Docker devices use
the same host-only segment. A persistent presenter checkout is available at
`~/.local/share/pinpoint-defense/host-presenter-checkout`.

## 1. Connect the appliance

The owner has already attached `Pinpoint-Final` adapter 2 to `vboxnet1`. Its MAC
is `08:00:27:fa:10:0a`. The expected guest address is `10.77.1.1/27`, with no
DHCP, gateway or DNS on that interface. A Windows ping to this address did not
receive a reply on 2026-10-27; the actual guest address and any guest firewall
have not yet been checked. In the appliance console, run:

```bash
ip -br link
ip -br -4 address
```

Match the adapter using its MAC. If it is not configured as `10.77.1.1/27`,
inspect the VM's existing network configuration and report the output before
changing it; `Pinpoint-Final` is the owner's VM and its current configuration
and recovery snapshot have not been inventoried. Once configured, check from
inside the appliance using `ping -c 2 10.77.1.3` for Windows and
`ping -c 2 10.77.1.4` for the web container. Leave NAT adapter 1 and its
forwarding rules unchanged. Do not select a physical or Wi-Fi adapter.

Open `http://127.0.0.1:18080` on the laptop to use `Pinpoint-Final` and sign
in with that VM's existing application credentials. Its console login and
application credentials have not been verified by this guide.

The separate `pinpoint-qa-appliance` is powered off and still uses the old
`pinpoint-demo` internal network. Its lab VM login password, administrator email
and administrator password are under `~/.local/share/pinpoint-vmlab/` in
`lab-password`, `admin-email` and `admin-password` respectively. Those are for
the old QA appliance; do not assume they work for `Pinpoint-Final`. Both VMs
forward the same laptop ports, so do not start both without changing the port
configuration.

The ordinary `scripts/vmlab` commands validate the older internal-network setup
and should not be used to control `Pinpoint-Final`.

## 2. Windows credentials and NCPA registration

The Windows VM's local account is `presenter`. Its password and NCPA token are
stored separately on the laptop:

```bash
cat "$HOME/.local/share/pinpoint-defense/windows-home/login-password"
cat "$HOME/.local/share/pinpoint-defense/windows-home/ncpa-token"
```

Use the first value to sign in to Windows, and the second in Pinpoint's
registration dialog. Do not put either value into a command argument, a report,
Git, or a recording. Windows is at `10.77.1.3`; NCPA listens on TCP `5693` and
its Windows firewall rule permits the appliance address `10.77.1.1`.

In Pinpoint, open **NCPA Deployment → Register an agent I installed**, select
the discovered Windows device, and enter the NCPA token and port `5693`.
The picker requires an existing discovered device; if Windows is not listed,
registration must wait until the appliance is connected and the approved
Pinpoint discovery step is completed. Registration itself contacts NCPA and is
not a ping-only check. Confirm a real Windows metric afterward. The Windows
image is a Home test installation; activation/license acceptance is still
pending.

For other credentials: the current SNMP pilot community is in the root-owned
file `~/.local/share/pinpoint-defense/host-docker/pilot-catalog/private/snmp-community`.
If needed, read it locally with `sudo cat` and keep it private. It is separate
from the Windows NCPA token.

The Linux pilot containers do not use a shared demo login/password: their SSH
configuration disables password authentication, and each container has a
private host identity. Use the presenter commands on the laptop for the demo;
do not assume the old five-VM lab credentials apply to these containers.
