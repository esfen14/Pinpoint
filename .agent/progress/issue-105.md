# Issue #105: QA: Functional Suitability follow-up VM-lab run (2026-10-12)

Branch: `issue-105-qa-run`
Status: in-progress

## Finish condition

- [x] Safe environment ownership/baseline is confirmed; only `10.77.0.0/28` is scanned.
- [x] Up to five FS cases are observed and recorded, or blocking conditions are documented.
- [x] Every mutation is restored.
- [x] QA report/index/traceability/progress records are current and `scripts/verify.sh docs` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Use only a safe, owner-authorized VM lab and scan only the allowed subnet | Safe environment ownership/baseline | `scripts/vmlab status`, read-back of configured discovery networks, and sanitized report |
| Observe up to five unblocked FS cases or document a blocker | Up to five FS cases recorded | QA report plus traceability rows |
| Restore every mutation | Every mutation restored | Recorded restoration command/status in QA report |
| Keep QA artifacts synchronized and docs valid | Records current and docs check passes | Rendered paper table and `scripts/verify.sh docs` |

## Plan

1. [x] Create the dedicated worktree, issue branch, and this progress record; inspect issue #105 and existing FS evidence.
2. [x] Establish safe VM-lab preflight: verify no owner claim, check VM/snapshot/target state, and read configured discovery networks before claiming a live case.
3. [x] Select the first unclaimed FS case whose prerequisites are satisfied; inspect its full requirements and known gaps, execute it (repeating a failure once only), and preserve sanitized evidence.
4. [x] Stop after the first observed case because the run's restoration/reporting round completes the owner-approved scope; restore the appliance snapshot.
5. [x] Create the sanitized run report; update traceability, regenerate the paper table, run docs verification, and checkpoint the result.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Created tracking issue #105, dedicated worktree/branch, and QA progress plan. | Issue and existing FS report/traceability inspected. | Ready for safety preflight; no case claimed yet. |
| 1 | Verified the VM/snapshot, started all five targets, freshly deployed `24cac847`, replaced the installer default discovery range with exactly `10.77.0.0/28`, and ran the restricted smoke. | `scripts/vmlab status`; `scripts/vmlab targets up`; fresh setup; discovery read-back; `scripts/vmlab smoke --discovery-timeout 900 --hosts-timeout 300`; `scripts/verify.sh all`. | Snapshot/stamp valid, full suite green (warnings only), and smoke observed all five targets Up after a successful restricted scan. |
| 2 | Claimed and observed J4-01; created its sanitized report and synchronized QA records. | Authenticated summary/inventory check: summary=65, total=65, returned=65; browser lane smoke; `python3 -I scripts/render_qa_case_tables.py --write`; `git diff --check`; `scripts/verify.sh docs`. | J4-01 Pass; no finding. |
| 3 | Reset the disposable restricted account and reverted appliance mutations to `os-nagios-ready`. | `scripts/vmlab revert`. | Snapshot restoration completed; no lab state remains claimed for this run. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): green (`verify: docs OK`).
- Hypothesis: No further case is needed for issue #105; J4-01 evidence and all required records are synchronized, and the VM was reverted.
- Next action (one specific step, not "continue"): Open a draft documentation PR for issue #105 with the report, traceability, rendered table, index, and progress checkpoint.

## Decisions and notes

- This is a QA-finding loop: do not modify product code or weaken expectations.
- Existing cases passed in issue #100 remain evidence only; no status is changed without an observed run on this QA round.
- The initial tree on `main` contained uncommitted QA artifact changes that have since merged in `a8fa51f7`; this dedicated worktree starts clean from `origin/main`.
- Human cases remain untested absent attributable human evidence.
- J4-01 was selected because it is an untested FS case with the fresh discovery baseline as its only application prerequisite. Searches of open and closed issues found no duplicate J4-01 finding.
- The first smoke attempt timed out at the default status timeout while the host table was still incomplete. It was not counted as case evidence, no product defect was inferred, and the fresh/restricted repeat passed before the case was claimed.
- No failure occurred, so the required repeat-before-filing branch was not invoked. The QA run filed no `qa-found` issue.
- `scripts/vmlab revert` restored `os-nagios-ready` after the case.
