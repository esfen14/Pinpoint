# Issue #115: STARTTLS custom SMTP relays and notification failures

Branch: `issue-115-smtp-relays`
Status: in-progress

## Finish condition

User scope decision (2026-10-15): STARTTLS only. Implicit TLS and installer changes are deferred. Migration and permission deliverables apply only if schema or permissions change; existing columns and settings.email suffice.

#### E. Acceptance Criteria

- [ ] **Part 2.1 (Installer):** The helper accepts `tls: "tls"` (implicit) and writes a valid msmtp account for it, and still accepts `starttls`.
- [ ] **Part 2.1 (Installer):** Any other `tls` value, including a plain-text mode, is rejected with exit code 1 and no password in the message.
- [ ] **Part 2.1 (Installer):** An existing appliance configured for STARTTLS keeps working after upgrade without re-entering the password.
- [ ] **Part 2.1 (Installer):** File ownership and mode of `/etc/msmtprc` remain `root:nagios` and 0640.
- [ ] **Part 2.2 (System):** A custom host, port and `starttls` can be saved, written through the helper and used for a test email.
- [x] **Part 2.2 (System):** An invalid host, port or TLS mode returns 400 with a message naming the field, and never reaches the helper.
- [x] **Part 2.2 (System):** The Gmail settings and test email behave exactly as before.
- [ ] **Part 2.2 (System):** After a notification fails because mail is not configured, the API reports a last-failure time and reason within one poll cycle. With no failures the field is empty.
- [x] **Part 2.2 (System):** A missing or unreadable `nagios.log` yields an empty indicator, not an error.
- [x] **Part 2.2 (System):** No password appears in any response or log.
- [x] **Part 2.3 (Web-Interface):** Choosing Gmail shows exactly the current form and saves the same request body as today.
- [x] **Part 2.3 (Web-Interface):** Choosing a relay shows host, port and TLS fields, validates them, and saves.
- [x] **Part 2.3 (Web-Interface):** When the API reports a mail failure the tab shows its time and reason, and shows nothing when there is none.
- [x] **Part 2.3 (Web-Interface):** No password is ever displayed or kept in browser storage.
- [x] **Part 2.3 (Web-Interface):** The existing EmailSettings tests pass unchanged.

#### F. Required Deliverables

- [x] Updated application source code (paths in section C).
- [x] New or updated API endpoints, with route docstrings and permission checks.
- [ ] Database migration (multi-database, with downgrade) and `flask sync-permissions` note if a permission is added.
- [x] Updated frontend components, types and routes (paths in section C).
- [x] Unit tests for new or modified logic.
- [x] Frontend interaction tests under `client/src/test/`.
- [ ] Integration or regression tests for the workflows in section G.
- [x] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Frontend_Modules_and_Routes.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes; Email settings help text and the user guide section on mail; Help text on the tab.
- [ ] Evidence that the functionality works: `scripts/verify.sh all` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- **Part 2.1 (Installer):** Installer-side script tests for each valid and invalid `tls` value and for the exact-field check.
- **Part 2.1 (Installer):** VM-lab run (`scripts/vmlab`, recorded under `docs/test-runs/`): save an implicit-TLS configuration and send the PinPoint test email through a local TLS sink.
- **Part 2.1 (Installer):** Upgrade test: install the previous helper, configure STARTTLS, upgrade, send a test email.
- **Part 2.2 (System):** Unit: custom preset validation (valid, bad host, bad port, bad TLS, unsupported `tls`), unchanged Gmail cases.
- **Part 2.2 (System):** Unit: the log reader with sample `wproc` failure text, a truncated file, a missing file and a large file (byte cap).
- **Part 2.2 (System):** API: `settings.email` permission, 400 and success paths with the helper mocked.
- **Part 2.2 (System):** Lab (record in `docs/test-runs/`): configure a custom relay against a local sink, then clear it and confirm the failure indicator after a forced notification.
- **Part 2.3 (Web-Interface):** Frontend: provider switch, validation, save, failure notice shown and hidden, password never rendered. Extend `EmailSettings.test.tsx`.
- **Part 2.3 (Web-Interface):** Regression: `PageAccess.test.tsx`.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

**A pull request addressing this issue must not be merged until all applicable conditions below are fulfilled.**

#### Functional Completion

- [ ] All mandatory acceptance criteria are satisfied.
- [ ] Required functionality works as specified.
- [ ] Existing behavior has not been unintentionally broken.
- [ ] Applicable edge cases are handled.

#### Code Quality

- [x] Code follows PinPoint's existing architectural patterns and conventions.
- [x] No unnecessary duplicate functionality is introduced.
- [x] Relevant linting and static analysis checks pass.
- [ ] No unresolved critical defects remain.

#### Testing

- [x] Required automated tests are added or updated.
- [ ] All applicable automated tests pass.
- [ ] Relevant integration and regression tests pass.
- [ ] Test results or verification evidence are attached to the pull request.

#### Security and Reliability

- [x] User inputs and configuration values are validated.
- [x] Authorization is enforced where required.
- [x] Sensitive data is handled securely.
- [x] Errors are handled without introducing uncontrolled failures.
- [x] Relevant performance and reliability requirements are satisfied.

#### Documentation

- [x] Relevant technical documentation is updated.
- [x] User documentation is updated for user-facing changes.
- [x] New configuration parameters are documented.
- [x] Deployment or migration steps are documented where applicable.

#### Pull Request Review

- [x] The pull request references the corresponding issue number.
- [x] The pull request describes the implementation and testing performed.
- [ ] Required CI checks pass.
- [ ] All required reviewer approvals are obtained.
- [ ] Blocking review comments are resolved.
- [ ] All applicable acceptance criteria and required deliverables are complete.

Do not mark this issue as completed solely because code has been written. Test results, reviewer approvals and deployment verification must be backed by evidence attached to the pull request and must not be claimed without it.


Requirement coverage (every requirement in A–H):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| A/C custom relay, helper-compatible validation, Gmail unchanged | E Part 2.2 relay/validation/Gmail | Existing test_smtp_settings.py unchanged plus test_smtp_relays.py |
| B/C password encryption and preservation, no leaks | E password rules | API/helper/SMTP error and audit tests |
| C bounded missing/unreadable/rotated log reader, time/reason | E failure API and empty indicator | test_mail_failures.py plus real Nagios log trial if available |
| C provider form, validation, same Gmail payload, notice/test link/polling | E Part 2.3 | EmailSettings.test.tsx unchanged plus EmailSettingsRelay.test.tsx, smtpSettingsApi.test.ts |
| D default behavior, envelopes, permissions, reliability and input review | E defaults/security and H quality/security | Focused tests and verify.sh all; explicit review in progress |
| F code, endpoint contracts, tests, technical and user docs | F applicable deliverables | Source/spec diffs, docs/manuals/Email_Settings.md, suite outputs |
| F migration/sync-permissions conditional | F migration/permissions | Model and permission inspection: no new schema or permission required |
| G STARTTLS local sink and failed-notification lab evidence | F evidence and H testing | docs/test-runs report; blocked if no accessible lab |
| A/C/E/G implicit TLS, installer upgrade/modes/release notes | Deferred by user decision | No installer change; STARTTLS contract unchanged |
| H PR, CI and reviewer approvals | H review | Draft PR, gh pr checks; human approvals cannot be self-certified |
| A out of scope plaintext SMTP, Microsoft 365/OAuth | Deliberately excluded | Validation tests reject tls/none/plain modes |

## Plan

1. [x] Backend: add failing relay/error tests in server/tests/unit/test_smtp_relays.py; implement STARTTLS custom validation and provider-aware safe errors in server/app/smtp_settings.py; retain helper JSON fields; verify backend.
2. [x] Failure reporting: test bounded parser/API in server/tests/unit/test_mail_failures.py; implement server/app/nagios/mail_failures.py, config/README path and GET contract; verify backend.
3. [x] Frontend: add relay/API/polling tests; update EmailSettings.tsx, types/smtpSettings.ts and lib/smtpSettingsApi.ts; preserve existing Gmail tests; verify frontend.
4. [x] Documentation and evidence: update owning specs, tests README and user guide; attempt authorized scoped real SMTP/Nagios verification when infrastructure permits; record actual lab limitations; verify docs and all.
5. [x] Re-read issue and user decision, audit requirements, push draft or ready PR as evidence permits, inspect CI.

6. [ ] Resume live acceptance: create owned standalone Docker appliance from existing cached image; install unchanged SMTP helper/dependencies; run actual STARTTLS sink, save/reload/test, real forced Nagios notification failure, service-user log reads, and Playwright Email tab checks. Record fresh docs/test-runs report; no changes to shared lab.
7. [ ] Re-audit acceptance, update Implementation_Status.md and PR evidence; verify docs/all, remove progress and mark ready only when all applicable acceptance has observed proof.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| intake | Scope resolved by user: STARTTLS only | scripts/vmlab preflight; docker ps --format '{{.Names}}' | VBoxManage absent; Docker socket access denied; no live mutations performed |
| 1 | Implemented STARTTLS custom validation/API/helper and UI; added bounded failure reader and tests. Confirmed red before code: relay 31 failures; missing reader collection error; frontend 8 failures. | Focused backend: 89 passed; frontend: 38 passed; verify.sh frontend and docs green; verify.sh backend still running | Core source implemented; live checks blocked by infrastructure. Broad backend and final documentation pending. |
| 2 | Documented STARTTLS-only scope, API/failure semantics and user workflow; matched custom password limit to helper (256) while retaining Gmail 200 limit; added boundary/rotation cases. | verify.sh backend: 2889 passed/14 skipped; verify.sh frontend green; verify.sh docs green; focused frontend 38 passed | Full initial stages green; final combined all verification pending after final source refinements. |

| 3 | Fixed experimentally confirmed descriptor leak on a directory configured as log path; new regression failed with +5 open descriptors before fix and passed after. Replaced fdopen with explicit descriptor ownership/finally-close. | Focused backend including email alerts: 119 passed; prior combined run deliberately interrupted at pytest after review found the leak | Re-run combined checks on corrected source; no live product acceptance claimed. Draft PR #172 opened; GitHub reports no checks so far. |

| 4 | Merged main e0a61570, resolving the report-index conflict without dropping either entry; final source verified at 58e672b4; code/spec/guide/report complete for available scope. | scripts/verify.sh all: 3056 backend passed, 14 skipped; 653 frontend passed; build/docs green; lint 0 errors/29 warnings | Local gate green. Draft #172 remains blocked solely on real-appliance acceptance and human review; CI backend is still pending at checkpoint. |

| 5 | Regression-tested and corrected overbroad credential redaction: only raw SMTP details are redacted; fixed API codes/messages remain stable even when a short password matches them. Two new cases failed before fix, then passed. | scripts/verify.sh all: 3058 backend passed/14 skipped, 653 frontend passed, build/docs green, lint 0 errors/29 warnings; focused backend 121 passed | Local gate green for final source in this checkpoint. Published pre-correction draft CI was green. Final push triggers CI again; live appliance acceptance still blocked. |

| resumed | User explicitly authorized Docker access. Unix account is already listed in docker group; current process lacks refreshed supplementary group. `sg docker` succeeds. Existing shared lab remains untouched. | sg docker -c "docker ps --format '{{.Names}}'"; resumed verify.sh all running | Infrastructure blocker cleared for isolated Docker acceptance. |

## State for the next session

- Last check run (exact command): `scripts/verify.sh all > test-results/issue-115-all-final-correction.log 2>&1`
- Result (first failing lines, or "green"): green; 3058 backend passed / 14 skipped, 653 frontend passed, build/docs green, lint 0 errors / 29 warnings. This ran on a8a112a5 plus the error-redaction correction and its tests, committed with this progress checkpoint. Prior draft CI run 38705934980 passed all three jobs; final source push triggers a new run.
- Hypothesis: Isolated implementation is complete and the log/error privacy guards are verified. Actual installed-helper/SMTP/Nagios behavior and service-user log access cannot be certified in this environment.
- Next action (one specific step): Inspect the latest CI checks on draft PR #172, then use an accessible exclusively owned appliance to run the four skipped cases in docs/test-runs/2026-10-15-issue-115-starttls-preflight/REPORT.md and create a fresh report before review readiness.

## Decisions and notes

- User explicitly selected STARTTLS-only; do not modify the installer or enable implicit TLS.
- Existing SmtpSettings already stores Provider, Host, Port and Tls; no migration or new permission needed.
- Issue authorizes scoped SMTP/Nagios lab trials, but this environment has no VBoxManage and Docker is denied. Do not claim live passes or close the issue without that evidence.
- Existing Gmail tests must remain unchanged. Custom usernames follow the helper's printable ASCII/length contract; sender remains a valid email.

- Injection/secret review: helper invocation remains a fixed argument list with exactly six JSON fields on stdin; custom host/port/TLS/username/sender mirror the installed helper contract, no shell interpolation. Custom SMTP failures expose fixed text; helper diagnostics redact credentials. Log reader returns fixed reasons only and reads at most 64 KiB from a nonblocking regular file. Existing Gmail test files are unchanged.
- Format evidence: inspected upstream Nagios Core tag nagios-4.5.11 base/workers.c (NOTIFY header and contiguous indented stderr blocks), not a live appliance observation. Raw command logging is DEBUG-only; parser never requires it.
- Isolated backend environment copied from the existing dependency environment into this checkout because uv and ensurepip are absent; no dependency/version change. Frontend npm ci completed.

- Re-read #115 body/comments before draft PR: no new comments or requirement changes. User scope decision controls conditional installer work; all application requirements map to the table above. Live delivery and service-user readability lack proof, so do not mark overall acceptance or reviewer approval complete. Final scripts/verify.sh all is running on application source 899e7cd2.

- Main advanced to e0a61570 (#129) while this issue was being worked. PR initially showed CONFLICTING and no CI run. Merged origin/main locally, preserving both report-index entries; unrelated upstream NCPA changes are retained. Final combined run is restarted against the merged source. No issue-115 requirement or scope changed.

- Final coverage audit: all application requirements have source/unit/API/interaction proofs listed above, but actual helper writes and notification-generated failures remain unticked because mocks/source-format inspection are not live proof. Gmail behavior is proven by unchanged regression files, not a new inbox send. The F migration/permission deliverable is not applicable (existing columns/permission); installer release notes and implicit-TLS checks are deferred by the user's choice. The user guide and on-tab help are complete. No reviewer approvals or full live acceptance claimed.
- Infrastructure confirmation: `sudo -n docker ps` also fails with "interactive authentication is required". No privileged bypass, VM mutation, relay change or external email send was performed.
- Five rounds completed; no repeated-failure loop. No further source work is pending. Resume requires working lab access and the scoped live proof, then normal human review.

- Final correction review: only SMTP diagnostic details may contain a server echo and need credential replacement; fixed classification codes/messages must remain independent of password contents. New Gmail/custom regression cases prove this and existing Gmail tests still pass unchanged. No new behavior or scope beyond #115 was introduced.

- Resume authorization: user says "I give permission to use docker access". This answers the blocker directly and takes precedence over requiring a new issue comment. Use sg docker to refresh the already-granted group, not sudo or socket permission changes. No additional approval needed for scoped live checks already required by #115.
