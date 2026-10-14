# Issue #141: History backend acknowledgement episodes

Branch: `issue-141-ack-episodes`
Status: in-progress

## Finish condition

- [ ] Alert event badge/filter/detail associates acknowledgement actions with the corresponding active problem episode and does not attribute an earlier episode to a later one.
- [ ] Tests cover multiple problem/recovery/ack cycles on the same target, manual unacknowledge, host and service cases.
- [ ] Relevant spec and status inventory updated.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Earlier ACKNOWLEDGED must not mark later never-acknowledged events or return wrong user/comment | 1, 2 | `server/tests/unit/test_history.py` episode API tests |
| AUTO_RESOLVED and UNACKNOWLEDGED bound episodes; multiple problem/recovery/ack cycles for host and service | 1, 2 | `server/tests/unit/test_history.py` episode API tests |
| Update relevant spec and status inventory | 3 | `scripts/verify.sh docs` and spec diff |
| Backend-dependent gap from #133; do not implement in #133 | out of scope for #141 (separate branch) | branch name and diff |

## Plan

1. [ ] Add failing episode-specific list/filter/detail tests in `server/tests/unit/test_history.py`; implement episode association in `server/app/api/system/history.py`; verify focused file and `scripts/verify.sh backend`.
2. [ ] Add regression coverage for window boundaries and same-target mixed host/service actions in `server/tests/unit/test_history.py`; adjust `server/app/api/system/history.py` only if needed; verify focused file and `scripts/verify.sh backend`.
3. [ ] Update `spec files/Alerts_Notifications_History_Requirements.md`, `spec files/Implementation_Status.md` for the behavior/gap and verify `scripts/verify.sh docs` (then finish checks).

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

- Last check run (exact command): `git fetch -q origin && git checkout -b issue-141-ack-episodes origin/main`
- Result (first failing lines, or "green"): green
- Hypothesis: Target-only lookup loses episode boundaries; derive episodes from Nagios transitions and time-ordered ACK_HISTORY actions, including recovery and manual clear.
- Next action (one specific step, not "continue"): Add failing list/filter/detail episode tests to `server/tests/unit/test_history.py`.

## Decisions and notes

The issue explicitly changes the old target-only lookup wording in Alerts & Notifications History §3.2; update that spec at finish. No model change or live lab needed. Other history gaps #142–#144 remain out of scope.
