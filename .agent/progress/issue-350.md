# Issue #350: demo/demo qa reset fails when Ubuntu's automatic upgrades hold the package lock

Branch: `issue-350-lab-apt-lock`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] Decide whether the fix belongs in `scripts/vmlab`, the installer, or both.
- [x] `demo/demo qa reset` completes while Ubuntu has upgrades pending, without a manual step. Record the run in `docs/test-runs/`.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Reset must not fail on the package lock | 2 | `scripts/test_vmlab_auto_upgrades.py`; live `demo/demo qa reset` |
| Where the fix goes (a new appliance may meet the same lock; untested) | 1 | Owner answer 2026-11-26: both. vmlab here, installer issue filed |
| Record the run | 2 | `docs/test-runs/<date>-issue-350-*/REPORT.md` |

## Plan

1. [x] Failing test `scripts/test_vmlab_auto_upgrades.py` (fake ssh/VBoxManage/systemctl/fuser); add it to `scripts/verify.sh`
2. [x] Guest script `lab/stop_auto_upgrades.sh`; call it from `provision` and `fresh` in `scripts/vmlab`
3. [x] File the PinPoint-Installer issue (lock wait on a new appliance)
4. [x] Docs: `spec files/Agent_Workflow_and_CI.md`, `docs/qa/Demo_Lab_QA_Handoff.md`
5. [x] Live: run the guest script against a really running upgrade, then `demo/demo qa reset`; report in `docs/test-runs/`

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | New test, `lab/stop_auto_upgrades.sh`, calls in `vmlab`, docs, installer issue #20 | `python3 -I scripts/test_vmlab_auto_upgrades.py` (failed first: script missing) | 8 OK |
| 2 | None | `scripts/verify.sh docs`; live wait check started 2026-11-26T03:01Z on `18b58b4e` | Docs green. Live check stopped on user request while the script was still waiting (about 60 s in): not a result |
| 3 | Report, index row, Implementation_Status | Owner asked for testing; two live wait checks and `demo/demo qa reset` on `b7762c34` | All passed |

## State for the next session

- Last check run (exact command): `demo/demo qa reset`
- Result (first failing lines, or "green"): green
- Hypothesis: the lab snapshot is old, so apt-daily-upgrade is overdue after each restore
- Next action (one specific step, not "continue"): `scripts/verify.sh all`, then finish (section 5)

## Decisions and notes

- 2026-11-26: the user said not to run any tests yet. Partial log (not evidence of a result):
  `~/pinpoint-test-results/2026-11-26-issue-350/wait-check.log`. `verify.sh all` and
  `demo/demo qa reset` have not run.
- Fix location (owner, 2026-11-26): both. `scripts/vmlab` stops the lab VM's apt timers and waits
  for a running upgrade (never kills dpkg); the installer gets its own issue.
- The installer enables unattended-upgrades on real appliances in `configure-monitoring-updates.sh`,
  which vmlab does not run, so disabling them in the lab conflicts with no vmlab step.
