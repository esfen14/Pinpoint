# Issue #208: TC-ACK-05: confirm before removing an acknowledgement

Branch: `issue-208-confirm-unacknowledge`
Status: in-progress

## Finish condition

- [ ] Confirmation on every unacknowledge entry point; cancel makes no DELETE.
- [ ] Confirm removes once, no comment, refreshes state, keeps permission/error behavior.
- [ ] Frontend regressions for Dashboard, Inventory, System Status, detail drawer.
- [ ] Fresh authorized case verification (needs a person; NOT doable by the agent).
- [ ] Frontend checks and CI pass; docs only if behavior changes (spec 4.6 already requires it).

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Prompt at all entry points, cancel = no DELETE | 1, 3 | cancel tests in 4 test files |
| Confirm removes once, refresh, errors kept | 2, 3 | confirm tests |
| Live re-verification with SHA | 4 | person; out of agent scope |
| CI green | 5 | scripts/verify.sh frontend |

## Plan

1. [ ] Tests: cancel/confirm for Dashboard, DeviceInventoryPage, SystemStatusPage, StatusDetailDrawer (client/src/test/)
2. [ ] Add window.confirm("Remove acknowledgement for this alert?") (repo convention) in the 4 handlers
3. [ ] verify.sh frontend, then docs/all

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan | | |

## State for the next session

- Last check run (exact command): none
- Result: n/a
- Hypothesis: window.confirm matches RemediationPage convention
- Next action: write the four tests

## Decisions and notes

Item 4 needs a person with an authorized lab run.
