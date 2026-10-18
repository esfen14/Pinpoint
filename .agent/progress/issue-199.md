# Issue #199: Reports aligned with Nagios Core reporting

Branch: `issue191-reports_alignment` (user-directed; NOT committed or pushed, user finalizes)
Status: in-progress

## Scope update (2026-10-18)
User then asked to do all remaining items. Done in the working tree (uncommitted): contract probe, Reports requirements spec, report_events.py + three routes, alert/notification filters, drawer, analysis views, export context, tests, lab report. Not done: maintenance live check, scale, real export download, PR/CI.

## Scope agreed with user
Phases 1-3 only: Reports spec, backend semantic tests, host/OS snapshot-count removal, shared applied-query controls. No live lab, no new endpoints, no commits/pushes/checkpoints.

## Finish condition
Full list is in the issue (16 items). Delivered this session: snapshot-count removal (item 2), part of item 3. All others remain open.

## Plan
1. [x] Test first: host/OS rows carry explicit duration fields, no total_snapshots (server/tests/unit/test_report_availability.py)
2. [x] Backend: report.py replace total_snapshots; remove dead snapshot code after return in hosts-by-os
3. [x] Frontend: types/report.ts, HostAvailabilityReportTable.tsx duration columns, no Snapshots label
4. [x] Specs: Frontend/Backend_Modules_and_Routes.md, Implementation_Status.md; new Reports requirements spec; route in AGENTS.md
5. [x] Applied-query controls (draft vs applied, Run Report) in ReportsPage.tsx
6. [ ] scripts/verify.sh backend/frontend/docs

## Round log
| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Host/OS rows: explicit duration seconds, dead snapshot code removed; UI columns/exports; draft/applied query | pytest report tests (137), vitest (1011), tsc src | green |
| 1 | Specs updated (Frontend, Backend, Implementation_Status) | scripts/verify.sh docs | fails only at test_qa_transport (Unsafe transport path, unrelated, env) |

## State for the next session
- Last check: verify.sh docs/frontend; frontend tsc fails only on e2e (@playwright/test not installed); docs fails at qa_transport (path resolve).
- Next action: run scripts/verify.sh backend/frontend/docs with PATH including server/venv/bin; fill final numbers in the lab report and PR text; human review. Remaining open: scheduled-maintenance live case, scale, real export downloads.

## Decisions and notes
Remaining phases (interval detail, summary, histogram, live-lab evidence) are out of this session.
