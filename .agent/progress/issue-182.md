# Issue #182: Remote service restart, settings UI and run-history integrity

Branch: `issue-182-remote-restart`
Status: in-progress

## Finish condition

- [ ] Accepted design records the on-device helper/rule decision.
- [ ] Trusted/pinned device restart succeeds; changed fingerprint refuses and records.
- [ ] Off-list services refuse on the device.
- [ ] Every attempt is recorded without credentials in logs/responses.
- [ ] Live timeout, paused and disabled cases refuse; helper/sudoers verified.
- [ ] Injection and secret-exposure security review documented.
- [ ] Admin guide explains pre-change cleanup/redeploy and allowlist redeploy.
- [ ] Per-device settings UI and remediation unit form included (owner decision 2026-10-17).
- [ ] Action_Id foreign key prevents deleted-action history affecting replacement actions (owner decision 2026-10-17).
- [ ] Relevant automated checks and CI green; evidence attached; human review obtained before merge.

Requirement coverage (every issue requirement):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| A/B: reuse accepted implementation and deployment identity | Design; trusted/pinned restart | Existing design/source review and remote restart tests |
| C/D: trusted target, changed fingerprint, allowlist, attempt audit, no credentials | Live restart, refusals and audit | Unit tests plus docs/test-runs report of real target runs |
| C: timeout, paused, disabled; helper and sudoers | Live edge cases | Real target evidence report |
| C/E: security review | Security review | Written review of remote_restart.py and deployment helper |
| C/E: administrator documentation | Admin guide | docs/manuals and docs verification |
| C: settings and unit UI decision | UI included | Frontend tests for load/save/error/permissions and unit parameters |
| C: reused Action_Id decision | Foreign key | Model/API/migration regression tests retaining audit snapshots |
| E: tests, CI, review and evidence | Verification and review | scripts/verify.sh all, PR checks, report and human approval |

## Plan

1. [ ] Incorporate the accepted branch into this issue branch; inspect source/tests and migration ancestry (server/app/remote_restart.py, remediation*.py, ncpa_deployment*, migrations and existing tests).
2. [ ] Test and fix run-history identity with a nullable foreign key, preserving audit snapshots and nulling links at deletion; migrate pre-existing orphan links safely (system_models.py, api/system/remediation.py, migrations, tests/unit/test_remediation*).
3. [ ] Test and add per-device remote restart settings UI and action unit input (client/src/components/ncpa-deployment, remediation/ActionFormDialog.tsx, lib/ncpaDeploymentApi.ts, types and frontend tests).
4. [ ] Review remote command/helper security, run authorized real-target cases, and document admin workflows and evidence (docs/plans, docs/manuals, docs/test-runs and owning specifications).
5. [ ] Re-read issue, run scripts/verify.sh all, checkpoint results, open PR from template, and inspect CI; retain draft/progress if live evidence or human prerequisites remain.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Owner selected UI implementation and FK fix; separate worktree created from origin/main | git log --oneline origin/main..origin/issue-8-3-remote-restart | Existing implementation identified; no prior #182 progress file |

## State for the next session

- Last check run (exact command): git log --oneline origin/main..origin/issue-8-3-remote-restart
- Result: five branch commits, including accepted design, implementation, merge and partial lab report.
- Hypothesis: Existing remote branch can be merged without reimplementing its completed behavior; FK must preserve runs on deletion and safely detach old orphan links.
- Next action: Merge origin/issue-8-3-remote-restart into this branch and run focused existing regression tests.

## Decisions and notes

- User explicitly includes settings UI and remediation unit form; fixes Action_Id now as a foreign key.
- Nullable ON DELETE SET NULL plus Action_Name snapshot retains audit history. Explicit transactional detachment in delete route is needed even where SQLite foreign-key enforcement is disabled.
- User-authorized issue scope includes remote-command security review. Existing accepted on-device design is retained pending inspection.
- Requested target/lab preference asynchronously; no live mutation before ownership/target access is established.
- Human reviewer approval is external and must never be claimed by the agent.
