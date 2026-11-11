# Issue #304: Update live e2e specs that still expect the removed five-VM lab addresses (10.77.0.x)

Branch: `issue-304-live-e2e-lab-addresses`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

- [ ] No `10.77.0.` literal remains in `client/e2e/` (offline test proves it)
- [ ] host-recipients specs match hosts on the current labs (demo 10.77.1.0/27, local 10.78.0.0/24)
- [ ] remote-restart spec reads its target IP from the environment and skips with a reason if unset
- [ ] `Agent_Workflow_and_CI.md` scan-range wording matches the current lab; `scripts/vmlab` guard checked

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Decide address source per spec, update values | items 2, 3 | test_playwright_safety.py; spec diffs |
| Reconcile `10.77.0.0/28` wording/guard only if stale | item 4 | vmlab already `10.77.1.0/27` (not stale); spec text edited; verify.sh docs |
| No `10.77.0.` literal in client/e2e | item 1 | offline test |
| Specs run against current lab or marked not runnable with reason | items 2, 3 | Not run live (hard limit); remote-restart skip reason explicit |

## Plan

1. [ ] Test first: no `10.77.0.` in client/e2e (`scripts/test_playwright_safety.py`)
2. [ ] Add `client/e2e/labAddresses.ts`; use it in both host-recipients specs
3. [ ] remote-restart spec: target IP from `PINPOINT_ISSUE182_TARGET_IP`; update `server/tests/plans/REMOTE_RESTART_ACCEPTANCE.md`
4. [ ] Update `spec files/Agent_Workflow_and_CI.md` safety boundary wording
5. [ ] `scripts/verify.sh docs` and `frontend`

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan | n/a | n/a |

## State for the next session

- Last check run (exact command): none
- Result (first failing lines, or "green"): n/a
- Hypothesis: spec edits are small
- Next action: step 1, write failing test

## Decisions and notes

- `scripts/qa_pilot.py` `10.77.0.0/28` is a frozen baseline check for the retired controlled deployment; out of scope, not touched.
- Specs not run live (hard limit).
