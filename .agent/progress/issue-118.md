# Issue #118: Host-based service notification dependencies

Branch: `issue-118-notification-dependencies`
Status: in-progress

## Finish condition

- [ ] Generated NCPA dependencies validate in Nagios; a lab host outage sends one host notification and no service notifications.
- [ ] NCPA metrics depend on their own host's NCPA port service when present, and have no dangling dependency when absent.
- [ ] With the dependency setting off, generated config is unchanged from the prior output.
- [ ] Dashboard and Network Health continue showing real service states.
- [ ] Source, unit and regression tests, technical and user documentation, backend output, and sanitized lab report are delivered.
- [ ] Applicable code, security, reliability, documentation, verification, CI, and PR review conditions in section H are met or accurately recorded as pending human review.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Nagios suppresses same-host service alerts while host is DOWN; checks continue | 1, 4 | Lab notification/status report |
| NCPA metric alerts depend on NCPA port OK, criteria c,u | 1, 2 | Renderer unit tests and Nagios -v in lab |
| Missing services create no dangling dependencies | 2 | Renderer missing-target tests and Nagios -v |
| Default on; off preserves old config | 3 | Byte comparison regression test |
| Generation uses shared validated apply path | 1, 5 | Source review and lab apply/rollback check |
| Source, tests, documentation, backend output, lab evidence | 5 | Changed files, verify logs, report |
| No dependency editing UI, new endpoint, or migration | Out of scope / N/A | Source diff |
| Security, reliability, CI and review gates | 6 | Review checklist and CI status; approvals remain human-owned |

## Plan

1. [x] Add failing renderer tests in `server/tests/unit/test_create_host_cfg.py` for default-on, NCPA metric/port pairing, absent target and setting-off baseline service list; implement in `server/app/network_discovery/create_host_cfg.py`, `host_config_templates.py`, `templates/servicedependency.cfg.tpl`, and `server/config.py`; run focused tests and `scripts/verify.sh backend`.
2. [x] Run Nagios validation and a host-down notification/state trial using the isolated lab; write sanitized evidence in `docs/test-runs/2026-10-17-issue-118/REPORT.md` and add its index entry in `docs/test-runs/README.md`.
3. [x] Update `spec files/Data_Model_and_Integrations.md`, `Backend_Modules_and_Routes.md`, `Implementation_Status.md`, `README.md`, and the relevant user manual with the behavior and setting; run `scripts/verify.sh docs`.
4. [ ] Re-read #118, run regressions including `test_plugin_reconcile.py` and `scripts/verify.sh all`, attach backend output, complete the security review, remove this progress file, and open a PR using `.github/pull_request_template.md`.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|
| 0 | Scope clarified with user: Nagios native host suppression plus NCPA dependency, default on | Issue updated | Plan ready |
| 1 | Added the user-approved NCPA TCP master service, notification-only dependencies, and strict default-on environment setting; off leaves the old service set | Focused renderer/reconcile (140 passed); `scripts/verify.sh backend` | 3751 passed, 14 skipped; backend OK |
| 2 | Ran Docker lab and wrote sanitized `docs/test-runs/2026-10-17-issue-118/REPORT.md` plus index row | Nagios -v: 3 dependencies, 0 warnings/errors; host outage: 1 host event, 0 service events; APIs show 3 critical services; `scripts/verify.sh docs` | Lab checks pass; docs gate fails because new environment variable is absent from README production settings table |
| 3 | Documented the configuration variable, dependency behavior, native host suppression, and lab result in README, owning specs, status, and user manual | `scripts/verify.sh docs` | green: 174 links, 25 environment variables, 17 browser routes, docs OK |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs`
- Result (first failing lines, or "green"): green — 174 documents, 25 environment variables, 17 browser routes; docs OK.
- Hypothesis: the scoped behavior is complete; remaining work is the final issue coverage audit and all-stage verification.
- Next action (one specific step, not "continue"): Re-read issue #118 and run the focused regression and `scripts/verify.sh all` with output saved for the PR.

## Decisions and notes

- The user approved verifying Nagios's built-in host-down suppression and implementing NCPA metric-to-port dependencies. The issue's explicit default-on setting takes precedence over its general backward-compatibility note. Issue body was updated accordingly.
- `hostdependency` cannot reference services; no host dependency object will be generated.
- The user approved a visible per-agent TCP port service as the master. The issue body records this decision. It is generated only while the feature is on and `check_tcp` is enabled.
- Sensitive-module review will check Nagios object escaping, secret exposure, and pre-apply validation before the PR.
