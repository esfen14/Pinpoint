# Test run: issue-110-polling-retest

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `6cbc59d0` |
| Plan | [Issue #110 acceptance requirements](https://github.com/esfen14/Pinpoint/issues/110) |
| Tester | Codex |
| Environment | Isolated Docker appliance, Ubuntu 22.04, Python 3.14, Nagios Core 4.5.11, Gunicorn one worker/four threads; network disabled; retained database from the previous run |
| Raw evidence | Local host `/home/paeng/pinpoint-test-results/2026-10-15-issue-110-polling-retest/` (not committed) |

## Result

**Overall: Pass for the scoped issue #110 retest.** The full automated verification
passed again. Actual Nagios polls followed the selected 30/60-second cadence,
live changes retained the same worker, and a saved nondefault 30-second interval
survived restart. HTTP validation, authentication, version conflicts and omitted-field
compatibility also passed against the running service.

Totals: Pass 9, Fail 0, Blocked 0, Skipped 0 (report cases).
The backend suite separately skipped 14 tests; those are not claimed as passes.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| AUTO-01: documentation checks | Pass | Fresh `scripts/verify.sh all` documentation stage; final report/index also checked with `scripts/verify.sh docs`. `verify-all.log`. | #110 |
| AUTO-02: backend regression suite | Pass | 2850 passed, 14 skipped. Includes API, populated migration round trip, reschedule/commit/audit failure recovery, disabled scheduling, overlap and coalescing tests. `verify-all.log`. | #110 |
| AUTO-03: frontend regression suite | Pass | 643 passed, including polling options, save/reload, saved hint and Manual refresh. `verify-all.log`. | #110 |
| AUTO-04: production build and lint | Pass | Build passed; lint had no errors (29 warnings). `verify-all.log`. | #110 |
| LIVE-01: 30-second cadence | Pass | Three real polls; start gaps 30.000022 and 30.000069 seconds. `observations.json`. | #110 |
| LIVE-02: live change and 60-second cadence | Pass | HTTP saves selected 30 then 60, with worker PID 103 unchanged. Two 60-second polls, gap 60.000046 seconds. Check/retry/discovery settings stayed unchanged. `observations.json`. | #110 |
| LIVE-03: nondefault restart persistence | Pass | Saved 30; restarted Gunicorn; new worker PID 205, API and job used 30, with an immediate first poll and next gap 29.998284 seconds. `observations.json`. | #110 |
| LIVE-04: HTTP guards and compatibility | Pass | Five invalid values (unsupported number, string, bool, null, float) returned 400 without changing saved settings; unauthenticated write 401; stale version 409; omitted polling field kept 30 seconds. `observations.json`. | #110 |
| LIVE-05: singleton and non-overlap | Pass | One polling job at restart, max_instances=1, coalesce=true. Every captured poll ended before the next started; no skipped/missed runs or backlog/coalescing occurred in this unloaded observation. `poll-events.jsonl`. | #110 |

### Observed poll times

Distilled start/end observations, all UTC:

| Interval/phase | Worker PID | Run | Start UTC | End UTC |
|---|---|---|---|---|
| 30 s | 103 | 1 | 2026-10-15T07:01:47.922760+00:00 | 2026-10-15T07:01:48.053252+00:00 |
| 30 s | 103 | 2 | 2026-10-15T07:02:17.922773+00:00 | 2026-10-15T07:02:18.146148+00:00 |
| 30 s | 103 | 3 | 2026-10-15T07:02:47.922850+00:00 | 2026-10-15T07:02:47.971119+00:00 |
| 60 s | 103 | 1 | 2026-10-15T07:03:48.047443+00:00 | 2026-10-15T07:03:48.261380+00:00 |
| 60 s | 103 | 2 | 2026-10-15T07:04:48.047489+00:00 | 2026-10-15T07:04:48.166570+00:00 |
| 30 s after restart | 205 | 1 | 2026-10-15T07:04:51.158251+00:00 | 2026-10-15T07:04:51.209465+00:00 |
| 30 s after restart | 205 | 2 | 2026-10-15T07:05:21.156546+00:00 | 2026-10-15T07:05:21.205189+00:00 |

## Deviations from the plan

No acceptance requirement changed. This is a fresh repetition of the prior
[run](../2026-10-15-issue-110-polling/REPORT.md), using the retained database in
the dedicated container and the PR head `6cbc59d0`; the automated migration test
uses throwaway databases. The three deployed Python implementation files were
SHA-256 compared with the checkout before testing (`source-hashes.json`).

The Docker appliance has networking disabled and uses its actual localhost
Nagios CGI. An external Python observer records poll call/return times and
APScheduler submission/skip/misfire events without replacing the job or modifying
application source. The existing shared lab and VM were not changed. The
owner-approved options remain 30/60/120/300 seconds; measurements verify runtime
behavior rather than select those options. The dedicated container was stopped
after evidence capture.

## Follow-up

- Defects found: none in the scoped checks.
- Not exercised: installer/systemd appliance, prolonged load, browser click-through.
  The settings UI is covered by automated tests. Deliberate overlap and overdue
  coalescing are covered by isolated real-scheduler tests, not induced in this
  unloaded live trial.
- No immediate repeat required unless source or requirements change.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted (only distilled timings above)
