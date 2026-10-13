# Issue #113: System Implementation Add Configurable Notification Policy With Nagios Timeperiods and Settings Screen

Branch: `issue-113-notification-policy`
Status: in-progress

## Finish condition

- [x] **Part 1.1 (System):** A policy with quiet hours produces a valid `define timeperiod` block, and hosts, services and contacts reference it.
- [x] **Part 1.1 (System):** With the default policy, generated `hosts.cfg` is byte-identical to the output before this change.
- [x] **Part 1.1 (System):** Saving an invalid policy (bad time, overlap, unknown option letter, interval out of range) returns 400 with a message that names the field.
- [x] **Part 1.1 (System):** A stale `version` returns 409. A policy that Nagios rejects is rolled back and returns 422 with Nagios's message.
- [x] **Part 1.1 (System):** Without `settings.system` the API returns 403.
- [x] **Part 1.1 (System):** On a lab appliance, a forced state change inside a quiet window sends no notification, and the same change outside it does.
- [x] **Part 1.1 (System):** Existing hosts, services, contacts and Check interval behavior are unchanged.
- [x] **Part 1.2 (Web-Interface):** The old toggle's label and help text say it controls the header bell only.
- [x] **Part 1.2 (Web-Interface):** A user with `settings.system` can add, edit and remove quiet-hour windows and change options and interval, and the values reload after a refresh.
- [x] **Part 1.2 (Web-Interface):** Invalid input is blocked in the form with a message naming the field, and a server 400, 409 or 422 shows the server's message.
- [x] **Part 1.2 (Web-Interface):** A user without the permission does not see the card and cannot reach it by URL.
- [x] **Part 1.2 (Web-Interface):** The existing General and System settings tests still pass.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Implement NotificationPolicy model | Model creation | Unit test |
| Migration | Database migration | DB check |
| Timeperiod rendering | Nagios config | `nagios -v` |
| Parameterize templates | Template update | `test_create_host_cfg.py` |
| API endpoints | API endpoints | `test_notification_policy_api.py` |
| UI settings card | Frontend settings | Manual/automated test |
| Permissions check | Permission check | API test |

## Plan

1. [x] Create `NotificationPolicy` model in `server/app/system_models.py`.
2. [x] Add multi-bind migration via `flask db migrate` (the `--multidb` flag is unsupported in this repository's initialized multi-bind Alembic environment).
3. [x] Create `server/app/api/system/notification_policy.py` and register it in `server/app/api/system/__init__.py`.
4. [x] Create `server/app/network_discovery/templates/timeperiod.cfg.tpl` and update `host.cfg.tpl`, `service.cfg.tpl`, `contact_template.cfg.tpl` and rendering in `host_config_templates.py`.
5. [x] Update `server/app/network_discovery/create_host_cfg.py` to render the timeperiod in the candidate file.
6. [x] Create `client/src/types/notificationPolicy.ts` and `client/src/lib/notificationPolicyApi.ts`.
7. [x] Create `client/src/components/settings/NotificationPolicySettings.tsx`, place in permission-gated System tab through `SystemSettings.tsx`, and relabel General bell toggle.
8. [x] Strengthen generated-config regression and full contact/service propagation in `server/tests/unit/test_notification_policy_templates.py`, `server/app/network_discovery/create_host_cfg.py`, `server/app/network_discovery/host_config_templates.py`.
9. [x] Expand frontend permission/label tests in `client/src/test/NotificationPolicySettings.test.tsx` and related Settings tests; correct UI as needed.
10. [x] Review backend validation/apply edge cases and default byte parity in `server/tests/unit/test_notification_policy_api.py`, `server/tests/unit/test_notification_policy_templates.py` and owning backend modules.
11. [x] Run approved Docker lab for `nagios -v` and inside/outside notification events; record sanitized evidence under `docs/test-runs/` (host DOWN and service CRITICAL dispatch; browser/VM/email evidence remains unverified).
12. [x] Update manual and owning specs (`spec files/Backend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`), then verify docs.
13. [x] Exercise browser save/reload with the approved Docker lab, update `docs/test-runs/2026-10-13-issue-113-notification-policy/REPORT.md` and check required finish evidence.
14. [x] Run `scripts/verify.sh all`, re-read issue and decide PR status from observed evidence (draft pending installer VM/inbox/review).
15. [x] Inspect isolated VM-lab prerequisites and deploy issue branch to installer-built appliance without touching unrelated lab work (`scripts/vmlab`, `demo/`, VM plan). Preflight: 98 GB disk available, 6.5 GiB RAM available before shutting down Docker lab, VirtualBox appliance powered off with base snapshot present; retained `demo-ready` snapshot must not be deleted.
16. [x] Run `nagios -v`, force service CRITICAL within/outside a quiet window, and verify browser/API behavior in VM; record sanitized evidence in `docs/test-runs/2026-10-13-issue-113-vm-service-retest/REPORT.md`. Nagios dispatch observed (0 quiet, 1 outside); mailbox arrival unverified.
17. [x] Re-run applicable verification, update owning status/docs and draft PR with observed VM outcome; retain progress file until all finish conditions are proven.
18. [ ] Attach the full `scripts/verify.sh all` output to PR #140 in an approved, sanitized artifact; obtain required reviewer approval before marking all issue boxes complete.
19. [x] After lab owner privately configured Gmail SMTP, compare quiet-window suppression and outside-window CRITICAL arrival with owner-reported mailbox result; record separate sanitized runs. No independent agent mailbox access or direct Settings test-email send was used.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan created | N/A | N/A |
| resumed | Issue comment approves sensitive-module changes and repository Docker lab | N/A (no prior check run) | in-progress |
| 1 | Added failing model-default test then `NotificationPolicy` model | `.venv/bin/python -m pytest tests/unit/test_notification_policy.py -q`; `scripts/verify.sh backend` | focused green (1 passed); broad check timed out after 45%, not a test failure |
| 2 | Added failing migration round-trip test, generated multi-bind revision, manually seeded singleton | `.venv/bin/python -m pytest tests/unit/test_notification_policy_migration.py -q`; `scripts/verify.sh backend` | 1 passed; 2354 passed, 14 skipped |
| 3 | Added failing API cases; implemented guarded GET/PUT, validation and rollback; updated route catalog for drift check | `.venv/bin/python -m pytest tests/unit/test_notification_policy_api.py -q`; `scripts/verify.sh backend` | 11 passed; 2365 passed, 14 skipped |
| 4 | Added failing rendering test, conditional period and template directives preserving default | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend` | 2 passed; 2367 passed, 14 skipped |
| 5 | Added failing full-file test; render custom period in shared candidate config | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend` | 3 passed; 2368 passed, 14 skipped |
| resumed | No earlier plan steps repeated | `scripts/verify.sh backend` | green: 2368 passed, 14 skipped |
| 1 | Added failing client adapter test, typed wire contract and shared GET/PUT wrapper; fixed test typing after build exposed widened literals | `npm run test -- src/test/NotificationPolicyApi.test.ts`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-round1.log 2>&1` | green; 505 frontend tests and build/lint pass (25 warnings) |
| 2 | Added failing interaction suite, policy card on System tab and corrected bell-only label | `npm run test -- src/test/NotificationPolicySettings.test.tsx`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-round2.log 2>&1` | green: focused 5 passed; full frontend stage passed (26 warnings) |
| 3 | Added failing contact propagation/template-registration test; custom contacts inherit a non-registering policy template while default users retain generic-contact | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend > /tmp/opencode/issue113-backend-round3b.log 2>&1` | green: 4 focused; 2369 passed, 14 skipped |
| 4 | Added Settings permission/fragment and bell-label regression assertions; existing tab guard and corrected label already satisfied them | `npm run test -- src/test/SystemSettingsConflict.test.tsx src/test/PageAccess.test.tsx`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-round4.log 2>&1` | green: 27 focused tests; frontend stage green (26 warnings) |
| 5 | Reproduced boolean-version optimistic-lock bypass and rejected it before Nagios apply | `.venv/bin/python -m pytest tests/unit/test_notification_policy_api.py -q`; `scripts/verify.sh backend > /tmp/opencode/issue113-backend-round5.log 2>&1` | green: 12 focused; 2370 passed, 14 skipped |
| resumed | Re-read issue and continued at default byte-parity proof | `scripts/verify.sh backend > /tmp/opencode/issue113-resume-backend.log 2>&1` | green: 2370 passed, 14 skipped |
| 1 | Rendered identical isolated fixture on pre-change commit `92a896d5`; checked normalized output with `cmp`; added golden-file byte comparison with active email contact | `.venv/bin/python -m pytest tests/unit/test_notification_policy_templates.py -q`; `scripts/verify.sh backend > /tmp/opencode/issue113-backend-parity.log 2>&1` | green: 5 focused; 2371 passed, 14 skipped |
| 2 | Docker lab: upgraded existing seeded DB after initial smoke failed (missing table); repeat 9/9 passed; policy PUT and `nagios -v` accepted custom period; forced host DOWN yielded zero notifications quiet versus 28 outside; recorded partial sanitized report | `scripts/lab smoke`; `docker compose -f lab/compose.yaml exec appliance /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg`; `scripts/verify.sh docs > /tmp/opencode/issue113-docs-lab.log 2>&1` | smoke 9/9 after upgrade; Nagios 0 warnings/errors; docs green; service CRITICAL and browser still untested |
| 3 | Enabled SSH plugin, generated five service checks, forced CRITICAL to HARD during quiet/24x7 windows; sanitized partial report updated | `docker compose -f lab/compose.yaml exec appliance /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg`; `scripts/verify.sh docs > /tmp/opencode/issue113-docs-service.log 2>&1` | 13 services and 0 Nagios errors; 0 quiet service notifications versus 28 outside; docs green |
| 4 | Documented API contract, model/Nagios ownership, settings UI and operator instructions; status notes Docker coverage and remaining gaps | `scripts/verify.sh docs > /tmp/opencode/issue113-docs-specs.log 2>&1` | green |
| 5 | Added opt-in Playwright Docker browser flow: sign in, save quiet window, refresh/reload, remove and save; updated sanitized report and status | `LAB_ADMIN_PASSWORD=… node_modules/.bin/playwright test --config=notification-policy.lab.config.ts`; `scripts/verify.sh docs > /tmp/opencode/issue113-docs-browser.log 2>&1`; `scripts/verify.sh frontend > /tmp/opencode/issue113-frontend-browser.log 2>&1` | Playwright 1 passed; docs green; frontend green (26 warnings) |
| resumed | Re-read issue and comments; clean branch, reran prior frontend verification | `scripts/verify.sh frontend > /tmp/opencode/issue113-resume-frontend.log 2>&1` | green (26 warnings) |
| 1 | Verified full suites and acceptance regressions, corrected lab report commit attribution; remaining installer VM/inbox/reviewer conditions prevent ready-for-review claim | `scripts/verify.sh all > /tmp/opencode/issue113-all.log 2>&1`; focused backend/frontend; `scripts/verify.sh docs > /tmp/opencode/issue113-docs-correction.log 2>&1` | all green: 2371 backend passed, 14 skipped; 513 frontend passed; docs green; focused 93 backend/38 frontend passed |
| resumed | User explicitly authorized VM testing; issue unchanged, clean branch and docs check rerun | `scripts/verify.sh docs > /tmp/opencode/issue113-vm-resume-docs.log 2>&1` | green |
| resumed | Rechecked docs, tested VM service CRITICAL to HARD in and out of quiet hours (0 vs 1 Nagios dispatch), restored target/policy; Playwright VM save/reload; corrected initial overclaim in separate retest report | `scripts/verify.sh docs > /tmp/opencode/issue113-vm-resume-docs.log 2>&1`; VM Nagios log; `LAB_BASE_URL=… node_modules/.bin/playwright test --config=notification-policy.lab.config.ts`; `scripts/verify.sh frontend > /tmp/opencode/issue113-vm-frontend.log 2>&1` | VM dispatch comparison passed; browser 1 passed; frontend green (26 warnings); inbox unverified |
| resumed | Audited issue E/F/H, checked evidenced items on issue, reran full local verification; PR CI green but no reviewer approval and full local output not attached | `scripts/verify.sh all > /tmp/opencode/issue113-final-all.log 2>&1`; `gh pr checks 140` | all green (2371 backend, 14 skipped, 513 frontend, 26 warnings); PR checks green; issue remains open/draft |
| resumed | Fast-forwarded clean installer checkout to `697869e`; applied only current `configure-pinpoint-privileges.sh` to existing VM, recorded incremental mail transport run | VM scoped helper with empty stdin, `nagios -v`, `scripts/vmlab health`, `scripts/verify.sh docs` | Helper reached JSON validation without password prompt, Nagios zero warnings/errors, appliance 60/0; SMTP send and inbox untested; existing base snapshot still older |
| resumed | Owner confirmed earlier recovery inbox receipt; ran paired VM CRITICAL trial with quiet window, then no quiet window; restored target SSH and policy; documented flapping confounder and non-flapping retry | Nagios log/status, `nagios -v`, journal msmtp response, `scripts/vmlab targets status`, `scripts/verify.sh docs` | Quiet web02 0 dispatch; first outside web02 flapped, so repeated on web01: 1 Nagios CRITICAL dispatch and Gmail SMTP 250/EX_OK; specific CRITICAL inbox receipt awaits owner |
| resumed | Owner clarified duplicate pasted CRITICAL body was one web01 email, plus a separate recovery email; documented new mailbox confirmation run | Compared owner-provided timestamps/types with Nagios notification counts and SMTP 250 journal records; `scripts/verify.sh docs` | One web01 CRITICAL and one RECOVERY delivered per owner; quiet web02 inbox/spam absence still awaiting confirmation |
| resumed | Owner reported no quiet-window web02 CRITICAL email after inbox/spam question; recorded a separate sanitized follow-up run without changing VM state | Owner confirmation correlated with earlier zero Nagios quiet notification events; `scripts/verify.sh docs` | Paired email comparison supported: no web02 quiet email observed, web01 outside CRITICAL delivered; review and PR full-output attachment still pending |

## State for the next session

- Last check run (exact command): `scripts/verify.sh docs > /tmp/opencode/issue113-mail-docs.log 2>&1`
- Result (first failing lines, or "green"): green; Nagios quiet web02 0 CRITICAL dispatch; outside non-flapping web01 1 CRITICAL dispatch, Gmail SMTP 250/EX_OK. Owner confirmed earlier recovery inbox receipt. Policy restored to no quiet hours; web01/web02 SSH UP.
- Hypothesis: Owner confirmed one web01 CRITICAL inbox arrival at 15:22:08 UTC and a separate recovery at 15:22:29; owner reported no web02 quiet-window email at ~15:19 UTC after inbox/spam question. F full local output attachment and H reviewer approval remain outstanding.
- Next action (one specific step, not "continue"): Attach a sanitized full local `scripts/verify.sh all` output to PR #140 by an approved means, then seek reviewer approval; keep PR draft until all issue boxes are satisfied.

## Decisions and notes

- Reusing `SystemSettings` singleton pattern for `NotificationPolicy`.
- `flask db migrate --multidb` and `flask db upgrade --multidb` are not recognized by installed Flask-Migrate; `flask db migrate` generated both default and history functions. Reviewed generated schema; manual seed necessary because autogenerate does not populate singleton data. Migration round trip tested on disposable databases.
- Resolved blocker: issue comment from esfen14 on 2026-10-13 approves and instructs use of repository Docker labs. No source code changed yet.
- The earlier pre-existing worktree modification to `client/src/test/SystemSettingsConflict.test.tsx` was not included in issue commits; inspect status before touching it.
- Plan expanded after lab evidence showed browser UI flow remains untested and the issue requires full verification; added steps 13–14. Prior session stopped at five rounds; step 10 now has an independent fixture from pre-change commit `92a896d5` and a byte comparison (timestamp normalized only). Plan revised because the original final step omitted explicit lab, documentation and regression stages; these are required deliverables. This session must verify actual default generated-file byte parity against pre-change output, not only template-level assertions. Also review timeperiod syntax against Nagios (`24:00` and comma-separated ranges) in the Docker lab, and review whether service default directives must be explicit without violating byte parity.
- User explicitly approved VM testing in the current conversation. Plan expanded with VM deployment, observation and reporting steps because earlier draft lacked installer-built VM evidence. Draft PR #140 opened with progress file retained and outstanding VM/inbox/review work listed. Five rounds completed the prior session; stop per workflow §4. Sensitive-module review: API validation whitelists weekday/time/option values, no shell interpolation introduced, generated file uses fixed destination and existing Nagios pre-apply validation; no secrets added to policy logs/responses. Docker lab and documentation done; installer VM, inbox delivery and reviewer approval remain unverified.
