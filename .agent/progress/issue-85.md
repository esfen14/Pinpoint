# Issue #85: Add a fix-found loop that fixes QA-found issues and returns cases to retest

Branch: `issue-63-qa-loop-readiness` (Phase 3 evidence carried on PR #88)
Status: ready-for-review (not blocked)

Issue #85 has no remaining implementation or `qa-found` issue dependency. Its
changes share PR #88 with issue #63, so final delivery waits only for that PR's
main-branch conflict and CI state to be resolved.

## Finish condition

- [x] `.agent/workflows/fix-found.md` and both adapters exist and do not contradict `work-issue.md`.
- [x] Queue selection, severity ordering, skip rules, and exact `gh` commands are documented.
- [x] A synthetic demonstration opened PR #91 unmerged with a closing reference; scratch queue evidence records `needs-decision` and existing-open-PR skips.
- [x] Retest handoff requires a merged fix and is demonstrated only on a scratch row after the human merge of PR #91; no product traceability case was changed.
- [x] The 3-PR cap, two-failed-fix stop, and denied-permission stop are documented and covered by written contract checks.
- [x] `scripts/verify.sh docs` passes.

## Plan

- [x] Recovery: correct queue, command compatibility, guardrails and handoff in `.agent/workflows/fix-found.md` and the owning specification.
- [x] Recovery: correct overstated synthetic report; add written boundary checks and verify actual GitHub evidence.

- [x] Create the workflow and thin adapters.
- [x] Document queue ordering, skip rules, caps, permission stop, and merged-fix retest semantics.
- [x] Record the corrected synthetic demonstration with scratch skips and scratch-only retest handoff.
- [x] Verify docs and update the evidence report with observed results; `scripts/verify.sh docs` passes and the 2026-10-11 live continuation is recorded as partial.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Created workflow and adapters | `scripts/check_agent_progress.py` | Initial draft created |
| 2 | Added queue rules and synthetic demonstration | `gh issue list --label qa-found --state open` | Issue #90 was closed as incorrectly filed; PR #91 was later merged; no product fix |
| Recovery 1 | Corrected queue, gh compatibility, guardrails, human merge gate and overstated report | `scripts/verify.sh docs` | green; live/synthetic acceptance incomplete |
| Recovery 2 | Added executable documentation contracts for queue, skips, limits, permission stop, real-merge handoff and human merge gate | `python3 -I scripts/test_fix_found_workflow.py`; `scripts/verify.sh docs` | contract tests pass; later expanded to 7 checks |
| 3 | Repaired progress structure for PR verification | `scripts/verify.sh docs` | green |
| Recovery 3 | Ran the planted assertion twice and reconciled #90/#91 as scratch-only workflow evidence | two `scripts/playwright-lab --project admin -g 'J2-01 planted failure'` runs; PR #91 merge evidence; workflow contract tests | expected assertion failed twice; PR was human-merged; scratch row moves to retest while product J2-08 remains unchanged |

## State for the next session

- Last check run: `scripts/verify.sh all` with local-socket/DNS permission.
- Result: green: docs including 7 fix-found contracts; backend 2315 passed, 14 skipped; frontend 492 passed, build passed, lint 0 errors/25 tracked warnings.
- Hypothesis: all #85 finish conditions are covered by corrected historical evidence, scratch queue fixtures and executable contract checks.
- Next action: keep #85 ready for review; delete this shared progress file only when PR #88 is reconciled with main and made ready after #63's CI requirement is satisfied.

## Decisions and notes

- No PR is merged by the agent.
- Issue #90 was synthetic and incorrectly treated intentional #86 identity conflicts as a defect; it was closed. PR #91 is merged but is not a product fix and must not be presented as one.
- Live restricted-role smoke passed; the remaining J2/J3 acceptance is independent of #85.
- The planted J2-labelled assertion is deliberately false workflow evidence, not a `qa-found` product issue. It does not change the real J2-01 result.
- PR #91 was opened unmerged by the agent and later merged by a human. Its closed synthetic issue supplies a scratch-only handoff example; it does not prove a J2-08 fix.
- The queue's `needs-decision` and open-PR skip paths are exercised by scratch fixtures and enforced by `scripts/test_fix_found_workflow.py`, avoiding more fake GitHub issues.
- #85 is not blocked. The shared PR's merge conflict and missing CI checks are #63
  integration work, not missing fix-found behavior.

### 2026-10-11 resumed audit

- Re-ran `scripts/verify.sh docs`: green. Existing uncommitted progress edits retained.
- Read current GitHub issues #63, #85 and #93. User released the lab for the remaining checks, including restricted-account provisioning and restoration.
- PR #91 is merged (2026-10-11); it is a synthetic no-product-fix PR. Its merge does not prove J2-08 was fixed.
- Source inspection contradicts earlier completion notes: restricted setup is selected by the admin setup project, forced-change handling is absent, and fix-found has conflicting filenames and unsupported CLI fields. Recovery steps above supersede those completion claims.
