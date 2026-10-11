# Issue #85: Add a fix-found loop that fixes QA-found issues and returns cases to retest

Branch: `issue-63-qa-loop-readiness` (Phase 3 evidence carried on PR #88)
Status: in-progress

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
| 3 | Repaired progress structure for PR verification | `scripts/verify.sh docs` | Pending rerun |

## State for the next session

- Last check run: `python3 -I scripts/test_fix_found_workflow.py`.
- Result: 6 contract tests pass after correcting the workflow and its GitHub CLI commands.
- Hypothesis: implementation and written guardrails are complete; only an attributable external synthetic issue/PR/skip/handoff demonstration remains.
- Next action: after explicit approval for the external GitHub mutations, file the prepared planted finding and run the synthetic queue demonstration without merging.

## Decisions and notes

- No PR is merged by the agent.
- Issue #90 was synthetic and incorrectly treated intentional #86 identity conflicts as a defect; it was closed. PR #91 is merged but is not a product fix and must not be presented as one.
- Live restricted-role smoke passed; the remaining J2/J3 acceptance is independent of #85.

### 2026-10-11 resumed audit

- Re-ran `scripts/verify.sh docs`: green. Existing uncommitted progress edits retained.
- Read current GitHub issues #63, #85 and #93. User released the lab for the remaining checks, including restricted-account provisioning and restoration.
- PR #91 is merged (2026-10-11); it is a synthetic no-product-fix PR. Its merge does not prove J2-08 was fixed.
- Source inspection contradicts earlier completion notes: restricted setup is selected by the admin setup project, forced-change handling is absent, and fix-found has conflicting filenames and unsupported CLI fields. Recovery steps above supersede those completion claims.
