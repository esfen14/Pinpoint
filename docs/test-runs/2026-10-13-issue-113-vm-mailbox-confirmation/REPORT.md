# Test run: issue-113-vm-mailbox-confirmation

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | Appliance application `1ca2c757`; installer mail transport module `697869e` applied incrementally |
| Plan | Follow-up to [VM email-delivery run](../2026-10-13-issue-113-vm-email-delivery/REPORT.md), issue #113 email check |
| Tester | Mailbox owner reported receipt in chat; OpenCode agent correlated with appliance logs |
| Environment | Existing installer-built VM, Gmail SMTP transport; no direct mailbox access granted |
| Raw evidence | Conversation mailbox-owner confirmation; VM `/usr/local/nagios/var/nagios.log` and Nagios systemd journal (not committed) |

## Result

**Overall: Partial.** Owner clarified that the duplicated pasted CRITICAL body represented **one** web01 PROBLEM email, followed by a distinct web01 RECOVERY email. Both timestamps/content correlate with the Nagios log and Gmail SMTP 250 acknowledgements. No claim of two CRITICAL messages is supported. The owner has not yet said whether a web02 CRITICAL message appeared in inbox/spam during the quiet-window trial (~15:19 UTC), so mailbox absence remains unverified; Nagios logged zero matching notification dispatches in that trial.

Totals: Pass 2, Fail 0, Blocked 0, Skipped 1.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Outside-window CRITICAL inbox receipt | Pass | Owner supplied web01 `ssh-22-tcp` PROBLEM/CRITICAL email body dated 15:22:08 UTC, and clarified its duplicate paste was the same email. Nagios logged exactly one matching CRITICAL notification; msmtp journal recorded SMTP 250 at 15:22:11 UTC. | — |
| Restoration RECOVERY inbox receipt | Pass | Owner supplied distinct web01 `ssh-22-tcp` RECOVERY email body dated 15:22:29 UTC. Nagios logged one matching OK notification; msmtp recorded SMTP 250 at 15:22:33 UTC. | — |
| Quiet-window mailbox absence | Skipped | Owner has not reported checking for web02 `ssh-22-tcp` CRITICAL around 15:19 UTC in inbox/spam. The paired VM run observed zero matching Nagios notification events, but that is not independent mailbox-absence evidence. | — |

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No recipient email addresses or private addresses beyond documented lab range
- [x] Full email bodies and raw journal output not committed
