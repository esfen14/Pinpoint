# Test run: issue-113-vm-email-delivery

| | |
|---|---|
| Date | 2026-10-13 |
| Commit tested | Application `1ca2c757` (existing VM deployment), installer mail-transport module `697869e` applied incrementally |
| Plan | Issue #113 §G, additional end-to-end delivery check following the VM dispatch retest |
| Tester | OpenCode agent; mailbox owner confirmed receipt of a separate recovery message in chat |
| Environment | Existing installer-built appliance VM, Nagios Core 4.5.11; mail helper from current installer applied without reprovisioning base snapshot; isolated web01/web02 targets |
| Raw evidence | VM `/usr/local/nagios/var/nagios.log`, systemd Nagios journal and appliance `status.dat` (not committed); mailbox confirmation in conversation; no mailbox screenshot/credentials collected |

## Result

**Overall: Partial.** A recovery email was confirmed by the mailbox owner for the monitored web02 SSH service. In the new paired CRITICAL experiment, Nagios suppressed notifications in the quiet window and dispatched one outside it for web01, which Gmail SMTP accepted (250, `EX_OK`). The mailbox owner has **not yet confirmed arrival of that specific CRITICAL message**, nor absence of a matching message for the quiet trial. SMTP acceptance and Nagios dispatch are not inbox delivery.

Totals: Pass 4, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| Owner-reported recovery receipt | Pass | Owner pasted the body of a `RECOVERY` for web02 `ssh-22-tcp`, dated 15:14:53 UTC, and said it came from the inbox, not the spam folder (previously un-spammed). Nagios log records one matching `OK` service notification at that timestamp. This is owner attestation, not agent inspection of mailbox. | — |
| Quiet-window policy and validity | Pass | Versioned API PUT set Tuesday 15:00–16:00 UTC (Nagios server local time), rendered Tuesday `00:00-15:00,16:00-24:00`; Nagios preflight zero warnings/errors. | — |
| CRITICAL during quiet hours | Pass | web02 SSH was stopped; three passive CRITICAL checks reached HARD CRITICAL at 15:19:24 UTC. Nagios log had **0** matching `SERVICE NOTIFICATION` events. SSH was restarted and OK applied. No claim about inbox absence. | — |
| CRITICAL after removing quiet hours | Pass | Versioned API PUT restored empty quiet hours and Nagios preflight had zero warnings/errors. The first outside trial on web02 reached HARD CRITICAL but sent no notification because the service was flapping; this attempt **does not prove delivery**. Retried on non-flapping web01 SSH: stopped service, three passive CRITICAL checks reached HARD CRITICAL at 15:22:08 UTC; Nagios logged **1** matching CRITICAL notification and the Nagios systemd journal recorded msmtp SMTP status 250 and `EX_OK` at 15:22:11. This shows acceptance by Gmail's SMTP server, not mailbox receipt. | — |
| CRITICAL inbox arrival | Skipped | Await owner confirmation of the **web01** `ssh-22-tcp` CRITICAL message dated approximately 15:22 UTC, in inbox or spam. The prior owner-confirmed web02 recovery is a different message. | — |
| Quiet-window inbox absence | Skipped | Await owner check for any matching web02 CRITICAL message from approximately 15:19 UTC; Nagios dispatch log count zero is the primary suppression evidence. | — |

## Restoration and limitations

- Both targets' SSH services were restarted and observed UP in the demo lab status; passive OK submitted to Nagios. The notification policy was returned to no quiet hours (version 7). Existing SMTP settings and recipient opt-in were left in place.
- Flapping on web02 suppressed the first outside-window attempt; it was not counted as a policy failure or success. The separate non-flapping web01 trial produced a logged notification and SMTP acceptance. Do not identify the two trials as the same target.
- The installer base snapshot still reflects the older revision; this was an incremental installer-module update, not fresh acceptance of the newer installer.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No email addresses or private addresses beyond the documented lab range
- [x] Raw log output and SMTP message IDs are not committed
