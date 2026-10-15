# Test run: issue-79-inbox-confirmed

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Application `4ed80435f088ddda26302a44a6008037bdfec933`; confirmation recorded after documentation checkpoint `03f32a74ce2fed98c29735658ce04faa065f49cd` |
| Plan | Issue [#79](https://github.com/esfen14/Pinpoint/issues/79), remaining actual-inbox comparison from [rebuilt VM run](../2026-10-15-issue-79-rebuilt-inbox/REPORT.md) |
| Tester | Mailbox owner, confirmed in the task conversation; Codex correlated the run and events |
| Environment | Same rebuilt VM/Nagios run on `10.77.0.0/28`, original Gmail delivery transport and two owner-controlled inboxes |
| Evidence | Owner-pasted message contents and explicit mailbox comparison in the task conversation; private raw lab evidence remains in ignored `test-results/issue79-post165/` |

## Result

**Overall: Pass for actual-inbox acceptance.** The owner identified the eight pasted messages as arriving in the selected-recipient mailbox and confirmed four messages for the default-group host only in the other mailbox, including checking Spam for exclusions. This completes the remaining inbox condition from the preceding run. No additional mail was sent and the lab was not redeployed.

Totals: Pass 3, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Observed evidence | Issue |
|---|---|---|---|
| I1: selected recipient receives selected host | Pass | Selected mailbox received host DOWN/UP and SSH CRITICAL/OK for `dev-16a18e` (`10.77.0.2`). Pasted diagnostics carry run ID `Issue79-20261015T031546Z`; UTC event times are 03:15:09, 03:15:18, 03:15:30 and 03:15:38 on Oct 15 | — |
| I2: default host reaches both eligible users | Pass | Same four events for `dev-c61190` (`10.77.0.3`) received in both inboxes. Eight total messages in selected mailbox, four total in default-only mailbox; owner explicitly confirmed the mailbox assignment | — |
| I3: selected host excluded from default-only mailbox | Pass | Owner explicitly confirmed only the default host's four events in the second inbox, and no selected-host messages there, including Spam | — |

## Correlation and limits

The [preceding run](../2026-10-15-issue-79-rebuilt-inbox/REPORT.md) independently verified exact Nagios host/service recipient sets, all 12 Gmail SMTP 250/EX_OK receipts, actual browser E2E, rescan preservation, fallback validation and baseline restoration. Its original Partial result remains historical; this report records the later owner observation that resolves its remaining inbox blocker.

The owner response confirmed the requested eight-versus-four comparison. Actual mailbox addresses and raw message copies are omitted from committed evidence. This report does not claim new browser, VM or SMTP execution; those results remain attributed to the preceding run and its exact application commit.

## Follow-up

No remaining issue-79 inbox acceptance gap. Final local `scripts/verify.sh all` passes: 2821 backend tests, 14 skips, 640 frontend tests, build/lint/docs green (29 existing lint warnings). Log: ignored `test-results/issue79-inbox-final-all.log`. Existing PR #160 is being submitted for review; final CI status is available on the PR. Human reviewers retain the merge decision.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range; mailbox addresses omitted
- [x] Raw evidence referenced without copying message bodies or configurations
