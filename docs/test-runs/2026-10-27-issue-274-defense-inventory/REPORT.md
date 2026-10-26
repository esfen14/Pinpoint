# Defense demo: read-only inventory and transition preparation

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila |
| Commit inspected | `8201ce27ca4fcce3e8fb398e35d8cdcef1a1d874` (plan checkpoint; lab code unchanged from `00d78f10`) |
| Plan | [Defense demo plan](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor / mode | Codex, AI-assisted host CLI; read-only inventory, no browser or product case execution |
| Catalog / queue / session / batch | Not a QA catalog run; issue #274 preparation only; no catalog credit |
| Deployed application / installer | Not inspected; no deployment or guest login performed |
| Baseline / restoration | Eleven registered VMs, all powered off; no VM/network/guest/database mutation |
| Final inventory window | 2026-10-27 01:03:41–01:03:46 Asia/Manila (2026-10-26 17:03:41–17:03:46 UTC) |
| Host tooling | VirtualBox `7.2.14r174565`; host Docker network metadata readable |
| Private raw evidence | `/home/paeng/pinpoint-test-results/issue-274-inventory-20261027/inventory.json`, owner-only directory/file |

## Result

**Overall: Partial — preparation only.** Existing ownership/snapshot/NIC and
host capacity/network metadata were observed. A new isolated segment and
recovery procedure are proposed. The architecture spike, new controller,
15-device catalog, five-client DHCP, Windows and rehearsals have not run.
No finish-condition item is complete.

Totals: 0 unique catalog TC, 0 E2E cases, 0 accepted historical results.
The rows below are preparation observations, not product acceptance cases.

## Observations

| Observation | Result | Evidence / limitation | Issue |
|---|---|---|---|
| Appliance ownership preflight | Pass | `scripts/vmlab preflight`: UUID `351eb491-f5e1-4854-a7e4-68309ad774ad`, powered off, exclusive control/endpoints | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Existing VM inventory | Pass | Eleven registered, zero running; exact owned identities below | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Candidate host IPv4 overlap check | Pass, scoped | Candidate `10.77.1.0/27` has no overlap among 22 collected route/interface/Docker/documented lab ranges; guest routes and configured inactive VPN profiles not checked | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Network boundary preparation | Partially Pass | New `pinpoint-defense` network proposed; old network includes unowned appliances, one with a bridged NIC; no packet capture or isolation claim | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Resource budget | Blocked for proposed start | 8705 MiB available, below proposed 9216 MiB Linux-start threshold before overhead; 81785 MiB free disk; growth budget not yet measured | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Recovery | Partially Pass | Existing snapshot names/UUIDs inventoried; new pre-transition snapshot and actual endpoint restore trial still required | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Presenter migration sources | Pass, inventory only | Three Documents files exist; hashes below; existing launcher hardcodes checkout/five old targets; no copy/shortcut change | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Sensitive command-path review | Blocked | Work-issue section 4 requires person review; proposed enforcement/tests in plan | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Windows | Blocked | Owner explicitly confirmed image still unavailable; unrelated Windows-named VMs are outside scope | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Live architecture/catalog/DHCP/faults/product checks/two rehearsals | Not run | No devices started, no discovery, no DHCP traffic generated | [#274](https://github.com/esfen14/Pinpoint/issues/274) |

## Owned VM inventory

These UUIDs and NIC MACs were read from VirtualBox; ownership here means the
existing repository lab's exact resources, not permission to change arbitrary
VMs sharing a prefix. Every row was powered off. Guest IPs and live listeners
were not probed.

| VM | UUID | RAM MiB | Demo NIC MAC | Recovery metadata observed |
|---|---|---|---|---|
| pinpoint-qa-appliance | 351eb491-f5e1-4854-a7e4-68309ad774ad | 4096 | 08:00:27:71:fa:84 | `os-nagios-ready` / `5c4cc2ec-af83-4b98-af64-9ae7202880a6`; additional snapshots retained |
| pinpoint-demo-base | cb0c6add-d74f-4e67-8266-fac0d011ae57 | 1024 | No demo NIC | `base-ready` / `9c3a578a-1ce3-42d3-b39a-236bd9324c5e` |
| pinpoint-demo-web01 | d064f0c0-e36a-4566-a78a-bdf5327288c5 | 512 | 08:00:27:e3:78:0f | `demo-ready` / `39890d9b-529a-4d08-a4d8-4191f28f6934` |
| pinpoint-demo-web02 | 5adb31b2-079e-4eff-b61a-b8a34c08db6d | 512 | 08:00:27:fe:bd:db | `demo-ready` / `fc0b38ca-5ff0-4e30-93e7-296f6afb04ea` |
| pinpoint-demo-app01 | 623f2af9-4f15-4fb2-b28e-a587bd91fa55 | 512 | 08:00:27:1b:d7:c8 | `demo-ready` / `17f42c1e-d21a-4b10-9d22-08ed4480dd1f` |
| pinpoint-demo-snmp01 | 5671094a-9132-44ee-87a9-06ac92133e83 | 512 | 08:00:27:a5:48:3f | `demo-ready` / `309ffc66-b141-4c45-8ead-12f99f3f00ba` |
| pinpoint-demo-legacy01 | a35d3875-87e4-4bbe-97b5-c84e7d464cb1 | 512 | 08:00:27:64:e5:42 | `demo-ready` / `60aa9e66-bb10-43f8-9177-0edf9bc0ad6e` |

The appliance and five targets have NAT NIC 1 and `pinpoint-demo` Internal
Network NIC 2. The base has NAT only. Appliance forwards bind loopback ports
2250 (SSH) and 18080 (HTTP); base/target SSH forwards use 2200–2205. No VM or
snapshot was restored or changed. Snapshot existence does not establish a
backup of the current application state or a verified endpoint restore.

The other four registered VMs (`Win Server`, `Win Client`, `Pinpoint-Final`,
`Nagios-Demo`) are excluded. Two use another internal network; the latter two
join `pinpoint-demo`, and `Nagios-Demo` also has a physical bridged adapter.
The new defense segment must have only its pinned appliance, target-host and
explicitly owner-supplied Windows member.

Docker networks inspected: ordinary `bridge`, `host`, `none`, `pinpoint-lab_lab`
and `pinpoint-lab_mgmt`. Documented lab scopes `10.77.0.0/28`, `10.78.0.0/24`
and `10.79.0.0/28` are distinct from the candidate. A VirtualBox DHCP server
exists on a separate host-only network; none was listed for `pinpoint-defense`.
This inventory does not prove future absence of rogue DHCP or packet leakage.

## Resource observation

Host RAM: 23273 MiB total, 8705 MiB available. Swap: 23799 MiB total, 2 MiB
used in one sample. Disk: 81785 MiB available. A single sample cannot establish
absence of sustained swap activity. No boot time, all-target peak memory,
scan/check duration or Windows growth requirement was measured. Start must
recheck capacity and preserve at least 3072 MiB available after the workload.

## Migration source inventory

SHA-256 from the three original files in `~/Documents/Pinpoint-Demo/`:

| Source | SHA-256 |
|---|---|
| Pinpoint-Demo-faults.sh | `334cbdf5aa958e48b50d37edbf8c365c8d267a66637a297c6bc2878a29433672` |
| Pinpoint-Demo-Script.md | `2fcb0cc0782168b3d3553081c058fd7f3a2e059e86fe531cea69fe7769db37cb` |
| Pinpoint-Defense-Cue-Card.md | `b9a9ca6fe70a7a31814f3d4e79741cd7ab423bd3c0c07fb4a70989e75d2f4a50` |

## Deviations and restoration

The first sandboxed VBox/netlink calls could not inspect the real host; their
missing-driver/network errors are not host results. After host access changed,
the bounded actual-host inventory and ownership preflight succeeded. No running
VM was stopped, no control process was killed, and no lock/IPC file was removed.
Only private evidence and checkout documentation were written. The successful
final inventory found all eleven VMs off; no restoration mutation was needed.

## Follow-up

Review the concrete injection/secret-exposure boundaries in the plan before
implementing new command paths, as required by the invoked workflow. Then
repeat preflight/capacity/collision checks, inspect guest state and VPN profiles,
prove snapshot recovery and run the two-MAC/DHCP spike before expanding.
Windows remains pending the owner-supplied licensed image. No product defect was
observed; no separate defect issue is justified by this preparation.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside documented existing/candidate lab ranges
- [x] Raw route/interface metadata stays private; only relevant summaries committed
