# Workflow: fix-found

Run the fix loop for `qa-found` issues. The fix loop picks candidates, implements fixes, and opens pull requests, keeping the traceability matrix up to date for re-testing.

## Constraints
- Max 5 rounds per session.
- At most 3 PRs per session.
- Keep agent state in `.agent/progress/fix-found.md`.
- All fixes must first add or update a test that fails for the right reason.
- QA-found defects are verified by their original test case (or a regression).
- Mark newly found defects with label `qa-found`.
- Do not log known gaps documented in `docs/qa/QA_Journeys_and_Scope.md`.
- Use `scripts/vmlab` and `scripts/lab` for VM/Docker environments. Limit network scanning strictly to `10.77.0.0/28`. Use credentials from `.local/share/pinpoint-vmlab-*` but never print them.

## Fix Loop Steps
1. Create or resume `.agent/progress/issue-85.md` (not `fix-found.md`; the progress file is issue-scoped).
2. List candidates: `gh issue list --label qa-found --state open --limit 100 --json number,title,labels,createdAt | jq -r '.[] | select(.labels[].name == "needs-decision" | not) | "\(.number)|\(.title)|\(.createdAt)"' | sort -t'|' -k1,1`.
3. Filter and rank: highest severity first (rubric in `docs/qa/QA_Journeys_and_Scope.md`), then oldest. Skip — and record the skip reason in `.agent/progress/issue-85.md` — any issue that:
    - has `needs-decision` label.
    - has an open PR (`gh pr list --state open --search "Closes #<n>"`).
    - has an active `issue-<n>-*` working branch (`git branch -a --list 'issue-*-*'`).
    - lacks a defined case ID (no `J*`/`PT*`/`BB*` reference in the title or body).
    - lacks a finish condition.
    - touches a sensitive module (see `spec files/Engineering_Standards.md`).
    - needs a migration, new dependency, or live Nagios integration (needs a person).
4. If this session already has 3 PRs or this case has had 2 failed fixes, stop and record the reason (3-PR cap / 2-failed-fix stop) in the progress file.
5. If a tool denies permission, stop immediately; do not switch tools to bypass. Record the denial.
6. Run `work-issue.md` for the chosen issue in a new branch `issue-<n>-<slug>`.
7. Testing: The fix must pass the original failing QA case (or a new regression test). Repeat once if it fails; if the repeat differs, mark inconclusive.
8. Opening PR: `gh pr create --title '<case>: fix' --body 'Closes #<n> • Test case <id>'`. Do not merge; leave it open for human review.
9. Verification: CI must be green (run `scripts/verify.sh all` or at least `docs` / the relevant stage).
10. Retest: After the PR is merged (`gh pr view <n> --json mergedAt,merged` confirms) and the issue is marked `closed` with the PR cross-referenced, update the traceability row to `retest`; do not retest on unmerged or unreferenced closure.
