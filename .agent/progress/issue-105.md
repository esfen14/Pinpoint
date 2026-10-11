# Issue #105: QA: Functional Suitability follow-up VM-lab run (2026-10-12)

Branch: `issue-105-qa-run`
Status: in-progress

## Finish condition

- [ ] Safe environment ownership/baseline is confirmed; only `10.77.0.0/28` is scanned.
- [ ] Up to five FS cases are observed and recorded, or blocking conditions are documented.
- [ ] Every mutation is restored.
- [ ] QA report/index/traceability/progress records are current and `scripts/verify.sh docs` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Use only a safe, owner-authorized VM lab and scan only the allowed subnet | Safe environment ownership/baseline | `scripts/vmlab status`, read-back of configured discovery networks, and sanitized report |
| Observe up to five unblocked FS cases or document a blocker | Up to five FS cases recorded | QA report plus traceability rows |
| Restore every mutation | Every mutation restored | Recorded restoration command/status in QA report |
| Keep QA artifacts synchronized and docs valid | Records current and docs check passes | Rendered paper table and `scripts/verify.sh docs` |

## Plan

1. [x] Create the dedicated worktree, issue branch, and this progress record; inspect issue #105 and existing FS evidence.
2. [ ] Establish safe VM-lab preflight: verify no owner claim, check VM/snapshot/target state, and read configured discovery networks before claiming a live case.
3. [ ] Select the first unclaimed FS case whose prerequisites are satisfied; inspect its full requirements and known gaps, execute it (repeating a failure once only), and preserve sanitized evidence.
4. [ ] Repeat step 3 for at most five total QA rounds, restoring each mutation before another destructive/live case.
5. [ ] Create the sanitized run report; update traceability, regenerate the paper table, run docs verification, and checkpoint the result.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Created tracking issue #105, dedicated worktree/branch, and QA progress plan. | Issue and existing FS report/traceability inspected. | Ready for safety preflight; no case claimed yet. |

## State for the next session

- Last check run (exact command): `gh issue view 105 --json number,title,state,url,body,labels`
- Result (first failing lines, or "green"): Issue #105 is open and has the intended FS QA finish condition.
- Hypothesis: The VM lab may be available for the next untested FS case, J4-01, after strict safety preflight.
- Next action (one specific step, not "continue"): Run `scripts/vmlab status` and inspect the configured discovery-network state before claiming J4-01.

## Decisions and notes

- This is a QA-finding loop: do not modify product code or weaken expectations.
- Existing cases passed in issue #100 remain evidence only; no status is changed without an observed run on this QA round.
- The initial tree on `main` contained uncommitted QA artifact changes that have since merged in `a8fa51f7`; this dedicated worktree starts clean from `origin/main`.
- Human cases remain untested absent attributable human evidence.
