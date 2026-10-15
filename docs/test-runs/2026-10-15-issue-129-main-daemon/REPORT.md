# Test run: issue-129 main Nagios daemon

| | |
|---|---|
| Date | 2026-10-15 Asia/Manila (2026-10-14 UTC) |
| Commit tested | Application `c9f8e263`; installed helper functional source `15c27d1`, published installer `b166953` |
| Plan | [Check secret transport](../../plans/Issue_129_Check_Secret_Transport.md); issue #129 sections E/G |
| Tester | Codex |
| Environment | Existing Ubuntu 22.04.5 QA appliance, Nagios 4.5.11, NCPA client 1.2.4; existing web01 on guarded 10.77.0.0/28. Shared system/history databases upgraded from 143c48cd6663 to 7db78f308ee5. |
| Raw evidence | Local git-ignored `test-results/issue-129/`: `main-daemon-resume-verify.log`, `clean-checkout-migration.log`, `main-daemon-setup.log`, `main-daemon-observed.log`, `main-daemon-acceptance.log`. Root-private guest pre-upgrade DB backups: `/var/backups/pinpoint/issue129-pre-upgrade/`. |

## Result

**Overall: Partial.** Supported macro-secret implementation now passes installed full generation/apply/reload and main NCPA engine acceptance. Remaining complete-issue live port/cleanup journeys and paired human reviews still prevent issue completion. Password-bearing SMB is explicitly refused under the owner's chosen unsupported-plugin policy.

Totals: Pass 8, Fail 0, Blocked 1, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Full verification on published source | Pass | 2766 backend tests passed/14 skipped; 554 frontend tests passed; build/docs passed; lint 0 errors/29 existing warnings. Native/NCPA process tests and config/snapshot regressions included. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Paired publication/application CI | Pass | App ea0a4284/c9f8e263 published with authorization. Docs/backend/frontend CI all green on c9f8e263. Installer b166953 published through approved fork as draft PR #7; no PR merged. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Existing database upgrade | Pass | Stopped application before private backups; real multi-bind upgrade applied b7d3f1a9c8e5, c5e2a8f4d716 and 7db78f308ee5; sync-permissions completed. Stored web01 port 5693 verified. This run does not repeat downgrade. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Full generated configuration/apply/reload | Pass | Clean current build enabled check_ncpa and set deployed web01 port MONITORED through authenticated admin test-client routes (HTTP 200), using actual DB/permissions/renderer/helper/Nagios validation and reload. Follow-up regeneration was unchanged. Fifteen generated NCPA services loaded in main daemon. Duplicate pending-device rows without tokens remained skipped by existing behavior. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Main NCPA results and protected host readability | Pass | Forced actual main-daemon web01 CPU, memory and root-disk checks returned OK with performance data. Stock-vs-adapter parity is separately recorded in the earlier helper report. Live hosts 0640; nagios user read probe succeeded. Inherited host monitoring is paused, so these were forced checks rather than scheduled cadence evidence. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Main check process/config/log secrecy | Pass | Observed three running adapter process IDs via /proc; protected resource credentials absent from their argv. Current live hosts, status.dat, Nagios log and application service journal for acceptance interval contained no resource credential literals. No raw credentials printed. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Actual stored snapshot secrecy | Pass | Ran real authenticated CGI get_status poll into shared history DB. Three latest web01 NCPA snapshot rows stored only command names, without ! arguments or token literals in command/output. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Real validation rejection/resource rollback | Pass | Stopped Gunicorn/scheduler to avoid concurrent writers. Test injected an invalid host/service reference after real rendering and an additional synthetic owned resource slot. Real Nagios binary rejected candidate; production generation transaction invoked installed helper rollback. Resource bytes, uid/gid/mode restored exactly; live hosts unchanged. Renderer injection was test-only, not a deployed source change. Application restarted. Reload-failure behavior remains covered by automated tests, not an induced daemon fault here. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Paired human review/final acceptance | Blocked | App PR #161 and installer PR #7 remain draft; required reviewer approvals not obtained. Other section G journeys remain below. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Non-default-port and failed-install/cleanup live journeys | Skipped | This run used existing deployed port 5693 and did not intentionally fail an install or run remote cleanup. Automated coverage passes, but those mandatory live journeys still need execution. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |
| Complete ISO and remaining native endpoint parity | Skipped | No ISO built/reinstalled. Native installed synthetic check_nt evidence is in earlier transport report; no new real Radius/MySQL endpoint parity. SMB remains refused because secure child credential input is unsupported. | [#129](https://github.com/esfen14/Pinpoint/issues/129) |

## Deviations from the plan

The guest's original application checkout contained prior dashboard/status edits and untracked client/.npm. Preserved them by serving detached c9f8e263 from `/opt/pinpoint/issue-129-acceptance/server` through the service's `129-acceptance.conf` WorkingDirectory drop-in; existing installed venv and shared databases are used. No snapshot reset, reprovision, original source overwrite or new agent deployment occurred.

Global Nagios notifications were suppressed during forced checks and restored to their original enabled value afterward. Existing host pause state was retained. Temporary acceptance scripts were removed. Gunicorn and Nagios remain active with the clean upgraded build; QA appliance and web01 remain running. Installed restricted helper/sudoers remain present. No production deployment claimed.

## Follow-up

- Complete mandatory live non-default-port and intentional failed-install/cleanup journeys before checking final issue completion.
- Obtain paired application/installer review; keep unsupported password-bearing SMB refusal explicit.
- Ask before pushing the new report/progress checkpoint; previously published source is green in application CI.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
