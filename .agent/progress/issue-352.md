# Issue #352: Discovery silently drops hosts that share an SSH host key when their MACs are randomized

Branch: `issue-352-shared-ssh-key`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] A regression test fails before the fix and passes after: a known device owns an SSH host key, and a later scan sees that key at other addresses in the same network with no hardware MAC. The hosts are not silently dropped.
- [x] The intended behavior (separate records, or a review item naming the unmonitored addresses) is decided and stated in `spec files/Device_Inventory_Requirements.md` and `Data_Model_and_Integrations.md`.
- [x] A true multi-NIC device still resolves to one record, and the #67 and #59 cases still pass.
- [x] A regression test: several known devices share a key, each at its own address with no hardware MAC; a rescan updates every one of them.
- [x] `scripts/verify.sh backend` passes.
- [x] The lab steps above are repeated and the result is recorded under `docs/test-runs/`.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| New addresses showing a known key are not dropped | 1 | |
| Intended behavior decided and specified | 2 | |
| Multi-NIC, #67, #59 unchanged | 3 | |
| Known devices sharing a key are updated on rescan (owner comment) | 4 | |
| Backend verification | 5 | |
| Lab repeat | 6 | |

## Plan

1. [x] Failing tests for both issue cases, merge-stays-merged, own NCPA cert, self-heal: `server/tests/unit/test_device_identity.py`
2. [x] Shared-key rules in `server/app/network_discovery/device_identity.py` (`resolve_observation`, `reconcile_scan`)
3. [x] Single-device scan checks the key owner's address: `identity_probes.py`, `create_host_cfg.py`, tests
4. [x] Security review of the diff; specs: `Device_Inventory_Requirements.md`, `Data_Model_and_Integrations.md`, `Implementation_Status.md`
5. [ ] `scripts/verify.sh backend` and `all`
6. [x] Lab repeat (needs the user's approval for `scripts/lab reset`) and report under `docs/test-runs/`

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan | - | - |
| 1 | Tests and shared-identifier rules | `pytest tests/unit/test_device_identity.py` | 9 red, then 71 green |
| 2 | Single-device scan owner check | `scripts/verify.sh backend` | green, 4516 passed, 14 skipped |
| 3 | Specs, review manual, security review | `scripts/verify.sh docs` | green |
| 4 | Lab runs and report | issue steps on the Docker lab | pass |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): issue scenarios on the Docker lab (see the test-run report)
- Result (first failing lines, or "green"): pass
- Hypothesis: ready to finish
- Next action (one specific step, not "continue"): run `scripts/verify.sh all`, then work section 5 of the workflow

## Decisions and notes

- User chose: a new address showing a known device's key, with no hardware MAC, becomes a separate monitored record plus a duplicate-identity review item. Hardware-MAC behaviour is unchanged.
- User approved changing the sensitive module `app/network_discovery/`. No database schema change.
- The user approved using the lab after the code was done.
- The owner comment's checkbox was added to the issue body with the user's approval.
- Rules cover any strong identifier seen at two or more addresses (SSH key or NCPA certificate); with SSH only, a clone sharing both would get a new record on every scan.
- Security review of the diff: no shell commands, credentials or secret logging added. New network access: a single-device scan reads the SSH host key and NCPA certificate of the identifier owner's stored address (saved networks only).
- Follow-up outside this issue (not filed yet): the page cannot dismiss a duplicate identity review.
