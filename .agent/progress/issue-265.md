# Issue #265: Refresh stale NCPA plugin warning

Branch: `issue-265-refresh-ncpa-plugin-state`
Status: in-progress

## Finish condition

- [x] Initial Enabled/Active inventory hides warning.
- [x] Returning/remounting or focusing an open tab refreshes and clears warning after enable.
- [x] Missing/disabled plugin shows warning, including after disable transition.
- [x] Failed/403 inventory remains unknown with no misleading warning.
- [x] Regression coverage for initial and transition states.
- [x] Frontend verification and refresh specifications updated.

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

- Last check run (exact command): TMPDIR=/private/tmp scripts/verify.sh frontend
- Result: green; 82 test files, 1063 tests passed; build passed; lint 0 errors, 33 existing warnings.
- Hypothesis: focus/visibility refresh and backend-aligned filename recognition address both stale warning causes.
- Next action: finish all-stage verification, then open PR without waiting for CI.

## Decisions and notes

No live lab mutation required by finish conditions. Tests use documented inventory responses; no fresh live-browser reproduction claimed. Preserve Enabled/Active semantics and align filename identity with the backend registry and unknown response behavior. Do not change plugin enable/reconciliation or deployment backend. User prefers no CI wait.

Round1: initial transition tests5failed beforefocusrefresh, then40focusedpassedtwice. Deeperinventory inspection confirms scanner preserves entry.name and serializer returns Plugin.Name; check_ncpa.py is valid per backend registry. Addedname/duplicate regressions:5failed before correction. Recognize only canonical base plus backend-supported py/pl/sh, case/whitespace normalization; any Enabled/Active match wins. This addresses the issue initial-enabled condition, not an unrelated behavior expansion. Next: focused rerun and gates/specs.

Round 2: focused regression suite 46 passed; full frontend stage passed (1063 tests, build, lint). Documentation links and 239 coverage records validate. All-stage gate running.
