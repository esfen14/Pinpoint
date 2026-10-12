# Sharing QA work between two testers

Use your agent to make one list of assignments, share it with your teammate, then
each start your own assignment on your own machine. You do not need to write JSON
or run terminal commands yourself.

The agent follows [the QA workflow](../../.agent/workflows/qa-run.md).
It waits for an explicit start before running tests.

## What the names mean

| Name | Meaning |
|---|---|
| Test case | One test from the QA plan, such as `J2-03`. |
| ISO characteristic | A group of tests: FS = Functional Suitability, PE = Performance Efficiency, IC = Interaction Capability, RE = Reliability, SE = Security. |
| Pending | A case marked `untested` or `retest`. Passed cases and filed failures are excluded. |
| Set | One tester's named assignment for one ISO characteristic, such as `paeng-fs`. You can split an ISO group into smaller sets. |
| Queue | One saved file containing all the sets you prepared together. |
| Owner | The tester assigned to a set. This label does not reserve a test machine. |
| Queue path | The location of the generated JSON file inside your repository, for example `docs/qa/queues/team-01.json`. |
| Preview | The generated Markdown file, such as `team-01.md`, containing readable case lists. |
| Prerequisite | Something a case needs before it can run, such as discovered devices or an enabled plugin. |
| Tracking issue | The GitHub issue used to record a tester's progress and results. Each tester uses a separate issue and branch. |

## 1. Have your agent prepare the assignments

Copy this prompt to your agent. Change the tester names and ISO groups as needed:

> Follow `.agent/workflows/qa-run.md`. Prepare pending FS cases in a set named
> `paeng-fs`, owned by Paeng, and pending SE cases in a set named `teammate-se`,
> owned by my teammate. Save the queue as `docs/qa/queues/team-01.json`. Show the
> full case list for each set, including modules, prerequisites and environments.
> Tell me where the JSON and Markdown files were saved. Wait for my explicit start.

The agent generates both `team-01.json` and `team-01.md`. Those files do not exist
until preparation succeeds. Preparing assignments does not start tests.

Review the preview together. It shows who owns each set and exactly which cases
are planned. Some cases may need setup or human participation before they can run.

To divide the same ISO group instead, give specific case IDs:

> Follow `.agent/workflows/qa-run.md`. Prepare two FS sets: `paeng-fs`, owned
> by Paeng, with J2-03, J7-07 and J7-08; and `teammate-fs`, owned by my teammate,
> with J8-01, J8-02 and J8-03. Save them as `docs/qa/queues/team-02.json`, show
> both case lists, and wait for my explicit start.

These IDs are examples. The agent reports an ID that is no longer pending rather
than replacing it. The tool rejects assigning the same case twice in one queue.
Use a new filename when changing assignments; existing queue files are preserved.

## 2. Share the generated files with your teammate

Choose either way:

- **GitHub:** commit and push the generated JSON and Markdown files to an agreed
  branch. Tell your teammate which branch to get and the file paths.
- **Your usual chat:** send both files through Messenger, Discord, email, or wherever
  you coordinate. Your teammate places them at the same relative path in their
  repository, for example `docs/qa/queues/team-01.json` and `team-01.md`.

Nothing is sent automatically. A path on your computer does not make the file
available on your teammate's computer.

Both agents use copies of the same reviewed JSON. The Markdown is for reading;
the JSON tells the agent which cases belong to each tester. Have your teammate
use that file rather than generate a second queue from scratch.

## 3. Prepare each machine

Each tester needs their own repository checkout containing the queue tool,
workflow, QA plan and traceability matrix. Start from the same agreed repository
commit so both agents read the same case definitions and starting statuses. Each
tester then uses a separate QA branch and tracking issue.

For live tests, also agree on the application commit being tested and record the
actual deployed commit in each report. The two machines can have different absolute
repository paths; the relative queue path can stay the same.

**Different machines do not necessarily mean different test environments:**

- If each tester has their own appliance and target VMs, you can run your assigned
  sets at the same time. Each tester prepares their own baseline and prerequisites,
  and runs one appliance at a time on their machine.
- If both machines connect to the same appliance or target VMs, take turns using
  that shared environment. Agree who is using it before either agent connects or
  changes its state.

A test passing on your machine does not configure your teammate's appliance.
For example, deploying NCPA or enabling a plugin on your appliance does not satisfy
the same prerequisite on theirs. Each agent checks its own environment against
the [QA plan](QA_Test_Plan.md), including the supported lab and scan restrictions.
A missing environment or prerequisite is recorded as blocked; a separate
prerequisite set can be prepared when necessary.

## 4. Each tester reviews and explicitly starts their set

Send your teammate this message after sharing the files:

> Your assignment is `teammate-se` in `docs/qa/queues/team-01.json`.
> Review `docs/qa/queues/team-01.md`. Tell your agent: "Follow
> `.agent/workflows/qa-run.md`. Show only `teammate-se` from
> `docs/qa/queues/team-01.json`, check it against current sources, and wait for
> my explicit start." We will each test on our own appliance and targets.

Use the last sentence only if you have separate environments. For a shared
environment, replace it with your agreed turn or access window.

After reviewing the list, start your own set with:

> Follow `.agent/workflows/qa-run.md`. Start only `paeng-fs` from
> `docs/qa/queues/team-01.json`, using tracking issue #123.
> Verify the prerequisites on my test environment before running cases.

Your teammate gives the same instruction with `teammate-se` and their own issue
number. Replace #123 with the actual GitHub tracking issue number; it is an example.

Starting one set does not start anyone else's set or the next set in the queue.
If case definitions, statuses or notes have changed, the agent shows a replacement
queue and waits for a new explicit start. Newly pending cases and prerequisite
tests are not added automatically.

## 5. Share results through GitHub

Each agent records the tested commit, its own environment, per-case results and
restoration state in a sanitized [run report](../test-runs/README.md). It updates
the traceability matrix and regenerates the paper tables on its own QA branch,
following the workflow's checkpoint and PR rules.

Use distinct report names so the two machines' results stay attributable. After
five rounds, checkpoint unfinished work and resume the same assignment. Do not
count a queued case as tested before there is observed evidence.

When combining the two testers' PRs, preserve both reports and both testers'
traceability updates, then regenerate the paper tables. Do not replace one
tester’s results with the other checkout's older copy.

## Optional terminal commands

If you prefer commands, run these from the repository root. Preparing saves files;
showing and checking them does not execute tests.

```bash
python3 -I scripts/qa_queue.py prepare \
  --set paeng-fs:FS:Paeng \
  --set teammate-se:SE:teammate \
  --output docs/qa/queues/team-01.json

python3 -I scripts/qa_queue.py show \
  --queue docs/qa/queues/team-01.json --run teammate-se

python3 -I scripts/qa_queue.py check \
  --queue docs/qa/queues/team-01.json --run teammate-se
```

Each `--set` is `NAME:ISO:OWNER`, optionally followed by `:ID,ID` for a subset.
Set names use letters, numbers, underscores or hyphens. Empty selections are
rejected. Cases keep master-plan order, subject to prerequisites. The tool checks
overlap within one queue file; it does not coordinate separate files or machines.
