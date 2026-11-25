# Issue #336: Give one demo container SSH so the NCPA Deployment wizard can be tested in the Docker lab

Branch: `issue-336-demo-ssh-ncpa`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue; the last three were added by owner decision (2026-11-25).

- [ ] One container accepts SSH password login with sudo; `demo/demo preflight` and `demo/demo setup` report it and the other 13 are unchanged.
- [ ] Tested, not assumed: in the NCPA Deployment page, Verify the host key, Deploy NCPA to that container, status Deployed NCPA with CPU, memory and disk checks OK once `check_ncpa` is enabled. Record the run in `docs/test-runs/`.
- [ ] Failure paths tried on it: wrong password, changed host key, Clean up after a failed deploy, and a redeploy.
- [ ] `demo/targets` tests updated for the relaxed catalog rule and passing.
- [ ] `docs/manuals/Local_Lab.md` ("What it cannot test") and `docs/manuals/NCPA_Deployment.md` updated; `Implementation_Status.md` updated if a gap closes.
- [ ] `scripts/verify.sh all` passes.
- [ ] The lab password stays in the private state folder, out of the repository and reports.
- [ ] The lab docs say how the container reaches `repo.nagios.com`.
- [ ] The design decisions are recorded in the spec.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| SSH password login with sudo on one container | 1 | offline tests; live `ssh` + `sudo -k -v` |
| Other 13 unchanged | 1 | `test_create.py`; live inspect |
| NCPA listener rule relaxed for that container only | 4 | `test_defense.py` |
| Init/service need of the deploy script | 2 | `test_systemctl_shim.py`; live deploy |
| Password private | 7 | `test_create.py`; grep of diff and report |
| Outbound access to repo.nagios.com, documented | 2, 8 | live deploy; docs |
| Decisions recorded in spec | 9 | `spec files/Agent_Workflow_and_CI.md` |
| Wizard happy path and failure paths | 2, 3 | `docs/test-runs/` report |

## Plan

1. [x] Catalog: `ssh-alt02` gets an `ncpa` 5693 listener; rule relaxed for it only. `demo/targets/catalog.py`, `manifest.json`, `test_defense.py`.
2. [x] Image: `ncpa-target` stage (sudo, curl, gpg, cached Nagios repo, `labadmin`, systemctl shim), default stage unchanged. `Dockerfile`, new `fetch_mirror.py`, `systemctl_shim.py` and tests.
3. [x] Node: with the password secret mounted, ssh-alt02 enables password SSH (UsePAM, sftp), sets the password, trusts a lab certificate, runs the mirror on 127.0.0.1:443, restarts NCPA on baseline. `node.py`, `test_runtime.py`.
4. [x] Creation: second image tag, private password file, mount, add-host, memory/pids; presenter validates the mount. `create.py`, `setup.py`, `presenter.py` and tests; new tests in `scripts/verify.sh`.
5. [x] `setup` plan and `preflight` report the deploy target.
6. [x] Live build of both images and an offline-network smoke of the deploy helper in a throwaway container.
7. [ ] Live lab run through the NCPA Deployment page, failure paths; report in `docs/test-runs/`. Needs the owner (sudo, appliance VM).
8. [x] Docs: `Local_Lab.md`, `NCPA_Deployment.md`, `demo/targets/README.md`, `demo/USAGE.md`, `Demo_Lab_QA_Handoff.md`, spec, `Implementation_Status.md`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written | none | plan only |
| 1 | Catalog rule and ssh-alt02 NCPA listener | demo/targets tests | green |
| 2 | ncpa-target image stage, mirror fetch (curl: server refuses urllib), systemctl shim | test_deploy_target.py; docker build --target ncpa-target | green, NCPA 3.5.1 mirrored |
| 3 | node.py deploy-target setup; creation, presenter, setup report | demo/targets + demo/appliance tests | green |
| 4 | Sandbox smoke: throwaway ssh-alt02 on an internal no-route network, server's real deploy functions | wrong password, changed fingerprint, deploy, restart, redeploy, cleanup, redeploy | all as expected; memory peak 262 MiB of 512; sandbox removed |
| 5 | Docs, spec, Implementation_Status (live wizard run marked not done) | scripts/verify.sh docs | green |

## State for the next session

- Last check run (exact command): for t in demo/targets/test_*.py demo/appliance/test_*.py; do python3 -I $t; done
- Result (first failing lines, or "green"): green
- Hypothesis: none
- Next action (one specific step, not "continue"): plan step 8 docs, then `scripts/verify.sh all`, then step 7 with the owner.

## Decisions and notes

- Issue #336 has no comments; owner said to work from the description (2026-11-25).
- Owner chose `ssh-alt02` (SSH port 2223) and "bake at build": image build downloads Nagios's signed repo files and the NCPA deb; ssh-alt02 serves them as `repo.nagios.com` on loopback with a lab certificate. The deploy script is unchanged and the containers stay isolated.
- Cached files keep Nagios's signature, so apt still verifies them with the real key.
- NCPA 3.5.1 deb: postinst needs `systemctl` (or `service`); depends only on libc6, libgcc-s1, libstdc++6, zlib1g. Image lacks sudo, curl, gpg, visudo, systemctl.
- `useradd` leaves the deploy account locked ("!"), which sshd refuses without PAM, so ssh-alt02 needs `UsePAM yes`.
- Deploy features switch on only when `/run/secrets/deploy-password` is mounted, so the legacy guest compose is unaffected.
- Existing labs need `demo/demo destroy --apply` then `setup --apply` (new image).
- Sandbox NCPA disk nodes are only `|data` and `|identity` (overlayfs is excluded), which are bind mounts of the host filesystem (92% full on 2026-11-25), so the live disk check reflects the host.
