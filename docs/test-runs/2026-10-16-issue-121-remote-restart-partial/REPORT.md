# Test run: issue-121-remote-restart-partial

| | |
|---|---|
| Date | 2026-10-16 |
| Commit tested | `f7905202` (branch `issue-8-3-remote-restart`, Part 8.3), applied as a patch on top of `main` at `8869235`. The migration chain at that time ended at `b8e3d5f2a417`; the branch has since been re-parented onto `d117f3b8a053` and has not been re-run on the lab |
| Plan | Issue #121 (`docs/issues/issue-008.md`) Part 8.3 acceptance criteria; design in `docs/plans/Issue_8_3_Remote_Restart_Design_Note.md` |
| Tester | Claude Code agent for the project owner, who approved running this on the lab |
| Environment | Same lab appliance as `2026-10-16-issue-121-local-restart`, with the 8.3 patch applied to the checkout (uncommitted there), migration `c7a1f4d92e60` applied to both databases and the service restarted. Four Linux devices were in the inventory; none had the NCPA deployment key installed, and no administrator login for any of them was available |
| Raw evidence | On the appliance: the journal of `pinpoint-gunicorn` and the `REMEDIATION_RUN` table. Not committed |

## Result

**Overall: Partial.** Everything that does not need a deployed device passed: the per-device settings routes, input validation, the action type, and live refusals for an untrusted device and for Maintenance Mode. The criteria that matter most for sign-off were **not** exercised, because no device with the helper and deployment key was available: a successful remote restart, a changed host-key fingerprint stopping the run, a service missing from the device's list, an SSH timeout, and a paused device. The on-device helper script and its sudoers line were never installed or run on a real device.

Totals: Pass 28, Fail 0, Blocked 5, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| Settings routes need a login | Pass | `GET` and `PUT .../remote-restart` returned 401 without a session | |
| Settings for an untrusted device | Pass | `GET` returned `enabled: false`, no services, `trusted: false` | |
| Unknown device | Pass | 404 on `GET` and `PUT` | |
| Turning it on for an untrusted device | Pass | 409 "The device must be trusted and deployed before remote restart can be turned on." | |
| Bad `PUT` bodies (10 cases) | Pass | 400 for non-boolean `enabled`, an unknown field, shell characters, a path, a space, a leading dash, a non-list, a non-string item, an empty name and more than 20 services; nothing was saved by any of them | |
| Action creation validation (8 cases) | Pass | 400 for `unit` with shell characters, a path, a space, empty, missing, a list, a leading dash, and an extra `device_id` parameter | |
| Action type is offered | Pass | `restart_remote_service` is listed by the action types route | |
| Live run on an untrusted device | Pass | Forced HARD DOWN: one run, `failed`, "Refused: the device is not trusted for remote actions."; no SSH attempt; no key, password or key path in the output | |
| Live run in Maintenance Mode | Pass | Run `failed`, "Refused: Maintenance Mode is on." | |
| Migration `c7a1f4d92e60` on the live databases | Pass | Applied to both databases from `b8e3d5f2a417` | |
| A restart runs only on a trusted device with a matching fingerprint | Blocked | No device with the deployment key | |
| A changed fingerprint stops the run and is recorded | Blocked | Needs a trusted device and a way to change its host key | |
| A service not on the device's list is refused | Blocked | Needs an enabled, trusted device | |
| SSH timeout | Blocked | Needs a trusted device | |
| Paused device refused | Blocked | Needs a device in the inventory with scanning turned off and the action enabled for it; also not reached | |

(The totals count the individual validation cases in the grouped rows.)

## Deviations from the plan

- The plan's lab run "against a target" was not possible: deploying the helper needs the device's administrator SSH login, which was not available and was not guessed.
- Two of the agent's helper scripts failed to turn Maintenance Mode off (a stale settings version), which made two early results misleading. They were redone with the setting re-read to confirm it, and Maintenance Mode was verified off at the end.

## Follow-up

- Repeat this run against a device with the NCPA deployment installed, covering the five blocked cases and the helper script on the device.
- Re-run the migration step on the lab with the re-parented migration (`d117f3b8a053` is its parent).
- The security review of the remote command construction and the helper script is still outstanding (Engineering Standards "Sensitive modules").

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
