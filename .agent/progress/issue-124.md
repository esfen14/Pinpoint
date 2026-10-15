# Issue #124: System Refinement Set Journald Limit, Report Storage Usage and Add Nagios Log Tab

Branch: `issue-124-storage-and-nagios-log`
Status: in-progress

## Finish condition

Copied from issue sections E, F and H; approvals and live evidence remain unticked until observed.

- [ ] **Part 11.1 (Installer):** A fresh install has the drop-in with the documented limits and `journalctl --disk-usage` stays within them.
- [ ] **Part 11.1 (Installer):** An upgrade does not overwrite an administrator's own journald settings.
- [ ] **Part 11.1 (Installer):** Installer logs are rotated or the exemption is documented.
- [ ] **Part 11.2 (System):** The status data lists database, backup and archive sizes and free disk space, and handles missing paths without error.
- [ ] **Part 11.2 (System):** The Nagios log route returns at most the configured lines and bytes, newest last, and returns an empty list if the file is unreadable.
- [ ] **Part 11.2 (System):** The route cannot be used to read any other file.
- [ ] **Part 11.2 (System):** Both require login and the stated permission (403 otherwise).
- [ ] **Part 11.3 (Web-Interface):** The Dashboard shows storage sizes and free disk and a warning when space is low.
- [ ] **Part 11.3 (Web-Interface):** The Nagios log tab shows the latest lines, refreshes, and shows a clear state when the log is unavailable.
- [ ] **Part 11.3 (Web-Interface):** Users without `system.logs` or `system.dashboard` do not see the matching element.
- [ ] **Part 11.3 (Web-Interface):** Existing dashboard and logs tests pass unchanged.
- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components, types and routes (paths in section C).
- [ ] Unit tests for new or modified logic.
- [ ] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, `spec files/Display_Requirements.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes; Help text.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.
- [ ] All mandatory acceptance criteria are satisfied.
- [ ] Required functionality works as specified.
- [ ] Existing behavior has not been unintentionally broken.
- [ ] Applicable edge cases are handled.
- [ ] Code follows PinPoint's existing architectural patterns and conventions.
- [ ] No unnecessary duplicate functionality is introduced.
- [ ] Relevant linting and static analysis checks pass.
- [ ] No unresolved critical defects remain.
- [ ] Required automated tests are added or updated.
- [ ] All applicable automated tests pass.
- [ ] Relevant integration and regression tests pass.
- [ ] Test results or verification evidence are attached to the pull request.
- [ ] User inputs and configuration values are validated.
- [ ] Authorization is enforced where required.
- [ ] Sensitive data is handled securely.
- [ ] Errors are handled without introducing uncontrolled failures.
- [ ] Relevant performance and reliability requirements are satisfied.
- [ ] Relevant technical documentation is updated.
- [ ] User documentation is updated for user-facing changes.
- [ ] New configuration parameters are documented.
- [ ] Deployment or migration steps are documented where applicable.
- [ ] The pull request references the corresponding issue number.
- [ ] The pull request describes the implementation and testing performed.
- [ ] Required CI checks pass.
- [ ] All required reviewer approvals are obtained.
- [ ] Blocking review comments are resolved.
- [ ] All applicable acceptance criteria and required deliverables are complete.

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

1. [ ] Backend tests first: add server/tests/unit/test_storage_usage.py and test_nagios_log.py; implement server/app/storage_usage.py and nagios_log.py; extend api/system/dashboard.py and log.py, config.py/README settings and backend route catalog. Run focused and backend checks.
2. [ ] Frontend tests first: storage card and log panel under client/src/test/; implement components/dashboard/StorageUsageCard.tsx and components/system-logs/NagiosLogPanel.tsx; wire pages/DashboardPage.tsx, SystemLogsPage.tsx and types/dashboard.ts, log.ts. Preserve existing page tests and permissions; run frontend verification.
3. [ ] Separate installer issue branch: tests for setup/configure-log-retention.sh, wire setup/deploy-pinpoint-web.sh and document limits/admin preservation in README.md. Run isolated tests and security review of fixed paths, arguments and secret exposure.
4. [ ] Finish owning specs, Help and server/tests/README.md; run actual fresh/upgrade lab cases only after proving exclusive lab ownership; record sanitized docs/test-runs report with exact tested commits and observed/untested cases. Re-read issue and run scripts/verify.sh all; checkpoint evidence.
5. [ ] Create paired PRs from repository templates, attach output/evidence and check CI. Keep application PR draft with this progress file if any mandatory criterion remains unproven; otherwise remove progress file and mark ready. Never merge.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added storage/tail helpers and fixed-path APIs plus tests; initial red confirmed missing modules | focused storage/log/dashboard pytest | 70 passed, 1 failed: authorization test requested anonymous and logged-in fixtures sharing a client; split test required |
| Plan | Read issue and shared workflow; isolated checkout from origin/main cc1305c6; inspected external installer deploy script | gh issue view 124; installer tree/deploy inspection | Installer located; no code changed |

## State for the next session

- Last check run (exact command): scripts/verify.sh backend > /tmp/issue124-backend-stage.log 2>&1
- Result (first failing lines, or "green"): focused 70 passed, 1 failed: anonymous assertion saw limited-client session (403); backend stage launched, result pending
- Hypothesis: Backend and UI are independent of installer privileges; all three parts need evidence before ready-for-review.
- Next action (one specific step, not "continue"): Split anonymous/limited-client authorization tests, then rerun focused and backend checks.

## Decisions and notes

- User said continue after being given concrete privileged-change proposal; proceed with that boundary. Installer work stays in lorraine-pangilinan/PinPoint-Installer, separate issue-124 branch and PR.
- Proposed installer limits: SystemMaxUse=100M, MaxRetentionSec=7day; these apply to the host journal, not just Gunicorn. Preserve any administrator journald setting and edited managed file; skip managed defaults when competing admin limits exist. Document exceptions rather than silently overriding.
- Installer file logs: weekly rotation, four compressed archives, missingok/notifempty/copytruncate because installer scripts use tee/open descriptors.
- Tail request accepts only lines (1..500) and after (nonnegative Unix seconds); fixed trusted config path; cap input/output bytes at 64 KiB and disclose unavailable state. Default/old dashboard fields retain their values.
- Storage traversal must be bounded and report incomplete scans explicitly, skip symlinks and avoid repeated per-host work. Per-location filesystem measurements handle split mounts.
- No lab ownership established yet; never reset shared VMs or discard other agents' edits.
