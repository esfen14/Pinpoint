# Windows Home and NCPA preparation (#274)

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila |
| Repository revision during installation | `2a0bb730716f808a937fd80818dff570b8fae360`; lab source unchanged from `00d78f10` |
| Plan | [Defense demo plan](../../plans/Defense_Demo_Lab_Plan.md), user-requested Windows preparation before the remaining controller stages |
| Executor / mode | Codex, AI-assisted VirtualBox CLI, bounded private one-time helpers and observed guest setup screens |
| Catalog / queue / credit | Not a QA catalog run; no TC/E2E or historical credit |
| Successful installation / verification window | 07:11:56–07:44:14 Asia/Manila (2026-10-26 23:11:56–23:44:14 UTC); includes guest-tools restart and setup diagnostics |
| Application / installer deployment | Existing Pinpoint appliance not started or modified; no application deployment |
| Private evidence | `~/.local/share/pinpoint-defense/windows-home/`: owner state, VM logs, screenshots, private helper copies and API observations; directories 0700, credential/configuration files 0600 |
| Final state | Owned Windows VM powered off; all other registered VMs also off; setup media detached and disk-only boot; powered-off `ncpa-ready` snapshot |

## Result

**Partial for issue #274; Windows installation and local agent preparation pass.**
Windows 10 Home build 19045 is installed, NCPA 3.5.0 returns real CPU/memory/disk
values, its process check passes, and the service starts without desktop sign-in.
This is an unactivated test installation selected by the owner after stating
that no purchased license is available. It does not pass the issue's licensed
Windows, appliance registration, fifteen-device or rehearsal finish conditions.

No product scan, Pinpoint registration, Nagios reload or appliance-to-Windows
request was performed. The proposed demo range is not approved for product
scanning merely because this isolated VM exists.

## Observations

These are setup observations, not product QA cases.

| ID | Observation | Result | Proof / limit | Issue |
|---|---|---|---|---|
| W1 | Exact-owned VM, separate persistent identity and internal-only NIC | Pass | UUID/MAC/NIC metadata rechecked under canonical host claim before mutations; other VMs left off | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W2 | Windows installation and Guest Additions | Pass | Actual guest CIM: `Microsoft Windows 10 Home`, version `10.0.19045`, computer `WIN01`; guest execution works after a Windows restart | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W3 | Static addressing and firewall | Pass, configured | One `10.77.1.3/27` IPv4 address, matching MAC, zero default routes; inbound TCP 5693 rules restricted to `10.77.1.1`; appliance reachability not tested | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W4 | Official NCPA package and private configuration | Pass | Windows Authenticode `Valid`, publisher Nagios Enterprises; version 3.5.0; token supplied by preseeded private config, never a token CLI flag | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W5 | Authenticated local CPU/memory API | Pass | First observations: per-core CPU 18.8/23.5%, virtual-memory use 34.2%; authenticated POST body, no token in URL; samples are point observations | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W6 | Windows disk/process node proof | Pass after diagnostic correction | Real disk node `C:\|`; `disk/logical/C:\|/used_percent` = 45.2%; `processes?name=ncpa.exe&check=1&critical=1:` returns OK, count 3 | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W7 | Fresh-boot NCPA without desktop sign-in | Pass | Service Running and the authenticated disk/process checks passed after another boot; temporary Administrator account confirmed disabled | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W8 | Shutdown, media cleanup and baseline | Pass | Graceful guest shutdown; powered-off snapshot; auxiliary installer ISO detached; boot order disk only; final running-VM list empty | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W9 | Activation/licensed-Windows finish condition | Blocked | Owner supplied no purchased license; guest reports Core edition LicenseStatus 5 (not activated); no product key supplied or activation bypass used | [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| W10 | Pinpoint manual registration, Windows metric in UI, final catalog and rehearsals | Not run | Appliance stayed off; new target-host/controller/catalog/approved scope and final license acceptance still pending | [#274](https://github.com/esfen14/Pinpoint/issues/274) |

## Identity and recovery

| Item | Observed value |
|---|---|
| VM | `pinpoint-defense-win01` |
| UUID | `5fb21051-8a4f-45b0-a7f0-de3cedceab83` |
| Resources | 3072 MiB RAM, 2 CPUs, 40 GiB maximum dynamic VDI |
| NIC | Internal Network `pinpoint-defense`, MAC `02:77:01:00:00:02`; seven other adapters disabled; no NAT, physical bridge or port forward |
| IPv4 | `10.77.1.3/27`, no default route |
| Pre-agent snapshot | `windows-installed`, UUID `b4d69a15-a224-4888-b1bc-1b7cf39af783` |
| Intermediate snapshot retained | `ncpa-pre-media-cleanup`, UUID `f56e6264-46f1-47c4-81b9-39a0880d8344` |
| Final snapshot | `ncpa-ready`, UUID `24eb5fdd-5f6c-4fdb-bfb8-a4b19e08523e` |

The same VM, disk, MAC and private login credential survived installation and
all guest restarts. Existing appliance/target disks were not restored, replaced
or changed. The final snapshot is a preparation baseline, not an endpoint-marker
restore trial or evidence of a fifteen-device run. Prefer that final snapshot
for later preparation; intermediate snapshots retain their earlier setup state.

## Package and credential handling

Owner media: `Win10_22H2_English_x64v1.iso`, image 1. VirtualBox detected x64
Windows and unattended installation support. No assertion of a verified
Microsoft ISO checksum is made.

NCPA came from the [official 3.5.0 archive](https://www.nagios.org/ncpa/archive.php),
using its [Windows installer](https://assets.nagios.com/downloads/ncpa3/ncpa-3.5.0.exe).
SHA-256: `bda660451c13f6730e9c40a3b31ec16bfcd20731a26830850d2a09d96c8ab700`.
The [tagged official installer source](https://github.com/NagiosEnterprises/ncpa/blob/v3.5.0/build/resources/ncpa.nsi)
retains an existing configuration, enabling preseeded private configuration
instead of a token-bearing argument. Its executable signature/publisher and
hash were verified in Windows before execution.

A generated 32-hex token and login password remain outside Git in the private
preparation directory. Guest configuration ACLs restrict access to administrators
and SYSTEM. API verification used POST form authentication over loopback TLS,
keeping the token out of URLs and process arguments. The probe found zero token
matches in agent logs. Temporary guest credential staging was removed, automatic
logon and its stored password were removed, and the temporary built-in
Administrator account was disabled before the final baseline. UAC stayed enabled.
The final snapshot has no mounted unattended media containing setup credentials.

The guest is configured for manual preinstalled-agent registration later; Linux
SSH deployment is not the Windows workflow. Windows metric defaults and Pinpoint
registration/help behavior have not been verified by this run.

## Diagnostics and resource observations

- First boot was blocked by host `VERR_SVM_IN_USE`, with KVM loaded. The owner
  locally unloaded KVM after being asked; noninteractive sudo was unavailable
  and no password was requested. Serial ownership preflight then passed.
- Windows Setup reached the desktop. Guest execution became ready after a normal
  Windows restart; the virtual ACPI power-button attempt had no effect. Fixed
  Windows desktop commands were used, preserving the VM/disk identity.
- Standard-user guest execution could read the OS but could not apply network
  settings. Setup used normal UAC consent and a temporary administrator context;
  a private script file avoided the Run dialog's long-command problem. No global
  UAC/host security setting was disabled.
- The first disk probe incorrectly expected a nested `disk.logical` response
  and requested a nonexistent path. The corrected probe used the actual
  `logical` response, asserted a real nonempty node and numeric percentage, and
  passed on `C:|`. This was a preparation-helper parsing error, not a Pinpoint
  defect. An Explorer process count of zero before interactive sign-in was real;
  the positive service-process probe used `ncpa.exe` instead.
- Resume start: 7603 MiB available RAM. During later verification: 6154 MiB
  available. Swap occupancy grew during installation; a four-second `vmstat`
  interval sampled zero swap-in/out, which does not establish a full-cycle
  absence of thrashing. Final host: 9255 MiB available, 1753 MiB swap used,
  70348 MiB free disk. The all-target resource acceptance gate remains unrun.
- Installation/verification elapsed about 32 minutes, including setup diagnostics.
  This is not a measured clean reusable provisioning time or discovery/alert timing.

All VM mutations targeted only the new recorded UUID and verified owner marker
under the canonical host claim. Host KVM restoration is an owner-local step after
all VirtualBox VMs stop; no permanent host module/boot configuration was changed.

## Follow-up

Complete the shared controller/target-host feasibility, approved product scan
scope and catalog. Resolve the licensed-Windows finish condition, manually
register the prepared agent through Pinpoint and show a Windows metric, then
repeat the fifteen-device and rehearsal gates. Keep those results separate from
this local guest preparation. No Pinpoint defect was observed or filed.

## Sanitization

- [x] No password, token, key, community string, license key or private key path
- [x] Addresses limited to the documented existing/candidate lab scopes
- [x] Raw logs, screenshots, answer files and configuration retained privately
- [x] Local guest proof distinguished from pending product/defense acceptance
