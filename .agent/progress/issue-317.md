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

1. [x] Test first: `scripts/test_lab_drift.py` (unittest, offline, temporary fixture installer directory): Dockerfile pin parsing, installer pin reading (baseline manifest and `setup/deploy-pinpoint-web.sh`), comparison, exit codes; the real `lab/appliance/Dockerfile` yields every pin.
2. [x] Implement `scripts/lab_drift.py` (comparison and command line: 0 match, 1 drift, 2 cannot read).
3. [x] Add `check-drift` to `scripts/lab`: installer directory from `VMLAB_INSTALLER_DIR`, else the vmlab config file, else the vmlab cache (cloned or fast-forwarded as `scripts/vmlab` does; a user's own clone is only read). Update the help text.
4. [x] Add the unit test to the docs stage of `scripts/verify.sh`.
5. [x] Document in `docs/manuals/Local_Lab.md` (command list and "How it matches a real appliance"); mention in `spec files/Agent_Workflow_and_CI.md` local-lab row if it lists commands.
6. [ ] Run `scripts/lab check-drift` against installer main, then `scripts/verify.sh all`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written | none | n/a |
| 1 | `scripts/test_lab_drift.py` (failed: module missing), then `scripts/lab_drift.py`, `scripts/lab check-drift`, `verify.sh` docs stage, `Local_Lab.md`, spec rows | `python3 -I scripts/test_lab_drift.py`; `VMLAB_CONFIG=/nonexistent scripts/lab check-drift` | 10 tests OK; 11 pins match installer main `9bc7150` (exit 0); a copy with two changed pins exits 1; a checkout without a manifest exits 2 |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `python3 -I scripts/test_lab_drift.py`
- Result (first failing lines, or "green"): green
- Hypothesis: n/a
- Next action (one specific step, not "continue"): run `scripts/verify.sh all`, then finish (section 5 of the workflow).

## Decisions and notes

Choices made, things ruled out, questions for a person.

- Pins compared: Ubuntu release (`FROM`), Nagios Core version, URL and SHA-256, plugins version, URL and SHA-256, `check_ncpa` URL and SHA-256, Python version, Gunicorn requirement. Installer sources: highest-numbered `setup/manifests/pp-mon-baseline-*.json` and `setup/deploy-pinpoint-web.sh`.
- The existing `server/tests/unit/test_lab_appliance_drift.py` stays as it is (it pins settings inside this repository; the new script compares with the installer checkout).
- `VMLAB_INSTALLER_DIR` in the environment wins over the vmlab settings file; the settings file wins over the cache. A user's own clone is only read, as in `scripts/vmlab`.
- The help text of `scripts/lab` printed `set -euo pipefail` (range one line too long); corrected while adding the new line.
- This machine's vmlab settings file points at a local installer clone 18 commits behind `origin/main`, with no baseline manifest, so plain `scripts/lab check-drift` exits 2 here until that clone is pulled. Not changed (a user's clone is never modified).
