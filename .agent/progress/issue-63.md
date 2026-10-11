# Issue #63: Complete QA loop readiness

Branch: `issue-63-qa-loop-readiness`
Status: in-progress

## Finish condition

- [ ] Complete traceability including BB cases, spec headings and observed evidence; tested drift checker.
- [ ] Resumable qa-run and thin adapters with consistent safety and retest rules.
- [ ] Labels, draft severity rubric and enforceable lab/browser boundaries.
- [ ] Exact-pinned Playwright, credential-safe role setup, Vitest exclusion and both-role live smoke passes.
- [ ] Actual planted-failure J2/J3 dry run and sanitized report.
- [ ] Full verification and CI green; retain draft while live checks pending.

## Plan

- [ ] Restore accurate state; test and fix Playwright credential/artifact defaults.
- [ ] Test-first complete traceability checker and matrix; integrate docs drift check.
- [ ] Complete qa-run progress validation, safety, issue search and merged-fix retest semantics.
- [ ] Complete role setup, forced-change handling, mock validation and teammate installation instructions.
- [ ] After owner releases lab, execute live role smoke and real dry run.
- [ ] Verify all and update PR checklist with only observed results.

## Round log

| Round | Change | Check | Result |
|---|---|---|---|
| Recovery 1 | Restore progress; exact pin, fail-closed credentials, ignored auth/artifacts and disabled login captures; expand qa-run | `python3 -I scripts/test_playwright_safety.py` red then green (4 tests); `scripts/verify.sh docs` | passed offline checks only; live lab untouched |

## State for the next session

- Last check run: `git status --short`
- Result: clean before recovery changes.
- Hypothesis: previous scaffolding lacks security protections and acceptance evidence.
- Next action: Add and run isolated browser configuration safety tests, fix failures without contacting the lab.

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


Owner currently owns shared VM for #86. Do not access/reset it, discover, deploy,
or mutate accounts/settings. Live role smoke and J2/J3 dry run wait for release.
Fresh reset and Playwright installation were approved earlier, but lab ownership
restriction takes precedence. No PR merges. PR #88 remains draft, based on #62.
Previous fabricated dry-run evidence is withdrawn in its report; it is not a pass.
2026-10-11 live NCPA continuation on `67243ef5003c6ecd8f31f2c34c9036a49f4552fe`: J3-02
passed for `10.77.0.2` and `10.77.0.3` (16/16 helper checks); J3-06 passed with a
sanitized deployment log. J3-03 remains partial because database-level inspection
was not performed; J3-05 is blocked because `check_ncpa` was not enabled; J3-09 was
not captured with the required identity baseline. Report:
`docs/test-runs/2026-10-11-j2-j3-dry-run/REPORT.md`.
Full test timeout never means success. Existing checker does not validate headings,
BB rows are absent, role tests have not run, and safety rules are not enforced yet.
