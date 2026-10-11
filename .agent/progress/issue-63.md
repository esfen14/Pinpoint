# Issue #63: Complete QA loop readiness

Branch: `issue-63-qa-loop-readiness`
Status: in-progress (not blocked)

The planned `qa-found` case is no longer an issue dependency. The planted failure
was deliberately synthetic and proved the workflow without creating a product issue.
The remaining work is remote delivery only: main is merged locally and the release
verification is green. PR #88 still needs the owner to release the local branch so
GitHub can recalculate its mergeability and run CI.

## Finish condition

- [x] Complete traceability checker/matrix structure and test the docs drift checker; live rows still contain explicit untested/partial notes where evidence is incomplete.
- [x] Resumable qa-run and thin adapters with consistent safety and retest rules.
- [x] Labels, draft severity rubric and enforceable lab/browser boundaries.
- [x] Exact-pinned Playwright, credential-safe role setup, Vitest exclusion and both-role live smoke passes.
- [x] Complete the planted-failure J2/J3 dry run and sanitized report; both expected failures are recorded without filing a product issue.
- [ ] Full verification and CI green: the main-integrated local branch passes `scripts/verify.sh all`; remote PR #88 CI has not run because the release branch has not yet been pushed.

## Plan

- [x] Recovery: repair role-separated Playwright setup and forced-change handling in `client/e2e/`; verify offline, then both roles live.
- [x] Recovery: verify lab authentication and provision the approved restricted account.
- [x] Record and link the planted-failure evidence without changing the real J2-01 result or filing a synthetic product issue.

- [x] Restore accurate state; test and fix Playwright credential/artifact defaults.
- [x] Test-first complete traceability checker and matrix; integrate docs drift check.
- [x] Complete qa-run progress validation, safety, issue search and merged-fix retest semantics.
- [x] Complete role setup, forced-change handling, mock validation, repeatable Staff provisioning and teammate installation instructions.
- [x] Keep the broader incomplete J2/J3 acceptance cases recorded as partial; they are outside the single planted-failure round required by #63.
- [ ] Owner releases the verified branch, updates PR #88's stale checklist, and records green CI checks.

## Round log

| Round | Change | Check | Result |
|---|---|---|---|
| Recovery 1 | Restore progress; exact pin, fail-closed credentials, ignored auth/artifacts and disabled login captures; expand qa-run | `python3 -I scripts/test_playwright_safety.py` red then green (4 tests); `scripts/verify.sh docs` | passed offline checks only; live lab untouched |
| Recovery 2 | Separate role projects; add repeatable Staff provisioning, forced-change setup and Docker no-network runner | `python3 -I scripts/test_playwright_safety.py`; `scripts/playwright-lab` | 8 offline checks passed; 4/4 live setup/smoke tests passed |
| Recovery 3 | Added fix-found contract checks and executed the planted failure twice; removed scratch assertion | `scripts/verify.sh all` with required socket/DNS permissions | all green: docs, 2315 backend passed/14 skipped, 492 frontend passed/build/lint with 25 tracked warnings |
| Recovery 4 | Corrected planted-failure handling and audited PR state | two matching planted runs; `gh pr checks 88` | sanitized workflow report added; no product issue required; PR #88 has no reported checks |
| Recovery 5 | Merged `origin/main` locally and audited the issue/PR checklists; did not push at the owner's direction | `scripts/verify.sh all` with required socket/DNS permissions | all green on the integrated checkout: docs, 2315 backend passed/14 skipped, 492 frontend passed/build/lint with 25 tracked warnings |
| Release 6 | Re-fetched main, simulated the merge, ran the release suite, and corrected QA-document contradictions | `git merge-tree`; `scripts/verify.sh all` | no merge conflict markers; docs green; 2315 backend passed/14 skipped; 492 frontend passed/build/lint with 25 tracked warnings |

## State for the next session

- Last check run: `scripts/verify.sh all` with local-socket/DNS permission.
- Result: green: docs contracts and merge simulation; backend 2315 passed, 14 skipped; frontend 492 passed, build passed, lint 0 errors/25 tracked warnings.
- Hypothesis: implementation, live role coverage, planted-failure evidence, QA-table consistency and full local verification are complete.
- Next action: after the owner releases the branch, check PR #88's CI and update this file only with the observed remote result.

## Decisions and notes

### J2-08 update and resumed fresh-fixture checks

- Renamed J2-08 to Identity stability and explicit conflicts after rescans; added
  baseline classification, inventory/review comparisons after each scan and preservation
  of ownership/history. Counts in Network Health alone cannot establish a pass.
- Unattended upgrades released the lock within the second bounded wait; installer
  privilege step exited 0. Fresh appliance health: 60 passed, 0 warnings/failures.
- Confirmed deployed commit `b11e6dcb7ee3b9928af34f8d069addddc27dff9d`.
- `scripts/vmlab setup-admin` exited 0, but the subsequent authenticated J2-09 driver
  failed its login assertion BEFORE changing settings or starting a scan. The helper
  can return success on presence of old credential files without verifying login.
- Next action: inspect fresh installer credential handoff privately and reconcile
  the stale harness credentials; no guessed passwords, credential printing or bypass.
  Fresh-baseline J2-09 remains unexecuted. No test process remains running.


### Fresh baseline attempt: blocked by package-manager lock

- Executed `scripts/vmlab fresh main` with private output at
  `/tmp/opencode/qa63-fresh-main.log`. Snapshot restored and application deployment
  advanced to privilege provisioning; nmap installation failed because Ubuntu
  unattended-upgrades owned `/var/lib/dpkg/lock-frontend` (PID 8884).
- Waited up to 600 seconds for lock release before retrying the privilege step;
  command exited 124. Did not kill upgrades or remove package-manager locks.
- Appliance is now a partially provisioned fresh baseline, NOT the old healthy
  baseline. Earlier health/login passes do not certify its current state.
- Next action: check package-manager completion, rerun only the installer privilege
  step, then health and setup-admin before setting lab-only scan settings. Live
  J2-09 has not run on this new baseline. No tests are currently running.


### Revised expectations and targeted retest

- Confirmed PR #89 is merged; its actual diff documents intentional conflict isolation,
  not blanket approval of all duplicates. Updated QA_Test_Plan J2-08/J3-09 accordingly.
- Ran `server/.venv/bin/python -m pytest -c server/pytest.ini server/tests/unit/test_device_identity.py -k 'known_clone_key_hosts_keep_new_tcp_ports or removed_network_device_not_reassigned or devices_on_networks_that_were_not_scanned or address_unknown_host_reactivates or a_rescan_at_the_same_address' -q`: 6 passed, 51 deselected.
- Read-only appliance SQL confirmed app01 already has 8080 rows on IDs 5 and 10,
  respectively ADDRESS_UNKNOWN and ACTIVE. Neither can establish first-time insertion.
- Next action: establish an approved fresh appliance fixture before live J2-09;
  do not delete existing port/history rows to manufacture a pass. No reset performed
  and no long-running test launched in this round.


### Observed live preflight on resumed testing

- Owner released the VM and authorized testing; prior ownership restriction below is historical.
- `scripts/verify.sh backend`: 2315 passed, 14 skipped; frontend passed with 25 lint warnings.
- `scripts/vmlab health`: 60 passed, zero failures. This is not cleanup evidence.
- Authenticated API preflight using private harness credentials: login HTTP 200;
  discovery status Success; configured networks include BOTH `10.0.2.0/24` and
  `10.77.0.0/28`. No scan started: the former violates authorized scan scope.
- Actual Chromium login with private harness credentials reached `/dashboard`;
  browser HTTP requests restricted to the loopback application origin, no captures saved.
- Next live action: inspect discovery-settings update/restoration contract and approved
  #86 findings before narrowing configuration. Do not run the stock smoke command,
  which adds a lab range without removing the existing unauthorized range.
- #86 issue comment points to PR #89 (not PR #86); issue currently open. Findings
  describe intentional identity conflicts requiring operator review, not a verified fix.
- J2/J3 rescans and #82 measurement have NOT started. Existing cleanup and synthetic
  completion reports remain unsupported and need correction.


The earlier owner claim for #86 is historical. The owner released the shared VM on
2026-10-11 and authorized restricted-account provisioning and the remaining checks.
Fresh reset and Playwright installation were approved earlier, but lab ownership
restriction takes precedence. No PR merges. PR #88 remains draft, based on #62.
Previous fabricated dry-run evidence is withdrawn in its report; it is not a pass.
2026-10-11 live NCPA continuation on `67243ef5003c6ecd8f31f2c34c9036a49f4552fe`: J3-02
passed for `10.77.0.2` and `10.77.0.3` (16/16 helper checks); J3-06 passed with a
sanitized deployment log. J3-03 remains partial because database-level inspection
was not performed; J3-05 is blocked because `check_ncpa` was not enabled; J3-09 was
not captured with the required identity baseline. Report:
`docs/test-runs/2026-10-11-j2-j3-dry-run/REPORT.md`.
Full test timeout never means success. Earlier statements that role tests had not run
and browser safety was unenforced are superseded by the verified role-smoke evidence below.

### Current remaining work for PR #88

- Issue #93 is implemented on this branch: `scripts/vmlab setup-restricted` creates or
  resets a Staff account using private state files, and both role smokes passed live.
- Live report `docs/test-runs/2026-10-11-j2-j3-dry-run/REPORT.md` records J3-02/J3-06
  as passed, J3-03 as partial, J3-05 as blocked, and J3-09 as skipped.
- Broader QA evidence still includes clean-baseline J2-09, complete UI/config assertions
  for API-only J2 cases, J2-05, J3-03 database inspection, J3-05 with check_ncpa,
  J3-07/J3-08, and J3-09 identity baseline comparison.

### 2026-10-11 resumed audit

- Re-ran `scripts/verify.sh docs`: green. Existing uncommitted progress edits retained.
- Read current GitHub issues #63, #85 and #93. User released the lab for the remaining checks, including restricted-account provisioning and restoration.
- PR #91 is merged (2026-10-11); it is a synthetic no-product-fix PR. Its merge does not prove J2-08 was fixed.
- Source inspection contradicts earlier completion notes: restricted setup is selected by the admin setup project, forced-change handling is absent, and fix-found has conflicting filenames and unsupported CLI fields. Recovery steps above supersede those completion claims.

### Restricted-role live evidence

- Checkpoint `c8fcd586cf2072099d1ece0caf8482a0e2f67b17` was tested after resetting the temporary Staff account.
- `scripts/playwright-lab`: 4 passed, 0 failed, 0 skipped. The Docker container had no network; a private Unix socket exposed only the application loopback origin.
- The restricted setup observed and completed the forced password-change window. J9-04 then observed the Dashboard redirect, General-only Settings access and a Dashboard API 403.
- Sanitized report: `docs/test-runs/2026-10-11-role-smoke/REPORT.md`.

### Planted-failure execution

- A scratch-only Playwright assertion titled `J2-01 planted failure: impossible discovery banner` ran twice through `scripts/playwright-lab --project admin`.
- Both attempts loaded the administrator Dashboard and failed at the same intentionally impossible heading assertion. Each attempt reported one setup pass and one planted failure.
- The scratch spec and temporary config inclusion were removed immediately afterward. No J2-01 product result or traceability status was changed.
- The open/closed issue search for the exact planted symptom returned no match. No
  issue is needed because the failure was deliberately injected and does not describe
  product behavior. Sanitized report: `docs/test-runs/2026-10-11-qa-loop-planted-run/REPORT.md`.

### Current state

- #63 is not blocked and has no `qa-found` dependency. The only unticked finish item
  is remote delivery/CI. Local release evidence is complete, including a clean merge
  simulation against `origin/main`; PR #88 has not yet received the released head.
- No product code, scratch assertion or lab process remains unfinished or running. The temporary Staff account remains only on the disposable appliance and is reset safely by `scripts/vmlab setup-restricted`.
