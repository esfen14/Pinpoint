# Issue #85: Add a fix-found loop that fixes QA-found issues and returns cases to retest

Branch: `issue-63-qa-loop-readiness` (Phase 3 evidence carried on PR #88)
Status: blocked

## Finish condition

- [x] `.agent/workflows/fix-found.md` and both adapters exist and do not contradict `work-issue.md`.
- [x] Queue selection, severity ordering, skip rules, and exact `gh` commands are documented.
- [ ] A synthetic demonstration opens one unmerged PR with a closing reference and records skipped candidates.
- [ ] Retest handoff requires a merged fix and records the affected traceability case.
- [x] The 3-PR cap, two-failed-fix stop, and denied-permission stop are documented and covered by written contract checks.
- [x] `scripts/verify.sh docs` passes.

## Plan

- [x] Recovery: correct queue, command compatibility, guardrails and handoff in `.agent/workflows/fix-found.md` and the owning specification.
- [x] Recovery: correct overstated synthetic report; add written boundary checks and verify actual GitHub evidence.

- [x] Create the workflow and thin adapters.
- [x] Document queue ordering, skip rules, caps, permission stop, and merged-fix retest semantics.
- [ ] Record a valid synthetic demonstration with observed skips and scratch retest handoff.
- [x] Verify docs and update the evidence report with observed results; `scripts/verify.sh docs` passes and the 2026-10-11 live continuation is recorded as partial.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Created workflow and adapters | `scripts/check_agent_progress.py` | Initial draft created |
| 2 | Added queue rules and synthetic demonstration | `gh issue list --label qa-found --state open` | Issue #90 was closed as incorrectly filed; PR #91 was later merged; no product fix |
| Recovery 1 | Corrected queue, gh compatibility, guardrails, human merge gate and overstated report | `scripts/verify.sh docs` | green; live/synthetic acceptance incomplete |
| Recovery 2 | Added executable documentation contracts for queue, skips, limits, permission stop, real-merge handoff and human merge gate | `python3 -I scripts/test_fix_found_workflow.py`; `scripts/verify.sh docs` | 6 contract tests pass; external synthetic issue/PR demonstration still pending |
| 3 | Repaired progress structure for PR verification | `scripts/verify.sh docs` | green |
| Recovery 3 | Ran the real planted assertion twice and prepared the candidate issue; audited the external gate | two `scripts/playwright-lab --project admin -g 'J2-01 planted failure'` runs; exact `gh issue list` search | both attempts failed at the planted assertion; no duplicate issue exists; GitHub mutations await explicit approval |

## State for the next session

- Last check run: `scripts/verify.sh all` with local-socket/DNS permission.
- Result: green: docs including 6 fix-found contracts; backend 2315 passed, 14 skipped; frontend 492 passed, build passed, lint 0 errors/25 tracked warnings.
- Hypothesis: implementation, written guardrails and the planted input are complete; only the attributable external issue/PR/skip demonstration and post-merge scratch retest handoff remain.
- Next action: obtain explicit approval, create the prepared synthetic `qa-found` candidate and a `needs-decision` skip candidate, then run the documented queue and open one unmerged closing PR.

## Decisions and notes

- No PR is merged by the agent.
- Issue #90 was synthetic and incorrectly treated intentional #86 identity conflicts as a defect; it was closed. PR #91 is merged but is not a product fix and must not be presented as one.
- Live restricted-role smoke passed; the remaining J2/J3 acceptance is independent of #85.
- Automatic approval review rejected the PR comment/issue-state mutations because the user had not explicitly approved publishing project evidence or changing GitHub issue state. Do not retry through another tool.
- The planned valid demonstration uses a clearly synthetic J2-01 scratch failure. It must not change the real J2-01 traceability result. One synthetic candidate will be skipped for `needs-decision`; after the selected candidate receives an open PR, the next queue pass records the open-PR skip.
- The agent will not merge the demonstration PR. The final retest-handoff checkbox remains blocked until a human merge supplies the required merged-fix event.

### 2026-10-11 resumed audit

- Re-ran `scripts/verify.sh docs`: green. Existing uncommitted progress edits retained.
- Read current GitHub issues #63, #85 and #93. User released the lab for the remaining checks, including restricted-account provisioning and restoration.
- PR #91 is merged (2026-10-11); it is a synthetic no-product-fix PR. Its merge does not prove J2-08 was fixed.
- Source inspection contradicts earlier completion notes: restricted setup is selected by the admin setup project, forced-change handling is absent, and fix-found has conflicting filenames and unsupported CLI fields. Recovery steps above supersede those completion claims.
