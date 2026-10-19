# Test run: module-19-device-extras

| | |
|---|---|
| Date | 2026-10-19 |
| Commit tested | Checkout `44471f7c` plus the uncommitted Module 18 result changes. The deployed application revision is unknown. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Module 19 TC-DX-06 and TC-DX-07 |
| Tester / executor mode | Human manual. The tester ran the case in the lab app. Claude (AI) wrote the walkthrough, read the UI source to state the expected messages, and recorded the tester's reported results; it did not drive the browser. |
| Catalog revision and SHA-256 | Checkout `44471f7c` with uncommitted changes; catalog SHA-256 `99d678ed060786b505edcfb6afe3ec6637cf6db9232d9667d95d052a188ec945` (after the Module 18 result edits, before the TC-DX-06 result edit) |
| Queue / set / session / batch | No prepared queue for this case (ad hoc, human manual). Session 1. The Module 18 draft queue was never started. |
| Deployed application / installer revision | Unknown. Not verified; installer revision not checked. |
| Baseline / preflight / restoration | No `vmlab preflight`. Restoration of the original SNMP settings was not confirmed by the tester. |
| Start / end / time zone | Not recorded. |
| Environment | Not recorded. |
| Raw evidence | None supplied. Nothing is committed. |

## Result

**Overall: Partially pass.** TC-DX-06 was run by hand. The tester reported that the UI messages are accurate, and that pressing the form's buttons (Save, Test, Reset to defaults) makes the whole SNMP section disappear until the drawer is refreshed. TC-DX-07 was also run and reported PASS. TC-DX-08 to TC-DX-10 were not run.

Totals (unique TC): Pass 1, Fail 0, Partial 1, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; link reviewed mappings separately.
Attempts and setup operations are not extra unique cases. Historical credit is not a new execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-DX-06 | Partially pass | Tester reported the UI messages were accurate (they match `snmpForm.ts` and `DeviceSnmpSection.tsx`). Tester also reported that after pressing the buttons the SNMP section is removed until the page is refreshed. Per-step values (fields per version, password display, test result text, non-editing user's view) were not supplied. Not confirmed: that every step 1 to 5 was completed. No evidence file. | Not filed. A `qa-found` issue is pending; no existing issue found by searching "SNMP section" and "TC-DX-06". |
| TC-DX-07 | Pass | Tester reported all expected items were seen and the case passed: Interfaces only on the SNMP device, Refresh reading the list, and the Monitor tick saved and shown in Interface Bandwidth. The tester said it had already been tested before this walkthrough. Per-item values, timings and restoration of the tick were not supplied. No evidence file. | |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-DX-06 | E1 fields follow version and security level; a missing required field is blocked | Messages reported accurate; field-by-field values not recorded | Not independently observed; tester reported messages accurate | None | n/a |
| TC-DX-06 | E2 a saved password shows only as "Saved"; blank box keeps it; **Remove saved** deletes it | Not recorded. The form vanished after the buttons, so the repeat-save steps could only be done after a refresh | Partial | None | Not confirmed |
| TC-DX-06 | E3 changing and testing need `system.hosts.edit`; success shows "The device answered:" | Not recorded | Not observed | None | n/a |
| TC-DX-06 | Observed violation: SNMP section disappears after Save, Test and Reset until refresh | Reported by the tester for the buttons ("all" of them) | Fail (defect) | None | n/a |
| TC-DX-07 | E1 Interfaces only on the SNMP device, with name, index, speed, status | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DX-07 | E2 Refresh reads the list from the device | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DX-07 | E3 Monitor tick saved; interface appears in Interface Bandwidth | Not recorded; tester confirmed | Pass | None | Tick restoration not confirmed |

## Source analysis (not an execution)

Reading the code explains the Save and Reset cases: `PUT` and `DELETE` in `server/app/api/system/device_plugin_variables.py` return the settings without `in_use`, the client maps the missing value to null (`client/src/lib/devicePluginVariablesApi.ts`), and `DeviceSnmpSection.tsx` returns null when `in_use` is not true. The code does not explain a disappearance after Test, which never reloads the saved settings. This is a hypothesis from reading, not a reproduction.

## Deviations from the plan

- Only TC-DX-06 and TC-DX-07 were run. TC-DX-08 to TC-DX-10 remain Not run.
- Steps could only continue after refreshing the drawer.
- No repeat attempt was made and no `qa-found` issue has been filed.

## Follow-up

- Defects found: SNMP section disappears after Save, Test and Reset until refresh. Needs a `qa-found` issue and a second attempt on a clean state.
- Cases to repeat in the next run: TC-DX-06 after a merged fix, with per-step evidence; TC-DX-08 to TC-DX-10 untested.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
