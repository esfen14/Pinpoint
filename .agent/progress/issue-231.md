# Issue #231: Move Topology after System Status in navigation

Branch: `issue-231-navigation-order`
Status: in-progress

## Finish condition

- [x] The existing device entry is followed by System Status and then Topology for a user permitted to view all three.
- [x] Existing route destinations and permission filtering continue to work.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Device Inventory → System Status → Topology, immediately adjacent | First item | PageAccess.test.tsx rendered link order |
| Keep device label and route destinations | Second item | PageAccess.test.tsx names and hrefs |
| Preserve permission filtering | Second item | PageAccess.test.tsx allowed/denied sidebar and guards |

## Plan

1. [x] Add regression coverage in client/src/test/PageAccess.test.tsx; reproduce the ordering failure; reorder client/src/components/layout/Sidebar.tsx; run frontend verification.
2. [ ] Review Sidebar dependency assertions and refresh docs/qa/automation-coverage.json with review in docs/qa/Automation_Readiness.md; document the order in spec files/Frontend_Modules_and_Routes.md and completed gap in spec files/Implementation_Status.md; run docs and full verification; create PR and check CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added order/destination/permission regressions; reordered Sidebar.tsx | PageAccess.test.tsx: red before fix, 25 green after; TMPDIR=$PWD/../test-tmp scripts/verify.sh frontend | green: 1026 tests, build, lint (existing warnings) |
| 2 | Updated navigation specs; reviewed eight unchanged permission adapters and refreshed Sidebar dependency hashes | TMPDIR=$PWD/../test-tmp scripts/verify.sh docs | coverage validates; unrelated supervisor tests reject macOS /tmp canonical lock path |
| 0 | Read issue, required specs and sidebar/access sources; prepared isolated checkout | git status --short | green |

## State for the next session

- Last check run (exact command): TMPDIR=/Users/karell/Documents/Codex/2026-10-19/s/work/test-tmp scripts/verify.sh docs
- Result: fails in test_qa_supervisor.py: ValueError: Host controller unavailable, already owned or unsafe. qa_control.canonical_root uses /tmp, a symlink to /private/tmp on macOS, and claim rejects noncanonical paths. Coverage source validation passed.
- Hypothesis: Linux CI will pass the unchanged supervisor checks; altering their host safety rules is outside this issue.
- Next action: Finish the running verify.sh all attempt and standalone backend suite, then open a draft PR with the local platform limitation and inspect Linux CI.

## Decisions and notes

- Work in an isolated clone under the task workspace; the original checkout stays available to its owner. Its protected Git metadata prevented a worktree fetch.
- Acceptance criteria cover all issue requirements; no rename requested.
- Owning specification: Frontend Modules and Routes, Application shell and Page access rules.
- No live tests or labs authorized or needed.

- Initial frontend gate rejected macOS noncanonical temporary paths; canonical task-local TMPDIR resolves it without code/test changes.

- Docs gate caught Sidebar.tsx fingerprints in eight QA mappings. Reviewed affected written cases and assertions; only the dependency hash changes. This is necessary source-binding maintenance for the sidebar reorder, not new QA coverage or execution.

- origin/main advanced with QA catalog consolidation (#241); merged it, preserving both sidebar-review and catalog-review sections in Automation_Readiness.md. QA source fingerprints and incoming catalog fingerprints are both retained.
