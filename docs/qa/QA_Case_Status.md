# Derived black-box case status

Generated from the module catalog; do not hand-edit.
This is a source/result-conflict view, not a new execution or current-build certification.
Catalog results include human manual confirmations and report-attributed outcomes. Historical reports retain their original executors.
E2E without a detailed Result field is pending/unrecorded, not proof it was never attempted.
Accepted evidence and new execution totals must be reported separately.

Source SHA-256: `61c352f34706d0e2f03966b45a6a9158130201ebeacbe4f138b1af78b3519758`.
Cases: 231 TC plus 8 E2E.
Regenerate: `python3 -I scripts/render_qa_case_tables.py --write`.

| Case | Module / phase | Summary result | Detailed result | Eligibility | Historical evidence |
|---|---|---|---|---|---|
| TC-AUTH-05 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-06 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-07 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-01 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-02 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-03 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-04 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-09 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-12 | AUTH / 1 | PASS | PASS | pass | No reviewed mapping |
| TC-ROL-01 | ROL / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ROL-02 | ROL / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ROL-03 | ROL / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-01 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-02 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-03 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-08 | AUTH / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-04 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-05 | ACC / 2 | FAIL | FAIL - the suspended account successfully signed out but it didn't have any warning when user session is timed out | fail | No reviewed mapping |
| TC-ACC-06 | ACC / 2 | FAIL | FAIL - the administrator cannot change or reset the other user password | fail | No reviewed mapping |
| TC-ACC-07 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-09 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ACC-10 | ACC / 2 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-191-accounts/REPORT.md) |
| TC-ACC-08 | ACC / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ROL-04 | ROL / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ROL-05 | ROL / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-ROL-06 | ROL / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-10 | AUTH / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-AUTH-11 | AUTH / 2 | PASS | PASS | pass | No reviewed mapping |
| TC-SHL-09 | SHL / 2 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-SHL-04 | SHL / 2 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-SHL-10 | SHL / 2 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DASH-08 | DASH / 3 | PASS | PASS | pass | No reviewed mapping |
| TC-SS-04 | SS / 3 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-01 | HIS / 3 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-07 | PLG / 3 | PASS | PASS | pass | No reviewed mapping |
| TC-NCPA-08 | NCPA / 3 | Not run | Not run | untested | No reviewed mapping |
| TC-RPT-07 | RPT / 3 | PASS | PASS | pass | No reviewed mapping |
| TC-LOG-05 | LOG / 3 | PASS | PASS | pass | No reviewed mapping |
| TC-SHL-06 | SHL / 3 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-NFR-01 | NFR / 3 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-NFR-02 | NFR / 3 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-SET-07 | SET / 4 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-115-inbox-confirmed/REPORT.md) |
| TC-SET-01 | SET / 4 | PASS | PASS | pass | No reviewed mapping |
| TC-SET-02 | SET / 4 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-110-polling-retest/REPORT.md) |
| TC-SET-03 | SET / 4 | PASS | PASS | pass | No reviewed mapping |
| TC-SET-04 | SET / 4 | PASS | PASS | pass | No reviewed mapping |
| TC-SET-05 | SET / 4 | PASS | PASS | pass | No reviewed mapping |
| TC-SET-06 | SET / 4 | PASS | PASS | pass | No reviewed mapping |
| TC-SHL-01 | SHL / 4 | PASS | Not run | needs-decision | retest required: [source report](../test-runs/2026-10-15-issue-116-escalations/REPORT.md) |
| TC-SHL-02 | SHL / 4 | PASS | Not run | needs-decision | retest required: [source report](../test-runs/2026-10-15-issue-116-escalations/REPORT.md) |
| TC-SHL-03 | SHL / 4 | PASS | Not run | needs-decision | retest required: [source report](../test-runs/2026-10-15-issue-116-escalations/REPORT.md) |
| TC-DSC-01 | DSC / 5 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DSC-02 | DSC / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DSC-03 | DSC / 5 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DSC-04 | DSC / 5 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DSC-05 | DSC / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DSC-08 | DSC / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DSC-09 | DSC / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-01 | PLG / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-02 | PLG / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-03 | PLG / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-04 | PLG / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-05 | PLG / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-PLG-06 | PLG / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-01 | DI / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-02 | DI / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-03 | DI / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-04 | DI / 5 | PASS | PASS | pass | No reviewed mapping |
| TC-DASH-01 | DASH / 6 | PASS | PASS (re-check: this case was reworded to match the real cards) | pass | No reviewed mapping |
| TC-DASH-05 | DASH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-DASH-07 | DASH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-NH-01 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-NH-02 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-NH-03 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-NH-04 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-NH-05 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-SS-01 | SS / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-SS-02 | SS / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-SS-03 | SS / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-DX-01 | DX / 6 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DX-02 | DX / 6 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DX-03 | DX / 6 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DX-04 | DX / 6 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DX-05 | DX / 6 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-DX-06 | DX / 6 | PARTIALLY PASS | PARTIALLY PASS (messages accurate; SNMP section disappears after Save, Test and Reset until refresh) | partial | No reviewed mapping |
| TC-DX-07 | DX / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-DX-08 | DX / 6 | Not run | Not run | untested | No reviewed mapping |
| TC-DX-09 | DX / 6 | Not run | Not run | untested | No reviewed mapping |
| TC-DX-10 | DX / 6 | Not run | Not run | untested | No reviewed mapping |
| TC-NH-06 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-NH-07 | NH / 6 | PASS | PASS | pass | No reviewed mapping |
| TC-TOP-01 | TOP / 6 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-117-live-browser/REPORT.md) |
| TC-TOP-02 | TOP / 6 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-117-live-browser/REPORT.md) |
| TC-TOP-03 | TOP / 6 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-117-live-browser/REPORT.md) |
| TC-TOP-04 | TOP / 6 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-117-live-browser/REPORT.md) |
| TC-TOP-05 | TOP / 6 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-117-live-browser/REPORT.md) |
| TC-TOP-06 | TOP / 6 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-117-manual-topology/REPORT.md) |
| TC-DI-05 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-06 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-07 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-08 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-09 | DI / 7 | FAIL - Notes in the step-by-step | FAIL - Using network discovery again assigns the device with a port 80 named into a different service name to a new record in network discovery, and saying that the old record has an unknown IP address. The same device is said to have a different SSH key despite being the same device, this needs to be investigated, the device used is 10.77.0.8. | fail | No reviewed mapping |
| TC-DI-11 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-12 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-13 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DASH-02 | DASH / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-14 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-15 | DI / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DI-16 | DI / 7 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-164-identity-review/REPORT.md); supporting: [source report](../test-runs/2026-10-15-issue-164-final-refresh/REPORT.md) |
| TC-DI-17 | DI / 7 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-164-identity-review/REPORT.md); supporting: [source report](../test-runs/2026-10-15-issue-164-final-refresh/REPORT.md) |
| TC-DI-18 | DI / 7 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-164-identity-review/REPORT.md); supporting: [source report](../test-runs/2026-10-15-issue-164-final-refresh/REPORT.md) |
| TC-DI-19 | DI / 7 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-164-identity-review/REPORT.md); supporting: [source report](../test-runs/2026-10-15-issue-164-final-refresh/REPORT.md) |
| TC-DSC-06 | DSC / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DSC-07 | DSC / 7 | PASS | PASS | pass | No reviewed mapping |
| TC-DASH-03 | DASH / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-ACK-01 | ACK / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-ACK-02 | ACK / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-ACK-03 | ACK / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-ACK-04 | ACK / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-ACK-05 | ACK / 8 | FAIL - see details in step-by-step | FAIL - there is no prompt to ask you if you want to remove the acknowledge for the alert | fail | No reviewed mapping |
| TC-ACK-06 | ACK / 8 | FAIL - See note | There is no filter in acknowledgement/ active alerts | needs-decision | No reviewed mapping |
| TC-ACK-07 | ACK / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-ACK-08 | ACK / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-DASH-04 | DASH / 8 | PASS | PASS (re-check: wording changed) | pass | No reviewed mapping |
| TC-HIS-02 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-03 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-04 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-05 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-06 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-07 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-HIS-08 | HIS / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-SHL-07 | SHL / 8 | PASS | Not run | needs-decision | partial historical coverage: [source report](../test-runs/2026-10-18-issue-153-failure-escalation/REPORT.md) |
| TC-SHL-08 | SHL / 8 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-MNT-01 | MNT / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-MNT-02 | MNT / 8 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md) |
| TC-MNT-03 | MNT / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-MNT-04 | MNT / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-MNT-05 | MNT / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-MNT-06 | MNT / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-MNT-07 | MNT / 8 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md) |
| TC-MNT-09 | MNT / 8 | PASS | PASS | pass | No reviewed mapping |
| TC-MNT-10 | MNT / 8 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md) |
| TC-NCPA-01 | NCPA / 9 | Not run | Not run | untested | No reviewed mapping |
| TC-NCPA-02 | NCPA / 9 | Not run | Not run | untested | No reviewed mapping |
| TC-NCPA-03 | NCPA / 9 | Not run | Not run | untested | No reviewed mapping |
| TC-NCPA-04 | NCPA / 9 | Not run | Not run | untested | No reviewed mapping |
| TC-NCPA-05 | NCPA / 9 | Not run | Not run | untested | No reviewed mapping |
| TC-NCPA-06 | NCPA / 9 | Not run | Not run | untested | retest required: [source report](../test-runs/2026-10-15-issue-129-finish-journeys/REPORT.md) |
| TC-NCPA-07 | NCPA / 9 | Not run | Not run | untested | retest required: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-NCPA-09 | NCPA / 9 | Not run | Not run | untested | partial historical coverage: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-NCPA-10 | NCPA / 9 | Not run | Not run | untested | partial historical coverage: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-NCPA-11 | NCPA / 9 | Not run | Not run | untested | partial historical coverage: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-DI-10 | DI / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-129-finish-journeys/REPORT.md) |
| TC-DASH-09 | DASH / 9 | PASS | PASS | pass | No reviewed mapping |
| TC-SS-05 | SS / 9 | PASS | PASS | pass | No reviewed mapping |
| TC-REM-02 | REM / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-REM-01 | REM / 9 | PASS | PASS | pass | No reviewed mapping |
| TC-REM-04 | REM / 9 | PARTIALLY PASS | PARTIALLY PASS - | partial | retest required: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-REM-03 | REM / 9 | PASS | PASS | pass | No reviewed mapping |
| TC-REM-05 | REM / 9 | PASS | PASS | pass | No reviewed mapping |
| TC-REM-07 | REM / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) |
| TC-REM-09 | REM / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) |
| TC-REM-06 | REM / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) |
| TC-REM-08 | REM / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) |
| TC-REM-10 | REM / 9 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) |
| TC-RPT-01 | RPT / 10 | FAIL (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded) | FAIL (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded) | fail | retest required: [source report](../test-runs/2026-10-17-issue-134-reports-documentation/REPORT.md) |
| TC-RPT-02 | RPT / 10 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-134-reports-documentation/REPORT.md) |
| TC-RPT-03 | RPT / 10 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-134-reports-documentation/REPORT.md) |
| TC-RPT-04 | RPT / 10 | PASS | PASS | pass | No reviewed mapping |
| TC-RPT-05 | RPT / 10 | PASS | PASS | pass | No reviewed mapping |
| TC-RPT-06 | RPT / 10 | PARTIALLY PASS (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded) | PARTIALLY PASS (initial main-lab run; temporary scratch retest PASS; post-merge confirmation not recorded) | partial | No reviewed mapping |
| TC-LOG-01 | LOG / 10 | PASS | PASS | pass | partial historical coverage: [source report](../test-runs/2026-10-15-issue-124-storage-logs/REPORT.md) |
| TC-LOG-02 | LOG / 10 | PASS | PASS | pass | No reviewed mapping |
| TC-LOG-03 | LOG / 10 | PASS | PASS | pass | partial historical coverage: [source report](../test-runs/2026-10-15-issue-124-storage-logs/REPORT.md) |
| TC-LOG-04 | LOG / 10 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-124-storage-logs/REPORT.md) |
| TC-SHL-05 | SHL / 10 | PASS | Not run | needs-decision | retest required: [source report](../test-runs/2026-10-15-issue-124-storage-logs/REPORT.md) |
| TC-DASH-06 | DASH / 11 | FAIL - While Nagios is down, there is no indication that Nagios is not running and not polling, this was confirmed when trying to modify a Nagios config but can't save. | FAIL | fail | No reviewed mapping |
| TC-MNT-08 | MNT / 11 | PASS | PASS | pass | No reviewed mapping |
| TC-SET-08 | SET / 11 | PASS | PASS | pass | No reviewed mapping |
| TC-SET-09 | SET / 11 | PASS | PASS | pass | No reviewed mapping |
| TC-NFR-03 | NFR / 12 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-NFR-04 | NFR / 12 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-NFR-05 | NFR / 12 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-NFR-06 | NFR / 12 | Not run | Not run | untested | No reviewed mapping |
| TC-NFR-07 | NFR / 12 | FAIL - returns to login, other result is, data is showing but plaintext only without UI | Not run | needs-decision | No reviewed mapping |
| TC-NFR-08 | NFR / 12 | FAIL - returns to login, other result is, data is showing but plaintext only without UI | Not run | needs-decision | No reviewed mapping |
| TC-NFR-09 | NFR / 12 | Not run | Not run | untested | No reviewed mapping |
| TC-NFR-10 | NFR / 12 | PASS | Not run | needs-decision | No reviewed mapping |
| TC-NFR-11 | NFR / 12 | Not run | Not run | untested | No reviewed mapping |
| TC-EDG-01 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-02 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-03 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-04 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-05 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-06 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-07 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-08 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-09 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-10 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-11 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-12 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-13 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-14 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-15 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-16 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-17 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-EDG-18 | EDG / 13 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-01 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-02 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-03 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-04 | SEQ / 14 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-15-issue-122-maintenance-windows/REPORT.md) |
| TC-SEQ-05 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-06 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-07 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-08 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-10 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-11 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-12 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-13 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-14 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-15 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-16 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-18 | SEQ / 14 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) |
| TC-SEQ-19 | SEQ / 14 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-16-issue-121-local-restart/REPORT.md) |
| TC-SEQ-20 | SEQ / 14 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-155-remediation-safety/REPORT.md) |
| TC-SEQ-21 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-22 | SEQ / 14 | PASS | PASS | pass | retest required: [source report](../test-runs/2026-10-17-issue-182-remote-restart/REPORT.md) |
| TC-SEQ-23 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-24 | SEQ / 14 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-09 | SEQ / 15 | PASS | PASS | pass | No reviewed mapping |
| TC-SEQ-17 | SEQ / 15 | PASS | PASS | pass | No reviewed mapping |
| E2E-01 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-02 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-03 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-04 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-05 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-06 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-07 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
| E2E-08 | E2E / 15 | No Result column / no recorded verdict | PASS (historical checklist) | pass | No reviewed mapping |
