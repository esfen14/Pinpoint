# Test run: j2-j3-dry-run

| | |
|---|---|
| Date | 2026-10-11 |
| Commit tested | `67243ef5003c6ecd8f31f2c34c9036a49f4552fe` |
| Plan | `docs/qa/QA_Test_Plan.md` (J2/J3) |
| Tester | QA agent |
| Environment | Pinpoint VM appliance; authorized discovery range `10.77.0.0/28`; inherited/conflicted device state |
| Raw evidence | Local sanitized command result; raw harness output is not committed |

## Result

**Overall: Partial.** The live NCPA deployment to two authorized targets completed successfully and produced a deployment log. NCPA service validation, clean-baseline port insertion, complete browser coverage, and restricted-role coverage were not established in this run.

Totals: Pass 2, Fail 0, Blocked 1, Skipped 2.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| J3-02 | Pass | `scripts/vmlab ncpa 10.77.0.2,10.77.0.3` completed with 16 checks passed. Both targets were listed, host keys were approved, SSH credential checks succeeded, deployment returned HTTP 202, the run ended `Success`, both device outcomes were `Success`, and both devices reported `Deployed NCPA`. No credentials are recorded here. | — |
| J3-03 | Partial | Deployment run `GET /api/system/deployment/ncpa/runs/1` returned no password fields or values. The trusted-device response was queried without recording secret material, but a database-level inspection was not performed; full non-persistence coverage is therefore not claimed. | — |
| J3-05 | Blocked | The deployment completed, but `check_ncpa` was not enabled before this run. The service API returned 12 total services and no NCPA-like service rows, so the three-service-per-host assertion was not exercised. | — |
| J3-06 | Pass | `GET /api/system/ncpadeployment?per_page=100` returned one sanitized deployment log with actor, timestamp, `Success` status, 100% progress, and “Deployed NCPA to 2 device(s).” | — |
| J3-09 | Skipped | Deployment outcomes were observed, but the required before/after identity ownership/history and Needs Review comparison was not captured as part of this deployment run. | — |

## Deviations from the plan

- The API-backed lab helper was used instead of browser-driving the deployment wizard; it exercises the documented deployment API flow.
- Targets were `10.77.0.2` and `10.77.0.3`; no scan outside `10.77.0.0/28` was performed.
- J3-05 was not converted into a pass from the successful deployment alone because its plugin prerequisite was absent.

## Follow-up

- Enable `check_ncpa`, wait for a Nagios check cycle, and rerun J3-05.
- Perform a sanitized database/schema inspection for J3-03, without recording credentials or fingerprints.
- Capture the J3-09 identity baseline before a deployment and compare it afterward.
- Continue the remaining J2 cases and restricted-role smoke when a real restricted account is available.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
