# Test run: issue-133-expanded

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Application source synced from issue #133 branch at `4dd006e3` (VM on-disk Git HEAD still `1ca2c757`; matching source/build hashes recorded in prior [run](../2026-10-14-issue-133-live/REPORT.md)). Expanded Playwright spec/config were uncommitted during this run; they are committed with this report. |
| Plan | Issue #133 §G; `.agent/progress/issue-133.md` step 7; not an ISO QA queue |
| Tester | OpenCode agent; separate owner-reported manual path noted below |
| Environment | Existing Ubuntu/Nagios VM with preserved database and lab targets on `10.77.0.0/28`; disposable administrator and Staff accounts. No reset, discovery or new fault injection in this run. |
| Raw evidence | Ignored `client/test-results/playwright-results.json` (last run was restricted project); local `/tmp/opencode/issue-133-expanded-frontend.log`. Do not commit auth state, raw JSON or screenshots. |

## Result

**Overall: Partial.** Expanded real-event History browser interactions and a restricted-role permission guard passed. This is not a full manual inspection of every requirement or proof of backend-dependent gaps. The owner's four-step manual result is reported separately, not counted as agent-observed.

Totals: Pass 3, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (observed evidence) | Issue |
|---|---|---|---|
| Expanded administrator History browser | Pass | `scripts/playwright-lab --project issue-133-live`: 2/2 passed (admin setup and lab test). On real events, filtered alert host/service, expanded plugin output, changed rows per page, sorted host, refreshed, exercised incomplete custom-range validation/clear, switched tabs, filtered Nagios and Pinpoint notifications, expanded each source's message/detail, and checked no-match/clear. This re-ran the earlier coverage with extra checks; it did not assert exact cross-event association. | — |
| Restricted History guard | Pass | First attempt failed in setup because the retained disposable Staff account no longer had the expected temporary password; no permission assertion ran. `scripts/vmlab setup-restricted` re-created/reset only that disposable account. Rerun `scripts/playwright-lab --project issue-133-restricted`: 2/2 passed. Direct `/history` redirected to permitted `/settings`; `GET /api/system/history/alerts` returned 403. | — |
| Frontend regression | Pass | `scripts/verify.sh frontend`: tests, build and lint passed (26 warnings, 0 errors). | — |
| Full requirements manual walk / exact links / load and error injection | Skipped | Existing [audit](../2026-10-14-issue-133-history-audit/AUDIT.md) records partly-met backend features (#141–#144). This run did not induce server errors, build enough events for live pagination, or validate all columns and associated-event identity. Isolated frontend tests cover other states but are not a live pass. | [#141](https://github.com/esfen14/Pinpoint/issues/141), [#142](https://github.com/esfen14/Pinpoint/issues/142), [#143](https://github.com/esfen14/Pinpoint/issues/143), [#144](https://github.com/esfen14/Pinpoint/issues/144) |

## Owner-reported manual observation (not included in agent pass totals)

The owner stated in chat that their single manual `/history` path worked: filtering host `dev-28829a` and service `ssh-22-tcp`, seeing CRITICAL and recovery events, expanding detail, and refreshing. No independent transcript, screenshots or timestamps were supplied. This is a reported observation, not a claim that the agent witnessed the owner's session or that every History requirement passed.

## Deviations from the plan

No new application deployment, target break/fix, database reset or destructive fixture. Expanded browser spec checked read-only History interactions; resetting the disposable Staff account was required to run its existing forced-password-change setup. The first restricted attempt was a fixture failure, not a product permission failure. The Playwright runner's JSON file is overwritten per invocation; command summaries above distinguish the two runs.

## Follow-up

- Defects found: none newly confirmed. Backend History gaps remain separately filed as #141–#144.
- Human PR review and current-head CI conclusions still needed. A broader manual requirement-by-requirement page walk, live pagination/error states, and deployment/performance sign-off are not claimed here.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by location and summarized, not pasted
