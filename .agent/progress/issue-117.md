# Issue #117: Manual multiple-parent topology

Branch: `issue-117-manual-topology`
Status: in-progress

## Finish condition

#### E. Acceptance Criteria

- [ ] **Part 4.1 (System):** Setting one or multiple parents makes the generated host definition contain the corresponding Nagios `parents` list, and Nagios validates it.
- [ ] **Part 4.1 (System):** A self-parent, a cycle through any parent path, duplicate IDs, or a missing, retired or merged parent is refused with 400; the previous parent set remains intact.
- [ ] **Part 4.1 (System):** Retiring or merging a parent leaves no dangling reference and the config still validates.
- [ ] **Part 4.1 (System):** Ineligible parents are individually omitted and reported; eligible parents remain in the generated list. A host with no eligible parents gets valid config without `parents`.
- [ ] **Part 4.1 (System):** On a lab network, demonstrate Nagios reachability for both a single parent and redundant parents: a failed intermediate parent makes dependent children UNREACHABLE when no alternate route remains; loss of one parent with an available alternate route does not incorrectly mark a reachable child UNREACHABLE. Record observed host states and DOWN/UNREACHABLE notification behavior.
- [ ] **Part 4.1 (System):** Hosts without a parent behave exactly as before.
- [ ] **Part 4.2 (Web-Interface):** A user with `system.hosts.edit` can set, change and clear multiple parents from both Inventory and Topology, and the complete parent set persists after reload.
- [ ] **Part 4.2 (Web-Interface):** Cycle and invalid choices show the server message.
- [ ] **Part 4.2 (Web-Interface):** A user without the permission sees the parents in both Inventory and Topology but cannot change them.
- [ ] **Part 4.2 (Web-Interface):** Existing drawer and table tests pass unchanged.

- [ ] **Topology:** The supported routed page displays real backend devices and configured parent edges, including all Device Inventory devices, paused devices and devices without parents.
- [ ] **Topology:** Automatic hierarchy handles shared children with multiple parents; node dragging and layout modification are disabled.
- [ ] **Topology:** Loading, error, empty and permission states are tested; hardcoded sample nodes and edges are removed from the supported page.
- [ ] **Topology:** Matching specifications and tests recognize topology as supported, superseding the former release exclusion.
- [ ] **Topology:** Detail panels use real device data and manual parent relationships only; tests verify sample interface details, interface navigation, and placeholder traffic/utilization charts are absent from the supported topology page.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Device_Inventory_Requirements.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`, and the topology boundary in `spec files/System_Overview_and_Architecture.md`.
- [ ] Updated user-facing documentation: Drawer help text.
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
- [ ] Required functionality works as specified.
- [ ] Existing behavior has not been unintentionally broken.
- [ ] Applicable edge cases are handled.

#### Code Quality

- [ ] Code follows PinPoint's existing architectural patterns and conventions.
- [ ] No unnecessary duplicate functionality is introduced.
- [ ] Relevant linting and static analysis checks pass.
- [ ] No unresolved critical defects remain.

#### Testing

- [ ] Required automated tests are added or updated.
- [ ] All applicable automated tests pass.
- [ ] Relevant integration and regression tests pass.
- [ ] Test results or verification evidence are attached to the pull request.

#### Security and Reliability

- [ ] User inputs and configuration values are validated.
- [ ] Authorization is enforced where required.
- [ ] Sensitive data is handled securely.
- [ ] Errors are handled without introducing uncontrolled failures.
- [ ] Relevant performance and reliability requirements are satisfied.

#### Documentation

- [ ] Relevant technical documentation is updated.
- [ ] User documentation is updated for user-facing changes.
- [ ] New configuration parameters are documented.
- [ ] Deployment or migration steps are documented where applicable.

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

1. [ ] Add failing backend parent/API/config/lifecycle tests in `server/tests/unit/test_device_parents.py`; implement relationship model, validation/serialization in existing device modules, rendering and atomic apply; document routes/data contract; run focused regressions and backend gate.
2. [ ] Generate/review multi-bind migration in `server/migrations/versions/`; add populated round-trip test/runner in `server/tests/`; verify upgrade/downgrade and backend gate.
3. [ ] Add failing frontend editor/layout/topology tests under `client/src/test/`; implement shared parent editor/API/types, wire Inventory and existing React Flow prototype, routing/navigation/access, automatic hierarchy and device-only panels; update frontend/domain specs; verify frontend gate.
4. [ ] Record isolated live Nagios reachability/rollback evidence in `docs/test-runs/` using the template; update remaining specifications and local issue mirror; run docs/all verification and checkpoint.
5. [ ] Re-read issue and prove acceptance; publish PR using `.github/pull_request_template.md`, monitor CI; keep draft/progress if live acceptance or human decisions remain outstanding.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Backend graph/model/API/rendering and generated migration; baseline tests fail as expected before implementation. Fixed an authorization test that reused the authenticated client fixture; 308 focused regressions and then 34 parent/migration proofs pass. | FLASK_DEBUG=1 .venv/bin/python -m pytest tests/unit/test_device_parents.py tests/unit/test_device_parent_migration.py -q | 34 passed; first full backend gate still running and contains the already-fixed test fixture failure |
| intake | Reviewed issue scope and existing React Flow frontend; created isolated checkout | gh issue view 117 --json body,comments,title | Product decisions recorded; no implementation yet |

## State for the next session

- Last check run (exact command): cd server && FLASK_DEBUG=1 .venv/bin/python -m pytest tests/unit/test_device_parents.py tests/unit/test_device_parent_migration.py -q
- Result: 34 passed in 6.23s. Broader focused regression: 308 passed in 39.12s. Initial full backend gate running at /tmp/issue117-backend-gate.log; it collected the old test-auth fixture before its correction.
- Hypothesis: Existing writer and Inventory modules can support this without a new dependency; use a relationship table and shared editor.
- Next action: Finish/re-run backend gate after correcting test-auth fixture, then implement frontend against the newly failing editor/topology tests.

## Decisions and notes

- User explicitly authorized implementation after resolving scope, including relationship migration, sensitive Nagios rendering and scoped lab tests described by the issue. No additional permission is inferred for unrelated labs or deployments.
- Security review required for parent rendering: only stable validated Nagios identifiers may enter generated config; retain shared writer pre-apply validation/resource rollback. Parent IDs are positive distinct integers; graph traversals are iterative and bounded by loaded rows.
- Existing topology is a disconnected static React Flow prototype; retain canvas/node/edge selection structure, remove fake telemetry, do frontend layout only. Keep System Status separate.
- No new permissions or dependency planned. View uses `system.network_health` as Inventory does; parent write uses `system.hosts.edit`. Gateway suggestions remain advisory.
- The issue asks existing drawer/table regressions to pass unchanged; route tests excluding topology must change because the owner explicitly reversed that scope.

- Migration generation: used private databases upgraded to a129f6d23901, flask_migrate.migrate with rev_id b117d9a2c041 (multi-bind environment). Reviewed generated operations: default-bind table/index/FKs/self-check only, no history changes.
- Shared writer inspection found a legacy history commit inside successful apply; added opt-in deferred commit for parent transactions while preserving the existing default for all other callers. Lifecycle parent edits reuse sync_rows/desired_services/set_plugin_states without committing early.
