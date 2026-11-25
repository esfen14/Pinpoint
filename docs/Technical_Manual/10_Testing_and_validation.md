## 10. Testing and validation

### 10.1 Levels

| Type | Where | How to run |
|---|---|---|
| Backend unit and mocked API/DB | `server/tests/unit/` | `scripts/verify.sh backend` |
| Frontend unit and interaction | `client/src/test/` (Vitest) | `scripts/verify.sh frontend` |
| Docs and drift checks | `scripts/` | `scripts/verify.sh docs` |
| Integration (real Nagios CGIs) | `server/tests/integration/` | Opt-in; needs a lab Nagios |
| End-to-end lab | `server/tests/e2e/`, `scripts/lab`, `scripts/vmlab` | Opt-in |
| QA black-box cases | [Case catalog](../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md) | Manual and Playwright; [QA scope](../qa/QA_Journeys_and_Scope.md) |

CI (`.github/workflows/ci.yml`) runs docs, backend and frontend jobs on every
pull request; all three block merging.

### 10.2 Functional and integration testing

Covered by the unit suites and recorded lab runs in
[`docs/test-runs/`](../test-runs/README.md).

### 10.3 Network connectivity testing

From the appliance: `ping <host>`, `nmap -p <port> <host>`,
`snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.1` (do not paste the
community into tickets), `curl -k https://<host>:5693/` for NCPA reachability
**[A]**.

### 10.4 Performance testing

These are single lab measurements taken on 2026-11-25 (and one earlier scan
timing). They are not a load test.

**Discovery scan, 14 container hosts** (QA lab appliance, 4 CPUs, 3.9 GB memory,
one scan of a `/27`):

| Metric | Result |
|---|---|
| Scan duration | 226 s (3 min 46 s) |
| CPU busy, average | 1.4% |
| Memory used, minimum to maximum | 357 to 437 MB |
| Traffic on the monitored interface | about 8.5 MB in, 8.6 MB out (about 0.6 Mbit/s average) |
| `system.db` after the scan | 628 KB |
| `history.db` after the scan | 84 KB |

**Wide port range:** on another lab VM, scanning one host on ports 1 to 10000
took 10 min 52 s. Scan time depends strongly on the port range and on how the
hosts respond.

**Idle** (fresh ISO install, 4 CPUs, 1 monitored host):

| Metric | Result |
|---|---|
| Memory used | 426 MB of 3911 MB |
| Disk used | 8.8 GB of 40 GB |
| `system.db` / `history.db` | 624 KiB / 168 KiB |

**Current limitations of this testing:**

- No more than 14 hosts were monitored, and they were containers, not real
  network devices.
- Only the 4 CPU, 4 GB configuration was measured.
- Peak CPU, response times and the duration of periodic checks were not recorded.
- Database and disk growth over days or months was not measured. The
  rows-per-host measurement is deferred (#82).
- No test at a production host count was run.

**[R]** Measure poll duration and database growth at the expected host count.

### 10.5 Security testing

Unit tests check argv secrecy, input validation and permission denials.
**[R]** A periodic authenticated scan (for example OWASP ZAP) of the UI.

### 10.6 User acceptance testing

Use the black-box case catalog and QA journeys; record results in
`docs/test-runs/`.

### 10.7 Sample test cases

| ID | Test | Expected result |
|---|---|---|
| T-01 | Sign in with an Inactive account | "Account inactive." |
| T-02 | Viewer opens `/accounts` by URL | Access denied; API returns 403 |
| T-03 | Acknowledge an alert with a comment | Badge shown; History records actor and comment; Nagios shows acknowledged |
| T-04 | Scan one known address | Device appears; no change to saved networks |
| T-05 | Enable `check_ssh` | SSH services appear for hosts with port 22 |
| T-06 | Save an invalid Nagios setting that Nagios rejects | Config rolled back; error shown |
| T-07 | `flask restore-backup` while service runs | Refused; nothing changed |
| T-08 | Stop the poller | Dashboard freshness warning |

### 10.8 Error handling and validation

Routes return standard `success`/`error` envelopes; validation uses guard
clauses; failed commits roll back; Nagios-rejected configs roll back with
`422`; settings conflicts return `409`.
