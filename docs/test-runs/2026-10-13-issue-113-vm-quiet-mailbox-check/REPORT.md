# Test run: issue-113-vm-quiet-mailbox-check

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | Appliance application `1ca2c757`; installer mail transport module `697869e` applied incrementally |
| Plan | Follow-up mailbox check for [the paired VM email trial](../2026-10-13-issue-113-vm-email-delivery/REPORT.md) |
| Tester | Mailbox owner reported result in chat; agent correlated prior Nagios log |
| Environment | Existing installer-built VM and dedicated test mailbox; agent did not access mailbox |
| Raw evidence | Owner's chat confirmation and appliance Nagios log from paired run (not committed) |

## Result

**Overall: Pass for the paired quiet/outside email comparison.** The owner reported finding no email for the web02 quiet-window CRITICAL trial around 15:19 UTC after being asked to check inbox and spam. The VM log recorded a HARD CRITICAL and zero matching service notifications then. In the separate outside-window web01 trial, the owner confirmed receipt of one CRITICAL and one RECOVERY email, matching Nagios notification records and Gmail SMTP acceptance. This is human-reported mailbox evidence, not independent agent access; absence is limited to the observed mailbox check and trial period.

Totals: Pass 2, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Quiet-window CRITICAL suppression | Pass | Owner replied that no corresponding email was found after being asked specifically about web02 `ssh-22-tcp` CRITICAL at ~15:19 UTC in inbox or spam. Nagios log: one HARD CRITICAL and zero matching CRITICAL notification events. | — |
| Outside-window CRITICAL delivery | Pass | Owner previously confirmed one web01 PROBLEM/CRITICAL email at 15:22:08 UTC (duplicate pasted body was the same message), followed by RECOVERY at 15:22:29 UTC. Nagios log: one CRITICAL and one OK notification; SMTP journal: both accepted with status 250. Different non-flapping target was used after a web02 outside trial was suppressed by flapping; see paired-run report. | — |

## Restoration and limitations

The paired run returned the policy to empty quiet hours, restarted both target SSH services, and applied passive OK. This follow-up involved no new state changes. The installer base snapshot still reflects an earlier installer revision; the mail transport module alone was updated on this VM. Other issue #113 deliverables and review requirements remain separate from this email test.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No recipient email addresses or private addresses beyond documented lab range
- [x] No raw mailbox or SMTP output committed
