# Issue #221: TC-NFR-08: Clarify conflicting availability test results

Branch: `issue-221-availability-timing`
Status: in-progress

## Finish condition

Issue items, with the timing items replaced by the
[owner decision](https://github.com/esfen14/Pinpoint/issues/221#issuecomment-7165385861).

- [ ] Establish whether this case was executed and retain both original conflicting entries.
- [ ] Capture the exact URL, authenticated state, HTTP status/content type, expected page/API behavior, actual tested build and sanitized evidence for the reported redirect/plain-text symptom.
- [ ] With exactly 10 monitored hosts, record 10 scripted response times for each availability endpoint and assess whether at least 9 of 10 per endpoint complete within 5 seconds.
- [ ] Attach the result as a separately attributed, AI-executed scripted run; unknown timings stay unmeasured.
- [ ] If a reproducible authentication, rendering, or performance defect is observed, link/file a focused defect; otherwise document the clarification disposition.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Execution status, keep both entries | 1 | report and catalog diff |
| Symptom URL, state, status, type, build | 2 | `--probe` output and browser capture in report |
| 9/10 within 5 s, 10 hosts | 3 | `scripts/availability_timing.py` output |
| Separately attributed result | 4 | report and index row |
| Defect or disposition | 5 | report section, issue link |
| Comment: re-run with a time script | 3, 4 | script and report |
| Original verdicts preserved, no product fix | 1; out of scope | `git diff --stat origin/main` has no `server/` or `client/` change |

## Plan

1. [x] Test then script: `scripts/test_availability_timing.py`, `scripts/availability_timing.py` (reuses `startup_timing.py` session helpers); register in `scripts/verify.sh`, `scripts/README.md`
2. [ ] Live run on `qa-pinpoint-appliance`: temporary snapshot, `scripts/vmlab up`, `sync --client`, reduce to exactly 10 monitored hosts, time, probe symptom URLs and pages, restore snapshot, power off, delete the temporary snapshot (raw evidence in `~/pinpoint-test-results/`)
3. [ ] Report `docs/test-runs/<date>-issue-221-availability-timing/REPORT.md`, index row, disposition and any defect
4. [ ] Catalog TC-NFR-08 result lines, `docs/qa/QA_Case_Status.md`, `automation-coverage.json` fingerprints, `Automation_Readiness.md` note, `spec files/Implementation_Status.md` if a gap opens
5. [ ] `scripts/verify.sh all`, remove this file, pull request

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan | none | |
| 1 | timing script and test | `scripts/verify.sh docs` | green |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): green
- Hypothesis: n/a
- Next action (one specific step, not "continue"): power-off-state snapshot `pre-issue-221` of `qa-pinpoint-appliance`, then `scripts/vmlab up` and `sync --client`

## Decisions and notes

- Owner approved (2026-11-25) a scripted run, exactly 10 monitored hosts, and the live VM run.
- The "10 seconds" in the team comment is TC-NFR-07's; this limit is 5 s.
