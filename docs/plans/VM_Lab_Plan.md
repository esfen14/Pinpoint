# VM Lab Plan (faithful lane)

Status: **control recovery and clean rebuild in progress ([#162](https://github.com/esfen14/Pinpoint/issues/162)); alerts and the `break` commands not yet run; NCPA run done (partial, #45).** Design agreed
2026-10-08. The first end-to-end run passed (create, provision, fresh install of `main`,
healthcheck 59/0, discovery and monitoring of five targets, sync); see
[`docs/test-runs/2026-10-08-vm-lab-first-run/`](../test-runs/2026-10-08-vm-lab-first-run/REPORT.md). Feeds
[`Agent_Workflow_and_CI.md`](../../spec%20files/Agent_Workflow_and_CI.md) (test
environments) and replaces nothing in the Docker lab
([`Local_Lab.md`](../manuals/Local_Lab.md)).

## 1. Why a second lane

The Docker lab is fast but is not the installer's appliance: no systemd, no real
`pinpoint` sudo rules, no DHCP, no NCPA install. The faithful lane runs the real
installer steps on a real Ubuntu 22.04.5 VM and monitors real Ubuntu target VMs.
It is slower, so it is for installer-contract changes, NCPA, and pre-release checks.

## 2. Design

### 2.1 Snapshot below the app

A snapshot of a finished install goes stale: a new migration, environment variable,
sudo rule or Nagios setting can make it test something the code no longer does.
So the snapshot stops before Pinpoint.

| Installer step | Depends on Pinpoint's code? | Where it runs |
|---|---|---|
| install-packages, install-nagios-core, install-nagios-plugins, configure-snmp, configure-nagios | No | Once, then frozen in snapshot `os-nagios-ready` |
| deploy-pinpoint-web, configure-pinpoint-privileges | Yes | On every fresh test |

### 2.2 Modes

| Mode | Command | What it does | Use for |
|---|---|---|---|
| Fresh | `scripts/vmlab fresh [branch]` | Restore the snapshot, start, install the pushed branch with the installer's deploy and privilege steps, run the healthcheck | Anything touching migrations, env vars, permissions, configs, the installer contract |
| Quick | `scripts/vmlab sync [--client]` | Copy the working tree into the running VM, restart Gunicorn; does not run migrations | UI and API fixes during QA |
| Upgrade | A second snapshot holding an older release | Re-run the deploy step on it | Testing the upgrade path; retake only at releases |

The installer's `deploy-pinpoint-web.sh` hardcodes `REPO_URL` and
`REPO_BRANCH="main"`. `vmlab fresh` patches a copy inside the VM; the installer
repository is never modified. The branch must be pushed.

### 2.3 Staleness guard

`provision` writes `/etc/pinpoint-vmlab-stamp` (installer commit and a hash of the
five base steps) before the snapshot. `scripts/vmlab status` compares it with the
current installer repository and warns when the base steps changed, which is the
signal to run `provision --force`.

## 3. Pieces

| Piece | State |
|---|---|
| Targets: `demo/demo_lab.py` (five Ubuntu 24.04 VMs on internal network `pinpoint-demo`, `10.77.0.0/28`; break, fix, load, reset, wall, NCPA login) | Built; `up` verified |
| Appliance VM `pinpoint-appliance` (4 GB, 4 CPUs; NIC 1 NAT with SSH and web port forwards, NIC 2 on `pinpoint-demo`), built by `scripts/vmlab create` from the stock Ubuntu 22.04.5 live-server ISO, unattended | Built and verified. Your existing `pinpoint-demo` VM was left alone |
| `scripts/vmlab`: iso, create, prepare, status, provision, fresh, sync, health, setup-admin, smoke, ncpa, alerts, creds, up, down, revert, targets | `create`, `prepare`, `provision`, `fresh`, `health`, `setup-admin`, `smoke`, `sync` (also `--client`), `ncpa`, `alerts`, `up`, `down`, `revert` verified ([run report](../test-runs/2026-10-08-vm-lab-remaining/REPORT.md)). Not run on its own: `status` with a live VM |
| `lab/smoke.py`: `--email`, `--password`/`SMOKE_PASSWORD`, `--set-network`, `--expect-ips` | Verified on the appliance and, as a regression, on the Docker lab |
| `lab/vmlab.env.example` | Written |

## 4. Steps to get running

No console steps: everything runs from `scripts/vmlab`, using your local clone of the
installer repository for the setup steps.

### 4.0 Preflight and recovery

Before a QA run, run `scripts/vmlab preflight`, then `scripts/vmlab status`.  A usable faithful lane has all of
the following:

- the configured appliance VM exists;
- the `os-nagios-ready` snapshot exists and is not stale against the installer
  base steps;
- `VBoxManage list vms` runs without a missing-`/dev/vboxdrv` error (the
  VirtualBox host driver and its udev device nodes are available);
- VirtualBox has enough free disk and RAM for one appliance plus the five
  targets; and
- no other tester owns the appliance or targets.

### Control and endpoint ownership (#162)

`status`, a successful SSH login, and a successful snapshot command do not prove
that the manager controls the VM serving the lab ports. The read-only Linux-host
preflight in `scripts/vmlab_preflight.py` requires:

- exactly one same-user `VBoxSVC` control process;
- for a running appliance, exactly one VM process for its UUID, matching
  the sole parent controller PID (and `SessionPID` when supplied by the version);
- exactly one listener on each configured port, bound to `127.0.0.1`, plus active runtime `TCP[HOST_FORWARD]` sockets reported by that controlled
  VM through `VBoxManage debugvm <vm> info nat0`, targeting guest SSH/22 and web/80
  on the same guest (IPv6/wildcard host conflicts also reject);
- for a powered-off appliance, no process for its UUID and no listener on either
  lab port. Transitional states, unreadable process identity, missing/unsupported NAT output and unavailable
  host procfs reject. Run on the host; a container/PID sandbox is not sufficient.

Appliance/target mutation commands run this check before SSH/API/control actions;
start and power-off paths recheck ownership at state boundaries. `create` requires
an unused name/ports, a single controller and no same-user running VM processes.
VirtualBox 7.2 does not include `SessionPID` in machine-readable metadata and its
SUID VM processes protect `/proc/<pid>/fd`. Runtime NAT socket inspection provides
positive listener proof without weakening OS permissions or requiring sudo.
These checks are observations, not a distributed lock: retain exclusive lab ownership
and do not run concurrent VM/control commands.

If preflight fails, do not start another copy, delete IPC sockets/locks, kill
inherited processes, or retry snapshot/restore. Preserve all disks, checkouts and
uncommitted changes. Inspect `ps` parent PIDs, `/proc/net/unix`, the selected
`VBoxSVC.log` and both listener socket owners read-only. An administrator may need
to inspect protected `/proc/<pid>/fd` metadata. Do not supply sudo passwords to an
agent or put them in evidence. The owner must coordinate any shutdown of inherited
sessions. Rebuilding a VM can provide a fresh lab, but cannot recover overwritten
edits or repair a split host control context by itself.

After control is coherent, prefer a separately named, newly created appliance
with its own empty disk, state/config folder and unused loopback ports. Do not
clone the inherited application disk for the snapshot trial. Before relying on
snapshot protection, verify it through the actual endpoint. A fresh application
install on the blank disk may be used to exercise HTTP as well as SSH:

1. Prove ownership with preflight; record VM UUID, process identity, ports and
   endpoint identity (for example guest machine-id or SSH host-key fingerprint).
   Verify the web listener too.
2. Write a random non-secret marker through SSH to a dedicated guest file and
   flush it. If an HTTP service is installed, serve that file and read it through
   HTTP too. Power off through the guarded lab command, require no remaining
   UUID process/listeners, then take a uniquely named powered-off snapshot and
   record its UUID. Restart through the guarded command.
3. Change that marker through the same SSH endpoint and read it back through
   each tested endpoint. Power off and restore only the disposable VM, then
   restart it. Powered-off snapshots avoid a restored saved state, which the
   current preflight intentionally rejects.
4. Repeat preflight after restart (a new VM process PID is expected); read the marker
   through the same endpoints and require its original value. Record both values,
   endpoint/VM identity and observed result in a sanitized report. A reported
   successful restore without the marker result is insufficient.
5. Keep inherited disks until the owner explicitly resolves the lost edits;
   an explicit owner-authorized retirement may remove them. Retain sanitized recovery evidence. The incident snapshots are not verified endpoint backups.

Before any later sync, inspect the guest destination's Git status and the service
WorkingDirectory. Preserve existing edits and choose an explicitly separate test
checkout rather than overwriting inherited work. The ownership guard does not
back up application data or establish a clean destination.

See the [read-only recovery report](../test-runs/2026-10-15-issue-162-recovery/REPORT.md).
The original inherited disks were retired with explicit owner approval after the
owner accepted the overwritten edits as unrecoverable. The new appliance uses a
new UUID and a blank disk; it contains no inherited application data.

If the appliance or snapshot is missing, recreate the lane with steps 1 through
5 below.  This is a setup/recovery operation, not a QA case: obtain the lab
owner's approval first and do not run it alongside another live test.  After
recovery, prove the lane with `scripts/vmlab fresh`, `scripts/vmlab setup-admin`
and `scripts/vmlab smoke` before claiming a journey case.  Record that recovery
and the tested commit in a new sanitized test-run report.

1. **Targets.** `python3 demo/demo_lab.py create --apply` (after `build-base`), then
   `scripts/vmlab targets up`.
2. **ISO.** `scripts/vmlab iso` downloads the stock Ubuntu 22.04.5 live-server ISO
   (about 2 GB). The installer's own ISO is not needed: its install screens are
   interactive, and the lab runs the same setup steps itself.
3. **Appliance VM.** `scripts/vmlab create` builds `pinpoint-appliance` with an
   unattended install (10 to 25 minutes): SSH key, passwordless sudo, apt sources and
   `10.77.0.1/28` on NIC 2 are set up for you.
4. **Config (optional).** Copy `lab/vmlab.env.example` to
   `~/.config/pinpoint-vmlab/env`; set `VMLAB_INSTALLER_DIR` to your installer clone to
   test installer edits before pushing them.
5. **Snapshot.** `scripts/vmlab provision` runs installer steps 1 to 5, powers off and
   takes `os-nagios-ready`.
6. **First test.** `scripts/vmlab fresh`, then `scripts/vmlab creds`; sign in once at
   `http://127.0.0.1:18080`. `scripts/vmlab setup-admin` sets a fresh administrator
   password (stored privately, never printed) and `scripts/vmlab smoke` signs in with it.

What is not automated: the installer ISO's own install path (interactive screens, the
late-commands that copy the setup files, the first-boot service and the setup wizard).
Test that by hand with `PinPoint-Installer-v1.1.iso` before a release.

## 5. Risks and unknowns

- **Resolved:** the installer steps ran non-interactively without the setup wizard.
- **Installer steps may prompt or expect the setup wizard's environment (was open; resolved above).** The five
  base steps and the two app steps are run directly over SSH, not through
  `pinpoint-setup.sh`. If one needs input or state the wizard provides, `provision`
  or `fresh` will fail at that step; fix by adapting `vmlab`, not the installer.
- **The deploy step needs internet and GitHub access in the VM** (the NAT NIC) and a
  pushed branch.
- **Unattended install on Ubuntu 22.04.5** follows the recipe `demo_lab.py` proved on
  24.04. VirtualBox's generated installer file could differ for 22.04; `create` stops
  with a clear message if its apt section is not in the expected form.
- **Disk:** the appliance disk is sparse (40 GB maximum); the host is near 90% full.
- **Time:** a fresh install builds the client and installs Python dependencies, so
  expect several minutes. Not yet measured.
- **The administrator password** is generated by the installer; `scripts/vmlab setup-admin`
  replaces it and keeps the new one privately. `smoke.py` stops with a clear message if
  a change is still pending.
- **Disk and RAM:** appliance 4 GB plus five targets at 512 MB each fits in about
  9.6 GB free RAM, with little headroom. Close other VMs.
- **`vmlab sync` does not run migrations or re-run privileges.** Use `fresh` when
  models or the installer contract change.

## 6. Done when

- `scripts/vmlab provision` and `fresh` complete on a clean VM and the healthcheck
  reports 0 failed checks.
- `scripts/vmlab smoke` passes against the five demo targets from a fresh install.
- NCPA deployment succeeds and NCPA monitoring is OK. Deployment passed (two targets, one on SSH port 2222, 70 s);
  monitoring failed on installer-built appliances (#45). Recorded in
  [`docs/test-runs/2026-10-08-ncpa-run/`](../test-runs/2026-10-08-ncpa-run/REPORT.md). Repeat after #45.
- `status` correctly warns after the installer's base steps change.
- This plan is folded into a manual (`docs/manuals/`) and closed.
