# Issue #167: VM lab setup-admin misreads current installer label and accepts stale host login state

Branch: `issue-167-setup-admin-state`
Status: in-progress

## Finish condition

- [x] Parse both the previous email label and the current temporary-placeholder label without exposing credential values.
- [x] Existing host state is not reported as a configured login for a fresh appliance without validating that it applies to the actual endpoint and that first-run setup is complete.
- [x] Add isolated regression tests for current/previous labels and stale host state; relevant verification passes.
- [x] Update the VM lab documentation to reflect the corrected setup behavior.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Parse old and current installer email labels | 1 | `test_previous_and_current_installer_labels_complete_setup` in `scripts/test_vmlab_setup_admin.py`; asserts all stored credential values are absent from output |
| Reject stale host state unless valid for endpoint and setup complete | 2 | `test_stale_state_is_rejected_at_current_endpoint`, `test_saved_login_requires_explicit_completed_setup`, `test_valid_saved_login_is_confirmed_through_current_endpoint` |
| Regression coverage and verification | 3 | `python3 -I scripts/test_vmlab_setup_admin.py` and `scripts/verify.sh docs` |
| Document corrected VM lab setup behavior | 4 | Updated `docs/plans/VM_Lab_Plan.md`; `scripts/verify.sh docs` |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [x] Add isolated failing tests for credential label parsing and host-state validation (`scripts/test_vmlab_setup_admin.py`).
2. [x] Implement safe label parsing and endpoint/setup validation for existing state; wire tests into docs verification (`scripts/vmlab`, `scripts/verify.sh`).
3. [x] Update VM lab setup documentation, owning workflow specification and current implementation status (`docs/plans/VM_Lab_Plan.md`, `docs/plans/Installer_Handoff.md`, `spec files/Agent_Workflow_and_CI.md`, `spec files/Implementation_Status.md`).
4. [x] Run focused regression and docs verification; record results (`scripts/test_vmlab_setup_admin.py`, progress file).

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Plan and requirement coverage recorded | Source/spec inspection | Ready to add failing regressions |
| 1 | Added actual-command isolated regressions; recognized both labels; authenticated saved state and checked /me setup flags; sanitized output; wired verification | `python3 -I scripts/test_vmlab_setup_admin.py` (red then green), `bash -n scripts/vmlab`, `scripts/verify.sh docs` | Original command failed 8 subcases across 5 tests; fixed command passes all 5 tests and docs verification |
| 2 | Replaced obsolete setup workaround notices with current label parsing and saved-login validation contract; documented no live rerun | `scripts/verify.sh docs && git diff --check` | green |
| 3 | Finish audit confirmed unchanged issue; strengthened secret-output and failure preservation coverage; installed checkout-local dependencies | `python3 -I scripts/test_vmlab_setup_admin.py && scripts/verify.sh docs && git diff --check` | green; 7 tests pass, including both labels and stale-state subcases |
| 4 | Added preflight recheck before new saved-login API validation; regression reproduces changed ownership after credential read and blocks all API calls | `python3 -I scripts/test_vmlab_setup_admin.py` (red then green), `bash -n scripts/vmlab`, `scripts/verify.sh docs && git diff --check` | green; 8 tests pass; full verification is running backend and frontend stages independently of this docs-only change |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `python3 -I scripts/test_vmlab_setup_admin.py && bash -n scripts/vmlab && scripts/verify.sh docs && git diff --check`
- Result (first failing lines, or "green"): green; 8 isolated setup tests, 18 ownership tests and all docs checks pass.
- Hypothesis: all issue requirements have current-session focused proofs; required full verification and CI remain.
- Next action (one specific step, not "continue"): inspect completion of `scripts/verify.sh all` (log `/tmp/issue167-verify-all.log`, exec session 27899), then remove the progress file and open the PR if green. Final docs checks were rerun after the scoped preflight recheck; backend/frontend files have not changed.

## Decisions and notes

- Work is isolated in `/tmp/issue167` on the required issue branch. Existing root worktree edits remain untouched.
- Do not operate the VM or Docker lab; this issue asks for isolated regressions and script/doc changes.
- Plan refinement: actual-command tests use fake SSH/preflight/API boundaries, so no new production helper module is needed. Existing inline Python remains the smallest implementation.
- Injection and secret review: credentials remain in environment/stdin/private state, never command arguments; no untrusted command interpolation added. Generic errors suppress API messages and transport details; setup state uses umask 077. No live lab calls occur in the tests.
- Finish audit: `gh issue view 167 --json number,title,body,comments,state` confirmed unchanged requirements and no comments. All requirements map to the four finish items; none omitted. Failure-path tests assert guest credential preservation and unchanged saved state.
- Final boundary review: saved-state validation now rechecks preflight after the SSH credential read. This prevents a failed/changed ownership observation from falling through to the newly added API requests. Regression observed failure before the recheck and green after it.
