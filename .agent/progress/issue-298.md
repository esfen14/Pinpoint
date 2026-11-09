# Issue #298: Split demo into Pinpoint device setup and Docker container setup (also covers #289)

Branch: `issue-298-demo-split-setup`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Issue #298 "Done when" plus its tasks; #289 is folded in by the owner's instruction (same branch, to avoid collisions). Tick an item only when a check proves it.

- [ ] A newcomer can set up the Pinpoint device (`demo/appliance/`) and the Docker devices (`demo/targets/`) from two separate guides and one setup script, run the demo from the `demo/README.md` index, and use `demo/USAGE.md` to take a device down, change its IP or add a port in one command each.
- [ ] No broken links or paths; `demo/` tests (moved) and `scripts/verify.sh all` pass.
- [ ] No personal-machine paths or UUIDs in the docs (#289).
- [ ] Legacy five-VM lab removed from `demo/` (owner decision: moved with `git mv` to `lab/legacy-vms/`, `scripts/vmlab` and `lab/*.py` repointed; clean-up chore opened as a follow-up issue).
- [ ] `demo/appliance/` and `demo/targets/` created with `git mv`; every path reference updated (code, tests, scripts, CI docs, `.agent/`, spec files, `docs/test-runs/*` links).
- [ ] `demo/README.md` rewritten as a short index (current lab, setup order, links); contradictory status lines reconciled (#289).
- [ ] `docs/manuals/Local_Lab.md`, `docs/plans/VM_Lab_Plan.md`, `docs/plans/Defense_Demo_Lab_Plan.md`, `lab/` cross-linked.
- [ ] `AGENTS.md` router and spec files updated for moved paths.
- [ ] Setup script `demo/demo setup`: plan-only without `--apply`, re-runnable; preflight, builds image and creates the fourteen containers from compose, attaches DHCP interfaces, enrolls, checks appliance/Windows attachment, pass/fail summary.
- [ ] Whole-lab lifecycle: `demo/demo up` (create if missing, start, restore baseline), `down`, `destroy` (only demo-owned containers/network, typed confirmation); documented in `USAGE.md`.
- [ ] Manual-only steps (appliance adapter, Windows credentials, discovery network, Nagios timing) printed as a checklist with a check command each.
- [ ] `demo/USAGE.md` cheat sheet (down/up service, dhcp-move, address-mode, ports open/close/restore, reset, expected Pinpoint delays).
- [ ] One front door: `demo/demo`; `Pinpoint-Demo-faults.sh` kept as thin alias or removed.
- [ ] `demo/demo help` and per-command `--help` show the same examples as `USAGE.md`.
- [ ] Tests for setup plan and preflight output (no containers).

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| #298 delete legacy lab (decided) | Legacy lab removed from demo/ (owner chose move, not delete) | `ls demo`, `scripts/vmlab` help, grep demo_lab |
| #298 two folders via git mv | appliance/targets item | `git log --follow`, `git status` renames |
| #298 update hard-coded paths | path item | `grep -rn demo/defense`, `scripts/verify.sh all` |
| #298 README index | README item | read file, link check in `verify.sh docs` |
| #298 setup script, containers, lifecycle | setup, lifecycle items | new tests under `demo/targets/` |
| #298 manual checklist, USAGE.md, front door, help | checklist, USAGE, front door, help items | tests + read |
| #289 index, status lines, machine values, cross-links | README, no-personal-paths, cross-link items | `grep` for UUID / `~/.local/share` |

## Plan

1. [x] Branch, read specs, write this plan and checkpoint (`.agent/progress/issue-298.md`).
2. [x] Move legacy lab: `git mv demo/demo_lab.py demo/smoke_test.py demo/manual lab/legacy-vms/`; repoint `scripts/vmlab`, `lab/alerts_run.py`, `lab/ncpa_run.py`; run `scripts/vmlab` help / syntax check.
3. [ ] Structure move: `git mv` appliance docs (PRESENTER_SETUP, WINDOWS_READY, appliance parts of DEMO_READY) to `demo/appliance/`; `demo/defense/*` to `demo/targets/`; fix `demo/demo`, Dockerfile, `bootstrap.py`, `sampler.py`, tests, `Pinpoint-Demo-faults.sh`, `scripts/verify.sh`; run moved tests.
4. [ ] Update path references: spec files, `AGENTS.md`, `docs/plans/*`, `docs/qa/Automation_Readiness.md`, `docs/test-runs/*` links, `.agent/` docs.
5. [ ] Docs: rewrite `demo/README.md` index, `demo/appliance/README.md`, `demo/targets/README.md`; reconcile status lines; strip UUIDs/laptop paths; cross-link Local_Lab, VM_Lab_Plan, Defense_Demo_Lab_Plan, `lab/`.
6. [ ] Tests first then `demo/targets/setup.py`: plan, preflight, `--apply` create/enroll, manual checklist; wire `demo/demo setup`.
7. [ ] Tests first then `up` / `down` / `destroy` (typed confirmation, demo-owned only).
8. [ ] Front door: `demo/demo` accepts presenter commands directly, `Pinpoint-Demo-faults.sh` becomes alias; `help` and `--help` examples; `demo/USAGE.md`, test that help examples match USAGE.
9. [ ] Spec files + `Implementation_Status.md`, `scripts/verify.sh docs`, `scripts/verify.sh all`, finish (section 5), open follow-up chore issue for removing old VM references.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Branch created, issue read, plan written | n/a | n/a |
| 1 | git mv demo_lab.py, smoke_test.py, manual/ to lab/legacy-vms/; repointed scripts/vmlab, lab/alerts_run.py, lab/ncpa_run.py | bash -n scripts/vmlab; py_compile lab files; alerts_run.py --help | green (vmlab targets needs live VBox, not run) |

## State for the next session

- Last check run (exact command): bash -n scripts/vmlab && python3 -m py_compile lab/alerts_run.py lab/ncpa_run.py lab/legacy-vms/*.py
- Result (first failing lines, or "green"): green
- Hypothesis: moves are mechanical; setup/lifecycle need new code in presenter-style modules
- Next action: step 2, `git mv demo/demo_lab.py demo/smoke_test.py demo/manual lab/legacy-vms/` and repoint scripts/vmlab line 541 and lab/alerts_run.py line 24

## Decisions and notes

- Owner asked for #298 first, then #289, on one branch (`issue-298-...`); one progress file covers both. PR will say `Closes #298` and `Closes #289`.
- Legacy lab: issue says delete; `scripts/vmlab` and `lab/*.py` depend on `demo_lab.py`. Owner decision: move to `lab/legacy-vms/` for now, open a chore to remove old-VM references and test with Docker containers instead.
- Owner question: Docker vs VMs for testing. Recommendation: Docker for routine/fast testing (disposable, scriptable, no VirtualBox); keep a VM only for what containers cannot prove (installer, systemd, Windows/NCPA).
