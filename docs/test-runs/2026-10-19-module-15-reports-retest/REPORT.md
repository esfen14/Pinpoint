# Test run: module-15-reports-retest

| | |
|---|---|
| Date | 2026-10-19 (tester's local date; the lab ran the cases on 2026-10-18 UTC, about 18:25 to 18:45) |
| Commit tested | A temporary scratch build: `main` at `1a6142c2` plus the fix branches `issue-228-host-current-state` (PR #235) and `issue-229-host-reports-no-data` (PR #236), merged with one manual conflict resolution in `HostAvailabilityReportTable.tsx` and `Implementation_Status.md` (keeping both notices). The lab's own code is `43f0df1`, which equals `main` apart from one test file, so the build differs from the lab only by the two fixes. The scratch build was not pushed. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, TC-RPT-01 and TC-RPT-06 (the two cases that failed or partly passed in the [first Module 15 run](../2026-10-19-module-15-reports/REPORT.md)) |
| Tester / executor mode | Mixed. AI-assisted (Claude) built and deployed the scratch build, drove the browser UI with a Playwright script on installed Chrome, and cross-checked with the API. The lab owner approved the temporary deployment. |
| Catalog revision and SHA-256 | The Module 15 section is unchanged since the first run (see that report). |
| Queue / set / session / batch | No prepared queue (ad hoc retest approved by the lab owner in chat). |
| Deployed application / installer revision | The scratch build described above, deployed temporarily; `report.py` hash `c5b98b9c…` matched the built file. Installer revision not checked. |
| Baseline / preflight / restoration | Before: lab at `43f0df1`, `client/dist` hash `d5ddc89262a2139e`, `report.py` hash `c8995b4ada881760`, no local changes except an untracked `client/.npm/`. A copy of `client/dist` and `report.py` was taken first. After: both restored from that copy; the hashes match the originals, `host_current_status.py` is gone, nginx, gunicorn and Nagios are active, and the app shows the old "Unknown" behaviour again. |
| Start / end / time zone | 2026-10-18 18:20 to 18:45 UTC. Appliance in UTC; browser display time zone UTC+08:00. |
| Environment | Ubuntu 22.04.5 lab appliance reached over Tailscale; nginx serves `client/dist`, gunicorn serves the API; Nagios Core 4.5.11. |
| Raw evidence | Run scratch folder on the tester machine. Not committed. |

## Result

**Overall: Pass.** Both cases behave as the catalog expects on the build with the fixes. This is not a verdict on the code on `main`, which still has the defects until #235 and #236 are merged and deployed.

Totals (unique TC): Pass 2, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
The original Fail and Partially Pass in the first run are kept; this is a new execution, not a correction.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-RPT-01 | Pass | Host Availability, Last 24 hours, run twice with identical results. 9 rows, exactly the 9 hosts the Device Inventory marks Monitored (the three Missing devices and `localhost` are gone). Every row has a real state (8 Up, 1 Down for `gateway`, matching the Inventory), a last check and a last state change. Summary cards: Total 9, Up 8, Down 1, uptime 57.59 %. Every uptime value is between 0 and 100. `current_status` reports available. | [#228](https://github.com/esfen14/Pinpoint/issues/228) |
| TC-RPT-06 | Pass | Custom range 2026-09-01 to 2026-09-30 on all six tabs. Host Availability and Hosts by OS show "No data in this period. Nagios has no recorded history for these hosts in the selected period." Host Availability no longer shows "Report generated successfully." Alerts and Notifications show "No data in this period"; Network Services and Device Services show their "No recorded data: …" note. No tab shows an error or a blank page. A Last 24 hours control shows the success banner and no no-data notice. See the observation below. | [#229](https://github.com/esfen14/Pinpoint/issues/229) |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-RPT-01, attempt 1 and repeat | E1 one row per monitored host with state, Uptime % and last check | 9 of 9 rows with state and last check | Pass | scratch `rp1_report.png`; API output | Lab restored; hashes match |
| TC-RPT-01, attempt 1 and repeat | E2 every uptime between 0 and 100 | 0 to 100 on all rows | Pass | API output | |
| TC-RPT-01, attempt 1 and repeat | E3 row count equals monitored hosts in Device Inventory | 9 rows, 9 monitored, same names | Pass | scratch `rp1_inventory.png`; API lookup | |
| TC-RPT-06 | E1 a "No data in this period" style message shows | Shown on Host Availability, Hosts by OS, Alerts and Notifications; a no-data note on Network Services and Device Services | Pass | scratch `rp6_fixed_hostavail.png`, `rp6_fixed_byos.png` | None needed |
| TC-RPT-06 | E2 not an error or a blank page | No error and no blank page on any tab | Pass | scratch run output | |

## Deviations from the plan

- The tested build was a temporary scratch merge of two unmerged pull requests, deployed to the shared lab for about 15 minutes and then removed, with the lab owner's approval. The frontend was built on the tester machine and copied; the two Python files were copied over; gunicorn was restarted.
- The scratch build is not any commit on `main`; a retest on the merged code is still needed once #235 and #236 are merged and deployed.
- The run happened after the first Module 15 run, so the lab's data had moved on (more history; the earlier dummy devices were already removed).

## Follow-up

- Defects found: none new. #228 and #229 are fixed on the scratch build; they close when their pull requests merge.
- Observation, not filed: with the pre-install range, Network Services shows both "Report generated successfully." and its "No recorded data: …" note. #229 covers only Host Availability and Hosts by OS, and the wording difference between tabs is documented in the Frontend specification.
- Cases to repeat in the next run: none, apart from a confirmation after #235 and #236 are merged and deployed.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
