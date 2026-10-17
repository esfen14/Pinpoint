# Issue #173: Decide child DOWN notification guarantee with one host check attempt

Branch: `issue-173-document-parent-alert-quirk`
Status: in-progress

## Finish condition

- [ ] Decide and document whether child-DOWN suppression is guaranteed for all supported retry settings or only after Nagios confirms parent reachability.
- [ ] Reproduce the one-attempt transient with an isolated real Nagios routed network; preserve a sanitized report with exact Nagios/timing/cache settings, hard states and notification events.
- [ ] If a configuration change is approved, name its owning installer/application contract and preserve no-parent behavior; do not silently change Nagios main caching settings in #117.
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

1. [ ] Document the user's Option A decision in `spec files/Device_Inventory_Requirements.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Implementation_Status.md`, and `docs/manuals/Notification_Policy.md`.
2. [ ] Run `scripts/verify.sh docs`, review the documentation diff, and checkpoint the scoped decision work.
3. [ ] Open a draft PR recording that reproduction and acceptance coverage remain outstanding; do not close #173.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Recorded scoped documentation plan and user's choice | Read #173, existing routed report, specifications and Nagios host/cached-check documentation | Option A accepted; no monitoring policy/configuration change requested |

## State for the next session

- Last check run (exact command): `git status --short`
- Result (first failing lines, or "green"): green; clean starting checkout
- Hypothesis: Existing engine behavior needs an explicit documented guarantee and operator guidance.
- Next action: Update the four documentation files named in plan step 1.

## Decisions and notes

On 2026-10-17 the user chose Option A: allow a transient child DOWN notification before Nagios confirms parent reachability. One-attempt monitoring remains supported; the default is three attempts. No immediate suppression guarantee, fixed convergence timeout, cache change, notification delay, or retry restriction is introduced. The user requested documenting the quirk, not completing the remaining live reproduction and acceptance work; keep #173 open.
