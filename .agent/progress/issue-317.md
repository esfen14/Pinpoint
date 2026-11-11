# Issue #317: System Refinement Add a drift guard between lab/appliance and the installer

Branch: `issue-317-lab-drift-guard`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] A script (`scripts/lab check-drift`) compares the pinned versions in `lab/appliance/Dockerfile` with the PinPoint-Installer, reusing the cached clone `scripts/vmlab` keeps or `VMLAB_INSTALLER_DIR`, and exits non-zero on a difference.
- [ ] Unit test for the comparison.
- [ ] Documented in `Local_Lab.md`: run it when the installer changes.
- [ ] Starts from a clean baseline (after the #316 audit): the check passes against the current installer.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Script compares Dockerfile pins with the installer, non-zero on a difference | Item 1 | `python3 -I scripts/test_lab_drift.py`; `scripts/lab check-drift` |
| Reuses the vmlab cached clone or `VMLAB_INSTALLER_DIR` | Item 1 | `scripts/lab check-drift` with and without `VMLAB_INSTALLER_DIR` |
| Unit test for the comparison | Item 2 | `python3 -I scripts/test_lab_drift.py`, in `scripts/verify.sh docs` |
| Documented in `Local_Lab.md` | Item 3 | `scripts/verify.sh docs`; read the section |
| After the audit, clean baseline | Item 4 | `scripts/lab check-drift` exits 0 on installer main |
| Not a CI job (decided in #306) | Out of scope by decision | The live comparison is not added to `verify.sh` or CI; only its offline unit test is |

## Plan

Ordered steps the agent will take. Write the whole plan before changing code;
revise it in place and say why in the round log. Name the files each step touches.

1. [ ] Test first: `scripts/test_lab_drift.py` (unittest, offline, temporary fixture installer directory): Dockerfile pin parsing, installer pin reading (baseline manifest and `setup/deploy-pinpoint-web.sh`), comparison, exit codes; the real `lab/appliance/Dockerfile` yields every pin.
2. [ ] Implement `scripts/lab_drift.py` (comparison and command line: 0 match, 1 drift, 2 cannot read).
3. [ ] Add `check-drift` to `scripts/lab`: installer directory from `VMLAB_INSTALLER_DIR`, else the vmlab config file, else the vmlab cache (cloned or fast-forwarded as `scripts/vmlab` does; a user's own clone is only read). Update the help text.
4. [ ] Add the unit test to the docs stage of `scripts/verify.sh`.
5. [ ] Document in `docs/manuals/Local_Lab.md` (command list and "How it matches a real appliance"); mention in `spec files/Agent_Workflow_and_CI.md` local-lab row if it lists commands.
6. [ ] Run `scripts/lab check-drift` against installer main, then `scripts/verify.sh all`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written | none | n/a |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: n/a
- Next action (one specific step, not "continue"): write `scripts/test_lab_drift.py` and confirm it fails because `scripts/lab_drift.py` does not exist.

## Decisions and notes

Choices made, things ruled out, questions for a person.

- Pins compared: Ubuntu release (`FROM`), Nagios Core version, URL and SHA-256, plugins version, URL and SHA-256, `check_ncpa` URL and SHA-256, Python version, Gunicorn requirement. Installer sources: highest-numbered `setup/manifests/pp-mon-baseline-*.json` and `setup/deploy-pinpoint-web.sh`.
- The existing `server/tests/unit/test_lab_appliance_drift.py` stays as it is (it pins settings inside this repository; the new script compares with the installer checkout).
