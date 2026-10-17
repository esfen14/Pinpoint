# Issue #167: VM lab setup-admin misreads current installer label and accepts stale host login state

Branch: `issue-167-setup-admin-state`
Status: in-progress

## Finish condition

- [ ] Parse both the previous email label and the current temporary-placeholder label without exposing credential values.
- [ ] Existing host state is not reported as a configured login for a fresh appliance without validating that it applies to the actual endpoint and that first-run setup is complete.
- [ ] Add isolated regression tests for current/previous labels and stale host state; relevant verification passes.
- [ ] Update the VM lab documentation to reflect the corrected setup behavior.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Parse old and current installer email labels | 1 | Isolated parser tests using synthetic credential text; assert credentials are absent from output |
| Reject stale host state unless valid for endpoint and setup complete | 2 | Isolated state validation tests for login failure, pending setup, and configured endpoint |
| Regression coverage and verification | 3 | `python3 -I scripts/test_vmlab_setup_admin.py` and `scripts/verify.sh docs` |
| Document corrected VM lab setup behavior | 4 | Updated `docs/plans/VM_Lab_Plan.md`; `scripts/verify.sh docs` |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] Add isolated failing tests for credential label parsing and host-state validation (`scripts/test_vmlab_setup_admin.py`, `scripts/vmlab_setup_admin.py`).
2. [ ] Implement safe label parsing and endpoint/setup validation for existing state (`scripts/vmlab`, `scripts/vmlab_setup_admin.py`).
3. [ ] Update VM lab setup documentation and current implementation status (`docs/plans/VM_Lab_Plan.md`, `spec files/Implementation_Status.md`).
4. [ ] Run focused regression and docs verification; record results (`scripts/test_vmlab_setup_admin.py`, progress file).

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan and requirement coverage recorded | Source/spec inspection | Ready to add failing regressions |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `rg -n "setup-admin|vmlab" 'spec files/Implementation_Status.md' 'spec files/Agent_Workflow_and_CI.md'`
- Result (first failing lines, or "green"): confirmed issue is listed as open in Implementation_Status and setup-admin completes first-run setup.
- Hypothesis: extract deterministic parsing/state decisions into a small Python helper imported by the script's inline Python, and verify stored credentials against the currently configured web endpoint before accepting them.
- Next action (one specific step, not "continue"): add failing unit tests for both credential labels and rejection of stale/unconfigured login state.

## Decisions and notes

- Work is isolated in `/tmp/issue167` on the required issue branch. Existing root worktree edits remain untouched.
- Do not operate the VM or Docker lab; this issue asks for isolated regressions and script/doc changes.
