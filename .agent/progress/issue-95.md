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
- [ ] Operator documentation covers development invocation and session behavior.
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
| Development invocation and session documentation | Operator documentation | README and architecture/spec documentation review; docs verification |
| Specifications and current status | Documentation | Backend/data specs and Implementation_Status updates; docs verification |
| No migration and no immediate session invalidation | Out of scope | No model/migration change; command tests and documentation state timeout behavior |

## Plan

1. [x] Add failing CLI recovery tests in `server/tests/unit/test_bootstrap_admin_recovery.py` for successful pre/post-setup recovery, password validation/confirmation, target ambiguity/missing cases, preserved account state, and sanitized audit logging.
2. [x] Implement the `recover-bootstrap-admin` Flask command and safe bootstrap-identity helper in `server/app/api/commands/seed.py`, then register it in `server/app/__init__.py`.
3. [x] Document development and installed-appliance recovery invocation plus session behavior in `README.md`, `spec files/Backend_Modules_and_Routes.md`, `spec files/Data_Model_and_Integrations.md`, and `spec files/Implementation_Status.md`.
4. [ ] Run focused tests, backend verification, docs verification, and full verification; re-read issue #95, then remove this progress file and open a pull request if every finish condition is proven.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Added private CLI recovery, safe earliest-created bootstrap lookup, tests, and documentation. | `server/.venv/bin/python -m pytest server/tests/unit/test_bootstrap_admin_recovery.py -q`; `scripts/verify.sh docs`; `scripts/verify.sh backend` | Focused tests: 8 passed. Docs: green. Initial restricted backend run failed only local socket/DNS tests; approved rerun: 2,330 passed / 14 skipped, green. |
| 2 | Ran final CI-equivalent verification and inspected the installer contract. | `scripts/verify.sh all`; installer tree API inspection | `all` green: docs, 2,330 backend passed / 14 skipped, 492 frontend passed, build and lint (25 existing warnings/no errors). Installer wrapper work was filed as PinPoint-Installer#6. |
| 3 | Updated #95 acceptance criteria to make appliance-wrapper work an installer follow-up, then aligned local docs. | GitHub REST PATCH; pending final verification | The issue's complete backend finish condition is now actionable in this repository; the wrapper remains separately tracked in PinPoint-Installer#6. |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `scripts/verify.sh all` (approved unrestricted execution)
- Result (first failing lines, or "green"): green — docs, 2,330 backend passed / 14 skipped, 492 frontend passed, build and lint completed with 25 existing warnings and no errors.
- Hypothesis: The application-side change satisfies every current issue #95 finish-condition item; only final verification and PR preparation remain.
- Next action (one specific step, not "continue"): Run `scripts/verify.sh docs` and `scripts/verify.sh all`, then remove this progress file and open the PR.

## Decisions and notes

- Issue #95 has no comments and its stated requirements are all represented in the finish condition above.
- The installer wrapper lives in the separate installer repository and is a follow-up, not a backend completion requirement.
- No migration is planned: the command changes only an existing password hash and `Must_Change_Password`; sessions continue to use the configured timeout, as explicitly scoped by the issue.
- Final issue re-read found no comments or changed requirements. The installer repository's recursive tree on `main` has no `pinpoint` wrapper. The user updated #95 so that appliance-wrapper work is an explicit follow-up, owned by [lorraine-pangilinan/PinPoint-Installer#6](https://github.com/lorraine-pangilinan/PinPoint-Installer/issues/6), rather than a backend completion blocker.
