# Demo cheat sheet

One command: `demo/demo`, run from the repository root. Each entry is one task, the
exact command, and what Pinpoint should show. `demo/demo help` prints the same
commands. Use these only on the disposable demo lab.

Pinpoint delays are measured in the lab, not promised: a failed check turns
CRITICAL at the next hard state (Nagios `check_interval` times `max_check_attempts`;
about 7 minutes with the shipped 5 and 3, about 1 to 3 with 1 and 1), a recovery
clears at the next check, and a new port or address needs a **Rescan Network**
(about 7.5 minutes).

## Lab lifecycle

| Task | Command | What happens |
|---|---|---|
| First-time or fresh-machine setup | `demo/demo setup` then `demo/demo setup --apply` | The first prints the plan and the manual checklist and changes nothing |
| Create the two VMs (missing ones only) | `demo/demo create-vms` then `demo/demo create-vms --apply --windows-iso WIN.iso` | Appliance and Windows VMs on `vboxnet1`; OS install of the appliance is `scripts/vmlab`, NCPA is installed in Windows |
| Start everything and restore baseline | `demo/demo up` | Creates missing containers first, then starts the fourteen and restores baseline services and DHCP leases |
| Stop everything | `demo/demo down` | Stops the fourteen containers; Windows and the appliance are untouched |
| Remove the lab | `demo/demo destroy --apply` | Removes only demo-owned containers and network after a typed confirmation |
| Return everything to baseline | `demo/demo reset` | Addresses, daemons and extra ports back to baseline (about 90 seconds) |
| Check the lab | `demo/demo preflight` and `demo/demo presenter manifest` | Host checks; observed MAC, IP and listeners |

## Take a device or service down and back up

| Task | Command | Pinpoint shows |
|---|---|---|
| One service fails | `demo/demo down web03 http` | `http-80-tcp` CRITICAL on Dashboard Active Alerts after the next hard state |
| Restore it | `demo/demo up web03 http` | The alert clears at the next check; History shows both events |
| A whole device stops | `demo/demo down dynapp01 host` | The host goes DOWN |
| Bring it back | `demo/demo up dynapp01 host` | The host is UP again |
| Live status | `demo/demo status` or `demo/demo wall` | Service states and addresses, from the laptop |

## Change a DHCP device's address

| Task | Command | Pinpoint shows |
|---|---|---|
| Move its lease | `demo/demo dhcp-move dynweb01 10.77.1.25` | After a rescan, the same device has the new address |
| Move it back | `demo/demo dhcp-move dynweb01 10.77.1.20` | Original address |
| Fixed address, same device | `demo/demo address-mode static dynweb01 10.77.1.15` | Same device, address `.15`; host count unchanged |
| Back to DHCP | `demo/demo address-mode dhcp dynweb01` | Returns to a pool address |
| After an interrupted move | `demo/demo dhcp-recover` or `demo/demo address-mode recover` | Finishes or rolls back |

## Open or close an extra port

| Task | Command | Pinpoint shows |
|---|---|---|
| List ports | `demo/demo ports list web03` | Baseline and extra ports |
| Open a port | `demo/demo ports open web03 http 8088` | After a rescan, the port appears in the device's Ports section as Monitored |
| Close it | `demo/demo ports close web03 8088` | Its check goes CRITICAL; it becomes Missing after five scans |
| Remove every extra port | `demo/demo ports restore all` | End-of-demo cleanup |

Targets: `dhcp01 web03 api02 ftp01 mail01 dns01 db01 snmp02 ssh-alt02` (static) and
`dynweb01 dynapp01 dynmail01 dynsnmp01 dynweb02` (DHCP). Windows (`win01`) has no controls.
Services per target are listed by `demo/demo help`.
