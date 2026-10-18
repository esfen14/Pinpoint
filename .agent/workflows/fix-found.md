# Fix QA findings

This queue delegates each fix to [work-issue.md](work-issue.md), without replacing
any of its steps, verification requirements or stop conditions. Read `AGENTS.md`,
the current module catalog, historical evidence review and owning specifications first.

## Start or resume

Use a dedicated checkout and an `issue-<tracking-number>-<slug>` branch. Keep queue
state in `.agent/progress/issue-<tracking-number>.md` using `TEMPLATE.md`; each chosen
finding has its own issue-scoped progress file in its own worktree. Never hardcode
issue #85 as the tracking issue for future sessions. Record candidates, skip reasons,
case IDs, PR count, failed-fix history, evidence and next action; checkpoint after
each round. Resume existing work instead of creating a competing branch or PR.

The severity rubric is in `spec files/Agent_Workflow_and_CI.md`: High, Medium, Low.
Existing labels map `Top Priority` to High, `Medium Priority` to Medium, and
`Low Priority` to Low. If neither the issue body nor a label establishes severity,
record it as blocked for triage; conflicting severities also need a decision.

## Select the queue

Fetch all pages, including issue bodies and labels (REST also returns PRs, so filter
those out). These are read-only commands; replace NUMBER with an observed issue ID.

```bash
gh api --paginate 'repos/esfen14/Pinpoint/issues?state=open&labels=qa-found&per_page=100' \
  --jq '.[] | select(.pull_request == null) | {number,title,body,labels:[.labels[].name],created_at,html_url}'
git fetch -q origin
gh issue view NUMBER --json number,title,body,labels,comments,state,url
gh api --paginate repos/esfen14/Pinpoint/issues/NUMBER/timeline \
  --jq '.[] | select(.event == "cross-referenced") | .source.issue.html_url'
gh api --paginate 'repos/esfen14/Pinpoint/pulls?state=open&per_page=100' \
  --jq '.[] | {number,title,body,html_url,head:.head.ref}'
git branch -a --list 'issue-NUMBER-*' 'remotes/origin/issue-NUMBER-*'
git worktree list --porcelain
```

Inspect cross-references and open PR bodies for actual links to the finding,
including `Fixes`, `Resolves` and `Closes`; a search for only `Closes #NUMBER` misses
valid fixes. Record every skipped candidate and reason before ordering eligible
candidates by severity descending, then `created_at` ascending (number breaks ties).
Skip a candidate that:

- has `needs-decision`;
- has an open fix PR, or an `issue-NUMBER-*` branch with work: record the existing
  worktree/PR as the resume target rather than creating a duplicate;
- has no valid case ID in the current module catalog or no explicit finish condition
  covering that failing case;
- touches a sensitive module, needs a migration, new dependency, live Nagios or a
  secret without the required authorization; record the question for the owner;
- belongs to the installer: write sanitized notes for its owner, do not fix it here.

Known gaps are linked, not refiled. Never alter the QA plan to make a failure pass;
a disputed case needs a separate documentation issue labelled `needs-decision`.

## Fix and open for review

1. Stop after five total rounds per session or three rounds on the same failure,
   as in `work-issue.md`. At most three PRs may be opened per session, including
   drafts. Persist the count so a resume cannot reset it.
2. If two merged fixes have failed retesting the same case, run
   `gh issue edit NUMBER --add-label needs-decision`, record both PRs and failed
   retest reports, and stop on that case. Failed attempts before merge still obey
   the work-issue three-round limit; they are not two merged fixes.
3. If any permission is denied (filing, PR creation, lab access), stop the loop and
   record the action and denial. Do not switch tools or accounts to bypass it.
4. Follow `work-issue.md` exactly in the finding's own worktree and issue branch:
   test first, implement one fix per PR, verify the failing case or regression,
   update specs and progress, checkpoint, and run `scripts/verify.sh all`.
   Lab retests require explicit authorization for that case in the issue and the
   `qa-run.md` safety preflight; no libvirt harness. Never print credentials.
5. Use the repository PR template. Put the actual case ID and `Closes #NUMBER` in
   a reviewed body file. The work-issue finish rules determine ready versus draft:
   `gh pr create --base main --title 'CASE: fix description' --body-file /tmp/fix-body.md`
   (add `--draft` when unfinished). Never merge. Record the actual URL and inspect
   CI with `gh pr checks PR_NUMBER`; local verification alone does not prove CI green.

## Return a merged fix to retest

Use the [qa-run.md retest handoff](qa-run.md#retest-handoff). Check the actual issue
state, timeline closing event, merged PR, and case coverage. A closed issue or a
synthetic documentation PR alone is not proof of a product fix. Do not use the
unsupported `merged` JSON field or assume a PR number equals the issue number.

```bash
gh issue view NUMBER --json state,url,body
gh api --paginate repos/esfen14/Pinpoint/issues/NUMBER/timeline \
  --jq '.[] | select(.event == "closed" or .event == "cross-referenced")'
gh pr view PR_NUMBER --json state,mergedAt,mergeCommit,body,url
gh pr diff PR_NUMBER
```

Only after the fix is merged and the finding closed, record affected current case
eligibility as `retest required` in a reviewer-bound evidence record, retaining the
original failure and recording the issue, PR, merge SHA and evidence. Prepare a
new reviewed version-2 queue with purpose `retest`; do not overwrite human verdicts. Confirm that the lab contains the merge before the next qa-run.
A failed retest links the original finding (reopen it if appropriate), increments
its failed-fix count, and never creates a disconnected duplicate issue. A synthetic
handoff must use clearly separate scratch evidence; it cannot certify a product case.

## Written boundary checks

Run these checks with scratch queue/progress data; do not create real defects merely
to exercise a limit. Record the input, selected action and expected result.

| Input | Required action / expected result |
|---|---|
| High newer issue, Low older issue, Medium issue | Select High, then Medium, then Low; oldest first within each severity |
| Candidate has both `qa-found` and `needs-decision` | Skip once with reason, never select because another label differs |
| Candidate linked by `Fixes #NUMBER` to an open PR | Skip and record existing PR/resume target |
| Progress already records three opened PRs | Stop before a fourth `gh pr create` |
| Case has two merged fixes, each followed by a failed retest | Label `needs-decision`, record both failures, stop on case |
| Issue creation, PR creation or lab command denied | Record denial and stop; no retry through another tool |
| Closed issue with an unmerged PR | Keep the original failure; no retest handoff |
| Closed issue with merged documentation-only/synthetic PR | No product retest; scratch demonstration only |
| Closed finding with merged actual fix and recorded case coverage | Record retest eligibility; preserve failure evidence |

## Session report

One line per issue: PR link, skipped with reason, or blocked with the precise
question. Keep unfinished work draft and checkpoint its next action.
