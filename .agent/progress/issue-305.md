# Issue #305: Document what each lab/ file serves

Branch: `issue-305-lab-readme-owners`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] `lab/README.md` maps every file to its owner script and lab
- [ ] Move decision recorded; no files moved, so no broken links and no affected-test changes
- [ ] `scripts/verify.sh all` passes

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| README states owner script and lab per file or group | item 1 | review of lab/README.md against git grep |
| Decide whether to move shared helpers | item 2 | decision in README and notes |
| verify.sh all after any move | item 3 | scripts/verify.sh all |
| No broken links if files move | item 2 | scripts/check_doc_links.py |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] Rewrite lab/README.md with per-file owner map and move decision (lab/README.md)
2. [ ] Run verify docs then all

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan | n/a | n/a |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: README-only change suffices
- Next action (one specific step, not "continue"): rewrite lab/README.md

## Decisions and notes

Choices made, things ruled out, questions for a person.

Decision: do not move files. Queue JSONs under docs/qa/queues hash lab/unix_web_proxy.mjs and qa_queue.py checks it; moving invalidates reviewed queues. Document owners instead.
