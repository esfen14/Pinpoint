# Issue #162: control diagnosis and lost-edit resolution

| | |
|---|---|
| Date | 2026-10-15 (Asia/Manila) |
| Code tested | Preflight rejection at `5fefa6a2`; positive runtime-NAT preflight at `b22221eb` plus working-tree refinements |
| Plan | [VM Lab Plan](../../plans/VM_Lab_Plan.md), [issue #162](https://github.com/esfen14/Pinpoint/issues/162) |
| Tester | Codex; lab owner supplied retirement and data-loss decisions |
| Environment | Debian Linux host, VirtualBox 7.2.14; inherited Ubuntu appliance and demo target |
| Raw evidence | Tool-session read-only process/source inspection; ignored worktree `test-results/issue162/` (retired inventory and fresh NAT runtime) |

## Result

**Partial recovery, owner-resolved loss.** Split VirtualBox control was observed;
no exact source backup was recovered. The owner explicitly accepted the two
pre-existing uncommitted versions as unrecoverable and authorized removing the
old lab disks and rebuilding the lab. This resolves the recovery decision; it
does not establish recovery of the file contents. A clean-appliance snapshot
trial and replacement-lab provisioning are separate from this diagnosis.

## Cases

| Case | Result | Observed evidence | Issue |
|---|---|---|---|
| R1 Detect split control | Pass | Two same-user VBoxSVC processes, PIDs 130559 and 305485, shared the same registry, IPC pathname and host namespaces. Each held a distinct listening Unix socket: inode 623615 versus 2096899. | |
| R2 Observe control/endpoint disagreement | Pass | Selected manager returned poweroff and no running VMs; loopback SSH/2250 and web/18080 listened with inodes 738211 and 738212. Inherited appliance PID 146006 remained under controller 130559. | |
| R3 Identify exact overwritten originals | Blocked | Read-only search found matching replacement contents in three retained checkouts; no independent backup in the searched guest paths. The owner subsequently resolved this as unrecoverable loss, not successful recovery. | [#162](https://github.com/esfen14/Pinpoint/issues/162) |
| R4 Reject unsafe operations | Pass | Initial 13 isolated regressions and docs stage passed; live preflight returned nonzero with duplicate controllers. Mutation-command tests prove rejection before SSH/API/VBox control operations. | |
| R5 Owner resolution and retirement | Pass | Owner said “Remove the old disks and remake the Lab” and “Accept as unrecoverable but document loss”. Actual SSH endpoints shut down the inherited appliance and web01; after their processes exited, seven explicitly inventoried lab VMs/disks were unregistered/deleted. Unrelated VMs were excluded. | |
| R6 Fresh positive ownership proof | Pass | Newly created blank-disk appliance UUID 351eb491-f5e1-4854-a7e4-68309ad774ad, one same-user controller and one UUID process, exclusive host listeners and actual runtime NAT forwarding sockets. No inherited application data was copied. | |

## Control diagnosis

The two live Unix listening sockets used the identical pathname
`/tmp/.vbox-paeng-ipc/ipcd` in the same host namespaces. Their distinct socket
inodes establish separate IPC listeners. **Inference:** the pathname was removed
or replaced and rebound while the older listener and its established clients
remained alive. New clients reached the new service, while the inherited VM
remained a child of the older service. Both services loaded the same VirtualBox
registry and appliance UUID; the new service's state and snapshot operations did
not describe the inherited process serving the endpoints.

After the newer GUI service exited, a read-only `VBoxManage list runningvms`
again launched a new VBoxSVC rather than reconnecting to the old service, while
the inherited children remained alive. Thus merely closing the GUI or restarting
the command was insufficient. The exact actor that first removed/replaced the
IPC pathname is unknown; no audit trace establishes it. No destructive duplicate
VM start or snapshot reproduction was attempted against the inherited disks.

The initial inode-based positive guard could not pass on this host: the SUID VM
launcher protects `/proc/<pid>/fd`, and this VirtualBox version omits SessionPID
from machine-readable VM metadata. The revised guard queries the controlled VM's
read-only `debugvm ... info nat0` table, requiring actual TCP HOST_FORWARD
sockets to guest SSH/22 and web/80, the same guest destination, exclusive host
listeners and the unique UUID process under the sole controller. Missing or
unsupported runtime evidence rejects. OS permissions were not weakened.

## Lost source contents and comparison

The affected inactive checkout was at `1ca2c75`; the other retained checkouts
were `issue-129-acceptance` at `c9f8e26` and `issue79-tested-20261015` at `3d6471d`.
Before retirement, all three had identical contents for each affected file:

| File | SHA-256 in all three retained checkouts |
|---|---|
| `server/app/api/system/dashboard.py` | `d931fda80e929b6b61c8d34ceb73a5604831fcb3b8330113c73210502bc56e89` |
| `server/app/nagios/status.py` | `6b650f51a05606c68ab35da33fb6145b1452c9ea3bc3b6d910ff167b5d8d94d9` |

Both differed from their committed `1ca2c75` baseline. This proves the retained
copies agree; it cannot identify either overwritten uncommitted version. The
read-only search covered the retained checkout files and backup-name candidates
under guest `/opt/pinpoint`, `/tmp`, `/var/tmp` and `/home/lab`, excluding Git
object stores, virtual environments and node_modules. It was not disk forensics
or exhaustive editor-history recovery. After being told no exact source was
found, the owner accepted the loss and authorized deleting those old disks.

The original issue-129 checkout/database had been retained through the initial
incident recovery. They were then deliberately retired under this new owner
decision. The two incident snapshots were never verified endpoint backups and
were removed with the old appliance; they must not be cited as recovery sources.

## Sanitization

No credentials, keys, raw application configurations, mailbox data, databases or
disk images committed. Source hashes, process identifiers and the documented
loopback lab endpoints are the only identifying evidence included here.
