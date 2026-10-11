# Issue #95: Add backend recovery for the bootstrap administrator account

Branch: `issue-95-bootstrap-admin-recovery`
Status: in-progress

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] An authorized CLI operator can recover the bootstrap account without another administrator, SMTP, or browser recovery.
- [ ] Recovery works before and after first-run setup.
- [ ] The command prompts privately for a confirmed, policy-compliant temporary password; passwords never appear in arguments, logs, output, or audit records.
- [ ] It sets `Must_Change_Password` and preserves an outstanding `Needs_Setup` requirement.
- [ ] It does not reactivate inactive or suspended accounts or modify permissions or related account data.
- [ ] Unknown or ambiguous bootstrap identity fails without modifying any account.
- [ ] Tests cover success, validation, setup-state preservation, rejected targets, and audit logging.
- [ ] Operator documentation covers development invocation and the installed-appliance wrapper.
- [ ] Relevant specifications and `Implementation_Status.md` are updated.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| CLI recovery without another administrator, SMTP, or browser | CLI operator recovery | `test_bootstrap_admin_recovery.py::TestRecoverBootstrapAdmin::test_recovers_sole_earliest_account` |
| Works before and after first-run setup | Recovery works before and after setup | Before/after setup CLI tests |
| Private confirmed, policy-compliant password; no secret output/log/audit | Private password handling | Prompt, validation, output and audit tests; source review |
| Force password change while retaining setup gate | Flag preservation | Setup-state tests |
| Preserve status, role, permissions and related data | No unrelated account changes | Inactive/suspended preservation tests |
| Unknown or ambiguous identity does not modify data | Rejected targets | Missing/tied bootstrap tests |
| Regression coverage | Tests | Focused test module and backend verification |
| Development and appliance invocation docs | Operator documentation | README and architecture/spec documentation review; docs verification |
| Specifications and current status | Documentation | Backend/data specs and Implementation_Status updates; docs verification |
| No migration and no immediate session invalidation | Out of scope | No model/migration change; command tests and documentation state timeout behavior |

## Plan

1. [ ] Add failing CLI recovery tests in `server/tests/unit/test_bootstrap_admin_recovery.py` for successful pre/post-setup recovery, password validation/confirmation, target ambiguity/missing cases, preserved account state, and sanitized audit logging.
2. [ ] Implement the `recover-bootstrap-admin` Flask command and safe bootstrap-identity helper in `server/app/api/commands/seed.py`, then register it in `server/app/__init__.py`.
3. [ ] Document development and installed-appliance recovery invocation plus session behavior in `README.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
4. [ ] Run focused tests, backend verification, docs verification, and full verification; re-read issue #95, then remove this progress file and open a pull request if every finish condition is proven.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `gh api repos/{owner}/{repo}/issues/95`
- Result (first failing lines, or "green"): Retrieved the issue through REST; `gh issue view 95` is blocked by the GitHub CLI's deprecated Projects-classic GraphQL field.
- Hypothesis: The production initializer creates exactly one initial user. The recovery command can identify it as the sole earliest-created user, fail safely on no user or equal earliest timestamps, and never rely on email, user ID, or `Needs_Setup`.
- Next action (one specific step, not "continue"): Add the focused failing CLI recovery tests.

## Decisions and notes

- Issue #95 has no comments and its stated requirements are all represented in the finish condition above.
- The installer wrapper lives in the separate installer repository. This repository will document its required installed-appliance invocation (`sudo pinpoint recover-bootstrap-admin`) without changing installer code.
- No migration is planned: the command changes only an existing password hash and `Must_Change_Password`; sessions continue to use the configured timeout, as explicitly scoped by the issue.
