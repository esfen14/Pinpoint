# Test run: issue-117-live-browser

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Application source `b0a105e6443a32e9bf5a0344e107949b21aede59`; the browser tested the identical one-line drawer fix before it was committed, with no intervening source edits |
| Plan | [Manual Topology Acceptance](../../../server/tests/plans/MANUAL_TOPOLOGY_ACCEPTANCE.md), continued at the owner's request |
| Tester | Codex |
| Environment | Chromium/Playwright, real Vite frontend, real Flask HTTP backend and Nagios Core 4.5.11 in a dedicated disposable Ubuntu 22.04 container; isolated routed targets within `10.77.0.0/28`; separate management bridge publishes HTTP only on host loopback |
| Databases | Private system/history SQLite databases upgraded through `b117d9a2c041`; device fixtures plus history snapshots initialized from the real checked HARD-UP Nagios baseline |
| Raw evidence | Local host `/tmp/issue117-live-e0853d16/` (`browser.log`, `server.log`, `nagios-final.log`); `/tmp/issue117-real-browser-run3.log`; `/tmp/issue117-real-topology.png`; driver `/tmp/issue117-browser-live.py`, browser `/tmp/issue117-real-browser.cjs`; regression `/tmp/issue117-drawer-proof.log`, gate `/tmp/issue117-live-browser-frontend.log` |

## Result

**Overall: Partial.** All seven executed continued-test cases passed on the corrected
source. The real browser now covers the previously unverified frontend/backend/
Nagios save path. Final pushed-tree CI/human review are separate; no SMTP delivery,
production deployment or new polling acceptance is claimed.

Totals: Pass 7, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (observed behavior; evidence) | Issue |
|---|---|---|---|
| B117-01 | Pass | Standard login HTTP API accepted private ephemeral administrator and reader credentials. Browser used actual session cookies and permission APIs; no API interception. Credentials were supplied in memory and never logged or committed. `browser.log`, `server.log`. | — |
| B117-02 | Pass | Topology selected child-a, set two parents, received 200, displayed success and retained both selections after a full browser reload. Three configured edges appeared. Every save used the actual shared writer and real Nagios validation/reload. | — |
| B117-03 | Pass | Selecting child-a as parent of parent-a returned 400 with the server cycle message, kept the draft checked and did not corrupt saved graph. Clearing that rejected draft and saving succeeded. | — |
| B117-04 | Pass | Inventory drawer showed both persisted parents. Clear-all/save returned 200 and displayed success; after browser reload neither parent was selected. Setting parent-a again displayed a persistent success message. The new integration regression also verifies that the drawer does not unmount/refetch its detail while the Inventory table refreshes. | — |
| B117-05 | Pass | Returning to Topology showed two edges and the real GET response reported child-a's parent IDs as `[1]`, matching the Inventory save. | — |
| B117-06 | Pass | A separately authenticated reader saw configured parents and read-only text with no checkboxes. A direct parent PUT returned 403. No browser page errors occurred throughout the run. | — |
| B117-07 | Pass | New drawer integration regression failed before the fix, then passed with 43 focused frontend tests. Full frontend gate: 52 files / 654 tests passed, production build passed, lint had 0 errors / 30 warnings. Documentation checks passed. | — |
| B117-08 | Skipped | Source `519a00a8` had all three CI jobs green in [run 38713297084](https://github.com/esfen14/Pinpoint/actions/runs/38713297084). This report does not claim final CI for the later drawer fix/report commit; follow the implementation PR's current checks. | [#117](https://github.com/esfen14/Pinpoint/issues/117) |

## Deviations from the plan

- The first continued browser run could not reach a correctly started backend
  through an internal-only Docker network. A dedicated disposable management
  bridge, following the existing Docker lab pattern, allowed loopback HTTP access.
  The target networks stayed isolated; no discovery scan or host route was added.
- The next real browser run on `519a00a8` reproduced a product defect: the Inventory
  parent save callback reloaded/unmounted the entire detail drawer and could erase
  its success message. Evidence is retained at `/tmp/issue117-live-5d3945f0/browser.log`.
  The new `DeviceParentDrawer.test.tsx` reproduced it, and the one-line callback fix
  retains the editor while refreshing the table. This is part of [#117](https://github.com/esfen14/Pinpoint/issues/117), not an unrelated change.
- History snapshots were initialized from actual Nagios checks to make Inventory
  rows available without configuring a separate CGI/status poller. This run proves
  the parent edit/visualization integration, not an additional poller journey.
- Authentication used real login requests in the browser request context; no login
  form recording, trace, credential screenshot or storage-state file was created.
- Private test accounts and sendmail sink were confined to owned containers. All
  owned containers/networks were removed in `finally`; the shared lab/VM was untouched.

## Follow-up

- Human review and current CI: [PR #174](https://github.com/esfen14/Pinpoint/pull/174).
- The separate one-attempt notification guarantee remains [#173](https://github.com/esfen14/Pinpoint/issues/173); this browser run does not change the routed trial's timing conclusions.
- Original routed failure/recovery, migration and writer rollback evidence remains in
  [the preceding report](../2026-10-15-issue-117-manual-topology/REPORT.md).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No private addresses outside the documented target lab range
- [x] Raw evidence is referenced, not committed
