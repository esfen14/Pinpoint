# NCPA deployment and failed-install cleanup

The issue #129 build tracks each installed agent's listener port and adds explicit
cleanup of failed deployment bootstrap artifacts. Process-secret transport and
installer-compatible atomic resource updates are still unfinished; this build is
not ready for production security sign-off.

## Deploy and track an agent

Open **NCPA Deployment** with `system.deploy.ncpa`. Confirm each device's SSH host
key and enter credentials in the deployment wizard. Enable `check_ncpa` in Plugin
Manager to monitor its agent metrics. Deployment records the configured
`NCPA_PORT` in `NCPADeployment.Port`; checks, disk and identity probes, relocation
and port protection use that installed port. A missing stored port uses the
configured default. Changing the default does not change existing listeners.
There is no re-port control in this build.

Back up both databases before upgrading. From the installed `server` environment,
run `flask db upgrade` and `flask sync-permissions`, then restart the backend.
Migration `7db78f308ee5` backfills deployed agents with the configured legacy port;
make sure that setting matches the ports of existing agents before migration.
The migration handles both binds and can downgrade by removing the Port column.
No new permission is introduced by cleanup.

## Clean up a failed deployment

On a trusted device showing **Deployment Failed**, select **Clean up**. The dialog
lists the deployment key, sudo rule and helper that will be removed. Review the
saved SSH fingerprint, enter an SSH login with sudo access, and optionally choose
to remove the deployment account. The backend checks the live key again before
running any command. If it changed, confirm trust through the deployment wizard
before retrying.

Select **Run cleanup** and read each step's result. The optional account removal
runs only after the other artifacts were successfully removed. Complete cleanup
returns the device to **Pending NCPA** so it can be deployed again. Incomplete
cleanup keeps **Deployment Failed**; review the failed steps before retrying.
Credentials clear after the request and when the dialog closes. The list refreshes
without a page reload. Cleanup does not uninstall NCPA and is unavailable for
healthy deployed agents, untrusted devices or a running deployment.

## Administrator note: secret storage and outstanding requirements

Custom-check passwords remain encrypted in the application database using the
fixed `PINPOINT_SECRETS_KEY` or `SECRET_KEY`. Do not change that key without a
recovery plan. NCPA tokens remain in `NCPADeployment.Token` on the system bind.
During generation, check secrets are written to the owned block of
`NAGIOS_RESOURCE_CFG` (default `/usr/local/nagios/etc/resource.cfg`). Host config
contains USER macro references; Nagios history snapshots retain command names
without arguments. Do not publish resource files or raw check transcripts.

The resource file must retain `nagios:nagios` ownership and mode 0660. The generated
and successfully applied live hosts file uses 0640 with its existing owner/group.
Atomic updates require a supported ownership-preserving installer mechanism;
ordinary group write permission is insufficient. The current writer refuses
unsafe permissions or an update that cannot preserve ownership. Config generation
and application restore previous resources on failure or cancellation.

Nagios expands macros into the plugin's arguments. The current NCPA/SMB plugins
need a secure credential input or reviewed adapter; some C plugins support
`--extra-opts`. Until that work and the required lab cases are complete, process
secrecy is not achieved. The implementation and installer handoff are tracked in
[the transport plan](../plans/Issue_129_Check_Secret_Transport.md).
