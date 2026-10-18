# Prepared pilot queues

The v4 pilot has completed one browser attempt; its overall result is INCONCLUSIVE
and the supervisor ledger is halted. The user subsequently
authorized appliance access, deployment and Staff setup; see the
[preparation report](../../test-runs/2026-10-18-issue-206-pilot-preflight/REPORT.md).

| Queue | State | Scope |
|---|---|---|
| [Current executable pilot preview](2026-10-18-today-ss04-v4.md), [JSON](2026-10-18-today-ss04-v4.json) | Attempt 1 INCONCLUSIVE; halted; never replay | TC-SS-04 only, `today-ss04`, Paeng; browser assertions/logout passed, timing-import issue [#211](https://github.com/esfen14/Pinpoint/issues/211); [run report](../../test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md) |
| [Previous pilot preview](2026-10-18-today-ss04-v3.md), [JSON](2026-10-18-today-ss04-v3.json) | Superseded, never started; source check rejects it | `today-ss04`, Paeng, TC-SS-04 only; target `299ab3b` deployed and Staff initialized; fresh execution proof still required |
| [Container/worker draft](2026-10-18-today-ss04-v2.md), [JSON](2026-10-18-today-ss04-v2.json) | Superseded, never started; source check rejects it | Preserved scope before owned bridge/deployment-observer changes |
| [Initial draft](2026-10-18-today-ss04.md), [JSON](2026-10-18-today-ss04.json) | Superseded, never started; source check now rejects it | Preserved initial scope before container/worker preparation changes |

The current pilot checks that a Staff user cannot see/open System Status and is
redirected to Settings. The v4 initial attempt was authorized and ran once. Its parser timing rejection
blocks result acceptance; preserve the halted ledger and outputs. Resource/session
cleanup and independent baseline inspection passed. Harness fix, reviewed recovery,
a new recheck queue and explicit start are required before any later attempt. Prepared scope and passing offline fixtures are
not acceptance results. Follow the [QA workflow](../../../.agent/workflows/qa-run.md).
