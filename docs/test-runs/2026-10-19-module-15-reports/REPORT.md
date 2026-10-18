# Test run: module-15-reports

| | |
|---|---|
| Date | 2026-10-19 (tester's local date; the lab ran the cases on 2026-10-18 UTC, about 16:25 to 16:45) |
| Commit tested | The lab runs `43f0df1`. The checkout used for this report is `0c7d7567`. Pull request #217 ("reports alignment") was merged into `main` after this run and reverted shortly afterwards (#227); the Reports code on `main` is again the code the lab runs, so these results describe the code on `main`. See the [retest](../2026-10-19-module-15-reports-retest/REPORT.md) of the two failing cases on a build with the fixes. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Module 15 TC-RPT-01 and TC-RPT-06 |
| Tester / executor mode | Mixed. AI-assisted (Claude) drove the browser UI with a Playwright script on installed Chrome and cross-checked with the API. The lab owner approved the plan and the filing of the defects. |
| Catalog revision and SHA-256 | The Module 15 section is byte-identical at `65a5862c` and at `0c7d7567` (`git diff` of the catalog between them is empty). Whole-file SHA-256 of the catalog as checked out on Windows at `65a5862c`: `ec2b1c3f3b98f73da9b0f5d6656d1565b1405af97a58b2fcc8fe7481fbe5af71`; the worktree for this report hashes differently (`d9374c41d7f4e5304c3475735d765ad66cb4352cc9745f76e96d78c4de0e398f`) because of line-ending conversion, not content. |
| Queue / set / session / batch | No prepared queue (ad hoc run approved by the lab owner in chat). Session 1, one module per branch: `qa-run-module-15-reports`. |
| Deployed application / installer revision | Application `43f0df1` (git HEAD on the appliance). Installer revision not checked. |
| Baseline / preflight / restoration | Both cases are read-only (running reports and reading Device Inventory). Nothing on the lab was created or changed, so there is nothing to restore. |
| Start / end / time zone | 2026-10-18 16:25 to 16:45 UTC. Appliance in UTC; browser display time zone UTC+08:00. |
| Environment | Ubuntu 22.04.5 lab appliance reached over Tailscale; Nagios Core 4.5.11. The lab was installed on 2026-10-17. |
| Raw evidence | Run scratch folder on the tester machine. Not committed. |

## Result

**Overall: Fail.** TC-RPT-01 failed and TC-RPT-06 passed only in part. The other five Module 15 cases (TC-RPT-02, 03, 04, 05, 07) already carry a human PASS and were not run, as agreed with the lab owner.

Totals (unique TC): Pass 0, Fail 1, Partial 1, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
Attempts and setup operations are not extra unique cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-RPT-01 | Fail | Host Availability, Last 24 hours, run twice with identical results. All 13 rows show state `Unknown`; the summary cards read Total 13, Up 0, Down 0, while Device Inventory shows 12 Up and 2 Down. Last Check and Last State Change are `—` on all 13 rows. The report has 13 rows, Device Inventory has 9 hosts marked Monitored: the 4 extra rows are `dev-255061`, `dev-2b4118` and `dev-3ffc88` (state Missing, not monitored) and Nagios's own `localhost`. All 9 monitored hosts are present. Uptime % values are between 0 and 100. | [#228](https://github.com/esfen14/Pinpoint/issues/228) |
| TC-RPT-06 | Partially Pass | A custom range before the install (2026-09-01 to 2026-09-30) gave no error and no blank page on any of the six tabs. Alerts and Notifications show "No data in this period"; Network Services and Device Services show "No recorded data: …" notes. Host Availability and Hosts by OS show no no-data message: 13 `Unknown` rows with `—` and the banner "Report generated successfully." | [#229](https://github.com/esfen14/Pinpoint/issues/229) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-RPT-01, attempt 1 and repeat | E1 one row per monitored host with state, Uptime % and last check | State `Unknown` and last check empty on 13 of 13 rows | Fail | scratch `rp1_report.png`; API output | None needed (read-only) |
| TC-RPT-01, attempt 1 and repeat | E2 every uptime between 0 and 100 | 0 to 100 on all rows | Pass | API output | |
| TC-RPT-01, attempt 1 and repeat | E3 row count equals monitored hosts in Device Inventory | 13 rows against 9 monitored hosts | Fail | scratch `rp1_inventory.png`; API lookup | |
| TC-RPT-06 | E1 a "No data in this period" style message shows | Shown on Alerts and Notifications; a no-data note on Network Services and Device Services; not shown on Host Availability and Hosts by OS | Partially observed | scratch `rp6_hostavail.png` | None needed |
| TC-RPT-06 | E2 not an error or a blank page | No error and no blank page on any tab | Pass | scratch `rp6_oneday.png` | |

Timing: no elapsed time was involved. The custom range uses date inputs; the 24-hour window is relative to the time of the run.

## Deviations from the plan

- Only TC-RPT-01 and TC-RPT-06 were run, as agreed; the already-passed cases were not rechecked and no Staff user was created.
- For TC-RPT-06 the step does not name a tab; all six tabs were run, and a start-after-end range and a one-day range were added as extra checks. Start after end shows "end_date must be on or after start_date" (HTTP 400) and leaves the previous table on screen.
- The Device Inventory count was read from the Monitoring column (9 Monitored) and cross-checked against the host lookup API (9 monitored); the inventory also lists 5 older Nagios entries that are not monitored devices (`localhost`, `pp153-dummy`, `pp153b-dummy`, and two entries for dummy devices removed earlier in this session).
- PR #217 was merged into `main` and then reverted (#227) while this module was being tested. It was never deployed to the lab and was not tested here.

## Follow-up

- Defects found: #228 (TC-RPT-01) and #229 (TC-RPT-06), both filed with the label `qa-found` against `43f0df1`.
- Cases to repeat in the next run: TC-RPT-01 and TC-RPT-06, on a build with fixes for #228 and #229. Done: see the [retest](../2026-10-19-module-15-reports-retest/REPORT.md).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
