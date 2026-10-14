# Issue #144: History backend recovery duration and previous state

Branch: `issue-144-history-recovery`
Status: ready-for-review

## Finish condition

- [x] History list/detail derive or retrieve correct prior state and duration from first problem detection through recovery, including window-boundary events.
- [x] Tests cover missing Nagios duration/last_state, multi-transition episodes, and boundary windows; specs updated.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Archive CGI often omits duration and previous state; list window and detail lose history | 1 | `server/tests/unit/test_history.py` boundary list/detail regression |
| Recovery duration starts at first problem detection, not latest transition | 1, 2 | `server/tests/unit/test_history.py` multi-transition regression |
| Missing Nagios duration/last_state, boundary windows, specs updated | 2 | `server/tests/unit/test_history.py`; `scripts/verify.sh docs` |
| Backend-dependent gap from #133; do not implement in #133 | 1 | Changes confined to issue #144 branch |

## Plan

1. [x] Add failing list/detail and normalization regression tests for absent archive metadata, episode transitions and window boundaries in `server/tests/unit/test_history.py`.
2. [x] Derive previous state and episode duration from archive timeline in `server/app/nagios/notifications.py` and wire list/detail in `server/app/api/system/history.py`; run focused tests and `scripts/verify.sh backend`.
3. [x] Update `spec files/Alerts_Notifications_History_Requirements.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Implementation_Status.md`; verify docs and all stages.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added host/service boundary and multi-transition regressions; derived archive timeline fields for list/detail; updated owning specs and gap inventory | `cd server && .venv/bin/python -m pytest tests/unit/test_history.py -q`; `scripts/verify.sh docs` | 136 passed; docs green |
| 2 | Re-read issue and checked all requirements against regression and specs | `scripts/verify.sh all`; `cd server && .venv/bin/python -m pytest tests/unit/test_history.py -q` | all green; 136 passed |

## State for the next session

- Last check run (exact command): `cd server && .venv/bin/python -m pytest tests/unit/test_history.py -q`
- Result (first failing lines, or "green"): green (136 passed); `scripts/verify.sh all` green
- Hypothesis: Finish condition is proven by isolated tests and full verification.
- Next action (one specific step, not "continue"): Remove progress file and open PR.

## Decisions and notes

Owning spec §§3.1–3.2. No data migration or live Nagios required. When an archive begins with a recovery and no problem detection exists, a supplied archive duration can be retained; otherwise unknown duration cannot be inferred from absent events.
