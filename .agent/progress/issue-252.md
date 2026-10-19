# Issue #252: Remove unsupported Plugin Manager summary cards

Branch: `issue-252-plugin-summary`
Status: in-progress

## Finish condition

- [x] Remove Custom Plugins and Updates Available cards from PluginsPage.tsx.
- [x] Use three columns and verify the summary row at mobile and desktop widths.
- [x] Remove unused Puzzle and RefreshCcw imports.
- [x] Drop custom_plugins and updates_available from client PluginSummary; document retained backend fields as unused.
- [x] Frontend regression checks all three remaining cards and absence of both removed cards.
- [x] Update frontend/backend specs and Implementation_Status Custom plugins row.
- [ ] scripts/verify.sh all passes (record platform limitations and Linux CI results).

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Remove unsupported cards and imports | 1, 3, 5 | PluginsPage.test.tsx and source review |
| Responsive three-card row | 2 | isolated rendered browser preview at mobile/desktop summary widths |
| Client type and retained backend contract | 4 | TypeScript build; backend summary source and spec |
| Documentation | 6 | docs gate and diff |
| Full verification | 7 | verify.sh all and Linux CI |
| Disabled upload button and model enum removal excluded | Deliberately out of scope | diff review confirms unchanged |

## Plan

1. [x] Add regression in client/src/test/PluginsPage.test.tsx, confirm failure, remove cards/imports and change grid in client/src/pages/PluginsPage.tsx; remove unused client summary fields in client/src/types/plugin.ts; run focused tests and visual row checks.
2. [ ] Update spec files/Frontend_Modules_and_Routes.md, spec files/Backend_Modules_and_Routes.md and spec files/Implementation_Status.md; run frontend/docs/full verification; publish PR and inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Removed cards/imports/client fields; updated specs; isolated browser preview at 390/1000 px | PluginsPage.test.tsx red before fix, 15 green after; verify.sh frontend | green: 1027 tests, build, lint (existing warnings) |
| resumed | Recovered interrupted work and removed temporary preview files | git diff --check | green |
| 2 | Docs updated; full gate attempted; merged latest main without conflict | verify.sh all | existing macOS host-lock supervisor failure in docs; Linux CI required |
| 0 | Read issue and affected specs/source; prepared plan | git status --short | green before plan |

## State for the next session

- Last check run (exact command): TMPDIR=/Users/karell/Documents/Codex/2026-10-19/s/work/test-tmp scripts/verify.sh all
- Result: docs fails in unchanged test_qa_supervisor.py because canonical_root uses /tmp (symlink on macOS): ValueError: Host controller unavailable, already owned or unsafe. Frontend gate previously passed.
- Hypothesis: supported Linux CI will validate all stages, as on issue #231. No backend implementation changed.
- Next action: Publish PR and inspect all Linux CI jobs; report local platform limitation honestly.

## Decisions and notes

- No backend implementation changes, new dependencies, migrations or live lab access needed.
- Add Custom Plugin controls and PluginType/PluginStatus remain outside scope.
- The existing macOS full gate has known unrelated canonical /tmp lock and GNU sed incompatibilities; report them honestly and rely on supported Linux CI for final validation.
- Reuse this chat's isolated checkout; #231 changes remain on their own branch.

- Merged latest origin/main before publishing; unrelated incoming resource-card and catalog changes are retained.
