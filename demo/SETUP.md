# Setup from a clean machine

Everything to go from nothing to a working demo lab. Run all commands from the
repository root. Commands that change things print a plan first and need `--apply`.

## 1. What you need

| Need | Notes |
|---|---|
| Linux laptop, Python 3.10+, `git` | Developed on Debian 13 |
| Docker, usable without `sudo` | `docker version` must work |
| VirtualBox 7.x | `VBoxManage --version` |
| `sudo` | Setup writes root-owned private files (run `sudo -v` first) |
| RAM and disk | At least 3 GiB RAM free for the containers (preflight refuses less), more for two VMs; about 20 GiB disk free |
| Windows 10 ISO | Only if you create the Windows VM; or reuse your prepared `pinpoint-defense-win01`. `create-vms --download-windows-iso` fetches Microsoft's Windows 10 Enterprise evaluation ISO (about 5.5 GB), or pass your own with `--windows-iso` |
| Ubuntu 22.04.5 live-server ISO | For the QA appliance (`scripts/vmlab iso` downloads it) and the demo appliance (`create-vms --download-appliance-iso`, or `--appliance-iso PATH`); both use the same file, `VMLAB_ISO` (default `~/Downloads/ubuntu-22.04.5-live-server-amd64.iso`) |
| NCPA 3.5.0 Windows installer | For the Windows VM; scripted install is tracked in #302 |
| Internet | Image build, Ubuntu and installer downloads |

## 2. Host network

The lab uses VirtualBox's host-only network `vboxnet1` (`10.77.1.0/27`; the host side is
`192.168.57.1`). Check it exists: `VBoxManage list hostonlyifs`. **`vboxnet1` only has an
address and carrier while a VM attached to it is running.**

Stop VPNs and tunnels before the preflight: `sudo systemctl stop tailscaled` (and any
other VPN). The presenter refuses an active tunnel.

## 3. The two VMs

```bash
demo/demo create-vms                  # plan: what is missing
demo/demo create-vms --apply          # creates only the missing VMs
demo/demo create-vms --apply --download-windows-iso --download-appliance-iso   # also fetch the ISOs (plan without --apply shows the URLs)
demo/demo create-vms --apply --windows-iso WIN.iso --appliance-iso UBUNTU.iso  # or use ISOs you already have
```

Then, by hand (see [`appliance/README.md`](appliance/README.md) and
[`appliance/PRESENTER_SETUP.md`](appliance/PRESENTER_SETUP.md)): install the application
on the appliance, give its second adapter `10.77.1.1/27`, install NCPA in Windows
(`10.77.1.3`) and register it in Pinpoint. For a disposable tester appliance use
`demo/demo qa create` instead ([QA hand-off](../docs/qa/Demo_Lab_QA_Handoff.md)).

**Start both VMs and leave them running.** The presenter's safety check requires exactly
these two VMs on `vboxnet1`, both running.

```bash
VBoxManage startvm Pinpoint-Final --type headless
VBoxManage startvm pinpoint-defense-win01 --type headless
```

## 4. The Docker devices

```bash
sudo -v
demo/demo setup                       # plan, preflight and the manual checklist
demo/demo setup --apply               # builds the image, creates and starts the 14 containers
demo/demo presenter enroll-vms        # once, after both VMs are running
demo/demo preflight                   # read-only gate
```

## 5. Check it works

- `demo/demo presenter status` lists all fourteen devices with their services running (the
  DHCP clients on `.20` to `.24`).
- `demo/demo down` then `demo/demo up` stops and restores them.
- In Pinpoint: Settings, Discovery, Networks lists `10.77.1.0/27`; rescan; the devices appear.
  For faster alerts set Nagios `check_interval 1` and `max_check_attempts 1` on the appliance.

Then run the demo from [`README.md`](README.md) and [`USAGE.md`](USAGE.md).

## 6. Troubleshooting

| You see | Cause and fix |
|---|---|
| `Presenter control refused` on every command | Both VMs must be running; wait a minute after starting them, then retry. `vboxnet1` needs an address: `ip -br addr show vboxnet1` |
| `Preflight blocked: Active VPN/tunnel` | Stop the tunnel service: `sudo systemctl stop tailscaled` |
| Setup: `network id ... not found` on `docker start` | The macvlan network went stale while `vboxnet1` was down. `demo/demo destroy --apply`, start a VM, `demo/demo setup --apply` |
| Containers exit with `Owned defense node operation refused` | The owner marker in the private `context.json` changed. Never delete it; setup keeps the existing one |
| Setup: `uses an older image` | Rebuilt image. `demo/demo destroy --apply`, then setup again |
| `snmp02`/`dynsnmp01` refuse to start | The SNMP community file is invalid (needs 32 lowercase hex). Rewrite it: `openssl rand -hex 16 \| sudo tee <private dir>/pilot-catalog/private/snmp-community` |
| `Host controller unavailable, already owned` in tests | Another `demo/demo` or `scripts/vmlab` run holds the host lock; wait for it |
| `vmlab: preflight FAILED: ownership is ambiguous` during `demo/demo qa create` | A VM is running or port 2251/18080 is in use. Power off every VM first, then retry |
| Start over | `demo/demo destroy --apply`, then `demo/demo setup --apply` |

The private state (identities, credentials, pins) lives in
`~/.local/share/pinpoint-defense/`. Never commit it and never delete `host-docker/context/`.
