# Issue #187: Implement isolated DHCP lab with real lease-change acceptance

Branch: `issue-187-isolated-dhcp-lab`
Status: in-progress

## Finish condition

- [x] Docker feasibility experiment documents real DHCP, running A-to-B move, appliance connectivity, cleanup, privilege/isolation/cost and design decision.
- [x] Opt-in controls create/manage isolated server, appliance interface and two persistent clients; capture evidence, reset and cleanly tear down owned resources.
- [x] Safety guards enforce one allocator, binding/isolation, separate management, infrastructure outside pool, ownership, approved range; static labs still work.
- [ ] Live client-1 A-to-B and real discovery/Nagios/browser/history identity continuity pass.
- [ ] Live client-2 A reuse and remaining bounded matrix pass, with clean repeat of primary cases.
- [ ] Sanitized test-run report includes commit, owner, range, DHCP/client/OS/discovery/Nagios/browser/timing/cleanup evidence; raw logs stay on host.
- [ ] Manuals, plans, owning specifications and status updated; changed-stage and all verification pass.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Docker first, real DHCP, fallback if needed | 1 | Throwaway exchange/move/cleanup log and design record |
| Opt-in isolated topology, persistent distinct clients, reservations/leases, lifecycle | 2 | Control tests and live clean setup/teardown |
| Server/client behavior experimentally confirmed | 1, 2 | DHCP packet/lease/client-address evidence |
| Bounded six-case acceptance and primary real product evidence | 4, 5 | Runner results, Nagios/browser capture |
| Approved collision-free range, ownership, no broadcast escape | 3 | Route/preflight checks, QA scope, control tests |
| Repeat primary cases from clean lab | 5 | Two run records |
| Sanitized reporting and unchanged static labs | 3, 6 | Report and existing lab smoke |
| Documentation and all verification | 7 | Docs, stage and all gates |
| Routed discovery, clones, IPv6, failover, NCPA | Excluded | Phase-one exclusions stated in report |

## Plan

1. [x] Run a throwaway Docker feasibility experiment and document evidence/decision in `docs/plans/DHCP_Lab_Extension_Proposal.md` and a new `docs/test-runs/.../REPORT.md`; check routes and lab ownership first.
2. [x] Add failing lifecycle/safety tests under `server/tests/unit/` or `lab/tests/`, then implement the isolated opt-in lab in `lab/dhcp/` and `scripts/dhcp-lab` using the chosen design.
3. [x] Add failing bounded runner tests, then implement `lab/dhcp/acceptance.py` and a test plan under `server/tests/plans/` for the six cases and evidence collection.
4. [ ] Run the live clean-lab matrix with real discovery, Nagios and browser evidence; preserve raw logs off-repository and record actual pass/fail in `docs/test-runs/` (the QA range approval moved before the first full setup).
5. [ ] Update `docs/manuals/Local_Lab.md`, `docs/plans/VM_Lab_Plan.md` if applicable, `spec files/Agent_Workflow_and_CI.md`, `spec files/Data_Model_and_Integrations.md` if behavior changes, and `spec files/Implementation_Status.md`; run changed-stage gates.
6. [ ] Re-read issue and prove each finish item, run `scripts/verify.sh all`, remove progress, push branch and open PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Proved Docker DHCP A-to-B with `CAP_NET_ADMIN`, documented privilege, isolation, cost, cleanup and failure/recovery; selected Docker | `bash /tmp/pinpoint-187-feasibility/run.sh`; `scripts/verify.sh docs` | Two final experiments green; docs green; no residual owned container/network |
| 2 | Added opt-in controller, images, persistent distinct clients, ownership/collision checks, lease operations, evidence and teardown; approved DHCP-only QA range | Focused pytest (4 passed); live `up`, `move`, `reuse`, `client-restart`, `reset`, server stop/start, `down`; `scripts/verify.sh docs`; `scripts/verify.sh backend` | Live controls passed after management bridge correction; no owned resource residue; docs green; backend 3753 passed, 14 skipped |
| 3 | Added bounded live runner, Playwright Inventory/History checkpoint and plan; corrected active-device lookup, host-state casing and browser readiness; documented controls | Focused pytest (11 passed), `scripts/verify.sh frontend`, `scripts/verify.sh docs`; full live matrix cycle 1 | Eight of nine cycle-1 cases pass; browser Inventory checked before client-2's first Nagios snapshot and failed. Runner now waits for that snapshot. Interrupted cycle 2 after preserving cycle-1 evidence; owned lab cleaned up. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh frontend > /tmp/pinpoint-187-frontend.log 2>&1`
- Result (first failing lines, or "green"): green; 0 errors, 1 existing lint warning.
- Hypothesis: Waiting for client-2's fresh UP snapshot before starting Playwright will make Inventory show its A row; all other cycle-1 cases already passed.
- Next action (one specific step, not "continue"): Re-run `scripts/dhcp-accept --lease-seconds 90` from a clean lab and inspect both cycles and browser screenshots.

## Decisions and notes

- Issue finish condition covers all stated implementation requirements and phase-one exclusions.
- No product discovery changes are planned unless the live run exposes a defect; such a defect requires a separate issue under this workflow.
- Docker selected after two successful real A-to-B trials. The first attempt failed because dnsmasq could not reopen its old log file on restart; using a fresh log succeeded. Host sudo is unavailable, so the host-bridge candidate was rejected. The switch uses host PID visibility and `CAP_NET_ADMIN`, with its own network namespace and no host network.
- `10.79.0.0/28` was used only for DHCP feasibility, with no scan. It must be added to approved QA scope before product discovery.
- QA scope was updated before the first full controller setup or any product scan. This moved the documentation part of plan step 4 earlier to satisfy the scan-range safety requirement.
- The first full setup acquired A but could not expose loopback API through an internal Docker management bridge; it timed out at 180 seconds and removed all owned resources. A dedicated ordinary Docker management bridge fixed loopback access. DHCP remains inside the switch namespace, never on that bridge.
- Live control evidence: client1 A-to-B retained container ID, machine ID and SSH key across an independent restart; client2 had distinct MAC, machine ID and SSH key and obtained released A. Server leases showed both clients. `down` left no named containers, management network, state directory or host route change. Raw evidence is under `~/pinpoint-test-results/issue-187-dhcp/`.
