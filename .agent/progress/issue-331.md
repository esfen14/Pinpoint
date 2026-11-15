# Issue #331: Add module and function docstrings to undocumented backend code

Branch: `issue-331-backend-docstrings`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

- [ ] Each of the 37 files has a one-paragraph module docstring (inventory text, TBC lines confirmed)
- [ ] The 217 public names have docstrings, largest modules first
- [ ] AST count re-run and inventory totals updated
- [ ] `scripts/verify.sh backend` passes

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Comments and docstrings only, no behavior change | all | `git diff` shows only docstrings; backend tests green |
| Module docstrings for 37 files | item 1 | AST count: nomod = 0 |
| Docstrings for 217 public names | item 2 | AST count: missing = 0 |
| Frontend out of scope | (out of scope) | no client/ files changed |
| Re-run count, update inventory | item 3 | docs/plans/Code_Documentation_Inventory.md |
| verify backend | item 4 | `scripts/verify.sh backend` |

## Plan

1. [ ] Module docstrings, 37 files (all listed in the inventory)
2. [ ] Name docstrings: system_models.py, history_models.py, plugin_models.py, remediation_actions.py
3. [ ] Name docstrings: api/** (user/management, helper/*, commands/seed, plugin/*, system/*)
4. [ ] Name docstrings: logging/*, nagios/*, maintenance.py, smtp_settings.py
5. [ ] Name docstrings: ncpa_deployment, network_discovery/*, scripts/*
6. [ ] Re-run AST count, update docs/plans/Code_Documentation_Inventory.md
7. [ ] `scripts/verify.sh all`, delete progress file, open PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan | AST count (scratchpad count.py) | 37 / 217 baseline |

## State for the next session

- Last check run (exact command): python3 count.py
- Result: nomod 37, missing 217
- Hypothesis: n/a
- Next action: step 1

## Decisions and notes

Docstrings only; sensitive modules (network_discovery, ncpa_deployment) are named by the issue, comments only.
