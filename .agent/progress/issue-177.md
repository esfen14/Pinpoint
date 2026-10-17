# Issue #177: document a future DHCP lab extension

Branch: `issue-177-dhcp-lab-proposal`
Status: in-progress

## Finish condition

- [x] Save the proposal as a versioned document in `docs/plans/`, with proposed status, owning specification links, and an issue link; review and correct stale baseline claims.
- [x] Document opt-in isolation, Docker feasibility versus VM fallback, privileges, ownership, scan approval, and cleanup without claiming validation.
- [x] Specify repeatable real DHCP same-client A-to-B and different-client A-reuse acceptance, with identity, lease, OS, discovery, Nagios, browser/history and teardown evidence; distinguish simulated observations.
- [x] Keep the test matrix, bounded waits, failure evidence and exclusions for future implementation scope.
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

1. [x] Write `docs/plans/DHCP_Lab_Extension_Proposal.md` from the issue proposal, correcting baseline details against `lab/`, `demo/demo_lab.py`, `docs/manuals/Local_Lab.md`, `docs/plans/VM_Lab_Plan.md` and identity specifications. Verify with `scripts/verify.sh docs`.
2. [x] Link the proposal from `spec files/Agent_Workflow_and_CI.md` without changing current lab claims. Review finish-condition coverage and run `scripts/verify.sh docs`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Saved and refined the future DHCP lab proposal, with relative specification links, current static lab baseline, real lease acceptance steps, deadlines and failure evidence. | `scripts/verify.sh docs` | Green: 174 relative-link documents and all docs checks passed. |
| 2 | Linked the proposal from the owning lab workflow specification and reread the unchanged issue finish condition. | `scripts/verify.sh docs`; `git diff --check` | Green: docs verification and whitespace check passed. |

## State for the next session

- Last check run (exact command): `git diff --check`
- Result (first failing lines, or "green"): green.
- Hypothesis: The draft satisfies the documentation requirements; final work is issue cross-linking, full CI-equivalent verification and PR creation.
- Next action (one specific step, not "continue"): Add the proposal link to issue #177, then run `scripts/verify.sh all`.

## Decisions and notes

- Scope is documentation only. The future extension's implementation and live completion criteria remain proposed and are not this issue's finish condition.
- The existing Docker and VM lab configurations use static target addresses. The Local Lab manual's DHCP limitation and #164 recorded evidence must remain intact.
