# Issue #169: Add Codex skill adapters

Branch: `issue-169-codex-skills`
Status: in-progress

## Finish condition

- [x] Three valid adapters link to the shared workflows.
- [x] AGENTS.md and Agent_Workflow_and_CI.md document adapters.
- [ ] Skill validation and docs verification pass; PR and CI results recorded.

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Add all three adapters | Three valid adapters | quick_validate.py and reference inspection |
| Document entry points | Documentation | scripts/verify.sh docs and diff review |
| Verify and open PR | Validation and PR | gh pr checks |

## Plan

1. [x] Add .codex/skills adapters and update AGENTS.md and spec files/Agent_Workflow_and_CI.md.
2. [ ] Validate skills, run scripts/verify.sh docs and all, remove progress scaffolding and open PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read workflows and plan | Source inspection | Three workflow adapters required |
| 1 | Added three adapters and documentation | quick_validate.py for all three; scripts/verify.sh docs; scripts/verify.sh all | Skills and docs green; all stops at missing python in isolated checkout |

## State for the next session

- Last check run (exact command): scripts/verify.sh all
- Result: docs green; backend cannot start because python is unavailable in the isolated checkout.
- Hypothesis: Thin adapters preserve workflow ownership.
- Next action: Open PR after removing progress scaffolding and inspect CI for backend/frontend checks.

## Decisions and notes

Use the user-requested .codex/skills location. Keep all procedure text in .agent/workflows.
