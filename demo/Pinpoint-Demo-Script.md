# Pinpoint live demo script

**Lab:** the `Pinpoint-Final` appliance at <http://127.0.0.1:18080>, the Windows VM `pinpoint-defense-win01` and fourteen Linux containers, all on the isolated host-only network `10.77.1.0/27`. Setup and appliance addressing are in [`defense/PRESENTER_SETUP.md`](defense/PRESENTER_SETUP.md). Run the fault commands on the **laptop**; they affect only the demo containers. Use a second terminal for the live status wall. The commands below are written `Pinpoint-Demo-faults.sh`; run them as `demo/Pinpoint-Demo-faults.sh` from the repository root, or through the `~/Documents/Pinpoint-Demo/` shortcut.

## Before the audience arrives

1. Start the lab: `Pinpoint-Demo-faults.sh up-all` (starts all fourteen containers and the five DHCP leases; `down-all` stops them). If a previous run left faults behind, `Pinpoint-Demo-faults.sh reset` returns the lab to its baseline (addresses, daemons, extra ports) in about 90 seconds, and make sure the appliance and Windows VMs are running. `Pinpoint-Demo-faults.sh manifest` prints the observed MAC, IP, live listeners and expected plugin of every device. Then run `demo/demo presenter preflight`: it must print `Preflight OK` (isolated owned network, only the two pinned VMs on `vboxnet1`, no subnet collision, at least 3 GiB RAM and 20 GiB disk free, no swap thrash). A measured down/up of all fourteen containers took 17 s and 70 s with at least 7.3 GiB RAM available throughout.
2. In a second terminal run `Pinpoint-Demo-faults.sh wall` (`Ctrl+C` exits). Confirm every target shows its address and services running, and the five DHCP clients show `.20` to `.24`. Open <http://127.0.0.1:18080> in a signed-out/private window.
3. **First-login check:** the prepared appliance has already completed bootstrap setup. To show the password-change screen, create a disposable account in **Manage Accounts** with **Require password change at first sign-in**, sign out, and use it. Do not restore an older snapshot during a live demo: it rolls back Pinpoint's database.
4. Check **Settings → Network Discovery → Networks & Ports**. The range must be `10.77.1.0/27` and the ports must cover the demo (TCP 21, 22, 25, 80, 143, 443, 2223, 5432, 5693, 8080, 8081, 9090 and UDP 53, 161). Save only if missing. Leave `check_ncpa` for the on-stage enable step if you want to show it.
5. Keep administrator and target logins off slides and recordings. Leave several minutes for Nagios checks to reach a **hard** failure.

## Presenter run of show

| Step | Say / do | Verify on screen |
|---|---|---|
| 1. First login | Sign in; if showing the password-change flow, use the disposable account from step 3 above. | Blocking password-change form, then the authenticated UI. |
| 2. Discovery range | In **Settings → Network Discovery**, show `10.77.1.0/27` and the scan ports. Add it if missing. | The lab range is saved; no real LAN range is selected. |
| 3. Scan | On **Dashboard**, click **Rescan Network**. Open **Device Inventory** and **Network Status**. | Fifteen devices: `.2` to `.11` (including Windows at `.3`) and the five DHCP clients `.20` to `.24`. If already discovered, say this is a rescan updating the inventory. |
| 4. NCPA plugin | In **Plugin Manager**, find `check_ncpa` and **Enable** it. | Enabled/Active. The SSH, HTTP, NCPA, DNS, FTP, SMTP, SNMP and TCP checks are enabled in the rehearsal lab, so those ports become Monitored after discovery. There is no PostgreSQL plugin: `db01` is monitored with `check_tcp` (Pinpoint labels `5432` as `nagios-nsca`). |
| 5. Windows metrics | Show `win01` CPU, memory and disk checks from its registered NCPA agent. Register it with **Register an agent I installed** if it is not already (token private). | Windows metric checks are OK. |
| 6. Discovered ports | Open `web03` or `api02` → **Ports**. Show the discovered service, the monitoring reason and **Set service…** where offered. | A port attaches only when its plugin is enabled. |
| 7. One service fails | Run `Pinpoint-Demo-faults.sh down web03 http`. Keep the wall visible. | `web03` HTTP goes DOWN while its HTTPS and container stay UP. After Nagios retries, **Network Status** shows Critical and the Dashboard shows the alert. Acknowledge it if you want to show the workflow. |
| 8. Restore it | Run `Pinpoint-Demo-faults.sh up web03 http`. | The wall returns to running at once. After the next checks, Network Status recovers and **History** shows the failure and recovery. |
| 9. Remediation | In **Remediation**, add an enabled **Record only** action scoped to the exact `web03` host and HTTP service, with automatic recovery on. Run `down web03 http` again and wait for a hard failure. | **Run log** records the action. Record only never restarts the service; run `up web03 http` afterward. |
| 10. Maintenance | In **Maintenance**, create a one-off window for `api02`, active during the test. Once active, run `down api02 http`. | The service can become Critical with a downtime indication while notifications are suppressed. Cancel the window, then run `up api02 http` and confirm recovery. **Settings → System → Maintenance Mode** is a different, global control. |
| 11. Address change | Run `Pinpoint-Demo-faults.sh dhcp-move dynweb01 10.77.1.25`, then rescan. | The same device now shows `.25`; no second device appears. Pinpoint shows only the current address (history is tracked in #277). Move it back with `... dynweb01 10.77.1.20`. |
| 11b. New port | Run `Pinpoint-Demo-faults.sh ports open web03 http 8088`, rescan, then `ports close web03 8088` and rescan again. | The port appears on `web03` as Monitored with its check. After the close, the check goes CRITICAL; it becomes Missing only after five scans and archives after the configured period (it does not disappear at once). `ports restore all` closes every extra port. |
| 11c. Fixed address | Run `Pinpoint-Demo-faults.sh address-mode static dynweb01 10.77.1.15`, then wait for the next discovery (about five minutes in the rehearsal) and look at **Device Inventory**. Return with `address-mode dhcp dynweb01`. | The same device (`dynweb01`) moves to `.15` with no second device; DHCP return brings it back to `.20`. `address-mode show dynweb01` reports `dhcp` or `static` and the one address. |
| 12. Host failure (optional) | Run `Pinpoint-Demo-faults.sh down dynapp01 host`; then `up dynapp01 host`. | The container stops and starts; Nagios host state follows its check timing. |
| 13. Accounts & settings | Sign out before switching users. Tour **Manage Accounts**, **Manage Roles** and **Settings** tabs. | The new account's permissions change which tabs and actions are available. Email delivery needs separate SMTP setup. |

## Fault command card

```bash
Pinpoint-Demo-faults.sh status
Pinpoint-Demo-faults.sh reset                # baseline after any fault
Pinpoint-Demo-faults.sh manifest
Pinpoint-Demo-faults.sh services web03
Pinpoint-Demo-faults.sh down web03 http
Pinpoint-Demo-faults.sh up web03 http
Pinpoint-Demo-faults.sh down dynapp01 host
Pinpoint-Demo-faults.sh up dynapp01 host
Pinpoint-Demo-faults.sh dhcp-move dynweb01 10.77.1.25
Pinpoint-Demo-faults.sh dhcp-recover      # only after an interrupted move
Pinpoint-Demo-faults.sh address-mode show dynweb01
Pinpoint-Demo-faults.sh address-mode static dynweb01 10.77.1.15   # slots .15 to .19 only
Pinpoint-Demo-faults.sh address-mode dhcp dynweb01
Pinpoint-Demo-faults.sh address-mode recover                       # only after an interrupted change
Pinpoint-Demo-faults.sh ports list web03
Pinpoint-Demo-faults.sh ports open web03 http 8088     # also: tcp; ports 1024-65535 only
Pinpoint-Demo-faults.sh ports close web03 8088
Pinpoint-Demo-faults.sh ports restore all             # end-of-demo cleanup
```

Other prepared faults: `web03 https`, `api02 http`, `ftp01 ftp`, `mail01 smtp|imap`, `dns01 dns`, `db01 pgsql`, `snmp02 snmp`, and `ssh` on the targets that run it. `host` stops only the selected container. Unknown targets and services are rejected, and DHCP moves accept only the five DHCP clients and an address in `10.77.1.0/27`. Extra ports are HTTP or plain TCP only, between 1024 and 65535, never a management, NCPA or baseline port, at most four per target, and `close` works only on ports opened this way. A container restart also clears them. Stopping a monitored SSH service does not remove your way back in: the controls reach the containers through Docker.

While a DHCP move or address-mode change is interrupted, every modifying command is refused until `dhcp-recover` or `address-mode recover` completes. A static address is not saved across a container restart: the client comes back on DHCP at its reserved address. Return a client to DHCP before `dhcp-move`, `up` or lease commands. `status` still works.

## Port Missing and archive: timing

Closing a listener does not make the row disappear. The sequence is: the check fails (CRITICAL) at the next hard state; after five scans do not see the port it becomes **Missing** and stays monitored; after the configured period (`PORT_ARCHIVE_AFTER_DAYS`, default 30 days) it is **archived** and its Nagios service is removed. See the Ports rules in the [Device Inventory requirements](../spec%20files/Device_Inventory_Requirements.md). For a live demo, show the failed check and recovery, and describe Missing and archive instead of waiting for them.

## Timing and recovery cues

- The wall measures the target immediately; Pinpoint waits for Nagios checks, retries and polling. A red wall row before a Pinpoint alert is expected. Do not keep rescanning while a scan is running.
- For the simple failure demo, keep automatic recovery **off** or use **Record only**, or the fault may disappear before the audience sees it.
- If the alert does not appear, confirm the service is monitored, its plugin is enabled, the wall says it is stopped, and the appliance can reach the target.
- At the end run `up` for every fault you used, run `ports restore all`, return every DHCP client to DHCP on its own address (`dynweb01` is `.20`), cancel any maintenance window, and disable or delete the demo remediation action. Check `status`: all fourteen targets running and five DHCP leases at `.20` to `.24`.
