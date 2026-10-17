# Test run: issue-182-remote-restart

| | |
|---|---|
| Date | 2026-10-17 |
| Commit tested | `910d6f99` |
| Plan | server/tests/plans/REMOTE_RESTART_ACCEPTANCE.md |
| Tester | Codex agent |
| Environment | Fresh Ubuntu 22.04.5 appliance, Nagios 4.5.11; separate Ubuntu target; exclusive internal virtual network using 10.77.0.0/28; scans restricted to 10.77.0.2/32 |
| Raw evidence | Local host /tmp/issue182-*.log (temporary, uncommitted) |

## Result

**Overall: Partial.** Fresh installation passed all 60 installer health checks, the full local automated gate passed, and supported first-run setup succeeded. Eleven live/API acceptance cases passed after adding the documented installer #129 prerequisite. Browser case RR-12 is blocked because no browser provider is connected; human review and current-head PR CI remain merge gates. Full local gate passed: 3,864 backend tests, 14 skips, 875 frontend tests, build and lint (30 warnings, no errors).

Totals: Pass 12, Fail 0, Blocked 1, Skipped 0.

Automated evidence: `scripts/verify.sh all` finished with `verify: all OK` on the unchanged product tree, followed by final documentation verification. `issue182-resume-all.log`. The focused backend run passed 301 tests.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| ENV-01 | Pass | Fresh pushed issue branch installed at `910d6f99`; migration `a182f6c9d301`; 60 health checks passed; supported first-run setup succeeded. `issue182-vm-fresh.log`; setup output | — |
| RR-01 | Pass | Observed helper root:root 755, directory 755, allowlist 644 and sudoers 440; visudo passes and deployment account has only the two fixed helpers. `issue182-live-cases.log` | — |
| RR-02 | Pass | Real settings API save/reload, independent fingerprint verification, normal credential checks, trusted deployed cleanup and successful redeployment. No browser claim; UI errors/permissions covered by focused frontend tests. `issue182-live-redeploy.log` | — |
| RR-03 | Pass | Synthetic HARD event delivered to real consumer; actual SSH and systemd restart succeeded with one additional target marker. `issue182-live-cases.log` | — |
| RR-04 | Pass | Distinct events recorded skipped_cooldown and skipped_hourly_cap; target marker did not change. `issue182-live-cases.log` | — |
| RR-05 | Pass | Distinct synthetic events for disabled, paused, untrusted and Maintenance Mode each produced a failed run with the expected refusal, without a target marker change. Pause/trust/maintenance flags were temporarily set on the real appliance and restored in finally. `issue182-live-cases.log` | — |
| RR-06 | Pass | Changed the actual service SSH host key while keeping the stored fingerprint; observed a failed run with Host key changed, no marker change. Restored original service SSH configuration; separate management daemon retained its keys. `issue182-live-cases.log` | — |
| RR-07 | Pass | Removed fixture only from the root-owned on-device list; server allowlist still included it. Real helper refused it and consumer recorded the fixed on-device list message; no marker change. `issue182-live-cases.log` | — |
| RR-08 | Pass | Real 45-second systemd start returned a timed_out run after 20.29 seconds; stopped the already-submitted service job separately. `issue182-live-cases.log` | — |
| RR-09 | Pass | Deployment user was refused for off-list, extra-argument, hostile and option-shaped helper calls, and direct sudo systemctl. No injection file or target marker change. `issue182-live-cases.log` | — |
| RR-10 | Pass | API run details and captured application logs excluded the synthetic fixture sentinel, bootstrap password and actual deployment private-key bytes (compared only in memory). An additional root-owned wrapper emitted the sentinel on actual SSH stdout/stderr while invoking the unchanged original helper; restart succeeded and only fixed status was recorded. The first wrapper attempt correctly refused while the switch remained off; enabled it for the repeat. Restored the helper and disabled the test action. `issue182-live-cases.log`, `issue182-live-output.log` | — |
| RR-11 | Pass | API deletion retained audit rows with actionId null; immediate replacement succeeded despite prior cap/cooldown. `issue182-live-cases.log` | — |
| RR-12 | Blocked | No browser provider connected; UI unit tests cover settings load/save/errors/permissions and remote/local unit controls, but browser behavior was not observed | [#182](https://github.com/esfen14/Pinpoint/issues/182) |

## Deviations from the plan

The previous session cloned the disposable target after the new-VM preflight refused creation while the appliance was running. Existing VMs were untouched; this session proved the clone powered off with no endpoint listeners before configuring it, then proved process/controller/runtime-forward ownership after startup. Both guests use a separate issue182 internal network; all pre-existing target VMs remain off.

Installer base SHA `697869e` lacks the required #129 resource helper. The first deployment installed NCPA successfully but could not apply its Nagios config. Installed the exact helper from installer branch SHA `b166953d2e7e5b4bae12bf723712224cc97fae94`, with its fixed no-argument sudoers grant, then used the normal cleanup/redeployment API successfully. This known installer prerequisite is [installer PR #7](https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/7).

The initial discovery used an empty UDP list, which invokes nmap default ports. Requested stop, then terminated only its verified owned UDP nmap process; this intentional interrupted attempt is not an acceptance failure. Repeated with only UDP/161 and discovery succeeded.

The temporary consumer harness required correcting the installed venv path, Python module path, and event timestamp units before any action could run. These preparation errors produced no run rows. Accepted events use synthetic epoch-second timestamps; SSH/systemd and the production consumer remain real. No Nagios-generated event-chain claim.

Final normal cleanup/redeployment succeeded again. The installed helper SHA-256 matches the repository HELPER_SCRIPT exactly, the root-owned list contains both fixtures, and all test actions and remote restart are disabled. The paused/trusted/maintenance flags and original SSH host keys are restored. Stopped both fixture services and removed only the temporary rotated key files. Deployed SQLite PRAGMA confirms Action_Id points to REMEDIATION_ACTION.Id with ON DELETE SET NULL; 13 recorded attempts remain for audit. `issue182-final-redeploy.log`.

No browser provider is connected (`cua.listBrowsers()` returned an empty list); browser case RR-12 remains unverified.

The setup helper expects an older installer credential label (existing #167). First-run setup was completed with the supported API, parsing the current installer format privately; no product or helper changes were made.

## Follow-up

- Pending: RR-12 browser walkthrough, human security review and PR CI.
- Both owned VMs shut down through the guarded controller; final preflight confirms poweroff and no endpoint listeners. Disks and private runtime state retained.
- KVM restoration needs the owner: `sudo -n modprobe kvm_amd` refused because a password is required; requested owner terminal restoration.
- Existing compatibility finding: [#167](https://github.com/esfen14/Pinpoint/issues/167).

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
