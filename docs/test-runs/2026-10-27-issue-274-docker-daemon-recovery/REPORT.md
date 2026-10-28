# Test run: issue-274-docker-daemon-recovery

| | |
|---|---|
| Date and time | 2026-10-27, Asia/Manila; Docker active since 20:51:06 |
| Controller revision | `4ce0dedf` in the persistent presenter checkout; the later `c68dfc70` checkpoint changed progress only |
| Plan | [Defense demo lab](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor | Owner initiated daemon restart and presenter up; AI-assisted read-only status and ping checks |
| Catalog | `manifest.json` SHA-256 `7a2ab626fb66bc71ff660347fd6ba8d118d2c67e600041c84575fa7d47fdc1f8` |
| Environment | Laptop Docker, VirtualBox Windows and host-only `10.77.1.0/27` pilot |
| Restoration | All 14 pilot containers running, baseline services running and all five reserved leases present |
| Raw evidence | User acknowledgement and console observations; no raw log retained |

## Result

**Partial issue acceptance.** The owner reported restarting Docker and running
`presenter up`; systemd reports the daemon active since 20:51 and container
start times are after that. Presenter status reported all fourteen containers,
and Windows pinged every Linux target successfully. A laptop reboot and the
complete Pinpoint demo remain untested. No product QA or E2E case credit is
claimed.

| Check | Result | Observation |
|---|---|---|
| Docker daemon restart | Pass | Owner reported completion; systemd reported Docker active with new start time. |
| Pilot startup and DHCP | Pass | Fourteen targets running; DHCP clients had `.20` through `.24`. |
| Windows to Linux reachability | Pass | One successful ping to each of the fourteen Linux target addresses. |
| Appliance address reachability | Inconclusive | `Pinpoint-Final` was running and attached to `vboxnet1`, but Windows received no ping reply from expected `10.77.1.1`. Guest address and firewall were not observed. |
| Laptop reboot | Not run | Restart recovery after a host reboot is not established. |
| Pinpoint monitoring | Not run | Appliance configuration and Windows registration need follow-up in issue [#274](https://github.com/esfen14/Pinpoint/issues/274). |

The user's selected appliance is `Pinpoint-Final`; it is distinct from the older
`pinpoint-qa-appliance`. Local NCPA registration tests in the checked-out source
passed for both eligible and non-eligible devices, but they do not prove the
running appliance's registration or connectivity.

No passwords, tokens, private keys, community values or addresses outside the
lab range are included.
