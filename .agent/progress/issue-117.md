# Issue #117: Manual multiple-parent topology

Branch: `issue-117-manual-topology`
Status: in-progress

## Finish condition

#### E. Acceptance Criteria

- [x] **Part 4.1 (System):** Setting one or multiple parents makes the generated host definition contain the corresponding Nagios `parents` list, and Nagios validates it.
- [x] **Part 4.1 (System):** A self-parent, a cycle through any parent path, duplicate IDs, or a missing, retired or merged parent is refused with 400; the previous parent set remains intact.
- [x] **Part 4.1 (System):** Retiring or merging a parent leaves no dangling reference and the config still validates.
- [x] **Part 4.1 (System):** Ineligible parents are individually omitted and reported; eligible parents remain in the generated list. A host with no eligible parents gets valid config without `parents`.
- [x] **Part 4.1 (System):** On a lab network, demonstrate Nagios reachability for both a single parent and redundant parents: a failed intermediate parent makes dependent children UNREACHABLE when no alternate route remains; loss of one parent with an available alternate route does not incorrectly mark a reachable child UNREACHABLE. Record observed host states and DOWN/UNREACHABLE notification behavior.
- [x] **Part 4.1 (System):** Hosts without a parent behave exactly as before.
- [x] **Part 4.2 (Web-Interface):** A user with `system.hosts.edit` can set, change and clear multiple parents from both Inventory and Topology, and the complete parent set persists after reload.
- [x] **Part 4.2 (Web-Interface):** Cycle and invalid choices show the server message.
- [x] **Part 4.2 (Web-Interface):** A user without the permission sees the parents in both Inventory and Topology but cannot change them.
- [x] **Part 4.2 (Web-Interface):** Existing drawer and table tests pass unchanged.

- [x] **Topology:** The supported routed page displays real backend devices and configured parent edges, including all Device Inventory devices, paused devices and devices without parents.
- [x] **Topology:** Automatic hierarchy handles shared children with multiple parents; node dragging and layout modification are disabled.
- [x] **Topology:** Loading, error, empty and permission states are tested; hardcoded sample nodes and edges are removed from the supported page.
- [x] **Topology:** Matching specifications and tests recognize topology as supported, superseding the former release exclusion.
- [x] **Topology:** Detail panels use real device data and manual parent relationships only; tests verify sample interface details, interface navigation, and placeholder traffic/utilization charts are absent from the supported topology page.

#### F. Required Deliverables

- [x] Updated application source code (paths in section C).
- [x] New or updated API endpoints, with route docstrings and permission checks.
- [x] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [x] Updated frontend components, types and routes (paths in section C).
- [x] Unit tests for new or modified logic.
- [x] Frontend interaction tests under `client/src/test/`.
- [x] Integration or regression tests for the workflows in section G.
- [x] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Device_Inventory_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`, and the topology boundary in `spec files/System_Overview_and_Architecture.md`.
- [x] Updated user-facing documentation: Drawer help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 4.1 (System):** Unit: multiple-parent cycle detection, duplicate IDs, atomic parent-set updates, merge and retire re-pointing/deduplication, template output with zero/one/multiple parents, mixed eligible/ineligible parents, paused-parent handling.
- **Part 4.1 (System):** API: permission and 400 paths for the extended device route.
- **Part 4.1 (System):** Migration up and down.
- **Part 4.1 (System):** Lab (record in `docs/test-runs/`): single-parent gateway with two children, plus a child with redundant parents and verified alternate routes; exercise parent failures and record reachability and notification behavior.
- **Part 4.1 (System):** Regression: `test_device_identity.py`, `test_device_identity_routes.py`, `test_create_host_cfg.py`.
- **Part 4.2 (Web-Interface):** Frontend: set, change, clear, error and read-only states on both pages; topology backend wiring, all inventory devices, automatic multiple-parent hierarchy and disabled layout modification.
- **Part 4.2 (Web-Interface):** Regression: Device Inventory tests listed above.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

**A pull request addressing this issue must not be merged until all applicable conditions below are fulfilled.**

#### Functional Completion

- [ ] All mandatory acceptance criteria are satisfied.
- [x] Required functionality works as specified.
- [x] Existing behavior has not been unintentionally broken.
- [x] Applicable edge cases are handled.

#### Code Quality

- [x] Code follows PinPoint's existing architectural patterns and conventions.
- [x] No unnecessary duplicate functionality is introduced.
- [x] Relevant linting and static analysis checks pass.
- [ ] No unresolved critical defects remain.

#### Testing

- [x] Required automated tests are added or updated.
- [x] All applicable automated tests pass.
- [x] Relevant integration and regression tests pass.
- [ ] Test results or verification evidence are attached to the pull request.

#### Security and Reliability

- [x] User inputs and configuration values are validated.
- [x] Authorization is enforced where required.
- [x] Sensitive data is handled securely.
- [x] Errors are handled without introducing uncontrolled failures.
- [x] Relevant performance and reliability requirements are satisfied.

#### Documentation

- [x] Relevant technical documentation is updated.
- [x] User documentation is updated for user-facing changes.
- [x] New configuration parameters are documented.
- [x] Deployment or migration steps are documented where applicable.

#### Pull Request Review

- [ ] The pull request references the corresponding issue number.
- [ ] The pull request describes the implementation and testing performed.
- [ ] Required CI checks pass.
- [ ] All required reviewer approvals are obtained.
- [ ] Blocking review comments are resolved.
- [ ] All applicable acceptance criteria and required deliverables are complete.

Do not mark this issue as completed solely because code has been written. Test results, reviewer approvals and deployment verification must be backed by evidence attached to the pull request and must not be claimed without it.




Requirement coverage (all issue sections):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| A/B: remove flat reachability; reuse inventory and prototype | E parent rendering/topology; F source | device-parent tests, topology interaction tests, source inspection |
| Scope: manual zero/one/multiple parents, DAG, all inventory devices | E topology/set/change/clear/validation | API tests and topology tests |
| Scope: both editors and existing permissions | E edit/read-only; F endpoint/types | API authorization and frontend interaction tests |
| Scope: automatic hierarchy, no layout edits | E hierarchy | layout tests and React Flow prop assertions |
| Scope: device-only panels, no telemetry/map inference/layout persistence | E detail panels; explicit exclusions | frontend tests and source inspection |
| C backend 1/2/3: relationship table, validation, atomic edits, parent summaries | E validation/persistence; F migration/API | parent API tests, populated multi-bind migration up/down |
| C backend 4/6: eligibility, omission feedback, safe Nagios apply/rollback | E config handling; H security | generation and real writer rollback regression tests; injection review |
| C backend 5: merge/retire rewiring, deduplicate, prevent cycles | E lifecycle | merge/retire API tests |
| C frontend 1–7: search, clear, advisory gateway, errors, permissions, topology | E frontend/topology; F help/types | frontend interaction tests |
| D: defaults, envelopes/docstrings, secret safety, bounded work, no new dependencies | E regression; H architecture/security | focused regression tests, source/security review, scripts/verify.sh all |
| E/F/G: real Nagios reachability and notifications, evidence | E lab; F report; H evidence | isolated lab report with observed single/redundant-parent behavior |
| H: quality, tests, docs, migration/deployment notes, CI | H corresponding checkboxes | scripts/verify.sh all, PR CI and linked evidence |
| H: reviewer approvals and merge | H review | human review required; agent never merges or claims approvals |

## Plan

1. [x] Add failing backend parent/API/config/lifecycle tests in `server/tests/unit/test_device_parents.py`; implement relationship model, validation/serialization in existing device modules, rendering and atomic apply; document routes/data contract; run focused regressions and backend gate.
2. [x] Generate/review multi-bind migration in `server/migrations/versions/`; add populated round-trip test/runner in `server/tests/`; verify upgrade/downgrade and backend gate.
3. [x] Add failing frontend editor/layout/topology tests under `client/src/test/`; implement shared parent editor/API/types, wire Inventory and existing React Flow prototype, routing/navigation/access, automatic hierarchy and device-only panels; update frontend/domain specs; verify frontend gate.
4. [x] Record isolated live Nagios reachability/rollback evidence in `docs/test-runs/` using the template; update remaining specifications and local issue mirror; run docs/all verification and checkpoint.
5. [x] Re-read issue and prove acceptance; publish PR using `.github/pull_request_template.md`, monitor CI; keep draft/progress if live acceptance or human decisions remain outstanding.

6. [ ] Owner-requested continued testing: run browser against real backend/Nagios; fix any in-scope interaction issue with a failing regression, record a new report and verify frontend/docs/CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Backend graph/model/API/rendering and generated migration; baseline tests fail as expected before implementation. Fixed an authorization test that reused the authenticated client fixture; 308 focused regressions and then 34 parent/migration proofs pass. | FLASK_DEBUG=1 .venv/bin/python -m pytest tests/unit/test_device_parents.py tests/unit/test_device_parent_migration.py -q | 34 passed; first full backend gate still running and contains the already-fixed test fixture failure |
| 2 | Added generated/reviewed migration and populated round trip; shared frontend editor, hierarchy, real-data topology, route/access wiring and specs; protected unsaved drafts during refresh | scripts/verify.sh frontend; scripts/verify.sh docs; focused parent proof | Frontend green (30 warnings, no errors); docs green; 35 latest parent tests pass. Stable full backend gate finishing. |
| 3 | Full verification green; added real-writer deferred-commit compensation proof; browser fixture smoke verified real React Flow, fixed positions, editor and read-only; corrected applied/unchanged response flags | scripts/verify.sh all; parent/migration focus; browser fixture script | Green gates and 38 focused tests. Routed trials verify final reachability but max-attempts=1 can emit transient child DOWN; default 3-attempt trial pending. |
| 4 | Real routed default-three-attempt HARD-state checks and notification dispatch passed; published sanitized report and documented separate one-attempt caveat in #173; reread unchanged issue | python3 /tmp/issue117-live.py; scripts/verify.sh docs; gh issue view 117 --json body,comments | Default-retry single/redundant paths, pause/merge/retire pass; 14 notification events, zero child DOWN in final trial. Docs green. |
| 5 | Final review caught oversized positive IDs returning 500 from SQLite; added failing regression, bounded IDs to SQLite integer range and proved 400. Stable full gate passed; draft PR #174 published. | final all-stage gate; focused parent/migration proof; PR checks | Local gates green; final pushed-tree CI to be observed after checkpoint. Human review and #173 guarantee remain outstanding. |
| intake | Reviewed issue scope and existing React Flow frontend; created isolated checkout | gh issue view 117 --json body,comments,title | Product decisions recorded; no implementation yet |

## State for the next session

- Last check run (exact command): cd server && FLASK_DEBUG=1 .venv/bin/python -m pytest tests/unit/test_device_parents.py tests/unit/test_device_parent_migration.py -q
- Result: Final focused parent/migration proof green at /tmp/issue117-last-parent-proof.log (39 passed). Full stable-tree gate /tmp/issue117-final-all.log passed 3040 backend / 14 skips and 653 frontend tests before the final oversized-ID guard. That guard was first proven red (500 from SQLite overflow) then fixed to return 400. Final pushed-tree CI is the remaining automated gate.
- Hypothesis: Existing writer and Inventory modules can support this without a new dependency; use a relationship table and shared editor.
- Next action: Record real-browser evidence from /tmp/issue117-live-e0853d16, verify the changed frontend/docs, and watch CI for the drawer fix.

## Decisions and notes

- User explicitly authorized implementation after resolving scope, including relationship migration, sensitive Nagios rendering and scoped lab tests described by the issue. No additional permission is inferred for unrelated labs or deployments.
- Security review required for parent rendering: only stable validated Nagios identifiers may enter generated config; retain shared writer pre-apply validation/resource rollback. Parent IDs are positive distinct integers; graph traversals are iterative and bounded by loaded rows.
- Existing topology is a disconnected static React Flow prototype; retain canvas/node/edge selection structure, remove fake telemetry, do frontend layout only. Keep System Status separate.
- No new permissions or dependency planned. View uses `system.network_health` as Inventory does; parent write uses `system.hosts.edit`. Gateway suggestions remain advisory.
- The issue asks existing drawer/table regressions to pass unchanged; route tests excluding topology must change because the owner explicitly reversed that scope.

- Migration generation: used private databases upgraded to a129f6d23901, flask_migrate.migrate with rev_id b117d9a2c041 (multi-bind environment). Reviewed generated operations: default-bind table/index/FKs/self-check only, no history changes.
- Shared writer inspection found a legacy history commit inside successful apply; added opt-in deferred commit for parent transactions while preserving the existing default for all other callers. Lifecycle parent edits reuse sync_rows/desired_services/set_plugin_states without committing early.

- Round 1 full gate completed: 3022 passed, 14 skipped, 3 failed. One was the corrected shared-client auth fixture; two were a migration-head collection race because generation happened during the gate (old HEAD constant versus new runner head). No production behavior or tests were weakened; rerunning from a stable tree.
- Round 2: frontend first failed on missing editor/layout modules, then 82 focused tests passed. A malformed response guard allows unchanged drawer mocks to show a parent loading error rather than crash. Added a draft-preservation regression and minute-based shared refresh. Frontend gate passed once with only known lint/build warnings; revised code gate pending. Docs gate passed after matching the route-catalog parser's exact component-name cell.

- Source security review: all parent names use full-match whitelist before directive rendering; request IDs never reach commands; no secrets added to API/data; existing Nagios and resource rollback retained. Graph validation/layout are iterative, no new application dependencies. Added compensating regeneration after rollback if audit/commit fails following an applied parent edit.

- Live evidence: disposable Docker containers/networks only, all owned and cleaned after each trial; no existing lab/VM touched. First setups needed a stock service definition and a same-user Nagios validator; root-run temporary config was unreadable after Nagios privilege drop. Accelerated max-attempts=1 trials showed transient child DOWN before UNREACHABLE. Nagios official docs discuss cached reachability and recommend max_check_attempts >1. The current trial uses Pinpoint's default 3 attempts and waits for HARD states with nonzero last_check before evaluating notifications. Preserve these limitations in the report; do not claim universal child-DOWN suppression.
- After the full gate began, minor apply-status reporting and fit-on-panel-open fixes were made; current parent/migration focused proof and browser smoke pass. CI must verify the final source tree. No tests were weakened; topology-exclusion route tests changed only to reflect the approved scope reversal.

- Final live evidence: /tmp/issue117-live-a2ab65f9 and /tmp/issue117-live-active-checks.log, source 051abed5. Active physical checks were scheduled through Nagios FIFO and HARD/nonzero-check states required. See committed report for fixture/setup deviations and SMTP/browser limitations.
- Finish re-read: issue body unchanged, no comments. All E acceptance behavior has unit/frontend/live proof as mapped above. Human review/approvals and final CI remain unchecked; no merge will be attempted.

- PR: https://github.com/esfen14/Pinpoint/pull/174 (draft). Progress is intentionally retained because human review/approval and the separate #173 notification-guarantee decision are not agent-proven. Implementation steps and default-retry acceptance are complete; no required reviewer approval or universal single-attempt suppression is claimed. Session has reached five recorded rounds; no further speculative implementation in this session.
- Final full run before the one-line oversized-ID guard: /tmp/issue117-final-all.log. The added guard had a red regression (1 failed / 7 passed invalid-ID cases), then the complete focused parent/migration proof passed. CI must verify the final source. No source migration or dependency changed during that full run.

- Owner explicitly requested continued testing after the prior handoff, then resumed after an interruption. The prior final source 519a00a passed all CI jobs: https://github.com/esfen14/Pinpoint/actions/runs/38713297084 .
- Continued round 1: real browser/backend run reproduced an Inventory success-message loss. The parent callback unnecessarily set the host-detail reload key, unmounting the parent editor. A new focused integration regression (`DeviceParentDrawer.test.tsx`) failed first; changed callback to refresh the table only, preserving the editor and confirmation. 43 focused frontend tests then passed, with existing drawer/Inventory tests unchanged.
- Current actual-browser evidence: /tmp/issue117-live-e0853d16/browser.log and /tmp/issue117-real-browser-run3.log. Real standard login, real Flask APIs and real Nagios validation/reload; no API interception. Both editor placements set/clear/reload, cross-page edges and persistence, cycle rejection/draft retention, restricted controls/direct 403 and zero page errors passed. Initial setup needed a dedicated management bridge to publish the loopback HTTP listener; all owned containers/networks cleaned up. No shared appliance/targets were touched.
