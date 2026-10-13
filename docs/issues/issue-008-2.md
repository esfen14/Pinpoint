### Issue #8.2 — Installer Implementation Add Restricted Sudo Rule for Allowlisted Local Service Restarts

**Category:** Installer

**Work Type:** Implementation

**Priority:** Low

**Estimated Complexity:** Low

**Related Nagios Core Feature:** Service Recovery

**Dependencies:** None

**Plan reference:** Issue #8 in [`docs/NAGIOS_CORE_FEATURE_GAP_PLAN.md`](../NAGIOS_CORE_FEATURE_GAP_PLAN.md) §3; this is a sub-issue of Issue #8. The number is a plan identifier, not a GitHub issue number.

> **Blocked / conditional:** Wait for the security review of Issue #7.1. The installer code location is not in this repository, *further investigation required*.

#### A. Problem Description

`pinpoint` may not restart services. A recovery action needs a rule that allows exactly the permitted restarts and nothing more.

#### B. Current Implementation

Paths below were verified in the repository on 2026-10-13 unless marked *(proposed)*.

- Verified `sudoers` on a lab appliance: `pinpoint ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-apply-smtp ""` and `pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl reload nagios, /bin/systemctl reload nagios`.
- The SMTP helper pattern (fixed path, exact-field input, root-owned) is the model for a narrow privilege.

#### C. Required Changes

**Installer / Deployment**

1. Add a drop-in under `/etc/sudoers.d/` that allows `pinpoint` to run `systemctl restart` for each allowlisted unit as separate full command lines (no wildcards), validated with `visudo -c` during install.
2. Keep the list identical to the list in Issue #8.1's code and document where both must change together.
3. Add upgrade handling and make sure a failed validation leaves the previous sudoers state in place.

#### D. Implementation Guidelines


General rules for every issue:

- Reuse the existing modules named in section B instead of adding parallel ones.
- Follow `spec files/Engineering_Standards.md`: route docstrings and banners, `success()`/`error()` envelopes, guard-clause validation, `db.session.rollback()` on every failed commit, TypeScript only in `client/src`.
- Keep existing behavior unchanged by default. New settings must default to what the code does today, and an existing test must prove the default output is unchanged.
- Any change under `app/network_discovery/`, `app/ncpa_deployment/` or a command execution path needs the injection and secret-exposure review required by Engineering Standards "Sensitive modules": no untrusted input in shell commands or Nagios config, no secrets in logs or responses, and Nagios pre-apply validation preserved.
- New permissions are seeded in `server/app/api/commands/seed.py`, granted through `flask sync-permissions`, and wired to client page access where applicable. The client guard never replaces the server check.
- Model changes need a multi-database migration (`flask db migrate --multidb`) that is reviewed, not hand-edited without reason, with a working downgrade.
- Any Nagios config change goes through `regenerate_and_apply_config_status()` in `server/app/network_discovery/create_host_cfg.py`, so it is validated with the Nagios binary and rolled back if rejected.
- Every user-facing control needs loading, error, empty and success states and a plain-language label.
- Consider reliability and cost: bound loops, set timeouts on network calls, and avoid per-poll work that grows with the number of hosts.
- Update the matching file in `spec files/` and `Implementation_Status.md` in the same pull request, as `AGENTS.md` requires.

#### E. Acceptance Criteria

- [ ] `sudo -n systemctl restart <allowlisted unit>` works for `pinpoint` and any other unit is refused.
- [ ] No wildcard or shell is permitted by the rule, and `visudo -c` passes.
- [ ] Existing sudo rules are unchanged.

#### F. Required Deliverables

- [ ] Updated application source code (paths in section C).
- [ ] New or updated API endpoints: N/A.
- [ ] Database migrations: N/A.
- [ ] Updated frontend components: N/A.
- [ ] Installer tests or a scripted check in the installer repository (this repository's lab only verifies the result).
- [ ] Frontend tests: N/A.
- [ ] Integration or regression tests for the workflows in section G.
- [ ] Updated technical documentation: `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
- [ ] Updated user-facing documentation: Installer release notes.
- [ ] Evidence that the functionality works: `scripts/verify.sh backend` output attached to the pull request; plus a sanitized lab report in `docs/test-runs/` using its `TEMPLATE.md`.

#### G. Testing and Verification

- Installer script test with `visudo -c`.
- VM-lab: positive and negative `sudo -n` commands as `pinpoint`, recorded under `docs/test-runs/`.

Test results must be real runs. Do not claim a test passed without attaching its output.

#### H. Definition of Done / Merge Requirements

**A pull request addressing this issue must not be merged until all applicable conditions below are fulfilled.**

#### Functional Completion

- [ ] All mandatory acceptance criteria are satisfied.
- [ ] Required functionality works as specified.
- [ ] Existing behavior has not been unintentionally broken.
- [ ] Applicable edge cases are handled.

#### Code Quality

- [ ] Code follows PinPoint's existing architectural patterns and conventions.
- [ ] No unnecessary duplicate functionality is introduced.
- [ ] Relevant linting and static analysis checks pass.
- [ ] No unresolved critical defects remain.

#### Testing

- [ ] Required automated tests are added or updated.
- [ ] All applicable automated tests pass.
- [ ] Relevant integration and regression tests pass.
- [ ] Test results or verification evidence are attached to the pull request.

#### Security and Reliability

- [ ] User inputs and configuration values are validated.
- [ ] Authorization is enforced where required.
- [ ] Sensitive data is handled securely.
- [ ] Errors are handled without introducing uncontrolled failures.
- [ ] Relevant performance and reliability requirements are satisfied.

#### Documentation

- [ ] Relevant technical documentation is updated.
- [ ] User documentation is updated for user-facing changes.
- [ ] New configuration parameters are documented.
- [ ] Deployment or migration steps are documented where applicable.

#### Pull Request Review

- [ ] The pull request references the corresponding issue number.
- [ ] The pull request describes the implementation and testing performed.
- [ ] Required CI checks pass.
- [ ] All required reviewer approvals are obtained.
- [ ] Blocking review comments are resolved.
- [ ] All applicable acceptance criteria and required deliverables are complete.

Do not mark this issue as completed solely because code has been written. Test results, reviewer approvals and deployment verification must be backed by evidence attached to the pull request and must not be claimed without it.
