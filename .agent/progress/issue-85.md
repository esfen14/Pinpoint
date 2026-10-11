# Issue #85: Add a fix-found loop that fixes QA-found issues and returns cases to retest

Branch: `issue-63-qa-loop-readiness` (Phase 3 evidence carried on PR #88)
Status: in-progress

## Finish condition

- [ ] `.agent/workflows/fix-found.md` and both adapters exist and do not contradict `work-issue.md`.
- [ ] Queue selection, severity ordering, skip rules, and exact `gh` commands are documented.
- [ ] A synthetic demonstration opens one unmerged PR with a closing reference and records skipped candidates.
- [ ] Retest handoff requires a merged fix and records the affected traceability case.
- [ ] The 3-PR cap, two-failed-fix stop, and denied-permission stop are documented.
- [ ] `scripts/verify.sh docs` passes.

## Plan

- [x] Create the workflow and thin adapters.
- [x] Document queue ordering, skip rules, caps, permission stop, and merged-fix retest semantics.
- [x] Record synthetic issue/PR demonstration without merging.
- [ ] Verify docs and update the evidence report with observed results.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Created workflow and adapters | `scripts/check_agent_progress.py` | Initial draft created |
| 2 | Added queue rules and synthetic demonstration | `gh issue list --label qa-found --state open` | Issue #90 was closed as incorrectly filed; PR #91 remains unmerged |
| 3 | Repaired progress structure for PR verification | `scripts/verify.sh docs` | Pending rerun |

## State for the next session

- Last check run: `scripts/verify.sh docs`
- Result: previously failed because this file had the wrong format; repaired now.
- Hypothesis: docs verification will pass after the structural repair unless another progress file is malformed.
- Next action: rerun `scripts/verify.sh docs`, then run the offline PR #88 checks.

## Decisions and notes

- No PR is merged by the agent.
- Issue #90 was synthetic and incorrectly treated intentional #86 identity conflicts as a defect; it was closed. PR #91 is not a product fix and must not be presented as one.
- Live restricted-role and J2/J3 acceptance tests remain pending unless an authorized account and clean appliance baseline are available.
