# Manual multiple-parent topology acceptance (#117)

Scope: manual reachability parents, generated Nagios definitions, real single and
redundant routed paths, and device-only React Flow panels. No discovery scan,
SMTP delivery, automatic inference or interface traffic work is required.

Use a dedicated disposable Docker project, never the shared lab or appliance.
Engine and two routers are on `10.77.0.0/29`; two children and the routers' other
interfaces are on `10.77.0.8/29`. Both are isolated internal bridges. Containers
have NET_ADMIN only for explicit static routing and forwarding. No route is added
on the host; no external devices are probed. Parent failure means powering off the
owned router container. Cleanup removes only containers/networks created for this
run. This subnet is the already-documented VM-lab range, isolated in separate
Docker bridges; no VM access is needed.

| Case | Action and required evidence |
|---|---|
| P117-01 | Run parent API, permission, graph, generation, lifecycle, real-writer rollback and populated migration regression tests; retain output. |
| P117-02 | Set two manual parents through the authenticated API; verify candidate directive with the real Nagios binary. Clear parents and verify original behavior. |
| P117-03 | Real writer validation failure and reload failure preserve graph and live config bytes; keep Nagios validation enabled. |
| P117-04 | Single-parent gateway and two children initially UP; power off gateway, then observe gateway DOWN and children UNREACHABLE. Capture Nagios notification events; at the default three attempts this trial expects no child DOWN notification. This is a scoped acceptance result, not a guarantee for every retry/cache configuration. |
| P117-05 | Redundant parents initially UP; power off one parent and explicitly activate the alternate route. A reachable child remains UP. Power off both and observe UNREACHABLE; capture notifications at the default three attempts. Parent declarations alone do not provide network failover. |
| P117-06 | Pause one selected parent: stored edges remain, generated directive contains only eligible parents, response explains omission. Pause both: directive absent, real Nagios validation succeeds. |
| P117-07 | Merge/retire a parent, verify graph rewiring/cleanup and real Nagios validation; invalid merge cycles are refused atomically. |
| P117-08 | Frontend tests cover both editor placements, read-only/search/set/change/clear/error/empty/loading, real-data node/edge selection and fixed hierarchy; existing Inventory/drawer regressions pass. |
| P117-09 | Full `scripts/verify.sh all` and PR CI pass; retain output. |

Record observed outcomes in a sanitized `docs/test-runs/` report from its template.
Do not treat a scripted check result as a browser walkthrough or SMTP delivery.

## One-attempt notification contract (#173, Option A)

Temporary child DOWN notifications before Nagios confirms parent reachability are
accepted. One-attempt monitoring remains supported; the earlier three-attempt
trial does not imply universal suppression. A parent relationship does not stop
child checking. The operator contract is in
[Device Inventory §13](../../../spec%20files/Device_Inventory_Requirements.md#13-manual-parent-devices-and-topology)
and the [notification manual](../../../docs/manuals/Notification_Policy.md#parent-outages-and-temporary-child-down-alerts).

The opt-in driver uses the same two isolated internal bridges described above.
It creates fresh containers from locally available appliance/router images,
performs real ICMP host checks with Nagios Core, powers off owned routers and
cleans up only its own resources. It does not access the shared lab, scan a subnet,
inject passive results, send SMTP or alter production configuration.

```bash
python3 server/tests/e2e/parent_reachability.py --run --output-root /tmp/pinpoint173-acceptance
```

Image prerequisites: `pinpoint-lab-appliance:latest` must contain Nagios Core
4.5.11 at `/usr/local/nagios/bin/nagios`, `check_ping`, an unprivileged `nagios`
user and `ip`; `pinpoint-issue117-routing:latest` must contain `ip` and support
forwarding. Explicit image overrides are available with `--appliance-image` and
`--router-image`; record the actual image IDs and Core version in the report.
Docker access and NET_ADMIN in the disposable containers are required. Raw
output must remain outside the repository. This runner is never run by ordinary
pytest collection, CI, installation or startup.

| Case | Required observation |
|---|---|
| P173-01 | Real Core validation succeeds; all baseline hosts have fresh active checks and HARD UP states. Record exact main/object settings, version and image IDs. |
| P173-02 | Single-parent loss immediately after a fresh parent UP check: capture child HARD DOWN and DOWN notification, then parent HARD DOWN and child HARD UNREACHABLE and its notification. |
| P173-03 | Two parents: explicitly select the alternate route, stop the first parent and observe child UP; stop the remaining parent after priming its UP cache and capture child DOWN notification followed by UNREACHABLE once both parents are confirmed unavailable. |
| P173-04 | A separate host definition for the same target without a parents directive remains HARD DOWN during the outage; restoring the selected router restores both child and no-parent host to HARD UP. |
| P173-05 | Cleanup leaves no containers or networks belonging to either trial. |

Controlled timing: the runner sets `interval_length=2`, host `check_interval=60`
(120 seconds), `retry_interval=1` (2 seconds), `max_check_attempts=1`, and both
cache horizons to 15 seconds. Per-host scheduled active checks are disabled;
forced **active** checks through the Core command FIFO control ordering. Passive
checks are disabled. A fresh parent UP result is requested just before router
power-off; child failure is processed inside that cached-UP window. Follow-up
forced checks confirm parent loss and child UNREACHABLE. This deliberately exposes
the supported quirk; it does not measure normal scheduler latency or establish a
convergence deadline. Notifications use `/bin/true` as a disposable sink, with
Core dispatch events recorded in logs; inbox receipt is outside this test.

Review `observations.json` for checked HARD states and last-check timestamps,
`state-and-notification-events.log` for dispatch ordering, `nagios.cfg`,
`objects.cfg`, `settings.json` and `validation.txt` for exact configuration, and
`cleanup.json` for removal. Preserve a sanitized run report and do not require a
new application regression test for unchanged engine behavior. The real routed
acceptance driver covers the agreed Option A classification and notifications.
