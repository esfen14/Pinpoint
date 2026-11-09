# Part 1: Pinpoint device setup

The machine **under test**: the Pinpoint appliance VM and the Windows test VM.
Do this once, then do [Part 2: Docker devices](../targets/README.md), then run the
demo from the [demo index](../README.md).

Paths such as `~/.local/share/pinpoint-defense/` are **example locations** of
private state on the presenter's laptop; credentials never live in the repository.
Read them locally and keep them out of slides, recordings and reports.

## Creating the two VMs

`demo/demo create-vms` prints the VBoxManage plan for the Pinpoint appliance (`Pinpoint-Final`) and the Windows test VM (`pinpoint-defense-win01`) and creates only the missing ones with `--apply` (add `--windows-iso`). Installing the application is `scripts/vmlab`; the NCPA install and snapshots are manual.

## What the appliance must have

| Item | Required value | Check |
|---|---|---|
| Adapter 1 | NAT, forwards the web UI to `http://127.0.0.1:18080` | open the URL |
| Adapter 2 | VirtualBox host-only `vboxnet1` (never a physical or Wi-Fi adapter) | `VBoxManage showvminfo <vm> \| grep -i "NIC 2"` |
| Adapter 2 address | `10.77.1.1/27`, no gateway, no DNS, no DHCP; cloud-init network config disabled | in the appliance: `ip -br -4 address` |
| Reachability | Windows `10.77.1.3` and the Docker devices answer ping | in the appliance: `ping -c 2 10.77.1.3` |
| Pinpoint discovery network | `10.77.1.0/27` (Settings, Discovery, Networks) | Settings page |
| Nagios timing | `check_interval 1`, `max_check_attempts 1` in the service template, so alerts show in minutes instead of about 7 | change on the appliance only, not in this repository |
| Session timeout | raised so nobody is logged out mid-demo | Settings page |

Step-by-step commands, the netplan edit and the cloud-init setting:
[`PRESENTER_SETUP.md`](PRESENTER_SETUP.md) section 1.

## Windows test VM (`win01`)

Windows 10 Home with NCPA, host-only `vboxnet1`, address `10.77.1.3`. Preparation
facts, credentials location and the verified agent paths: [`WINDOWS_READY.md`](WINDOWS_READY.md).
Registering it in Pinpoint (**NCPA Deployment, Register an agent I installed**,
port `5693`): [`PRESENTER_SETUP.md`](PRESENTER_SETUP.md) section 2.

## Credentials

| Secret | Where it is | Notes |
|---|---|---|
| Pinpoint administrator | the appliance's own application credentials | not stored in this repository |
| Windows `presenter` password, NCPA token | `login-password` and `ncpa-token` in the private state directory | never put in command arguments |
| SNMP community | `snmp-community` in the private host-Docker catalog | separate from the NCPA token |
| Linux containers | none: SSH password login is off; use the presenter commands | |

## Restore to baseline

Power the appliance off and restore its saved snapshot with
`VBoxManage snapshot <vm> restore <snapshot>`; restore the Windows VM to its
`ncpa-ready` snapshot only if you intend to register the agent again. Restoring a
snapshot does not reset the Docker devices: run `demo/demo reset` (see
[`USAGE.md`](../USAGE.md)).

## Cannot be scripted

These need a person; `demo/demo setup` prints them as a checklist with the check
above: appliance adapter 2, its address, Windows credentials and NCPA
registration, the Pinpoint discovery network, and the Nagios timing.
