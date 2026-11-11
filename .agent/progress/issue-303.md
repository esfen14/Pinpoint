# Issue #303: System Refinement Audit docs/issues against implemented work and refresh the status

Branch: `issue-303-audit-docs-issues`
Status: in-progress

## Finish condition

- [ ] Every one of the 25 plan issues has one evidence-based status (Implemented / Partly implemented / Open / Superseded) with GitHub and PR numbers
- [ ] Status column added to the issue index; GitHub number recorded in each plan file that lacks one; "none is implemented" sentence fixed
- [ ] Proactive_Resolution plan, Event_Handler_Security_Review and the AGENTS.md routing row checked against the audit and updated or retired
- [ ] Implementation_Status.md reconciled with the audit
- [ ] Plan files' acceptance criteria unchanged
- [ ] `scripts/verify.sh docs` passes

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Status per plan issue with GitHub/PR numbers | item 1 | audit table in docs/archive/issues/INDEX.md |
| Status column, GitHub number per file, fix sentence | item 2 | grep "none is implemented"; each issue-NNN.md names its GitHub number |
| Proactive plan, security review, AGENTS.md row | item 3 | diff of those files |
| Implementation_Status reconcile | item 4 | diff |
| Acceptance criteria unchanged | item 5 | git diff shows no edits inside criteria sections |
| Not in this issue: no implementing | scope | no code changed |
| Done-when: docs verify | item 6 | scripts/verify.sh docs |

## Plan

Note: since the issue was written, #308 moved the files to `docs/archive/issues/` and `docs/archive/plans/`; paths below are the current ones.

1. [ ] Audit: per plan issue, GitHub closer PR(s) (collected) and code/spec spot-check for partial items; record in scratch table
2. [ ] Edit docs/archive/issues/INDEX.md: fix "none is implemented", add Status column (with PR numbers), update GitHub-number table
3. [ ] Add GitHub number line to each issue-NNN.md lacking one (docs/archive/issues/issue-*.md), acceptance criteria untouched
4. [ ] Update docs/archive/issues/README.md state paragraph to match the table
5. [ ] Check Proactive_Resolution_Implementation_Plan.md, Event_Handler_Security_Review.md; update AGENTS.md routing row (no longer "planned")
6. [ ] Reconcile spec files/Implementation_Status.md with the audit
7. [ ] scripts/verify.sh docs, then verify.sh all, finish per section 5

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | plan written; closers collected via gh | gh graphql | all 25 GitHub issues CLOSED |

## State for the next session

- Last check run (exact command): gh graphql closer lookup for #113-#134, #153-#156
- Result: all closed; closers 113:140 115:172 116:168 117:174 118:184 119:148 120:6aef2f8(commit) 121:183 122:166 123:manual 124:178 125:203 126:163 127:179 128:159 129:161 130:manual 131:180 132:139 133:145 134:200 153:204 154:205 155:194 156:185
- Hypothesis: closed != complete; Partly cases: #115 (implicit TLS deferred), #124 (journald in installer repo), #120/#121 installer items, #134 (targets rejected), #125 (no frontend backup_health)
- Next action: step 1, spot-check partial items in code and Implementation_Status.md, then edit INDEX.md

## Decisions and notes

