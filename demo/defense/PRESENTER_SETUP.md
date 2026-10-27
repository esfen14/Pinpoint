# Connect the appliance and register Windows

This guide is for the current laptop pilot. The owner selected the existing
`Pinpoint-Final` VM as the appliance. Its adapter 2 is attached to the isolated
VirtualBox host-only adapter `vboxnet1`; its NAT adapter forwards the web UI to
`http://127.0.0.1:18080`. The Windows VM and fourteen host Docker devices use
the same host-only segment. A persistent presenter checkout is available at
`~/.local/share/pinpoint-defense/host-presenter-checkout`.

## 1. Connect the appliance

The owner has already attached `Pinpoint-Final` adapter 2 to `vboxnet1`. Its
MAC is `08:00:27:fa:10:0a`, and the guest interface is `enp0s8`. The owner
observed `/etc/netplan/50-cloud-init.yaml` as the only netplan file and
`sudo netplan get network.ethernets.enp0s8` initially returned the old address
`10.77.0.1/28`. The owner subsequently changed it to `10.77.1.1/27`, disabled
cloud-init network configuration, and rebooted the appliance. Windows could
ping the appliance afterward. The instructions below describe that setup for
reference; check the current configuration before changing it again.

In the appliance console, back up and edit the existing file:

```bash
sudo cp -n -p /etc/netplan/50-cloud-init.yaml /root/50-cloud-init.before-defense.yaml
sudo nano /etc/netplan/50-cloud-init.yaml
```

Under `enp0s8`, replace `10.77.0.1/28` with `10.77.1.1/27`. Preserve all other
entries, especially `enp0s3` (NAT); do not add DHCP, a gateway, or DNS for
`enp0s8`. Save and exit. Use the appliance console for the following command,
then accept the netplan prompt to retain the change:

```bash
sudo netplan try
ip -br -4 address
ping -c 2 10.77.1.3
ping -c 2 10.77.1.4
```

`enp0s8` should display `10.77.1.1/27`; the pings are to Windows and the web
container. The owner confirmed the file header warns cloud-init can overwrite
it, and Windows successfully pinged the appliance at `.1` after the address
change. To keep cloud-init from regenerating networking on future boots, first
check whether the disable file already exists:

```bash
sudo ls -l /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
```

If it does not exist, create it with exactly this content:

```bash
printf 'network: {config: disabled}\n' | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg >/dev/null
```

If it already exists, inspect its content and do not overwrite it blindly.
This disables **cloud-init network configuration for the whole guest**; the
existing netplan files still configure both adapters, including NAT. Future
cloud-init network updates will no longer apply automatically. Keep the backup
outside `/etc/netplan` so netplan does not load it as another configuration.
The owner confirmed this setting and a normal guest reboot; Windows ping to
`10.77.1.1` passed afterward. The guest file and interface were not
independently inspected.
Leave adapter 1 and its NAT forwarding rules unchanged. Do not select a
physical or Wi-Fi adapter.

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
the discovered Windows device, and enter the NCPA token and port `5693`. The
owner confirmed Windows appeared in this manual registration picker and later
reported adding it to Pinpoint; it need not appear in the automatic deployment
eligibility list. The owner later reported Windows NCPA checks as OK, including
memory, CPU, and disk values; these UI observations were not independently
inspected. The appliance address answered ping after a VM start,
and the owner confirmed the cloud-init setting and reboot.
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
