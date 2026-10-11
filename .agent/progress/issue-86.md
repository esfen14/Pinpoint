# Issue #86: J3-09 / J2-08: duplicate device records persist after identity fixes

Branch: `issue-86-duplicate-device-records`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] Isolate the first scan/deployment that creates the duplicate using an owner-approved fresh lab reset (or deterministic regression with matching identity evidence).
- [ ] Add a failing regression for the established cause before changing product code.
- [ ] Repeated scans and NCPA deployment preserve one appropriate record per lab target; deployment remains on the active device.
- [ ] Retest J2-08/J3-09, with sanitized report and exact tested commit.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Isolate duplicate creation | Isolate the first scan/deployment... | |
| Failing regression | Add a failing regression... | |
| One record per target | Repeated scans and NCPA deployment... | |
| Retest J2-08/J3-09 | Retest J2-08/J3-09... | |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] Investigate `server/app/network_discovery/network_discovery.py` and `server/app/system_models.py` to understand how devices are identified and merged during scans.
2. [ ] Try to reproduce the issue in a unit/integration test within `server/tests/unit/`.
3. [ ] If reproducible, fix the issue.
4. [ ] Verify the fix with tests and `scripts/verify.sh`.
5. [ ] Update documentation if needed.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | | | |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): None yet.
- Result (first failing lines, or "green"): N/A.
- Hypothesis: Duplicate devices are being created because the identification logic in `network_discovery` is failing to correctly match existing devices to scanned MAC/IP/Hostname combinations, and `system_models.py` might lack proper constraints or uniqueness checks.
- Next action (one specific step, not "continue"): Investigate `server/app/network_discovery/network_discovery.py` to understand device matching.

## Decisions and notes

Choices made, things ruled out, questions for a person.
- I will first try to reproduce this with an isolated unit/integration test as per `Engineering_Standards.md` and `server/tests/README.md`.
