# Pinpoint monitoring demo checklist

Status: **partially verified on the connected appliance**. The owner reports
Windows NCPA checks OK and observed web03 HTTP move from OK to CRITICAL and
back to OK when its service was stopped and restored. The owner also reports all fifteen demo addresses visible and Windows
memory 47.5944%, CPU 0.0853%, and disk 45.6%. Individual UI rows,
alert-notification timing and full rehearsals still need evidence. See [presenter setup](PRESENTER_SETUP.md) and the
[web test report](../../docs/test-runs/2026-10-27-issue-274-pinpoint-web-alert/REPORT.md).
The separate network connectivity test remains ping-only.

## Prepare

1. Start the pinned Linux pilot with `./demo/demo presenter up` and check
   `./demo/demo presenter status`. All fourteen containers should show their
   intended addresses and baseline services. Windows should be running at
   `10.77.1.3`, and the appliance should use `10.77.1.1/27` on `vboxnet1`.
2. In Pinpoint, review the discovery networks and port settings before any
   product discovery. The intended defense segment is `10.77.1.0/27`; exclude
   physical and VPN networks. Preserve or record existing settings and disable
   unattended discovery while making changes. Discovery itself is a product
   scan; a ping reply alone does not prove discovery or monitoring.
3. Once the bounded discovery scope is approved and run, compare Device
   Inventory with [the catalog](manifest.json): 14 Linux devices and Windows,
   excluding the appliance. Record missing, duplicate or unexpected devices.
4. In Plugin Manager, inspect the applicable enabled plugins and resulting
   monitoring checks. `check_http` is needed for the web example; other
   services may need their own plugin and settings. SNMP and PostgreSQL require
   configuration before a working check can be claimed. Windows NCPA requires
   the manual registration and token described in the setup guide.

## Service failure and recovery

1. With `web03` at `10.77.1.4`, confirm its HTTP check is healthy in Pinpoint.
2. On the laptop, run `./demo/demo presenter break web03 http`. The HTTP and
   HTTPS services both stop because they share nginx. The host remains running,
   so its `host_check/ping` can stay OK; inspect the HTTP service check on
   port 80 for the failure.
3. Observe the check and alert in Pinpoint. Record the time to a confirmed
   failure; checks and retries may delay the visible alert.
4. Run `./demo/demo presenter fix web03 http`. Observe the check recover and
   the alert clear. Record the recovery time.
5. Always restore the service even if a check fails. Use `presenter up` to
   restore all baseline services and reserved DHCP leases if needed.

Repeat the full demonstration from a clean baseline before relying on it.
Avoid treating the local presenter service state, or a ping reply, as proof that
Pinpoint discovery, Nagios checks, alerts, or NCPA registration succeeded.
