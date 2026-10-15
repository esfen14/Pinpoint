# Test run: issue-115-starttls-docker

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | Application `6e14836e8e0f441d7785a741dfaac8ef34f41732` (same application source as `de7909e4`); new browser spec was uncommitted during the run |
| Plan | [STARTTLS acceptance](../../../server/tests/plans/SMTP_Relay_Acceptance.md), [#115 scope](../../issues/issue-002.md); implicit TLS deferred by requester |
| Tester | Codex |
| Environment | Owned standalone Ubuntu 22.04 Docker appliance, Nagios 4.5.11, Python 3.14, msmtp 1.8.16, real sudo; fresh migrated/seeded databases; loopback SMTP sink and browser port 18115; background automation disabled; no network scans |
| Image | `sha256:ecfc82b51c40fe08cc2874540dd321560582bb8b921b04745f4b8ab111038251` |
| Helper | Unmodified installer script from `6c23656ad87cdbb58a293f3c87bd56587246cd74`; extracted helper SHA256 `6b58bcb3f0376f68ddd2f8897fbc002909481fd1d8e65f3dcf51e23c4d5ce47e` |
| Raw evidence | Dev host `/tmp/Pinpoint-issue-115/test-results/`: `issue-115-live-api.log`, `issue-115-live-notifications.log`, `issue-115-live-browser.log`, `issue-115-live-browser-repeat.log`, `issue-115-nagios-validation.log`, `issue-115-resumed-all.log`; setup harnesses outside Git |

## Result

**Overall: Pass for the completed Docker acceptance scope.** The unchanged helper
applied settings through real sudo; authenticated STARTTLS test mail and real
Nagios host/service notifications reached the local sink. An actual failed
notification appeared in the API in 0.33 seconds, and browser interactions passed.
This does not claim external-provider acceptance or actual mailbox arrival.

Totals: Pass 14, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Owned isolated fixture | Pass | Separate labeled container and loopback endpoint; shared running lab untouched; no scans | — |
| Unmodified helper and real sudo | Pass | Installed existing helper, exact-command sudoers validated; API ran under pinpoint; helper checksum above | — |
| Custom relay save | Pass | Actual PUT invoked the privileged helper successfully (`issue-115-live-api.log`) | — |
| Protected transport metadata | Pass | Actual `/etc/msmtprc` owner/group root:nagios and mode 0640, checked after helper apply | — |
| Authenticated STARTTLS test email | Pass | Real local sink accepted the API test message; certificate trusted only inside test container | — |
| Blank-password preservation | Pass | Subsequent save omitted replacement password; second actual STARTTLS send succeeded | — |
| Invalid input | Pass | Invalid host, boolean port and implicit-TLS value produced field-specific 400 responses | — |
| Nagios pre-apply validation | Pass | Scoped fixture configuration passed `nagios -v` before reload (`issue-115-nagios-validation.log`) | — |
| Real host notification | Pass | External command drove production formatted-email script → sendmail/msmtp → sink (`issue-115-live-notifications.log`) | — |
| Real service notification | Pass | Separate custom service notification reached sink through same real path | — |
| Actual failed notification / next poll | Pass | Emptied only disposable transport, forced host notification; API returned matching UTC time and fixed exit-code-3 reason within 0.33 s; raw message/address text not exposed | — |
| Service-user log access | Pass | Read the actual NOTIFY worker log block as pinpoint (`issue-115-live-notifications.log`) | — |
| Browser interaction | Pass | Corrected test passed in 31.7 s: Gmail/custom help, validation, real save with blank password, test send, notice time/reason/link, retention after success, removal after log rotation, unsaved edits preserved; no credential in browser storage (`issue-115-live-browser-repeat.log`) | — |
| Complete isolated gate | Pass | 3058 backend passed/14 skipped; 653 frontend passed; docs/build green; lint 0 errors/29 warnings (`issue-115-resumed-all.log`) | — |
| Initial browser harness trial | Skipped | Interrupted while waiting for an incorrect Sign in locator; corrected to actual LOG IN label and rerun. No product failure claimed; original output retained (`issue-115-live-browser.log`) | — |

## Deviations from the plan

The fresh appliance entrypoint initially imported the scheduler before tables
existed. Background automation was disabled in the owned container before
migration/seed; no application source was changed. The cached image's sudo shim
was replaced only inside this container with real sudo and the SMTP-only rule.
The local sink records counters, not mail or authentication values. Its final
five messages were all encrypted and authenticated: two API tests, two Nagios
notifications and one browser-triggered test.

This retests the inaccessible-lab cases in the earlier
[preflight report](../2026-10-15-issue-115-starttls-preflight/REPORT.md), whose
original results are unchanged. The requester subsequently asked for a real inbox
trial; that is a separate test with separate provider acceptance and owner
confirmation. It is not inferred from these sink counts.

## Follow-up

- No application defect was observed in this Docker acceptance run.
- Repeat the browser test after restoring its synthetic baseline to verify the
  final fail-fast guard against accidentally using real relay credentials.
- Complete the separately requested inbox trial before final owner sign-off.
- No full installer ISO/upgrade trial, OAuth, implicit TLS or plaintext SMTP pass
  is claimed. These are outside this STARTTLS-only scope.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
