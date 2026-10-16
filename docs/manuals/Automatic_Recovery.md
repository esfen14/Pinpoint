# Automatic recovery: restarting a PinPoint host service

Administrators with **remediation.manage** can open **Remediation** in the sidebar to tell PinPoint what to do when a check reaches a hard failure. People with **remediation.view** can read the rules and the run log. Run `flask sync-permissions` after upgrading; both permissions go to Administrator, and other roles get them under **Manage Roles**.

## What PinPoint can restart automatically

The action **Restart a PinPoint host service** restarts one service on the PinPoint appliance itself. Today the only choice is **nagios**. PinPoint cannot restart any other service, and it never takes a service name from an alert or from a typed command. `pinpoint-gunicorn` (PinPoint's own web service) is left out on purpose, because restarting it would stop the process that carries out the restart.

Restarting services on monitored devices is not part of this feature (it is tracked in issue #182).

## Before you turn it on

- The appliance installer must have installed the restart permission, `/etc/sudoers.d/pinpoint-restart`, which allows `pinpoint` to run exactly `systemctl restart nagios` and nothing else. Without it the action runs but fails with "Restart of nagios failed with exit code 1."
- The event handler and its spool folder must be installed (see [`Installer_Handoff.md`](../plans/Installer_Handoff.md)). Without them no event reaches PinPoint and no rule runs.

## Create a rule

1. Open **Remediation** and choose **Add action**.
2. **Name:** 3 to 60 letters, numbers, spaces, dots, dashes or underscores.
3. **Action type:** **Restart a PinPoint host service**, then choose **nagios**. **Record only** changes nothing; it writes a line in the run log each time the rule matches, so you can see what a rule would cover first.
4. **Scope:** a host (a host reaches a hard DOWN) or a service (a service reaches a hard problem state). A service rule also needs a service pattern. Patterns may use `*`.
5. **Runs per hour** (1 to 60, default 2) and **Cooldown** (60 seconds to 24 hours, default 10 minutes) limit how often the rule can act.
6. Rules start **disabled**. Tick **Enabled** (or use the switch in the table) when you are ready.

Saving, changing or deleting a rule regenerates the Nagios configuration. If Nagios rejects the new configuration, the change is rolled back and the page shows the error.

## When a rule runs

A rule acts only when a covered check reaches a **hard** failure. Recoveries and soft states never run it. For each matching event PinPoint writes one line in the run log with the outcome:

| Outcome | Meaning |
|---|---|
| **Succeeded** | The restart command finished with exit code 0. |
| **Failed** | The restart did not happen. The reason is in the run detail, for example "Refused: Maintenance Mode is on." or "Restart of nagios failed with exit code 1." |
| **Timed out** | The restart did not finish in time. |
| **Skipped (cooldown)** | The same rule already ran for this host and service within its cooldown. |
| **Skipped (hourly cap)** | The rule already reached its runs per hour. |
| **Interrupted** | PinPoint stopped while the run was in progress. It is never run again. |
| **Skipped (kill switch)** | Automatic recovery was switched off when the failure arrived. |
| **Skipped (maintenance)** | Maintenance Mode was on. |
| **Skipped (downtime)** | The problem was in scheduled downtime. |
| **Skipped (acknowledged)** | An operator had already acknowledged the problem and the rule does not have **Run when acknowledged** ticked. |

**Maintenance Mode** (Settings, System) blocks every rule and records **Skipped (maintenance)**. Only the exit code of the restart is recorded; the command's own output is never kept, and the recorded text never contains secrets.

## Stop everything: the automatic recovery switch

The status panel at the top of **Remediation** has an **Automatic recovery** switch. Switch it off during an incident and no rule runs on the next check, with no restart needed. Every covered failure is still written to the run log as **Skipped (kill switch)**, so you can see what would have happened. Switching it off or on asks for confirmation. Changing it needs **remediation.manage**, and each change is written to the configuration log.

## Acknowledged problems

By default a rule does not act on a problem that someone has already acknowledged, because a person is looking at it. Tick **Run when acknowledged** on a rule to let it act anyway.

## Is automatic recovery working? The health panel

| Item | Meaning |
|---|---|
| **Last check-in** | When PinPoint last looked for failures to act on. It does this every 15 seconds. |
| **Events waiting** | Failures received but not handled yet. Normally 0 or close to it. |
| **Runs (24 h)** | Actions that were started in the last day. |
| **Limits hit (24 h)** | Runs refused by a rule's hourly limit. A rule that keeps hitting it points to a fault that keeps coming back. |
| **Skipped (24 h)** | Decisions that ran nothing, for any reason. |
| **Events dropped** | Failures discarded because more than 1000 were waiting. |

### What to do when it says "Automatic recovery has stopped checking in"

No failure is being handled until this is fixed. Check, in this order:

1. The PinPoint service is running and was not stopped or restarted a moment ago (wait one minute and reload).
2. The **Last problem** text. "The spool folder could not be read." means the event folder is missing or has the wrong owner; compare it with the installer handoff.
3. Free disk space on the appliance.
4. The PinPoint application log for lines starting with "Remediation:".

Until it recovers, handle failures by hand. PinPoint does not queue a restart for later. Old run records are removed after the retention period (default 90 days); event files nobody handled for 7 days are removed too.

## Release note

PinPoint can now restart `nagios` automatically when a covered check reaches a hard failure. This needs the installer's `pinpoint-restart` sudoers rule (one line, `systemctl restart nagios`, no wildcard). After upgrading, run the database migrations and `flask sync-permissions`.
