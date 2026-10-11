# QA finding loop

Read `AGENTS.md`, `docs/qa/QA_Journeys_and_Scope.md`, the master test plan
(`docs/qa/QA_Test_Plan.md`), `docs/qa/Requirements_Traceability.md`,
`docs/qa/QA_Paper_Test_Case_Tables.md`, `docs/test-runs/README.md`, and the QA rules in
`spec files/Agent_Workflow_and_CI.md`. This workflow finds and retests defects;
it never fixes product code or weakens the case's expected result.

## Start or resume

Use a dedicated checkout and an `issue-<n>-qa-run` branch for the tracking issue.
Use `.agent/progress/issue-<n>.md` and the existing TEMPLATE and checkpoint script:
this deliberately reuses the validated issue-file format rather than an unchecked
`qa-run.md` progress filename. Record the claimed case, tested SHA, environment,
restoration steps, evidence location, issue links and next action. Resume by reading
that file, checking git status and re-running the last safe check. Never rerun a
mutating test without checking the current lab state first.

Owner lab claims override earlier general approval. If another person owns the lab,
do only isolated tests and document the live checks pending; do not connect to it.
HUMAN cases remain untested until a person supplies attributable evidence.

## Each round (maximum five per session)

1. Check merged-fix candidates as below, then select the next unclaimed `retest`
   or `untested` row whose prerequisites are satisfied. Record the claim before work.
2. Read the full case, applicable spec and implementation-status gap. Status inventory
   does not override requirements. On an unresolved conflict, search for an existing
   `needs-decision` issue, link it or file one, and continue another unblocked case.
3. Check environment safety. Unit tests must not invoke integration/e2e harnesses.
   Lab cases require exclusive ownership, authorized operations, a known baseline,
   restoration plan and terminal preceding discovery. Only `10.77.0.0/28` may be
   scanned. Read back configured networks and reject any outside range before start;
   if the guard cannot be established, stop that case. This manual preflight is not
   an atomic enforced scan guard; until one is implemented, unattended scan starts
   remain blocked. Never use the libvirt harness.
4. Execute the written case, preserving sanitized observations. A command timeout,
   successful HTTP response alone, mock result or partial UI run is not a full pass.
   On failure restore safely, repeat once, and record both outcomes. If the repeat
   differs, record inconclusive evidence and keep the row untested, not pass.
5. Before filing, search both open and closed issues by case ID and symptom:
   `gh issue list --state all --search 'J2-09' --limit 100 --json number,title,state,url`
   (replace ID). Inspect matches and the known-gap list. Link known gaps rather than
   filing duplicates. Installer-owned failures become sanitized owner notes.
6. For a repeatable new application failure, use the Task template's sections:
   case ID, expected/observed behavior, exact tested SHA, sanitized reproduction and
   evidence, both attempts, severity, finish condition and narrowly allowed lab retest.
   `gh issue create --label qa-found --title '<case>: <symptom>' --body-file <sanitized-file>`
   Record the returned URL; never invent one. On denied permission stop, record it,
   and do not switch tools to bypass the denial.
   A deliberately false scratch assertion used only to validate this workflow is
   expected harness evidence, not an application defect: record both attempts in a
   sanitized synthetic report, remove the assertion, and do not create a `qa-found`
   issue or change the real case's traceability status.
7. Create a report with `scripts/new_test_run.sh <unique-slug> docs/qa/QA_Test_Plan.md`,
   fill actual results, and index it in `docs/test-runs/README.md`. Raw auth state,
   traces, screenshots and database extracts stay outside committed evidence.
8. Synchronize the result artifacts before checkpointing:
   - Update `docs/qa/Requirements_Traceability.md`: `pass` only for full observed
     coverage; `fail-filed` with the real issue and evidence; `needs-decision` with
     the question. Skipped/blocked and partial observations stay `untested` with
     reasons. `won't-do` requires an explicit scope decision, not an agent's inability
     to execute. Every changed row links the new report and, where applicable, the
     finding or decision issue.
   - Regenerate, never hand-edit, `docs/qa/QA_Paper_Test_Case_Tables.md` with
     `python3 -I scripts/render_qa_case_tables.py --write`. Inspect the rendered
     result so its case status and note match the traceability row.
   - Restore the case's mutations, run `git diff --check`, then run
     `scripts/verify.sh docs`. A failed render or docs check blocks the checkpoint;
     correct the records rather than leaving one artifact stale.
9. Update progress with the report path, traceability status, paper-table regeneration
   and docs-check result, then checkpoint with
   `scripts/agent_checkpoint.sh <n> '<case and observed result>'`.

## Retest handoff

Query all closed findings, without the CLI default 30-result limit:

```bash
gh api --paginate 'repos/esfen14/Pinpoint/issues?state=closed&labels=qa-found&per_page=100' \
  --jq '.[] | select(.pull_request == null) | {number,title,html_url}'
```

For each matching `fail-filed` row, inspect its issue timeline:

```bash
gh api --paginate repos/esfen14/Pinpoint/issues/NUMBER/timeline \
  --jq '.[] | select(.event == "cross-referenced") | .source.issue.html_url'
gh pr view PR_NUMBER --json state,mergedAt,mergeCommit,body,url
```

Inspect the timeline closing event and PR diff to verify the closing reference and
actual fix (`gh pr diff PR_NUMBER`); this also works with older gh versions.
Replace NUMBER/PR_NUMBER from the finding and linked fix, not a guessed search hit.
Only a merged PR actually fixing/closing the finding triggers `retest`; closure as
unreproducible, duplicate or out-of-scope does not establish a fix. Record merge SHA,
issue, PR and affected cases; confirm the test environment contains that SHA before
execution. Preserve original failure evidence. A failed retest links the original
finding; after two failed fixes for the same case, mark needs-decision and stop on it.

## Complete the tracking issue and report

Stop at five rounds, denied permissions, unsafe/unavailable environment or an owner
lab claim. Checkpoint with exact unfinished work; leave PR draft. Continue unrelated
safe cases when only a product decision is blocking. Never merge a PR.

The finding pass is accounted for when every in-scope row is `pass`, `fail-filed`,
`needs-decision` or explicitly authorized `won't-do` (none untested/retest). This is
not release approval: unresolved failures and decisions still need human triage.

For a tracking issue that covers the whole test plan, do not treat that accounting
shortcut as completion: every master-plan case, including HUMAN cases, must have the
result and attributable evidence required by the tracking issue's finish condition.
Before resolving that issue, verify that every executed case has a sanitized run report
and index entry, its traceability row is current, the paper table was regenerated, and
`scripts/verify.sh docs` is green. Re-read the issue and its comments; if its finish
condition is narrower than the whole plan, close only the work it actually covers.

When the tracking issue's finish condition is fully met, open the documentation PR
with `Closes #<n>` in its body and the report, matrix and rendered-table changes in the
diff. GitHub automatically closes the tracking issue when the PR merges; do not close
it directly or claim completion while the PR is draft, checks are red, a HUMAN result
is missing, or any required row is still `untested` or `retest`. Never merge the PR. Report
case/result/evidence/issue and restoration state, plus what was not verified.
