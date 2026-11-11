# Issue #311: qa_pilot controlled-baseline range

Branch: `issue-311-qa-pilot-baseline-range`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] Person decided: move to 10.77.1.0/27 (asked in session)
- [x] qa_pilot.py, test_qa_pilot.py and spec updated together; verify.sh docs passes
- [x] Other 10.77.0.0/28 guards in scripts/ and lab/ audited (control.py:164, test_defense.py:102, vmlab.env.example:22, qa-run.md:347)

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Decide range | 1 | user answer |
| Change check+test+spec | 2 | test_qa_pilot.py, verify.sh docs |
| Audit other mentions | 3 | grep + notes below |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [x] Test fixture to /27 (scripts/test_qa_pilot.py), see it fail
2. [x] qa_pilot.py:74 to /27; spec Agent_Workflow_and_CI.md (pilot paragraph ~311)
3. [x] Audit: qa-run.md:347, vmlab.env.example:22 to /27; control.py:164 comment; test_defense.py:102 left

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | /27 in qa_pilot, test, spec, qa-run.md, vmlab.env.example, control.py comment | pytest scripts/test_qa_pilot.py | 14 passed |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): pytest scripts/test_qa_pilot.py
- Result (first failing lines, or "green"): green
- Hypothesis: none; work complete
- Next action (one specific step, not "continue"): run scripts/verify.sh all, delete this file, open PR

## Decisions and notes

Choices made, things ruled out, questions for a person.

Audit: control.py:164 and test_defense.py:102 are reject/overlap lists (intentional; comment refreshed). Server test fixtures use /28 as data, not a guard.
