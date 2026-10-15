# Issue #169: Add Codex skill adapters

Branch: `issue-169-codex-skills`
Status: in-progress

## Finish condition

- [ ] Three valid adapters link to the shared workflows.
- [ ] AGENTS.md and Agent_Workflow_and_CI.md document adapters.
- [ ] Skill validation and docs verification pass; PR and CI results recorded.

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Add all three adapters | Three valid adapters | quick_validate.py and reference inspection |
| Document entry points | Documentation | scripts/verify.sh docs and diff review |
| Verify and open PR | Validation and PR | gh pr checks |

## Plan

1. [ ] Add .codex/skills adapters and update AGENTS.md and spec files/Agent_Workflow_and_CI.md.
2. [ ] Validate skills, run scripts/verify.sh docs and all, remove progress scaffolding and open PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read workflows and plan | Source inspection | Three workflow adapters required |

## State for the next session

- Last check run (exact command): git status --short
- Result: green; clean checkout before progress file.
- Hypothesis: Thin adapters preserve workflow ownership.
- Next action: Create three SKILL.md files and document their paths.

## Decisions and notes

Use the user-requested .codex/skills location. Keep all procedure text in .agent/workflows.
