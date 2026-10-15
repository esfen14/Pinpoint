# Event handler framework: design for review (GitHub #120, plan Issue #7)

Status: **approved 2026-10-15; implementation may start.** The project owner asked for the
design to be reviewed before any code touches the sensitive files (`app/network_discovery/`, and a
new path that runs actions). Written for the reviewer and for the engineer who will build it.

Review answers (section 6), 2026-10-15: Q1 accepted (one file per event). Q2 accepted (two
commands). Q3 accepted (two permissions). Q4 changed on 2026-10-15: `RemediationRun` goes in `system.db`, not `history.db`, because the Engineering Standards allow only Nagios-produced snapshots in `history.db`. Retention addition kept:
one addition: `_purge_old_data` in `scheduler.py` also deletes `RemediationRun` rows older than
`Diagnostic_History_Retention_Days` (default 90) in this issue, with a unit test, so the table is
bounded from the start (it is an audit trail, not a source for network statistics). Q5: cover every
threat row with a test, and keep the lab run to the security-relevant checks.

Decisions already made by the project owner (2026-10-14): **D1** narrow the `nagios` group rights,
**D2** leave remote restart out of the first release, **D3** the handler is
`/usr/local/sbin/pinpoint-event-handler`, root-owned, with its source kept in this repository.
Installer changes are written up in `Installer_Instructions_Proactive_Resolution.md` (not built
here).

## 1. What this issue delivers (and what it does not)

Delivers:

1. A fixed list of **action types**, and admin-defined **actions** (an action type plus a scope plus
   limits).
2. A way for Nagios to tell PinPoint "this service just reached a HARD failure": a tiny handler
   that writes one small file to a spool folder.
3. A PinPoint **consumer** that reads those files, decides, runs the allowed action, and records every
   decision in a **run log**.
4. API routes, a **Remediation** page (action list, form, run log), permissions, tests and specs.

Does not deliver: any real recovery such as restarting a service (that is #121), the kill switch,
acknowledgement and downtime checks, retention and health reporting (#155), escalation (#153), the
per-service toggle (#154), or the installer-side work (written up as instructions only).

The one action type shipped here is `record_only`: it changes nothing and only writes a run row. It
is what the lab test uses, and it proves the whole chain without any side effect. #121 adds
`restart_local_service` as a second type through the same registry.

## 2. How an event travels

```
Nagios (user nagios)                      PinPoint (user pinpoint)
  service/host reaches a state             APScheduler job every 15 s
  event_handler runs  ───────────►         reads spool files
  /usr/local/sbin/pinpoint-event-handler   validates, ignores SOFT states
  writes ONE file, exits                   matches enabled actions
                                           cooldown + hourly cap
        spool folder                       runs the action type (fixed code)
  /usr/local/nagios/var/spool/             writes one RemediationRun row per decision
  pinpoint-events  (nagios:pinpoint 2770)
```

Nagios never runs a fix. The only thing it can do is leave a small note.

## 3. The pieces

### 3.1 Handler program

`server/scripts/pinpoint_event_handler.py` (source here, copied by the installer to
`/usr/local/sbin/pinpoint-event-handler`, `root:root` 755). Standard library only, run as
`/usr/bin/python3 -I`, like `pinpoint_notify_email.py`.

- Called as `pinpoint-event-handler <host|service> <state> <state_type> <attempt> <host> [<service>] <last_change>`.
- Validates every argument: allowed characters (`A-Za-z0-9 ._:/-` plus the words Nagios uses for
  states), maximum lengths, `state` and `state_type` from fixed sets. Anything else: exit non-zero,
  write nothing.
- Writes **one file per event**, named `<epoch_ns>-<pid>.json`, content one JSON line
  `{"v":1,"kind":..,"host":..,"service":..,"state":..,"state_type":..,"attempt":..,"last_change":..}`.
  It writes to a temporary name and renames, so the consumer never sees a half-written file.
- Refuses to write when the spool folder holds more than 1000 files (flood control); it exits quietly.
- Never opens a shell, never reads the network, never reads anything but its arguments.

*Deviation from the issue text:* the issue says "appends one validated JSON line". One file per
event avoids two Nagios processes writing to the same file at once, and makes "delete once handled"
atomic. The content is still one JSON line.

### 3.2 Nagios command definitions

Rendered into `hosts.cfg` only when at least one **enabled** action exists, and only when the handler
file exists on this machine (the same safety pattern as the HTML email script):

```
define command { command_name pinpoint_event_handler_service
  command_line /usr/bin/python3 -I /usr/local/sbin/pinpoint-event-handler service '$SERVICESTATE$' '$SERVICESTATETYPE$' '$SERVICEATTEMPT$' '$HOSTNAME$' '$SERVICEDESC$' '$LASTSERVICESTATECHANGE$' }
define command { command_name pinpoint_event_handler_host
  command_line /usr/bin/python3 -I /usr/local/sbin/pinpoint-event-handler host '$HOSTSTATE$' '$HOSTSTATETYPE$' '$HOSTATTEMPT$' '$HOSTNAME$' '$LASTHOSTSTATECHANGE$' }
```

Every macro is in single quotes. Nagios removes `'` and `$` from macro values (its default
`illegal_macro_output_chars`), so a value cannot end its quotes; the handler validates again anyway.
`illegal_macro_output_chars` must keep its default: this is listed in the installer note's checks.

*Deviation from the issue text:* two commands, because a host event has no service macros. One
program, one `kind` argument.

A covered object gets `event_handler pinpoint_event_handler_service` (or `_host`) and
`event_handler_enabled 1`. An uncovered object is rendered exactly as today. This is proven by the
existing byte-for-byte fixtures (`notification_policy_default_hosts.cfg`) plus a new test.

### 3.3 Data model

| Table | Database | Fields |
|---|---|---|
| `RemediationAction` | `system.db` | `Id`, `Name` (unique, 3 to 60 chars), `Action_Type` (fixed enum), `Scope_Kind` (`service` or `host`), `Host_Pattern`, `Service_Pattern`, `Parameters` (JSON, validated per type), `Enabled`, `Max_Runs_Per_Hour` (1 to 60, default 2), `Cooldown_Seconds` (60 to 86400, default 600), `Version`, `Updated_By`, `Updated_At` |
| `RemediationRun` | `system.db` | `Id`, `Event_Key` (unique with `Action_Id`), `Action_Id`, `Action_Name` (snapshot), `Hostname`, `Service`, `State`, `State_Type`, `Attempt`, `Received_At`, `Started_At`, `Finished_At`, `Outcome`, `Reason`, `Output` (max 1 KB, redacted) |

`RemediationRun` lives in `system.db` with the actions: it is written by PinPoint, and the standards
reserve `history.db` for Nagios snapshots. The existing `_purge_old_data` job deletes rows older than
`Diagnostic_History_Retention_Days`. The row keeps no foreign key to the action: deleting an action must
leave its runs, so `Action_Id` is a plain number and the action name is copied into the row.

`Outcome` values: `running`, `succeeded`, `failed`, `timed_out`, `skipped_cooldown`,
`skipped_hourly_cap`, `interrupted`. (Changed during build: a replayed event, a malformed file and a
disabled action cannot be stored as rows. The unique key on `Event_Key` and `Action_Id` is what stops a
replay; a malformed file has no action or valid host to record; only enabled actions are ever matched.
Replays and malformed files are discarded and written to the application log with no file content.)

Patterns are exact names or contain `*` only (`web-*`). Allowed characters `A-Za-z0-9._*-`. No regex.

One migration on the default bind (`upgrade_`; `upgrade_history` is empty), reviewed by hand, with a working
downgrade, chained after the current head.

### 3.4 Action registry

`server/app/remediation_actions.py`: a dictionary `ACTION_TYPES` of code-defined types. Each type
has: a key, a label, a plain-language description, a **parameter schema** (names, types, bounds,
allowed values), a `validate(params)` that returns cleaned values or an error per field, and a
`run(context)` function with a timeout. No parameter can be a command line, a script path or a unit
name. (#121 will take unit names from a code allowlist, not from the request.)

Shipped here: `record_only` (no parameters, `run` returns "recorded").

### 3.5 Consumer

`server/app/remediation.py`, called by an APScheduler job in `scheduler.py` every 15 seconds with
`max_instances=1` and `coalesce=True`.

For each run (bounded to 200 files, oldest first):

1. Skip anything that is not a regular file owned by `nagios` (checked with `lstat`; symlinks are
   never followed) or is larger than 2 KB. Record `discarded_malformed` and delete it.
2. Parse strictly (`json.loads`, exactly the expected keys and types, same character and length
   rules as the handler). Anything else: `discarded_malformed`, delete.
3. State type not `HARD`, or a recovery (state `OK` or `UP`): delete the file, write nothing (a soft state "produces none"). Found in the lab run: a HARD recovery is also a HARD event, and without this rule it ran the action when the service came back.
4. Build `Event_Key = sha256(kind|host|service|state|last_change)`.
5. Find enabled actions whose scope matches. None: delete the file, write nothing.
6. For each action: if a row with the same `Event_Key` and `Action_Id` exists, count it as `duplicate`
   and do not run again. Otherwise check the **cooldown** (last run of this action for this host and
   service) and the **hourly cap** (runs of this action in the last hour). A failed check writes a
   `skipped_*` row with the reason and does not run.
7. Otherwise insert the row with `Outcome=running` and commit, **then** delete the spool file, **then** run
   the action type with its timeout, then update the row with the outcome. If PinPoint stops in the
   middle, the next start marks every leftover `running` row `interrupted` and never runs it again.
8. Write one line to the activity log per executed run (no output text, no parameters).

Failures never crash the job: each file is handled in its own `try`, with `db.session.rollback()` on
error.

### 3.6 API

New module `server/app/api/system/remediation.py`, banners and docstrings as required by the
engineering standards.

| Route | Permission | Purpose |
|---|---|---|
| `GET /api/system/remediation/action-types` | `remediation.view` | Types with their parameter schema, for the form |
| `GET /api/system/remediation/actions` | `remediation.view` | List actions |
| `POST /api/system/remediation/actions` | `remediation.manage` | Create; 400 with per-field errors |
| `PUT /api/system/remediation/actions/<id>` | `remediation.manage` | Update with `version`; 409 when stale |
| `DELETE /api/system/remediation/actions/<id>` | `remediation.manage` | Delete (run rows remain) |
| `GET /api/system/remediation/runs` | `remediation.view` | Paginated, filters: action, host, outcome, date range |
| `GET /api/system/remediation/runs/<id>` | `remediation.view` | Detail for the drawer |

Creating, updating, enabling, disabling or deleting an action regenerates the Nagios config through
`regenerate_and_apply_config_status()`; a rejected config rolls the change back and returns 422.

*Deviation from the issue text:* two permissions (`remediation.view`, `remediation.manage`) instead
of one, so an operator can read the log without being able to define actions. Both are seeded in
`seed.py`; the Administrator role gets both. This is a decision for the reviewer.

### 3.7 Web interface

A **Remediation** page (`client/src/pages/RemediationPage.tsx`, components in
`client/src/components/remediation/`), added to `App.tsx`, `Sidebar.tsx` and `pageAccess.ts`
together, with `PageAccess.test.tsx` and `App.test.tsx` updated.

- Action list with an enable switch per row and a clear banner: "Actions run automatically when a
  service reaches a hard failure."
- Add/edit form generated from the action type's schema, showing server messages against the right field.
- Run log with filters, pagination and a detail drawer; skipped runs show their reason.
- Loading, empty, error and 403 states everywhere.

## 4. Security review: each threat, the control, the test

(T1 to T12 are the rows in `Event_Handler_Security_Review.md`.)

| # | Threat | Control in this design | Test that proves it |
|---|---|---|---|
| T1 | Someone else forges a spool file | Folder `nagios:pinpoint` 2770, not group `nagios`; consumer requires file owner `nagios`, regular file, and treats content as untrusted | Unit: wrong owner, symlink, directory, oversized file are discarded. Lab: `www-data` cannot list or write the folder |
| T2 | Handler replaced | `/usr/local/sbin`, `root:root` 755 (installer) | Installer check; lab `stat` and write attempts |
| T3 | Shell injection through Nagios macros | Single-quoted macros, handler argument validation, no shell in the handler | Unit: hostile host and service names (`;`, `$(`, backtick, quote, newline) are rejected by the handler and the consumer; config test shows the quoting |
| T4 | Injection through action parameters | Typed schemas, no command or path parameters | Unit: hostile input for every parameter returns 400 |
| T5 | sudo privilege | None added in this issue (`record_only` needs none) | `sudo -n -l -U pinpoint` unchanged in the lab report |
| T6 | Restart loop | Cooldown and hourly cap per action; (#155 adds the kill switch) | Unit: repeated events are skipped with a reason |
| T7 | Spool flood | Handler stops writing at 1000 files; consumer processes at most 200 per run | Unit: 5000 files, bounded work |
| T8 | Secrets in rows, logs, responses | Output limited to 1 KB and redacted; no parameters in log lines; `record_only` has no output | Unit: a secret-like string never reaches a run row or log |
| T9 | Duplicate or replayed events | `Event_Key` unique per action; `running` rows become `interrupted`, never re-run | Unit: replay, and a simulated crash between steps 7 and 8 |
| T10, T11 | Wide `nagios` group rights | D1, installer-side | Installer instructions Fix A and B |
| T12 | Remote restart | Not shipped (D2) | n/a |

## 5. Test plan

- **Backend unit:** handler argument validation (valid, hostile, too long); spool parsing (valid,
  malformed, oversized, duplicate, wrong owner, symlink); consumer decisions (SOFT ignored, match,
  cooldown, cap, duplicate, interrupted); parameter validation per type; template output with and without
  actions; byte-identical default config; migration up and down; permission seeding.
- **Backend API:** permissions (403), 400, 409, 422 on apply failure, run filters and pagination.
- **Frontend:** form generated from schema, server validation shown per field, enable switch, log
  filters, permission guard, navigation and page access.
- **Cross-platform:** the handler path check is Linux-only like the email script; tests that compare
  whole generated files use the existing `plain_alert_email` style fixture so Windows and Linux agree.
  CI (Linux) is the combined check.
- **Lab:** deploy to the lab appliance, create a `record_only` action for one lab service, force a
  hard failure and recovery with passive results while that service's notifications are off, and check
  exactly one run row, a SOFT state with none, the cap and cooldown skips, and the permissions in the
  security review. Needs the installer fixes C and D applied on the appliance first (done by hand
  for the lab, recorded in the lab report).

## 6. Questions for the reviewer

1. One file per event instead of one appended line (3.1). Accept?
2. Two commands (service and host) instead of one (3.2). Accept?
3. `remediation.view` and `remediation.manage` instead of one permission (3.6). Accept?
4. `RemediationRun` in `system.db` (3.3), pruned by the existing retention job. Accept? (Changed from `history.db`: the standards reserve that for Nagios snapshots.)
5. Anything in section 4 that should be tested differently before it can be signed off?

## 7. Build order once the design is approved

1. Migration, models and the action registry with tests.
2. Handler script and consumer with tests (the security-sensitive part).
3. Config rendering in `create_host` / `create_service` with the byte-identical proof.
4. API routes and permission seeding.
5. Frontend page, route, navigation, tests.
6. Specs, lab run, report.

## 8. What was built and seen live (for the security review and the installer)

Status after the build and two lab runs on 2026-10-15
([first](../test-runs/2026-10-15-issue-120-event-handler/REPORT.md),
[second](../test-runs/2026-10-15-issue-120-service-and-spool/REPORT.md)). The security review and the installer
instructions live on the docs branch of PR #157, not in this branch; these are the points to carry into them.

| Threat | What was observed live |
|---|---|
| T1 forged spool file | A valid-looking event owned by `pinpoint`, a non-JSON file, a 3000-byte file and a symlink were all discarded with a warning that carries no file content; the symlink target was untouched. `www-data` could neither list nor write the spool folder |
| T2 handler replaced | `/usr/local/sbin/pinpoint-event-handler` is `root:root` 755; `www-data` could not modify it |
| T3 injection through macros | `nagios -v` accepted the generated commands (0 warnings, 0 errors). Every macro is single-quoted, and the appliance keeps Nagios's default `illegal_macro_output_chars` (`` `~$&|'"<> ``), which the installer must not change |
| T5 sudo | No sudo rule was added; `pinpoint` can still run only `pinpoint-apply-smtp` and `systemctl reload nagios` |
| T6 restart loop | A repeat inside the cooldown was skipped (`skipped_cooldown`) and a run past the hourly limit was skipped (`skipped_hourly_cap`), each with its reason |
| T7 flood | Unit tested only (5000 files, bounded work) |
| T8 secrets | A planted `password=hunter2` in a spool file never reached a run row or the service journal |
| T9 replay | A copy of a real event produced no second run |
| T10, T11 wide `nagios` group rights | Not changed here; installer work (Fix A and B in the installer instructions) |
| T12 remote restart | Not shipped (D2) |

Rules found during the build:

- A HARD recovery (`OK` or `UP`) is also a HARD event. The consumer ignores it, so an action reacts only to problems.
  The first lab run showed the bug (a recovery produced a run row); it was fixed test-first and re-run.
- A passive result is hard on the first result for a service (hosts are hard too), so a live SOFT state needs an
  active check that really fails; SOFT is unit tested only.

For the installer: create `/usr/local/nagios/var/spool/pinpoint-events` as `nagios:pinpoint` with mode 2770 (its
parent is root-owned), install the handler script from `server/scripts/pinpoint_event_handler.py` as
`/usr/local/sbin/pinpoint-event-handler` (`root:root`, 755) and keep `enable_event_handlers=1` and the default
`illegal_macro_output_chars`. The `pinpoint` service user must be in group `pinpoint`.

### Checking the page by hand

Not yet done in a browser on the lab (no login was available to the agent). With an account that has
`remediation.view` and `remediation.manage`:

1. Open Remediation in the sidebar: the banner "Actions run automatically when a service reaches a hard failure"
   and the action `lab-120-record-only` (host `dev-0abb55`) are shown, with its switch on.
2. Run log tab: five rows for that host (one `Succeeded`, one `Skipped (cooldown)` for the early recovery that
   ran before the fix, `Succeeded`, `Skipped (cooldown)`, `Skipped (hourly limit)`) plus one for the test service.
   Open one: the drawer shows the state, outcome, reason and, for a run, the output `recorded`.
3. Turn the switch off and on again: each change is accepted and the page shows the new state after a reload.
4. Add action with a name of two letters: the message appears under the Name field and the dialog stays open.
5. With an account that has only `remediation.view`: no Add, Edit or Delete, and the switch cannot be toggled.
