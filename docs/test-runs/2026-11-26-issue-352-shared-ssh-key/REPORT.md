# Test run: issue-352-shared-ssh-key

| | |
|---|---|
| Date | 2026-11-26 |
| Commit tested | `cfe2cf75` (branch `issue-352-shared-ssh-key`) |
| Plan | The "Steps" and owner comment of issue #352 |
| Tester / executor mode | AI-assisted, scripted through the lab API (Claude Code, run approved by the repository user) |
| Catalog revision and SHA-256 | Not a catalog run |
| Queue / set / session / batch | None |
| Deployed application / installer revision | Local lab appliance synced from this branch; SHA-256 of `device_identity.py`, `identity_probes.py` and `create_host_cfg.py` in the appliance matched the checkout. No installer |
| Baseline / preflight / restoration | `scripts/lab down` and `up` (rebuild), then `scripts/lab reset` before runs B, A2 and C. All five targets confirmed to share one ED25519 host key and to have locally administered MACs. The earlier lab state was discarded with approval and the lab is left running the last run's data |
| Start / end / time zone | Lab clock: about 02:25 to 03:04 on 2026-11-26 |
| Environment | Docker local lab (`docs/manuals/Local_Lab.md`), Docker 29.9.3, network `10.78.0.0/24`, fresh databases per run |
| Raw evidence | Lab owner's host, `/home/paeng/pinpoint-test-results/2026-11-26-issue-352/` (`runs-a1-b.log`, `runs-a2-c.log`, `lab352.py`) |

## Result

**Overall: Pass** for the issue's scenarios: in every run all five targets that
were scanned got their own record, rescans updated all of them, and a merge held.
The separate smoke script ended 19 passed, 1 failed on its alert-clear check
(see Deviations). The browser UI was not driven.

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial. These are issue scenarios, not catalog cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| A. Issue steps: scan device `10.78.0.2`, then scan the saved network | Pass | Five targets listed and Up with their own addresses; four `DUPLICATE_IDENTITY` reviews, each comparing the new device with web01 (`runs-a1-b.log`, repeated in `runs-a2-c.log`) | #352 |
| A. Second full scan | Pass | Same five devices updated, 0 missed scans, no new review item (`runs-a2-c.log`) | #352 |
| A. Merge web02 into web01, then full scan | Pass | web02 stayed `MERGED`; `.3` recorded as a closed address of web01; no new device; three reviews left (`runs-a2-c.log`) | #352 |
| B. First full scan on an empty appliance (`scripts/lab smoke`), second full scan about 10 minutes later | Pass | All five devices separate after both scans, `Last_Seen_At` advanced for all, 0 missed scans, one open address each, no review item (`runs-a1-b.log`) | #352 |
| C. Scan device `.2`, then scan device `.3` twice, then full scan | Pass | `.3` became its own device with one review and web01 kept `.2`; the repeat updated only `.3`; the full scan added the other three with one review each (`runs-a2-c.log`) | #352 |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| A | All targets `.2` to `.6` listed, or a review naming unmonitored addresses | All five listed and Up; Needs Review (4) | Pass | `runs-a2-c.log` | Not required (disposable lab) |
| B | A rescan updates every known device | All five updated | Pass | `runs-a1-b.log` | Not required |
| C | A single-device scan of a clone does not move web01 | web01 stayed at `.2` | Pass | `runs-a2-c.log` | Not required |

Review items and lists were read through the API (`/api/system/discover/review`,
`/api/system/network-health/hosts`); device state and address history were read
from the appliance's `system.db`.

## Deviations from the plan

- The steps were driven through the API, not the Settings and Device Inventory pages.
- In the first execution of run A, the state tables printed after the first full
  scan were read from a database backup inside the appliance, not the live
  database. They were discarded and run A was repeated (A2) against `system.db`.
  One state read in A2 failed with "database is locked"; the review and host
  lists at that point and the following state read are recorded.
- `scripts/lab smoke` (run B): 19 passed, 1 failed. Its break/fix check picked up
  the first new alert, `localhost / Current Load`, rather than web01 SSH, and that
  alert did not clear in time. The Docker host was busy (load average about 14 on
  16 threads shortly afterwards), which is the likely cause. The smoke run was not
  repeated, so the web01 SSH alert and its clearing are not verified here. All
  discovery checks passed.

## Not covered

An installation already holding dropped addresses, clones sharing an NCPA
certificate, hosts with hardware MACs, and an address reused by a conflicting
identity are covered by isolated tests only.

## Follow-up

- Defects found: none in discovery. The Device Inventory page cannot dismiss a
  duplicate identity review (recorded in `Implementation_Status.md`).
- Cases to repeat in the next run: the smoke break/fix alert on an idle host.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
