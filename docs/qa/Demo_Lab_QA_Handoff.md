# Demo lab: QA hand-off

How a QA tester builds, uses, resets and destroys the demo test environment: one
disposable Pinpoint appliance VM, the Windows NCPA VM and fourteen Docker devices, all on
the host-only network `10.77.1.0/27`. Prerequisites and troubleshooting:
[`demo/SETUP.md`](../../demo/SETUP.md). Command list: [`demo/USAGE.md`](../../demo/USAGE.md).
What is in and out of QA scope: [`QA_Journeys_and_Scope.md`](QA_Journeys_and_Scope.md).

## Build

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

- Run live: the container creation, `demo/demo preflight`, and `demo/demo create-vms` (it leaves
  existing VMs untouched). Not yet run live: creating a missing VM with `create-vms --apply`, and
  `demo/demo qa create`.
- A new Windows VM has no scripted NCPA install (#302); the prepared VM already has it.
- No automated NCPA deployment run: the Linux containers have no password SSH.
