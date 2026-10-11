# Issue #85: Add a fix-found loop that fixes QA-found issues and returns cases to retest

Branch: `issue-85-fix-found-loop`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

- [ ] `fix-found.md` and both adapters exist and `work-issue.md` and `Agent_Workflow_and_CI.md` do not contradict them
- [ ] The queue selection and skip rules (scope 2) are written as checkable steps, with the exact `gh` commands
- [ ] A dry run on a deliberately planted `qa-found` issue: the loop opens one PR with `Closes #<n>`, does not merge, and skips an issue labelled `needs-decision` and an issue that already has an open PR; recorded in `docs/test-runs/`
- [ ] The retest handoff is shown once: the traceability row of the planted case becomes `retest` after its issue closes
- [ ] The 3-PR cap, the 2-failed-fix stop and the denied-permission stop are each demonstrated or covered by a written check
- [ ] `scripts/verify.sh docs` passes

## Plan

1. [ ] Create `.agent/workflows/fix-found.md`, `.claude/skills/fix-found/SKILL.md`, `.opencode/commands/fix-found.md` (thin adapters, mirroring `work-issue`).
2. [ ] Extend `scripts/check_agent_progress.py` to handle the new workflow name/pattern, verify with tests.
3. [ ] Harmonize rules in `Agent_Workflow_and_CI.md`: resolve contradictions regarding lab use, PR caps, and merge gates.
4. [ ] Implement dry run: setup a planted `qa-found` issue with a deliberate local failure, verify queue selection logic (`skip` rules on `needs-decision` etc.).
5. [ ] Perform and record the dry run in `docs/test-runs/` and verify the retest handoff mechanism.
6. [ ] Implement/verify stop/cap rules (Demonstrate 3-PR cap and 2-failed-fix stop).
7. [ ] Verification & PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Initialized progress | N/A | Initialized |

## State for the next session

- Last check run (exact command): `scripts/check_agent_progress.py`
- Result (first failing lines, or "green"): green
- Hypothesis: Progress file established, ready to implement Step 1 (create fix-found workflow).
- Next action (one specific step, not "continue"): Create `.agent/workflows/fix-found.md` and adapters.
