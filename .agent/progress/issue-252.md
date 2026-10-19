# Issue #252: Remove unsupported Plugin Manager summary cards

Branch: `issue-252-plugin-summary`
Status: in-progress

## Finish condition

- [ ] Remove Custom Plugins and Updates Available cards from PluginsPage.tsx.
- [ ] Use three columns and verify the summary row at mobile and desktop widths.
- [ ] Remove unused Puzzle and RefreshCcw imports.
- [ ] Drop custom_plugins and updates_available from client PluginSummary; document retained backend fields as unused.
- [ ] Frontend regression checks all three remaining cards and absence of both removed cards.
- [ ] Update frontend/backend specs and Implementation_Status Custom plugins row.
- [ ] scripts/verify.sh all passes (record platform limitations and Linux CI results).

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Remove unsupported cards and imports | 1, 3, 5 | PluginsPage.test.tsx and source review |
| Responsive three-card row | 2 | computed layout and screenshots at mobile/desktop summary widths |
| Client type and retained backend contract | 4 | TypeScript build; backend summary source and spec |
| Documentation | 6 | docs gate and diff |
| Full verification | 7 | verify.sh all and Linux CI |
| Disabled upload button and model enum removal excluded | Deliberately out of scope | diff review confirms unchanged |

## Plan

1. [ ] Add regression in client/src/test/PluginsPage.test.tsx, confirm failure, remove cards/imports and change grid in client/src/pages/PluginsPage.tsx; remove unused client summary fields in client/src/types/plugin.ts; run focused tests and visual row checks.
2. [ ] Update spec files/Frontend_Modules_and_Routes.md, spec files/Backend_Modules_and_Routes.md and spec files/Implementation_Status.md; run frontend/docs/full verification; publish PR and inspect CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue and affected specs/source; prepared plan | git status --short | green before plan |

## State for the next session

- Last check run (exact command): git status --short
- Result: green before plan.
- Hypothesis: remove the two cards and client fields; preserve backend response for compatibility and document it.
- Next action: Add and run the remaining/removed summary card regression before implementation.

## Decisions and notes

- No backend implementation changes, new dependencies, migrations or live lab access needed.
- Add Custom Plugin controls and PluginType/PluginStatus remain outside scope.
- The existing macOS full gate has known unrelated canonical /tmp lock and GNU sed incompatibilities; report them honestly and rely on supported Linux CI for final validation.
- Reuse this chat's isolated checkout; #231 changes remain on their own branch.
