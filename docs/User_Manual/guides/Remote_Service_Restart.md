# Remote service restart

Remote restart lets a remediation action restart one service on the monitored
Linux device where a HARD failure occurred. It uses the NCPA deployment account,
a confirmed SSH host key and the deployment key. Administrator passwords are used
only for deployment or cleanup and are never stored by this workflow.

## Configure a device

1. Open **NCPA Deployment** with the `system.deploy.ncpa` permission. Verify the
   device's SSH host key through the normal deployment wizard before trusting it.
2. On that device's row, choose **Remote restart**. Enter one service name per
   line (for example `apache2` or `ncpa`, at most 20). You can save the list with
   remote restart off before deploying. An empty list allows nothing.
3. Deploy NCPA using an administrator login you control. Deployment installs the
   root-owned `pinpoint-service-restart` helper, its restricted sudo rule and
   `/etc/pinpoint/restartable-services` on the device.
4. Return to **Remote restart**, enable **Allow remote service restart**, and save.
   Enabling requires a confirmed fingerprint and an installed deployment key.

A device deployed before this feature needs **Clean up**, then an NCPA redeploy
to receive the helper. Changing the allowed service list also requires cleanup
and redeployment: saving settings changes Pinpoint's copy; only a deployment
with device administrator credentials can update the device's root-owned copy.
Clean up is available on trusted failed and deployed devices. It removes the
Pinpoint bootstrap key, helpers, sudo rules and restart list, and stops remote
restarts until successful redeployment. It does not uninstall NCPA or remove its
monitoring token. Leave account removal unchecked unless you also intend to
recreate the deployment account. Review every cleanup step; retry an incomplete
cleanup before redeployment. The saved service list remains in Pinpoint.

## Configure an action

Open **Remediation** with `remediation.view` and `remediation.manage`. Add or edit
an action, choose **Restart a service on the monitored device**, and enter the
**Service to restart**. Choose a host/service pattern, cooldown and hourly limit.
Enable the action when ready. The device comes from the failing Nagios host;
the form cannot redirect a restart to another address.

The service name must be plain (letters, digits, dots, underscores, @ and dashes;
start with a letter or digit, at most 63 characters). The service must appear in
both Pinpoint's per-device list and the device's own list. For local restart,
**Service to restart** instead offers only the units returned by the API.
Switching action types clears the previous type's parameters.

## Refusals and run history

Only an Active, unpaused, trusted device with remote restart enabled is eligible.
Maintenance Mode, cooldown and hourly limits also block execution. A changed SSH
host key stops the connection; verify the device's identity before confirming a
replacement key. Do not bypass the fingerprint warning to make a restart work.

The run log records successes, failures, timeouts and limit skips. Command output
and exception text are not exposed; outcomes use fixed messages and exit codes.
A timeout closes Pinpoint's SSH connection; it does not guarantee systemd cancels
an already submitted restart. Check the device before manually retrying.

Deleting an action keeps its run names and outcomes, clears their action link,
and prevents a newly created action from inheriting the deleted action's
cooldown or hourly history. The upgrade migration also clears links whose action
no longer exists, keeping their audit data. Previously reused IDs cannot be
reliably attributed retroactively; the migration retains links to existing IDs.
Back up the databases before upgrading. Downgrading removes the foreign-key
constraint but cannot restore cleared links.
