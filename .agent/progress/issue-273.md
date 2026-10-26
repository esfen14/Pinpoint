# Issue #273: System Refinement Add One-Time Single-Device Network Discovery Scan

Branch: `issue-273-single-device-scan`
Status: ready-for-review

## Finish condition

- [x] An authorized administrator can submit one valid IPv4 address and scan only that address through the existing discovery and Nagios configuration pipeline.
- [x] Saved networks and later scheduled/full scans remain unchanged after successful, failed, and stopped focused scans.
- [x] Devices and ports outside the requested target retain their state.
- [x] Invalid, CIDR range, loopback, multicast, unspecified, reserved, and IPv6 targets are rejected before scanning; unauthorized requests are denied.
- [x] Concurrency, status, stop, and progress work in both modes.
- [x] An unreachable target gives clear feedback and leaves inventory and Nagios configuration intact.
- [x] Existing full-network and scheduled discovery continue to work.
- [x] Automated tests and backend/frontend verification pass.
- [x] Backend, frontend, data, and implementation-status specifications and user help are updated.
- [ ] PR references #273, records verification and security review, and receives required CI checks and review approvals.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Optional one-time IPv4 target, existing permission, validation and normalization before worker | 1, 4 | `TestDiscoverStart` focused/invalid/permission tests; final all gate |
| Target reaches host and port discovery without settings writes | 1, 2 | `test_focused_scan_probes_only_requested_host_and_keeps_saved_networks`; final all gate |
| One scan at a time; status, progress, stop, audit, reconciliation, plugin attachment and Nagios rollback | 1, 3, 5 | `test_focused_stop_then_retry_uses_same_shared_worker_lock`, `test_focused_scan_uses_same_validated_config_pipeline`; final all gate |
| Unscanned devices and ports stay intact | 3 | `test_focused_save_preserves_other_device_and_ports`, `test_focused_refresh_does_not_probe_other_snmp_devices`, focused plugin reconciliation tests; final all gate |
| Unreachable target has clear result and no empty/unrelated config change | 6 | `test_focused_unreachable_target_skips_save_and_config`; final all gate |
| Admin Scan device input, help, permission gate and feedback; full rescan remains | 1, 5, 7 | `DiscoverySettings.test.tsx`, `useNetworkRescan.test.tsx`; final all gate |
| Full/scheduled scans and settings remain unchanged even after fail/stop | 2, 7 | `test_new_focused_device_outside_saved_network_keeps_later_full_scan_scope`, stop/retry and unreachable tests; final all gate |
| API contract, four named specifications, user help, security review | 9, 10 | Docs gate; explicit review notes; PR diff |
| Relevant automated tests, backend/frontend results and CI/review | 8, 10 | `scripts/verify.sh backend`, `frontend`, `docs`, `all`; PR checks/review |
| No migration unless persistent state is added; no hostname or bulk entry | 1, 2 | Diff review |

## Plan

1. [x] Add failing validation, permission and concurrency tests in `server/tests/unit/test_network_discovery.py`; implement optional target parsing/thread handoff in `server/app/api/system/network_discovery.py`.
2. [x] Add failing scan-scope, empty-result and full/scheduled regression tests in `server/tests/unit/test_network_discovery.py`, `test_device_config.py`, `test_plugin_reconcile.py`, `test_interface_discovery.py` and identity tests as applicable; implement target flow in `server/app/network_discovery/network_discovery.py`, `create_host_cfg.py`, `device_identity.py`, interface/port lifecycle and scoped plugin reconciliation in `server/app/api/plugin/reconcile.py`.
3. [x] Add failing UI interaction tests in `client/src/test/DiscoverySettings.test.tsx` and hook tests as applicable; implement `Scan device` in `client/src/components/settings/DiscoverySettings.tsx`, `client/src/hooks/useNetworkRescan.ts` and shared API/types as needed.
4. [x] Update `spec files/Backend_Modules_and_Routes.md`, `Frontend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Implementation_Status.md` and user-facing help for the resulting contract; verify docs.
5. [ ] Re-read issue and prove each finish item; run backend, frontend, docs and all gates; remove this progress file, push and open PR with verification and injection/secret review.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue, workflow, specs and source; wrote plan; no product code changed | `gh issue view 273 --json number,title,body,comments,state,labels,assignees` | Requirements covered; sensitive-module review checkpoint required |
| 1 | Added strict optional IPv4 route validation and worker handoff after user approved sensitive changes | `.venv/bin/python -m pytest tests/unit/test_network_discovery.py -q`; `scripts/verify.sh backend` | 25 passed; backend gate reached 30% with no failure before I interrupted it to avoid blocking the next TDD round. Full gate remains required. |
| 2 | Scoped host/port probes, identity lifecycle, port promotion and interface refresh; empty focused scan ends before save/config | `.venv/bin/python -m pytest tests/unit/test_network_discovery.py tests/unit/test_device_identity.py tests/unit/test_device_config.py -q --tb=short` | 130 passed; backend stage gate deferred to finish verification |
| 3 | Added permission-gated Scan device and full rescan controls, validation/help/status, shared hook body, and caller event wrappers | `scripts/verify.sh frontend` outside sandbox | Green: 84 files/1081 tests, build and lint (33 existing warnings). Sandbox run could not collect nested Playwright JSON; unchanged main failed the same way. |
| 4 | Updated backend, frontend, data and implementation-status specs; corrected stale stop permission inventory | `scripts/verify.sh docs` outside sandbox | Green; sandbox run hit temporary Unix-socket bind denial in unrelated QA fixtures |
| 5 | Added focused stop/retry, UI feedback and interface tests; scoped plugin reconciliation after diff review and documented it; reread issue | `scripts/verify.sh all` outside sandbox | Green: docs, 4,419 backend passed/14 skipped, 84 frontend files/1,082 tests, build and lint (0 errors/33 warnings) |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `scripts/verify.sh all`
- Result (first failing lines, or "green"): green outside sandbox; 4,419 backend passed/14 skipped, 1,082 frontend passed, docs/build/lint passed
- Hypothesis: all local work is proven; final pushed CI and required human PR review remain.
- Next action (one specific step, not "continue"): Check final CI status on draft PR #275 after this checkpoint.

## Decisions and notes

- `Engineering_Standards.md` marks `app/network_discovery/` sensitive and requires an explicit injection and secret-exposure review; `.agent/workflows/work-issue.md` says to stop for a person before changing it. The user approved proceeding in chat on 2026-10-26.
- Security review proposal: accept one strict IPv4 host (canonical dotted-decimal address or `/32` if contract chooses), reject ranges, unsafe/non-global classes and unexpected JSON; hand only the normalized numeric address to nmap; do not interpolate a shell or log request data that can carry secrets; keep existing Nagios validation, resource transaction and rollback. Inspect nmap3 invocation and scanned-result address matching during implementation.
- Current source shows the stop route already uses `system.discover`, while `Backend_Modules_and_Routes.md` and `Implementation_Status.md` still describe a `network.discovery` mismatch. Update those inventories with the issue's owning spec change; this is a stale inventory entry, not a requested permission redesign.
- No hostname resolution or bulk targets. No migration is planned.
- Final diff review found that the existing post-scan plugin reconciler promoted suggested ports on every device. Step 2 was expanded to scope its promotion and AUTO rows to the focused device; ordinary full scans retain global reconciliation. The focused plugin regression failed first, then 159 related backend tests passed.
- Five rounds were used in this session. Keep the progress file and draft PR until final CI and review approvals satisfy the issue's external merge condition. No live lab test was run under the workflow's live-test restriction.
