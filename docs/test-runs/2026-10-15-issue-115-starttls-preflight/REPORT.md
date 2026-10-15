# Test run: issue-115-starttls-preflight

| | |
|---|---|
| Date | 2026-10-15 |
| Commit tested | `899e7cd2c4ef5b53fcf55c3b478d3e267feb51ac` (final application source) |
| Plan | [Issue #115 specification](../../issues/issue-002.md), STARTTLS-only user decision |
| Tester | Codex |
| Environment | Development checkout; VirtualBox unavailable and Docker socket access denied. No appliance or database changed. No lab network contacted. |
| Raw evidence | Local checkout `test-results/issue-115-vmlab-preflight.log`, `issue-115-docker-preflight.log`; not committed |

## Result

**Overall: Partial; live acceptance blocked.** Both available lab entry points
were checked and could not be used. No live SMTP send, installed-helper apply,
forced notification or service-user log readability was observed. This is an
infrastructure preflight record, not a product pass.

Totals: Pass 0, Fail 0, Blocked 2, Skipped 4.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| VM lab prerequisite | Blocked | `scripts/vmlab preflight` exits 1: VBoxManage not found (`issue-115-vmlab-preflight.log`). | [#115](https://github.com/esfen14/Pinpoint/issues/115) |
| Docker fallback prerequisite | Blocked | `docker ps` exits 1: permission denied connecting to the Docker socket (`issue-115-docker-preflight.log`). | [#115](https://github.com/esfen14/Pinpoint/issues/115) |
| Existing helper save and STARTTLS local-sink email | Skipped | No usable appliance. Mocked API/helper/SMTP round trips do not prove installed behavior. | — |
| Real failed notification and next-poll API indicator | Skipped | No usable Nagios instance; exact runtime worker block and time-to-notice remain unverified. | — |
| Pinpoint service-user log read access | Skipped | Cannot inspect or execute as the appliance service user. No permissions changed. | — |
| Real browser against appliance | Skipped | Isolated React interaction tests only; no live browser acceptance. | — |

## Deviations from the plan

Implicit TLS, installer edits, installer release notes and implicit-TLS/upgrade
trials are deferred by the user's explicit STARTTLS-only decision. Existing SMTP
columns and `settings.email` suffice, so no migration or permission seed changes
are applicable. The failure fixtures were checked against upstream Nagios Core
4.5.11 `base/workers.c`; source inspection is not live evidence.

## Follow-up

- No product defect was observed or filed during this preflight.
- Keep the #115 pull request in draft until an accessible, exclusively owned
  appliance can run the four skipped cases. Confirm installed helper validation
  and service-user log access before asserting notification-failure acceptance.
- Preserve existing STARTTLS credentials and restore temporary relay settings
  after the future local-sink and forced-notification trial.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
