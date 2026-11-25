# Issue #220: TC-NFR-07: Clarify conflicting start-up test results

Branch: `issue-220-startup-timing`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

From the issue, with the timing items replaced by the owner decision of 2026-11-25
(issue comment 7162363681). Tick an item only when a check proves it.

- [ ] Establish whether this case was executed and retain both original conflicting entries.
- [ ] Capture the exact URL, authenticated state, HTTP status/content type, expected page/API behavior, actual tested build and sanitized evidence for the reported redirect/plain-text symptom.
- [ ] Record three scripted start-up samples (restart the service, sign in, call `/api/system/dashboard/summary` until it returns data) and assess whether the median is 10 seconds or less.
- [ ] Attach the result as a separately attributed, AI-executed scripted run (not a human manual result); unknown timings of earlier runs stay unmeasured.
- [ ] If a reproducible authentication, rendering or performance defect is observed, link/file a focused defect; otherwise document the clarification disposition.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Conflicting entries: executed or not | 1 | New report; catalog summary row unchanged |
| Redirect / plain-text symptom unidentified | 2 | Script probe output and browser check in the report |
| Median of three samples at most 10 s | 3 | `scripts/startup_timing.py` run on the appliance |
| Comment: re-run with a timing script | 3, 4 | Same script and report |
| Do not infer failure from source; preserve verdicts | 1, 4 | `scripts/verify.sh docs`; diff of catalog |
| No product fix | out of scope | Defects become new issues |

## Plan

1. [ ] Failing tests: `scripts/test_startup_timing.py` against a local fake server.
2. [ ] Implement `scripts/startup_timing.py` (stdlib; samples, median, URL probes) and add the test to `scripts/verify.sh` docs.
3. [ ] Live run on `qa-pinpoint-appliance` (authorized): boot, deploy current main, 3 samples, probes, browser check of the mistyped address, power off.
4. [ ] Report `docs/test-runs/<date>-issue-220-startup-timing/`, index row, catalog `Recorded run` note, derived QA files (`render_qa_case_tables.py`).
5. [ ] Finish: verify all, post disposition, PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | | | |

## State for the next session

- Last check run (exact command): none
- Result (first failing lines, or "green"): n/a
- Hypothesis: n/a
- Next action (one specific step, not "continue"): write `scripts/test_startup_timing.py`.

## Decisions and notes

- Owner (2026-11-25): scripted timing replaces manual timing; live run on `qa-pinpoint-appliance` authorized (boot, sync main, restart `pinpoint-gunicorn` three times, power off). #221 follows afterwards on its own branch.
- `~/.config/pinpoint-vmlab/env` names `pinpoint-qa-appliance` and SSH port 2250; the registered VM is `qa-pinpoint-appliance`. Use a temporary `VMLAB_CONFIG`, do not edit the user's file.
