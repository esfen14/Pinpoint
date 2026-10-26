# Issue #274: One isolated 15-device defense demo lab

Branch: `issue-274-defense-demo`
Status: in-progress

## Finish condition

- [ ] FC1: Inventory lab-owned VMs/networks and recovery; transition to one isolated network; refuse collisions and physical/VPN DHCP or scans.
- [ ] FC2: One real appliance discovers all 15 catalog devices including Windows; manifest records MAC/IP/live listeners/plugins; reproducible start/status/stop/reset.
- [ ] FC3: Five simultaneous real DHCP leases; persistent identities; A-to-B and IP reuse; running-client DHCP/static/DHCP with association/recovery, collision refusal, outage rollback and reset.
- [ ] FC4: Allowlisted reversible listener/service/host/DHCP faults, real listener and product checks, idempotent undo and baseline restoration.
- [ ] FC5: Preinstalled Windows NCPA, manual registration and one real metric; no token in repository/evidence.
- [ ] FC6: Migrate Documents controls/walkthrough/cue card into demo; portable command set and working Documents shortcut; safe fault/undo and Missing/archive timing.
- [ ] FC7: Two full clean-baseline rehearsals; sanitized report of count, leases, scan/alert/recovery timing, resources, undo and healthy finish.
- [ ] FC8: Update manuals/specifications/Implementation_Status; docs and tooling/backend checks; product defects tracked separately.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Replace/repurpose old five-VM demo; record exact ownership and recovery before mutation | FC1 | Read-only VBox UUID/NIC/snapshot inventory; transition plan; guarded rollback rehearsal |
| One isolated appliance, target-host with no demo IP, fourteen Linux targets and Windows; first prove two MACs and real DHCP across VirtualBox | FC1, FC2 | Appliance ARP/nmap and packet capture, guest NIC/routes/firewall checks, management survival after selected fault |
| Collision-checked subnet large enough for pool/static slots; approved bounded scan; no physical/household/campus/VPN exposure | FC1 | Route/interface/VM/Docker collision tests; guarded scan refusal; internal NIC and physical capture evidence |
| Resource check on every start; measured all-target cycle with >=3 GiB available and no sustained swap thrash; disk for Windows/snapshots/logs | FC1, FC7 | Preflight resource rejection tests; free/df/vmstat sampling during all-target boot/scan/check |
| All catalog targets and real protocol daemons; distinct stable MAC/IP; plugins/settings verified or discovered-only label; UDP included | FC2 | Versioned manifest validation; real protocol probes, appliance service mapping and nagios validation/reload; UI count |
| status/wall derived from manifest; preflight/up/down/reset reproducible | FC2, FC4 | Controller contract tests and two real clean-baseline runs |
| ports list/open/close/restore; preset pairs and checked high HTTP/TCP ports; reserve management/NCPA, reject collision/wrong target, interrupted cleanup | FC4 | Isolated invalid-input/ownership tests; real listener addition/rescan/failure/restore, SSH survival and interruption tests |
| Host stop/start preserves identity and persistent data; end-of-demo restoration | FC4 | Runtime/volume/identity and baseline comparison around faults and repeated undo |
| Five real clients on interfaces not numbered by Docker IPAM; stable MAC/client ID/SSH key; lease logs and one DHCP allocator | FC3 | Five distinct DHCP ACK/lease/interface records and identity fingerprints; network attachment inventory |
| Release/reservation/acquire A-to-B; other-client reuse; no replacement or manual merge; history/monitoring association | FC3 | DHCP logs and unchanged runtime identity, product device/Nagios IDs and before/after history/checks |
| address-mode show/static/dhcp; checked unused slots outside pool; one address; outage return rollback, interruption and idempotent reset | FC3 | Address-mode unit/state-machine tests and real fault matrix with identity/ARP/address/product proof |
| Server stop/start and reset preserve management/logs; existing scripts/dhcp-lab independent | FC3, FC4 | Recovery tests, saved DHCP logs, unchanged issue-187 source and isolated tests |
| Windows licensed image owner-supplied; isolated NIC, powered-off ncpa-ready snapshot, firewall/listener/API/disk/process probes; token private | FC5 | Owner image, appliance-to-Windows probes, snapshot UUID and manual registration/real metric evidence |
| Linux win-slot permitted temporarily; cannot pass Windows/final fifteen gates | FC2, FC5 | Explicit manifest role and status label; final count repeated with real Windows |
| Existing Documents files copied/adapted to repo; one command set, portable paths and working Documents shortcut | FC6 | Source inventory, migration diff, shell/path tests and shortcut dispatch proof |
| Presenter distinguishes addition, failed check and lifecycle; Missing after five scans and archive after configured period | FC4, FC6 | Walkthrough/cue card plus observed rescan/check sequence; no promise of immediate deletion |
| Twice from clean baseline, exact timing/resources/restoration and sanitized live report | FC7 | Two recorded rehearsal matrices in docs/test-runs with raw private evidence |
| Matching manuals/specs/status and checks; defects filed separately, no product scope creep | FC8 | scripts/verify.sh docs/all and relevant tooling/backend tests; linked findings |

## Plan

1. [ ] Record ownership, snapshots, routes, capacity, transition/recovery, architecture probe and injection/secret review in `docs/plans/Defense_Demo_Lab_Plan.md`; record observed inventory under `docs/test-runs/`.
2. [ ] Test first, then add manifest and guarded preflight/controller in `demo/` with isolated tests; update `spec files/Agent_Workflow_and_CI.md` for the new explicitly bounded demo scope before any scan.
3. [ ] Prove the two-MAC/DHCP/management/isolation spike with the real appliance and dedicated target-host; record exact settings and measurements in the plan/report; revise topology if needed.
4. [ ] Build the real daemon catalog in `demo/defense/`; test/provision 14 Linux targets plus clearly labelled win-slot; verify product discovery, plugins and Nagios against the manifest.
5. [ ] Test/implement portable allowlisted listener and host controls in `demo/`; migrate and adapt the three Documents files; verify shortcut and interruption/restore paths.
6. [ ] Test/implement five-client DHCP and transactional address-mode controls in `demo/`; run real identity, history, collision, outage and rollback matrix; keep `lab/dhcp/` independent.
7. [ ] With owner-supplied Windows, prepare NCPA privately, snapshot/register/probe metrics, replace win-slot and repeat all-15 validation; document Windows instructions in `demo/`.
8. [ ] Rehearse twice, record sanitized `docs/test-runs/` evidence; update `demo/README.md`, lab manuals and owning specs/status; run relevant tooling/backend checks and `scripts/verify.sh all`; finish PR after all acceptance evidence exists.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Read #274 and workflow; isolated checkout; full requirement coverage and ordered plan | gh issue view 274 --json title,body,comments,state,labels,url; scripts/vmlab preflight | Issue open with no comments; ownership preflight green for powered-off QA appliance |

## State for the next session

- Last check run (exact command): `scripts/vmlab preflight`
- Result (first failing lines, or "green"): green; appliance UUID 351eb491-f5e1-4854-a7e4-68309ad774ad powered off, exclusive controller/endpoints.
- Hypothesis: Stage one can retain old powered-off disks as recovery while using a new target-host and isolated network. New command execution paths require the workflow's person review before implementation.
- Next action (one specific step, not "continue"): Write the concrete transition/security-review plan and sanitized read-only inventory report, then checkpoint the required review gate.

## Decisions and notes

- All issue requirements are covered by FC1-FC8. No final requirement is waived. Temporary win-slot exercises Linux/device-count work only.
- Owner confirmed on 2026-10-27 that a licensed Windows image is still unavailable. Step 7 and final Windows acceptance remain pending; issue explicitly permits finishing other stages first.
- Worktree is `/tmp/pinpoint-issue-274` because the initial sandbox allowed writes there; branch metadata is in the original repository. No changes to the user's main checkout.
- Initial sandboxed VBox/netlink observations were unusable. After access changed, actual host preflight passed. Do not treat sandbox missing-vboxdrv output as host failure.
- Existing unrelated Windows-named VMs are not authorized Windows images and must not be touched.
- `.agent/workflows/work-issue.md` section 4 explicitly stops at sensitive modules; Engineering Standards includes command execution paths. Prepare an explicit injection/secret-exposure review before changing the presenter controller or VM networking.
