# Prepared pilot queues

The original v4 attempt remains INCONCLUSIVE and consumed. After separately
approved audited recovery, the v2 #211 recheck passed the complete supervised
TC-SS-04 result/cleanup path. Its slot is also consumed. The active halt is false;
old attempts/archives/budgets remain preserved. No queue below is a new executable
assignment or permission to replay a completed case.

| Queue | State | Scope |
|---|---|---|
| [Accepted #211 recheck v2](2026-10-18-issue-211-ss04-recheck-v2.md), [JSON](2026-10-18-issue-211-ss04-recheck-v2.json) | PASS, consumed/historical; never replay | TC-SS-04 only; complete import/logout/resource/baseline proof; [report](../../test-runs/2026-10-18-issue-211-ss04-recheck/REPORT.md) |
| [Earlier #211 recheck v1](2026-10-18-issue-211-ss04-recheck-v1.md), [JSON](2026-10-18-issue-211-ss04-recheck-v1.json) | Superseded/unstarted; source-stale preparation | Replaced by the separately authorized v2 recheck |
| [Original pilot preview](2026-10-18-today-ss04-v4.md), [JSON](2026-10-18-today-ss04-v4.json) | Original attempt INCONCLUSIVE; preserved/consumed, audited recovery recorded; never replay | TC-SS-04 only, `today-ss04`, Paeng; browser assertions/logout passed, timing-import issue [#211](https://github.com/esfen14/Pinpoint/issues/211); [run report](../../test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md) |
| [Previous pilot preview](2026-10-18-today-ss04-v3.md), [JSON](2026-10-18-today-ss04-v3.json) | Superseded, never started; source check rejects it | `today-ss04`, Paeng, TC-SS-04 only; target `299ab3b` deployed and Staff initialized; fresh execution proof still required |
| [Container/worker draft](2026-10-18-today-ss04-v2.md), [JSON](2026-10-18-today-ss04-v2.json) | Superseded, never started; source check rejects it | Preserved scope before owned bridge/deployment-observer changes |
| [Initial draft](2026-10-18-today-ss04.md), [JSON](2026-10-18-today-ss04.json) | Superseded, never started; source check now rejects it | Preserved initial scope before container/worker preparation changes |

The accepted pilot proves the narrow TC-SS-04 path, not broader automation.
`qa_pilot.py` still permits only that one case, while the recovery disposition
binds dispatch to its named completed queue. A reviewed next-assignment handoff,
selected case adapters/fixtures and appropriately bounded launcher extension are
needed before a new source-current queue/card and explicit start. Preserve all
original human results and attributable reports. Follow the
[QA workflow](../../../.agent/workflows/qa-run.md).
