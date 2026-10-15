# Issue #124: System Refinement Set Journald Limit, Report Storage Usage and Add Nagios Log Tab

Branch: `issue-124-storage-and-nagios-log`
Status: in-progress

## Finish condition

Copied from issue sections E, F and H; approvals and live evidence remain unticked until observed.

- [x] **Part 11.1 (Installer):** A fresh install has the drop-in with the documented limits and `journalctl --disk-usage` stays within them.
- [x] **Part 11.1 (Installer):** An upgrade does not overwrite an administrator's own journald settings.
- [x] **Part 11.1 (Installer):** Installer logs are rotated or the exemption is documented.
- [x] **Part 11.2 (System):** The status data lists database, backup and archive sizes and free disk space, and handles missing paths without error.
- [x] **Part 11.2 (System):** The Nagios log route returns at most the configured lines and bytes, newest last, and returns an empty list if the file is unreadable.
- [x] **Part 11.2 (System):** The route cannot be used to read any other file.
- [x] **Part 11.2 (System):** Both require login and the stated permission (403 otherwise).
- [x] **Part 11.3 (Web-Interface):** The Dashboard shows storage sizes and free disk and a warning when space is low.
- [x] **Part 11.3 (Web-Interface):** The Nagios log tab shows the latest lines, refreshes, and shows a clear state when the log is unavailable.
- [x] **Part 11.3 (Web-Interface):** Users without `system.logs` or `system.dashboard` do not see the matching element.
- [x] **Part 11.3 (Web-Interface):** Existing dashboard and logs tests pass unchanged.
- [x] Updated application source code (paths in section C).
- [x] New or updated API endpoints, with route docstrings and permission checks.
- [x] Database migrations: N/A.
- [x] Updated frontend components, types and routes (paths in section C).
- [x] Unit tests for new or modified logic.
- [x] Frontend interaction tests under `client/src/test/`.
- [x] Integration or regression tests for the workflows in section G.
- [x] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Display_Requirements.md`, and `spec files/Implementation_Status.md`.
- [x] Updated user-facing documentation: Installer release notes; Help text.
- [x] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.
- [x] All mandatory acceptance criteria are satisfied.
- [x] Required functionality works as specified.
- [x] Existing behavior has not been unintentionally broken.
- [x] Applicable edge cases are handled.
- [x] Code follows PinPoint's existing architectural patterns and conventions.
- [x] No unnecessary duplicate functionality is introduced.
- [x] Relevant linting and static analysis checks pass.
- [x] No unresolved critical defects remain.
- [x] Required automated tests are added or updated.
- [x] All applicable automated tests pass.
- [x] Relevant integration and regression tests pass.
- [x] Test results or verification evidence are attached to the pull request.
- [x] User inputs and configuration values are validated.
- [x] Authorization is enforced where required.
- [x] Sensitive data is handled securely.
- [x] Errors are handled without introducing uncontrolled failures.
- [x] Relevant performance and reliability requirements are satisfied.
- [x] Relevant technical documentation is updated.
- [x] User documentation is updated for user-facing changes.
- [x] New configuration parameters are documented.
- [x] Deployment or migration steps are documented where applicable.
- [x] The pull request references the corresponding issue number.
- [x] The pull request describes the implementation and testing performed.
- [ ] Required CI checks pass.
- [ ] All required reviewer approvals are obtained.
- [x] Blocking review comments are resolved.
- [x] All applicable acceptance criteria and required deliverables are complete.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| A/B/C: explicit journald limits, installer rotation, idempotent upgrade preserving admin settings | E installer; F source/docs; H deployment/security | Separate installer tests plus fresh-install/upgrade VM report |
| C: database/backup/archive sizes and filesystem free space, missing paths | E status; F API/unit tests | test_storage_usage.py and test_dashboard.py |
| C/G: bounded end-read, newest-last, missing/unreadable file, fixed path, lines/after validation and redaction | E log route; H security/reliability | test_nagios_log.py API and helper tests |
| C: login and existing permissions; no new permission or migration | E permissions; F migrations N/A | authenticated/anonymous/limited API checks; client access tests |
| C/G: dashboard compact storage card, low-space warning with threshold text, loading/empty/error/403 | E dashboard; F frontend tests; H edge cases | StorageUsageCard.test.tsx, DashboardPage.test.tsx |
| C/G: latest log tab, refresh, latest-lines/host-address notice, states and permission hiding | E log UI; F frontend tests | NagiosLogPanel.test.tsx and SystemLogsPage.test.tsx |
| C: reuse export menu if appropriate | E/F UI | Existing audit export kept; bounded raw log has no export to reduce accidental sharing |
| D: reuse modules, docstrings/envelopes/validation/TypeScript, safe defaults, bounded work | F source/API; H quality/security/reliability | source review and scripts/verify.sh all, existing regression tests unchanged |
| D: config generation and model/permission guidance conditional on such changes | F migration N/A; H architecture | No config generation/model/permission changes planned |
| Out of scope: replacing Nagios rotation | E installer/archive reporting | Archive size read only; no Nagios rotation changes |
| F: all five owning specs and implementation inventory, installer release notes and Help | F docs; H docs | scripts/verify.sh docs; inline UI help and installer README |
| F/G: real verification output and sanitized lab evidence | F evidence; H tests | test-results logs, PR attachments, docs/test-runs report |
| H: issue-linked PR, accurate checks, green CI, reviewer approvals/resolved blockers | H PR review | gh pr checks/view; human approvals must be observed |

## Plan

1. [x] Backend tests first: add server/tests/unit/test_storage_usage.py and test_nagios_log.py; implement server/app/storage_usage.py and nagios_log.py; extend api/system/dashboard.py and log.py, config.py/README settings and backend route catalog. Run focused and backend checks.
2. [x] Frontend tests first: storage card and log panel under client/src/test/; implement components/dashboard/StorageUsageCard.tsx and components/system-logs/NagiosLogPanel.tsx; wire pages/DashboardPage.tsx, SystemLogsPage.tsx and types/dashboard.ts, log.ts. Preserve existing page tests and permissions; run frontend verification.
3. [x] Separate installer issue branch: tests for setup/configure-log-retention.sh, wire setup/deploy-pinpoint-web.sh and document limits/admin preservation in README.md. Run isolated tests and security review of fixed paths, arguments and secret exposure.
4. [x] Finish owning specs, Help and server/tests/README.md; run actual fresh/upgrade lab cases only after proving exclusive lab ownership; record sanitized docs/test-runs report with exact tested commits and observed/untested cases. Re-read issue and run scripts/verify.sh all; checkpoint evidence.
5. [ ] Paired draft PRs created and evidence attached; remaining: final publication CI and required human reviews. Keep application PR draft with this progress file if any mandatory criterion remains unproven; otherwise remove progress file and mark ready. Never merge.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Plan | Read issue and shared workflow; isolated checkout from origin/main cc1305c6; inspected external installer deploy script | gh issue view 124; installer tree/deploy inspection | Installer located; no code changed |
| 1 | Added storage/tail helpers and fixed-path APIs plus tests; initial red confirmed missing modules | focused storage/log/dashboard pytest | 70 passed, 1 failed: authorization test requested anonymous and logged-in fixtures sharing a client; split test required |
| 2 | Split shared-client auth test; implemented storage/log UI and permission guards; preserved existing dashboard tests | focused backend: 72 pass; focused frontend: 27 pass; scripts/verify.sh frontend | 695 frontend tests pass, build/lint green (32 warnings). Backend stage still running; initial collected auth test is expected to fail once |
| 3 | Implemented separate fixed-path installer helper, admin override preservation and logrotate; upstream push denied, existing fork used | python3 -m unittest discover -s tests -p test_log_retention.py; bash -n | 4 installer tests pass, syntax green; installer commit ffb4cc3 |
| 4 | Updated all five owning specs, user help and test inventory; isolated VM fresh install, journal volume, logrotate/admin-policy and live permission/API checks; added status-source independence regression and fix | scripts/verify.sh all; docs final; focused frontend 28 tests; actual VM checks | Backend 3315 passed / 14 skipped; docs green; full frontend 695 passed / 1 unrelated BandwidthCard callback timing failure. Fresh install health 60/0, journald 92.5 MiB after 192 MB input, logrotate/admin policy and live API checks pass. Browser/full upgrade pending |
| 5 | Retested unchanged BandwidthCard 19/19; full all gate green; upgraded isolated appliance, 4/4 no-network Playwright journeys, final docs/report; created paired draft PRs and separate installer healthcheck issue #9; powered off exclusive clone | scripts/verify.sh all; scripts/verify.sh docs; real VM/Playwright checks | 3315 backend passed / 14 skipped; 696 frontend passed; build/lint green (31 warnings); docs green. Final publication CI and human reviews remain to observe |

## State for the next session

- Last check run (exact command): git merge-tree --write-tree --name-only HEAD origin/main
- Result (first failing lines, or "green"): exit 1; sole conflict is docs/test-runs/README.md. GitHub reports mergeable=false / mergeable_state=dirty. origin/main advanced from cc1305c6 to edb503620c272f432ed4196ee53e563f320fda26 during this task. No merge was applied to the worktree. Local full gate on issue source 5f0a7ef8 is green (3315 backend passed / 14 skipped, 696 frontend passed, build/lint green with 31 warnings); report docs gate is green. Final publication head has no CI because the PR conflicts; earlier source CI docs/frontend passed, backend was still running when inspected.
- Hypothesis: Both branches added test-run index entries at the same location. Preserve both additions when merging latest origin/main, then reverify the resulting tree. This is an agent-resolvable documentation conflict, not a person-required blocker.
- Next action (one specific step, not "continue"): Merge latest origin/main into issue-124-storage-and-nagios-log in this isolated checkout, resolve only docs/test-runs/README.md by preserving both run rows, run scripts/verify.sh all on the merged tree, checkpoint and verify final-head CI on PR #178; then obtain paired human reviews for #178 and installer #8. Five implementation rounds have been used this session.


## Decisions and notes

- User said continue after being given concrete privileged-change proposal; proceed with that boundary. Installer work stays in lorraine-pangilinan/PinPoint-Installer, separate issue-124 branch and PR.
- Proposed installer limits: SystemMaxUse=100M, MaxRetentionSec=7day; these apply to the host journal, not just Gunicorn. Preserve any administrator journald setting and edited managed file; skip managed defaults when competing admin limits exist. Document exceptions rather than silently overriding.
- Installer file logs: weekly rotation, four compressed archives, missingok/notifempty/copytruncate because installer scripts use tee/open descriptors.
- Tail request accepts only lines (1..500) and after (nonnegative Unix seconds); fixed trusted config path; cap input/output bytes at 64 KiB and disclose unavailable state. Default/old dashboard fields retain their values.
- Storage traversal must be bounded and report incomplete scans explicitly, skip symlinks and avoid repeated per-host work. Per-location filesystem measurements handle split mounts.
- No lab ownership established yet; never reset shared VMs or discard other agents' edits.

- To avoid shared-lab ownership ambiguity, created a linked clone of the base snapshot named pinpoint-issue124-appliance; its separate internal network and loopback ports will isolate acceptance without changing shared appliance/targets. Base snapshot remains untouched.

- Installer draft PR: https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/8 (existing esfen14 fork; upstream push denied). VM private config /tmp/issue124-vmlab.env, guarded SSH wrapper /tmp/issue124-ssh, private test credentials /tmp/issue124-private. App fresh commit f80d6c1; installer ffb4cc3.

- Paired draft PRs: https://github.com/esfen14/Pinpoint/pull/178 and https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/8. Report: docs/test-runs/2026-10-15-issue-124-storage-logs/REPORT.md. All E/F items and applicable H quality/documentation/security items have observed proof in that report, tests and PR; final CI/human approval boxes remain unticked at checkpoint.
- Full gate failure history is retained, not hidden: the initial run had an unchanged BandwidthCard callback timing failure; its exact 19-test retest and the final 696-test frontend suite pass without changing that file.
- The exclusive VM was powered off after acceptance; shared QA appliance/targets were not modified. No ISO packaging/boot or seven elapsed days of retention is claimed. Installer #9 captures the pre-existing 664-versus-640 healthcheck mismatch (main already uses 640).

- Final publication audit: GitHub did not schedule final-head checks because main advanced and the PR became conflicting. Closing/reopening preserved draft state but did not remove that conflict. Read-only merge-tree confirmed the sole conflict is the test-run index; all five owning specs auto-merge. No main merge, conflict edits or extra implementation round was performed after the workflow limit. The worktree remains clean apart from this checkpoint until it is saved.
