# Test run: issue-274-appliance-ip-persistence

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila |
| Controller and documentation revision | `da59d88b`; application revision on the owner's VM not observed |
| Plan | [Defense demo lab](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor | Owner configured cloud-init and rebooted the appliance; AI-assisted ping observation |
| Environment | Owner's `Pinpoint-Final`, Windows VM and laptop Docker pilot on `10.77.1.0/27` |
| Raw evidence | Owner's confirmation, shared screenshot and console observations; no raw log retained |

## Result

**Partial.** The owner confirmed creating the cloud-init network-disable file
and rebooting `Pinpoint-Final` before registering Windows. After that report,
Windows ping to the appliance's intended `.1` address passed. This corroborates
reachability after the reported reboot, but the guest file and guest interface
were not independently inspected. A screenshot shows an Average Resource card
with memory 47.7%, CPU 0% and disk 45.6%; the image alone does not establish
which devices contributed. The checked-out Network Health source uses NCPA
trend values for that card; the running appliance revision was not confirmed.
No QA catalog or E2E cases are claimed.

| Check | Result | Observation |
|---|---|---|
| Cloud-init configuration and reboot | Owner confirmed | The owner reports both actions completed; no independent guest file read. |
| Post-reboot appliance reachability | Pass | Windows ping to `10.77.1.1` returned replies. |
| Pinpoint resource card | Observed | Shared screenshot displays aggregate values; attribution to Windows is unconfirmed. |
| Windows NCPA registration and metric | Partial | Owner reports registration; a device-specific metric in Pinpoint remains to be confirmed. |
| Service alert and recovery | Not run | Pinpoint monitoring integration remains pending under [#274](https://github.com/esfen14/Pinpoint/issues/274). |

No passwords, tokens, private keys, communities or addresses outside the
lab range are included.
