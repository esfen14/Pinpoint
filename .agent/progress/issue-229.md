# Issue #229: TC-RPT-06: Host Availability and Hosts by OS give no "no data" message for a period with no data

Branch: `issue-229-host-reports-no-data`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [x] When no host has recorded time in the period, Host Availability and Hosts by OS show a clear no-data message (the wording may match the other tabs), and do not show the "generated successfully" banner as if data existed.
- [x] The no-data wording is consistent across the six tabs, or the difference is documented. (Documented in `Frontend_Modules_and_Routes.md`.)
- [ ] Re-run TC-RPT-06 on the fixed build and record it in a new run report; keep this original result. **Needs a person: the fixed build must be deployed to the lab first. Not done in this PR.**
- [ ] `scripts/verify.sh all` passes (CI on Linux is the real check; see Decisions and notes).

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Host Availability shows 13 `Unknown` rows and a success banner for a period with no data | Item 1 | `client/src/test/HostReportsNoData.test.tsx` (table notice; page shows no "generated successfully") |
| Hosts by OS shows the same with no message | Item 1 | same file, Hosts by OS case |
| Wording differs between tabs | Item 2 | documented in `Frontend_Modules_and_Routes.md` |
| Re-run TC-RPT-06 on a fixed build | Item 3 | lab run after deployment (a person) |
| Verification gate | Item 4 | `scripts/verify.sh all` (CI) |

## Plan

"No recorded time" means every listed host has zero known host-state time (`total_snapshots` 0 in Host Availability, no uptime in Hosts by OS). The rows stay (they say which hosts were asked about); a notice says there is no data, and the success banner is not shown.

1. [x] Tests first (red): new `client/src/test/HostReportsNoData.test.tsx`.
2. [x] New `client/src/components/reports/NoRecordedDataNotice.tsx`; use it in `HostAvailabilityReportTable.tsx` and `ExtraReports.tsx` (Hosts by OS); `ReportsPage.tsx` skips the success banner when nothing was recorded.
3. [x] Spec: `spec files/Frontend_Modules_and_Routes.md` (Reports) and `Implementation_Status.md`.
4. [ ] Final gates and pull request.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written; branch from origin/main 1a6142c2 | none | n/a |
| 1 | Tests first: `HostReportsNoData.test.tsx`; 3 of 6 fail on main's source (the 3 no-data cases), 3 controls pass | `npx vitest run src/test/HostReportsNoData.test.tsx` | red as expected |
| 2 | `NoRecordedDataNotice.tsx`; used in the host table and Hosts by OS; page skips the success banner when nothing was recorded | same, plus `tsc -b`, `ServiceReports.test.tsx`, lint | 6 passed; 16 passed together; tsc clean; lint 0 errors, 33 warnings (same as main) |
| 3 | Specs (`Frontend_Modules_and_Routes.md`, `Implementation_Status.md`); full vitest | `npx vitest run` | 79 files, 1016 tests passed |

## State for the next session

- Last check run (exact command): `cd client && npx vitest run`
- Result (first failing lines, or "green"): green (1016 passed)
- Hypothesis: nothing open; remaining work is the docs gate on an LF export and opening the draft PR.
- Next action: run `qa_coverage.py check` and the docs link check on an LF export of this branch, then open the draft PR with `Closes #229`.

## Decisions and notes

- Rows are kept (not hidden) when nothing was recorded, so the user still sees which hosts were asked about; the notice and the missing success banner are the fix.
- This branch is independent of #228 (PR #235), but both touch `HostAvailabilityReportTable.tsx` and `ExtraReports.tsx`; whichever merges second may need a small conflict fix.
- Live verification on the lab is out of scope here (needs a person to deploy).
