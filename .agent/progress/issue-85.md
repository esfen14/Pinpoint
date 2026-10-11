# Phase 3 — Issue #85 fix-found loop demonstration

Status: in-progress (dry-run; no merge)

Setup:
- VM cleaned; #86 documented; PR #88 draft.
- Playwright admin/restricted smoke verified (security passes; live restricted deferred).

Demonstration steps (each recorded with commands, not fabricated):
1. Queue selection: `gh issue list --label qa-found --state open` → filter skips.
2. Skip `needs-decision`; skip existing PR / branch; skip missing case ID.
3. Select highest-severity / oldest candidate (severity rubric from QA_Journeys_and_Scope.md).
4. Create branch `issue-85-fix-found-loop` (exists); open PR with `Closes #<n>`.
5. Do NOT merge. Record retest handoff when PR is merged.

Constraints observed:
- 3-PR cap per session (none open in this session for #85).
- 2-failed-fix stop documented; denied-permission stop documented.
- Human merge gate preserved (agent never merges).

Evidence will be added to `docs/test-runs/2026-10-11-fix-found-demo/` after execution.
