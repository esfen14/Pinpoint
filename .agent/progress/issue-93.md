# Issue #93: Provide a safe restricted-role account for live QA smoke tests

Branch: `issue-93-restricted-qa-account`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] Define the supported QA provisioning path for a temporary Staff or Manager account on a fresh appliance.
- [x] Ensure the account has the permissions required by the restricted-role QA cases and lacks administrator-only permissions.
- [x] Make the provisioning step safe to repeat and document cleanup or appliance-reset handling.
- [x] Supply credentials to Playwright through approved environment/secret handling only; never commit or print them.
- [x] Run the restricted-role Playwright smoke suite successfully, or record any genuine product defect separately.
- [x] Update the QA documentation and PR #88 evidence with the attributable result.
- [x] Run the relevant verification checks, including `scripts/verify.sh docs`.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Deterministic temporary restricted-role account on a fresh appliance without exposed credentials or committed auth state | 1, 3, 4 | Inspect `scripts/vmlab`, `lab/setup_restricted.py`, `scripts/playwright-lab`, `.gitignore`, and `scripts/test_playwright_safety.py` |
| Restricted permissions cannot be substituted with an administrator | 2, 5 | `client/e2e/smoke.restricted.spec.ts`; sanitized J9-04 result in `docs/test-runs/2026-10-11-role-smoke/REPORT.md` |
| Live restricted-role smoke coverage for PR #88 | 5, 6 | `docs/test-runs/2026-10-11-role-smoke/REPORT.md`; merged PR #88 commit ancestry |
| Documentation and docs verification | 3, 6, 7 | `docs/qa/Playwright_Setup.md`; `scripts/verify.sh docs` |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [x] Verify that the already-merged restricted-role provisioning, smoke, documentation, and PR #88 evidence satisfy each issue requirement; inspect `scripts/vmlab`, `lab/setup_restricted.py`, `scripts/playwright-lab`, `client/e2e/`, `docs/qa/Playwright_Setup.md`, and `docs/test-runs/2026-10-11-role-smoke/REPORT.md`.
2. [x] Run the offline safety regression and `scripts/verify.sh docs`; record the observed results in this progress file.
3. [ ] Re-read issue #93 and PR #88, then close #93 with an attributable evidence comment if every finish-condition item is proven; remove this progress file and push the branch.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|
| 1 | Started issue branch after finding the full implementation and live report already merged via PR #88. | GitHub issue/PR and commit-ancestry inspection | Evidence is on `origin/main`; offline verification remains. |
| 2 | Installed the pinned isolated dependencies and verified the inherited implementation. | `python3 -I scripts/test_playwright_safety.py`; `scripts/verify.sh docs`; initial `scripts/verify.sh all` | Safety: 8 passed. Docs: green. The initial full check reached backend route drift then could not create the isolated worktree's generated `server/host-config-files` under the sandbox (`OSError: [Errno 30] Read-only file system`). |
| 3 | Re-ran the full gate with the isolated worktree write access required for generated test files. | `scripts/verify.sh all` | Green: docs, route/API drift, backend unit suite, frontend tests/build, and lint completed; the process exited cleanly and left the branch clean. |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `scripts/verify.sh all`
- Result (first failing lines, or "green"): green; docs, route/API drift, backend unit tests, frontend tests/build, and lint completed successfully.
- Hypothesis: #93 is fully satisfied by work merged into PR #88; closing it with the precise report and commit evidence is appropriate.
- Next action (one specific step, not "continue"): re-read issue #93 and PR #88, then post the attributable closure comment.

## Decisions and notes

The issue was opened at 2026-10-11T09:06:40Z. PR #88 merged at 2026-10-11T11:40:16Z and contains commits `c8fcd586` (provisioning/smoke), `1bae5171` (sanitized evidence), and the documentation/status updates. The live VM lab will not be rerun without an explicit release because it is outside the standard issue verification loop.
