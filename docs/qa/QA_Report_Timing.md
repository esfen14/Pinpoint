# Permission pilot report timing (#211)

The importer previously treated `attempt.startTime + attempt.duration` as a
wall-clock end. That inference is invalid for pinned Playwright **1.64.0**.
The sanitized fixture in `scripts/test_qa_results.py` reproduces the original
rejection: start `2026-10-18T07:21:18.069Z`, duration 910 ms, E1 at
`07:21:19.023Z` (44 ms beyond the computed end). The report-level fields remain
start `07:21:17.708Z`, duration 1448.738 ms. All remaining fixture content is
synthetic reviewed report structure. No private pilot report was copied.
Synthetic independent launch/completion bounds in that test are **not** new
observations about the historical pilot.

## Pinned source and observed semantics

Inspect the npm artifact installed from `client/package-lock.json`, under
`client/node_modules/playwright/lib/`:

| Source | Relevant behavior |
|---|---|
| `worker/workerProcessEntry.js`, `TestInfoImpl` constructor | `_startWallTime = Date.now()`; separately stores monotonic `_startTime` |
| Same file, `TimeoutManager.withRunnable` | Adds `monotonicTime() - start` to the selected slot; fixture/hook slots may differ from the default slot |
| Same file, `WorkerMain._runTest` | Final duration is integer-truncated `defaultSlot().elapsed + afterHooksSlot.elapsed`; separately timed beforeAll/worker setup and time between slots are not necessarily included |
| Same file, `buildTestBeginPayload` / `buildTestEndPayload` | Sends wall start and selected-slot duration separately |
| `runner/index.js`, dispatcher `_onTestBegin` / `_onTestEnd` | Copies worker wall start and worker duration into result |
| Same file, JSON reporter `_serializeTestResult` | Serializes those values without manufacturing a worker wall end |

`node --test qa/timing.node.mjs` from `client/` runs the actual pinned worker
with one synthetic test and a separately timed beforeAll slot. Its fixed
attachment's wall timestamp follows `startTime + duration`, while the report
passes. It imports no acceptance spec and requests no browser/page fixture,
credentials, appliance, container or network. This confirms the clock-domain
mistake with a real reporter rather than a fabricated JSON-only example.

The source establishes why duration cannot supply the required wall end.
The original report lacks per-slot clock telemetry: the precise distribution of
its 44 ms among omitted work, scheduling and possible wall-clock adjustment
remains unknown. The synthetic hook demonstrates the mechanism; it does not
claim the permission adapter has a beforeAll hook. No product permission defect
or independently validated performance result follows from this investigation.

## Bounded import rule

The owned container component records host UTC immediately before `start --attach`
and immediately after its bounded completion, plus the monotonic elapsed attach
time. Its fresh private evidence directory was empty before dispatch; source
mounts, container identity/image/command and stopped exit are checked. Removal
and bridge cleanup do not extend the evidence window.

The parser requires these independent values and the consumed remaining case
budget. It accepts only:

- A positive wall window within that budget, capped at the reviewed pilot's
  300 seconds, with completion no later than import-time UTC. No future grace.
- `launch <= report wall start <= attempt wall start <= E1 wall time <= completion`.
- Finite non-boolean durations: attempt 0–60000 ms; report at least attempt
  duration, at most the config's 90000 ms global limit and at most independently
  measured attach elapsed time. Monotonic elapsed must fit the consumed budget.
- Existing exact pinned version/config/project/case/title/initial-attempt checks,
  fixed E1 identity/verdict/text, private bounded attachments, no capture/retry,
  consistent unique-case totals and successful session cleanup.

There is no 44 ms allowance, report-duration-derived wall endpoint, fallback to
import time, timestamp rewriting or assertion change. Missing independent bounds
fail closed. Failed logout is INCONCLUSIVE with `restored: false`; parser errors
and failed container/bridge/process/baseline cleanup leave the supervisor halted.
The composed regression uses the real parser with simulated transport and proves
both acceptance and durable halting without a live resource.

This is trusted runner provenance, not a cryptographic signature. A malicious
same-user writer that can forge both private reports and trusted driver receipts
is outside the existing cooperative runner boundary. Identity/text/timing forgeries
covered by the regressions reject; JSON alone cannot authenticate arbitrary
fabricated content. Shell argv/environment/targets/credential handling are unchanged;
the command-path review found only independent clock acquisition and receipt
forwarding, with no new interpolation, output copying or secret-bearing fields.

## History and recheck

The [original pilot](../test-runs/2026-10-18-issue-206-ss04-pilot/REPORT.md)
remains INCONCLUSIVE. Its private evidence, consumed v4 attempt and halted ledger
must remain intact. These fixture results cannot retrospectively accept it.
A new reviewed queue, separately granted halted-state recovery and explicit
start are required before another case attempt. The separately approved
[audited recovery implementation](Issue_211_Recheck_Review.md) preserves exact
original ledger bytes and attempt/budget history; it supplies no store reset. Fresh live result acceptance and complete cleanup
remain unverified until that separately authorized run.
