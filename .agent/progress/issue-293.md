# Issue #293: Explain the AI-agent tooling directories for IT staff

Branch: `issue-293-agent-tooling-docs`
Status: in-progress

## Finish condition

- [ ] A short section (root README) states these are optional development tooling, what each is, and that removing them does not affect running Pinpoint.
- [ ] Workflows are not removed or altered.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Section: optional tooling, what each is, removal safe | item 1 | README.md section; `scripts/verify.sh docs` |
| Do not remove/alter workflows | item 2 | `git diff --stat origin/main` shows only README/docs |

## Plan

1. [ ] Add "Optional AI-agent tooling" section to README.md (and docs/README.md link if it fits)
2. [ ] Verify docs, finish

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan | n/a | n/a |

## State for the next session

- Last check run (exact command): none
- Result: n/a
- Hypothesis: docs-only change
- Next action: write README section

## Decisions and notes

Docs-only; no spec behavior change.
