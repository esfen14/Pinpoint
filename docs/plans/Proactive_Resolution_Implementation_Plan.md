# Proactive Resolution Implementation Plan

Status: **draft, Phase 0 in progress.** Drafted 2026-10-13. Nothing in this plan is implemented.

Scope: the issues in [`docs/issues/`](../issues/README.md) that make PinPoint act on a confirmed problem, tune when a problem is confirmed, and warn before one occurs: #6, #7, #8, #10, #19, #22, #23, #24, #25. Issue #9 (maintenance windows) is a dependency of one check in #24.

## 1. Rules for the whole plan

- **One branch and one pull request per issue.** Branch name `issue-<GitHub issue number>-<short-slug>`, created from the latest `origin/main`, as required by [`.agent/workflows/work-issue.md`](../../.agent/workflows/work-issue.md). Never commit to `main`. The plan numbers below are not GitHub numbers: file each issue on GitHub first, then use that number in the branch name.
- Installer parts (7.3, 8.2) live in the installer repository, so each gets its own branch and pull request there, linked from the PR of its PinPoint issue.
- A branch does not start until the issues it depends on are merged, unless the table says it can run in parallel.
- Run `scripts/verify.sh all` before finishing each branch; keep `.agent/progress/issue-<n>.md` and checkpoint after each round.
- Nothing may run automatically in production until Issue #24's safety controls are merged. Safety goes in before capability.
- Every PR updates the matching files in `spec files/` and `Implementation_Status.md`.

## 2. Branch map

| Plan issue | Suggested slug | Depends on (merged first) | Can run in parallel with |
|---|---|---|---|
| #10 | `issue-<n>-retry-interval-max-attempts` | none | #19 |
| #19 | `issue-<n>-nagios-command-channel` | none | #10 |
| #6 | `issue-<n>-flap-detection-settings` | #10 | #7 (installer part) |
| #7 | `issue-<n>-event-handler-framework` | Phase 0 security review | #6 |
| #24 | `issue-<n>-remediation-safety-controls` | #7 (ack check: #19, downtime check: #9) | #8 (local) |
| #8 | `issue-<n>-service-recovery-actions` | #7 | #24 |
| #22 | `issue-<n>-recovery-failure-escalation` | #7, #8, #19 | #23 |
| #23 | `issue-<n>-recover-automatically-toggle` | #7, #8 | #22 |
| #25 | `issue-<n>-trend-forecast-warnings` | product decision | any |

Issue #8 Part 8.3 (remote restart) stays in its branch but starts only after the Phase 0 finding in section 3.3 is resolved.

## 3. Phase 0: decisions and investigation

No application code. Output is a short note added to each affected issue.

### 3.1 Already verified in this repository (2026-10-13)

- The Nagios command pipe is writable by `pinpoint` and external commands are enabled (`check_external_commands=1`, `/usr/local/nagios/var/rw/nagios.cmd`, `prw-rw---- nagios:nagios`). This is recorded in Issue #19 and the gap plan, from a lab appliance. Issue #22 uses the same pipe, so only the specific custom-notification command still needs a lab check, not the pipe itself.

### 3.2 Lab checks still to run on an installed appliance (VM lab, `scripts/vmlab fresh`)

Most of these are scripted. With the appliance running (`scripts/vmlab fresh`, or `scripts/vmlab up` on an installed one):

```
scripts/vmlab phase0                       # read-only checks and a temporary spool trial
scripts/vmlab phase0 --with-notification   # also sends ONE custom notification (may email a real contact)
```

The probe is [`lab/phase0_event_handler_probe.sh`](../../lab/phase0_event_handler_probe.sh). It prints PASS, FAIL and INFO lines, saves the output under the vmlab state folder, and removes its test directories. It does not cover the handler timeout test or the installer re-run comparison (run `phase0` before and after `scripts/vmlab fresh` and compare the `nagios.cfg sha256` line). Record the output under `docs/test-runs/` with its template (`scripts/new_test_run.sh phase0-event-handler-checks`).

1. `ls -ld /usr/local/nagios/var/spool /usr/local/nagios/libexec` and `id nagios; id pinpoint`: can a new `pinpoint-events` directory be created with mode 2770 `nagios:nagios` and read by `pinpoint`?
2. `sudo -u nagios test -x <path>` for a candidate executable path: can `nagios` execute a root-owned file under `libexec`, and can it not traverse `/opt/pinpoint`?
3. `grep -E "enable_event_handlers|event_handler_timeout|log_event_handlers|check_external_commands" /usr/local/nagios/etc/nagios.cfg`.
4. Write a harmless `SEND_CUSTOM_SVC_NOTIFICATION` line to the pipe for a lab service and confirm a notification appears in the archive and in the PinPoint feed (needed by #22).
5. Confirm the Nagios event handler timeout kills a slow handler (the handler only writes one line, so this should be instant).

### 3.2.1 Results of the first run (2026-10-13)

| Check | Result | Consequence |
|---|---|---|
| `pinpoint` is in groups `pinpoint` and `nagios`; `www-data` is in `nagios` | As the installer read predicted | Spool group must be `pinpoint`, not `nagios`. |
| Trial spool `nagios:pinpoint` 2770 | `nagios` writes, new files inherit group `pinpoint`, `pinpoint` reads and deletes, `www-data` cannot list or write | Design for Part 7.3 confirmed. A `nagios:nagios` 2770 trial directory **was** writable by `www-data`. |
| `/usr/local/nagios/var/spool` | `root:root` 755 | `nagios` cannot create the spool subdirectory itself; the installer (root) must create it. |
| `/usr/local/nagios/libexec` | `nagios:nagios` 775 | Group-writable, so `pinpoint` and `www-data` could replace a file there. The handler must not live in `libexec`; `/usr/local/sbin/pinpoint-event-handler` (`root:root` 755) is confirmed as the location. `nagios` can execute a root-owned 755 file in `/usr/local/sbin`. |
| `/usr/local/nagios/var/rw/nagios.cmd` | `nagios:nagios` 660 pipe | **New finding for Issue #19 and its security review:** `www-data` is in group `nagios`, so the web server user can also write Nagios commands. Decide whether to remove `www-data` from the group (check what Nagios CGI needs it for) or accept and document the risk. |
| `nagios.cfg` | `enable_event_handlers=1`, `log_event_handlers=1`, `event_handler_timeout=30`, `check_external_commands=1`; `nagios -v` passes | These are stock values, as the installer read said. Part 7.3 still makes them explicit. |
| `pinpoint-gunicorn` | `NoNewPrivileges=no`, no `ProtectSystem` or `ReadWritePaths` | No systemd change needed. |
| sudo for `pinpoint` | Only `pinpoint-apply-smtp ""` and `systemctl reload nagios`; cannot restart Nagios | Matches installer step 9. |
| AppArmor | 39 profiles in enforce mode, none for nagios, pinpoint or gunicorn | No blocker. |

Limits: this appliance reports no vmlab stamp and a `.venv` is not under the app directory, so it was not built by `vmlab fresh`; repeat on a `vmlab fresh` build before relying on it for the report in `docs/test-runs/`.

### 3.3 Finding: the remote sudo rule does not allow restarts (Issue #8 Part 8.3)

From `server/app/ncpa_deployment/ncpa_deployment.py`:

- The sudoers drop-in on each device is `/etc/sudoers.d/pinpoint-ncpa-deploy`, and it contains exactly one line: the deployment user may run `/usr/local/sbin/pinpoint-ncpa-deploy` as root without a password (`install_restricted_sudo`).
- That rule does **not** restrict arguments. The helper itself checks that its single argument is a 32-character hex token (`^[a-f0-9]{32}$`) and then installs and configures NCPA (apt, gpg, sed on `ncpa.cfg`, certificate creation, `systemctl restart ncpa`). It has no service argument and cannot restart an arbitrary service.

Consequence: the existing deployment account **cannot** be used to restart a monitored service. Part 8.3 would need a second helper and a second sudo rule installed on every monitored device, which expands the privilege PinPoint holds on devices. That is a security decision for the team, not an implementation detail. Recommendation: ship Part 8.1 and 8.2 (local restart) first, and treat 8.3 as a separate, explicitly approved change.

### 3.4 Security review of the Issue #7 design

Review the model "Nagios only appends one validated JSON line to a spool, PinPoint decides and runs an allowlisted action as `pinpoint`" before any code. Questions for the review:

- Can any process other than `nagios` write a spool line, and what happens if it does (the consumer must treat every line as untrusted)?
- Is a root-owned executable under `libexec` acceptable, and is mode 0755 enough?
- Is the hourly cap and cooldown enough to stop a restart loop, given the kill switch in #24?

### 3.5 Product decisions

- Issue #25 (forecasting): wanted at all, and display-only or may it notify?
- Issue #8 Part 8.3: accept a new privileged helper on devices (see 3.3), or leave remote restart out?

## 4. Phases

### Phase 1: Foundations

| Branch | Exit condition |
|---|---|
| #10 retry interval and max attempts | Defaults produce byte-identical generated config; saved values appear in every host and service; Nagios validates. |
| #19 Nagios command channel | Acknowledgement, check-now and custom-notification commands reach Nagios; a rejected command is reported. |
| #6 flap settings (after #10) | A forced flap is flagged in `objects.cache` and listed in history. |

### Phase 2: Event handler framework (#7)

Work order inside the one branch: installer part first (in the installer repository, section 5), then Part 7.1 System, then Part 7.2 Web. Exit condition: with no actions defined, generated config is unchanged; on a lab service forced to HARD CRITICAL, exactly one run is recorded and a SOFT state records none.

### Phase 3: Safety before real actions (#24)

Start the parts that only need #7 (kill switch, retention, health, interrupted-run handling). Add the acknowledgement check when #19 is merged and the downtime check when #9 is merged; if #9 is not ready, ship without it and track the gap in `Implementation_Status.md`.

### Phase 4: Real recovery actions

1. #8 Parts 8.1 and 8.2: local restart and the narrow sudoers drop-in. `pinpoint-gunicorn` stays out of the first allowlist.
2. #22 escalation through Nagios custom notifications.
3. #23 per-service toggle.

### Phase 5: Conditional

- #8 Part 8.3 only if the team approves the privilege change in section 3.3.
- #25 only if the product decision is yes.

## 5. What to look for in the installer repository

The installer is outside this repository (the VM lab plan lists its steps: `install-packages`, `install-nagios-core`, `install-nagios-plugins`, `configure-snmp`, `configure-nagios`, `deploy-pinpoint-web`, `configure-pinpoint-privileges`). For each item, record the file and line so the issues can name an exact code location.

1. **Nagios directories and users.** Where the build creates `/usr/local/nagios/var/spool`, `libexec`, `var/rw`; the owners and modes it sets; the `nagios` user's umask; whether `pinpoint` is added to group `nagios` and where.
2. **Where sudoers is written.** The step that installs `pinpoint-apply-smtp` and the `systemctl reload nagios` rule (very likely `configure-pinpoint-privileges`). Note: file name under `/etc/sudoers.d/`, how it is validated (`visudo -c`), whether it replaces or appends, and what happens if validation fails. This is the model for the Part 8.2 drop-in.
3. **How the SMTP helper is installed.** Path, owner, mode and how it is copied. Part 7.3's executable should follow the same pattern.
4. **Upgrade behavior.** Does re-running the installer overwrite `nagios.cfg`, sudoers or the helpers, or skip them if present? Is there an installer version marker? Part 7.3 and 8.2 need an upgrade path that does not lose configuration.
5. **Application directory permissions.** Ownership and mode of `/opt/pinpoint` and `/opt/pinpoint/Network-Diagnosis-System`, and whether the `nagios` user can traverse them (git reports "dubious ownership" today).
6. **The `pinpoint-gunicorn` systemd unit.** Its `User=`, and any hardening such as `ProtectSystem`, `ReadWritePaths`, `PrivateTmp`, `NoNewPrivileges`. `NoNewPrivileges=true` would break `sudo -n systemctl restart`, and `ReadWritePaths` would need to include the spool.
7. **`nagios.cfg` settings it writes.** `enable_event_handlers`, `event_handler_timeout`, `log_event_handlers`, `check_external_commands`, `command_file`.
8. **Mandatory access control.** Whether AppArmor or SELinux profiles exist that could block the handler or the spool.
9. **Hardcoded values.** `REPO_URL`, `REPO_BRANCH="main"` and any hardcoded paths the new files must match.
10. **Idempotency and tests.** Whether the steps can be run twice safely and whether the installer has its own tests, so Part 7.3 and 8.2 can add ownership and mode tests.

### 5.1 Findings (installer repository, read 2026-10-13)

Source: a read of the installer's `setup/` scripts, supplied by the team. Items marked *lab* still need an installed appliance.

| # | Finding | Effect on the plan |
|---|---|---|
| 1 | The installer never creates `var/spool`, `libexec` or `var/rw`; it runs the stock Nagios `make` targets (`install-nagios-core.sh:98-114`). Their owners and modes are not visible in the installer. `www-data` is added to group `nagios` (line 100). `pinpoint` joins group `nagios` at `configure-pinpoint-privileges.sh:251`. | **Design change in #7:** a `nagios:nagios` 2770 spool would be writable by the web server. Use owner `nagios`, group `pinpoint`, mode 2770. Verify on *lab*. |
| 2 | Sudoers pattern: `mktemp`, `visudo -cf`, on failure delete and exit, otherwise `install -m 440 -o root -g root` (`configure-pinpoint-privileges.sh:302-316`, `545-559`). Step 9 asserts that restart, stop and start are **not** allowed. | #8 Part 8.2 copies the pattern and must update the step 9 negative check, or the installer fails its own verification. |
| 3 | The SMTP helper is `/usr/local/sbin/pinpoint-apply-smtp`, `root:root` 755, `#!/usr/bin/python3 -I`, JSON on stdin, no arguments (`:538-539`). | #7 handler becomes `/usr/local/sbin/pinpoint-event-handler` in the same style, not under `libexec` (whose only installer file is `nagios:nagios`). |
| 4 | Scripts overwrite their own helpers and sudoers on every run and keep user data. `nagios.cfg` is edited only when a line is missing, with backup and rollback on `nagios -v`. Whether `make install-config` overwrites `nagios.cfg` on a re-run is unknown (`configure-nagios.sh:76`). No installer version marker. | Upgrade handling is simple for new files. The `nagios.cfg` settings must be re-checked after a re-run (*lab*). |
| 5 | `APP_ROOT` is 755 (`deploy-pinpoint-web.sh:446`). Modes of `Network-Diagnosis-System` and `.venv` below it were not checked. | `nagios` can reach the app root, but the handler stays independent of it. |
| 6 | `pinpoint-gunicorn` has no `NoNewPrivileges`, `ReadWritePaths` or `ProtectSystem` (`deploy-pinpoint-web.sh:872-900`). | `sudo -n systemctl restart` will work and the spool needs no systemd change. Good: no blocker. |
| 7 | The installer writes only `interval_length` and `cfg_file=` lines. It does **not** set `enable_event_handlers`, `event_handler_timeout`, `log_event_handlers` or `check_external_commands`. | The earlier statement that event handlers are enabled came from the stock value on a lab appliance. #7 Part 7.3 adds an idempotent block (modeled on `ensure-nagios-interval.sh`) so the setting is explicit. Also confirm `check_external_commands` on a fresh install (*lab*). |
| 8 | AppArmor and SELinux are not mentioned anywhere. | Check `aa-status` on the lab VM (*lab*). |
| 9 | `REPO_BRANCH="main"` is hardcoded. Only `check-interval-tests.sh` and `smtp-admin-email-tests.sh` exist; nothing tests the privileges script or its re-run safety. | #7 and #8 each add a test script in the style of `smtp-admin-email-tests.sh` and new step 9 / healthcheck checks. |

New lab checks arising from these findings (add to section 3.2): `id pinpoint` and `getent group pinpoint`; a write as `nagios` and a delete as `pinpoint` in a test directory with the proposed owner, group and mode; confirm `www-data` cannot enter it; `aa-status`; re-run the installer and confirm `nagios.cfg` keeps the event handler settings.

## 6. Risks

| Risk | Control |
|---|---|
| Restart loops | Cooldown, hourly cap (#7), kill switch and stalled indicator (#24). |
| Privilege creep | Exact command lines in sudoers, no wildcards, `visudo -c` in the installer, remote restart out of the first release. |
| Silent failure | Consumer heartbeat (#24), failure escalation (#22). |
| Installer drift | Install and upgrade tests in the VM lab; record in `docs/test-runs/`. |
| Spool abuse | Treat every spool line as untrusted; validate and discard malformed lines; cap spool size. |

## 7. Status log

| Date | Item | Result |
|---|---|---|
| 2026-10-13 | 3.1 command pipe | Verified in earlier lab run, recorded in Issue #19. |
| 2026-10-13 | 3.3 remote sudo rule | Verified from source: helper cannot restart services. |
| 2026-10-13 | 5 installer repository | Read by the team; findings in 5.1. Issues #7 and #8 updated. |
| 2026-10-13 | 3.2 lab checks (plus the additions in 5.1) | Run once with `lab/phase0_event_handler_probe.sh` on a running appliance (host `pinpoint`, Ubuntu 22.04.5, app commit `d4df736`, no vmlab stamp, so not a `vmlab fresh` build): **16 PASS, 0 FAIL**. Findings in 3.2.1. Not run: custom notification (`--with-notification`), handler timeout, installer re-run comparison. |
| 2026-10-13 | 3.2 #4 custom notification (Issue #22) | **Verified on the lab appliance:** `pinpoint` wrote `SEND_CUSTOM_HOST_NOTIFICATION;gateway;0;...` to `nagios.cmd`; Nagios logged `EXTERNAL COMMAND` and sent a `HOST NOTIFICATION ... CUSTOM (DOWN)` to each contact, using the contact's notification command. Option `0` (no force) was used. Service form (`SEND_CUSTOM_SVC_NOTIFICATION`) not tried. |
| 2026-10-13 | HTML notification email (not in the plan's issues yet) | Now owned by the app: `server/scripts/pinpoint_notify_email.py` plus generated `pinpoint_notify_host_html` and `pinpoint_notify_service_html` commands (no installer change needed). Deployed to the lab appliance by copying the five changed files; the earlier hand edit of `commands.cfg` and the `/usr/local/sbin` copy were removed. A Nagios custom notification for `gateway` was sent through the generated command on 2026-10-13. |
| | 3.4 security review | Not started. |
| | 3.5 product decisions | Open. |
