# Prepared Windows test device (#274)

`pinpoint-defense-win01` has Windows 10 Home build 19045 and NCPA 3.5.0 installed.
It has a powered-off `ncpa-ready` snapshot; the VM is currently running for the laptop pilot. This is preparation for the
[defense lab plan](../docs/plans/Defense_Demo_Lab_Plan.md), not the completed
fifteen-device demo. [Observed installation and API results](../docs/test-runs/2026-10-27-issue-274-windows-home-install/REPORT.md).

| Item | Value |
|---|---|
| VM UUID | `5fb21051-8a4f-45b0-a7f0-de3cedceab83` |
| Windows computer name | `WIN01` |
| Resources | 3 GiB RAM, 2 CPUs, 40 GiB dynamic disk |
| Network | Host-only Adapter `vboxnet1`; no NAT or physical bridge |
| Address / MAC | `10.77.1.3/27`, `02:77:01:00:00:02`; no default route |
| NCPA | Automatic Windows service `ncpa`, TCP 5693; firewall permits `10.77.1.1` only |
| Final snapshot | `ncpa-ready`, UUID `24eb5fdd-5f6c-4fdb-bfb8-a4b19e08523e` |
| Activation | Pending; owner selected Home for testing without a purchased license |

For current appliance setup and registration steps, see [presenter setup](defense/PRESENTER_SETUP.md).

## Access and private state

The local Windows user is `presenter`. The generated login password and NCPA
token are stored in `login-password` and `ncpa-token` under
`~/.local/share/pinpoint-defense/windows-home/`. Read them privately when needed;
keep them outside recordings, reports and Git. Do not use credential values in
command-line arguments. The temporary built-in Administrator account is disabled,
UAC remains enabled, and automatic desktop logon is disabled. NCPA starts before
any user signs in. Setup media is detached and boot order is disk only.

The same private directory holds the VM, owner marker, preparation evidence and
one-time helper copies. These are local preparation artifacts, not a portable
presenter controller. Do not rerun the creation helper against this existing VM.
The earlier `windows-installed` and `ncpa-pre-media-cleanup` snapshots are retained
as intermediate recovery points; use the final `ncpa-ready` baseline for later
agent preparation.

Before any later start, establish exclusive host/VM ownership, check the exact
UUID/NIC attachment and resources, and acquire the canonical host control claim
as required by the [VM lab procedure](../docs/plans/VM_Lab_Plan.md). Never start
this VM alongside another user's lab. Host KVM can block VirtualBox with
`VERR_SVM_IN_USE`; the owner temporarily unloaded it for this installation.
Restore with `sudo modprobe kvm_amd` only while VirtualBox VMs are off. A later
VirtualBox session may need the owner to release KVM again; no persistent host
configuration was changed. Preserve state on an ownership or hypervisor failure.

## Verified agent paths

The local authenticated API returned CPU and virtual-memory percentages. The
Windows disk node is `C:|`, with metric `disk/logical/C:|/used_percent`. The
`processes` API accepts `name=ncpa.exe`; an actual check counted three processes.
This does not promise that every Windows version uses the same disk/process
names or that Pinpoint has configured these checks yet.

Once the appliance joins the completed, approved defense segment, discover the
Windows device and use **Register an agent I installed** with its private token.
Then verify authenticated disk discovery, a real Windows metric in Pinpoint and
monitoring recovery. That appliance registration, licensed-Windows acceptance,
all-fifteen count and rehearsals are still pending. The ordinary old VM/Docker
scan scopes are not expanded by this preparation.
