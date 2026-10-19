# Issue #265: Refresh stale NCPA plugin warning

Branch: `issue-265-refresh-ncpa-plugin-state`
Status: in-progress

## Finish condition

- [ ] Initial Enabled/Active inventory hides warning.
- [ ] Returning/remounting or focusing an open tab refreshes and clears warning after enable.
- [ ] Missing/disabled plugin shows warning, including after disable transition.
- [ ] Failed/403 inventory remains unknown with no misleading warning.
- [ ] Regression coverage for initial and transition states.
- [ ] Frontend verification and refresh specifications updated.

Requirement coverage:

| Requirement | Finish item | Proof |
|---|---|---|
| Enabled/Active initially | Initial state | Existing parameterized hook/page tests |
| Return/refocus after enable | Refresh transitions | Rendered route return and focus/visibility tests |
| Missing/disabled after disable | Reverse transition | Hook/page tests and current missing-plugin test |
| Error/missing permission | Unknown | 403/rejection tests after prior disabled state |
| Regressions | Test-first | Expected failures then focused green |
| Frontend gate/specs | Verification | scripts/verify.sh frontend; owning frontend specification |
| Investigate inventory and remount | Evidence | API client/model inventory name/status source; React route mounts deployment page anew |

## Plan

1. [x] Extend NcpaPluginNotice.test.tsx with enable/disable focus, visibility/route return, failed refresh, overlapping responses and cleanup regressions; confirm failures.
2. [x] Refresh useNcpaPluginState on focus and visible-tab events; retain unknown-on-error and discard outdated/unmounted results.
3. [ ] Update Frontend_Modules_and_Routes and Implementation_Status; run focused tests, frontend gate and all gate; review source bindings if affected.
4. [ ] Remove scaffold and open PR with verification/limits; leave CI running.

## Round log

| Round | Change | Check | Result |
|---|---|---|---|
| 0 | Read issue, API contract, router and hook | source inspection | Hook fetches only on mount; Enabled/Active mapping matches inventory contract; open tab lacks a refresh trigger |

## State for the next session

- Last check run (exact command): git status --short
- Result: clean before plan.
- Hypothesis: refresh on focus/visibility plus latest-request guard fixes stale open tabs without changing plugin/deployment behavior.
- Next action: add failing rendered transition regressions.

## Decisions and notes

No live lab mutation required by finish conditions. Tests use documented inventory responses; no fresh live-browser reproduction claimed. Preserve exact plugin name/status mapping and unknown response behavior. Do not change plugin enable/reconciliation or deployment backend. User prefers no CI wait.

Round1: initial transition tests5failed beforefocusrefresh, then40focusedpassedtwice. Deeperinventory inspection confirms scanner preserves entry.name and serializer returns Plugin.Name; check_ncpa.py is valid per backend registry. Addedname/duplicate regressions:5failed before correction. Recognize only canonical base plus backend-supported py/pl/sh, case/whitespace normalization; any Enabled/Active match wins. This addresses the issue initial-enabled condition, not an unrelated behavior expansion. Next: focused rerun and gates/specs.
