# Issue #164: Device identity review and merge controls

Branch: `issue-164-identity-review`
Status: in-progress

## Finish condition

- [x] Authorized users see the Needs Review table and correct unresolved identity-review count.
- [x] Reviews remain discoverable regardless of the host table’s monitoring filter.
- [x] Loading, error, empty and unavailable-evidence states are implemented.
- [x] Review opens a comparison drawer with candidate details and identity evidence.
- [x] A review with insufficient candidates allows selection of another discovered record.
- [x] The administrator explicitly selects the source and surviving target.
- [x] Confirmation explains merge direction, address retention, conflict precedence and historical-data limitations.
- [x] Users without merge permission cannot initiate a merge.
- [x] Self-merges, invalid targets, stale records and repeat submissions are handled.
- [x] Successful merges refresh the interface.
- [x] Saved merges with configuration warnings are accurately reported.
- [x] Device information notices open the same review flow.
- [x] A recognized IP change continues updating the existing device without requiring a merge.
- [x] Opening or cancelling review makes no persistent change.
- [x] Review table, comparison drawer, merge confirmation and device information notice.
- [x] Typed API helpers and any necessary discovered-device lookup.
- [x] Frontend interaction tests and relevant backend regression coverage.
- [x] Updated frontend and backend specifications where affected.
- [x] Updated `Device_Inventory_Requirements.md` and corrected `Implementation_Status.md`.
- [x] User-facing guidance explaining when merging is appropriate and which record to keep.
- [x] Verification output and sanitized browser/lab evidence attached to the pull request.
- [x] All acceptance criteria and required deliverables are complete.
- [x] Existing inventory, discovery and monitoring behavior passes regression checks.
- [x] Authorization, validation and error handling are verified.
- [ ] Automated checks and required CI checks pass.
- [x] Browser/lab evidence confirms the complete merge journey.
- [x] Technical and user-facing documentation is updated.
- [x] The pull request references this issue and describes implementation and verification.
- [ ] Required reviewer approvals are obtained and blocking comments are resolved.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| A, C1–3: separate unresolved identity table, all five kinds, service exclusions, states | E1–3, F1 | DeviceIdentityReview interaction tests; page integration tests |
| C4–5: on-demand comparison, missing evidence, explicit roles, discovered lookup | E4–6, F1–3 | DeviceIdentityReview tests; test_device_identity_lookup.py |
| C6–7: full confirmation, repeat guard, refresh and saved warnings | E7, E9–11 | Interaction tests; live browser journey |
| C8: device notice opens same flow | E12 | StatusDetailDrawer and page integration tests |
| Backend reuse, existing merge/config validation, no review mutation on open | E9, E13–14 | test_device_identity_routes.py, test_device_identity.py; browser cancellation |
| D: permissions, stale validation, shared typed API, keyboard/themes | E8–9, F2–3, H3 | Frontend tests, backend permissions tests, browser keyboard/theme checks |
| A exclusions: no automatic matching, retire/address editing, port mismatch, snapshot combination or undo changes | E13–14 | Scoped diff; regression tests |
| D, F4–6: specifications, status correction, user guidance | F4–6, H6 | docs verification; inventory spec and manual |
| F7, G, H1–5: actual automated and browser evidence | F7, H1–5 | verify.sh all; docs/test-runs report; CI |
| H7–8: linked PR, human review and resolved blocking comments | H7–8 | PR description, CI and reviewer status |


## Plan

1. [x] Add lookup regression tests, implement bounded permission-protected discovered lookup in server/app/api/system/device_identity.py; update backend specification; run focused and backend verification.
2. [x] Add failing frontend interaction tests; implement typed contracts/helpers, review table and comparison/confirmation components in client/src/types/deviceIdentity.ts, lib/deviceIdentityApi.ts and components/device-inventory/; integrate DeviceInventoryPage.tsx and StatusDetailDrawer.tsx; run frontend verification.
3. [x] Update Device_Inventory_Requirements.md, Frontend_Modules_and_Routes.md, Implementation_Status.md and docs/manuals/device identity guidance; verify docs and all.
4. [x] Run controlled browser/lab journey with duplicate outside Monitored, keyboard and themes; record sanitized docs/test-runs evidence and attach to PR.
5. [ ] Re-read issue, prove finish conditions, open appropriate PR from template, inspect CI and review requirements.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 7 | Fixed stale review summaries in selectors/confirmation by propagating fresh evidence summaries; regression added first | New regression red (old target name/IP); focused frontend green (51); verify.sh frontend green (702 tests); lookup tests green (6) | Corrected confirmation; test mocks now return the lifecycle of the requested fixture rather than a different device. CI on prior checkpoint is green; final-code all/lab repeat pending |
| 6 | Strengthened lookup wildcard regression against an unmerged visible record and a literal percent name | FLASK_DEBUG=1 server/.venv/bin/python -m pytest server/tests/unit/test_device_identity_lookup.py -q | Green: 6 passed; product code unchanged. Required full-stage CI is being observed before final checkpoint |
| finish | Opened draft PR #176 and attached sanitized report / verification | gh pr view issue-164-identity-review --json number,url,isDraft,statusCheckRollup,reviewDecision | PR exists; docs/backend/frontend CI in progress; no reviewer approval |
| 5 | Full local gate and restored Docker configuration | scripts/verify.sh all; restored reconcile; fixture verify; nagios -v | Green: 3302 backend passed/14 skipped; 701 frontend passed; build/lint successful (0 errors, 28 existing warnings); restored configuration passes with 0 Nagios errors/warnings |
| 4 | Recreated own appliance and deliberately stopped its Nagios before merge | Playwright issue-164-live with ISSUE164_EXPECT_CONFIG_WARNING=1 | Green: 1 passed; config_ok false with saved merge, one POST, source Merged, target retained, reviews refreshed. Full gate still running |
| 3 | Disposable Docker project; controlled reconciler fixtures; repeatable opt-in browser journey | Playwright issue-164-live twice (including real source snapshot + linked notice); fixture verify; nagios -v | Both browser runs pass; target address/port/review/config postconditions pass; Nagios 0 warnings/0 errors. Full verify.sh all still running |
| resumed | Docker membership enabled by user; sg docker activates it in this existing session | Docker ps; repeated comparison tests | Docker accessible; using a fresh isolated project, shared lab untouched |
| 2 | Fixed test query typing, added notice/filter integration and keyboard/address retry tests; new components lint cleanly | verify.sh backend; verify.sh frontend; verify.sh docs; focused comparison tests | Backend 3302 passed/14 skipped; frontend 699 passed, build/lint green; docs green; expanded comparison 15 passed |
| 1 | Lookup, review table/drawer, notices, tests and documentation implemented | Focused backend: 152 pass; focused frontend: 48 pass; verify.sh docs: green; verify.sh frontend | Frontend build rejects two new Testing Library queries using unsupported exact option; backend full suite still running |
| 0 | Intake and isolated worktree; requirement coverage and plan | gh issue view 164 --json body,comments | Requirements covered by E/F/H; reviewer approval remains a human finish requirement |

## State for the next session

- Last check run (exact command): scripts/verify.sh frontend
- Result (first failing lines, or "green"): green: 702 tests, successful build/lint (0 errors, 28 existing warnings). 51 focused inventory/comparison tests and 6 lookup tests pass. Prior checkpoint CI run 38736578525 passed all three jobs; fresh-summary correction must pass its own full/local/browser checks.
- Hypothesis: fresh evidence now consistently drives comparison, merge choices and confirmation, including lifecycle exclusions.
- Next action (one specific step, not "continue"): Run scripts/verify.sh all and repeat the normal/notice and unavailable-Nagios Docker browser journeys against this committed correction.

## Decisions and notes

- User invoked work-issue 164; isolated checkout is /tmp/Pinpoint-issue-164.
- Issue explicitly approves extending identity review UI and correcting stale specifications; no identity-matching, config-generation, migration, dependency or permission changes planned.
- Browser/lab work is explicitly authorized by issue G; use isolated controlled records and preserve shared lab ownership boundaries.
- Required reviewer approvals cannot be claimed by this agent; retain an honest unfinished checklist and draft PR if necessary.

- Docker socket is denied and passwordless sudo unavailable in this process. Real-Nagios lab acceptance requires an accessible reserved lab; no lab has been mutated.

- User selected Docker labs for acceptance. Docker access restoration requested asynchronously; do not mutate the VM. scripts/vmlab preflight also reports VBoxManage not found.

- Docker access now works through sg docker after the user added paeng to docker. Exclusive project pinpoint-issue164 uses API 8164 / Vite 5164 and an isolated private network; shared pinpoint-lab is untouched.
- Docker startup required disabling the opt-in scheduler before initial migrations; this is test provisioning only. Controlled observations perform no network scan. A forced real check supplies an address-unknown source snapshot for the notice journey. Raw screenshots: /home/paeng/pinpoint-test-results/issue164/{success,notice}.

- Re-read issue #164 after lab tests: body unchanged, no comments. Every requirement has proof in the coverage table and sanitized report. No exclusion was implemented. Retain progress file and draft PR because H8 reviewer approval is outstanding; do not claim issue completion.

- PR: https://github.com/esfen14/Pinpoint/pull/176 (draft; Closes #164). Evidence is attached by a branch-pinned link to the committed sanitized report.

- Security review: lookup uses SQLAlchemy-bound parameters and literal wildcard escaping with bounded search/results. The opt-in lab FIFO probe uses only a fixed fixture host name and integer timestamps, a fixed FIFO path and nonblocking write; it accepts no shell commands or credentials. No sensitive product module was modified.
- Disposable Docker project and local Vite process have been removed/stopped; raw evidence remains in the report location.

- Plan revision from evidence: a final comparison consistency check showed that freshly loaded name/IP/state only updated cards, not choices/confirmation. Added a failing regression, propagated fresh API device summaries, and updated the inventory specification. No backend behavior changed.
