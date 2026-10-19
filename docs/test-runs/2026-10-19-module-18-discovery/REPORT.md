# Test run: module-18-discovery

| | |
|---|---|
| Date | 2026-10-19 |
| Commit tested | Checkout `44471f7c`. The deployed application revision is unknown (see below). |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Module 18 TC-DSC-02 and TC-DSC-05 to TC-DSC-09 |
| Tester / executor mode | Human manual. The tester ran each case in the lab app. Claude (AI) wrote the step-by-step walkthrough and recorded the tester's reported results; it did not drive the browser. |
| Catalog revision and SHA-256 | Checkout `44471f7c`; catalog SHA-256 `2ef796eb541796e43187acd965431e4a40554a9f8b770fbee40a2bab3f7ba10e` |
| Queue / set / session / batch | Draft queue `docs/qa/queues/2026-10-19-module-18-dsc-v1.json`, set `dsc`, owner Elle. The queue was prepared against `44471f7c` and never formally started: the execution cards are empty and no tracking issue exists yet. Session 1. |
| Deployed application / installer revision | Unknown. The tester could not state the deployed revision. Not verified; installer revision not checked. |
| Baseline / preflight / restoration | No `vmlab preflight` was run. The tester was asked to confirm that the configured scan networks were inside `10.77.0.0/28`; the tester's reply did not state the networks. Restoration: the tester answered "yes" when asked whether everything changed (ports, removed network, stopped service) was restored. |
| Start / end / time zone | Not recorded. |
| Environment | Not recorded (OS, Nagios version and database state were not supplied). |
| Raw evidence | None supplied. Nothing is committed. |

## Result

**Overall: Pass (tester-reported).** The tester reported that all six selected cases (TC-DSC-02, 05, 06, 07, 08, 09) passed. The tester gave no per-item observations, timings or screenshots, so the notes below record only the tester's verdict and the expected items the tester was asked to confirm. Sign-off is limited by the unknown deployed revision, the missing preflight and the absence of evidence.

Totals (unique TC): Pass 6, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; link reviewed mappings separately.
Attempts and setup operations are not extra unique cases. Historical credit is not a new execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-DSC-02 | Pass | Tester reported the scan progress and final status behaved as expected: button "Scanning… N%" and disabled, bell in progress then complete, status ended in exactly one final state. The final state value and timings were not recorded. No evidence file. | |
| TC-DSC-05 | Pass | Tester reported port 8080 was absent with `1-1024` and present after adding it, invalid ports `0`, `65536` and `abc` were refused, the Configuration Change log recorded the edits, and the original ports were restored. No evidence file. | |
| TC-DSC-06 | Pass | Tester reported devices of the removed network stayed as they were (or became Missing) and devices of the scanned network did not become "Address unknown". No evidence file. | |
| TC-DSC-07 | Pass | Tester reported the port showed Missing with "Not seen lately" after one rescan, was not deleted after the second, and its Nagios service stayed. No evidence file. | |
| TC-DSC-08 | Pass | Tester reported the user without `system.discover` had the button disabled with the tooltip "Your role can't run network scans" and the status API returned 403, and Super Admin could start and cancel a scan. No evidence file. | |
| TC-DSC-09 | Pass | Tester reported the scan started with no confirmation dialog and the button was disabled while scanning, as the catalog expects. The catalog's spec-gap note stands: the journey plan expects a confirmation modal and the app has none. No evidence file. | |

## Expected-item observations and restoration

Per-item values were not supplied. Each row states the expected item and that the tester confirmed it in the summary answer, not a measured value.

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-DSC-02 | E1 button reads "Scanning… N%" and is disabled while running | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DSC-02 | E2 bell shows "in progress", later "complete" | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DSC-02 | E3 status ends in exactly one of Success, Failed, Interrupted | Final state not recorded; tester confirmed | Pass | None | n/a |
| TC-DSC-05 | E1 8080 not found, then found | Not recorded; tester confirmed | Pass | None | Ports restored (tester reply) |
| TC-DSC-05 | E2 invalid ports refused | Not recorded; tester confirmed | Pass | None | |
| TC-DSC-05 | E3 Configuration Change log records each edit | Not recorded; tester confirmed | Pass | None | |
| TC-DSC-06 | E1 removed-network devices unchanged or Missing | Not recorded; tester confirmed | Pass | None | Network restored (tester reply) |
| TC-DSC-06 | E2 scanned-network devices not "Address unknown" | Not recorded; tester confirmed | Pass | None | |
| TC-DSC-07 | E1 port Missing with "Not seen lately", Nagios service stays | Not recorded; tester confirmed | Pass | None | Service restored (tester reply) |
| TC-DSC-07 | E2 one missed scan does not delete or archive it | Not recorded; tester confirmed | Pass | None | |
| TC-DSC-08 | E1 button disabled with tooltip, status API 403 | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DSC-08 | E2 Super Admin can start and cancel | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DSC-09 | E1 scan starts with no confirmation dialog | Not recorded; tester confirmed | Pass | None | n/a |
| TC-DSC-09 | E2 button disabled while scanning | Not recorded; tester confirmed | Pass | None | n/a |

## Deviations from the plan

- No `vmlab preflight` and no formal start: the draft queue was never started, and the supervised launcher does not cover these cases.
- The deployed application revision is unknown. These results apply to whatever build the lab was running, not to `44471f7c`.
- The scan-range guard (`10.77.0.0/28`) was requested of the tester but its outcome was not recorded.
- The tester's confirmation was a one-word reply to a multi-part question. Per-item observations are therefore missing.

## Follow-up

- Defects found: none reported. TC-DSC-09's confirmation-dialog spec gap is already in the catalog note.
- Cases to repeat in the next run: re-verify against a known deployed revision with evidence for any case where a reviewer wants per-item proof. The tracking issue number, once created, belongs in the progress file and branch name.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
