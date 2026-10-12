# QA finding loop

Read `AGENTS.md`, `docs/qa/QA_Journeys_and_Scope.md`, the master test plan
(`docs/qa/QA_Test_Plan.md`), `docs/qa/Requirements_Traceability.md`,
`docs/qa/QA_Paper_Test_Case_Tables.md`, `docs/test-runs/README.md`, and the QA rules in
`spec files/Agent_Workflow_and_CI.md`. This workflow finds and retests defects;
it never fixes product code or weakens the case's expected result.

## Prepare a queue before execution

Every new QA run starts with preparation, not execution. Read
[`QA_Run_Queues.md`](../../docs/qa/QA_Run_Queues.md). A user may queue multiple
named sets in one request, each with one ISO characteristic (FS, PE, IC, RE, SE),
an owner, and optionally a subset of case IDs. Select only `untested` and `retest`
cases from the current plan and traceability matrix. Do not include passed cases
or filed failures, silently broaden scope, or add prerequisite cases from another
set or characteristic. Explicit IDs must also be pending and match the set's ISO.

Use `python3 -I scripts/qa_queue.py prepare` with repeated `--set` arguments and
a new `--output` filename. This saves a fixed JSON queue and a Markdown preview.
Show the full case list for every set before starting: set name, ISO, owner, case
ID, module, scenario, environment/executor, current status, prerequisites and
existing notes. Point out HUMAN cases, destructive actions, missing prerequisites
and shared-lab work. Queue preparation does not execute tests, provision/reset a
lab, file issues, change traceability statuses, or claim cases or lab ownership.

Wait for the user's explicit start command naming the queue and set. Displaying
the preview, elapsed time, or preparing another set is not permission to start.
After one set ends, wait for an explicit start for the next set; never automatically
drain the queue. Sets assigned to a teammate are handoffs, not permission for this
agent to execute them or message the teammate.

Assignments must be disjoint within a queue; the tool rejects duplicate IDs and
set names. Share the preview through the team's existing coordination channel
and compare it with other testers' queues/progress before execution. A local
queue cannot enforce reservations across separate checkouts or machines. Owners
must separately agree on access to each test environment. Testers on different
machines may run in parallel when each uses a separate appliance and targets;
each still runs one appliance at a time locally. If their machines connect to the
same appliance or targets, require exclusive access to that shared environment.
Use the same reviewed queue and agreed source revision, record each deployed
application SHA, and verify prerequisites on each tester's own environment.
Another tester's successful case does not establish this environment's setup.
Isolated MOCK work may run independently when its prerequisites do not require
the shared lab. Keep separate tracking issues, branches and attributable reports;
preserve both testers' result updates when combining their documentation PRs.

## Start or resume

On an explicit start, run `python3 -I scripts/qa_queue.py check --queue <file>
--run <set>` against current sources, then `show` the same set. If procedures,
statuses or notes changed, prepare and show a replacement queue and wait for a
new explicit start. Never silently substitute cases or include newly pending IDs.
The check confirms scope freshness, not environment readiness or lab ownership.

Use a dedicated checkout and an `issue-<n>-qa-run` branch for the tracking issue.
Use `.agent/progress/issue-<n>.md` and the existing TEMPLATE and checkpoint script:
this deliberately reuses the validated issue-file format rather than an unchecked
`qa-run.md` progress filename. Record the claimed case, tested SHA, environment,
restoration steps, evidence location, issue links and next action. Resume by reading
that file, checking git status and re-running the last safe check. Never rerun a
mutating test without checking the current lab state first.

Record the queue path, set name, owner and exact case IDs in the tracking issue
and progress file. On resume keep that fixed scope: compare remaining cases with
their saved procedures/status/notes, and use progress/report evidence for completed
cases (their result changes are expected). Re-preview changed remaining scope and
wait for an explicit start before continuing it. Preserve the five-round limit;
larger sets remain queued/in progress across sessions. Record blocked prerequisites
without adding their cases; request a separately prepared set if needed.

Owner lab claims override earlier general approval. If another person owns the lab,
do only isolated tests and document the live checks pending; do not connect to it.
HUMAN cases remain untested until a person supplies attributable evidence.

## Each round (maximum five per session)

1. Check merged-fix candidates as below only within the explicitly started set,
   then select its next unclaimed `retest` or `untested` row whose prerequisites
   are satisfied. Never select outside the saved case list. Record the claim before work.
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
