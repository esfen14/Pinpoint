# Test run: issue-116-escalations

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Backend application `c1bf732f` (all seven changed backend implementation/template files hash-identical at `b4d2c1648592c2e8294eb0d44fccb868d1fa9adb`); final browser source and test `b4d2c1648592c2e8294eb0d44fccb868d1fa9adb` |
| Plan | [Issue #116](https://github.com/esfen14/Pinpoint/issues/116), sections E–H; [repository plan](../../issues/issue-003.md) |
| Tester | Codex |
| Environment | Separate Docker project `pinpoint-issue116`, cached Ubuntu 22.04/Nagios Core 4.5.11 lab images; fresh multi-bind upgraded/seeded databases, two eligible contacts, two discovered targets. Exclusive internal bridge; scan restricted to two explicit /32 targets and TCP 22/80 plus UDP 161; addresses retained only in raw evidence |
| Timing | Lab `interval_length=10`: one Nagios time unit is ten seconds. Production uses the standard sixty-second unit. Notification-count routing, not production elapsed-minute timing, was tested |
| Raw evidence | This host: `/tmp/Pinpoint-issue-116/test-results/issue116-live/` (case ledger, config snapshots, validator output, source hashes, parsed routing and MIME captures); `/tmp/Pinpoint-issue-116/test-results/issue116-browser.json`. Harness scripts and detailed logs: `/tmp/pinpoint-116-*.py`, `/tmp/pinpoint-116-*.log`; not committed |

## Result

**Overall: Pass for the scoped Docker acceptance.** Real Nagios accepted both
escalation types. A scoped SSH service's first normal problem notification
reached only its selected normal recipient. With the problem still
unacknowledged and HARD CRITICAL, notification two reached the second contact
through the escalation group. The unchanged HTML notifier's real MIME output
was captured at the container-local sendmail boundary; external SMTP or inbox
delivery is not claimed.

Opt-out and deactivation each removed the now-empty group's escalation blocks
without losing the saved range. Restoring eligibility restored both blocks.
Deletion restored the previous generated file apart from its timestamp. An
actual Nagios validation rejection returned 422 and preserved the database and
live config. Browser CRUD and persistence passed against the real API.

Totals: Pass 12, Fail 0, Blocked 0, Skipped 2 (outside this scoped run).

## Cases

| Case | Result | Notes (observed evidence) | Issue |
|---|---|---|---|
| prepare-real-groups | Pass | Two eligible contacts; two discovered hosts; per-host recipients saved through the API; `cases.jsonl` | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| baseline-nagios-validates | Pass | Real `nagios -v` exits 0 with zero errors; `nagios-baseline.txt` | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| saved-host-and-service-escalations-valid | Pass | API-created scoped range produces one host and one service escalation; real validation succeeds; `escalations.cfg`, `nagios-escalations.txt` | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| notification-one-normal-recipient-only | Pass | First marker-bearing problem MIME goes to the normal selected contact only; Nagios notification count 1; `capture/`, `captured-routing.json` | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| unacknowledged-critical-escalates-at-two | Pass | Second distinct contact receives marker-bearing problem MIME at notification count 2; HARD CRITICAL remains unacknowledged; case ledger and MIME capture | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| delete-removes-live-blocks-and-restores-default | Pass | DELETE succeeds, both escalation types disappear; generated file matches pre-escalation baseline after timestamp normalization | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| opt-out-empty-group-omitted | Pass | Account API opt-out regenerates successfully; both blocks disappear, list explains inactivity, saving empty group returns 400, real validation passes | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| deactivation-empty-group-omitted | Pass | Account API deactivation has the same suppression, explanatory 400 and valid-config outcome | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| eligible-members-return-restores-saved-escalation | Pass | Returning the account to Active/opted-in regenerates both saved escalation blocks | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| actual-nagios-rejection-rolls-back | Pass | Deliberately invalid directive in this disposable lab's main config makes POST return 422; no saved range, live file unchanged | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| restored-nagios-validates | Pass | Original main config restored, real validation again exits 0 with zero errors | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| browser-add-edit-reload-delete | Pass | Opt-in `client/e2e/escalations.lab.spec.ts` passes twice, including final source: client validation, create, reload, edit, reload, cancel deletion, confirm deletion; final run 4.5 s | [#116](https://github.com/esfen14/Pinpoint/issues/116) |
| External SMTP/inbox delivery | Skipped | Local MIME capture proves routing only; no new transport implementation in this issue | — |
| Installer-built VM/production elapsed-minute timing | Skipped | Docker run only, accelerated Nagios clock; no installer or production timing claim | — |

## Deviations from the plan

The initial preparation harness expected HTTP 200 from discovery start; the API
correctly returned 202. It resumed the already-started scan without overlap.
An empty UDP list selected nmap's default set, so that isolated scan was stopped
and its process terminated before restarting with the explicit UDP 161 bound.
These were harness corrections, not application fixes.

The notification trial used normal passive check results while active checks on
the scoped service were temporarily disabled. Repeated results brought the
service to HARD CRITICAL, and a continuing failure result after the notification
interval triggered the second notification. No custom/forced-notification command
was used. The initial runner saw the second MIME before `status.dat` refreshed
and failed an immediate count assertion; the continuation waited for the actual
status count 2 and confirmed the unchanged event was unacknowledged. Raw outputs
retain the initial assertion and continuation. No product change or weakened
assertion was used to make notification acceptance pass.

The target was recovered and active checks re-enabled; saved escalation rows were
removed and the deliberately invalid main config restored. All changes were
confined to the separate disposable project; existing `pinpoint-lab` and issue-128
containers, the VM lab and host permissions were not changed by this run.

## Follow-up

No application defect was found in the scoped cases. Production elapsed-minute
and external inbox behavior remain untested here. PR CI and reviewer approval
are separate merge requirements; this report does not grant approval.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range (addresses omitted)
- [x] Evidence is referenced by name and location, not pasted
