# Test run: issue-220-startup-timing

| | |
|---|---|
| Date | 2026-11-25 |
| Commit tested | `cb96b118` (application code). The timing script is from branch `issue-220-startup-timing` at `feba3278` |
| Plan | TC-NFR-07 in the [case catalog](../../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md); scripted timing approved by the owner on [#220](https://github.com/esfen14/Pinpoint/issues/220#issuecomment-7162363681) |
| Tester / executor mode | AI-executed (Claude), scripted, authorized by the owner. Not a human manual result |
| Catalog revision and SHA-256 | `cb96b118`, `b341272a0d339d6ffa485a35e2ff2302da0abe3d4a6564cdd186532de11e9325` |
| Queue / set / session / batch | None; no supervised queue or card |
| Deployed application / installer revision | `cb96b118` copied with `scripts/vmlab sync --client` over an earlier install (`026fca71`); server Python files (`app`, `config.py`, `migrations`) and `client/dist/index.html` matched by SHA-256. No migration differs between the two. Snapshot base from installer `3a97733` |
| Baseline / preflight / restoration | VM was powered off; `vmlab` preflight passed. Services active after the run; VM powered off again. The deployed files were left at `cb96b118` |
| Start / end / time zone | Timing 20:40:57 to 20:42:08, UTC+8 |
| Environment | VirtualBox `qa-pinpoint-appliance`: Ubuntu 22.04, Nagios 4.5.11, 4 CPUs, 4 GB RAM (below the paper's 8 GB), existing database with 16 hosts and 30 services; reached on `127.0.0.1:18080` |
| Raw evidence | Lab host, `/home/paeng/pinpoint-test-results/2026-11-25-issue-220-startup-timing/` (timing JSON, log, wrapper scripts, browser results, 8 screenshots) |

## Result

**Overall: Pass.** The median of three start-up samples was 3.891 s against a
limit of 10 s. Initialization here means a restart of `pinpoint-gunicorn`, as
the case says, not an appliance boot.

Totals (unique TC): Pass 1, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
Attempts and setup operations are not extra unique cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-NFR-07 | Pass | Samples 3.891, 3.912 and 3.547 s (`timing.json`) | [#220](https://github.com/esfen14/Pinpoint/issues/220) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-NFR-07 / scripted | E1 median of three start-up times is 10 s or less | 3.891 s (sorted 3.547, 3.891, 3.912) | Pass | `timing.json`, `timing.err` | Services active; VM powered off |

How each sample was timed ([`scripts/startup_timing.py`](../../../scripts/startup_timing.py)):
the clock started before `sudo systemctl restart pinpoint-gunicorn` was sent
over SSH, so the SSH round trip is included. The script then signed in with a
new session and called `/api/system/dashboard/summary` every 0.25 s until it
returned 200 with host and service counts. Samples were 30 s apart.

| Sample | Total | Restart command | Replies before ready |
|---|---|---|---|
| 1 | 3.891 s | 1.208 s | 502, 502 |
| 2 | 3.912 s | 1.182 s | 502, 502 |
| 3 | 3.547 s | 0.868 s | 502, 502 |

## The "returns to login" and "plaintext without UI" observations

The original entry, kept as written: "returns to login, other result is, data is
showing but plaintext only without UI" (FAIL). The detail line first said Not
run; the [2026-10-19 records](../2026-10-19-module-20-21-records/REPORT.md) keep
both and add a tester-reported retest PASS without timings. The URL, signed-in
state, build, browser and times of those earlier runs are unknown and stay so.

On [#220](https://github.com/esfen14/Pinpoint/issues/220) a team member
suggested a mistyped address for the login redirect and hand timing for the
timing result. This run did not reproduce the original session; it records what
`cb96b118` does for the likely addresses (headless Chromium 156,
`browser.jsonl`):

| Signed in | Address | HTTP status and content type | What the browser showed | Expected |
|---|---|---|---|---|
| No | `/dashboard` | 200 `text/html` | `/login` with the sign-in form | As specified |
| No | `/dashbord` (typo) | 200 `text/html` | `/login` with the sign-in form | As specified: unmatched paths go to `/login` |
| No | `/api/system/dashboard/summary` | 401 `text/html` | Plain "Unauthorized" text | Differs: the API error envelope is JSON ([#343](https://github.com/esfen14/Pinpoint/issues/343)) |
| No | `/api/system/dashbord/summary` (typo) | 404 `text/html` | Plain "Not Found" text | No stated requirement; noted on #343 |
| Yes | `/dashboard` | 200 `text/html` | Overview page | As specified |
| Yes | `/dashbord` (typo) | 200 `text/html` | Redirected to the Overview page | As specified: `/login` sends a signed-in user on |
| Yes | `/api/system/dashboard/summary` | 200 `application/json` | Raw JSON text | Normal for an API address |
| Yes | `/api/system/dashbord/summary` (typo) | 404 `text/html` | Plain "Not Found" text | No stated requirement; noted on #343 |

A session signed in before the three restarts was still accepted after them
(200 with data), so these restarts did not send that user back to login.

**Disposition:** no start-up performance, sign-in or page rendering defect was
reproduced. Both symptoms can come from the address used (signed-out page or
typo goes to login; an API address shows text), which is a possible explanation,
not a proven one. The one deviation found is filed as #343.

## Deviations from the plan

- A script replaced the stopwatch (owner decision above).
- The appliance's earlier install was updated with `sync` rather than installed
  fresh. `sync` restarted the service once before the three samples.

## Follow-up

- Defects found: [#343](https://github.com/esfen14/Pinpoint/issues/343).
- Cases to repeat in the next run: TC-NFR-08 with recorded times
  ([#221](https://github.com/esfen14/Pinpoint/issues/221)).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
