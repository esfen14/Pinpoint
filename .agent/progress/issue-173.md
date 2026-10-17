# Issue #173: Decide child DOWN notification guarantee with one host check attempt

Branch: `issue-173-document-parent-alert-quirk`
Status: in-progress

## Finish condition

- [x] Decide and document whether child-DOWN suppression is guaranteed for all supported retry settings or only after Nagios confirms parent reachability.
- [ ] Reproduce the one-attempt transient with an isolated real Nagios routed network; preserve a sanitized report with exact Nagios/timing/cache settings, hard states and notification events.
- [x] If a configuration change is approved, name its owning installer/application contract and preserve no-parent behavior; do not silently change Nagios main caching settings in #117.
- [ ] Add appropriate regression/acceptance coverage and operator guidance for the agreed guarantee.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Choose notification guarantee | Decision and documentation | Device Inventory §13 and data integration specification |
| Reproduce transient with exact settings and events | Isolated real routed reproduction | Outstanding; earlier #117 report is context only |
| Configuration ownership and no-parent behavior | Conditional configuration change | Option A authorizes documentation only; no configuration changes |
| Coverage and guidance | Regression/acceptance coverage and operator guidance | Notification Policy manual; acceptance coverage remains outstanding |
| Exclude inference, interface mapping and telemetry | Scope | Documentation-only diff |

## Plan

1. [x] Document the user's Option A decision in `spec files/Device_Inventory_Requirements.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Implementation_Status.md`, and `docs/manuals/Notification_Policy.md`.
2. [x] Run `scripts/verify.sh docs`, review the documentation diff, and checkpoint the scoped decision work.
3. [x] Open a draft PR recording that reproduction and acceptance coverage remain outstanding; do not close #173.
4. [ ] Complete the remaining #173 finish conditions requested by the user: add an opt-in isolated routed acceptance driver in `server/tests/e2e/parent_reachability.py`, update `server/tests/plans/MANUAL_TOPOLOGY_ACCEPTANCE.md` and the test guide, reproduce one-attempt notifications and record exact settings/states/events in a new `docs/test-runs/` report.
5. [ ] Update implementation status and issue checkboxes from observed evidence; run `scripts/verify.sh all`, remove progress scaffolding, and mark PR #192 ready after CI passes.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Recorded scoped documentation plan and user's choice | Read #173, existing routed report, specifications and Nagios host/cached-check documentation | Option A accepted; no monitoring policy/configuration change requested |

| 1 | Documented Option A contract, classification conditions, timing/cache quirk and operator guidance in four files | `scripts/verify.sh docs`; `git diff --check` | green; no code or configuration changes |

| 2 | Opened draft PR https://github.com/esfen14/Pinpoint/pull/192; kept #173 open | `gh pr create --draft`; documentation gate from round 1 | Requested documentation complete; live reproduction and acceptance coverage still outstanding |

| 3 | Added opt-in real routed acceptance driver, exact-setting procedure, test-guide routing and Option A expectations; first single-parent physical outage reproduces HARD DOWN notification then UNREACHABLE and recovery | `python3 -m py_compile server/tests/e2e/parent_reachability.py`; live driver running; full gate running | Single-parent pass observed; redundant-parent and full gate pending |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs` and `git diff --check`
- Result (first failing lines, or "green"): green; all documentation checks and whitespace validation pass
- Hypothesis: The requested documentation is complete; remaining issue finish conditions require separate live reproduction and acceptance work.
- Next action: When full #173 work is resumed, inspect the earlier isolated routed driver and plan the exact-settings one-attempt reproduction before running it.

## Decisions and notes

On 2026-10-17 the user chose Option A: allow a transient child DOWN notification before Nagios confirms parent reachability. One-attempt monitoring remains supported; the default is three attempts. No immediate suppression guarantee, fixed convergence timeout, cache change, notification delay, or retry restriction is introduced. The user requested documenting the quirk, not completing the remaining live reproduction and acceptance work; keep #173 open.

The user subsequently requested all issue finish conditions completed and the PR ready for review. Scope is expanded to the isolated real Nagios reproduction already required by #173, acceptance coverage, full verification and review readiness. No shared lab or production configuration is authorized for mutation.

Verification refinement: repeat the final driver with ordinary active host checking enabled, using forced active checks only to control ordering inside the regular 120-second interval. This avoids relying on disabled scheduling for the reproduction; the earlier controlled run remains raw evidence.

Main sync: #118 merged during verification. Merged origin/main, preserving both its NCPA notification guidance and #173 parent guidance. Stopped the obsolete full-gate process before resolving the merge; rerun all checks on the combined tree. The routed Core fixture is independent of the application-only #118 changes.
