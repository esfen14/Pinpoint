# Issue #116: Alert contact groups and Nagios escalations

Branch: `issue-116-alert-escalations`
Status: in-progress

## Finish condition

Authoritative issue: https://github.com/esfen14/Pinpoint/issues/116 (read 2026-10-15, no comments).
All E, F and H checkboxes are retained below; review approvals remain human-owned.

#### E. Acceptance Criteria

- [ ] **Part 3.1 (System):** A saved escalation appears as a valid `define serviceescalation` or `hostescalation` block and Nagios validates the config.
- [ ] **Part 3.1 (System):** An escalation whose group has no eligible member is not written, and saving it explains why.
- [ ] **Part 3.1 (System):** Invalid values (first greater than last, unknown group, out-of-range interval) return 400.
- [ ] **Part 3.1 (System):** Deleting an escalation removes it from the live config.
- [ ] **Part 3.1 (System):** With no escalations defined, generated config is unchanged.
- [ ] **Part 3.2 (Web-Interface):** An administrator can add, edit and delete an escalation and sees it after reload.
- [ ] **Part 3.2 (Web-Interface):** Invalid input is blocked in the form and server errors are shown.
- [ ] **Part 3.2 (Web-Interface):** Users without permission do not see the card.
- [ ] **Part 3.2 (Web-Interface):** The settings page tests pass unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Help text on the card.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.


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



Requirement coverage:

| Issue requirement | Finish-condition item | Proof (planned, not yet run) |
|---|---|---|
| A: route alerts by host/group and escalate after notification count | E rendering and administrator CRUD; H functional completion | Renderer/API tests and two-contact live CRITICAL dispatch |
| A: no new channels | H no duplicate functionality; F source | Diff review: existing email only |
| C backend 1: model, first/last count, interval, group, all/host scope, migration | F source and downgrade migration; H migration documentation | Model/API tests and populated multi-bind upgrade/downgrade |
| C backend 2/4: templates, empty-group skip after opt-out/deactivation | E valid blocks and empty-member handling; H edge cases | Renderer/account regeneration regression tests; real nagios -v |
| C backend 3: CRUD, validation, settings.system, shared apply and rollback | E invalid input/delete; F endpoints; H authorization/error handling | API login/403/400/422 and persisted rollback tests |
| C frontend 1/2: settings card, fields, API/types, add/edit/delete/reload | E administrator CRUD; F frontend | Interaction tests and browser persistence walkthrough |
| C frontend 3/4: no-member explanation, server 400/422, delete confirmation, permission gate | E invalid input/permission; F help text | Interaction tests for disabled form, errors, confirmation and permission hiding |
| D: reuse #79 groups and existing modules | H architecture/no duplication | Single shared group computation used by writer and escalation options |
| D: exact unchanged defaults | E no-escalation output unchanged | Existing test_create_host_cfg.py plus fixed-time byte comparison |
| D: docstrings/envelopes, rollback, TS, validation/security review | F endpoints/source; H security and code quality | API assertions, explicit injection/secret review, lint/build |
| D: migration reviewed, working downgrade; permissions sync if added | F migration; H deployment steps | Generated multi-bind migration, round-trip test; reuse settings.system so no new permission |
| D: loading/error/empty/success and bounded work | H edge cases and reliability; F frontend/help | Interaction tests and query/loop inspection |
| D/F: technical docs and implementation status current | F four specs; H documentation | scripts/verify.sh docs |
| F/G: real unit/frontend/regression/live evidence | F tests and report; H testing | scripts/verify.sh all, sanitized docs/test-runs report with exact tested SHA |
| H: PR reference, description, green CI and approvals | H PR review | PR Closes #116, test evidence, gh pr checks; human reviewer approval |

## Plan

1. [x] Backend TDD: extend `server/tests/unit/test_create_host_cfg.py`, `test_host_recipients.py` and new escalation API/migration tests; add `Escalation` to `server/app/system_models.py`, generate/review multi-bind migration and add round-trip support runner. Extract the existing group computation from `server/app/network_discovery/create_host_cfg.py` for shared use without changing default output. Add `hostescalation.cfg.tpl` / `serviceescalation.cfg.tpl` and validated rendering in `host_config_templates.py`. Add CRUD/options in `server/app/api/system/escalations.py`, register in `__init__.py`, reuse `settings.system`, hold config lock through apply/commit, rollback failed apply. Verify focused tests, Python compilation, backend stage and explicit injection/secret-exposure review.
2. [x] Frontend TDD: add `client/src/test/EscalationSettings.test.tsx`; implement `client/src/components/settings/EscalationSettings.tsx`, `client/src/lib/escalationApi.ts`, `client/src/types/escalation.ts`; mount under existing System settings permission. Cover add/edit/delete/reload, validation, 400/422 messages, no-member disabled form, confirmation and loading/error/success states; verify focused tests, PageAccess/LayoutSettings regressions and frontend stage.
3. [x] Update `spec files/Backend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`, `server/tests/README.md` and UI help; document migration and reuse of settings.system; verify docs.
4. [ ] Execute issue G's bounded two-contact live Nagios escalation trial in the approved exclusive lab; record real validation, delayed second-contact dispatch, deletion and default regression evidence in a sanitized `docs/test-runs/` report and index. Re-read issue/comments and prove every applicable requirement, run `scripts/verify.sh all`, attach output to PR.
5. [ ] Remove progress file only after finish checks pass, push PR using template with Closes #116, observe CI, report reviewer approvals honestly; never merge.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Read workflow, issue/prerequisites/specifications and relevant writer/model/API/UI source; created isolated worktree; no application edits | gh issue view 79/113; git log -6 --oneline origin/main | #79 merged as e4130ccf (PR #160); #113 closed/merged. No existing #116 branch. |
| Plan | Saved finish conditions and coverage; stopped at explicit sensitive-module approval boundary | python3 -I scripts/check_agent_progress.py | green |

| 1 | Backend model/migration/group reuse, API, rendering and frontend settings card, with owning specs; frontend work ran while the independent backend suite was pending | Focused backend 184; focused frontend/access/layout 34; scripts/verify.sh backend/frontend/docs | green: backend 2858 passed/14 skipped; frontend 651 passed/build green/0 lint errors/29 existing warnings; docs green |

## State for the next session

- Last check run (exact command): scripts/verify.sh backend
- Result (first failing lines, or "green"): green: 2858 passed, 14 skipped in 411.54s; verify: backend OK
- Hypothesis: Prerequisites are satisfied; existing #79 group computation can supply escalation group choices and rendering. Implementation requires sensitive Nagios config changes, triggering the workflow's Needs a person stop.
- Next action (one specific step, not "continue"): Finish the isolated Docker two-contact Nagios escalation trial; discovery is Running on the two explicit target /32 ranges (do not start overlapping discovery).

## Decisions and notes

- Working directory: /tmp/Pinpoint-issue-116; root user's checkout remains on main and unchanged.
- The user requested `.agents/workflows/work-issue.md`; that path is absent. Followed the authoritative `.agent/workflows/work-issue.md` routed by AGENTS.md.
- The issue states the whole model, UI and lab scope. All requirements map to E/F/H above; no missing finish-condition requirement identified.
- Required approval comes from `.agent/workflows/work-issue.md` section 4: "the change touches a sensitive module (see spec files/Engineering_Standards.md)" requires stopping for a person. Engineering Standards classifies app/network_discovery/ as sensitive. Request authorization to implement the plan with explicit injection/secret review and preserved pre-apply validation.
- The issue explicitly requests the live lab trial, so lab testing is already in task scope. Select a lab only after checking exclusive ownership; do not reuse approval comments from unrelated issues.
- No tests, live checks, functionality or reviewer approvals claimed. No application code changed.

- User explicitly authorized the sensitive configuration changes: "proceed with configuration changes" (2026-10-15). No further sensitive-module approval required for this plan.

- Initial implementation checkpoint: backend/API/renderer tests failed first with missing routes (404 vs 403); focused backend + host/recipient/email regressions + migration now pass (184). Frontend tests failed first on missing component; focused frontend/access/layout checks pass (34). `scripts/verify.sh frontend` passes: 651 tests, build green, zero lint errors / 29 existing warnings. Full backend stage is still running; do not claim it passed yet.
- Generated migration using Flask-Migrate's multi-bind environment against disposable databases upgraded to e79b7d3c2641; inspected autogeneration: only ESCALATION added on default bind, history upgrade/downgrade no-op.
- Injection/secret review: group identifiers are system_users or generated numeric device names from the single recipient helper; API rejects arbitrary strings, scoped host IDs resolve to generated names and renderer rejects directive metacharacters. Count/interval inputs require exact integers (not bool), with database constraints too. No new shell commands, file destinations, network calls, secrets or log payloads are added. Shared pre-apply validation and config lock remain in place. Apply failures roll back choices; commit failure attempts to rebuild prior config.
- Frontend work/checks ran while the independent full backend suite was pending; required specs updated with source so route drift stage passes. No failed check was weakened.
- Docker access was explicitly authorized by the user and group membership granted. Fresh shells can access Docker through `sg docker -c ...` (the parent shell has stale groups). Created separate project pinpoint-issue116 on its own internal subnet and API port 18000 using cached lab images and this worktree's source mount. Existing pinpoint-lab and issue-128 containers are untouched. Lab is running, product acceptance not yet executed.

- Round 1 verification logs: /tmp/pinpoint-116-backend.log, /tmp/pinpoint-116-frontend.log, /tmp/pinpoint-116-docs.log. Lab source checkpoint c1bf732f. One lab harness expectation initially used HTTP 200 for discovery start; server correctly returned 202 and started discovery. Preparation resumed without restarting/overlapping the scan. No product failure claimed.
