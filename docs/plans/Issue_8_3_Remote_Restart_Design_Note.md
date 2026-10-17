# Issue #8 Part 8.3: remote service restart, design note

Status: ACCEPTED 2026-10-16 (option A, second fixed helper; extra privilege on monitored devices approved; redeploy of existing devices accepted).
Branch for the work: a new branch off the Part 8.1 branch (see "Sequencing").

## 1. What exists today (verified in source)

All references are to `server/app/ncpa_deployment/ncpa_deployment.py`.

| Item | What the code does |
|---|---|
| Account | `pinpoint-deployment`, created with `useradd -m` (no sudo group). |
| Key | PinPoint's private key `~/.ssh/pinpoint_ncpa_deploy` of the service user; the public key is appended to the account's `authorized_keys` (mode 600). |
| Host trust | `connect_with_fingerprint_check` re-reads the live host key, compares it with the stored `SSHCredentials.Key_Fingerprint` using `hmac.compare_digest`, then connects with `RejectPolicy` and a known-hosts entry for the pinned port. A mismatch returns `host_key_changed` and no login is attempted. |
| Sudo rule | `/etc/sudoers.d/pinpoint-ncpa-deploy`: `pinpoint-deployment ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-ncpa-deploy`. Validated with `visudo -cf`. Exactly one command is allowed, with no wildcard. |
| Helper | `/usr/local/sbin/pinpoint-ncpa-deploy`, root:root 755, so the deployment account cannot edit it. It takes one argument that must match `^[a-f0-9]{32}$`. |
| What the helper does | Installs and configures NCPA (apt, GPG key, ncpa.cfg edits, TLS cert) and runs `systemctl restart ncpa` as one step. It has no service-name input. |

## 2. Finding

The current rule does not allow restarting any service on demand.

- The only privileged command is the NCPA installer, and its only input is a hex token.
- Re-running it would restart `ncpa`, but it also reinstalls and reconfigures NCPA, rewrites the community string and needs apt and network access. That is a repair, not a restart, and it can only ever touch `ncpa`.
- Nothing else is reachable: the account has no general sudo, so `sudo systemctl restart X` is refused.

So Part 8.3 cannot be built on the existing rule. A remote restart needs a new privileged capability on every monitored device. That is the security decision the issue flags.

## 3. Options

### A. Second fixed helper, `pinpoint-service-restart` (recommended)

- A new root-owned script, installed beside the first, plus a second sudoers line: `pinpoint-deployment ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-service-restart`.
- The helper takes one argument and checks it against an allowlist file on the device (`/etc/pinpoint/restartable-services`, root-owned, 644). Only then does it run `/usr/bin/systemctl restart -- <unit>` through an argument list, with no shell.
- The device is the last line of defence. A compromised PinPoint server can still only restart units an administrator has listed on that device.
- PinPoint also keeps a per-device allowlist in its database (the issue requires this). The two lists must agree, and the device list wins.

### B. Sudoers rule naming each unit

- `NOPASSWD: /usr/bin/systemctl restart nagios.service`, one line per unit.
- No new script. But sudoers argument matching is easy to get wrong (an unquoted wildcard or extra arguments), and the rule file has to be rewritten whenever the allowlist changes.

### C. Re-run the NCPA helper

- Rejected. It restarts only `ncpa` and rewrites configuration as a side effect.

Recommendation: **A**. It has one reviewed code path on the device, no wildcards in sudoers, and an on-device allowlist that bounds what a compromised server could do.

## 4. Proposed PinPoint side (only if A is accepted)

- Action type `restart_remote_service` with params `device_id` and `unit`. The registry stays the single place that builds the command, as for `restart_local_service`.
- Per-device allowlist and an administrator-controlled enable switch stored per device. This needs a model and a migration.
- Run order, stopping at the first failure and recording why:
  1. Device exists, is Active (not Retired, Merged or Missing), and is not paused.
  2. Maintenance Mode, cooldown and the hourly cap, shared with Part 8.1.
  3. The action is enabled for the device and `unit` is on its allowlist.
  4. A trusted fingerprint and pinned port exist (`query_trusted_host`).
  5. `connect_with_fingerprint_check` with the deployment key. A changed fingerprint stops the run and is recorded as such.
  6. `sudo -n /usr/local/sbin/pinpoint-service-restart <unit>` with a timeout. The unit is validated against a strict pattern before it reaches the command.
- Output is truncated and never contains the key path contents, the token or credentials.

## 5. Open questions for a person to decide

1. Is expanding privilege on every monitored device acceptable (a second helper and sudoers line)? If no, Part 8.3 stays blocked and Issue #23 remote services stay out.
2. Option A or B?
3. Who installs the new helper on devices already deployed? The installer repo has the local sudoers work (see `Installer_Handoff.md`), but device-side installation is done by this repo's NCPA deployment code. Existing devices would need a redeploy step.
4. Where does the on-device allowlist come from? Proposal: written by the same deployment step from the per-device allowlist an administrator sets in PinPoint.
5. Is "paused" a device field or a monitoring state? Check `Device_Monitoring_State_Plan.md` before coding step 1 above.

## 5a. As built (2026-10-16)

- Option A as designed. Code: `server/app/remote_restart.py`; action `restart_remote_service`; migration `c7a1f4d92e60` (enum value, `SSH_CREDENTIALS.Remote_Restart_Enabled` and `Remote_Restart_Services`); settings route `GET`/`PUT /api/system/deployment/ncpa/<id>/remote-restart` under the existing `system.deploy.ncpa` permission.
- The helper, its sudoers line and the device's list are installed by the NCPA bootstrap (`give_program_permissions`) for every deployed device; an empty list allows nothing. Cleanup removes them.
- **Changing a device's list needs a redeploy with the administrator's password.** Only root can write the list on the device, which is the point of keeping it there. The route reports `redeploy_needed`. Choosing the list when enabling avoids repeating it.
- Paused means `Include_Device_In_Scanning` is false (Device Inventory spec).
- The device is found by `NetworkDiscovery.Nagios_Host_Name` equal to the event's host.
- #182 owner decision (2026-10-17): include the device settings dialog and remediation `unit` field; support cleanup on trusted deployed devices with a redeployment warning. `RemediationRun.Action_Id` becomes a nullable foreign key with `ON DELETE SET NULL`, preserving snapshots and separating replacement-action limits.

## 6. Verification plan

- Unit tests with SSH mocked: fingerprint mismatch, non-Active and paused device, unit not on the allowlist, action not enabled, timeout, no secret in output.
- Security review of the remote command construction and the helper script.
- VM-lab run against a target, recorded in `docs/test-runs/`.

## 7. Sequencing

Part 8.1 is unmerged. Part 8.3 should go on its own branch after the 8.1 PR is open, with its own migration parented on whatever head is current, to avoid another multiple-heads failure.
