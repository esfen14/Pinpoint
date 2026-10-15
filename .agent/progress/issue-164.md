# Issue #164: Device identity review and merge controls

Branch: `issue-164-identity-review`
Status: in-progress

## Finish condition

- [ ] Authorized users see the Needs Review table and correct unresolved identity-review count.
- [ ] Reviews remain discoverable regardless of the host table’s monitoring filter.
- [ ] Loading, error, empty and unavailable-evidence states are implemented.
- [ ] Review opens a comparison drawer with candidate details and identity evidence.
- [ ] A review with insufficient candidates allows selection of another discovered record.
- [ ] The administrator explicitly selects the source and surviving target.
- [ ] Confirmation explains merge direction, address retention, conflict precedence and historical-data limitations.
- [ ] Users without merge permission cannot initiate a merge.
- [ ] Self-merges, invalid targets, stale records and repeat submissions are handled.
- [ ] Successful merges refresh the interface.
- [ ] Saved merges with configuration warnings are accurately reported.
- [ ] Device information notices open the same review flow.
- [ ] A recognized IP change continues updating the existing device without requiring a merge.
- [ ] Opening or cancelling review makes no persistent change.
- [ ] Review table, comparison drawer, merge confirmation and device information notice.
- [ ] Typed API helpers and any necessary discovered-device lookup.
- [ ] Frontend interaction tests and relevant backend regression coverage.
- [ ] Updated frontend and backend specifications where affected.
- [ ] Updated `Device_Inventory_Requirements.md` and corrected `Implementation_Status.md`.
- [ ] User-facing guidance explaining when merging is appropriate and which record to keep.
- [ ] Verification output and sanitized browser/lab evidence attached to the pull request.
- [ ] All acceptance criteria and required deliverables are complete.
- [ ] Existing inventory, discovery and monitoring behavior passes regression checks.
- [ ] Authorization, validation and error handling are verified.
- [ ] Automated checks and required CI checks pass.
- [ ] Browser/lab evidence confirms the complete merge journey.
- [ ] Technical and user-facing documentation is updated.
- [ ] The pull request references this issue and describes implementation and verification.
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
3. [ ] Update Device_Inventory_Requirements.md, Frontend_Modules_and_Routes.md, Implementation_Status.md and docs/manuals/device identity guidance; verify docs and all.
4. [ ] Run controlled browser/lab journey with duplicate outside Monitored, keyboard and themes; record sanitized docs/test-runs evidence and attach to PR.
5. [ ] Re-read issue, prove finish conditions, open appropriate PR from template, inspect CI and review requirements.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 2 | Fixed test query typing, added notice/filter integration and keyboard/address retry tests; new components lint cleanly | verify.sh backend; verify.sh frontend; verify.sh docs; focused comparison tests | Backend 3302 passed/14 skipped; frontend 699 passed, build/lint green; docs green; expanded comparison 15 passed |
| 1 | Lookup, review table/drawer, notices, tests and documentation implemented | Focused backend: 152 pass; focused frontend: 48 pass; verify.sh docs: green; verify.sh frontend | Frontend build rejects two new Testing Library queries using unsupported exact option; backend full suite still running |
| 0 | Intake and isolated worktree; requirement coverage and plan | gh issue view 164 --json body,comments | Requirements covered by E/F/H; reviewer approval remains a human finish requirement |

## State for the next session

- Last check run (exact command): cd client && npm test -- --run src/test/DeviceIdentityReview.test.tsx
- Result (first failing lines, or "green"): green: 15 passed. Full backend 3302 passed/14 skipped, full frontend 699 passed with successful build/lint before two additional comparison tests; docs green. Logs /tmp/issue-164-{backend,frontend,docs,keyboard}.log.
- Hypothesis: implementation and isolated regressions are sound; browser/Nagios acceptance requires Docker socket access.
- Next action (one specific step, not "continue"): Add an opt-in browser journey and run verify.sh all while waiting for the user to restore Docker access.

## Decisions and notes

- User invoked work-issue 164; isolated checkout is /tmp/Pinpoint-issue-164.
- Issue explicitly approves extending identity review UI and correcting stale specifications; no identity-matching, config-generation, migration, dependency or permission changes planned.
- Browser/lab work is explicitly authorized by issue G; use isolated controlled records and preserve shared lab ownership boundaries.
- Required reviewer approvals cannot be claimed by this agent; retain an honest unfinished checklist and draft PR if necessary.

- Docker socket is denied and passwordless sudo unavailable in this process. Real-Nagios lab acceptance requires an accessible reserved lab; no lab has been mutated.

- User selected Docker labs for acceptance. Docker access restoration requested asynchronously; do not mutate the VM. scripts/vmlab preflight also reports VBoxManage not found.
