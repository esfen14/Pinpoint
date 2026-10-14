# Test Runs

The record of what was tested, on which commit, and what happened. One folder
per run; the plan that drives a run stays in
[`server/tests/plans/`](../../server/tests/plans/README.md).

## Where results go

| Kind | Where | Committed? | Kept |
|---|---|---|---|
| Automated suites in CI (pytest, vitest) | GitHub Actions run, `test-results` artifact (JUnit XML) | No | 30 days |
| Local runs while developing | `test-results/` in the repo root | No (git-ignored) | Until deleted |
| Live-lab and acceptance runs: summary | `docs/test-runs/<date>-<slug>/REPORT.md` | **Yes** | Permanent |
| Live-lab raw evidence (logs, Nagios configs, captures, screenshots) | The harness `output_root` on the lab host (for example `/home/paeng/pinpoint-test-results`) | **Never** | Lab owner |

Raw evidence can hold credentials, SNMP communities, host keys and lab
addresses, so it never enters the repository. The report records what the
evidence showed and where to find it.

## Starting a run

```bash
scripts/new_test_run.sh <slug> [path/to/test-plan.md]
```

This creates `docs/test-runs/<date>-<slug>/REPORT.md` from
[`TEMPLATE.md`](TEMPLATE.md) with the date and commit filled in. Fill the case
table while you test, not afterward.

## Rules

- Name the exact commit tested. A result without a commit is not reproducible.
- One row per plan case: `Pass`, `Fail`, `Blocked` or `Skipped`, and why.
- Every `Fail` and `Blocked` links a GitHub issue. Defects live in issues, not in
  the report.
- Sanitize before committing: no passwords, tokens, keys, community strings,
  private addresses beyond the documented lab range, or full command output that
  contains them.
- `Pass` means the behavior was observed running. Reading code or a diff is not a
  test: record it as `Skipped` or `Blocked` with the reason, and say "inspected" in the
  notes. A run with no observed behavior is not `Pass` overall, and does not change an
  earlier run's index row.
- A report is never edited to change a result. Re-test in a new run and link it. The one
  exception is a result that overstated its evidence: correct it in place, say so in the
  report, and fix the index row in the same change.

## Index

| Run | Kind | Commit | Result | Report |
|---|---|---|---|---|
| [2026-10-14 issue-129-resource-compatibility](2026-10-14-issue-129-resource-compatibility/REPORT.md) | Local config regression/full verification and installed plugin/ownership inspection | `87e00907`, `61ebb946` | Partial: local checks pass; secure transport and installer ownership mechanism block live sign-off | [REPORT.md](2026-10-14-issue-129-resource-compatibility/REPORT.md) |
| [2026-10-14 issue-141-docker-history](2026-10-14-issue-141-docker-history/REPORT.md) | Docker Nagios host acknowledgement/recovery/reproblem | `43c1be42` | Partial: host list/filter/detail pass; service and manual-unacknowledge not run | [REPORT.md](2026-10-14-issue-141-docker-history/REPORT.md) |
| [2026-10-14 issue-133-owner-path-recheck](2026-10-14-issue-133-owner-path-recheck/REPORT.md) | Existing VM, independent real-event owner History path repeat | app `4dd006e3` synced; harness base `93b8361e` plus test assertion | Pass for exact filtered CRITICAL/recovery/detail/Refresh path; no PR approval implied | [REPORT.md](2026-10-14-issue-133-owner-path-recheck/REPORT.md) |
| [2026-10-14 issue-133-poll-reliability](2026-10-14-issue-133-poll-reliability/REPORT.md) | Existing VM reversible SSH fault, still-failing ack and repeat recovery poll | app `4dd006e3` synced, branch `30bd3676` before report | Partial: lifecycle/idempotence pass; no load or failed-CGI run | [REPORT.md](2026-10-14-issue-133-poll-reliability/REPORT.md) |
| [2026-10-14 issue-133-more-browser](2026-10-14-issue-133-more-browser/REPORT.md) | Existing VM real-event browser plus intercepted pagination/error responses | app `4dd006e3` synced; test at `f1766fa2` plus new assertions | Partial: browser pass; actual backend second page and CGI outage untested | [REPORT.md](2026-10-14-issue-133-more-browser/REPORT.md) |
| [2026-10-14 issue-133-expanded](2026-10-14-issue-133-expanded/REPORT.md) | Existing VM, expanded real-event History Playwright and restricted permission | app source `4dd006e3` synced; new browser spec uncommitted during run | Partial: expanded browser and guard pass; full manual audit/CI/review outstanding | [REPORT.md](2026-10-14-issue-133-expanded/REPORT.md) |
| [2026-10-14 issue-133-live](2026-10-14-issue-133-live/REPORT.md) | Existing VM, real SSH service acknowledgement/recovery and focused History Playwright walk | app source `4dd006e3` synced without changing VM Git HEAD; browser spec uncommitted during run | Partial: auto-resolution and focused real-event browser interactions pass; full audit/live edge cases/review pending | [REPORT.md](2026-10-14-issue-133-live/REPORT.md) |
| [2026-10-13 issue-113-vm-quiet-mailbox-check](2026-10-13-issue-113-vm-quiet-mailbox-check/REPORT.md) | Owner-reported no quiet-window web02 CRITICAL mail; previously confirmed outside web01 CRITICAL delivery | app `1ca2c757`, installer mail module `697869e` | Pass for paired email comparison, with separate targets and owner-reported mailbox evidence | [REPORT.md](2026-10-13-issue-113-vm-quiet-mailbox-check/REPORT.md) |
| [2026-10-13 issue-113-vm-mailbox-confirmation](2026-10-13-issue-113-vm-mailbox-confirmation/REPORT.md) | Owner-confirmed web01 CRITICAL and RECOVERY mailbox receipt, correlated with Nagios and SMTP | app `1ca2c757`, installer mail module `697869e` | Partial: quiet-trial mailbox absence not confirmed | [REPORT.md](2026-10-13-issue-113-vm-mailbox-confirmation/REPORT.md) |
| [2026-10-13 issue-113-vm-email-delivery](2026-10-13-issue-113-vm-email-delivery/REPORT.md) | VM quiet/outside CRITICAL dispatch with Gmail SMTP acceptance; owner-confirmed prior recovery inbox arrival | app `1ca2c757`, installer mail module `697869e` | Partial: specific CRITICAL inbox receipt and quiet-trial absence await owner check | [REPORT.md](2026-10-13-issue-113-vm-email-delivery/REPORT.md) |
| [2026-10-13 issue-113-vm-mail-transport](2026-10-13-issue-113-vm-mail-transport/REPORT.md) | Incremental installer mail-transport update on existing VM | app `560ad780`, installer `697869e` (privileges module only) | Partial: transport and scoped helper verified; SMTP send and inbox delivery untested | [REPORT.md](2026-10-13-issue-113-vm-mail-transport/REPORT.md) |
| [2026-10-13 issue-113-vm-service-retest](2026-10-13-issue-113-vm-service-retest/REPORT.md) | Fresh VM policy, service CRITICAL inside/outside quiet hours and browser save/reload | app `1ca2c757` | Partial: Nagios dispatch and browser passed; inbox delivery unverified | [REPORT.md](2026-10-13-issue-113-vm-service-retest/REPORT.md) |
| [2026-10-13 issue-113-vm-initial](2026-10-13-2026-10-13-issue-113-notification-policy-vm/REPORT.md) | Initial VM policy apply, before forced service retest | app `1ca2c757` | Partial: configuration accepted; service comparison not run at that time | [REPORT.md](2026-10-13-2026-10-13-issue-113-notification-policy-vm/REPORT.md) |
| [2026-10-13 issue-113-notification-policy](2026-10-13-issue-113-notification-policy/REPORT.md) | Docker lab policy apply, Nagios validation, forced host DOWN inside/outside quiet hours | `6fb8df73`, `b5937ec4`, `6c2a5be1` (case commits in report) | Partial: host/service timing and browser flow passed; VM/email not exercised | [REPORT.md](2026-10-13-issue-113-notification-policy/REPORT.md) |
| [2026-10-14 issue-119](2026-10-14-issue-119-flap-detection/REPORT.md) | Existing lab appliance: flap detection settings, generated Nagios config, flapping history and filter | `efbd2525` (stacked on #123 `5d0b5dd6`) | Partial: 8 pass, 2 skipped (forced flap, browser click-through); no findings | [REPORT.md](2026-10-14-issue-119-flap-detection/REPORT.md) |
| [2026-10-12 demo-ready](2026-10-12-demo-ready/REPORT.md) | Demo appliance and target setup | app `6b558198`, installer `2859361` | Partial: installation, five-target discovery, monitoring baseline, web01 NCPA and installed snapshot verified; full presenter walkthrough pending | [REPORT.md](2026-10-12-demo-ready/REPORT.md) |
| [2026-10-12 fs-j4-inventory](2026-10-12-fs-j4-inventory/REPORT.md) | FS QA follow-up: fresh VM-lab Plugin Manager inventory | `24cac847` appliance deployment | Pass: J4-01 observes matching summary and inventory counts of 65; lab reverted | [REPORT.md](2026-10-12-fs-j4-inventory/REPORT.md) |
| [2026-10-12 fs-vm-lab](2026-10-12-fs-vm-lab/REPORT.md) | FS QA round: appliance/service wiring, restricted discovery smoke and isolated FS regression cases | `bb7e967` appliance deployment | Partial: J1-02, J2-01, J4-08, J5-08 and J7-09 pass; no findings filed | [REPORT.md](2026-10-12-fs-vm-lab/REPORT.md) |
| [2026-10-11 issue-92](2026-10-11-issue-92/REPORT.md) | Issue #92 mocked availability report checks | `e7eaecea` | Partial: targeted backend and docs checks pass; full backend/frontend/all pending | [REPORT.md](2026-10-11-issue-92/REPORT.md) |
| [2026-10-11 qa-loop-planted-run](2026-10-11-qa-loop-planted-run/REPORT.md) | Synthetic QA workflow probe, not a product test | `1bae5171` plus removed scratch assertion | Pass: identical expected failure twice; no product issue filed | [REPORT.md](2026-10-11-qa-loop-planted-run/REPORT.md) |
| [2026-10-11 role-smoke](2026-10-11-role-smoke/REPORT.md) | VM lab Playwright administrator and restricted Staff smoke | `c8fcd586` | Pass: 4/4 setup and smoke tests; J1-04/J9-04 browser-role coverage | [REPORT.md](2026-10-11-role-smoke/REPORT.md) |
| [2026-10-11 j2-j3-dry-run](2026-10-11-j2-j3-dry-run/REPORT.md) | VM lab J2/J3 continuation | `67243ef5` | Partial: J3-02 and J3-06 pass; J3-03 partial; J3-05 blocked; J3-09 skipped | [REPORT.md](2026-10-11-j2-j3-dry-run/REPORT.md) |
| [2026-10-11 qa-dry-run-j2-j3-second](2026-10-11-qa-dry-run-j2-j3-second/REPORT.md) | VM lab continuation and attributed handoff (#62) | `ebb5aea3` | Partial: 5 handoff passes, 1 fail (#86), 3 partial, 2 skipped; settings restored | [REPORT.md](2026-10-11-qa-dry-run-j2-j3-second/REPORT.md) |
| [2026-10-09 qa-dry-run-j2-j3](2026-10-09-qa-dry-run-j2-j3/REPORT.md) | VM lab, dry run of QA plan cases J1-01, J2 and J3 (issue #62) | `65b63e5b` (app code same as `main` `13076192`) | Partial: 13 pass, 1 fail (J2-09), 6 not run; plan steps corrected | [REPORT.md](2026-10-09-qa-dry-run-j2-j3/REPORT.md) |
| [2026-10-10 issue-80](2026-10-10-issue-80/REPORT.md) | VM lab, fresh install, per-user email alert setting, account.alerts, host and service alert email through Gmail | app `f0f934db`, re-checked on merged `6c6d0102`, installer `c5cd3de` | Pass; mail not re-sent on the merged commit; opted-out inbox check tester-reported | [REPORT.md](2026-10-10-issue-80/REPORT.md) |
| [2026-10-10 issue-60](2026-10-10-issue-60/REPORT.md) | VM lab, isolated fresh install, check cadence and rollback | app `bcf5f614`, installer `2859361` | Partial: live cadence and rollback pass; paired full-hour row measurement pending | [REPORT.md](2026-10-10-issue-60/REPORT.md) |
| [2026-10-10 issue-67-retest](2026-10-10-issue-67-retest/REPORT.md) | Fresh VM gateway removal and two-rescan J2-08 | app `72b51602` | Pass for address and port ownership; browser UI not driven | [REPORT.md](2026-10-10-issue-67-retest/REPORT.md) |
| [2026-10-10 issue-67](2026-10-10-issue-67/REPORT.md) | VM lab, removed-network rescan on existing appliance | app `f9f03bcf` | Partial: existing rows stable; fresh gateway reproduction and J2-08 not verified | [REPORT.md](2026-10-10-issue-67/REPORT.md) |
| [2026-10-10 issue-66](2026-10-10-issue-66/REPORT.md) | VM lab, narrow-to-single/ranged TCP rescans and legacy01 NCPA | app `c1f8fa74` | Pass for #66 port and NCPA checks | [REPORT.md](2026-10-10-issue-66/REPORT.md) |
| [2026-10-10 issue-59](2026-10-10-issue-59/REPORT.md) | VM lab, fresh install, repeated discovery and NCPA deployment to alternate-port SSH target | app `431f50ae` | Pass for one active record at `10.77.0.6`; scan waits timed out | [REPORT.md](2026-10-10-issue-59/REPORT.md) |
| [2026-10-08 issue-47-ncpa-live](2026-10-08-issue-47-ncpa-live/REPORT.md) | VM lab, live SSH/NCPA deployment for issue #47 | `7735fc1e` | Pass for #47 deployment/log behavior | [REPORT.md](2026-10-08-issue-47-ncpa-live/REPORT.md) |
| [2026-10-08 vm-lab-remaining](2026-10-08-vm-lab-remaining/REPORT.md) | VM lab, fresh install of the #43 fix, alerts, sync, up/down/revert | app `d8dc63e0`, `main` `483c8bdc` | Pass | [REPORT.md](2026-10-08-vm-lab-remaining/REPORT.md) |
| [2026-10-08 ncpa-fresh-run](2026-10-08-ncpa-fresh-run/REPORT.md) | VM lab, clean appliance with the #45 installer fix, NCPA deploy, all six services, negative tests | app `ed9f2c2`, installer `e471a1b8`, repeated on merged `2859361d` | Pass for #45 behavior; defect #59 found (duplicate device record) | [REPORT.md](2026-10-08-ncpa-fresh-run/REPORT.md) |
| [2026-10-08 ncpa-repeat-run](2026-10-08-ncpa-repeat-run/REPORT.md) | VM lab, partial recheck of the #45 installer fix (not a fresh deployment) | installer `e471a1b8` | Partial: fix inspected and one NCPA check OK; acceptance not complete (#45 open) | [REPORT.md](2026-10-08-ncpa-repeat-run/REPORT.md) |
| [2026-10-08 ncpa-run](2026-10-08-ncpa-run/REPORT.md) | VM lab, NCPA deployment and monitoring | app `1540545` | Partial: deployment passes, NCPA checks CRITICAL (#45) | [REPORT.md](2026-10-08-ncpa-run/REPORT.md) |
| [2026-10-08 vm-lab-first-run](2026-10-08-vm-lab-first-run/REPORT.md) | VM lab, installer-built appliance | app `1540545` | Pass (tooling); defect #43 found | [REPORT.md](2026-10-08-vm-lab-first-run/REPORT.md) |

Add a row when you commit a report. Earlier runs mentioned in
[`../plans/`](../plans/) (for example the 2026-10-03 and 2026-10-06 live runs)
were reported outside the repository and are not reproduced here.
