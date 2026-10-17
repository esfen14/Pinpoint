# Issue #187: Implement isolated DHCP lab with real lease-change acceptance

Branch: `issue-187-isolated-dhcp-lab`
Status: in-progress

## Finish condition

- [ ] Docker feasibility experiment documents real DHCP, running A-to-B move, appliance connectivity, cleanup, privilege/isolation/cost and design decision.
- [ ] Opt-in controls create/manage isolated server, appliance interface and two persistent clients; capture evidence, reset and cleanly tear down owned resources.
- [ ] Safety guards enforce one allocator, binding/isolation, separate management, infrastructure outside pool, ownership, approved range; static labs still work.
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

1. [ ] Run a throwaway Docker feasibility experiment and document evidence/decision in `docs/plans/DHCP_Lab_Extension_Proposal.md` and a new `docs/test-runs/.../REPORT.md`; check routes and lab ownership first.
2. [ ] Add failing lifecycle/safety tests under `server/tests/unit/` or `lab/tests/`, then implement the isolated opt-in lab in `lab/dhcp/` and `scripts/dhcp-lab` using the chosen design.
3. [ ] Add failing bounded runner tests, then implement `lab/dhcp/acceptance.py` and a test plan under `server/tests/plans/` for the six cases and evidence collection.
4. [ ] Update `docs/qa/QA_Journeys_and_Scope.md` for the approved range, then run the live clean-lab matrix with real discovery, Nagios and browser evidence; preserve raw logs off-repository and record actual pass/fail in `docs/test-runs/`.
5. [ ] Update `docs/manuals/Local_Lab.md`, `docs/plans/VM_Lab_Plan.md` if applicable, `spec files/Agent_Workflow_and_CI.md`, `spec files/Data_Model_and_Integrations.md` if behavior changes, and `spec files/Implementation_Status.md`; run changed-stage gates.
6. [ ] Re-read issue and prove each finish item, run `scripts/verify.sh all`, remove progress, push branch and open PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

- Last check run (exact command): `docker info --format '{{.ServerVersion}}'`
- Result (first failing lines, or "green"): `29.7.2`; daemon reachable with escalation.
- Hypothesis: A dedicated host bridge/veth connected to container namespaces can provide real DHCP without Docker IPAM on the test interface, but requires root/CAP_NET_ADMIN.
- Next action (one specific step, not "continue"): Check route collisions and exclusive lab ownership, then run the throwaway DHCP experiment.

## Decisions and notes

- Issue finish condition covers all stated implementation requirements and phase-one exclusions.
- No product discovery changes are planned unless the live run exposes a defect; such a defect requires a separate issue under this workflow.
