# Issue #349: NCPA Deployment wizard says port 22 for devices using another SSH port

Branch: `issue-349-wizard-ssh-port`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] The three messages show the device's actual SSH port, or name no port when it is not known.
- [ ] A frontend test covers a device on a port other than 22.
- [ ] `scripts/verify.sh all` passes.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Credential check message names the device's port | 1 | NcpaDeployWizard.test.tsx |
| Host key loading message names the device's port | 1 | NcpaDeployWizard.test.tsx |
| Host key unreachable message names the device's port | 1 | NcpaDeployWizard.test.tsx |
| Port matches the one the backend connects to (pinned, else recorded) | 1 | test_ssh_port.py |
| Test on a non-22 port | 2 | NcpaDeployWizard.test.tsx |
| Verification | 3 | scripts/verify.sh all |

## Plan

1. [x] `server/tests/unit/test_ssh_port.py`, then `server/app/api/system/ncpa_deployment.py`: the device list returns `ssh_port` (pinned port for a trusted device, else `device_ssh_port()`).
2. [ ] `client/src/test/NcpaDeployWizard.test.tsx`, then `client/src/types/ncpaDeployment.ts` and `DeployWizard.tsx`: the three messages use the device's port, or none.
3. [ ] Specs: `spec files/Backend_Modules_and_Routes.md` (list route), `Frontend_Modules_and_Routes.md` if it describes the wizard messages.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Device list returns `ssh_port` | `scripts/verify.sh backend` | green, 4498 passed |

## State for the next session

- Last check run (exact command): `scripts/verify.sh backend`
- Result (first failing lines, or "green"): green
- Hypothesis: n/a
- Next action (one specific step, not "continue"): add the failing wizard test for a non-22 port (plan step 2).

## Decisions and notes

- The issue has no comments; the body is the whole request.
- `ssh_port` is the port Pinpoint connects to, including the `SSH_PORT` fallback when no SSH port is recorded (same rule as the fingerprint route). The wizard names no port only when the response carries none.
- No change under `app/network_discovery/` or `app/ncpa_deployment/`.
