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
| P117-04 | Single-parent gateway and two children initially UP; power off gateway, then observe gateway DOWN and children UNREACHABLE. Capture Nagios notification events; children must not emit DOWN notifications. |
| P117-05 | Redundant parents initially UP; power off one parent and explicitly activate the alternate route. A reachable child remains UP. Power off both and observe UNREACHABLE; capture notifications. Parent declarations alone do not provide network failover. |
| P117-06 | Pause one selected parent: stored edges remain, generated directive contains only eligible parents, response explains omission. Pause both: directive absent, real Nagios validation succeeds. |
| P117-07 | Merge/retire a parent, verify graph rewiring/cleanup and real Nagios validation; invalid merge cycles are refused atomically. |
| P117-08 | Frontend tests cover both editor placements, read-only/search/set/change/clear/error/empty/loading, real-data node/edge selection and fixed hierarchy; existing Inventory/drawer regressions pass. |
| P117-09 | Full `scripts/verify.sh all` and PR CI pass; retain output. |

Record observed outcomes in a sanitized `docs/test-runs/` report from its template.
Do not treat a scripted check result as a browser walkthrough or SMTP delivery.
