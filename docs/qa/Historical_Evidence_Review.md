# Historical black-box evidence review

Cutoff candidate: October 15, 2026 (Asia/Manila); still provisional. This inventory
is a dated discovery aid, not a result ledger or a claim that every post-cutoff
report tested a current build. Original reports and human catalog verdicts remain unchanged.

Target reviewed for candidate overlap: `299ab3ba7203c89a3ca5d8fabea42d9e5f239be2`.
Later NCPA registration and remediation changes prevent blanket reuse of the October 17 browser report.
No full-case inherited PASS has been accepted. Six mappings below establish partial
candidate overlap only; they remain queued for missing checks/compatibility decisions.

## Case mappings

| Current case | Attached source run | Reuse decision / remaining coverage |
|---|---|---|
| TC-NCPA-09 | [RR-12 browser report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md#cases) | Partial: Remote settings persistence observed; twenty/21-service boundary and untrusted-device refusal are not all established by this report. |
| TC-NCPA-10 | [RR-12 browser report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md#cases) | Partial: Real settings Retry was observed after a synthetic load error; opening settings while deployment is running was not established. |
| TC-NCPA-11 | [RR-12 browser report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md#cases) | Partial: Cleanup notice, credential clearing and retained list are described; exact remote-restart-enabled prerequisite and current-build dependencies require review. |
| TC-REM-02 | [RR-12 browser report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md#cases) | Partial: Creation/edit/persistence of remote actions observed; Record only setup and cooldown boundary are not fully established. |
| TC-REM-04 | [RR-12 browser report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md#cases) | Partial: Read-only UI and real settings PUT/action creation 403 observed. Historical partial human entry and newer remediation changes need compatibility review. |
| TC-REM-10 | [RR-12 browser report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md#cases) | Partial: Local and remote unit fields were exercised; all action-type transitions and field clearing are not established. |

The [review records](historical-evidence-review.json) carry case/report hashes and
original executor/version attribution. Empty covered-item maps deliberately confer
no full-case credit. Accepting a case needs explicit item-level coverage, actual
execution version/date, unchanged requirements, environment/source/dependency impact
review and cutoff decision. Partial evidence may reduce a later reviewed subset;
it cannot satisfy the whole case or create an E2E result from separate module checks.

## Dated report candidates

41 reports found by directory date. Actual execution date/revision must be read
from each report before reuse. Missing raw files or revision detail limits acceptance.
The [machine inventory](historical-report-inventory.json) includes content hashes.

| Directory date | Attached report | Review state |
|---|---|---|
| 2026-10-15 | [Test run: issue-110-polling](../test-runs/2026-10-15-issue-110-polling/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-110-polling-retest](../test-runs/2026-10-15-issue-110-polling-retest/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-115-inbox-confirmed](../test-runs/2026-10-15-issue-115-inbox-confirmed/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-115-starttls-docker](../test-runs/2026-10-15-issue-115-starttls-docker/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-115-starttls-preflight](../test-runs/2026-10-15-issue-115-starttls-preflight/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-116-escalations](../test-runs/2026-10-15-issue-116-escalations/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-117-live-browser](../test-runs/2026-10-15-issue-117-live-browser/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-117-main-sync](../test-runs/2026-10-15-issue-117-main-sync/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-117-manual-topology](../test-runs/2026-10-15-issue-117-manual-topology/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-120-event-handler](../test-runs/2026-10-15-issue-120-event-handler/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-120-service-and-spool](../test-runs/2026-10-15-issue-120-service-and-spool/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-122-maintenance-windows](../test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-124-storage-logs](../test-runs/2026-10-15-issue-124-storage-logs/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-129 remaining live journeys](../test-runs/2026-10-15-issue-129-finish-journeys/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-129 main Nagios daemon](../test-runs/2026-10-15-issue-129-main-daemon/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-129 main synchronization](../test-runs/2026-10-15-issue-129-main-sync/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-129 polling migration CI repair](../test-runs/2026-10-15-issue-129-polling-ci-repair/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-129 review readiness](../test-runs/2026-10-15-issue-129-review-readiness/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Issue #162: control diagnosis and lost-edit resolution](../test-runs/2026-10-15-issue-162-recovery/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Issue #162: clean lab rebuild and endpoint snapshot restoration](../test-runs/2026-10-15-issue-162-snapshot-rebuild/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-164-final-refresh](../test-runs/2026-10-15-issue-164-final-refresh/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-164-identity-review](../test-runs/2026-10-15-issue-164-identity-review/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-79-inbox-confirmed](../test-runs/2026-10-15-issue-79-inbox-confirmed/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Test run: issue-79-rebuilt-inbox](../test-runs/2026-10-15-issue-79-rebuilt-inbox/REPORT.md) | Unreviewed candidate |
| 2026-10-15 | [Issue #79: VM recipients and browser acceptance](../test-runs/2026-10-15-issue-79-vm-browser/REPORT.md) | Unreviewed candidate |
| 2026-10-16 | [Test run: issue-121-local-restart](../test-runs/2026-10-16-issue-121-local-restart/REPORT.md) | Unreviewed candidate |
| 2026-10-16 | [Test run: issue-121-remote-restart-partial](../test-runs/2026-10-16-issue-121-remote-restart-partial/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue-118 notification dependencies](../test-runs/2026-10-17-issue-118/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue-134-reports-documentation](../test-runs/2026-10-17-issue-134-reports-documentation/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: 2026-10-17-issue-155-remediation-safety](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue-173-parent-notifications](../test-runs/2026-10-17-issue-173-parent-notifications/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Issue #182 Playwright browser walkthrough](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue-182-remote-restart](../test-runs/2026-10-17-issue-182-remote-restart/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue #187 isolated DHCP acceptance](../test-runs/2026-10-17-issue-187-dhcp-acceptance/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue #187 Docker DHCP feasibility](../test-runs/2026-10-17-issue-187-docker-feasibility/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: issue-191-accounts](../test-runs/2026-10-17-issue-191-accounts/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Issue #198: installed service-availability contract probe](../test-runs/2026-10-17-issue-198-contract-probe/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Issue #198: service availability implementation and native comparison](../test-runs/2026-10-17-issue-198-service-availability/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: PR #185 / issue #156 resource forecasts](../test-runs/2026-10-17-pr-185-issue-156/REPORT.md) | Unreviewed candidate |
| 2026-10-17 | [Test run: PR #185 / issue #156 forecast defect retest](../test-runs/2026-10-17-pr-185-issue-156-retest/REPORT.md) | Unreviewed candidate |
| 2026-10-18 | [Test run: issue-153-failure-escalation](../test-runs/2026-10-18-issue-153-failure-escalation/REPORT.md) | Unreviewed candidate |
