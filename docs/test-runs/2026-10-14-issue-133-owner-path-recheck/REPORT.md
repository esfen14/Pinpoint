# Test run: issue-133-owner-path-recheck

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Application source synced from issue branch `4dd006e3` to the existing VM; VM on-disk Git HEAD remains `1ca2c757` ([hash comparison and limits](../2026-10-14-issue-133-live/REPORT.md)). Browser harness base `93b8361e` plus the new, uncommitted assertion in this report's commit. |
| Plan | Issue #133 §G, `.agent/progress/issue-133.md` step 10; owner's chat request to independently repeat the four-step History path |
| Tester | OpenCode agent; distinct from owner's earlier reported manual pass |
| Environment | Existing appliance VM and preserved database, real previously recorded SSH fault/recovery events. No new fault, reset, or deployment. |
| Raw evidence | Ignored `client/test-results/playwright-results.json`; `/tmp/opencode/issue-133-owner-path-frontend.log`. No auth state, raw responses or screenshots committed. |

## Result

**Overall: Pass for the exact four-step History path.** The agent independently saw real CRITICAL and recovery rows for the owner's host/service filter, expanded them, and refreshed without losing the events. This is not a full manual requirement-by-requirement audit or a PR review approval.

Totals: Pass 2, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Owner's History path, independently repeated | Pass | `scripts/playwright-lab --project issue-133-live -g 'owner History path'`: 2/2 including admin setup. Opened `/history`, selected last 30 days to retain both previously generated events, filtered host `dev-28829a` and service `ssh-22-tcp`, observed a transition into CRITICAL and a later CRITICAL → OK recovery, expanded both rows and saw plugin output, an absolute timestamp on hover, and recovery duration, then clicked Refresh and saw both transition types remain. The first test iteration selected a recovery row as its ambiguous CRITICAL match and the duration assertion failed; the selector was narrowed to a transition *into* CRITICAL. Final focused rerun passed. |
| Full issue-133 live browser project / frontend regression | Pass | `scripts/playwright-lab --project issue-133-live`: 4/4 (admin setup, real-event walk, exact owner path, browser-only pagination/error). `scripts/verify.sh frontend`: green, 0 lint errors/26 warnings. The pagination/error case remains explicitly browser-intercepted, not a live backend outage. |
| Formal PR review / real CGI outage / real backend page two | Skipped | Not part of this read-only recheck; owner accepted focused VM scope for this module in chat, but no formal PR approval is inferred. |

## Deviations from the plan

No target fault was induced; earlier archive events were reused. The test used a 30-day time preset because the owner did not specify a preset and the events had aged beyond a short window. The failed intermediate assertion and selector correction are recorded above; no product defect was confirmed by that mismatch.

## Follow-up

- Request formal review of [PR #145](https://github.com/esfen14/Pinpoint/pull/145) after reconciling issue #133 Definition of Done, and obtain current-head CI conclusions at the final reviewable commit.
- Backend-dependent History gaps remain separate #141–#144. Owner described no major blockers in chat; this is not a substitute for inspecting review comments or a severity decision by a formal reviewer.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence summarized without raw response/auth data
