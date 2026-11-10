# Demo lab: QA hand-off

How a QA tester builds, uses, resets and destroys the demo test environment: one
disposable Pinpoint appliance VM, the Windows NCPA VM and fourteen Docker devices, all on
the host-only network `10.77.1.0/27`. Prerequisites and troubleshooting:
[`demo/SETUP.md`](../../demo/SETUP.md). Command list: [`demo/USAGE.md`](../../demo/USAGE.md).
What is in and out of QA scope: [`QA_Journeys_and_Scope.md`](QA_Journeys_and_Scope.md).

## Build

**Before `demo/demo qa create --apply`, power off every VM** (including `Pinpoint-Final` and
`pinpoint-defense-win01`). `scripts/vmlab`'s creation preflight refuses unless no VM is running,
ports 2251 and 18080 are free and only one VirtualBox service is active; it fails with
"ownership is ambiguous". Start the VMs again after the build.

```bash
demo/demo qa create                   # plan: iso, create, provision, fresh
demo/demo qa create --apply           # builds qa-pinpoint-appliance (30 to 60 minutes)
sudo -v && demo/demo setup --apply    # the fourteen Docker devices
scripts/vmlab setup-admin             # first-run administrator (credentials stay in the QA state folder)
```
Start the Windows VM (`pinpoint-defense-win01`) and register it as in
[`PRESENTER_SETUP.md`](../../demo/appliance/PRESENTER_SETUP.md) section 2. Run one lab at a
time: the demo appliance and the QA appliance share `vboxnet1`.

## Use

- Find devices: rescan in Pinpoint (`scripts/vmlab smoke` does login, discovery and an Up check).
- Create failures: `demo/demo down web03 http`, `demo/demo up web03 http`; change an
  address with `demo/demo dhcp-move` or `address-mode`; open and close ports with
  `demo/demo ports`; return to baseline with `demo/demo reset`.
- Alerts: `scripts/vmlab alerts [target]` takes a container down, checks the alert,
  acknowledges and restores.
- Record results as described in [`docs/test-runs/README.md`](../test-runs/README.md).

## Reset and destroy

```bash
demo/demo qa reset                    # clean Ubuntu+Nagios snapshot, fresh build of the branch
demo/demo reset                       # containers back to baseline
demo/demo qa destroy --apply          # type "destroy": removes only the QA VM, disk and QA state
demo/demo destroy --apply             # type "destroy": removes only the demo containers and network
```

## Known limits

- Run live: the container creation, `demo/demo preflight`, `demo/demo create-vms` (it leaves
  existing VMs untouched), `scripts/vmlab smoke` (18 of 18) and `scripts/vmlab alerts` (12 of 12)
  against the QA appliance. Discovery of the /27 takes about 13 minutes there (the smoke test
  waits up to 20). `create-vms --apply` was also run live to create a missing Pinpoint-Final (4096 MB, NAT with
  127.0.0.1:18080 to port 80, host-only vboxnet1 on NIC 2).
- The Windows unattended install was run live (Windows 10 Enterprise evaluation ISO fetched with
  `--download-windows-iso`): it reaches the desktop as `presenter` with the Guest Additions running.
  Evaluation media need no product key, so `create-vms` passes VirtualBox's answer-file template with
  the ProductKey element removed. NCPA is still installed by hand (#302).
- `demo/demo qa create` was run live (VM built, Ubuntu + Nagios provisioned, Pinpoint deployed).
  The installer health check ends with one expected failure, "pinpoint has sudo rights beyond
  'systemctl reload nagios'", so `qa create` reports "stopped at fresh" even though the appliance
  is up. The app grants `pinpoint` `systemctl restart nagios` on purpose (#121); the installer's
  `setup/pinpoint-healthcheck.sh` has not been updated to match. Continue with
  `scripts/vmlab setup-admin` (same `VMLAB_CONFIG`/`VMLAB_STATE_DIR` as `qa status`).
- A new Windows VM has no scripted NCPA install (#302); the prepared VM already has it.
- No automated NCPA deployment run: the Linux containers have no password SSH.
