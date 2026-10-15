# Issue #115: Email Settings sender input merge regression

Branch: `issue-115-smtp-relays`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] Restore separate, editable Username and Sender controls in Settings → Email after the merge, preserving Gmail/custom save payload behavior.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| | | |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] Add a regression assertion for distinct username/sender input and saved payload in `client/src/test/EmailSettings.test.tsx`.
2. [ ] Correct sender field markup and state updates in `client/src/components/settings/EmailSettings.tsx`.
3. [ ] Run focused EmailSettings tests, then `scripts/verify.sh frontend`; update this progress record and commit/push the issue branch.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | | | |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `npm run test -- --run src/test/EmailSettings.test.tsx src/test/EmailSettingsRelay.test.tsx`
- Result (first failing lines, or "green"): baseline run in progress; expected to expose missing Sender label from merged markup.
- Hypothesis: merge changed the Sender control to duplicate the Username input and update `form.username` rather than `form.sender`.
- Next action (one specific step, not "continue"): collect focused baseline test output and add a targeted regression assertion before fixing the component.

## Decisions and notes

Choices made, things ruled out, questions for a person.
