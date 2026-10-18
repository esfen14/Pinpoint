# Prepared pilot queues

No acceptance queue in this directory has been started. The user subsequently
authorized appliance access, deployment and Staff setup; see the
[preparation report](../../test-runs/2026-10-18-issue-206-pilot-preflight/REPORT.md).

| Queue | State | Scope |
|---|---|---|
| [Current pilot preview](2026-10-18-today-ss04-v3.md), [JSON](2026-10-18-today-ss04-v3.json) | Waiting; execution card BLOCKED | `today-ss04`, Paeng, TC-SS-04 only; target `299ab3b` deployed and Staff initialized; fresh execution proof still required |
| [Container/worker draft](2026-10-18-today-ss04-v2.md), [JSON](2026-10-18-today-ss04-v2.json) | Superseded, never started; source check rejects it | Preserved scope before owned bridge/deployment-observer changes |
| [Initial draft](2026-10-18-today-ss04.md), [JSON](2026-10-18-today-ss04.json) | Superseded, never started; source check now rejects it | Preserved initial scope before container/worker preparation changes |

The current pilot checks that a Staff user cannot see/open System Status and is
redirected to Settings. It requires actual running deployment/ownership proof,
a ready Staff account, an owned private bridge, a complete bounded execution
card and explicit named start. Prepared scope and passing offline fixtures are
not acceptance results. Follow the [QA workflow](../../../.agent/workflows/qa-run.md).
