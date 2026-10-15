# Event Handler Security Review (Issues #7, #8, #22)

Status: **draft checklist, review not yet held.** Prepared 2026-10-13 for the reviewer. Part of [`Proactive_Resolution_Implementation_Plan.md`](Proactive_Resolution_Implementation_Plan.md) section 3.4. The mandatory review is required by [`Issue #7`](../issues/issue-007.md) and the gap plan before any code is written.

## 1. What is being approved

1. Nagios calls one command, `pinpoint_event_handler`, on a state change. The command is a small root-owned program (`/usr/local/sbin/pinpoint-event-handler`) that **only appends one validated JSON line** to a spool folder. It never runs a fix.
2. A short PinPoint job (running as `pinpoint`) reads the spool, ignores anything that is not a HARD state, matches an enabled admin-defined action, applies cooldown, hourly cap and the kill switch, runs a fixed action type, and records a run row for every decision.
3. Action types are code with typed parameters. No command line, script path or unit name comes from a request or from a spool line.
4. Local restarts (Issue #8) use a narrow sudo rule listing each allowed unit as a full command line. Remote restarts are **not** part of the first release (see D2).
5. Failures are escalated through Nagios custom notifications (Issue #22), not a separate mail path.

## 2. Who can touch what today (lab appliance, 2026-10-13)

| Resource | Owner, mode | Who can use it through the `nagios` group |
|---|---|---|
| `/usr/local/nagios/var/rw/nagios.cmd` (command pipe) | `nagios:nagios` 660 | `pinpoint` and **`www-data`** can write Nagios commands |
| `/usr/local/nagios/var/status.dat` | group-writable | `pinpoint` and **`www-data`** can write |
| `/etc/msmtprc` (Gmail app password) | `root:nagios` 640 | `nagios`, `pinpoint` and **`www-data`** can read |
| `/usr/local/nagios/libexec` | `nagios:nagios` 775 | `pinpoint` and **`www-data`** can replace a program there |
| `/usr/local/nagios/var/spool` | `root:root` 755 | nobody but root can create entries |

Why `www-data` is in the group: Apache runs Nagios's own CGIs as `www-data` (`archivejson.cgi`, `statusjson.cgi`, `cmd.cgi`, served under `/nagios/cgi-bin`), and PinPoint reads alert and notification history from `archivejson.cgi`. The CGIs must read Nagios's files, so `www-data` **cannot simply be removed** from the group. `cmd.cgi` cannot be used to run commands today: `authorized_for_*_commands` lists only `nagiosadmin`, which has no usable password.

## 3. Threats and checks

Mark each row **Pass**, **Fail** or **Accept** with the evidence reference.

| # | Threat | Control in the design | How to check | Result |
|---|---|---|---|---|
| T1 | A process other than `nagios` forges a spool line | Spool is `nagios:pinpoint` 2770, not group `nagios`; the consumer treats every line as untrusted | Lab: `www-data` cannot list or write the spool (**done, passes**); send a malformed, oversized and duplicate line, confirm none runs | |
| T2 | The handler program is replaced | `/usr/local/sbin`, `root:root` 755, not under `libexec` | Lab: `pinpoint`, `nagios` and `www-data` cannot write it; installer test asserts owner and mode | |
| T3 | Shell injection through Nagios macros (host or service name, plugin output) | The handler only builds JSON in code; it never passes values to a shell; Nagios already strips illegal characters | Create hosts and services named with `; $( ) \` " '`, force a state change, confirm one valid line and no side effect | |
| T4 | Injection through an action's parameters | Fixed action types, parameters validated per type, unit names from a code allowlist | Unit tests with hostile input for every parameter; API returns 400 | |
| T5 | Privilege escalation through the sudo rule | One drop-in, exact command lines, no wildcards, `visudo -cf` before install | `sudo -n -l -U pinpoint` shows only the listed commands; installer step 9 negative checks (other units, `/bin/cat`) still refused | |
| T6 | Restart loop or self-inflicted outage | Cooldown, hourly cap, global kill switch (Issue #24); `pinpoint-gunicorn` excluded from the first allowlist | Lab: force repeated failures, confirm the cap stops it and the skip is recorded; flip the kill switch mid-run | |
| T7 | Spool flooding or disk fill | Per-line size limit, entry cap, retention in the existing purge job | Write 10,000 lines, confirm bounded storage and a recorded drop count | |
| T8 | Secrets in run records, logs or notifications | Output truncated and redacted; notification comment built from fixed text, never plugin output | Inspect a run row and the Nagios log after a run with a secret-like string in the output | |
| T9 | Duplicate or replayed events run an action twice | Event id and idempotent consumer; interrupted runs are never re-run | Restart the consumer mid-run; replay a spool line | |
| T10 | Anyone with write access to the command pipe can send Nagios commands (acknowledge, disable notifications, schedule downtime) | See D1 | See D1 | |
| T11 | The Gmail app password in `/etc/msmtprc` is readable by the web server | See D1 | See D1 | |
| T12 | Remote restart widens PinPoint's privilege on every monitored device | Left out of the first release | See D2 | |

## 4. Decisions for the reviewer

**D1. Narrow what the `nagios` group allows.** Removing `www-data` breaks PinPoint's alert history, so keep the membership and narrow the access instead. Proposed, each an installer change:

1. Put `/etc/msmtprc` in a smaller group that contains only the `nagios` user (change `OWNER_GROUP` in the root helper `pinpoint-apply-smtp`), so the web server cannot read the password.
2. Make `var/rw` group `pinpoint` mode 2770, so only `nagios` and `pinpoint` reach the command pipe and `www-data` does not. `cmd.cgi` is unusable today, so nothing is lost. Confirm the pipe keeps working after a Nagios restart.
3. Make the files in `var/` read-only for the group (directory 755, files 644), so the CGIs can still read them and the web server cannot write them. Confirm `pinpoint` does not need to write there.
4. Move any handler out of `libexec` (already the plan).

Options: **(a)** accept the current rights and record the risk, **(b)** apply 1 to 3 (recommended), **(c)** apply only 1 and 2. This is **not** a blocker for Phase 1 (#10, #19), but #19 adds more commands to the pipe, so decide before #19 is released.

**D2. Remote restart (Issue #8 Part 8.3).** The existing device rule only allows the NCPA install helper, which cannot restart anything. Restarting a remote service needs a second helper and rule on every device. Options: **(a)** leave it out (recommended), **(b)** approve a separate design with its own review.

**D3. Handler location and ownership.** Confirm `/usr/local/sbin/pinpoint-event-handler`, `root:root` 755, Python with `-I`, following the SMTP helper pattern.

## 5. Evidence to attach

- Lab output from `lab/phase0_event_handler_probe.sh` (first run 2026-10-13: 16 pass, 0 fail).
- Output for T1 to T3 and T6 to T9 from the lab run recorded under `docs/test-runs/`.
- `sudo -n -l -U pinpoint` before and after the Issue #8 installer change.
- The reviewer's decision on D1 to D3, written into the plan's status log.

## 6. Sign-off

| Role | Name | Decision on D1 | D2 | D3 | Date |
|---|---|---|---|---|---|
| Reviewer | | | | | |
| Project owner | (owner, decision recorded by the agent on request) | **b**: apply changes 1 to 3 | **a**: leave out | Confirmed: `/usr/local/sbin/pinpoint-event-handler`, source in this repository | 2026-10-14 |
