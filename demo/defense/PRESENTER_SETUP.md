# Connect the appliance and register Windows

This guide is for the current laptop pilot. A persistent presenter checkout is
available at `~/.local/share/pinpoint-defense/host-presenter-checkout`; use its
`demo/demo` commands after a reboot if the `/tmp` worktree is gone. The Linux devices run in Docker on
this laptop; `pinpoint-defense-win01` uses the isolated VirtualBox host-only
adapter `vboxnet1`. The appliance is `pinpoint-qa-appliance` and was powered
off when these instructions were written. The Docker pilot and Windows VM were
running. This setup is still being verified; keep your existing appliance data.

## 1. Connect the appliance

1. In VirtualBox Manager, confirm `pinpoint-qa-appliance` is **Powered Off**.
   If it is running, shut it down normally from the guest first. Create a new
   powered-off snapshot with a unique name such as `before-defense-2026-10-27`;
   keep the existing snapshots. Note the original network settings so you can
   restore them: adapter 1 is NAT with the SSH and web port forwards; adapter 2
   was Internal Network `pinpoint-demo`.
2. Open **Settings → Network → Adapter 2**, keep it enabled, and change
   **Attached to** to **Host-only Adapter**. Select `vboxnet1` as its name.
   Leave adapter 1 and its NAT forwarding rules unchanged. Do not select a
   physical or Wi-Fi adapter. Save the settings.
3. Start the appliance from VirtualBox Manager. Log in on its console as `lab`.
   The local VM login password is in the private laptop file:

   ```bash
   cat "$HOME/.local/share/pinpoint-vmlab/lab-password"
   ```

   Run that command on the laptop in a private terminal, not in a recording.
4. In the appliance console, identify adapter 2 by its MAC address
   `08:00:27:71:fa:84` and inspect the existing network configuration:

   ```bash
   ip -br link
   ip -br -4 address
   sudo cat /etc/netplan/60-pinpoint-lab.yaml
   ```

   Its interface is often `enp0s8`, but use the name matching that MAC. In the
   existing `60-pinpoint-lab.yaml`, replace the old lab address `10.77.0.1/28`
   with `10.77.1.1/27`. Keep the adapter's existing interface name and preserve
   the rest of the file. Do not enable DHCP or add a gateway or DNS server on
   this adapter. For example, use `sudo nano /etc/netplan/60-pinpoint-lab.yaml`.
   If the file or MAC differs, stop and report what you see rather than creating
   a second conflicting configuration.
5. From the appliance's **console**, apply and check it:

   ```bash
   sudo netplan try
   ip -br -4 address
   ping -c 2 10.77.1.3
   ping -c 2 10.77.1.4
   ```

   Confirm the netplan prompt to keep the changes. The adapter should show
   `10.77.1.1/27`; the pings are to Windows and the web container. Keep the
   console available while applying the network configuration.
6. On the laptop, open `http://127.0.0.1:18080`. The Pinpoint administrator
   email and password are in these private laptop files:

   ```bash
   cat "$HOME/.local/share/pinpoint-vmlab/admin-email"
   cat "$HOME/.local/share/pinpoint-vmlab/admin-password"
   ```

   Keep the values private. Reply **done** after the connection and pings so we
   can continue the remaining monitoring tests. Do not start discovery merely
   to perform this connection check; the agreed connectivity check uses ping.

The standard `scripts/vmlab` commands validate the old internal-network setup
and may refuse this modified adapter. Use VirtualBox Manager for the connection
steps above. To return to the old lab later, shut down the appliance and restore
its saved snapshot and adapter settings, checking the restored guest address and
network settings before starting old demo targets.

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
