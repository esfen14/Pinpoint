# Test run: issue-133-more-browser

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Application source synced from issue branch `4dd006e3` to the existing VM (source/build hash comparison in [prior run](../2026-10-14-issue-133-live/REPORT.md)); test harness at `f1766fa2` plus uncommitted browser assertions, committed with this report. VM on-disk Git HEAD remains `1ca2c757`. |
| Plan | Issue #133 §G, `.agent/progress/issue-133.md` step 8; not an ISO QA queue |
| Tester | OpenCode agent |
| Environment | Existing appliance VM, preserved database, isolated lab. No target faults, database changes, reset or new deployment. |
| Raw evidence | Local ignored `client/test-results/playwright-results.json`; `/tmp/opencode/issue-133-more-frontend.log`. Raw captures/auth state are not committed. |

## Result

**Overall: Partial.** Real-event browsing passed again. A page-two count/controls scenario required intercepted pagination metadata because the live appliance had only 24 matching alert events; the error/retry scenario intercepted one browser response. Neither proves live backend page two or actual backend/CGI outage behavior.

Totals: Pass 3, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Existing real-event History interactions | Pass | `scripts/playwright-lab --project issue-133-live`: admin setup and both History tests passed (3/3 total). Existing test covered real filters, detail, sorting, tabs, refresh, source, empty state and clear. | — |
| Browser pagination controls and error/retry display | Pass | The additional test first expected a real second page and failed: 24 events over 30 days, so no second page. Revised scope uses real backend rows with browser-intercepted page metadata to exercise Next, Previous and the page label; it then returns a one-off synthetic HTTP 503 for the alerts list, verifies error text, retries with the unmodified backend, and changes page size. Focused run 2/2, full issue-133-live project 3/3. The injected error did not touch the VM backend. | — |
| Frontend regression | Pass | `scripts/verify.sh frontend` passed (0 lint errors, 26 warnings). | — |
| Actual live backend page two | Skipped | Only 24 matching events existed. No synthetic history data was added to the preserved appliance. The browser pagination assertion is fixture-based and cannot demonstrate backend page-two correctness. | — |
| Real backend/CGI outage and recovery | Skipped | Only one browser response was intercepted. No Nagios outage or server failure was induced. Isolated server tests remain the evidence for failed/empty polls. | — |

## Deviations from the plan

A real pagination check could not reach the second page. The first failing Playwright run recorded `Showing 1–24 of 24 events`. The controlled fixture initially mixed synthetic totals with a real empty page-two response and failed (`Showing 26–24 of 24 events`); the fixture was corrected to use one previously fetched real row on page two. It is explicitly labeled as browser-only, not a backend pass. The existing VM snapshot stamp is older than current installer base steps; no destructive provision was attempted.

## Follow-up

- No product defect confirmed by this run. Backend-dependent History issues remain #141–#144.
- If an actual backend pagination proof is required, use a separately approved disposable dataset or wait for sufficient organic events; do not mislabel the browser fixture as live backend evidence.
- Bounded real-poll acknowledgement reliability check is planned separately. Human review and current-head CI remain outstanding.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence summarized without raw responses or auth state
