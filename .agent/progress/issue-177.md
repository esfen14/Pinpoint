# Issue #177: document a future DHCP lab extension

Branch: `issue-177-dhcp-lab-proposal`
Status: in-progress

## Finish condition

- [ ] Save the proposal as a versioned document in `docs/plans/`, with proposed status, owning specification links, and an issue link; review and correct stale baseline claims.
- [ ] Document opt-in isolation, Docker feasibility versus VM fallback, privileges, ownership, scan approval, and cleanup without claiming validation.
- [ ] Specify repeatable real DHCP same-client A-to-B and different-client A-reuse acceptance, with identity, lease, OS, discovery, Nagios, browser/history and teardown evidence; distinguish simulated observations.
- [ ] Keep the test matrix, bounded waits, failure evidence and exclusions for future implementation scope.
- [ ] Run `scripts/verify.sh docs`; leave lab, #164 evidence and product behavior unchanged.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Versioned proposal, status, source links, current baseline | 1 | Review `docs/plans/DHCP_Lab_Extension_Proposal.md` against lab Compose, target entrypoint, VM script and manuals; `scripts/verify.sh docs` |
| Isolated opt-in topology, Docker/VM decision, privilege/ownership/scan/cleanup constraints | 2 | Review proposal sections on topology, feasibility and lifecycle; `scripts/verify.sh docs` |
| Real DHCP same running client and later IP reuse with complete evidence, no simulated acceptance | 3 | Review acceptance procedure and evidence table; `scripts/verify.sh docs` |
| Test matrix, timeouts, failure evidence, future exclusions and implementation stages | 4 | Review proposal matrix and stages; `scripts/verify.sh docs` |
| No lab/product changes, no new coverage claim, #164 results intact | 5 | `git diff --name-only origin/main...HEAD`; `scripts/verify.sh docs` |

## Plan

1. [ ] Write `docs/plans/DHCP_Lab_Extension_Proposal.md` from the issue proposal, correcting baseline details against `lab/`, `demo/demo_lab.py`, `docs/manuals/Local_Lab.md`, `docs/plans/VM_Lab_Plan.md` and identity specifications. Verify with `scripts/verify.sh docs`.
2. [ ] Link the proposal from `spec files/Agent_Workflow_and_CI.md` without changing current lab claims. Review finish-condition coverage and run `scripts/verify.sh docs` and `scripts/verify.sh all`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

- Last check run (exact command): `git branch -a --list '*issue-177-*'`
- Result (first failing lines, or "green"): green; new issue branch created from `origin/main`.
- Hypothesis: The proposal can be recorded as a plan without changing lab or product behavior.
- Next action (one specific step, not "continue"): Write `docs/plans/DHCP_Lab_Extension_Proposal.md` and run `scripts/verify.sh docs`.

## Decisions and notes

- Scope is documentation only. The future extension's implementation and live completion criteria remain proposed and are not this issue's finish condition.
- The existing Docker and VM lab configurations use static target addresses. The Local Lab manual's DHCP limitation and #164 recorded evidence must remain intact.
