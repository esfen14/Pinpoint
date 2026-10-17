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

| 1 (checkpoint) | Incorporated accepted branch; added FK/data cleanup and UI; reproduced and fixed fingerprint race, unbounded exit wait and unsafe install logging; owner approved deployed cleanup | 196 focused backend tests; 13 migration tests; scripts/verify.sh docs; scripts/verify.sh frontend | 196 + 13 passed; docs green; 874 frontend passed/build/lint green (31 warnings). Full backend in progress with one failure pending final output. |

## State for the next session

- Last check run (exact command): scripts/verify.sh frontend
- Result: green: 874 tests passed, production build passed, lint 0 errors/31 warnings. docs and 13 migration tests also green. Full backend /tmp/issue182-backend-round1.log is still running; focused security/cleanup suite /tmp/issue182-round2-focused.log is still running.
- Hypothesis: Core/UI changes are implemented; complete backend output will identify the one current failure. Fresh VM Ubuntu installation is still running (SSH so far answers from installer environment only).
- Next action: Inspect /tmp/issue182-backend-round1.log and /tmp/issue182-round2-focused.log completion, fix the reported failure, then bootstrap the newly installed VM and provision Pinpoint.

## Decisions and notes

- User explicitly includes settings UI and remediation unit form; fixes Action_Id now as a foreign key.
- Nullable ON DELETE SET NULL plus Action_Name snapshot retains audit history. Explicit transactional detachment in delete route is needed even where SQLite foreign-key enforcement is disabled.
- User-authorized issue scope includes remote-command security review. Existing accepted on-device design is retained pending inspection.
- Requested target/lab preference asynchronously; no live mutation before ownership/target access is established.
- Human reviewer approval is external and must never be claimed by the agent.

- Owner approved cleanup on trusted deployed devices, with explicit warning/redeployment; issue #182 body updated with the two scope decisions and acceptance criteria.
- Fresh VM: pinpoint-issue182-appliance, UUID 8e0417fe-2d5f-4473-a6b3-74d91edbe2f1; fresh ISO install, SSH 2282 and web 18882. Private runtime state /tmp/pinpoint-issue182-vmlab; config /tmp/issue182-vmlab.env. No existing appliance/target was mutated.
- Boot initially failed due to KVM owning AMD-V. Owner authorized unloading only without running KVM guests, then ran sudo modprobe -r kvm_amd kvm themselves because this session has no passwordless sudo. Restore KVM after shutting down our test VM; may require owner terminal action.
- Security review: docs/plans/Issue_182_Remote_Restart_Security_Review.md; human review remains external.
- The action FK migration was generated with Flask-Migrate against both binds on disposable files, then reviewed/extended to null existing orphan links. No application database was modified.
