# Issue #285: System Refinement Prune superseded QA queue versions into an archive folder

Branch: `claude/workissue-workflow-issue-285-gd7clf`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

- [ ] Every file in `docs/qa/queues/` classified: keep / archive / untouched (`progress/`, `cards/`)
- [ ] Archived files moved with `git mv` into `docs/qa/queues/archive/`; every inbound link repointed
- [ ] `queues/README.md` rewritten as a short state table: current, consumed, archived
- [ ] `QA_Run_Queues.md` shrunk to match
- [ ] `scripts/verify.sh docs`, `scripts/test_qa_queue.py`, `test_qa_pilot.py`, `test_qa_coverage.py` pass
- [ ] PR lists every moved path and every repointed link

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Depends on inventory D3-1 | classification | Inventory is the comment on #284; per-file scan done here |
| Classify each file | item 1 | table under Decisions and notes |
| Move with git mv, repoint inbound links | item 2 | `git status` renames; `scripts/verify.sh docs` link check |
| Rewrite queues/README.md | item 3 | file review |
| Shrink QA_Run_Queues.md | item 4 | `wc -l`, review |
| Tests pass | item 5 | the commands named |
| PR lists moves and links | item 6 | PR body |
| Superseded versions archived, not deleted | item 2 | `git diff --stat -M` shows renames only |
| Repointing in test-runs/ allowed for moves only | item 2 | no test-runs/ file needs a repoint |

## Plan

1. [ ] Classify and record the table (this file)
2. [ ] `git mv` archive set into `docs/qa/queues/archive/`; repoint `Module_2-9_Adapter_Review.md`
3. [ ] Rewrite `docs/qa/queues/README.md`
4. [ ] Shrink `docs/qa/QA_Run_Queues.md`
5. [ ] Run docs/queue/pilot/coverage checks; update Implementation_Status if needed
6. [ ] Finish: delete progress file, push

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan written | none | n/a |

## State for the next session

- Last check run (exact command): none yet
- Result: n/a
- Hypothesis: moving files changes the hashes of docs frozen by qa_queue.references(); check tests
- Next action: step 2, git mv the archive set

## Decisions and notes

- No `team-*`, `progress/` or `cards/` files exist in `queues/`, so nothing to leave untouched.
- Keep: next-permissions (.json, .md, -execution.md), issue-211-ss04-recheck-v2 (.json, .md),
  today-ss04, today-ss04-v3, today-ss04-v4 (cited by test-run reports), modules-2-9-adapters-v12,
  modules-2-9-card-drafts-v5 (read by qa_queue.py), README.md.
- Archive: issue-211-ss04-recheck-v1, today-ss04-v2, modules-2-9-adapters-v1..v11,
  modules-2-9-v2..v10, modules-2-9-card-drafts-v1..v4 and v6 (json + md pairs where they exist).
- card-drafts-v6 is newer than v5 but nothing reads or cites it; archived, flagged for the owner.
- PR #295 (issue 284) is open and also touches docs/qa and the coverage register; expect overlap.
