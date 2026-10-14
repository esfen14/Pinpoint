# Test run: issue-133-live

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Issue branch `4dd006e3` for synced server/client source; Playwright spec and config were uncommitted during the browser run (recorded below). VM's on-disk Git HEAD still identified its prior install (`1ca2c757`); `scripts/vmlab sync --client` copied #133 source/build without changing that HEAD. Local/VM SHA-256 of `server/app/nagios/status.py` and built `client/dist/index.html` matched after sync. |
| Plan | Issue #133 §G and `.agent/progress/issue-133.md` step 6; not a full ISO QA queue |
| Tester | OpenCode agent |
| Environment | Existing installer-built Ubuntu appliance VM with Nagios; five demo targets on isolated `10.77.0.0/28`; preserved issue #113 database, not a fresh install. Installer base snapshot stamp predates current installer base-step hash. |
| Raw evidence | Local ignored `client/test-results/playwright-results.json` and `/tmp/opencode/issue-133-frontend-live.log`; appliance database inspected for counts only. No raw response, credential or screenshot committed. |

## Result

**Overall: Partial.** A real `web01` SSH service failure was acknowledged and recovered; the active acknowledgement disappeared and exactly one actorless AUTO_RESOLVED record was observed. The History page loaded real events and passed a targeted Playwright interaction walk. This does not verify every History requirement end-to-end, a fresh installer deployment, or reviewer approval.

Totals: Pass 3, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes (observed evidence) | Issue |
|---|---|---|---|
| J6-04 / #133 service auto-resolution | Pass | On the existing VM, `scripts/vmlab targets break web01 ssh` produced a CRITICAL `ssh-22-tcp` alert on `dev-28829a`; acknowledge API returned 201 and acknowledged filter listed the target. After `scripts/vmlab targets fix web01 ssh`, acknowledged filter no longer listed it. Read-only database count: active acknowledgement 0; exactly one AUTO_RESOLVED row for that target, actor null, preceded by an actor-attributed Acknowledged row. A second count after the browser run remained one. | — |
| History browser real-event walk | Pass | `scripts/playwright-lab --project issue-133-live`: setup-admin and issue-specific browser test passed (2/2). Opened `/history`; filtered real alert events by host/service, expanded a row to see plugin output, changed rows per page, refreshed, switched to Notifications, filtered Nagios then Pinpoint sources, exercised no-match and clear filters. First run failed only because the test locator matched a hidden `<option>` before the visible badge; selector was scoped to `tbody` and rerun passed. Raw JSON is ignored. | — |
| Local frontend regression | Pass | `scripts/verify.sh frontend` passed after Playwright test/config changes: 0 lint errors, 26 warnings. Prior full `scripts/verify.sh all` passed before the new live spec; rerun for final handoff pending. | — |
| Repeated live poll, failed/empty/stale poll, still-failing target, host recovery | Skipped | These are covered by isolated `server/tests/unit/test_status.py`, not deliberately induced on this live appliance. No claim of live pass. | — |
| Full manual History requirement audit / reviewer sign-off | Skipped | Source audit and focused real-event browser walk are not a full manual review of every requirement. Backend-dependent gaps remain tracked in #141–#144; human reviewer approval remains outstanding. | [#141](https://github.com/esfen14/Pinpoint/issues/141), [#142](https://github.com/esfen14/Pinpoint/issues/142), [#143](https://github.com/esfen14/Pinpoint/issues/143), [#144](https://github.com/esfen14/Pinpoint/issues/144) |

## Deviations from the plan

No VM reset: the owner's approval covered VM use and disposable lab administrator password reset, so the existing database was preserved. The supported `flask recover-bootstrap-admin` command was used with a privately generated temporary password, followed by the normal authenticated change-password API; credentials remained only in the private lab state directory. The VM Git HEAD was not changed by `sync`; matched file hashes plus observed behavior identify the deployed code. This targeted issue run did not claim ISO QA case status or update QA traceability.

## Follow-up

- Defects found in this run: none confirmed beyond the already filed backend History gaps #141–#144.
- Repeat on a clean installer-built appliance if release sign-off needs clean-deployment evidence. Obtain human PR review. Keep PR draft until applicable finish-condition boxes are supported.
- `web01` SSH service was restored after the failure injection.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by location and summarized, not pasted
