# Test run: module-20-21-records

| | |
|---|---|
| Date | 2026-10-19 (records consolidated; the tests themselves were run earlier, dates unknown) |
| Commit tested | Checkout `4b6063d7`. The deployed application revision when the cases were run is unknown. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Modules 20 and 21 |
| Tester / executor mode | Human manual. The tester ran the cases earlier in the lab and confirmed the outcomes in chat on 2026-10-19. Claude (AI) recorded the tester's statements and did not run any case. |
| Catalog revision and SHA-256 | Checkout `4b6063d7` with the Module 20 and 21 result edits; catalog SHA-256 `88eccc258964bc81a4bf0261cc9e43e6ff7d7c1fe0a88f96a3890702abd36948` |
| Queue / set / session / batch | None. This is a records consolidation, not a live run. |
| Deployed application / installer revision | Unknown. Not verified. |
| Baseline / preflight / restoration | Not applicable to this consolidation; no case was executed by this report. |
| Start / end / time zone | Not recorded. |
| Environment | Not recorded. |
| Raw evidence | None supplied. Nothing is committed. |

## Result

**Overall: Tester-reported.** The tester confirmed that 19 cases passed and that 2 failed. No new execution was performed, and the earlier human results in the summary tables were not changed. The detail `Result` lines that said "Not run" are aligned with the summary tables or the tester's statement, so the summary/detail conflicts on these cases are resolved.

Totals (unique TC): Pass 19, Fail 2, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; link reviewed mappings separately.
Attempts and setup operations are not extra unique cases. Historical credit is not a new execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-SHL-01 to TC-SHL-10 | Pass | Summary table said PASS; detail line said Not run. Tester confirmed all ten passed. No per-item values or evidence file. | |
| TC-NFR-01 to TC-NFR-05 | Pass | Summary table said PASS; detail line said Not run. Tester confirmed all five passed. No per-item values or evidence file. | |
| TC-NFR-10 | Pass | Summary table said PASS; detail line said Not run. Tester confirmed it passed. The measured alert delay was not supplied (the case asks for the numbers). | |
| TC-NFR-06 | Pass | Previously Not run. Tester said it was already run and passed. No per-item values or evidence file. | |
| TC-NFR-09 | Pass | Previously Not run. Tester said it was already run and passed. The five reload times were not supplied. | |
| TC-NFR-11 | Pass | Previously Not run. Tester said it was already run and passed. The four-hour sample data was not supplied. | |
| TC-NFR-07 | Fail | The original summary text, kept as written, reads "returns to login, other result is, data is showing but plaintext only without UI". The tester confirmed it failed. The detail line is now FAIL to match. The observation is not clear enough to reproduce; no timings were recorded. | [#220](https://github.com/esfen14/Pinpoint/issues/220) (open, clarify the conflicting results) |
| TC-NFR-08 | Fail | Same original summary text as TC-NFR-07. The tester confirmed it failed. The detail line is now FAIL to match. No timings were recorded. | [#221](https://github.com/esfen14/Pinpoint/issues/221) (open, clarify the conflicting results) |

## Expected-item observations and restoration

Per-item observations were not supplied for any case, so none are invented here. A case counts as Pass here only because the tester confirmed it; an auditor cannot re-verify any expected item from this report.

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-SHL-01 to 10, TC-NFR-01 to 06, 09, 10, 11 | All expected items | Not recorded; tester confirmed the case passed | Pass (tester-reported) | None | Not recorded |
| TC-NFR-07, TC-NFR-08 | Median start-up time 10 s or less; 9 of 10 availability responses 5 s or less | Not recorded; tester reported FAIL with the note above | Fail (tester-reported) | None | Not recorded |

## Deviations from the plan

- Nothing was run for this report. It consolidates earlier manual results and one more tester confirmation.
- TC-NFR-07 and TC-NFR-08 stay failed; the open clarification issues #220 and #221 are linked. The product defect behind them, if any, is not yet described well enough to file as a `qa-found` bug.
- The detail lines of 16 cases that conflicted with their summary were changed from Not run to Pass. The original summary values were not altered.

## Follow-up

- Defects found: none newly filed. #220 and #221 need a clear observation (start-up and availability times, and what "returns to login" and "plaintext without UI" mean) before a product defect can be filed.
- Cases to repeat in the next run: TC-NFR-07 and TC-NFR-08 with recorded times; any case where a reviewer wants per-item evidence.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
