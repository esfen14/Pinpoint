# Prepared QA queues

The original v4 attempt remains INCONCLUSIVE and consumed. After separately
approved audited recovery, the v2 #211 recheck passed the complete supervised
TC-SS-04 result/cleanup path. Its slot is also consumed. The active halt is false;
old attempts/archives/budgets remain preserved. The new two-case assignment below is prepared, waiting for separately reviewed
handoff and explicit start. No completed case may be replayed.

| Queue | State | Scope |
|---|---|---|
| [Next permission batch](2026-10-18-next-permissions.md), [JSON](2026-10-18-next-permissions.json) | Prepared; handoff/start pending, zero attempts | Paeng; TC-ACC-09 E1/E2 then TC-NCPA-08 E1, one fixed serial batch; [review](../Next_Permission_Batch_Review.md), [execution log](2026-10-18-next-permissions-execution.md) |
| [Accepted #211 recheck v2](2026-10-18-issue-211-ss04-recheck-v2.md), [JSON](2026-10-18-issue-211-ss04-recheck-v2.json) | PASS, consumed/historical; never replay | TC-SS-04 only; complete import/logout/resource/baseline proof; [report](../../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md) |
| [Earlier #211 recheck v1](2026-10-18-issue-211-ss04-recheck-v1.md), [JSON](2026-10-18-issue-211-ss04-recheck-v1.json) | Superseded/unstarted; source-stale preparation | Replaced by the separately authorized v2 recheck |
| [Original pilot preview](2026-10-18-today-ss04-v4.md), [JSON](2026-10-18-today-ss04-v4.json) | Original attempt INCONCLUSIVE; preserved/consumed, audited recovery recorded; never replay | TC-SS-04 only, `today-ss04`, Paeng; browser assertions/logout passed, timing-import issue [#211](https://github.com/esfen14/Pinpoint/issues/211); [run report](../../test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md) |
| [Previous pilot preview](2026-10-18-today-ss04-v3.md), [JSON](2026-10-18-today-ss04-v3.json) | Superseded, never started; source check rejects it | `today-ss04`, Paeng, TC-SS-04 only; target `299ab3b` deployed and Staff initialized; fresh execution proof still required |
| [Container/worker draft](2026-10-18-today-ss04-v2.md), [JSON](2026-10-18-today-ss04-v2.json) | Superseded, never started; source check rejects it | Preserved scope before owned bridge/deployment-observer changes |
| [Initial draft](2026-10-18-today-ss04.md), [JSON](2026-10-18-today-ss04.json) | Superseded, never started; source check now rejects it | Preserved initial scope before container/worker preparation changes |

The accepted pilot proves TC-SS-04. The supported launcher now accepts only
TC-SS-04, TC-ACC-09 and TC-NCPA-08 in one fixed serial permission batch, saving
results before the next case and stopping on non-PASS. The new untested scope
contains only the latter two. The separately reviewed `handoff` operation archives
exact prior ledger bytes and appends the next queue; it preserves all original
attempts, recovery history and budgets and grants no case start. Other case types
and unattended execution remain blocked. Follow the
[QA workflow](../../../.agent/workflows/qa-run.md).
