# Test run: issue-110-polling

| | |
|---|---|
| Date | 2026-10-15 (all times below UTC) |
| Commit tested | `30a7c7b03446eb282bf200a922e6efbc5380aee1` (application source unchanged throughout) |
| Plan | [Issue #110 finish condition](https://github.com/esfen14/Pinpoint/issues/110) |
| Tester | Codex, local Docker observation |
| Environment | Disposable `pinpoint-issue110-lab` container; Ubuntu 22.04, Python 3.14, Nagios Core 4.5.11, real local CGI, Gunicorn one worker/four threads; fresh migrated and seeded databases; Docker network disabled |
| Raw evidence | Local host `/home/paeng/pinpoint-test-results/2026-10-15-issue-110-polling/` (not committed) |

## Result

**Overall: Pass for the scoped polling cadence, live change and restart checks.**
Three polls at 30 seconds and two at 60 seconds completed without overlap.
The same worker handled both interval saves; restarts loaded the persisted
schedule and immediately polled. A separate restart at the nondefault 30-second
value confirms persistence beyond a fallback to the default.

Totals: Pass 8, Fail 0, Blocked 0, Skipped 0 (within this scoped run).

## Cases

| Case | Result | Notes (observed behavior; evidence file) | Issue |
|---|---|---|---|
| POLL-01: fresh default | Pass | System API initially returned 60 seconds; startup observer recorded one job, max_instances=1, coalesce=true. `poll-events.jsonl` | #110 |
| POLL-02: 30-second cadence | Pass | Three starts, gaps 29.999985 and 30.000201 seconds. `observations.json` | #110 |
| POLL-03: live change | Pass | HTTP saves selected 30 then 60; worker PID 147 stayed unchanged. Check/retry/discovery values stayed unchanged. `observations.json` | #110 |
| POLL-04: 60-second cadence | Pass | Two starts, gap 59.999749 seconds. `observations.json` | #110 |
| POLL-05: restart at 60 | Pass | Restart replaced worker, API and startup job both used 60; prompt first poll followed by another 60 seconds later. `observations.json` | #110 |
| POLL-06: restart at nondefault 30 | Pass | Saved 30 before restarting; API and new job both used 30; prompt first poll, next gap 29.998466 seconds. `restart-observations.json` | #110 |
| POLL-07: non-overlap and scheduling | Pass | All observed poll ends precede the next start. Exactly one polling job after each restart, max_instances=1 and coalesce=true. No skipped or missed runs and no backlog/coalescing occurred in this short unloaded run. Stress/overlap and deliberate overdue coalescing are covered separately by isolated scheduler tests. | #110 |
| POLL-08: actual ingestion | Pass | Real history database contained 8 host, 71 service and 11 program snapshots. Status ingestion was not mocked. `restart-observations.json` | #110 |

## Poll start/end observations

Sanitized timing summary derived from the external observer (not a raw log dump):

| Interval/phase | Worker PID | Run | Start UTC | End UTC |
|---|---|---|---|---|
| 30 s | 147 | 1 | 2026-10-15T06:37:36.417958+00:00 | 2026-10-15T06:37:36.655692+00:00 |
| 30 s | 147 | 2 | 2026-10-15T06:38:06.417944+00:00 | 2026-10-15T06:38:06.618552+00:00 |
| 30 s | 147 | 3 | 2026-10-15T06:38:36.418146+00:00 | 2026-10-15T06:38:36.612210+00:00 |
| 60 s | 147 | 1 | 2026-10-15T06:39:36.807752+00:00 | 2026-10-15T06:39:37.024710+00:00 |
| 60 s | 147 | 2 | 2026-10-15T06:40:36.807492+00:00 | 2026-10-15T06:40:37.036490+00:00 |
| 60 s after restart | 275 | 1 | 2026-10-15T06:40:40.239443+00:00 | 2026-10-15T06:40:40.321125+00:00 |
| 60 s after restart | 275 | 2 | 2026-10-15T06:41:40.237666+00:00 | 2026-10-15T06:41:40.456557+00:00 |
| 30 s after restart | 327 | 1 | 2026-10-15T06:41:51.623948+00:00 | 2026-10-15T06:41:51.824307+00:00 |
| 30 s after restart | 327 | 2 | 2026-10-15T06:42:21.622416+00:00 | 2026-10-15T06:42:21.711309+00:00 |

The saves returned before the first newly scheduled run. Each first run after
a save was one selected interval from the save; no process restart occurred
between the two cadence phases. Raw submit events include their scheduled times.
No skipped/missed events were observed during either restart phase either.

## Method and deviations from the plan

The container used the existing local appliance image and this issue checkout
mounted read-only. No target network, existing Docker lab or VM was changed.
A temporary Python `sitecustomize` observer, outside the application source,
recorded entry/return timestamps for `_poll_nagios_status` and APScheduler
submission/max-instance/misfire events. Requests used the real HTTP settings API.
The observer did not replace the job function or change scheduling.

The lab entrypoint was adjusted only inside this disposable container to disable
scheduler startup for initial migration/seed commands, as required by the
production deployment contract; the default lab entrypoint otherwise enables
jobs before tables exist. The running Gunicorn service retained scheduling.
Nagios's lab check acceleration is irrelevant to the wall-clock polling
measurements. The owner-approved choices remain exactly 30/60/120/300 seconds;
this run verifies behavior rather than selecting options.

## Follow-up and limits

No defect found in the scoped measurements. This run does not exercise the
installer/systemd appliance, long-duration load or browser click-through. The
isolated backend/migration and frontend suites cover input errors, permission,
version, failure compensation, disabled scheduling and UI contracts.

## Sanitization checklist

- [x] No passwords, tokens, keys, communities or private key paths
- [x] No target or external private addresses
- [x] Raw evidence referenced by location and filename; only distilled timings included
