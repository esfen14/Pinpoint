# Issue #274 Linux target-host installation

| Field | Observed scope |
|---|---|
| Date / executor | 2026-10-27 Asia/Manila; Codex, scripted VirtualBox/SSH plus guest console recovery |
| Source | Base `cf170772` plus the versioned installation/recovery fixes identified below; no deployed Pinpoint changes |
| Plan / issue | [Defense demo plan](../../plans/Defense_Demo_Lab_Plan.md); [#274](https://github.com/esfen14/Pinpoint/issues/274) |
| Catalog | `manifest.json`, SHA-256 `7a2ab626fb66bc71ff660347fd6ba8d118d2c67e600041c84575fa7d47fdc1f8` |
| Queue / credit | Issue preparation only; no QA queue/session/card; 0 unique TC and 0 unique E2E executions; no historical credit |
| Environment | VirtualBox 7.2.14; fresh Ubuntu Server 24.04.5 VM, 2048 MiB, 2 CPUs, dynamic 16 GiB disk |
| Application / installer | Pinpoint and its installer were not changed or exercised; Ubuntu autoinstall plus issue-local bootstrap |
| Private raw evidence | `~/.local/share/pinpoint-defense/controller/target-host/`: private logs/media/state, screenshots and `guest-observation.json`; never publish these |

Overall: **Partial preparation, no defense acceptance.** The dedicated VM and
container image preparation exist, and the original injected SSH host key is
verified after recovery. A subsequent boot re-enabled IPv4 forwarding through
Docker. The helper's forwarding check rejects attachment. No container, DHCP
allocator/client, appliance scan, Windows registration or rehearsal ran.

| Preparation observation | Result | Evidence and limit |
|---|---|---|
| New owned VM, preserved old resources | Pass | `pinpoint-defense-targets`, UUID `821464dc-e7ce-4067-8eec-5cb1c61d3632`; other VMs stayed off and unchanged |
| NIC boundary / management | Pass | NAT NIC1 MAC `02:77:01:fe:fc:bb`, exact loopback TCP2260→22; internal NIC2 MAC `02:77:01:fe:31:d7`, `pinpoint-defense`, allow-vms; remaining NICs disabled |
| Guarded installer boot | Pass | Actual pre-start 10073 MiB available / 70283 MiB disk free; exact owner, process/NAT, storage and NIC observations passed |
| Base OS and post-install | Partially Pass | Ubuntu installed; initial UUID-byte-order and offline-systemd failures were diagnosed and recovered without replacing/reformatting the disk; new negative regressions pass |
| First-boot automation | Partially Pass | Kernel-update dialog required Enter; code now sets noninteractive debconf/needrestart. Cloud-init replaced the injected host key; strict SSH refused it. Original key restored via the exact VM's stock-ISO live environment and private setup media; key-preservation config and future autoinstall user-data corrected |
| Pinned SSH | Pass | Final normal disk boot authenticated with `StrictHostKeyChecking=yes` and original known_hosts; no replacement-key acceptance or unverified SSH connection |
| Image preparation | Partially Pass | Guest completion marker/runtime-pin files observed; build service reported success. Image daemons/configurations and container execution remain untested; rebuild against final source before the spike |
| Unnumbered demo parent | Pass | Actual `enp0s8` has an empty address list; guest observation retained privately |
| Forwarding across reboot | Blocked ([#274](https://github.com/esfen14/Pinpoint/issues/274)) | Actual IPv4 forwarding `1`, IPv6 `0`; Docker startup re-enabled IPv4 despite the setup reset. Do not attach/start targets until durable guard and restart/reboot retests pass |
| Management privileges | Partially Pass | Actual no sudo/docker groups; sudo lists only the fixed helper. `lxd` group remains and must be removed/reviewed before acceptance |
| Capacity / isolation / all fifteen | Not run | Short install sample had ~8.6 GiB available and current swap-in/out 0; not the required simultaneous three-VM cycle or packet-isolation proof |

## Recovery and restoration

The original post-install failure occurred before state mutation (UUID byte order).
A diagnostic plain chroot lacked sysfs; repeating through Curtin identified the
actual UUID mismatch. The next setup attempt stopped at an unavailable systemd
bus. Before retry, its exact context and source files were checked and retained
under private `*-bootstrap-failed-1` directories inside the guest. Corrected
public source was transferred through a temporary loopback-only server, verified
by SHA-256, and used with the already-private payload. The server was stopped.
No password or private key appeared in command arguments or committed evidence.

The cloud-init host-key replacement was never trusted by SSH. Live rescue booted
only the stock ISO first; private media was attached after reaching the live
shell. The installed root context, VM identity and hostname were checked before
restoring the original key from the private payload. Its derived public half
matched the original public key. Management authorization and key-preservation
configuration were restored. Both DVDs were detached for the subsequent normal
boot; no disk was recreated or formatted during recovery.

Final observation confirms all VirtualBox VMs powered off, both target-host
DVDs empty and disk-only boot. Owned snapshot `installed-needs-forwarding-guard`
UUID `03940831-44b5-425b-93ec-7583dedade51` preserves this explicitly incomplete
baseline. The owner restored KVM after the temporary unload; fresh module and `/dev/kvm` observations confirm restoration, with all VirtualBox VMs still off. The next session must fix forwarding across Docker/VM restart,
remove the remaining privileged group, verify current image provenance and only
then implement the two-target spike. All eight issue finish-condition gates
remain pending. These are lab-tool preparation findings under #274, not observed
Pinpoint product defects.

## Candidate source fingerprints

- `provision.py`: `19daf736e21e3a070441014900bf4e1e13d719bbb29c33001095842503f18dc7`
- `bootstrap.py`: `d75a08c1ae2e4e692a94297e757523b2be0f1d216a5f43f9499c34c0f7360e49`
- `node.py`: `04a37b8046a9c58f4c057dcc9da097b6ceaf52a7cc1dda9e29f24301c265217f`
- `guest.py`: `fcf03115cea3489bda91eb79800df9e46c54fafeb0ff6393ab6dd6e2def41ebb`
