# Issue #318: Update lab documentation to the #306 decision

Branch: `issue-318-lab-docs-decision`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] `docs/manuals/Local_Lab.md`, `lab/README.md` and `spec files/Implementation_Status.md` match the #306 decision and the follow-up issues (#315, #316, #317)
- [ ] `scripts/verify.sh docs` passes

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Three documents state the lab is kept as the headless lane | Item 1 | `grep -n -i "headless" docs/manuals/Local_Lab.md lab/README.md "spec files/Implementation_Status.md"` |
| They state it is not in CI | Item 1 | `grep -n "not in CI\|Not in CI" ` on the three files |
| They state it tracks the installer through the drift guard | Item 1 | `grep -n "check-drift"` on the three files |
| They state where the plugin/alert smoke gap stands | Item 1 | `grep -n "#315"` on the three files |
| Update `spec files/Agent_Workflow_and_CI.md` if its lab row changes | Item 1 (conditional) | Read the row; edit only if it contradicts or omits the decision |
| `scripts/verify.sh docs` passes | Item 2 | `scripts/verify.sh docs` |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] `docs/manuals/Local_Lab.md`: add the role and decision near the top (headless lane, not in CI, tracks the installer through audit #316 and `check-drift` #317); rewrite "Status" (no longer "Spike"; plugin/alert gap closed by #315, mail checks from #316, what stays unverified, NCPA in #322)
2. [ ] `lab/README.md`: add a short "Role of the local lab" section with the same four facts and links
3. [ ] `spec files/Implementation_Status.md`: update the "Local lab" row (decision, stale "actual mail delivery unverified", and the "then consider a CI job" remaining-work cell)
4. [ ] `spec files/Agent_Workflow_and_CI.md`: add the decision to the "Local lab (fast lane)" row if it does not already state it
5. [ ] Run `scripts/verify.sh docs`, then `scripts/verify.sh all`; prove each coverage row

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan written | none | n/a |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: documentation only; no code or test changes needed
- Next action (one specific step, not "continue"): edit the top and the "Status" section of `docs/manuals/Local_Lab.md` (plan step 1)

## Decisions and notes

Choices made, things ruled out, questions for a person.

- Decision source: owner comment on #306 (keep as headless lane, keep in step with the installer, not in CI because it would slow every PR; options 2 and 3 not pursued).
- Follow-ups all merged: #315 (PR #320), #316 (PR #321), #317 (PR #323).
- Documentation only, so there is no failing test to write first; the proof is `scripts/verify.sh docs` and the greps above.
- The committed #315 run report says 16 of 16 smoke checks; PR #321 reports 20 of 20 after the mail checks, with no committed report. The docs will cite each number with its source.
- `scripts/lab sync` ran OK in the #306 evidence table (2026-11-10); `scripts/lab ui` was not run.
