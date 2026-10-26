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

1. [x] Record ownership, snapshots, routes, capacity, transition/recovery, planned architecture probe and injection/secret review boundaries in `docs/plans/Defense_Demo_Lab_Plan.md`; record observed inventory under `docs/test-runs/`. Preparation complete; person review and live proof are pending.
2. [ ] After the required person review, test first, then add manifest and guarded preflight/controller in `demo/` with isolated tests; update `spec files/Agent_Workflow_and_CI.md` for the new explicitly bounded demo scope before any scan.
3. [ ] Prove the two-MAC/DHCP/management/isolation spike with the real appliance and dedicated target-host; record exact settings and measurements in the plan/report; revise topology if needed.
4. [ ] Build the real daemon catalog in `demo/defense/`; test/provision 14 Linux targets plus clearly labelled win-slot; verify product discovery, plugins and Nagios against the manifest.
5. [ ] Test/implement portable allowlisted listener and host controls in `demo/`; migrate and adapt the three Documents files; verify shortcut and interruption/restore paths.
6. [ ] Test/implement five-client DHCP and transactional address-mode controls in `demo/`; run real identity, history, collision, outage and rollback matrix; keep `lab/dhcp/` independent.
7. [ ] With owner-supplied Windows, prepare NCPA privately, snapshot/register/probe metrics, replace win-slot and repeat all-15 validation; document Windows instructions in `demo/`.
   - [ ] 7a (current user-requested preparation): Install Windows 10 Home image 1 in a new exact-owned `pinpoint-defense-win01` VM, 3072 MiB/2 CPUs/40 GiB dynamic disk, only `pinpoint-defense` Internal Network; no default gateway, NAT or bridge. Use unattended private password files and Guest Additions; verify guest OS and take a powered-off `windows-installed` snapshot. Record sanitized installation observations under `docs/test-runs/` and private ownership/evidence under `~/.local/share/pinpoint-defense/windows-home/`. Activation/license acceptance stays pending.
   - [ ] 7b: Install/configure NCPA with private token and prove agent locally; later prove appliance-to-Windows manual registration, metric and all-fifteen acceptance on the completed network. A paid license or suitable evaluation must satisfy the final license requirement; Home testing installation alone cannot tick FC5.
8. [ ] Rehearse twice, record sanitized `docs/test-runs/` evidence; update `demo/README.md`, lab manuals and owning specs/status; run relevant tooling/backend checks and `scripts/verify.sh all`; finish PR after all acceptance evidence exists.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Read #274 and workflow; isolated checkout; full requirement coverage and ordered plan | gh issue view 274 --json title,body,comments,state,labels,url; scripts/vmlab preflight | Issue open with no comments; ownership preflight green for powered-off QA appliance |
| 1 | Recorded actual read-only inventory, proposed transition/recovery/security boundaries, sanitized report, and pending status/spec links; no runtime behavior changed | scripts/verify.sh docs | green: verify: docs OK; diff whitespace check also green |
| Installation inquiry | Owner supplied a Windows 10 ISO; confirmed bootable ISO metadata and NCPA Windows compatibility; queried unattended detection and current capacity without VM mutation | timeout 25s scripts/vmlab preflight | Failed: ownership ambiguous or metadata inaccessible; two same-user VBoxSVC processes observed. No installation started |
| Installation follow-up | Terminated only the agent-owned hung VBoxManage query; serial ownership check and bounded ISO detection then succeeded; no controller/VM killed | timeout 25s scripts/vmlab preflight; timeout 30s VBoxManage unattended detect --iso=/home/paeng/Documents/00-School_Documents/Mine/SAM/ISOs/Win10_22H2_English_x64v1.iso | Ownership green; Windows10_64, x64/en-US, Home/Pro/Education variants; unattended installation supported. Asked owner which licensed edition to install |
| Installation notes | Corrected current plan/status for available Windows installation media; retained historical report unchanged | scripts/verify.sh docs | green: verify: docs OK; edition choice still pending; no VM created or started |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): green: verify: docs OK. Serial host ownership preflight and bounded unattended detection also passed. Windows10_64, x64/en-US, image 1 Home, image 4 Education, image 6 Pro and other variants; unattended installation supported. No Windows VM created/started.
- Hypothesis: Serial VBox calls avoid the transient duplicate-controller startup observed during concurrent reads. Current sample: 8291 MiB available; Windows-only installation may fit, but the combined lab budget remains pending. New presenter command-path implementation still requires the recorded workflow review.
- Next action (one specific step, not "continue"): Perform step 7a's isolated Windows 10 Home preparation using private unattended credentials, a canonical host claim and fresh VM ownership/capacity checks.

## Decisions and notes

- All issue requirements are covered by FC1-FC8. No final requirement is waived. Temporary win-slot exercises Linux/device-count work only.
- Initial owner statement that Windows media was unavailable was superseded later on 2026-10-27: the owner identified `/home/paeng/Documents/00-School_Documents/Mine/SAM/ISOs/Win10_22H2_English_x64v1.iso`. `file` reports a bootable ISO 9660 image labelled `CCCOMA_X64FRE_EN-US_DV9`; size 6140975104 bytes. Installation media is available; integrity, edition, license, installation and NCPA acceptance are not verified. Historical inventory report retains the statement as it was at that run's time.
- Worktree is `/tmp/pinpoint-issue-274` because the initial sandbox allowed writes there; branch metadata is in the original repository. No changes to the user's main checkout.
- Initial sandboxed VBox/netlink observations were unusable. After access changed, actual host preflight passed. Do not treat sandbox missing-vboxdrv output as host failure.
- Existing unrelated Windows-named VMs are not authorized Windows images and must not be touched.
- `.agent/workflows/work-issue.md` section 4 explicitly stops at sensitive modules; Engineering Standards includes command execution paths. Prepare an explicit injection/secret-exposure review before changing the presenter controller or VM networking.
- Required person decision: approve the proposed controller/guest-helper boundaries in the plan's security review table, so implementation can resume within the already requested issue scope. This gate is an explicit workflow requirement, not a new request for general lab permission.
- Step 1 wording clarified to distinguish the planned architecture probe from a performed one. No live acceptance was observed, so all eight finish-condition items remain unticked.
- Actual inventory/preflight evidence is private at `/home/paeng/pinpoint-test-results/issue-274-inventory-20261027/inventory.json`; sanitized report is `docs/test-runs/2026-10-27-issue-274-defense-inventory/REPORT.md`. No VM, network, guest, discovery setting, listener or Documents shortcut was changed.
- Re-read issue finish conditions on 2026-10-27: still open, no comments, all eight gates unchanged. No product defect observed in this read-only preparation.
- Draft PR: https://github.com/esfen14/Pinpoint/pull/276. User asked whether the agent can install Windows; agent can automate VM setup/install/NCPA subject to successful ownership/capacity checks and any interactive Windows steps. The attempted unattended detection hung; only that agent-owned query process was terminated, not VBoxSVC or a VM process.
- Installation inquiry recovery succeeded without killing any VBoxSVC or VM or removing IPC/locks. VBox unattended supports password-file/stdin inputs; do not pass passwords or product keys on the CLI. Edition question is pending; no product key requested in chat. The initial media-unavailable blocker is superseded, and the transient ownership failure is resolved.
- Owner subsequently clarified that no purchased license is available, then answered the edition question with Windows 10 Home. Prepare the selected edition for testing with activation pending; do not claim the issue's licensed-Windows gate passed or use activation bypasses. A local Windows Server 2022 evaluation ISO was also detected and offered as an alternative (Microsoft documents 180 days and online activation within 10 days), but the owner's latest edition selection is Home.
- Plan order revised for the user's direct Windows installation request: perform isolated step 7a before the remaining shared-lab controller work. This creates no presenter controller or guest command-dispatch implementation; the earlier sensitive-code review remains pending for step 2. Existing VMs and appliance are not altered. Exact new VM name/UUID and private owner marker gate every setup action; all values and operations are fixed, argv is an argument list, passwords enter via private files, and unattended stdout remains private because it may include secrets.
