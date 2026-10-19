# Test run: module-20-21-records

| | |
|---|---|
| Date | 2026-10-19 (records consolidated; the tests themselves were run earlier, dates unknown) |
| Commit tested | Checkout `4b6063d7`. The deployed application revision when the cases were run is unknown. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Modules 20 and 21 |
| Tester / executor mode | Human manual. The tester ran the cases earlier in the lab and confirmed the outcomes in chat on 2026-10-19. Claude (AI) recorded the tester's statements and did not run any case. |
| Catalog revision and SHA-256 | Checkout `4b6063d7` with the Module 20 and 21 result edits; catalog SHA-256 `87592b3bbb903a70df3be5954c0765a157a197572b6660a1ed2cafba8701fa19` |
| Queue / set / session / batch | None. This is a records consolidation, not a live run. |
| Deployed application / installer revision | Unknown. Not verified. |
| Baseline / preflight / restoration | Not applicable to this consolidation; no case was executed by this report. |
| Start / end / time zone | Not recorded. |
| Environment | Not recorded. |
| Raw evidence | None supplied. Nothing is committed. |

## Result

**Overall: Tester-reported.** The tester confirmed that 20 cases passed (including later retests of TC-NFR-07 and TC-NFR-08) and that 1 failed (TC-NFR-06). No new execution was performed, and the earlier human results in the summary tables were not changed. The detail `Result` lines that said "Not run" are aligned with the summary tables or the tester's statement, so the summary/detail conflicts on these cases are resolved.

Totals (unique TC): Pass 20, Fail 1, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; link reviewed mappings separately.
Attempts and setup operations are not extra unique cases. Historical credit is not a new execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-SHL-01 to TC-SHL-10 | Pass | Summary table said PASS; detail line said Not run. Tester confirmed all ten passed. No per-item values or evidence file. | |
| TC-NFR-01 to TC-NFR-05 | Pass | Summary table said PASS; detail line said Not run. Tester confirmed all five passed. No per-item values or evidence file. | |
| TC-NFR-10 | Pass | Summary table said PASS; detail line said Not run. Tester reported the alert appeared after 1 s in one run and 2 s in the other, both within 3 s. The Nagios and alert times themselves, and whether the host was restored, were not supplied. No evidence file. | |
| TC-NFR-06 | Fail | Previously Not run, then reported as passed. The tester then confirmed that Overview shows no Retry button when its data cannot be loaded, so the case fails. The tester did not say whether the host drawer and Ports show Retry; unconfirmed. Code reading agrees: `DashboardPage.tsx` renders only the error text. No error text, screenshot or evidence file. | [#245](https://github.com/esfen14/Pinpoint/issues/245) |
| TC-NFR-09 | Pass | Previously Not run. Tester reported five reload times of 2, 2, 4, 3 and 4 seconds (sorted 2, 2, 3, 4, 4; the middle is 3 s, which meets 3 s or less). 15 hosts were reporting and the cache was disabled. No evidence file. | |
| TC-NFR-11 | Pass | Previously Not run. Tester reported it passed with all expected outputs and gave used-memory figures of 2% at the start, 7% lowest and 16% at the end (the tester clarified they are used memory). Used memory rising from 2% to 16% means free memory went from about 98% to about 84%, a fall of about 14%, which is under the 30% limit; this is derived from the tester's figures, not measured separately. How the 7% "lowest" fits between the start and end values was not explained. Start and end times, process numbers, and the restart, 500-error and missed-sample checks were reported only as "all expected outputs". No evidence file. | |
| TC-NFR-07 | Pass (retest) | Original summary text, kept as written: "returns to login, other result is, data is showing but plaintext only without UI" (FAIL). The tester later reported a retest that passed with all its expected output (median of three start-up times 10 s or less). The catalog keeps the original FAIL verdict with the retest recorded beside it. The three times, the build of the retest and what had changed were not supplied. | [#220](https://github.com/esfen14/Pinpoint/issues/220) (open; needs a comment with the retest and then a decision to close) |
| TC-NFR-08 | Pass (retest) | Original summary text, kept as written: "returns to login, other result is, data is showing but plaintext only without UI" (FAIL). The tester later reported a retest that PASSED. The catalog keeps the original FAIL verdict with the retest recorded beside it. No timings (9 of 10 responses at 5 s or less for each endpoint) were supplied, and the build of the retest is unknown. | [#221](https://github.com/esfen14/Pinpoint/issues/221) (open; needs a comment with the retest and then a decision to close) |

## Expected-item observations and restoration

Per-item observations were not supplied for most cases, so none are invented here. Where the tester gave numbers (TC-NFR-09, 10, 11), they are recorded as given. A case counts as Pass here only because the tester confirmed it; an auditor cannot re-verify any expected item from this report.

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-SHL-01 to 10, TC-NFR-01 to 05 | All expected items | Not recorded; tester confirmed the case passed | Pass (tester-reported) | None | Not recorded |
| TC-NFR-09 | E1 median of five reload times is 3 s or less | 2, 2, 4, 3, 4 s; median 3 s; 15 hosts reporting; cache disabled | Pass (tester-reported) | None | n/a (read-only) |
| TC-NFR-10 | E1 alert appears within 3 s of the Nagios state change, in both runs | 1 s and 2 s | Pass (tester-reported) | None | Host restoration not recorded |
| TC-NFR-11 | E1 no restart, no error 500, API answered at every sample, new status data hourly | Tester: all expected outputs | Pass (tester-reported) | None | Not recorded |
| TC-NFR-11 | E2 free memory did not fall by more than 30% without recovering | Used memory 2% at the start, 7% lowest, 16% at the end (tester: used memory); free memory about 98% to about 84%, a fall of about 14% (derived) | Pass (tester-reported) | None | n/a |
| TC-NFR-06 | Each part shows an error with Retry; Retry loads the data after the service is back | Overview shows no Retry (tester) | Fail (tester-reported) | None | Service restart not recorded |
| TC-NFR-07 | Median start-up time 10 s or less | Times not recorded; original FAIL, later retest reported PASS with all expected output | Pass on retest (tester-reported) | None | Not recorded |
| TC-NFR-08 | 9 of 10 availability responses 5 s or less for each endpoint | Not recorded; original FAIL, later retest reported PASS | Pass on retest (tester-reported) | None | Not recorded |

## Deviations from the plan

- Nothing was run for this report. It consolidates earlier manual results and one more tester confirmation.
- TC-NFR-06 was first recorded as Pass and then corrected to Fail after the tester confirmed Overview has no Retry.
- TC-NFR-07 and TC-NFR-08 failed originally and passed on later retests; the open clarification issues #220 and #221 are linked. The original failures were never described well enough to file as `qa-found` bugs, and both retests passed.
- The detail lines of 16 cases that conflicted with their summary were changed from Not run to Pass. The original summary values were not altered.

## Follow-up

- Defects found: TC-NFR-06 (Overview has no Retry), filed as [#245](https://github.com/esfen14/Pinpoint/issues/245). #220 and #221 need a clear observation (start-up and availability times, and what "returns to login" and "plaintext without UI" mean) before a product defect can be filed.
- Cases to repeat in the next run: TC-NFR-06 second attempt; TC-NFR-07 and TC-NFR-08 with recorded times; any case where a reviewer wants per-item evidence.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
