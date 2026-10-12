# Preparing ISO-scoped QA runs

Prepare the scope first, coordinate with your teammate, then explicitly start one
named set. The queue tool reads the master plan and traceability matrix and selects
only pending work (`untested` or `retest`). It does not run tests or change results.
Execution follows [the QA finding workflow](../../.agent/workflows/qa-run.md).

## Using an agent: copyable instructions

You can give these instructions directly to your coding agent; running the queue
commands yourself is optional. The agent reads the workflow, prepares the saved
queue and shows the case lists before execution.

To prepare different characteristics for two testers:

> Follow `.agent/workflows/qa-run.md`. Prepare a queue of pending FS cases in a
> set named `my-fs` owned by me, and pending SE cases in a set named `teammate-se`
> owned by my teammate. Show both full case lists, save the JSON queue and Markdown
> preview, and give me their paths. Wait for my explicit start command.

To split one characteristic instead:

> Follow `.agent/workflows/qa-run.md`. Prepare two FS sets: `my-fs`, owned by me,
> containing J2-03, J7-07 and J7-08; and `teammate-fs`, owned by my teammate,
> containing J8-01, J8-02 and J8-03. Include only pending cases, show both lists
> and give me the saved queue and preview paths. Wait for my explicit start command.

These case IDs are examples. If an explicit case has already passed or is otherwise
not pending, the agent must report it rather than silently replace it. Review the
lists with your teammate and settle prerequisites and shared-lab access.

To start your own set after review:

> Follow `.agent/workflows/qa-run.md`. Start only `my-fs` from `<queue-path>`,
> using tracking issue #NUMBER. Check the saved scope against current sources and
> follow the environment preflight before executing.

Replace `<queue-path>` with the actual JSON path returned during preparation and
`#NUMBER` with the run's real tracking issue. Each tester uses a dedicated checkout
and issue-scoped progress as required by the workflow.

### Message to give your teammate

Copy this handoff and fill in the actual paths, assigned set, tracking issue and
agreed lab window:

> Your QA assignment is set `<assigned-set>` in `<queue-path>`. Review the case
> list in `<preview-path>`. Use your own checkout with the queue tool, current QA
> plan, traceability matrix and workflow available. Give your agent this instruction:
> "Follow `.agent/workflows/qa-run.md`. Show only `<assigned-set>` from
> `<queue-path>`, check its scope against current sources, and wait for my explicit
> start command." After reviewing it, tell the agent: "Start only `<assigned-set>`
> from `<queue-path>`, using tracking issue #NUMBER." Our agreed shared-lab window
> is `<lab-window>`. Coordinate ownership before connecting to the appliance; stop
> after your assigned set and report results and restoration state.

Share both the JSON queue and Markdown preview through your team's existing
handoff channel, or make them available in the shared repository. Files saved in
your checkout are not automatically available in your teammate's checkout. Both
testers should use the same reviewed queue; independently preparing fresh queues
can select overlapping cases. If the teammate's source versions differ, the scope
check may require a replacement preview and another explicit start.

## Queue multiple characteristics

From the repository root:

```bash
python3 -I scripts/qa_queue.py prepare \
  --set my-fs:FS:me \
  --set teammate-se:SE:teammate \
  --set my-ic:IC:me \
  --output docs/qa/queues/coordination-01.json
```

Each `--set` is `NAME:ISO:OWNER`. Names must be unique and use letters, numbers,
underscores or hyphens. Supported characteristics are FS, PE, IC, RE and SE.
The command saves `coordination-01.json` and a sibling `coordination-01.md`, and
prints every set's full case list. The preview includes the module, scenario,
environment, executor, status, prerequisites and existing evidence note.

The saved list is fixed at preparation time. New pending cases do not silently
join it. Sets appear in the requested order; cases use master-plan order, with
execution constrained by prerequisites. An empty selection is an error.

## Split one characteristic between testers

Use optional comma-separated case IDs to make disjoint subsets:

```bash
python3 -I scripts/qa_queue.py prepare \
  --set my-fs:FS:me:J2-03,J7-07,J7-08 \
  --set teammate-fs:FS:teammate:J8-01,J8-02,J8-03 \
  --output docs/qa/queues/coordination-02.json
```

All explicit IDs must exist, match the ISO and still be pending. The tool rejects
overlap, including selecting the entire FS group alongside a smaller FS subset.
Use a new filename to revise a queue; existing queues and previews are never
overwritten. Keep planning snapshots under `docs/qa/queues/` if you want them in
the shared repository, or choose a local path for temporary coordination. Queue
snapshots are planning records, not test evidence or traceability results.

## Review, coordinate and start

```bash
python3 -I scripts/qa_queue.py show \
  --queue docs/qa/queues/coordination-02.json
python3 -I scripts/qa_queue.py check \
  --queue docs/qa/queues/coordination-02.json --run my-fs
```

Share the Markdown preview with your teammate. Agree on case assignments and lab
ownership before starting. A queue checks overlap within its own file; it is not
a distributed lock across teammates' checkouts. HUMAN cases need attributable
human evidence. VM sets share one appliance even when their ISO tags differ, so
they must run with exclusive lab ownership. MOCK cases may be independent.
Review destructive actions and restoration steps in the full master-plan cases.

Give the agent an explicit instruction, for example:

> Follow `.agent/workflows/qa-run.md`. Start only `my-fs` from
> `docs/qa/queues/coordination-02.json`, using tracking issue #NUMBER.

Preparing or showing the queue never starts it. Finishing one set does not start
the next. The workflow checks the chosen set against current sources before
execution. Changed procedures, statuses or notes require a replacement preview
and a new explicit start. Unrelated sets may change without invalidating this set.
The JSON is authoritative for scope; `show` renders it again if a Markdown copy
was edited.

Prerequisites from other ISO groups are shown but never automatically added or
run. Verify existing evidence and lab state; record blocked cases if prerequisites
are missing. Prepare a separate prerequisite set when necessary. Lab reset, scans,
credentials, claims and run reporting retain their existing workflow requirements.

Record the queue/set, owner, case IDs and results in issue-scoped progress. After
five rounds, checkpoint remaining work and resume the same set rather than picking
cases outside it. On resume compare the remaining cases against the saved scope;
completed result changes are expected and must have report/progress evidence.
Actual results still go in [test runs](../test-runs/README.md), followed by the
traceability and generated-table updates.
