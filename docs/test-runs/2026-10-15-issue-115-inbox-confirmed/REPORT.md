# Test run: issue-115-inbox-confirmed

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `432e492ffbe749458084f88a933d01a8789cffa2`; application source unchanged from `6e14836e` |
| Plan | [STARTTLS acceptance](../../../server/tests/plans/SMTP_Relay_Acceptance.md), issue #115 |
| Tester | Codex and mailbox owner |
| Environment | Same owned Docker appliance as the [local acceptance run](../2026-10-15-issue-115-starttls-docker/REPORT.md); owner-configured external Gmail relay via custom provider, port 587/STARTTLS |
| Raw evidence | Dev host `/tmp/Pinpoint-issue-115/test-results/`: `issue-115-real-inbox.log`, `issue-115-real-inbox-retry.log`, `issue-115-real-notification.log`, `issue-115-restore-synthetic.log`, `issue-115-browser-final.log`; receipt confirmation in owner conversation |

## Result

**Overall: Pass for the final external notification and guarded browser retest.**
The owner reported that the UI test email worked after changing sending accounts.
The agent then dispatched one labeled real Nagios notification. The owner pasted
the received message with the exact host, UTC timestamp and marker. Mailbox folder
placement was not specified. No additional external test email was sent by the
agent after the owner's successful test.

Totals: Pass 5, Fail 0, Blocked 0, Skipped 0 for the final run.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| External test email | Pass | Owner reported the configured UI test worked; owner-reported success, not independent agent mailbox inspection | — |
| Real Nagios dispatch | Pass | Production notification path dispatched `issue115-inbox-20261015T091201Z` for `issue115-host` at `2026-10-15T09:12:01Z`; no failed-notification indicator and worker finished (`issue-115-real-notification.log`) | — |
| Actual receipt | Pass | Owner pasted received NOTICE/UP message matching host, timestamp and unique marker; no mailbox-folder claim | — |
| Guarded browser repeat | Pass | Real sender credentials replaced with synthetic settings, account/contact restored, Nagios validated before reload; final committed browser test passed in 31.6 s against local sink (`issue-115-restore-synthetic.log`, `issue-115-browser-final.log`) | — |
| Owned fixture cleanup | Pass | Confirmed container label `pinpoint.issue=115`, then removed only `issue-115-smtp-appliance`; saved credentials had already been replaced before removal | — |

## Earlier provider setup attempts

These attempts preceded the successful final run and are retained rather than
reclassified as successful delivery. The first supplied credential failed AUTH
with SMTP 535. After the owner replaced it with a complete app password,
authentication succeeded, but DATA failed with SMTP 550 and the provider's daily
sending-limit classification. That sender's delivery trial was blocked by its
quota ([#115](https://github.com/esfen14/Pinpoint/issues/115)); no delivery is
claimed for either attempt. The owner chose and configured another account
through Settings → Email. No application change was needed for these setup
failures. Credentials and real sender/recipient addresses are omitted.

## Verification and limits

The complete local gate in this session passed: 3058 backend tests, 14 backend
skips, 653 frontend tests, docs/build and lint (0 errors, 29 warnings), recorded
in the preceding Docker report and `issue-115-resumed-all.log`. The final browser
repeat above exercises the committed guard added after that gate. Final frontend
and documentation checks are recorded in the PR.

The earlier Docker and preflight reports retain their original results. This
run supplies their pending external receipt and browser-repeat evidence. No
installer ISO/upgrade, implicit TLS, OAuth, plaintext SMTP or other provider's
compatibility is claimed. Human code review remains required before merge.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No real sender/recipient or private infrastructure addresses
- [x] Evidence is referenced by name and location, not pasted
