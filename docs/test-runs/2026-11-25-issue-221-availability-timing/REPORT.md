# Test run: issue-221-availability-timing

| | |
|---|---|
| Date | 2026-11-25 |
| Commit tested | `a87de8dd` (application code). The timing script is from branch `issue-221-availability-timing`, which changes nothing under `server/` or `client/`; the run used it at `e842b9e3`, which rounded each time to 1 ms before judging (changed afterwards; no sample was near the limit) |
| Plan | TC-NFR-08 in the [case catalog](../../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md); scripted timing with exactly 10 monitored hosts approved by the owner on [#221](https://github.com/esfen14/Pinpoint/issues/221#issuecomment-7165385861) |
| Tester / executor mode | AI-executed (Claude), scripted, authorized by the owner. Not a human manual result |
| Catalog revision and SHA-256 | `a87de8dd`, `249644804a3d87b04c7ebe461fd7cd2ea5b40e088ff8f75dc505c35bbb1980f0` |
| Queue / set / session / batch | None; no supervised queue or card |
| Deployed application / installer revision | `a87de8dd` copied with `scripts/vmlab sync --client`; server `app`, `config.py`, `migrations` and `client/dist/index.html` matched by SHA-256. No server or client difference from the `cb96b118` already deployed. Snapshot base from installer `3a97733` (recorded in the #220 run) |
| Baseline / preflight / restoration | VM powered off; temporary snapshot taken; `vmlab` preflight passed. 15 devices monitored; 5 paused for the run. Afterwards the VM was powered off, the temporary snapshot restored and then deleted, so the pauses and the deployment are undone |
| Start / end / time zone | Timing 22:37:43 to 22:38:20, UTC+8 (boot 22:36, restore done 22:40) |
| Environment | VirtualBox `qa-pinpoint-appliance`: Ubuntu 22.04.5, 4 CPUs, 4 GB RAM (below the paper's 8 GB), existing database; Nagios 4.5.11 as recorded in the #220 run; reached on `127.0.0.1:18080` |
| Raw evidence | Lab host, `/home/paeng/pinpoint-test-results/2026-11-25-issue-221-availability-timing/` (timing JSON and log, pause replies, appliance facts, browser script and results, 12 screenshots) |

## Result

**Overall: Pass.** With 10 monitored hosts, 10 of 10 requests to each
availability endpoint returned data within 5 s (9 required); the slowest was
0.070 s. This holds for a small Nagios history (see Limits).

Totals (unique TC): Pass 1, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
Attempts and setup operations are not extra unique cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-NFR-08 | Pass | Network Health endpoint 10/10, report endpoint 10/10 within 5 s (`timing.json`) | [#221](https://github.com/esfen14/Pinpoint/issues/221) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-NFR-08 / scripted | E1 9 or more of 10 responses for `/api/system/network-health/availability` are 5 s or less | 10 of 10; 0.046 to 0.070 s, all 200 JSON | Pass | `timing.json`, `timing.err` | Snapshot restored; VM powered off |
| TC-NFR-08 / scripted | E1 9 or more of 10 responses for `/api/system/report/availability` are 5 s or less | 10 of 10; 0.019 to 0.030 s, all 200 JSON | Pass | `timing.json`, `timing.err` | Snapshot restored; VM powered off |

How the samples were timed
([`scripts/availability_timing.py`](../../../scripts/availability_timing.py)):
from the lab host, signed in, one request at a time with 2 s between them, from
sending the request until the whole body was read. The queries are the ones the
web interface sends (`?days=7` and `?period=last_24h`, also the server
defaults). A reply that is not a successful data response never counts. Before
timing, one untimed report request confirmed 10 monitored hosts.

| Sample | Network Health (s) | Report (s) |
|---|---|---|
| 1 | 0.050 | 0.022 |
| 2 | 0.070 | 0.026 |
| 3 | 0.053 | 0.030 |
| 4 | 0.050 | 0.027 |
| 5 | 0.052 | 0.024 |
| 6 | 0.050 | 0.030 |
| 7 | 0.046 | 0.020 |
| 8 | 0.065 | 0.019 |
| 9 | 0.061 | 0.024 |
| 10 | 0.064 | 0.019 |

Supplementary, headless Chromium 156, as the network panel would show it: 10
loads each of `/network-health` (availability request 107 to 168 ms) and
`/reports` (42 to 68 ms), all 200 JSON (`browser.jsonl`).

## Monitored hosts

"Monitored host" means a device Pinpoint monitors. Devices 11 to 15 were paused
through `POST /api/system/hosts/<id>/pause` (each applied to Nagios), leaving 10
in the report. Nagios also checks its own `localhost`, so it held 11 hosts and
Network Health showed 11 online; the report excludes `localhost` and showed 10,
all Up.

## Execution record and the original entries

Both original entries are kept: "returns to login, other result is, data is
showing but plaintext only without UI" (summary, FAIL) and Not run (detail). The
[2026-10-19 records](../2026-10-19-module-20-21-records/REPORT.md) add a
tester-reported retest PASS without timings. Whether the original session timed
anything cannot be established: its URL, signed-in state, build, browser, date
and times are unknown. No timing from it exists.

## The "returns to login" and "plaintext without UI" observations

On [#221](https://github.com/esfen14/Pinpoint/issues/221) a team member
suggested a mistyped address for the login redirect. (The "10 seconds" in that
comment belongs to TC-NFR-07; this case's limit is 5 s.) This run did not
reproduce the original session; it records what `a87de8dd` does (headless
Chromium 156, `browser.jsonl`):

| Signed in | Address | HTTP status and content type | What the browser showed | Expected |
|---|---|---|---|---|
| No | `/network-health`, `/reports` | 200 `text/html` | `/login` with the sign-in form | As specified: protected pages need sign-in |
| No | `/report` (typo) | 200 `text/html` | `/login` with the sign-in form | As specified: unmatched paths go to `/login` |
| No | Either availability API address | 401 `text/html` | Plain "Unauthorized" text | Differs: the API error envelope is JSON (known, [#343](https://github.com/esfen14/Pinpoint/issues/343)) |
| No | `/api/system/report/availabilty` (typo) | 404 `text/html` | Plain "Not Found" text | No stated requirement; noted on #343 |
| Yes | `/network-health`, `/reports` | 200 `text/html` | The page with its interface and availability data | As specified |
| Yes | `/report` (typo) | 200 `text/html` | Redirected to the Overview page | As specified |
| Yes | Either availability API address | 200 `application/json` | Raw JSON text | Normal for an API address |
| Yes | `/api/system/report/availabilty` (typo) | 404 `text/html` | Plain "Not Found" text | No stated requirement; noted on #343 |

**Disposition:** no performance, sign-in or page rendering defect was
reproduced, and no new issue is filed. Both symptoms can come from the address
used (signed-out page or typo goes to login; an API address shows text), which
is a possible explanation, not a proven one. The signed-out HTML 401 is already
#343.

## Limits

- Light history: `/usr/local/nagios/var` was 192 KB with one archive entry, and
  the 24-hour report covered about 14.6 hours of known state. Only the latest
  of the seven Network Health days showed data. A long-running appliance with
  months of archives was not measured.
- Timed about two minutes after boot; some hosts' last check predated the boot.
- One client, no concurrent load.

## Deviations from the plan

- A script replaced timing in the browser's network panel (owner decision
  above); a headless browser pass is attached as supplementary.
- Five devices were paused to meet "10 monitored hosts".
- The appliance's earlier install was updated with `sync` rather than installed
  fresh.

## Follow-up

- Defects found: none new; [#343](https://github.com/esfen14/Pinpoint/issues/343) also covers these addresses.
- Cases to repeat in the next run: none required; repeat on an appliance with long history if that scale matters.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
