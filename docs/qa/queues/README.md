# QA queue state

Queues are immutable review artifacts and execution ledgers. A consumed queue is never
replayed, and no file here is edited to change its scope. The preparation procedure is
in [`QA_Run_Queues.md`](../QA_Run_Queues.md); the workflow is
[`qa-run.md`](../../../.agent/workflows/qa-run.md). The active halt is false and no QA run
is in flight.

## Current

| Queue | State | Scope |
|---|---|---|
| [Next permission batch](2026-10-18-next-permissions.md), [JSON](2026-10-18-next-permissions.json), [execution log](2026-10-18-next-permissions-execution.md) | Prepared; handoff and start pending, zero attempts | Paeng; TC-ACC-09 E1/E2 then TC-NCPA-08 E1, one fixed serial batch; [review](../../test-runs/2026-10-18-qa-next-permission-batch-review/REPORT.md) |
| [Module 2–9 adapters v12](2026-10-18-modules-2-9-adapters-v12.md), [JSON](2026-10-18-modules-2-9-adapters-v12.json) | Latest adapter preparation; not started | Read by the adapter docs ([readiness guide](../Automation_Readiness.md)) |
| [Card drafts v5](modules-2-9-card-drafts-v5.json) | Read by `scripts/qa_queue.py` | Frozen card drafts used by queue preparation |

## Consumed (kept in place; never replay)

| Queue | State | Scope |
|---|---|---|
| [Accepted #211 recheck v2](2026-10-18-issue-211-ss04-recheck-v2.md), [JSON](2026-10-18-issue-211-ss04-recheck-v2.json) | PASS, consumed | TC-SS-04; [report](../../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md) |
| [Pilot v4](2026-10-18-today-ss04-v4.md), [JSON](2026-10-18-today-ss04-v4.json) | INCONCLUSIVE, consumed, audited recovery recorded | TC-SS-04; [report](../../test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md) |
| [Pilot v3](2026-10-18-today-ss04-v3.md), [JSON](2026-10-18-today-ss04-v3.json) | Superseded, never started; cited by a report | `today-ss04`; [report](../../test-runs/2026-10-18-issue-206-pilot-preflight/REPORT.md) |
| [Initial draft](2026-10-18-today-ss04.md), [JSON](2026-10-18-today-ss04.json) | Superseded, never started; cited by reports | `today-ss04` initial scope |

## Archived

Superseded versions with no tool reader moved to [`archive/`](archive/) unchanged
(issue [#285](https://github.com/esfen14/Pinpoint/issues/285)); none is current.

| Group | Files in `archive/` |
|---|---|
| Earlier #211 recheck | `2026-10-18-issue-211-ss04-recheck-v1` |
| Container/worker draft | `2026-10-18-today-ss04-v2` |
| Module 2–9 adapters | `2026-10-18-modules-2-9-adapters-v1` to `v11` |
| Module 2–9 queues | `2026-10-18-modules-2-9-v2` to `v10` |
| Card drafts | `modules-2-9-card-drafts-v1` to `v4`, and `v6` |

Each name above has a `.json` and a `.md` pair, except card drafts (`.json` only).
