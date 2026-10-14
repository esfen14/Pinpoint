# Test run: issue-113-vm-mail-transport

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | PinPoint application `560ad780`; installer `697869e` (only `configure-pinpoint-privileges.sh` re-run on the existing VM) |
| Plan | Issue #113 email-delivery follow-up; `docs/plans/VM_Lab_Plan.md` (incremental VM update, not a fresh installer acceptance run) |
| Tester | OpenCode agent |
| Environment | Existing installer-built Ubuntu 22.04.5 VM, Nagios Core 4.5.11; no SMTP credentials configured |
| Raw evidence | Local `/tmp/opencode/issue113-installer-update.log`, `/tmp/opencode/issue113-mail-health.log`; VM `/var/log/pinpoint-privileges.log` (not committed) |

## Result

**Overall: Partial.** Updated the VM's mail transport and narrowly scoped helper/sudo rule from the current installer checkout without relaxing secret-file access. SMTP credentials, an actual send and inbox arrival are untested. This incremental update is not a fresh installation of the new installer version; its base snapshot remains at the older installer revision.

Totals: Pass 3, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Current installer checkout | Pass | Fast-forwarded the separate clean local installer clone from `2859361` to `697869e`. Confirmed mail transport/helper implementation in `setup/configure-pinpoint-privileges.sh`; only that module was copied and re-run on the active VM. `issue113-installer-update.log` | — |
| Mail transport and privileges | Pass | Installer module installed `msmtp-mta` and `bsd-mailx`; `/bin/mail` exists. `/etc/msmtprc` is `root:nagios` mode 640, helper is `root:root` 755 and the scoped sudoers file is `root:root` 440. Invoking the helper as `pinpoint` with `sudo -n` and empty stdin reached its JSON validator (`input is not valid JSON`, exit 1), rather than a sudo password prompt. `nagios` can read the config; neither receives broad write access. | — |
| Appliance health and Nagios config | Pass | `scripts/vmlab health`: 60 passed, zero warnings/failures; `nagios -v`: zero warnings/errors. `issue113-mail-health.log` | — |
| Settings → Email save and SMTP send | Skipped | No test account or Gmail app password was supplied; do not claim that a message was sent. | — |
| Inbox delivery | Skipped | Mailbox access/owner confirmation not available. | — |

## Deviations from the plan

The updated installer base steps changed (the running VM snapshot stamp still reflects `2859361`). Instead of `scripts/vmlab provision --force` and `fresh`, which would replace the base snapshot and discard this appliance's active policy-testing state, only the idempotent, relevant app-dependent privilege module was run on this lab VM. A future clean-installer acceptance run must reprovision a separate lane or explicitly coordinate snapshot replacement with the lab owner.

## Follow-up

- A permitted user can now enter a dedicated Gmail test account and app password privately through Settings → Email, save, and send a test message. Check the intended recipient inbox (and spam) without sharing credentials or message content in the repository.
- If the browser still reports `sudo: a password is required`, retest the scoped `pinpoint` sudo rule and application process identity; the rule was verified on the VM after this update.
- Installer owner retains production ownership; no app permission bypass or file ownership broadening was introduced.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
