# Pinpoint demo lab

**The current lab is the fifteen-device Docker lab:** fourteen Linux containers
(`demo/targets/`) plus one Windows VM, all on the isolated host-only network
`10.77.1.0/27`, monitored by a Pinpoint appliance VM. The earlier five-VM
VirtualBox lab is legacy and lives in [`lab/legacy-vms/`](../lab/legacy-vms/README.md).

## Order

1. **[Part 1: Pinpoint device setup](appliance/README.md)**: the appliance VM and
   the Windows test VM (what is under test).
2. **[Part 2: Docker container setup](targets/README.md)**: the fourteen monitored
   devices, the presenter controls and the DHCP allocator.
3. **Run the demo**: [`Pinpoint-Demo-Script.md`](Pinpoint-Demo-Script.md),
   [`Pinpoint-Defense-Cue-Card.md`](Pinpoint-Defense-Cue-Card.md),
   [`REHEARSAL.md`](REHEARSAL.md).

[`USAGE.md`](USAGE.md) is the command cheat sheet: take a device down, change its
IP, open a port, return to baseline. One front door: `demo/demo`.

## Related

- [Local lab manual](../docs/manuals/Local_Lab.md): the fast five-target Docker lab (`scripts/lab`), not this demo.
- [Defense demo lab plan](../docs/plans/Defense_Demo_Lab_Plan.md): why this lab is built this way.
- [VM lab plan](../docs/plans/VM_Lab_Plan.md) and [`lab/`](../lab/): the appliance/VM test harness.
- Rules and status: `spec files/Agent_Workflow_and_CI.md` (test environments) and `spec files/Implementation_Status.md`.
