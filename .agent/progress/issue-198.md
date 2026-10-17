# Issue #198: Nagios availability for service reports

Branch: `issue-198-service-availability`
Status: in-progress

## Finish condition

- [ ] No snapshot-count field (including `total_snapshots`) exists anywhere in the
  Network Services or Device Services report payloads, nested instances, types,
  tables, cards, help or exports. API contract tests assert key absence, and
  frontend/export tests assert the snapshot-count columns/labels are absent and
  recorded-time/coverage durations have correct names and units. No stored
  snapshot data or general polling behavior is removed.
- [ ] Both service report uptime values and aggregate values come solely from Nagios
  archive durations. Tests seed conflicting or absent database snapshots and
  prove they have no effect.
- [ ] The same service instance has identical durations/uptime in both reports;
  unequal-duration fixtures prove weighted totals and no rounded reconstruction.
- [ ] Cover all-OK, mixed states, UNKNOWN, no known time, partially missing history,
  engine downtime and scheduled downtime. A zero-known instance is excluded from
  the weighted denominator but remains visible in coverage/instance counts.
- [ ] Cover one state beginning before the range, transitions exactly at the bounds,
  a brief Nagios-recorded outage between Pinpoint polls, custom inclusive dates,
  and malformed/negative/nonfinite values. Fixtures use the real native shape.
- [ ] Current metadata is visibly distinct from historical uptime, joined by identity
  with correct pending/missing behavior. No last-check timestamp is fabricated.
- [ ] Empty and failed archive responses have distinct outcomes; archive failure
  never falls back to DB values. Status failure preserves historical data only
  with its explicit notice. Login and `system.report` permissions still apply.
- [ ] Instrumented tests prove one archive request and at most one status request per
  report execution, independent of host count. Record latency/response size for
  24-hour and 90-day windows and the supported lab inventory; document any
  performance limit rather than asserting untested large-scale capacity.
- [ ] Both views' filters, sorting, pagination, custom ranges, rerun/error handling
  and CSV/XLS/PDF paths have interaction coverage. Snapshot counts are absent, with duration/coverage fields in their place. Host/OS reports and alert/notification reports remain green.
- [ ] On an exclusively owned lab, compare both views against the installed native
  Nagios availability output using identical windows, state filters and
  assumptions. Verify a brief recorded outage and missing history, and repeat a
  failing case once before filing a separate defect. Record exact tested commit,
  Core version, assumptions, duration/percentage results and verification output.

- [ ] All requirements in the plan above are implemented and proven by the finish-condition tests; no requirements are silently omitted.
- [ ] Add native-shape sanitized fixtures, backend unit/mocked API tests and frontend interaction/export regressions in the existing test directories; use test-first implementation and do not weaken existing tests.
- [ ] Update backend, data, frontend and implementation-status specifications and operator/help text, covering sources, semantics, removed fields, units, coverage, current status and retention limits.
- [ ] `scripts/verify.sh all` passes; attach actual output/results to the PR. Existing host/OS, alert and notification report regressions pass.
- [ ] A sanitized real-Nagios comparison report is committed under `docs/test-runs/`, with exact tested commit/Core version, assumptions, cases, timings and results. This issue authorizes the scoped live contract/comparison checks described above on an exclusively owned lab; no destructive reset or unrelated lab sweep.
- [ ] The PR references this issue, describes the contract changes and verification, and has green required CI. Human reviewer approvals and blocking-comment resolution remain merge gates; do not claim them in advance.

Requirement coverage (the full issue plan is covered by the final deliverable “All requirements”):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Native Core contract, HARD/no invented healthy state, maintenance included, retention/backtracking, native shapes | Real-Nagios comparison; native fixtures | Read-only VM probe and committed sanitized fixture/report |
| Duration-only source; identity preservation; weighted exact sums; UNKNOWN and coverage; zero-known visible; count configured instances | Duration/aggregation and edge-case items | Native-fixture helper and mocked API regressions with conflicting DB rows |
| Remove counts from both contracts, nested rows, types, UI/help and all exports; preserve storage/poller and host report | Snapshot-removal and interaction items | API recursive key assertions, UI/export tests, host regressions |
| Separate current bulk status, observation time, pending/missing/null/error handling | Current metadata and failure items | Bulk-call instrumentation, identity/pending/failure API and UI tests |
| URL/permissions/period/grouping/uptime names; seconds fields; timezone/custom dates; one bulk request each, timeout 10s and bounded total budget | Permissions, requests, period and interaction items | Mocked request/API and interaction regressions |
| Invalid archive sanitized 502 with no fallback; empty distinct; no-known null; failed rerun clears prior data/exports | Failure and interaction items | Adapter/route failures and rerun/export tests |
| Search/filter/sort/10-row pages/full filtered CSV/XLS/PDF; loading/error/empty | Interaction item | Frontend interaction and real export tests |
| 24h/90d latency/size/inventory; native same-options comparison, brief outage/missing history, repeat failure once | Instrumentation and real-Nagios items | Sanitized exact-commit/Core comparison report under docs/test-runs |
| Owning backend/data/frontend/status specs, operator denominator/retention guidance | Specification deliverable | Owning specs and operator guide, docs gate |
| No targets, DB migration/dependency/permissions/job/config changes; keep #134 separate and preserve unrelated reports | Exclusions; all-requirements deliverable | Diff inspection and scripts/verify.sh all |
| Test first, checkpoint, PR with contract/results, green required CI; review/merge remains human | Regression, verification and PR deliverables | Focused red/green results, full gate log, PR and required checks |

## Plan

1. [x] Probe exclusively owned installed Core read-only, record assumptions/shapes/timings and sanitized native fixtures in `server/tests/fixtures/` and `docs/test-runs/`; stop to resolve disproven assumptions before adapter code.
2. [x] Test first and implement strict shared service archive/current-status readers in `server/app/nagios/notifications.py` (focused module if warranted), with helper regressions in `server/tests/unit/`.
3. [x] Test first and replace only two service report aggregations in `server/app/api/system/report.py`, including bulk limits, dates, identity/coverage/error/permissions and regression tests.
4. [x] Test first and update `client/src/types/report.ts`, `pages/ReportsPage.tsx`, both service tables in `components/reports/`, `utils/exportData.ts` as needed, and interaction/export regressions in `client/src/test/`.
5. [ ] Update backend/data/frontend/status owning specs, operator help and test inventory; run focused and backend/frontend/docs/all checks; compare both deployed views against native Core, record exact evidence and performance in `docs/test-runs/`; finish acceptance audit and PR/CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Read-only Core 4.5.11 contract probe; native fixtures and sanitized report; no application edits | CGI subprocess probes as www-data, live-now and fixed-window repeat; scripts/verify.sh docs green | Blocked: scheduled fields separate; all-zero missing coverage; historical/live-now discrepancy |
| 2 | Added shared native duration/status adapter and both report route replacements, service tables/types/help/exports, owning specs and guide; native transition fixture | Helper/API/host/event focused suite: 97 pass; later helper/API: 45 pass; frontend stage green (8 new interactions); backend adapter stage 4014 passed/14 skipped; docs green | Green; final full gate must rerun current complete tree |
| resumed | Owner approved corrections; restored active progress | scripts/verify.sh docs | green |
| Intake | Isolated checkout from latest origin/main; requirement coverage and complete plan written before code | gh issue view 198 --json number,title,body,comments,state | Open; full finish conditions; scoped live checks authorized |

## State for the next session

- Last check run (exact command): `scripts/verify.sh frontend`
- Result (first failing lines, or "green"): green; tests/build/lint pass (existing warning-level lint findings remain).
- Hypothesis: Ending strictly before native query time prevents the no-history pseudo-state path. Native injected-log fixture verifies 720 OK / 130 CRITICAL / 50 UNKNOWN / 100 engine-down seconds; normalized uptime is 80% of 900 recorded seconds.
- Next action (one specific step, not "continue"): Run the isolated live installed-Core/application comparison while the complete-tree all gate runs.

## Decisions and notes

- Isolated checkout: `/tmp/pinpoint-issue-198`; main checkout untouched.
- Owner confirmed existing VM lab exclusively available for this issue on 2026-10-17.
- No migration, monitoring configuration change, destructive lab reset, snapshot fallback or availability targets are authorized/planned.
- Owning spec sections: backend report route catalog; data current versus durable history and aggregation; frontend Reports; status report data sources/verification limits.

- Probe evidence: `docs/test-runs/2026-10-17-issue-198-contract-probe/REPORT.md`; five sanitized native fixtures in `server/tests/fixtures/nagios_service_availability/`.
- Question for owner: approve adding scheduled durations to normalized states and explicitly accounting for unreported window seconds, then resolve the native current-state synthesis/fixed-window discrepancy before implementation? An alternate source or extra calls would require scope approval.
- Step 1 remains unticked: shape capture is done, but retention/backtracking and no-history assumptions are unresolved. No application behavior changed.

- Owner approved implementation/documentation on 2026-10-17 after explanation of maintenance inclusion and separate missing coverage. Corrections accepted together. Resolve Core pseudo-state by requesting only completed seconds (end strictly before request time), prove with a repeated native probe, and document exact adjusted window.

- Probe discrepancy resolved for implementation: end < result.query_time is enforced, with last-completed-second resolution. Fixed-window repetition returned missing coverage consistently; native isolated CGI fixture parsed actual transition log syntax and produced expected scheduled/engine/UNKNOWN/boundary totals.
- Dependency note: adapter/route/UI changes were verified together in one implementation round because the response contract changes atomically; no compatibility snapshot field retained. Broad adapter backend run collected 4014 tests before the new API test file existed; the final all gate must include that file.
- Remote draft PR: https://github.com/esfen14/Pinpoint/pull/201 . No readiness or CI claim yet.

- Added actual CSV/XLS/PDF serialization checks on rows produced by both tables and timezone/DST date regressions. An expanded pagination assertion initially used visible page text instead of the existing accessible name; corrected to Page 2/Page 1, with no product change.

- Round 3 evidence: expanded UI tests now 10 passed, including actual CSV/XLS/PDF serialization of both tables' full filtered rows and failed/invalid reruns; custom server calendar/DST API tests pass. Real isolated installed-Core check generated a six-second recorded outage; both APIs matched archivejson and native avail.cgi at 6 OK / 6 CRITICAL seconds, 50% during the exact 12-second window. Both also matched native missing-history coverage of 86400 seconds. Live fixture configuration initially lacked Core's required dummy contact; added a no-delivery contact while notifications remain globally disabled. Harness missing-history assertion was corrected to total missing coverage rather than assuming which native component would contain it. No product fallback was introduced.
- scripts/verify.sh all is running against the complete product tree; backend is mid-run. Browser fixture comparison remains next, before final report/checklist audit.
