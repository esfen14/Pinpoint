# Test run: issue-350-lab-apt-lock

| | |
|---|---|
| Date | 2026-11-26; times are UTC, from the host |
| Commit tested | `b7762c34` for both completed live checks and the reset; `18b58b4e` for the interrupted attempt |
| Plan | Finish condition of [issue #350](https://github.com/esfen14/Pinpoint/issues/350) |
| Tester / executor mode | AI-executed (Claude Code) shell commands; the repository owner chose the fix location and asked for the tests |
| Catalog revision and SHA-256 | Not a queued catalog case |
| Queue / set / session / batch | None |
| Deployed application / installer revision | Application `b7762c34` (read from the appliance's checkout); installer checkout `3a97733` |
| Baseline / preflight / restoration | `qa-pinpoint-appliance`, snapshot `os-nagios-ready` restored before every check; `vmlab` preflight passed. See Restoration |
| Start / end / time zone | 03:01 to 03:54 UTC |
| Environment | Debian 13 host, VirtualBox, Ubuntu 22.04 appliance, fresh databases |
| Raw evidence | Lab host, `~/pinpoint-test-results/2026-11-26-issue-350/` (`wait-check.log`, `wait-check-install.log`, `qa-reset.log`) |

## Result

**Overall: Pass.** `demo/demo qa reset` completed with upgrades pending and no
manual step (exit 0, health check 61 passed, 0 failed). The stop script also
waited for a real automatic upgrade that was installing packages.

Not a catalog run: no TC or E2E case is claimed.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Wait for a running daily job (package list update) | Pass | `apt-daily.service` running; the script waited just over 3 minutes, then exit 0; both timers disabled, lock free, `dpkg --audit` empty (`wait-check.log`) | #350 |
| Wait for a running package install | Pass | `unattended-upgr` held `lock-frontend`, `apt-daily-upgrade.service` running; the script waited 32 minutes (03:17:53 to 03:50:06), then exit 0; the upgrade ran to its end, `dpkg --audit` empty (`wait-check-install.log`) | #350 |
| `demo/demo qa reset` | Pass | 03:50:15 to 03:54:07, exit 0, health 61/0, no wait needed, no lock error (`qa-reset.log`) | #350 |
| Upgrades pending and none started after the reset | Pass | 225 packages upgradable; both timers `disabled`; no `apt-daily` or `apt-daily-upgrade` journal entry since boot; web interface HTTP 200 | #350 |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| Daily job wait, attempt 1 | Script waits and exits 0 | Stopped about 60 s into the wait at the owner's request | Inconclusive | Log overwritten by attempt 2 | Snapshot restored by attempt 2 |
| Daily job wait, attempt 2 | Script waits and exits 0 | Exit 0 after the job ended | Pass | `wait-check.log` | Snapshot restored by the next check |
| Install wait | Script waits for the install and leaves a consistent package database | Exit 0, audit empty | Pass | `wait-check-install.log` | Snapshot restored by the reset |
| Reset | Completes without a manual step | Exit 0 | Pass | `qa-reset.log` | VM powered off afterwards |

## Deviations from the plan

- In the two wait checks the upgrade was started by hand with `systemctl`, so that
  the script had something to wait for.
- During the reset itself the script stopped the timers before any upgrade started.
  The failure in the issue (an upgrade starting by itself during the install) did
  not recur in this run; it was observed in the
  [#336 run](../2026-11-26-issue-336-demo-ncpa-deploy/REPORT.md).

## Restoration

`qa-pinpoint-appliance` is powered off with a fresh install of the issue branch.
First-run setup has not been done on it: run `scripts/vmlab setup-admin` with the QA
settings before signing in. Data from earlier runs on this disposable appliance was
discarded. The snapshot was not changed, and no container was changed.

## Follow-up

- A real new appliance meeting the same lock is untested:
  [PinPoint-Installer #20](https://github.com/lorraine-pangilinan/PinPoint-Installer/issues/20).
- Not run live: the same step in `scripts/vmlab provision` and the 60-minute wait
  limit (offline tests only). The longest wait seen was 32 minutes here; the #336
  run saw the lock held for about 37 minutes.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
