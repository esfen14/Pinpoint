# Issue #231: Move Topology after System Status in navigation

Branch: `issue-231-navigation-order`
Status: in-progress

## Finish condition

- [ ] The existing device entry is followed by System Status and then Topology for a user permitted to view all three.
- [ ] Existing route destinations and permission filtering continue to work.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Device Inventory → System Status → Topology, immediately adjacent | First item | PageAccess.test.tsx rendered link order |
| Keep device label and route destinations | Second item | PageAccess.test.tsx names and hrefs |
| Preserve permission filtering | Second item | PageAccess.test.tsx allowed/denied sidebar and guards |

## Plan

1. [ ] Add regression coverage in client/src/test/PageAccess.test.tsx; reproduce the ordering failure; reorder client/src/components/layout/Sidebar.tsx; run frontend verification.
2. [ ] Document the order in spec files/Frontend_Modules_and_Routes.md and completed gap in spec files/Implementation_Status.md; run docs and full verification; create PR and check CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue, required specs and sidebar/access sources; prepared isolated checkout | git status --short | green |

## State for the next session

- Last check run (exact command): git status --short
- Result: green before creating this plan
- Hypothesis: moving the existing Topology object after System Status satisfies both acceptance criteria without changing access mapping.
- Next action: Add the rendered-sidebar regression and run it before changing Sidebar.tsx.

## Decisions and notes

- Work in an isolated clone under the task workspace; the original checkout stays available to its owner. Its protected Git metadata prevented a worktree fetch.
- Acceptance criteria cover all issue requirements; no rename requested.
- Owning specification: Frontend Modules and Routes, Application shell and Page access rules.
- No live tests or labs authorized or needed.
