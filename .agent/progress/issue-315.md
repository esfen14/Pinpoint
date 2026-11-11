# Issue #315: Add plugin and alert checks to the local lab smoke test

Branch: `issue-315-lab-smoke-plugin-alert`
Status: in-progress

## Finish condition

- [ ] `scripts/lab smoke` enables a plugin on a discovered host and verifies the resulting service check
- [ ] `scripts/lab smoke` takes a target down with `scripts/lab break`, verifies the alert, restores it with `fix`
- [ ] Run live once; result recorded in `docs/test-runs/`
- [ ] Not wired into CI (decided in #306)

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Plugin enable + service check verified | item 1 | scripts/test_lab_smoke.py; live `scripts/lab smoke` |
| break, alert verified, fix | item 2 | scripts/test_lab_smoke.py; live `scripts/lab smoke` |
| Live run recorded | item 3 | docs/test-runs/<date>-issue-315-lab-smoke/REPORT.md |
| Not in CI | item 4 | no change to .github/workflows/ |

## Plan

1. [ ] Test first: scripts/test_lab_smoke.py with a fake API and fake lab script; add to scripts/verify.sh docs
2. [ ] Implement plugin and alert checks in lab/smoke.py (opt-in flags), scripts/lab smoke passes them
3. [ ] Update docs/manuals/Local_Lab.md, Implementation_Status.md, Agent_Workflow_and_CI.md as needed
4. [ ] Live run (issue authorizes it), record docs/test-runs report
5. [ ] verify.sh all, remove progress file, open PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan written | - | - |

## State for the next session

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: smoke.py runs by default for vmlab too, so new checks must be flag-gated; scripts/lab adds the flags
- Next action: write scripts/test_lab_smoke.py (fails first)

## Decisions and notes

- Plugin used: check_ssh (service-driven, all five targets run sshd). Alert target: web01 ssh service via `scripts/lab break web01 ssh`.
